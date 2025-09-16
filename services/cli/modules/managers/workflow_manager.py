"""Workflow Management module for the CLI service.

This module contains workflow-related CLI commands and operations,
extracted from the main CLI service to improve maintainability.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.prompt import Prompt

from services.shared.clients import ServiceClients

from ..base.base_manager import BaseManager


class WorkflowManager(BaseManager):
    """Handle workflow orchestration CLI operations."""

    def __init__(self, console: Console, clients: ServiceClients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return the main menu items for workflow management."""
        return [
            ("1", "Create New Workflow"),
            ("2", "List Active Workflows"),
            ("3", "Monitor Workflow Status"),
            ("4", "Workflow Templates"),
            ("5", "Workflow History")
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
            await self.workflow_templates()
        elif choice == "5":
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
                    self.console.print(f"Results: {workflow_result}")

        except Exception as e:
            self.console.print(f"[red]Error processing query: {e}[/red]")
