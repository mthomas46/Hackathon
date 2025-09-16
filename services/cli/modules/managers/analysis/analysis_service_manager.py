"""Analysis Service Manager for CLI operations."""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.prompt import Prompt

from ...base.base_manager import BaseManager
from .document_analysis_manager import DocumentAnalysisManager


class AnalysisServiceManager(BaseManager):
    """Main analysis service manager coordinating all analysis operations."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

        # Initialize specialized managers
        self.document_analysis = DocumentAnalysisManager(console, clients, cache)

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return analysis service main menu."""
        return [
            ("1", "Document Analysis (Single, Multiple, By Source)"),
            ("2", "Findings Management (View, Filter, Search)"),
            ("3", "Report Generation (Summary, Trends, Quality)"),
            ("4", "Analysis Configuration (Detectors, Templates)"),
            ("5", "Integration Analysis (Cross-service)"),
            ("b", "Back to Main Menu")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle menu choice."""
        if choice == "1":
            await self.document_analysis.run_menu_loop("Document Analysis")
        elif choice == "2":
            await self.findings_management_menu()
        elif choice == "3":
            await self.report_generation_menu()
        elif choice == "4":
            await self.analysis_configuration_menu()
        elif choice == "5":
            await self.integration_analysis_menu()
        else:
            return False

        return True

    async def findings_management_menu(self):
        """Findings management submenu."""
        self.display.show_info("Findings management feature coming soon!")
        self.display.show_info("This will include viewing, filtering, and managing analysis findings")
        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    async def report_generation_menu(self):
        """Report generation submenu."""
        self.display.show_info("Report generation feature coming soon!")
        self.display.show_info("This will include generating analysis reports and summaries")
        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    async def analysis_configuration_menu(self):
        """Analysis configuration submenu."""
        self.display.show_info("Analysis configuration feature coming soon!")
        self.display.show_info("This will include detector and analysis template configuration")
        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    async def integration_analysis_menu(self):
        """Integration analysis submenu."""
        self.display.show_info("Integration analysis feature coming soon!")
        self.display.show_info("This will include cross-service integration analysis")
        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    # CLI integration methods for backward compatibility
    async def analyze_document_from_cli(self, analysis_request: Dict[str, Any]):
        """Analyze document for CLI integration."""
        try:
            response = await self.clients.post_json("analysis-service/analyze", analysis_request)

            if response.get("success"):
                results = response.get("results", [])
                if results:
                    # Display summary
                    total_findings = sum(len(r.get("findings", [])) for r in results)
                    self.display.show_success(f"Analysis completed: {total_findings} findings across {len(results)} targets")

                    # Show findings by severity
                    severity_counts = {}
                    for result in results:
                        for finding in result.get("findings", []):
                            severity = finding.get("severity", "info")
                            severity_counts[severity] = severity_counts.get(severity, 0) + 1

                    if severity_counts:
                        severity_data = []
                        for severity, count in severity_counts.items():
                            severity_data.append([severity.upper(), str(count)])

                        self.display.show_table("Findings by Severity", ["Severity", "Count"], severity_data)
                else:
                    self.display.show_info("No analysis results found")
            else:
                self.display.show_error(f"Analysis failed: {response.get('message', 'Unknown error')}")

        except Exception as e:
            self.display.show_error(f"Error analyzing document: {e}")

    async def get_findings_from_cli(self, params: Dict[str, Any]):
        """Get findings for CLI integration."""
        try:
            query_params = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"analysis-service/findings?{query_params}"

            response = await self.clients.get_json(url)

            if response.get("success"):
                findings = response.get("findings", [])
                if findings:
                    # Display findings summary
                    self.display.show_info(f"Found {len(findings)} findings")

                    # Show first few findings
                    findings_data = []
                    for finding in findings[:10]:  # Show first 10
                        findings_data.append([
                            finding.get("document_id", "")[:20],
                            finding.get("type", ""),
                            finding.get("severity", "").upper(),
                            finding.get("description", "")[:50]
                        ])

                    self.display.show_table(
                        "Analysis Findings",
                        ["Document", "Type", "Severity", "Description"],
                        findings_data
                    )

                    if len(findings) > 10:
                        self.display.show_info(f"... and {len(findings) - 10} more findings")
                else:
                    self.display.show_info("No findings found matching criteria")
            else:
                self.display.show_error(f"Failed to get findings: {response.get('message', 'Unknown error')}")

        except Exception as e:
            self.display.show_error(f"Error getting findings: {e}")

    async def generate_report_from_cli(self, report_request: Dict[str, Any]):
        """Generate report for CLI integration."""
        try:
            response = await self.clients.post_json("analysis-service/reports/generate", report_request)

            if response.get("success"):
                report_data = response.get("report", {})
                report_type = report_request.get("type", "unknown")

                self.display.show_success(f"{report_type.title()} report generated successfully")

                # Show report summary
                if report_type == "summary":
                    summary = report_data.get("summary", {})
                    self.display.show_info(f"Total documents: {summary.get('total_documents', 0)}")
                    self.display.show_info(f"Total findings: {summary.get('total_findings', 0)}")
                    self.display.show_info(f"Documents analyzed: {summary.get('analyzed_documents', 0)}")

                elif report_type == "trends":
                    trends = report_data.get("trends", {})
                    self.display.show_info(f"Analysis period: {trends.get('period', 'Unknown')}")
                    self.display.show_info(f"Trend direction: {trends.get('direction', 'Unknown')}")

                elif report_type == "quality":
                    quality = report_data.get("quality", {})
                    self.display.show_info(f"Average quality score: {quality.get('average_score', 0):.2f}")
                    self.display.show_info(f"Quality threshold: {quality.get('threshold', 0)}")

                # Offer to save report
                if await self.confirm_action("Save report to file?"):
                    filename = await self.get_user_input("Report filename", default=f"analysis_report_{report_type}.json")
                    if filename:
                        import json
                        with open(filename, 'w') as f:
                            json.dump(report_data, f, indent=2, default=str)
                        self.display.show_success(f"Report saved to {filename}")

            else:
                self.display.show_error(f"Report generation failed: {response.get('message', 'Unknown error')}")

        except Exception as e:
            self.display.show_error(f"Error generating report: {e}")
