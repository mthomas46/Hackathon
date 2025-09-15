"""Document Analysis Manager for CLI operations."""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm

from ...base.base_manager import BaseManager
from ...formatters.display_utils import DisplayManager


class DocumentAnalysisManager(BaseManager):
    """Manager for document analysis operations."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return document analysis menu."""
        return [
            ("1", "Analyze Single Document"),
            ("2", "Analyze Multiple Documents"),
            ("3", "Analyze by Source Type"),
            ("4", "Configure Analysis Detectors"),
            ("5", "Analysis Templates"),
            ("b", "Back to Analysis & Reports")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle menu choice."""
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
        else:
            return False

        if choice in ["1", "2", "3"]:  # Choices that show results
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        return True

    async def analyze_single_document(self):
        """Analyze a single document."""
        try:
            doc_id = await self.get_user_input("Document ID to analyze")

            if not doc_id:
                return

            # Get available detectors
            detectors = await self._get_available_detectors()
            detector_choices = list(detectors.keys())

            selected_detectors = await self._select_multiple_detectors(detector_choices)
            if not selected_detectors:
                selected_detectors = detector_choices  # Use all if none selected

            # Perform analysis
            analysis_request = {
                "targets": [doc_id],
                "detectors": selected_detectors
            }

            with self.console.status("[bold green]Analyzing document...") as status:
                response = await self.clients.post_json("analysis-service/analyze", analysis_request)

            if response.get("success"):
                results = response.get("results", [])
                if results:
                    await self.display_analysis_results(results, f"Analysis Results for Document {doc_id}")
                else:
                    self.display.show_info("No analysis results found")
            else:
                self.display.show_error(f"Analysis failed: {response.get('message', 'Unknown error')}")

        except Exception as e:
            self.display.show_error(f"Error analyzing document: {e}")

    async def analyze_multiple_documents(self):
        """Analyze multiple documents."""
        try:
            # Get document selection criteria
            criteria_input = await self.get_user_input("Selection criteria (JSON format)", default='{"limit": 10}')

            try:
                criteria = eval(criteria_input) if criteria_input else {"limit": 10}
            except:
                criteria = {"limit": 10}

            # Confirm analysis
            doc_count = criteria.get("limit", "unknown")
            if not await self.confirm_action(f"Analyze up to {doc_count} documents?"):
                return

            # Get detectors
            detectors = await self._get_available_detectors()
            detector_choices = list(detectors.keys())

            selected_detectors = await self._select_multiple_detectors(detector_choices)
            if not selected_detectors:
                selected_detectors = detector_choices

            # Perform bulk analysis
            analysis_request = {
                "criteria": criteria,
                "detectors": selected_detectors
            }

            with self.console.status("[bold green]Analyzing documents...") as status:
                response = await self.clients.post_json("analysis-service/analyze/bulk", analysis_request)

            if response.get("success"):
                summary = response.get("summary", {})
                self.display.show_success(f"Analysis completed: {summary.get('processed', 0)} documents processed")
                self.display.show_info(f"Findings: {summary.get('total_findings', 0)}")
            else:
                self.display.show_error(f"Bulk analysis failed: {response.get('message', 'Unknown error')}")

        except Exception as e:
            self.display.show_error(f"Error analyzing multiple documents: {e}")

    async def analyze_by_source_type(self):
        """Analyze documents by source type."""
        try:
            source_types = ["api", "file", "web", "database", "git"]

            source_type = await self.select_from_list(source_types, "Select source type to analyze")

            if not source_type:
                return

            # Get detectors for this source type
            detectors = await self._get_detectors_for_source(source_type)

            # Perform analysis
            analysis_request = {
                "source_type": source_type,
                "detectors": detectors
            }

            with self.console.status(f"[bold green]Analyzing {source_type} documents...") as status:
                response = await self.clients.post_json("analysis-service/analyze/by-source", analysis_request)

            if response.get("success"):
                results = response.get("results", [])
                self.display.show_success(f"Analyzed {len(results)} {source_type} documents")
                self.display.show_info(f"Total findings: {sum(len(r.get('findings', [])) for r in results)}")
            else:
                self.display.show_error(f"Source analysis failed: {response.get('message', 'Unknown error')}")

        except Exception as e:
            self.display.show_error(f"Error analyzing by source type: {e}")

    async def configure_analysis_detectors(self):
        """Configure analysis detectors."""
        try:
            detectors = await self._get_available_detectors()

            table_data = []
            for name, config in detectors.items():
                enabled = "[green]YES[/green]" if config.get("enabled", True) else "[red]NO[/red]"
                table_data.append([name, config.get("description", ""), enabled])

            self.display.show_table(
                "Available Analysis Detectors",
                ["Detector", "Description", "Enabled"],
                table_data
            )

            # Allow configuration
            detector_to_configure = await self.select_from_list(list(detectors.keys()), "Select detector to configure")

            if detector_to_configure:
                config = detectors[detector_to_configure]
                self.display.show_dict(config, f"Configuration for {detector_to_configure}")

                # Simple enable/disable toggle
                current_state = config.get("enabled", True)
                new_state = not current_state

                if await self.confirm_action(f"{'Enable' if new_state else 'Disable'} detector '{detector_to_configure}'?"):
                    # In a real implementation, this would update the detector configuration
                    self.display.show_success(f"Detector '{detector_to_configure}' {'enabled' if new_state else 'disabled'}")

        except Exception as e:
            self.display.show_error(f"Error configuring detectors: {e}")

    async def analysis_templates(self):
        """Show analysis templates."""
        try:
            templates = await self._get_analysis_templates()

            if not templates:
                self.display.show_warning("No analysis templates found")
                return

            table_data = []
            for name, template in templates.items():
                table_data.append([
                    name,
                    template.get("description", ""),
                    str(len(template.get("detectors", [])))
                ])

            self.display.show_table(
                "Analysis Templates",
                ["Template", "Description", "Detectors"],
                table_data
            )

        except Exception as e:
            self.display.show_error(f"Error loading analysis templates: {e}")

    async def display_analysis_results(self, results: List[Dict[str, Any]], title: str):
        """Display analysis results."""
        if not results:
            self.display.show_info("No analysis results to display")
            return

        # Group by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for result in results:
            findings = result.get("findings", [])
            for finding in findings:
                severity = finding.get("severity", "info").lower()
                if severity in severity_counts:
                    severity_counts[severity] += 1

        # Show summary
        summary = f"Analysis Summary: {sum(severity_counts.values())} total findings"
        self.display.show_info(summary)

        # Show severity breakdown
        severity_data = []
        for severity, count in severity_counts.items():
            if count > 0:
                severity_data.append([severity.upper(), str(count)])

        if severity_data:
            self.display.show_table("Findings by Severity", ["Severity", "Count"], severity_data)

        # Show detailed results (first few)
        if len(results) > 0:
            first_result = results[0]
            findings = first_result.get("findings", [])

            if findings:
                findings_data = []
                for finding in findings[:10]:  # Show first 10
                    findings_data.append([
                        finding.get("type", ""),
                        finding.get("severity", "").upper(),
                        finding.get("description", "")[:50]
                    ])

                self.display.show_table(
                    f"Detailed Findings - {first_result.get('document_id', 'Unknown')}",
                    ["Type", "Severity", "Description"],
                    findings_data
                )

    async def _get_available_detectors(self) -> Dict[str, Dict[str, Any]]:
        """Get available analysis detectors."""
        # In a real implementation, this would fetch from the analysis service
        return {
            "consistency": {
                "description": "Checks document consistency and formatting",
                "enabled": True,
                "category": "quality"
            },
            "security": {
                "description": "Scans for security vulnerabilities and sensitive data",
                "enabled": True,
                "category": "security"
            },
            "syntax": {
                "description": "Validates code syntax and structure",
                "enabled": True,
                "category": "code"
            },
            "dependencies": {
                "description": "Analyzes dependency relationships and imports",
                "enabled": False,
                "category": "code"
            }
        }

    async def _select_multiple_detectors(self, detectors: List[str]) -> List[str]:
        """Allow user to select multiple detectors."""
        self.display.show_info("Available detectors:")
        for i, detector in enumerate(detectors, 1):
            self.console.print(f"  {i}. {detector}")

        selection_input = await self.get_user_input("Enter detector numbers (comma-separated, or 'all')", default="all")

        if selection_input.lower() == "all":
            return detectors

        try:
            indices = [int(x.strip()) - 1 for x in selection_input.split(",") if x.strip()]
            selected = []
            for idx in indices:
                if 0 <= idx < len(detectors):
                    selected.append(detectors[idx])
            return selected
        except ValueError:
            self.display.show_warning("Invalid selection, using all detectors")
            return detectors

    async def _get_detectors_for_source(self, source_type: str) -> List[str]:
        """Get appropriate detectors for a source type."""
        detector_mapping = {
            "api": ["consistency", "security"],
            "file": ["consistency", "syntax", "dependencies"],
            "web": ["consistency", "security"],
            "database": ["consistency"],
            "git": ["consistency", "syntax", "dependencies"]
        }

        return detector_mapping.get(source_type, ["consistency"])

    async def _get_analysis_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get analysis templates."""
        return {
            "security_audit": {
                "description": "Comprehensive security analysis",
                "detectors": ["security", "consistency"]
            },
            "code_review": {
                "description": "Code quality and syntax review",
                "detectors": ["syntax", "dependencies", "consistency"]
            },
            "documentation_check": {
                "description": "Documentation consistency and quality",
                "detectors": ["consistency"]
            }
        }
