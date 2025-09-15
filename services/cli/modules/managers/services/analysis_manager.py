"""Analysis Manager module for CLI service.

Provides power-user operations for analysis service including
analysis runs, reports generation, findings management, and quality metrics.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from ...shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class AnalysisManager:
    """Manager for analysis service power-user operations."""

    def __init__(self, console: Console, clients, cache: Dict[str, Any] = None):
        self.console = console
        self.clients = clients
        self.cache = cache or {}

    async def analysis_reports_menu(self):
        """Main analysis and reports menu."""
        while True:
            menu = create_menu_table("Analysis & Reports", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Run Analysis (Quality, Consistency, Security)"),
                ("2", "View Analysis Findings"),
                ("3", "Generate Reports (Confluence, Jira, Custom)"),
                ("4", "Quality Metrics & Statistics"),
                ("5", "Analysis Detectors Management"),
                ("6", "Integration Analysis (Prompt-based)"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.run_analysis_menu()
            elif choice == "2":
                await self.view_findings_menu()
            elif choice == "3":
                await self.generate_reports_menu()
            elif choice == "4":
                await self.quality_metrics_menu()
            elif choice == "5":
                await self.detectors_management_menu()
            elif choice == "6":
                await self.integration_analysis_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def run_analysis_menu(self):
        """Run analysis submenu."""
        while True:
            menu = create_menu_table("Run Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Quality Analysis"),
                ("2", "Consistency Analysis"),
                ("3", "Security Analysis"),
                ("4", "Custom Analysis"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.run_quality_analysis()
            elif choice == "2":
                await self.run_consistency_analysis()
            elif choice == "3":
                await self.run_security_analysis()
            elif choice == "4":
                await self.run_custom_analysis()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def run_quality_analysis(self):
        """Run quality analysis."""
        try:
            target = Prompt.ask("[bold cyan]Analysis target[/bold cyan]",
                              choices=["documents", "prompts", "all"], default="all")

            with self.console.status(f"[bold green]Running quality analysis on {target}...") as status:
                response = await self.clients.post_json("analysis-service/analyze", {
                    "type": "quality",
                    "target": target
                })

            if response.get("analysis_id"):
                self.console.print(f"[green]✅ Quality analysis started: {response['analysis_id']}[/green]")
                await self.monitor_analysis(response["analysis_id"])
            else:
                self.console.print("[red]❌ Failed to start quality analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error running quality analysis: {e}[/red]")

    async def run_consistency_analysis(self):
        """Run consistency analysis."""
        try:
            scope = Prompt.ask("[bold cyan]Analysis scope[/bold cyan]",
                             choices=["documents", "workflows", "all"], default="all")

            with self.console.status(f"[bold green]Running consistency analysis on {scope}...") as status:
                response = await self.clients.post_json("analysis-service/analyze", {
                    "type": "consistency",
                    "scope": scope
                })

            if response.get("analysis_id"):
                self.console.print(f"[green]✅ Consistency analysis started: {response['analysis_id']}[/green]")
                await self.monitor_analysis(response["analysis_id"])
            else:
                self.console.print("[red]❌ Failed to start consistency analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error running consistency analysis: {e}[/red]")

    async def run_security_analysis(self):
        """Run security analysis."""
        try:
            target_type = Prompt.ask("[bold cyan]Target type[/bold cyan]",
                                   choices=["documents", "prompts", "code", "all"], default="all")

            with self.console.status(f"[bold green]Running security analysis on {target_type}...") as status:
                response = await self.clients.post_json("analysis-service/analyze", {
                    "type": "security",
                    "target_type": target_type
                })

            if response.get("analysis_id"):
                self.console.print(f"[green]✅ Security analysis started: {response['analysis_id']}[/green]")
                await self.monitor_analysis(response["analysis_id"])
            else:
                self.console.print("[red]❌ Failed to start security analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error running security analysis: {e}[/red]")

    async def run_custom_analysis(self):
        """Run custom analysis."""
        try:
            analysis_type = Prompt.ask("[bold cyan]Analysis type[/bold cyan]")
            parameters = Prompt.ask("[bold cyan]Parameters (JSON)[/bold cyan]", default="{}")

            import json
            params = json.loads(parameters)

            with self.console.status(f"[bold green]Running custom {analysis_type} analysis...") as status:
                response = await self.clients.post_json("analysis-service/analyze", {
                    "type": analysis_type,
                    **params
                })

            if response.get("analysis_id"):
                self.console.print(f"[green]✅ Custom analysis started: {response['analysis_id']}[/green]")
                await self.monitor_analysis(response["analysis_id"])
            else:
                self.console.print("[red]❌ Failed to start custom analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error running custom analysis: {e}[/red]")

    async def monitor_analysis(self, analysis_id: str):
        """Monitor analysis progress."""
        try:
            import asyncio

            self.console.print(f"[yellow]Monitoring analysis {analysis_id}...[/yellow]")

            while True:
                await asyncio.sleep(2)

                try:
                    response = await self.clients.get_json(f"analysis-service/analysis/{analysis_id}")

                    if response.get("completed"):
                        status = response.get("status", "unknown")
                        if status == "success":
                            self.console.print(f"[green]✅ Analysis {analysis_id} completed successfully![/green]")
                        else:
                            self.console.print(f"[red]❌ Analysis {analysis_id} failed: {response.get('error', 'Unknown error')}[/red]")
                        break
                    else:
                        progress = response.get("progress", 0)
                        current_step = response.get("current_step", "processing")
                        self.console.print(f"[yellow]⏳ Progress: {progress}% - {current_step}[/yellow]")

                except KeyboardInterrupt:
                    self.console.print("[yellow]Stopped monitoring analysis.[/yellow]")
                    break
                except Exception as e:
                    self.console.print(f"[red]Error monitoring analysis: {e}[/red]")
                    break

        except Exception as e:
            self.console.print(f"[red]Error monitoring analysis: {e}[/red]")

    async def view_findings_menu(self):
        """View findings submenu."""
        while True:
            menu = create_menu_table("Analysis Findings", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View All Findings"),
                ("2", "Filter by Severity"),
                ("3", "Filter by Type"),
                ("4", "Search Findings"),
                ("5", "Export Findings"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_all_findings()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.filter_findings_by_severity()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.filter_findings_by_type()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                await self.search_findings()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "5":
                await self.export_findings()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_all_findings(self):
        """View all findings."""
        try:
            with self.console.status("[bold green]Fetching findings...") as status:
                response = await self.clients.get_json("analysis-service/findings")

            if response.get("findings"):
                table = Table(title="Analysis Findings")
                table.add_column("ID", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Severity", style="red")
                table.add_column("Title", style="white")
                table.add_column("Target", style="yellow")

                for finding in response["findings"][:20]:  # Show first 20
                    severity_color = {
                        "critical": "red",
                        "high": "red",
                        "medium": "yellow",
                        "low": "green",
                        "info": "blue"
                    }.get(finding.get("severity", "unknown"), "white")

                    table.add_row(
                        finding.get("id", "N/A")[:8],
                        finding.get("type", "unknown"),
                        f"[{severity_color}]{finding.get('severity', 'unknown')}[/{severity_color}]",
                        finding.get("title", "No title")[:50],
                        finding.get("target", "unknown")[:30]
                    )

                self.console.print(table)
                self.console.print(f"[dim]Showing {min(20, len(response['findings']))} of {len(response['findings'])} findings[/dim]")
            else:
                self.console.print("[yellow]No findings found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching findings: {e}[/red]")

    async def filter_findings_by_severity(self):
        """Filter findings by severity."""
        try:
            severity = Prompt.ask("[bold cyan]Severity level[/bold cyan]",
                                choices=["critical", "high", "medium", "low", "info"])

            with self.console.status(f"[bold green]Fetching {severity} severity findings...") as status:
                response = await self.clients.get_json(f"analysis-service/findings?severity={severity}")

            if response.get("findings"):
                self.display_findings_table(response["findings"], f"{severity.title()} Severity Findings")
            else:
                self.console.print(f"[yellow]No {severity} severity findings found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error filtering findings by severity: {e}[/red]")

    async def filter_findings_by_type(self):
        """Filter findings by type."""
        try:
            finding_type = Prompt.ask("[bold cyan]Finding type[/bold cyan]")

            with self.console.status(f"[bold green]Fetching {finding_type} findings...") as status:
                response = await self.clients.get_json(f"analysis-service/findings?type={finding_type}")

            if response.get("findings"):
                self.display_findings_table(response["findings"], f"{finding_type.title()} Findings")
            else:
                self.console.print(f"[yellow]No {finding_type} findings found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error filtering findings by type: {e}[/red]")

    async def search_findings(self):
        """Search findings."""
        try:
            query = Prompt.ask("[bold cyan]Search query[/bold cyan]")

            with self.console.status(f"[bold green]Searching findings for '{query}'...") as status:
                response = await self.clients.get_json(f"analysis-service/findings?search={query}")

            if response.get("findings"):
                self.display_findings_table(response["findings"], f"Search Results for '{query}'")
            else:
                self.console.print(f"[yellow]No findings found for '{query}'.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error searching findings: {e}[/red]")

    def display_findings_table(self, findings: List[Dict], title: str):
        """Display findings in a table format."""
        table = Table(title=title)
        table.add_column("ID", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Severity", style="red")
        table.add_column("Title", style="white")
        table.add_column("Description", style="dim white")

        for finding in findings[:15]:  # Show first 15
            severity_color = {
                "critical": "red",
                "high": "red",
                "medium": "yellow",
                "low": "green",
                "info": "blue"
            }.get(finding.get("severity", "unknown"), "white")

            table.add_row(
                finding.get("id", "N/A")[:8],
                finding.get("type", "unknown"),
                f"[{severity_color}]{finding.get('severity', 'unknown')}[/{severity_color}]",
                finding.get("title", "No title")[:40],
                finding.get("description", "No description")[:50]
            )

        self.console.print(table)

    async def export_findings(self):
        """Export findings."""
        try:
            export_format = Prompt.ask("[bold cyan]Export format[/bold cyan]",
                                     choices=["json", "csv", "html"], default="json")
            filename = Prompt.ask("[bold cyan]Filename[/bold cyan]", default=f"findings.{export_format}")

            with self.console.status(f"[bold green]Exporting findings to {filename}...") as status:
                response = await self.clients.get_json(f"analysis-service/findings?export={export_format}")

            if response.get("exported"):
                self.console.print(f"[green]✅ Findings exported to {filename}[/green]")
            else:
                self.console.print("[red]❌ Failed to export findings[/red]")

        except Exception as e:
            self.console.print(f"[red]Error exporting findings: {e}[/red]")

    async def generate_reports_menu(self):
        """Generate reports submenu."""
        while True:
            menu = create_menu_table("Report Generation", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Confluence Consolidation Report"),
                ("2", "Jira Staleness Report"),
                ("3", "Findings Report"),
                ("4", "Quality Metrics Report"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.generate_confluence_report()
            elif choice == "2":
                await self.generate_jira_staleness_report()
            elif choice == "3":
                await self.generate_findings_report()
            elif choice == "4":
                await self.generate_quality_report()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def generate_confluence_report(self):
        """Generate Confluence consolidation report."""
        try:
            with self.console.status("[bold green]Generating Confluence consolidation report...") as status:
                response = await self.clients.get_json("analysis-service/reports/confluence/consolidation")

            if response.get("report"):
                report = response["report"]
                content = f"""
[bold]Confluence Consolidation Report[/bold]

Total Pages: {report.get('total_pages', 0)}
Consolidated Pages: {report.get('consolidated_pages', 0)}
Duplicate Clusters: {report.get('duplicate_clusters', 0)}
Space Optimization: {report.get('space_saved_mb', 0)} MB

Generated: {report.get('generated_at', 'unknown')}
"""
                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[red]❌ Failed to generate Confluence report[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating Confluence report: {e}[/red]")

    async def generate_jira_staleness_report(self):
        """Generate Jira staleness report."""
        try:
            with self.console.status("[bold green]Generating Jira staleness report...") as status:
                response = await self.clients.get_json("analysis-service/reports/jira/staleness")

            if response.get("report"):
                report = response["report"]
                content = f"""
[bold]Jira Staleness Report[/bold]

Total Tickets: {report.get('total_tickets', 0)}
Stale Tickets: {report.get('stale_tickets', 0)}
Average Age: {report.get('avg_age_days', 0)} days
Critical Stale: {report.get('critical_stale', 0)}

Generated: {report.get('generated_at', 'unknown')}
"""
                print_panel(self.console, content, border_style="orange")
            else:
                self.console.print("[red]❌ Failed to generate Jira staleness report[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating Jira staleness report: {e}[/red]")

    async def generate_findings_report(self):
        """Generate findings report."""
        try:
            report_type = Prompt.ask("[bold cyan]Report type[/bold cyan]",
                                   choices=["summary", "detailed", "trends"], default="summary")

            with self.console.status(f"[bold green]Generating {report_type} findings report...") as status:
                response = await self.clients.post_json("analysis-service/reports/generate", {
                    "type": "findings",
                    "format": report_type
                })

            if response.get("report_id"):
                self.console.print(f"[green]✅ Findings report generated: {response['report_id']}[/green]")
            else:
                self.console.print("[red]❌ Failed to generate findings report[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating findings report: {e}[/red]")

    async def generate_quality_report(self):
        """Generate quality metrics report."""
        try:
            with self.console.status("[bold green]Generating quality metrics report...") as status:
                response = await self.clients.post_json("analysis-service/reports/generate", {
                    "type": "quality"
                })

            if response.get("report_id"):
                self.console.print(f"[green]✅ Quality metrics report generated: {response['report_id']}[/green]")
            else:
                self.console.print("[red]❌ Failed to generate quality report[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating quality report: {e}[/red]")

    async def quality_metrics_menu(self):
        """Quality metrics submenu."""
        while True:
            menu = create_menu_table("Quality Metrics", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Overall Quality Scores"),
                ("2", "Document Quality Trends"),
                ("3", "Prompt Quality Metrics"),
                ("4", "Quality Improvement Recommendations"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_overall_quality()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.view_document_quality_trends()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.view_prompt_quality_metrics()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                await self.view_quality_recommendations()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_overall_quality(self):
        """View overall quality scores."""
        try:
            with self.console.status("[bold green]Fetching quality metrics...") as status:
                response = await self.clients.get_json("analysis-service/quality/metrics")

            if response.get("metrics"):
                metrics = response["metrics"]
                content = f"""
[bold]Overall Quality Metrics[/bold]

Average Document Quality: {metrics.get('avg_doc_quality', 0):.2f}/10
Average Prompt Quality: {metrics.get('avg_prompt_quality', 0):.2f}/10
Overall System Quality: {metrics.get('overall_quality', 0):.2f}/10

Documents Analyzed: {metrics.get('total_documents', 0)}
Prompts Analyzed: {metrics.get('total_prompts', 0)}

Quality Distribution:
  High (8-10): {metrics.get('quality_distribution', {}).get('high', 0)} items
  Medium (5-7): {metrics.get('quality_distribution', {}).get('medium', 0)} items
  Low (0-4): {metrics.get('quality_distribution', {}).get('low', 0)} items
"""
                print_panel(self.console, content, border_style="green")
            else:
                self.console.print("[yellow]No quality metrics available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching quality metrics: {e}[/red]")

    async def view_document_quality_trends(self):
        """View document quality trends."""
        try:
            with self.console.status("[bold green]Fetching document quality trends...") as status:
                response = await self.clients.get_json("analysis-service/quality/trends?type=document")

            if response.get("trends"):
                trends = response["trends"]
                content = f"""
[bold]Document Quality Trends[/bold]

Current Average: {trends.get('current_avg', 0):.2f}
Trend Direction: {trends.get('trend', 'stable')}
Change (30 days): {trends.get('change_30d', 0):+.2f}

Quality Improvement Areas:
"""
                if trends.get("improvement_areas"):
                    for area in trends["improvement_areas"][:5]:
                        content += f"  • {area.get('area', 'Unknown')}: {area.get('impact', 'unknown')}\n"

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]No document quality trends available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching document quality trends: {e}[/red]")

    async def view_prompt_quality_metrics(self):
        """View prompt quality metrics."""
        try:
            with self.console.status("[bold green]Fetching prompt quality metrics...") as status:
                response = await self.clients.get_json("analysis-service/quality/prompts")

            if response.get("metrics"):
                metrics = response["metrics"]
                content = f"""
[bold]Prompt Quality Metrics[/bold]

Average Quality Score: {metrics.get('avg_quality', 0):.2f}/10
Total Prompts: {metrics.get('total_prompts', 0)}
High-Quality Prompts: {metrics.get('high_quality_count', 0)}

Category Breakdown:
"""
                if metrics.get("by_category"):
                    for category, score in metrics["by_category"].items():
                        content += f"  {category}: {score:.2f}/10\n"

                print_panel(self.console, content, border_style="cyan")
            else:
                self.console.print("[yellow]No prompt quality metrics available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching prompt quality metrics: {e}[/red]")

    async def view_quality_recommendations(self):
        """View quality improvement recommendations."""
        try:
            with self.console.status("[bold green]Fetching quality recommendations...") as status:
                response = await self.clients.get_json("analysis-service/quality/recommendations")

            if response.get("recommendations"):
                recommendations = response["recommendations"]
                content = "[bold]Quality Improvement Recommendations[/bold]\n\n"

                for rec in recommendations[:10]:  # Show top 10
                    content += f"[bold]{rec.get('priority', 'medium').title()} Priority:[/bold]\n"
                    content += f"  {rec.get('recommendation', 'No recommendation')}\n"
                    content += f"  [dim]Impact: {rec.get('impact', 'unknown')} | Effort: {rec.get('effort', 'unknown')}[/dim]\n\n"

                print_panel(self.console, content, border_style="yellow")
            else:
                self.console.print("[yellow]No quality recommendations available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching quality recommendations: {e}[/red]")

    async def detectors_management_menu(self):
        """Detectors management submenu."""
        while True:
            menu = create_menu_table("Analysis Detectors", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "List Available Detectors"),
                ("2", "View Detector Details"),
                ("3", "Enable/Disable Detectors"),
                ("4", "Detector Performance Stats"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.list_detectors()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.view_detector_details()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.toggle_detector()
            elif choice == "4":
                await self.detector_performance_stats()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def list_detectors(self):
        """List available detectors."""
        try:
            with self.console.status("[bold green]Fetching detectors...") as status:
                response = await self.clients.get_json("analysis-service/detectors")

            if response.get("detectors"):
                table = Table(title="Available Detectors")
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Description", style="white")

                for detector in response["detectors"]:
                    status_color = "green" if detector.get("enabled") else "red"
                    table.add_row(
                        detector.get("name", "unknown"),
                        detector.get("type", "unknown"),
                        f"[{status_color}]{'Enabled' if detector.get('enabled') else 'Disabled'}[/{status_color}]",
                        detector.get("description", "No description")[:50]
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No detectors available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching detectors: {e}[/red]")

    async def view_detector_details(self):
        """View detector details."""
        try:
            detector_name = Prompt.ask("[bold cyan]Detector name[/bold cyan]")

            with self.console.status(f"[bold green]Fetching details for {detector_name}...") as status:
                response = await self.clients.get_json(f"analysis-service/detectors/{detector_name}")

            if response.get("detector"):
                detector = response["detector"]
                content = f"""
[bold]Detector Details: {detector_name}[/bold]

Type: {detector.get('type', 'unknown')}
Status: {'Enabled' if detector.get('enabled') else 'Disabled'}
Version: {detector.get('version', 'unknown')}

Description: {detector.get('description', 'No description')}

Capabilities: {', '.join(detector.get('capabilities', []))}

Performance:
  Accuracy: {detector.get('performance', {}).get('accuracy', 'unknown')}
  Speed: {detector.get('performance', {}).get('speed', 'unknown')} items/sec
  Last Run: {detector.get('last_run', 'never')}
"""
                print_panel(self.console, content, border_style="cyan")
            else:
                self.console.print("[red]Detector not found.[/red]")

        except Exception as e:
            self.console.print(f"[red]Error fetching detector details: {e}[/red]")

    async def toggle_detector(self):
        """Enable/disable detector."""
        try:
            detector_name = Prompt.ask("[bold cyan]Detector name[/bold cyan]")
            action = Prompt.ask("[bold cyan]Action[/bold cyan]", choices=["enable", "disable"])

            with self.console.status(f"[bold green]{action.title()}ing detector {detector_name}...") as status:
                response = await self.clients.post_json(f"analysis-service/detectors/{detector_name}/{action}", {})

            if response.get("success"):
                self.console.print(f"[green]✅ Detector {detector_name} {action}d successfully[/green]")
            else:
                self.console.print(f"[red]❌ Failed to {action} detector {detector_name}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error toggling detector: {e}[/red]")

    async def detector_performance_stats(self):
        """View detector performance statistics."""
        try:
            with self.console.status("[bold green]Fetching detector performance stats...") as status:
                response = await self.clients.get_json("analysis-service/detectors/performance")

            if response.get("stats"):
                table = Table(title="Detector Performance Statistics")
                table.add_column("Detector", style="cyan")
                table.add_column("Runs", style="green")
                table.add_column("Avg Time", style="yellow")
                table.add_column("Success Rate", style="white")
                table.add_column("Findings", style="magenta")

                for stat in response["stats"]:
                    success_rate = f"{stat.get('success_rate', 0):.1f}%"
                    avg_time = f"{stat.get('avg_execution_time', 0):.2f}s"

                    table.add_row(
                        stat.get("detector_name", "unknown"),
                        str(stat.get("total_runs", 0)),
                        avg_time,
                        success_rate,
                        str(stat.get("total_findings", 0))
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No detector performance stats available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching detector performance stats: {e}[/red]")

    async def integration_analysis_menu(self):
        """Integration analysis submenu."""
        while True:
            menu = create_menu_table("Integration Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Natural Language Analysis"),
                ("2", "Prompt-Based Analysis"),
                ("3", "Log Analysis"),
                ("4", "Available Prompt Categories"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.natural_language_analysis()
            elif choice == "2":
                await self.prompt_based_analysis()
            elif choice == "3":
                await self.log_analysis()
            elif choice == "4":
                await self.view_prompt_categories()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def natural_language_analysis(self):
        """Run natural language analysis."""
        try:
            query = Prompt.ask("[bold cyan]Analysis query[/bold cyan]")
            context = Prompt.ask("[bold cyan]Context (optional)[/bold cyan]", default="")

            with self.console.status("[bold green]Running natural language analysis...") as status:
                response = await self.clients.post_json("analysis-service/integration/natural-language-analysis", {
                    "query": query,
                    "context": context
                })

            if response.get("analysis"):
                analysis = response["analysis"]
                content = f"""
[bold]Natural Language Analysis Results[/bold]

Query: {query}

Analysis Type: {analysis.get('type', 'unknown')}
Confidence: {analysis.get('confidence', 0):.2f}

Key Insights:
"""
                if analysis.get("insights"):
                    for insight in analysis["insights"]:
                        content += f"  • {insight}\n"

                content += f"\nRecommendations:\n"
                if analysis.get("recommendations"):
                    for rec in analysis["recommendations"]:
                        content += f"  • {rec}\n"

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[red]❌ Failed to run natural language analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error running natural language analysis: {e}[/red]")

    async def prompt_based_analysis(self):
        """Run prompt-based analysis."""
        try:
            prompt_category = Prompt.ask("[bold cyan]Prompt category[/bold cyan]")
            target_content = Prompt.ask("[bold cyan]Target content[/bold cyan]")

            with self.console.status(f"[bold green]Running {prompt_category} analysis...") as status:
                response = await self.clients.post_json("analysis-service/integration/analyze-with-prompt", {
                    "prompt_category": prompt_category,
                    "target_content": target_content
                })

            if response.get("result"):
                result = response["result"]
                content = f"""
[bold]Prompt-Based Analysis Results[/bold]

Category: {prompt_category}
Analysis Score: {result.get('score', 0):.2f}/10

Analysis: {result.get('analysis', 'No analysis available')}

Recommendations:
"""
                if result.get("recommendations"):
                    for rec in result["recommendations"]:
                        content += f"  • {rec}\n"

                print_panel(self.console, content, border_style="green")
            else:
                self.console.print("[red]❌ Failed to run prompt-based analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error running prompt-based analysis: {e}[/red]")

    async def log_analysis(self):
        """Run log analysis."""
        try:
            log_content = Prompt.ask("[bold cyan]Log content to analyze[/bold cyan]")

            with self.console.status("[bold green]Running log analysis...") as status:
                response = await self.clients.post_json("analysis-service/integration/log-analysis", {
                    "log_content": log_content
                })

            if response.get("analysis"):
                analysis = response["analysis"]
                content = f"""
[bold]Log Analysis Results[/bold]

Issues Found: {analysis.get('issues_count', 0)}
Error Patterns: {analysis.get('error_patterns', 0)}
Warning Patterns: {analysis.get('warning_patterns', 0)}

Key Findings:
"""
                if analysis.get("findings"):
                    for finding in analysis["findings"][:10]:  # Show first 10
                        content += f"  • {finding.get('type', 'unknown')}: {finding.get('description', 'No description')}\n"

                print_panel(self.console, content, border_style="red")
            else:
                self.console.print("[red]❌ Failed to run log analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error running log analysis: {e}[/red]")

    async def view_prompt_categories(self):
        """View available prompt categories."""
        try:
            with self.console.status("[bold green]Fetching prompt categories...") as status:
                response = await self.clients.get_json("analysis-service/integration/prompts/categories")

            if response.get("categories"):
                table = Table(title="Available Prompt Categories")
                table.add_column("Category", style="cyan")
                table.add_column("Description", style="white")
                table.add_column("Prompts Available", style="green")

                for category in response["categories"]:
                    table.add_row(
                        category.get("name", "unknown"),
                        category.get("description", "No description")[:50],
                        str(category.get("prompt_count", 0))
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No prompt categories available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching prompt categories: {e}[/red]")
