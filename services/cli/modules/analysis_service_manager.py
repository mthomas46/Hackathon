"""Analysis Service Manager module for CLI service.

Provides power-user operations for analysis service including
document analysis, findings management, report generation, and integration monitoring.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
import json
import os
import asyncio
from datetime import datetime
from collections import defaultdict

from .shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class AnalysisServiceManager:
    """Manager for analysis service power-user operations."""

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients
        self.analysis_history = []

    async def analysis_service_menu(self):
        """Main analysis service menu."""
        while True:
            menu = create_menu_table("Analysis Service Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Document Analysis (Analyze documents for consistency and issues)"),
                ("2", "Findings Management (Review, filter, and manage analysis findings)"),
                ("3", "Report Generation (Create various types of analysis reports)"),
                ("4", "Specialized Reports (Confluence consolidation, Jira staleness)"),
                ("5", "Integration Monitoring (Cross-service health and connectivity)"),
                ("6", "Natural Language Analysis (Conversational document analysis)"),
                ("7", "Prompt-Based Analysis (Use customizable analysis prompts)"),
                ("8", "Analysis History (Review past analysis operations)"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.document_analysis_menu()
            elif choice == "2":
                await self.findings_management_menu()
            elif choice == "3":
                await self.report_generation_menu()
            elif choice == "4":
                await self.specialized_reports_menu()
            elif choice == "5":
                await self.integration_monitoring_menu()
            elif choice == "6":
                await self.natural_language_analysis_menu()
            elif choice == "7":
                await self.prompt_based_analysis_menu()
            elif choice == "8":
                await self.analysis_history_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def document_analysis_menu(self):
        """Document analysis submenu."""
        while True:
            menu = create_menu_table("Document Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Analyze Single Document"),
                ("2", "Analyze Multiple Documents (Batch)"),
                ("3", "Analyze by Source Type (Confluence/Jira)"),
                ("4", "Configure Analysis Detectors"),
                ("5", "Analysis Templates"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.analyze_single_document()
            elif choice == "2":
                await self.analyze_multiple_documents()
            elif choice == "3":
                await self.analyze_by_source_type()
            elif choice == "4":
                await self.configure_analysis_detectors()
            elif choice == "5":
                await self.analysis_templates()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def analyze_single_document(self):
        """Analyze a single document for consistency and issues."""
        try:
            doc_id = Prompt.ask("[bold cyan]Document ID to analyze[/bold cyan]")

            if not doc_id.strip():
                self.console.print("[yellow]Document ID cannot be empty[/yellow]")
                return

            # Optional analysis parameters
            detectors = Prompt.ask("[bold cyan]Detectors to use (comma-separated, optional)[/bold cyan]", default="")
            severity_filter = Prompt.ask("[bold cyan]Minimum severity level (optional)[/bold cyan]", default="")

            # Build analysis request
            analysis_request = {
                "targets": [doc_id],
                "detectors": [d.strip() for d in detectors.split(",") if d.strip()] if detectors else None
            }

            if severity_filter:
                analysis_request["severity_filter"] = severity_filter

            with self.console.status(f"[bold green]Analyzing document {doc_id}...[/bold green]") as status:
                response = await self.clients.post_json("analysis-service/analyze", analysis_request)

            if response:
                # Store in history
                analysis_record = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "single_document",
                    "target": doc_id,
                    "detectors": detectors,
                    "severity_filter": severity_filter,
                    "response": response
                }
                self.analysis_history.append(analysis_record)

                await self.display_analysis_results(response, f"Analysis Results for {doc_id}")
                self.console.print(f"[green]✅ Document analysis completed[/green]")
            else:
                self.console.print("[red]❌ Failed to analyze document[/red]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing document: {e}[/red]")

    async def analyze_multiple_documents(self):
        """Analyze multiple documents in batch."""
        try:
            doc_ids_input = Prompt.ask("[bold cyan]Document IDs to analyze (comma-separated)[/bold cyan]")

            if not doc_ids_input.strip():
                self.console.print("[yellow]Document IDs cannot be empty[/yellow]")
                return

            doc_ids = [doc_id.strip() for doc_id in doc_ids_input.split(",") if doc_id.strip()]

            if not doc_ids:
                self.console.print("[yellow]No valid document IDs provided[/yellow]")
                return

            # Optional parameters
            detectors = Prompt.ask("[bold cyan]Detectors to use (comma-separated, optional)[/bold cyan]", default="")
            batch_size = int(Prompt.ask("[bold cyan]Batch size[/bold cyan]", default="10"))

            analysis_request = {
                "targets": doc_ids,
                "detectors": [d.strip() for d in detectors.split(",") if d.strip()] if detectors else None,
                "batch_size": batch_size
            }

            with self.console.status(f"[bold green]Analyzing {len(doc_ids)} documents...[/bold green]") as status:
                response = await self.clients.post_json("analysis-service/analyze", analysis_request)

            if response:
                # Store in history
                analysis_record = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "batch_analysis",
                    "targets": doc_ids,
                    "detectors": detectors,
                    "batch_size": batch_size,
                    "response": response
                }
                self.analysis_history.append(analysis_record)

                await self.display_analysis_results(response, f"Batch Analysis Results ({len(doc_ids)} documents)")
                self.console.print(f"[green]✅ Batch analysis completed[/green]")
            else:
                self.console.print("[red]❌ Failed to perform batch analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error in batch analysis: {e}[/red]")

    async def analyze_by_source_type(self):
        """Analyze documents by source type (Confluence/Jira)."""
        try:
            source_type = Prompt.ask("[bold cyan]Source type to analyze[/bold cyan]", choices=["confluence", "jira"])

            # Get documents by source type
            params = {"source_type": source_type, "limit": 100}

            with self.console.status(f"[bold green]Retrieving {source_type} documents...[/bold green]") as status:
                docs_response = await self.clients.get_json("doc-store/documents", params=params)

            if docs_response and "items" in docs_response:
                documents = docs_response["items"]
                doc_ids = [doc["id"] for doc in documents]

                if not doc_ids:
                    self.console.print(f"[yellow]No {source_type} documents found[/yellow]")
                    return

                self.console.print(f"[yellow]Found {len(doc_ids)} {source_type} documents to analyze[/yellow]")

                confirm = Confirm.ask(f"[bold cyan]Analyze all {len(doc_ids)} {source_type} documents?[/bold cyan]", default=False)

                if confirm:
                    analysis_request = {
                        "targets": doc_ids,
                        "source_type": source_type
                    }

                    with self.console.status(f"[bold green]Analyzing {len(doc_ids)} {source_type} documents...[/bold green]") as status:
                        response = await self.clients.post_json("analysis-service/analyze", analysis_request)

                    if response:
                        # Store in history
                        analysis_record = {
                            "timestamp": datetime.now().isoformat(),
                            "type": "source_type_analysis",
                            "source_type": source_type,
                            "target_count": len(doc_ids),
                            "response": response
                        }
                        self.analysis_history.append(analysis_record)

                        await self.display_analysis_results(response, f"{source_type.title()} Analysis Results")
                        self.console.print(f"[green]✅ {source_type.title()} analysis completed[/green]")
                    else:
                        self.console.print(f"[red]❌ Failed to analyze {source_type} documents[/red]")
                else:
                    self.console.print("[yellow]Analysis cancelled[/yellow]")
            else:
                self.console.print(f"[red]❌ Failed to retrieve {source_type} documents[/red]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing by source type: {e}[/red]")

    async def configure_analysis_detectors(self):
        """Configure analysis detectors."""
        try:
            # Get available detectors
            with self.console.status("[bold green]Retrieving available detectors...[/bold green]") as status:
                response = await self.clients.get_json("analysis-service/detectors")

            if response:
                detectors = response.get("detectors", [])

                table = Table(title="Available Analysis Detectors")
                table.add_column("Name", style="cyan")
                table.add_column("Description", style="white")
                table.add_column("Capabilities", style="green")

                for detector in detectors:
                    capabilities = ", ".join(detector.get("capabilities", []))
                    table.add_row(
                        detector.get("name", "Unknown"),
                        detector.get("description", "No description"),
                        capabilities
                    )

                self.console.print(table)

                # Option to configure specific detector
                configure_detector = Confirm.ask("[bold cyan]Configure a specific detector?[/bold cyan]", default=False)

                if configure_detector:
                    detector_names = [d.get("name") for d in detectors]
                    detector_name = Prompt.ask("[bold cyan]Detector to configure[/bold cyan]", choices=detector_names)

                    # In a real implementation, this would show configuration options
                    self.console.print(f"[yellow]Configuration for {detector_name} would be displayed here[/yellow]")
                    Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            else:
                self.console.print("[red]❌ Failed to retrieve detectors[/red]")

        except Exception as e:
            self.console.print(f"[red]Error configuring detectors: {e}[/red]")

    async def analysis_templates(self):
        """Manage analysis templates."""
        try:
            self.console.print("[yellow]Analysis templates would provide reusable analysis configurations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with analysis templates: {e}[/red]")

    async def display_analysis_results(self, results: Dict[str, Any], title: str):
        """Display analysis results in a formatted way."""
        if not results:
            self.console.print(f"[yellow]{title}: No results to display[/yellow]")
            return

        content = f"""
[bold]📊 {title}[/bold]

[bold blue]Analysis Summary:[/bold blue]
• Status: {results.get('status', 'unknown')}
• Total Findings: {results.get('total_findings', 0)}
• Processing Time: {results.get('processing_time', 'N/A')}
"""

        # Show findings breakdown
        findings = results.get("findings", [])
        if findings:
            severity_counts = defaultdict(int)
            type_counts = defaultdict(int)

            for finding in findings:
                severity_counts[finding.get("severity", "unknown")] += 1
                finding_type = finding.get("type", "unknown")
                type_counts[finding_type] += 1

            content += "\n[bold green]Findings by Severity:[/bold green]\n"
            for severity, count in sorted(severity_counts.items(), key=lambda x: x[1], reverse=True):
                severity_color = {
                    "critical": "red",
                    "high": "red",
                    "medium": "yellow",
                    "low": "green",
                    "info": "blue"
                }.get(severity.lower(), "white")
                content += f"• [{severity_color}]{severity}[/{severity_color}]: {count}\n"

            content += "\n[bold cyan]Findings by Type:[/bold cyan]\n"
            for finding_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                content += f"• {finding_type}: {count}\n"

        print_panel(self.console, content, border_style="blue")

        # Show detailed findings if requested
        if findings:
            show_details = Confirm.ask("[bold cyan]Show detailed findings?[/bold cyan]", default=False)

            if show_details:
                table = Table(title="Detailed Findings")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Type", style="green")
                table.add_column("Severity", style="yellow")
                table.add_column("Description", style="white")

                for finding in findings[:20]:  # Limit to first 20
                    severity = finding.get("severity", "unknown")
                    severity_color = {
                        "critical": "red",
                        "high": "red",
                        "medium": "yellow",
                        "low": "green",
                        "info": "blue"
                    }.get(severity.lower(), "white")

                    table.add_row(
                        finding.get("id", "unknown"),
                        finding.get("type", "unknown"),
                        f"[{severity_color}]{severity.upper()}[/{severity_color}]",
                        finding.get("description", "")[:60] + "..." if len(finding.get("description", "")) > 60 else finding.get("description", "")
                    )

                self.console.print(table)

                if len(findings) > 20:
                    self.console.print(f"[yellow]... and {len(findings) - 20} more findings[/yellow]")

    async def findings_management_menu(self):
        """Findings management submenu."""
        while True:
            menu = create_menu_table("Findings Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View All Findings"),
                ("2", "Filter Findings by Severity"),
                ("3", "Filter Findings by Type"),
                ("4", "Search Findings"),
                ("5", "Findings Statistics"),
                ("6", "Notify Owners of Findings"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_all_findings()
            elif choice == "2":
                await self.filter_findings_by_severity()
            elif choice == "3":
                await self.filter_findings_by_type()
            elif choice == "4":
                await self.search_findings()
            elif choice == "5":
                await self.findings_statistics()
            elif choice == "6":
                await self.notify_owners_of_findings()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_all_findings(self):
        """View all analysis findings."""
        try:
            limit = int(Prompt.ask("[bold cyan]Maximum findings to retrieve[/bold cyan]", default="50"))

            params = {"limit": limit}

            with self.console.status("[bold green]Retrieving findings...[/bold green]") as status:
                response = await self.clients.get_json("analysis-service/findings", params=params)

            if response and "findings" in response:
                findings = response["findings"]
                await self.display_findings(findings, f"All Findings (showing {len(findings)})")
            else:
                self.console.print("[yellow]No findings found[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error viewing findings: {e}[/red]")

    async def filter_findings_by_severity(self):
        """Filter findings by severity level."""
        try:
            severity = Prompt.ask("[bold cyan]Severity level to filter by[/bold cyan]", choices=["critical", "high", "medium", "low", "info"])
            limit = int(Prompt.ask("[bold cyan]Maximum findings to retrieve[/bold cyan]", default="50"))

            params = {"severity": severity, "limit": limit}

            with self.console.status(f"[bold green]Retrieving {severity} severity findings...[/bold green]") as status:
                response = await self.clients.get_json("analysis-service/findings", params=params)

            if response and "findings" in response:
                findings = response["findings"]
                await self.display_findings(findings, f"{severity.title()} Severity Findings ({len(findings)} found)")
            else:
                self.console.print(f"[yellow]No {severity} severity findings found[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error filtering by severity: {e}[/red]")

    async def filter_findings_by_type(self):
        """Filter findings by finding type."""
        try:
            finding_type = Prompt.ask("[bold cyan]Finding type to filter by[/bold cyan]")
            limit = int(Prompt.ask("[bold cyan]Maximum findings to retrieve[/bold cyan]", default="50"))

            params = {"finding_type_filter": finding_type, "limit": limit}

            with self.console.status(f"[bold green]Retrieving {finding_type} type findings...[/bold green]") as status:
                response = await self.clients.get_json("analysis-service/findings", params=params)

            if response and "findings" in response:
                findings = response["findings"]
                await self.display_findings(findings, f"{finding_type.title()} Type Findings ({len(findings)} found)")
            else:
                self.console.print(f"[yellow]No {finding_type} type findings found[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error filtering by type: {e}[/red]")

    async def search_findings(self):
        """Search findings by content."""
        try:
            search_term = Prompt.ask("[bold cyan]Search term in finding descriptions[/bold cyan]")
            limit = int(Prompt.ask("[bold cyan]Maximum findings to retrieve[/bold cyan]", default="50"))

            if not search_term.strip():
                self.console.print("[yellow]Search term cannot be empty[/yellow]")
                return

            params = {"limit": limit}

            with self.console.status("[bold green]Retrieving findings for search...[/bold green]") as status:
                response = await self.clients.get_json("analysis-service/findings", params=params)

            if response and "findings" in response:
                all_findings = response["findings"]
                matching_findings = []

                for finding in all_findings:
                    description = finding.get("description", "").lower()
                    if search_term.lower() in description:
                        matching_findings.append(finding)
                        if len(matching_findings) >= limit:
                            break

                await self.display_findings(matching_findings, f"Findings containing '{search_term}' ({len(matching_findings)} found)")
            else:
                self.console.print(f"[yellow]No findings found containing '{search_term}'[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error searching findings: {e}[/red]")

    async def display_findings(self, findings: List[Dict[str, Any]], title: str):
        """Display findings in a formatted table."""
        if not findings:
            self.console.print(f"[yellow]{title}: No findings found[/yellow]")
            return

        table = Table(title=title)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Severity", style="yellow")
        table.add_column("Document", style="blue")
        table.add_column("Description", style="white")

        for finding in findings[:30]:  # Limit display to 30 findings
            severity = finding.get("severity", "unknown")
            severity_color = {
                "critical": "red",
                "high": "red",
                "medium": "yellow",
                "low": "green",
                "info": "blue"
            }.get(severity.lower(), "white")

            description = finding.get("description", "")
            if len(description) > 50:
                description = description[:47] + "..."

            table.add_row(
                finding.get("id", "unknown"),
                finding.get("type", "unknown"),
                f"[{severity_color}]{severity.upper()}[/{severity_color}]",
                finding.get("document_id", "unknown"),
                description
            )

        self.console.print(table)

        if len(findings) > 30:
            self.console.print(f"[yellow]... and {len(findings) - 30} more findings[/yellow]")

    async def findings_statistics(self):
        """Show findings statistics and analytics."""
        try:
            # Get all findings
            params = {"limit": 1000}  # Get more for statistics
            response = await self.clients.get_json("analysis-service/findings", params=params)

            if response and "findings" in response:
                findings = response["findings"]

                # Calculate statistics
                total_findings = len(findings)
                severity_stats = defaultdict(int)
                type_stats = defaultdict(int)
                document_stats = defaultdict(int)

                for finding in findings:
                    severity_stats[finding.get("severity", "unknown")] += 1
                    type_stats[finding.get("type", "unknown")] += 1
                    document_stats[finding.get("document_id", "unknown")] += 1

                # Display statistics
                content = f"""
[bold]📈 Findings Statistics[/bold]

[bold blue]Overview:[/bold blue]
• Total Findings: {total_findings}
• Unique Document Types: {len(type_stats)}
• Documents with Findings: {len(document_stats)}

[bold green]By Severity:[/bold green]
"""

                severity_order = ["critical", "high", "medium", "low", "info", "unknown"]
                for severity in severity_order:
                    if severity in severity_stats:
                        percentage = (severity_stats[severity] / total_findings) * 100
                        severity_color = {
                            "critical": "red",
                            "high": "red",
                            "medium": "yellow",
                            "low": "green",
                            "info": "blue"
                        }.get(severity, "white")
                        content += f"• [{severity_color}]{severity.title()}[/{severity_color}]: {severity_stats[severity]} ({percentage:.1f}%)\n"

                content += f"\n[bold cyan]Top Finding Types:[/bold cyan]\n"
                for finding_type, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (count / total_findings) * 100
                    content += f"• {finding_type}: {count} ({percentage:.1f}%)\n"

                print_panel(self.console, content, border_style="blue")

            else:
                self.console.print("[yellow]No findings data available for statistics[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error showing findings statistics: {e}[/red]")

    async def notify_owners_of_findings(self):
        """Send notifications for findings to owners."""
        try:
            # Get recent findings
            params = {"limit": 50}
            response = await self.clients.get_json("analysis-service/findings", params=params)

            if response and "findings" in response:
                findings = response["findings"]

                if not findings:
                    self.console.print("[yellow]No findings available to notify owners about[/yellow]")
                    return

                self.console.print(f"[yellow]Found {len(findings)} recent findings[/yellow]")

                # Select findings to notify about
                notify_all = Confirm.ask(f"[bold cyan]Notify owners about all {len(findings)} findings?[/bold cyan]", default=False)

                if not notify_all:
                    # Let user select specific findings
                    finding_ids = [f.get("id") for f in findings[:10]]  # Show first 10
                    selected_ids = Prompt.ask(f"[bold cyan]Finding IDs to notify about (comma-separated, from: {', '.join(finding_ids)})[/bold cyan]")

                    if selected_ids.strip():
                        selected_ids_list = [fid.strip() for fid in selected_ids.split(",") if fid.strip()]
                        findings_to_notify = [f for f in findings if f.get("id") in selected_ids_list]
                    else:
                        self.console.print("[yellow]No findings selected[/yellow]")
                        return
                else:
                    findings_to_notify = findings

                # Choose notification channels
                channels_input = Prompt.ask("[bold cyan]Notification channels (comma-separated: email,webhook,slack)[/bold cyan]", default="email")
                channels = [ch.strip() for ch in channels_input.split(",") if ch.strip()]

                notify_request = {
                    "findings": findings_to_notify,
                    "channels": channels
                }

                with self.console.status(f"[bold green]Notifying owners about {len(findings_to_notify)} findings...[/bold green]") as status:
                    notify_response = await self.clients.post_json("analysis-service/reports/findings/notify-owners", notify_request)

                if notify_response:
                    notifications_sent = notify_response.get("notifications_sent", 0)
                    self.console.print(f"[green]✅ Sent {notifications_sent} notifications via {channels}[/green]")
                else:
                    self.console.print("[red]❌ Failed to send notifications[/red]")
            else:
                self.console.print("[yellow]No findings available for notification[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error notifying owners: {e}[/red]")

    async def report_generation_menu(self):
        """Report generation submenu."""
        while True:
            menu = create_menu_table("Report Generation", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Generate Summary Report"),
                ("2", "Generate Trends Report"),
                ("3", "Generate Quality Report"),
                ("4", "Custom Report Generation"),
                ("5", "Export Reports"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.generate_summary_report()
            elif choice == "2":
                await self.generate_trends_report()
            elif choice == "3":
                await self.generate_quality_report()
            elif choice == "4":
                await self.custom_report_generation()
            elif choice == "5":
                await self.export_reports()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def generate_summary_report(self):
        """Generate a summary report."""
        try:
            report_request = {
                "type": "summary",
                "include_findings": True,
                "include_statistics": True
            }

            with self.console.status("[bold green]Generating summary report...[/bold green]") as status:
                response = await self.clients.post_json("analysis-service/reports/generate", report_request)

            if response:
                await self.display_report(response, "Summary Report")
                self.console.print("[green]✅ Summary report generated[/green]")
            else:
                self.console.print("[red]❌ Failed to generate summary report[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating summary report: {e}[/red]")

    async def generate_trends_report(self):
        """Generate a trends report."""
        try:
            time_period = Prompt.ask("[bold cyan]Time period for trends[/bold cyan]", default="30d")

            report_request = {
                "type": "trends",
                "time_period": time_period,
                "include_charts": True
            }

            with self.console.status(f"[bold green]Generating trends report for {time_period}...[/bold green]") as status:
                response = await self.clients.post_json("analysis-service/reports/generate", report_request)

            if response:
                await self.display_report(response, f"Trends Report ({time_period})")
                self.console.print("[green]✅ Trends report generated[/green]")
            else:
                self.console.print("[red]❌ Failed to generate trends report[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating trends report: {e}[/red]")

    async def generate_quality_report(self):
        """Generate a quality report."""
        try:
            quality_threshold = float(Prompt.ask("[bold cyan]Quality threshold (0.0-1.0)[/bold cyan]", default="0.7"))

            report_request = {
                "type": "quality",
                "quality_threshold": quality_threshold,
                "include_recommendations": True
            }

            with self.console.status(f"[bold green]Generating quality report (threshold: {quality_threshold})...[/bold green]") as status:
                response = await self.clients.post_json("analysis-service/reports/generate", report_request)

            if response:
                await self.display_report(response, f"Quality Report (Threshold: {quality_threshold})")
                self.console.print("[green]✅ Quality report generated[/green]")
            else:
                self.console.print("[red]❌ Failed to generate quality report[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating quality report: {e}[/red]")

    async def custom_report_generation(self):
        """Generate a custom report."""
        try:
            self.console.print("[yellow]Custom report generation would allow advanced report configuration[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with custom report generation: {e}[/red]")

    async def export_reports(self):
        """Export reports to various formats."""
        try:
            self.console.print("[yellow]Report export would allow saving reports in different formats[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with report export: {e}[/red]")

    async def display_report(self, report: Dict[str, Any], title: str):
        """Display a report in a formatted way."""
        if not report:
            self.console.print(f"[yellow]{title}: No report data to display[/yellow]")
            return

        content = f"""
[bold]📋 {title}[/bold]

[bold blue]Report Information:[/bold blue]
• Generated: {report.get('generated_at', 'N/A')}
• Type: {report.get('type', 'N/A')}
• Period: {report.get('period', 'N/A')}
"""

        # Show summary metrics
        summary = report.get("summary", {})
        if summary:
            content += "\n[bold green]Summary Metrics:[/bold green]\n"
            for key, value in summary.items():
                content += f"• {key.replace('_', ' ').title()}: {value}\n"

        print_panel(self.console, content, border_style="green")

        # Show detailed sections if available
        sections = report.get("sections", [])
        if sections:
            for section in sections[:3]:  # Show first 3 sections
                section_title = section.get("title", "Section")
                section_content = section.get("content", "")

                if len(section_content) > 200:
                    section_content = section_content[:197] + "..."

                self.console.print(f"\n[bold]{section_title}:[/bold]")
                self.console.print(section_content)

    async def specialized_reports_menu(self):
        """Specialized reports submenu."""
        while True:
            menu = create_menu_table("Specialized Reports", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Confluence Consolidation Report"),
                ("2", "Jira Staleness Report"),
                ("3", "Cross-System Consistency Report"),
                ("4", "Documentation Gap Analysis"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.confluence_consolidation_report()
            elif choice == "2":
                await self.jira_staleness_report()
            elif choice == "3":
                await self.cross_system_consistency_report()
            elif choice == "4":
                await self.documentation_gap_analysis()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def confluence_consolidation_report(self):
        """Generate Confluence consolidation report."""
        try:
            min_confidence = float(Prompt.ask("[bold cyan]Minimum confidence threshold (0.0-1.0)[/bold cyan]", default="0.0"))

            params = {"min_confidence": min_confidence}

            with self.console.status("[bold green]Generating Confluence consolidation report...[/bold green]") as status:
                response = await self.clients.get_json("analysis-service/reports/confluence/consolidation", params=params)

            if response:
                await self.display_consolidation_report(response, "Confluence Consolidation Report")
                self.console.print("[green]✅ Confluence consolidation report generated[/green]")
            else:
                self.console.print("[red]❌ Failed to generate Confluence consolidation report[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating Confluence consolidation report: {e}[/red]")

    async def display_consolidation_report(self, report: Dict[str, Any], title: str):
        """Display a consolidation report."""
        if not report:
            self.console.print(f"[yellow]{title}: No report data to display[/yellow]")
            return

        items = report.get("items", [])
        summary = report.get("summary", {})

        content = f"""
[bold]🔄 {title}[/bold]

[bold blue]Summary:[/bold blue]
• Total Potential Duplicates: {summary.get('total_duplicates', 0)}
• Potential Time Savings: {summary.get('potential_savings', 'N/A')}

[bold green]Consolidation Opportunities:[/bold green]
"""

        for item in items[:5]:  # Show first 5
            content += f"• {item.get('title', 'Unknown')}\n"
            content += f"  Confidence: {item.get('confidence', 0):.2f}\n"
            content += f"  Documents: {len(item.get('documents', []))}\n"
            content += f"  Recommendation: {item.get('recommendation', 'N/A')}\n\n"

        if len(items) > 5:
            content += f"[yellow]... and {len(items) - 5} more consolidation opportunities[/yellow]"

        print_panel(self.console, content, border_style="cyan")

    async def jira_staleness_report(self):
        """Generate Jira staleness report."""
        try:
            min_confidence = float(Prompt.ask("[bold cyan]Minimum confidence threshold (0.0-1.0)[/bold cyan]", default="0.0"))

            params = {"min_confidence": min_confidence}

            with self.console.status("[bold green]Generating Jira staleness report...[/bold green]") as status:
                response = await self.clients.get_json("analysis-service/reports/jira/staleness", params=params)

            if response:
                await self.display_staleness_report(response, "Jira Staleness Report")
                self.console.print("[green]✅ Jira staleness report generated[/green]")
            else:
                self.console.print("[red]❌ Failed to generate Jira staleness report[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating Jira staleness report: {e}[/red]")

    async def display_staleness_report(self, report: Dict[str, Any], title: str):
        """Display a staleness report."""
        if not report:
            self.console.print(f"[yellow]{title}: No report data to display[/yellow]")
            return

        items = report.get("items", [])

        content = f"""
[bold]⏰ {title}[/bold]

[bold blue]Stale Items Found:[/bold blue] {len(items)}

[bold yellow]Stale Tickets:[/bold yellow]
"""

        for item in items[:5]:  # Show first 5
            content += f"• {item.get('id', 'Unknown')}\n"
            content += f"  Confidence: {item.get('confidence', 0):.2f}\n"
            content += f"  Reason: {item.get('reason', 'N/A')}\n"
            content += f"  Last Activity: {item.get('last_activity', 'N/A')}\n"
            content += f"  Recommendation: {item.get('recommendation', 'N/A')}\n\n"

        if len(items) > 5:
            content += f"[yellow]... and {len(items) - 5} more stale items[/yellow]"

        print_panel(self.console, content, border_style="yellow")

    async def cross_system_consistency_report(self):
        """Generate cross-system consistency report."""
        try:
            self.console.print("[yellow]Cross-system consistency analysis would check consistency across Confluence and Jira[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating cross-system report: {e}[/red]")

    async def documentation_gap_analysis(self):
        """Perform documentation gap analysis."""
        try:
            self.console.print("[yellow]Documentation gap analysis would identify missing or incomplete documentation[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error performing gap analysis: {e}[/red]")

    async def integration_monitoring_menu(self):
        """Integration monitoring submenu."""
        while True:
            menu = create_menu_table("Integration Monitoring", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Check Integration Health"),
                ("2", "Test Service Connectivity"),
                ("3", "Monitor Cross-Service Dependencies"),
                ("4", "Integration Logs and Events"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.check_integration_health()
            elif choice == "2":
                await self.test_service_connectivity()
            elif choice == "3":
                await self.monitor_cross_service_dependencies()
            elif choice == "4":
                await self.integration_logs_and_events()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def check_integration_health(self):
        """Check integration health with other services."""
        try:
            with self.console.status("[bold green]Checking integration health...[/bold green]") as status:
                response = await self.clients.get_json("analysis-service/integration/health")

            if response:
                await self.display_integration_health(response)
                self.console.print("[green]✅ Integration health check completed[/green]")
            else:
                self.console.print("[red]❌ Failed to check integration health[/red]")

        except Exception as e:
            self.console.print(f"[red]Error checking integration health: {e}[/red]")

    async def display_integration_health(self, health_data: Dict[str, Any]):
        """Display integration health status."""
        content = f"""
[bold]🔗 Integration Health Status[/bold]

[bold blue]Analysis Service:[/bold blue] {health_data.get('analysis_service', 'unknown')}
"""

        integrations = health_data.get("integrations", {})
        if integrations:
            content += "\n[bold green]Service Integrations:[/bold green]\n"
            for service, status in integrations.items():
                status_color = "green" if status == "healthy" else "red" if status == "error" else "yellow"
                content += f"• [{status_color}]{service}[/{status_color}]: {status}\n"

        available_services = health_data.get("available_services", [])
        if available_services:
            content += "\n[bold cyan]Available Services:[/bold cyan]\n"
            for service in available_services:
                content += f"• {service}\n"

        print_panel(self.console, content, border_style="blue")

    async def test_service_connectivity(self):
        """Test connectivity to integrated services."""
        try:
            services_to_test = ["doc-store", "source-agent", "prompt-store", "interpreter", "orchestrator"]

            results = {}

            for service in services_to_test:
                self.console.print(f"[yellow]Testing connectivity to {service}...[/yellow]")

                try:
                    # Try to get health from each service
                    response = await self.clients.get_json(f"{service}/health")
                    results[service] = "connected" if response else "no_response"
                except Exception:
                    results[service] = "error"

                status_color = "green" if results[service] == "connected" else "red"
                self.console.print(f"[{status_color}]{service}: {results[service]}[/{status_color}]")

            # Display summary
            connected_count = sum(1 for status in results.values() if status == "connected")
            total_count = len(results)

            content = f"""
[bold]🌐 Service Connectivity Test Results[/bold]

[bold blue]Connectivity Summary:[/bold blue] {connected_count}/{total_count} services connected

[bold green]Connected Services:[/bold green]
"""

            for service, status in results.items():
                if status == "connected":
                    content += f"• ✅ {service}\n"

            if any(status != "connected" for status in results.values()):
                content += f"\n[bold red]Disconnected Services:[/bold red]\n"
                for service, status in results.items():
                    if status != "connected":
                        content += f"• ❌ {service}: {status}\n"

            print_panel(self.console, content, border_style="green" if connected_count == total_count else "yellow")

        except Exception as e:
            self.console.print(f"[red]Error testing service connectivity: {e}[/red]")

    async def monitor_cross_service_dependencies(self):
        """Monitor cross-service dependencies."""
        try:
            self.console.print("[yellow]Cross-service dependency monitoring would track service interactions[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring dependencies: {e}[/red]")

    async def integration_logs_and_events(self):
        """View integration logs and events."""
        try:
            self.console.print("[yellow]Integration logs would show cross-service communication events[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing integration logs: {e}[/red]")

    async def natural_language_analysis_menu(self):
        """Natural language analysis submenu."""
        while True:
            menu = create_menu_table("Natural Language Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Analyze with Natural Language Query"),
                ("2", "Interactive Analysis Session"),
                ("3", "Query History and Patterns"),
                ("4", "Analysis Intent Recognition"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.analyze_with_natural_language()
            elif choice == "2":
                await self.interactive_analysis_session()
            elif choice == "3":
                await self.query_history_and_patterns()
            elif choice == "4":
                await self.analysis_intent_recognition()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def analyze_with_natural_language(self):
        """Analyze documents using natural language queries."""
        try:
            query = Prompt.ask("[bold cyan]Enter natural language analysis query[/bold cyan]")

            if not query.strip():
                self.console.print("[yellow]Query cannot be empty[/yellow]")
                return

            analysis_request = {"query": query}

            with self.console.status(f"[bold green]Performing natural language analysis...[/bold green]") as status:
                response = await self.clients.post_json("analysis-service/integration/natural-language-analysis", analysis_request)

            if response:
                await self.display_natural_language_results(response, f"Analysis for: '{query}'")
                self.console.print("[green]✅ Natural language analysis completed[/green]")
            else:
                self.console.print("[red]❌ Failed to perform natural language analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error with natural language analysis: {e}[/red]")

    async def display_natural_language_results(self, results: Dict[str, Any], title: str):
        """Display natural language analysis results."""
        if not results:
            self.console.print(f"[yellow]{title}: No results to display[/yellow]")
            return

        content = f"""
[bold]🗣️ {title}[/bold]

[bold blue]Interpretation:[/bold blue] {results.get('interpretation', {}).get('intent', 'unknown')}
[bold blue]Confidence:[/bold blue] {results.get('interpretation', {}).get('confidence', 'N/A')}
[bold blue]Status:[/bold blue] {results.get('status', 'unknown')}
"""

        execution = results.get("execution", {})
        if execution:
            content += "\n[bold green]Execution Results:[/bold green]\n"
            content += f"• Status: {execution.get('status', 'N/A')}\n"
            findings_count = len(execution.get('findings', []))
            content += f"• Findings: {findings_count}\n"

        print_panel(self.console, content, border_style="magenta")

    async def interactive_analysis_session(self):
        """Start an interactive analysis session."""
        try:
            self.console.print("[yellow]Interactive analysis session would provide conversational document analysis[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error starting interactive session: {e}[/red]")

    async def query_history_and_patterns(self):
        """View query history and patterns."""
        try:
            self.console.print("[yellow]Query history would show past natural language analysis queries[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing query history: {e}[/red]")

    async def analysis_intent_recognition(self):
        """Demonstrate analysis intent recognition."""
        try:
            self.console.print("[yellow]Intent recognition would analyze and categorize analysis queries[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with intent recognition: {e}[/red]")

    async def prompt_based_analysis_menu(self):
        """Prompt-based analysis submenu."""
        while True:
            menu = create_menu_table("Prompt-Based Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Analyze with Prompt Template"),
                ("2", "Browse Available Prompt Categories"),
                ("3", "Custom Prompt Analysis"),
                ("4", "Prompt Performance Comparison"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.analyze_with_prompt_template()
            elif choice == "2":
                await self.browse_prompt_categories()
            elif choice == "3":
                await self.custom_prompt_analysis()
            elif choice == "4":
                await self.prompt_performance_comparison()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def analyze_with_prompt_template(self):
        """Analyze documents using a prompt template."""
        try:
            target_id = Prompt.ask("[bold cyan]Target document ID to analyze[/bold cyan]")
            category = Prompt.ask("[bold cyan]Prompt category[/bold cyan]")
            name = Prompt.ask("[bold cyan]Prompt name[/bold cyan]")

            if not all([target_id, category, name]):
                self.console.print("[yellow]All fields (target ID, category, name) are required[/yellow]")
                return

            # Optional variables
            variables_input = Prompt.ask("[bold cyan]Template variables (key=value,key2=value2)[/bold cyan]", default="")
            variables = {}
            if variables_input.strip():
                for pair in variables_input.split(","):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        variables[key.strip()] = value.strip()

            analysis_request = {
                "target_id": target_id,
                "prompt_category": category,
                "prompt_name": name,
                **variables
            }

            with self.console.status(f"[bold green]Analyzing with {category}.{name} prompt...[/bold green]") as status:
                response = await self.clients.post_json("analysis-service/integration/analyze-with-prompt", analysis_request)

            if response:
                await self.display_prompt_analysis_results(response, f"Prompt Analysis: {category}.{name}")
                self.console.print("[green]✅ Prompt-based analysis completed[/green]")
            else:
                self.console.print("[red]❌ Failed to perform prompt-based analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error with prompt-based analysis: {e}[/red]")

    async def display_prompt_analysis_results(self, results: Dict[str, Any], title: str):
        """Display prompt analysis results."""
        if not results:
            self.console.print(f"[yellow]{title}: No results to display[/yellow]")
            return

        content = f"""
[bold]📝 {title}[/bold]

[bold blue]Target ID:[/bold blue] {results.get('target_id', 'N/A')}
[bold blue]Prompt Used:[/bold blue] {results.get('analysis_type', 'N/A')}
[bold blue]Content Length:[/bold blue] {results.get('content_length', 0)} characters
[bold blue]Status:[/bold blue] {results.get('status', 'unknown')}
"""

        prompt_used = results.get("prompt_used", "")
        if prompt_used:
            if len(prompt_used) > 200:
                prompt_used = prompt_used[:197] + "..."
            content += f"\n[bold green]Prompt Preview:[/bold green]\n{prompt_used}"

        print_panel(self.console, content, border_style="cyan")

    async def browse_prompt_categories(self):
        """Browse available prompt categories."""
        try:
            with self.console.status("[bold green]Retrieving prompt categories...[/bold green]") as status:
                response = await self.clients.get_json("analysis-service/integration/prompts/categories")

            if response:
                categories = response.get("categories", [])

                if categories:
                    table = Table(title="Available Prompt Categories")
                    table.add_column("Category", style="cyan")
                    table.add_column("Prompts Available", style="green", justify="right")

                    for category in categories:
                        prompt_count = len(category.get("prompts", []))
                        table.add_row(category.get("name", "Unknown"), str(prompt_count))

                    self.console.print(table)

                    # Show details of a specific category
                    show_details = Confirm.ask("[bold cyan]Show details of a specific category?[/bold cyan]", default=False)

                    if show_details:
                        category_names = [cat.get("name") for cat in categories]
                        selected_category = Prompt.ask("[bold cyan]Select category[/bold cyan]", choices=category_names)

                        category_data = next((cat for cat in categories if cat.get("name") == selected_category), None)

                        if category_data:
                            prompts = category_data.get("prompts", [])
                            self.console.print(f"\n[bold]Prompts in {selected_category}:[/bold]")

                            for prompt in prompts[:5]:  # Show first 5
                                self.console.print(f"• {prompt.get('name', 'Unknown')}: {prompt.get('description', 'No description')}")
                else:
                    self.console.print("[yellow]No prompt categories available[/yellow]")
            else:
                self.console.print("[red]❌ Failed to retrieve prompt categories[/red]")

        except Exception as e:
            self.console.print(f"[red]Error browsing prompt categories: {e}[/red]")

    async def custom_prompt_analysis(self):
        """Perform custom prompt analysis."""
        try:
            self.console.print("[yellow]Custom prompt analysis would allow creating custom analysis prompts[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with custom prompt analysis: {e}[/red]")

    async def prompt_performance_comparison(self):
        """Compare performance of different prompts."""
        try:
            self.console.print("[yellow]Prompt performance comparison would analyze effectiveness of different prompts[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error comparing prompt performance: {e}[/red]")

    async def analysis_history_menu(self):
        """Analysis history submenu."""
        while True:
            menu = create_menu_table("Analysis History", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Recent Analyses"),
                ("2", "Search Analysis History"),
                ("3", "Analysis Performance Metrics"),
                ("4", "Export Analysis History"),
                ("5", "Clear Analysis History"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_recent_analyses()
            elif choice == "2":
                await self.search_analysis_history()
            elif choice == "3":
                await self.analysis_performance_metrics()
            elif choice == "4":
                await self.export_analysis_history()
            elif choice == "5":
                await self.clear_analysis_history()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_recent_analyses(self):
        """View recent analysis operations."""
        try:
            if not self.analysis_history:
                self.console.print("[yellow]No analysis history available[/yellow]")
                return

            limit = min(int(Prompt.ask("[bold cyan]Number of recent analyses to show[/bold cyan]", default="10")), len(self.analysis_history))

            recent_analyses = self.analysis_history[-limit:]

            table = Table(title=f"Recent Analyses (Last {limit})")
            table.add_column("Time", style="blue", no_wrap=True)
            table.add_column("Type", style="cyan")
            table.add_column("Target(s)", style="green")
            table.add_column("Status", style="yellow")

            for analysis in recent_analyses:
                timestamp = analysis.get("timestamp", "")
                if timestamp and len(timestamp) > 19:
                    timestamp = timestamp[11:19]  # Show just time part

                analysis_type = analysis.get("type", "unknown")
                target = analysis.get("target", analysis.get("targets", ["unknown"]))

                if isinstance(target, list):
                    target_display = f"{len(target)} docs" if len(target) > 1 else target[0] if target else "unknown"
                else:
                    target_display = str(target)[:30] + "..." if len(str(target)) > 30 else str(target)

                # Determine status from response
                response = analysis.get("response", {})
                status = "✅ Success" if response else "❌ Failed"

                table.add_row(timestamp, analysis_type, target_display, status)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error viewing recent analyses: {e}[/red]")

    async def search_analysis_history(self):
        """Search analysis history."""
        try:
            if not self.analysis_history:
                self.console.print("[yellow]No analysis history available[/yellow]")
                return

            search_term = Prompt.ask("[bold cyan]Search term (type, target, or content)[/bold cyan]")

            if not search_term.strip():
                self.console.print("[yellow]Search term cannot be empty[/yellow]")
                return

            matching_analyses = []

            for analysis in self.analysis_history:
                # Search in type, target, and response content
                searchable_text = f"{analysis.get('type', '')} {str(analysis.get('target', ''))} {str(analysis.get('targets', ''))} {str(analysis.get('response', ''))}"

                if search_term.lower() in searchable_text.lower():
                    matching_analyses.append(analysis)

            if matching_analyses:
                self.console.print(f"[green]Found {len(matching_analyses)} matching analyses[/green]")

                table = Table(title=f"Search Results for '{search_term}'")
                table.add_column("Time", style="blue", no_wrap=True)
                table.add_column("Type", style="cyan")
                table.add_column("Target", style="green")

                for analysis in matching_analyses[-10:]:  # Show last 10 matches
                    timestamp = analysis.get("timestamp", "")
                    if timestamp and len(timestamp) > 19:
                        timestamp = timestamp[11:19]

                    analysis_type = analysis.get("type", "unknown")
                    target = analysis.get("target", analysis.get("targets", ["unknown"]))

                    if isinstance(target, list):
                        target_display = f"{len(target)} docs" if len(target) > 1 else target[0] if target else "unknown"
                    else:
                        target_display = str(target)[:30] + "..." if len(str(target)) > 30 else str(target)

                    table.add_row(timestamp, analysis_type, target_display)

                self.console.print(table)
            else:
                self.console.print(f"[yellow]No analyses found matching '{search_term}'[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error searching analysis history: {e}[/red]")

    async def analysis_performance_metrics(self):
        """Show analysis performance metrics."""
        try:
            if not self.analysis_history:
                self.console.print("[yellow]No analysis history available for metrics[/yellow]")
                return

            # Calculate metrics
            total_analyses = len(self.analysis_history)
            successful_analyses = sum(1 for a in self.analysis_history if a.get("response"))

            analysis_types = defaultdict(int)
            targets_processed = 0

            for analysis in self.analysis_history:
                analysis_type = analysis.get("type", "unknown")
                analysis_types[analysis_type] += 1

                targets = analysis.get("targets", [])
                if isinstance(targets, list):
                    targets_processed += len(targets)
                else:
                    targets_processed += 1

            success_rate = (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0

            content = f"""
[bold]📊 Analysis Performance Metrics[/bold]

[bold blue]Overall Performance:[/bold blue]
• Total Analyses: {total_analyses}
• Success Rate: {success_rate:.1f}%
• Targets Processed: {targets_processed}

[bold green]Analysis Types:[/bold green]
"""

            for analysis_type, count in sorted(analysis_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_analyses) * 100
                content += f"• {analysis_type}: {count} ({percentage:.1f}%)\n"

            print_panel(self.console, content, border_style="blue")

        except Exception as e:
            self.console.print(f"[red]Error showing performance metrics: {e}[/red]")

    async def export_analysis_history(self):
        """Export analysis history to file."""
        try:
            if not self.analysis_history:
                self.console.print("[yellow]No analysis history to export[/yellow]")
                return

            file_path = Prompt.ask("[bold cyan]Export file path[/bold cyan]", default="analysis_history.json")

            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_analyses": len(self.analysis_history),
                "analyses": self.analysis_history
            }

            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            self.console.print(f"[green]✅ Exported {len(self.analysis_history)} analyses to {file_path}[/green]")

        except Exception as e:
            self.console.print(f"[red]Error exporting analysis history: {e}[/red]")

    async def clear_analysis_history(self):
        """Clear analysis history."""
        try:
            if not self.analysis_history:
                self.console.print("[yellow]No history to clear[/yellow]")
                return

            confirm = Confirm.ask(f"[bold red]Clear all {len(self.analysis_history)} analyses from history?[/bold red]", default=False)

            if confirm:
                self.analysis_history.clear()
                self.console.print("[green]✅ Analysis history cleared[/green]")
            else:
                self.console.print("[yellow]History clearing cancelled[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error clearing analysis history: {e}[/red]")

    async def analyze_document_from_cli(self, analysis_request: Dict[str, Any]):
        """Analyze documents for CLI usage."""
        try:
            with self.console.status("[bold green]Analyzing documents...[/bold green]") as status:
                response = await self.clients.post_json("analysis-service/analyze", analysis_request)

            if response:
                # Store in history
                analysis_record = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "cli_analysis",
                    "targets": analysis_request.get("targets", []),
                    "detectors": analysis_request.get("detectors", []),
                    "response": response
                }
                self.analysis_history.append(analysis_record)

                await self.display_analysis_results(response, "CLI Document Analysis")
                self.console.print("[green]✅ Document analysis completed[/green]")
            else:
                self.console.print("[red]❌ Failed to analyze documents[/red]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing documents: {e}[/red]")

    async def get_findings_from_cli(self, params: Dict[str, Any]):
        """Get analysis findings for CLI usage."""
        try:
            response = await self.clients.get_json("analysis-service/findings", params=params)

            if response and "findings" in response:
                findings = response["findings"]
                await self.display_findings(findings, f"CLI Findings Query ({len(findings)} found)")
            else:
                self.console.print("[yellow]No findings found matching criteria[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error retrieving findings: {e}[/red]")

    async def generate_report_from_cli(self, report_request: Dict[str, Any]):
        """Generate reports for CLI usage."""
        try:
            with self.console.status("[bold green]Generating report...[/bold green]") as status:
                response = await self.clients.post_json("analysis-service/reports/generate", report_request)

            if response:
                await self.display_report(response, f"CLI Generated Report ({report_request.get('type', 'unknown')})")
                self.console.print("[green]✅ Report generation completed[/green]")
            else:
                self.console.print("[red]❌ Failed to generate report[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating report: {e}[/red]")
