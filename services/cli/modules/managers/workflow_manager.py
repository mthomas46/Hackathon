"""Workflow Management module for the CLI service.

This module contains workflow-related CLI commands and operations,
extracted from the main CLI service to improve maintainability.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.prompt import Prompt

from services.shared.integrations.clients.clients import ServiceClients

from ..base.base_manager import BaseManager


class WorkflowManager(BaseManager):
    """Handle workflow orchestration CLI operations."""

    def __init__(self, console: Console, clients: ServiceClients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

    async def get_required_services(self) -> List[str]:
        """Return list of required services for this manager."""
        return ["orchestrator", "interpreter", "architecture-digitizer", "analysis-service", "doc_store"]

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return the main menu items for workflow management."""
        return [
            ("1", "Create New Workflow"),
            ("2", "List Active Workflows"),
            ("3", "Monitor Workflow Status"),
            ("4", "Architecture Processing Workflows"),
            ("5", "Workflow Templates"),
            ("6", "Workflow History")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle menu choice selection."""
        if choice == "1":
            await self.create_workflow()
        elif choice == "2":
            await self.list_workflows()
        elif choice == "3":
            await self.monitor_workflows()
        elif choice == "4":
            await self.architecture_workflows()
        elif choice == "5":
            await self.workflow_templates()
        elif choice == "6":
            await self.workflow_history()
        else:
            return False
        return True

    async def workflow_orchestration_menu(self):
        """Workflow orchestration submenu with enhanced interactive experience."""
        await self.run_menu_loop("Workflow Orchestration", use_interactive=True)

    async def run_document_analysis(self):
        """Run document analysis workflow."""
        doc_id = Prompt.ask("Document ID or URL")

        try:
            payload = {
                "targets": [doc_id],
                "analysis_type": "consistency"
            }

            with self.console.status("[bold green]Running document analysis...[/bold green]"):
                url = f"{self.clients.analysis_service_url()}/analyze"
                response = await self.clients.post_json(url, payload)

            self.console.print("[green]✅ Document analysis completed![/green]")
            self.console.print(f"Analysis results: {response}")

        except Exception as e:
            self.console.print(f"[red]❌ Error running document analysis: {e}[/red]")
            self.console.print("[yellow]💡 Tip: Check if the document ID/URL is valid and the analysis service is running[/yellow]")

    async def trigger_ingestion(self):
        """Trigger data ingestion workflow."""
        source_type = Prompt.ask("Source type", default="github")
        source_url = Prompt.ask("Source URL")

        try:
            payload = {
                "source_type": source_type,
                "source_url": source_url
            }

            with self.console.status("[bold green]Triggering data ingestion...[/bold green]"):
                url = f"{self.clients.source_agent_url()}/ingest"
                response = await self.clients.post_json(url, payload)

            self.console.print("[green]✅ Data ingestion triggered successfully![/green]")
            self.console.print(f"Ingestion status: {response}")

        except Exception as e:
            self.console.print(f"[red]❌ Error triggering ingestion: {e}[/red]")
            self.console.print("[yellow]💡 Tip: Verify the source URL format and ensure the source agent service is running[/yellow]")

    async def run_consistency_check(self):
        """Run consistency check."""
        try:
            with self.console.status("[bold green]Running consistency check...[/bold green]"):
                url = f"{self.clients.analysis_service_url()}/consistency/check"
                response = await self.clients.get_json(url)

            self.console.print("[green]✅ Consistency check completed![/green]")
            self.console.print(f"Results: {response}")

        except Exception as e:
            self.console.print(f"[red]❌ Error running consistency check: {e}[/red]")
            self.console.print("[yellow]💡 Tip: Ensure the analysis service is running and accessible[/yellow]")

    async def generate_reports(self):
        """Generate reports."""
        report_type = Prompt.ask("Report type", default="summary")

        try:
            payload = {
                "type": report_type,
                "format": "json"
            }

            with self.console.status("[bold green]Generating report...[/bold green]"):
                url = f"{self.clients.analysis_service_url()}/reports/generate"
                response = await self.clients.post_json(url, payload)

            self.console.print("[green]✅ Report generated successfully![/green]")
            self.console.print(f"Report: {response}")

        except Exception as e:
            self.console.print(f"[red]❌ Error generating report: {e}[/red]")
            self.console.print("[yellow]💡 Tip: Check report type and ensure analysis service is running[/yellow]")

    async def view_workflow_status(self):
        """View workflow status."""
        try:
            # Try to get workflow status from orchestrator
            url = f"{self.clients.orchestrator_url()}/workflows/status"
            response = await self.clients.get_json(url)

            workflows = response.get("workflows", [])
            if not workflows:
                self.console.print("[yellow]No active workflows found.[/yellow]")
                return

            # Display workflow status
            for workflow in workflows:
                status = workflow.get("status", "unknown")
                if status == "running":
                    status_display = "[green]Running[/green]"
                elif status == "completed":
                    status_display = "[blue]Completed[/blue]"
                elif status == "failed":
                    status_display = "[red]Failed[/red]"
                else:
                    status_display = f"[yellow]{status}[/yellow]"

                self.console.print(f"Workflow {workflow.get('id', 'N/A')}: {status_display}")

        except Exception as e:
            self.console.print(f"[red]❌ Error viewing workflow status: {e}[/red]")
            self.console.print("[yellow]💡 Tip: Ensure the orchestrator service is running[/yellow]")

    async def execute_custom_workflow(self):
        """Execute a custom workflow."""
        self.console.print("\n[bold yellow]Custom Workflow Execution[/bold yellow]")
        self.console.print("This feature allows you to execute custom workflows defined in JSON format.")

        workflow_json = Prompt.ask("Enter workflow JSON")

        try:
            import json
            workflow = json.loads(workflow_json)

            # Validate workflow structure
            if not isinstance(workflow, dict) or "steps" not in workflow:
                self.console.print("[red]Invalid workflow format. Must contain 'steps' array.[/red]")
                return

            # Execute workflow
            with self.console.status("[bold green]Executing custom workflow...") as status:
                url = f"{self.clients.orchestrator_url()}/workflows/execute"
                response = await self.clients.post_json(url, workflow)

            self.console.print("[green]✅ Custom workflow executed successfully![/green]")
            self.console.print(f"Results: {response}")

        except json.JSONDecodeError:
            self.console.print("[red]Invalid JSON format.[/red]")
        except Exception as e:
            self.console.print(f"[red]Error executing custom workflow: {e}[/red]")

    async def run_interactive_query(self):
        """Run an interactive natural language query."""
        query = Prompt.ask("Enter your query")

        try:
            payload = {"query": query}

            with self.console.status("[bold green]Processing query...") as status:
                url = f"{self.clients.interpreter_url()}/interpret"
                response = await self.clients.post_json(url, payload)

            # Display interpretation results
            intent = response.get("intent", "unknown")
            confidence = response.get("confidence", 0.0)
            entities = response.get("entities", {})

            self.console.print(f"\n[bold blue]Query Interpretation:[/bold blue]")
            self.console.print(f"Intent: {intent}")
            self.console.print(f"Confidence: {confidence:.2f}")
            self.console.print(f"Entities: {entities}")

            # If there's a workflow, offer to execute it
            if response.get("workflow"):
                execute = Prompt.ask("Execute the generated workflow? (y/n)", default="n")
                if execute.lower() in ["y", "yes"]:
                    url = f"{self.clients.interpreter_url()}/execute"
                    workflow_result = await self.clients.post_json(url, payload)
                    self.console.print("[green]✅ Workflow executed![/green]")

        except Exception as e:
            self.console.print(f"[red]Error processing query: {e}[/red]")


    async def architecture_workflows(self):
        """Architecture processing workflow menu."""
        from rich.table import Table
        from rich.prompt import Prompt

        while True:
            # Create workflow options table
            table = Table(title="🏗️ Architecture Processing Workflows")
            table.add_column("Option", style="cyan", no_wrap=True)
            table.add_column("Workflow", style="white")
            table.add_column("Description", style="dim white")

            table.add_row("1", "Diagram → Doc Store", "Normalize diagram and store in document store")
            table.add_row("2", "Diagram → Analysis", "Normalize diagram and run architecture analysis")
            table.add_row("3", "Full Pipeline", "Normalize → Store → Analyze → Report")
            table.add_row("4", "Batch Processing", "Process multiple diagrams in batch")
            table.add_row("b", "Back", "Return to workflow menu")

            self.console.print(table)

            choice = Prompt.ask("[bold green]Select workflow[/bold green]")

            if choice == "1":
                await self._diagram_to_docstore_workflow()
            elif choice == "2":
                await self._diagram_to_analysis_workflow()
            elif choice == "3":
                await self._full_architecture_pipeline()
            elif choice == "4":
                await self._batch_diagram_processing()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def _diagram_to_docstore_workflow(self):
        """Workflow: Normalize diagram and store in doc_store."""
        self.console.print("\n[bold green]🏗️ Diagram → Doc Store Workflow[/bold green]")
        self.console.print("This workflow will normalize an architecture diagram and store it in the document store.")

        # Get diagram source
        system = Prompt.ask("System (miro/figjam/lucid/confluence)")
        board_id = Prompt.ask("Board/Document ID")
        token = Prompt.ask("API Token", password=True)

        if not Prompt.ask("Proceed with workflow? (y/n)", default="n").lower().startswith("y"):
            return

        try:
            with self.console.status("[bold green]Processing diagram...[/bold green]") as status:
                # Step 1: Normalize diagram
                normalize_result = await self.clients.post_json(
                    "architecture-digitizer/normalize",
                    {"system": system, "board_id": board_id, "token": token}
                )

                if not normalize_result.get("success"):
                    self.console.print(f"[red]❌ Normalization failed: {normalize_result.get('message')}[/red]")
                    return

                # The normalized data is automatically stored in doc_store via the architecture-digitizer service
                self.console.print("[green]✅ Diagram normalized and stored in document store![/green]")
                self.console.print(f"Components: {len(normalize_result.get('data', {}).get('components', []))}")
                self.console.print(f"Connections: {len(normalize_result.get('data', {}).get('connections', []))}")

        except Exception as e:
            self.console.print(f"[red]❌ Workflow failed: {e}[/red]")

    async def _diagram_to_analysis_workflow(self):
        """Workflow: Normalize diagram and run architecture analysis."""
        self.console.print("\n[bold green]🏗️ Diagram → Analysis Workflow[/bold green]")
        self.console.print("This workflow will normalize a diagram and run comprehensive architecture analysis.")

        # Get diagram source
        system = Prompt.ask("System (miro/figjam/lucid/confluence)")
        board_id = Prompt.ask("Board/Document ID")
        token = Prompt.ask("API Token", password=True)
        analysis_type = Prompt.ask("Analysis type (consistency/completeness/best_practices/combined)", default="combined")

        if not Prompt.ask("Proceed with workflow? (y/n)", default="n").lower().startswith("y"):
            return

        try:
            with self.console.status("[bold green]Processing and analyzing diagram...[/bold green]") as status:
                # Step 1: Normalize diagram
                normalize_result = await self.clients.post_json(
                    "architecture-digitizer/normalize",
                    {"system": system, "board_id": board_id, "token": token}
                )

                if not normalize_result.get("success"):
                    self.console.print(f"[red]❌ Normalization failed: {normalize_result.get('message')}[/red]")
                    return

                # Step 2: Run architecture analysis
                components = normalize_result.get("data", {}).get("components", [])
                connections = normalize_result.get("data", {}).get("connections", [])

                analysis_result = await self.clients.post_json(
                    "analysis-service/architecture/analyze",
                    {
                        "components": components,
                        "connections": connections,
                        "analysis_type": analysis_type
                    }
                )

                # Display results
                self.console.print("[green]✅ Architecture analysis completed![/green]")

                issues = analysis_result.get("issues", [])
                if issues:
                    from rich.table import Table
                    issue_table = Table(title="Analysis Issues")
                    issue_table.add_column("Severity", style="red")
                    issue_table.add_column("Type", style="cyan")
                    issue_table.add_column("Issue", style="white")

                    for issue in issues[:10]:  # Show first 10 issues
                        issue_table.add_row(
                            issue.get("severity", "unknown"),
                            issue.get("issue_type", "unknown"),
                            issue.get("message", "")
                        )

                    self.console.print(issue_table)

                    if len(issues) > 10:
                        self.console.print(f"[dim]... and {len(issues) - 10} more issues[/dim]")
                else:
                    self.console.print("[green]No issues found - architecture looks good![/green]")

        except Exception as e:
            self.console.print(f"[red]❌ Workflow failed: {e}[/red]")

    async def _full_architecture_pipeline(self):
        """Complete architecture processing pipeline."""
        self.console.print("\n[bold green]🏗️ Full Architecture Pipeline[/bold green]")
        self.console.print("Complete workflow: Normalize → Store → Analyze → Generate Report")

        # Get diagram source
        system = Prompt.ask("System (miro/figjam/lucid/confluence)")
        board_id = Prompt.ask("Board/Document ID")
        token = Prompt.ask("API Token", password=True)

        if not Prompt.ask("Proceed with full pipeline? (y/n)", default="n").lower().startswith("y"):
            return

        try:
            with self.console.status("[bold green]Running full architecture pipeline...[/bold green]") as status:
                # Step 1: Normalize (which also stores in doc_store)
                normalize_result = await self.clients.post_json(
                    "architecture-digitizer/normalize",
                    {"system": system, "board_id": board_id, "token": token}
                )

                if not normalize_result.get("success"):
                    self.console.print(f"[red]❌ Normalization failed: {normalize_result.get('message')}[/red]")
                    return

                # Step 2: Run comprehensive analysis
                components = normalize_result.get("data", {}).get("components", [])
                connections = normalize_result.get("data", {}).get("connections", [])

                analysis_result = await self.clients.post_json(
                    "analysis-service/architecture/analyze",
                    {
                        "components": components,
                        "connections": connections,
                        "analysis_type": "combined"
                    }
                )

                # Step 3: Generate report and store in doc_store
                report_data = {
                    "title": f"Architecture Analysis Report - {system.upper()} {board_id}",
                    "system": system,
                    "board_id": board_id,
                    "normalization_result": normalize_result,
                    "analysis_result": analysis_result,
                    "generated_at": "now"
                }

                await self.clients.post_json("doc_store/store", {
                    "type": "architecture_report",
                    "content": str(report_data),
                    "metadata": {
                        "source_type": "architecture_pipeline",
                        "type": "report",
                        "system": system,
                        "board_id": board_id
                    }
                })

                self.console.print("[green]✅ Full architecture pipeline completed![/green]")
                self.console.print("📊 Report generated and stored in document store")
                self.console.print(f"🔍 Issues found: {len(analysis_result.get('issues', []))}")

        except Exception as e:
            self.console.print(f"[red]❌ Pipeline failed: {e}[/red]")

    async def _batch_diagram_processing(self):
        """Batch process multiple diagrams."""
        self.console.print("\n[bold green]🏗️ Batch Diagram Processing[/bold green]")
        self.console.print("Process multiple architecture diagrams in batch mode.")
        self.console.print("[yellow]Feature coming soon! This will support CSV input of diagram URLs/tokens.[/yellow]")

        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
