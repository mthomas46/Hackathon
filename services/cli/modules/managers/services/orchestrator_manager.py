"""Orchestrator Manager module for CLI service.

Provides power-user operations for orchestrator management including
workflows, registry, infrastructure monitoring, and job management.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from services.shared.constants_new import ServiceNames
from ...base.base_manager import BaseManager


class OrchestratorManager(BaseManager):
    """Manager for orchestrator power-user operations."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return the main menu items for orchestrator management."""
        return [
            ("1", "Workflow Management (Run, Monitor, History)"),
            ("2", "Service Registry (Register, List, Poll)"),
            ("3", "Job Operations (Quality Recalc, Consolidation)"),
            ("4", "Infrastructure Status (System Health, Metrics)"),
            ("5", "E2E Demo (Full Pipeline Test)"),
            ("6", "Orchestrator Configuration")
        ]

    async def orchestrator_management_menu(self):
        """Main orchestrator management menu."""
        menu_items = await self.get_main_menu()
        await self.run_menu_loop("Orchestrator Management", menu_items)

    def get_required_services(self) -> List[str]:
        """Return list of services required by this manager."""
        return [ServiceNames.ORCHESTRATOR, ServiceNames.DOC_STORE]

    async def handle_choice(self, choice: str) -> bool:
        """Handle menu choice selection."""
        if choice == "1":
            await self.workflow_management_menu()
        elif choice == "2":
            await self.registry_management_menu()
        elif choice == "3":
            await self.job_operations_menu()
        elif choice == "4":
            await self.infrastructure_status_menu()
        elif choice == "5":
            await self.e2e_demo_menu()
        elif choice == "6":
            await self.configuration_menu()
        else:
            return False
        return True

    async def workflow_management_menu(self):
        """Workflow management submenu."""
        while True:
            menu = create_menu_table("Workflow Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "List Active Workflows"),
                ("2", "Run Workflow"),
                ("3", "View Workflow History"),
                ("4", "Monitor Workflow Status"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.list_workflows()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.run_workflow()
            elif choice == "3":
                await self.view_workflow_history()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                await self.monitor_workflow_status()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def list_workflows(self):
        """List active workflows."""
        try:
            with self.console.status("[bold green]Fetching workflows...") as status:
                response = await self.clients.get_json("orchestrator/workflows")

            if response.get("workflows"):
                table = Table(title="Active Workflows")
                table.add_column("Workflow ID", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Type", style="yellow")
                table.add_column("Started", style="white")

                for workflow in response["workflows"]:
                    table.add_row(
                        workflow.get("id", "N/A"),
                        workflow.get("status", "unknown"),
                        workflow.get("type", "unknown"),
                        workflow.get("started_at", "unknown")
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No active workflows found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching workflows: {e}[/red]")

    async def run_workflow(self):
        """Run a workflow."""
        try:
            workflow_type = Prompt.ask("[bold cyan]Workflow type[/bold cyan]",
                                     choices=["ingest", "analyze", "consolidate", "custom"])
            workflow_config = {}

            if workflow_type == "custom":
                # Allow custom workflow configuration
                config_input = Prompt.ask("[bold cyan]Workflow configuration (JSON)[/bold cyan]",
                                        default="{}")
                import json
                workflow_config = json.loads(config_input)

            with self.console.status(f"[bold green]Running {workflow_type} workflow...") as status:
                response = await self.clients.post_json("orchestrator/workflows/run", {
                    "type": workflow_type,
                    "config": workflow_config
                })

            if response.get("workflow_id"):
                self.console.print(f"[green]✅ Workflow started: {response['workflow_id']}[/green]")
                # Show initial status
                await self.monitor_workflow_status(response["workflow_id"])
            else:
                self.console.print("[red]❌ Failed to start workflow[/red]")

        except Exception as e:
            self.console.print(f"[red]Error running workflow: {e}[/red]")

    async def view_workflow_history(self):
        """View workflow history."""
        try:
            with self.console.status("[bold green]Fetching workflow history...") as status:
                response = await self.clients.get_json("orchestrator/workflows/history")

            if response.get("workflows"):
                table = Table(title="Workflow History")
                table.add_column("Workflow ID", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Type", style="yellow")
                table.add_column("Started", style="white")
                table.add_column("Completed", style="white")

                for workflow in response["workflows"][:20]:  # Show last 20
                    table.add_row(
                        workflow.get("id", "N/A"),
                        workflow.get("status", "unknown"),
                        workflow.get("type", "unknown"),
                        workflow.get("started_at", "unknown"),
                        workflow.get("completed_at", "unknown")
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No workflow history found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching workflow history: {e}[/red]")

    async def monitor_workflow_status(self, workflow_id: Optional[str] = None):
        """Monitor workflow status."""
        if not workflow_id:
            workflow_id = Prompt.ask("[bold cyan]Workflow ID[/bold cyan]")

        try:
            with self.console.status(f"[bold green]Monitoring workflow {workflow_id}...") as status:
                response = await self.clients.get_json(f"orchestrator/workflows/{workflow_id}")

            if response.get("workflow"):
                workflow = response["workflow"]
                status_color = {
                    "running": "yellow",
                    "completed": "green",
                    "failed": "red",
                    "pending": "blue"
                }.get(workflow.get("status", "unknown"), "white")

                content = f"""
[bold]Workflow Status[/bold]

ID: {workflow.get('id', 'N/A')}
Status: [{status_color}]{workflow.get('status', 'unknown')}[/{status_color}]
Type: {workflow.get('type', 'unknown')}
Started: {workflow.get('started_at', 'unknown')}
Progress: {workflow.get('progress', 'N/A')}%
"""

                if workflow.get("error"):
                    content += f"\nError: {workflow['error']}"

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[red]Workflow not found.[/red]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring workflow: {e}[/red]")

    async def registry_management_menu(self):
        """Registry management submenu."""
        while True:
            menu = create_menu_table("Service Registry", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "List Registered Services"),
                ("2", "Register New Service"),
                ("3", "Poll OpenAPI Specs"),
                ("4", "View Service Details"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.list_registry()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.register_service()
            elif choice == "3":
                await self.poll_openapi()
            elif choice == "4":
                await self.view_service_details()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def list_registry(self):
        """List registered services."""
        try:
            with self.console.status("[bold green]Fetching service registry...") as status:
                response = await self.clients.get_json("orchestrator/registry")

            if response.get("services"):
                table = Table(title="Service Registry")
                table.add_column("Service Name", style="cyan")
                table.add_column("URL", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Last Seen", style="white")

                for service in response["services"]:
                    table.add_row(
                        service.get("name", "N/A"),
                        service.get("url", "N/A"),
                        service.get("status", "unknown"),
                        service.get("last_seen", "unknown")
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No services registered.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching registry: {e}[/red]")

    async def register_service(self):
        """Register a new service."""
        try:
            service_name = Prompt.ask("[bold cyan]Service name[/bold cyan]")
            service_url = Prompt.ask("[bold cyan]Service URL[/bold cyan]")
            service_type = Prompt.ask("[bold cyan]Service type[/bold cyan]",
                                    choices=["api", "worker", "storage", "other"])

            with self.console.status("[bold green]Registering service...") as status:
                response = await self.clients.post_json("orchestrator/registry/register", {
                    "name": service_name,
                    "url": service_url,
                    "type": service_type
                })

            if response.get("registered"):
                self.console.print(f"[green]✅ Service '{service_name}' registered successfully![/green]")
            else:
                self.console.print("[red]❌ Failed to register service[/red]")

        except Exception as e:
            self.console.print(f"[red]Error registering service: {e}[/red]")

    async def poll_openapi(self):
        """Poll OpenAPI specifications."""
        try:
            service_url = Prompt.ask("[bold cyan]Service URL to poll[/bold cyan]")

            with self.console.status("[bold green]Polling OpenAPI spec...") as status:
                response = await self.clients.post_json("orchestrator/registry/poll-openapi", {
                    "url": service_url
                })

            if response.get("endpoints"):
                self.console.print(f"[green]✅ Found {len(response['endpoints'])} endpoints:[/green]")
                for endpoint in response["endpoints"][:10]:  # Show first 10
                    self.console.print(f"  {endpoint.get('method', 'GET')} {endpoint.get('path', 'unknown')}")
                if len(response["endpoints"]) > 10:
                    self.console.print(f"  ... and {len(response['endpoints']) - 10} more")
            else:
                self.console.print("[yellow]No endpoints found or service unavailable.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error polling OpenAPI: {e}[/red]")

    async def view_service_details(self):
        """View service details."""
        try:
            service_name = Prompt.ask("[bold cyan]Service name[/bold cyan]")

            with self.console.status(f"[bold green]Fetching details for {service_name}...") as status:
                response = await self.clients.get_json(f"orchestrator/registry/{service_name}")

            if response.get("service"):
                service = response["service"]
                content = f"""
[bold]Service Details: {service_name}[/bold]

URL: {service.get('url', 'N/A')}
Type: {service.get('type', 'N/A')}
Status: {service.get('status', 'unknown')}
Registered: {service.get('registered_at', 'unknown')}
Last Seen: {service.get('last_seen', 'unknown')}

Endpoints: {len(service.get('endpoints', []))}
"""

                if service.get("endpoints"):
                    content += "\n[bold]Available Endpoints:[/bold]\n"
                    for endpoint in service["endpoints"][:5]:  # Show first 5
                        content += f"  {endpoint.get('method', 'GET')} {endpoint.get('path', 'unknown')}\n"
                    if len(service["endpoints"]) > 5:
                        content += f"  ... and {len(service['endpoints']) - 5} more\n"

                print_panel(self.console, content, border_style="cyan")
            else:
                self.console.print("[red]Service not found in registry.[/red]")

        except Exception as e:
            self.console.print(f"[red]Error fetching service details: {e}[/red]")

    async def job_operations_menu(self):
        """Job operations submenu."""
        while True:
            menu = create_menu_table("Job Operations", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Recalculate Document Quality"),
                ("2", "Notify Consolidation Complete"),
                ("3", "View Job Status"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.recalc_quality()
            elif choice == "2":
                await self.notify_consolidation()
            elif choice == "3":
                await self.view_job_status()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def recalc_quality(self):
        """Recalculate document quality."""
        try:
            confirm = Confirm.ask("[bold yellow]This will recalculate quality for all documents. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Recalculating document quality...") as status:
                    response = await self.clients.post_json("orchestrator/jobs/recalc-quality", {})

                if response.get("job_id"):
                    self.console.print(f"[green]✅ Quality recalculation job started: {response['job_id']}[/green]")
                else:
                    self.console.print("[red]❌ Failed to start quality recalculation[/red]")
            else:
                self.console.print("[yellow]Quality recalculation cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error recalculating quality: {e}[/red]")

    async def notify_consolidation(self):
        """Notify consolidation complete."""
        try:
            consolidation_id = Prompt.ask("[bold cyan]Consolidation ID[/bold cyan]")

            with self.console.status("[bold green]Notifying consolidation complete...") as status:
                response = await self.clients.post_json("orchestrator/jobs/notify-consolidation", {
                    "consolidation_id": consolidation_id
                })

            if response.get("notified"):
                self.console.print(f"[green]✅ Consolidation notification sent for: {consolidation_id}[/green]")
            else:
                self.console.print("[red]❌ Failed to send consolidation notification[/red]")

        except Exception as e:
            self.console.print(f"[red]Error notifying consolidation: {e}[/red]")

    async def view_job_status(self):
        """View job status."""
        try:
            job_id = Prompt.ask("[bold cyan]Job ID[/bold cyan]", default="")

            endpoint = f"orchestrator/jobs/{job_id}" if job_id else "orchestrator/jobs"

            with self.console.status("[bold green]Fetching job status...") as status:
                response = await self.clients.get_json(endpoint)

            if response.get("jobs"):
                table = Table(title="Job Status")
                table.add_column("Job ID", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Progress", style="white")
                table.add_column("Started", style="white")

                for job in response["jobs"]:
                    table.add_row(
                        job.get("id", "N/A"),
                        job.get("type", "unknown"),
                        job.get("status", "unknown"),
                        f"{job.get('progress', 0)}%",
                        job.get("started_at", "unknown")
                    )

                self.console.print(table)
            elif response.get("job"):
                job = response["job"]
                content = f"""
[bold]Job Details[/bold]

ID: {job.get('id', 'N/A')}
Type: {job.get('type', 'unknown')}
Status: {job.get('status', 'unknown')}
Progress: {job.get('progress', 0)}%
Started: {job.get('started_at', 'unknown')}
Completed: {job.get('completed_at', 'unknown')}
"""
                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]No jobs found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching job status: {e}[/red]")

    async def infrastructure_status_menu(self):
        """Infrastructure status submenu."""
        while True:
            menu = create_menu_table("Infrastructure Status", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "System Health Overview"),
                ("2", "Orchestrator Metrics"),
                ("3", "Peer Services Status"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.system_health_overview()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.orchestrator_metrics()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.peer_services_status()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def system_health_overview(self):
        """System health overview."""
        try:
            with self.console.status("[bold green]Checking system health...") as status:
                response = await self.clients.get_json("orchestrator/health/system")

            if response.get("overall_healthy") is not None:
                health_color = "green" if response["overall_healthy"] else "red"
                content = f"""
[bold]System Health Overview[/bold]

Overall Status: [{health_color}]{'HEALTHY' if response['overall_healthy'] else 'UNHEALTHY'}[/{health_color}]

Services Checked: {response.get('services_checked', 0)}
Healthy Services: {response.get('healthy_services', 0)}
Unhealthy Services: {response.get('unhealthy_services', 0)}

Last Check: {response.get('timestamp', 'unknown')}
"""

                if response.get("service_details"):
                    content += "\n[bold]Service Details:[/bold]\n"
                    for service, details in response["service_details"].items():
                        status = "✅" if details.get("healthy") else "❌"
                        content += f"  {status} {service}: {details.get('status', 'unknown')}\n"

                print_panel(self.console, content, border_style="green" if response["overall_healthy"] else "red")
            else:
                self.console.print("[red]Unable to retrieve system health information.[/red]")

        except Exception as e:
            self.console.print(f"[red]Error checking system health: {e}[/red]")

    async def orchestrator_metrics(self):
        """Orchestrator metrics."""
        try:
            with self.console.status("[bold green]Fetching orchestrator metrics...") as status:
                response = await self.clients.get_json("orchestrator/metrics")

            if response.get("metrics"):
                metrics = response["metrics"]
                content = f"""
[bold]Orchestrator Metrics[/bold]

Active Workflows: {metrics.get('active_workflows', 0)}
Completed Workflows: {metrics.get('completed_workflows', 0)}
Failed Workflows: {metrics.get('failed_workflows', 0)}

Registered Services: {metrics.get('registered_services', 0)}
Active Services: {metrics.get('active_services', 0)}

Queue Depth: {metrics.get('queue_depth', 0)}
Processed Items: {metrics.get('processed_items', 0)}

Uptime: {metrics.get('uptime_seconds', 0)} seconds
Memory Usage: {metrics.get('memory_mb', 0)} MB
"""

                print_panel(self.console, content, border_style="cyan")
            else:
                self.console.print("[yellow]No metrics available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching metrics: {e}[/red]")

    async def peer_services_status(self):
        """Peer services status."""
        try:
            with self.console.status("[bold green]Checking peer services...") as status:
                response = await self.clients.get_json("orchestrator/peers")

            if response.get("peers"):
                table = Table(title="Peer Services")
                table.add_column("Service", style="cyan")
                table.add_column("URL", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Last Ping", style="white")

                for peer in response["peers"]:
                    status_color = "green" if peer.get("status") == "healthy" else "red"
                    table.add_row(
                        peer.get("name", "N/A"),
                        peer.get("url", "N/A"),
                        f"[{status_color}]{peer.get('status', 'unknown')}[/{status_color}]",
                        peer.get("last_ping", "unknown")
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No peer services configured.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error checking peer services: {e}[/red]")

    async def e2e_demo_menu(self):
        """E2E demo submenu."""
        while True:
            menu = create_menu_table("E2E Demo", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Run Full E2E Pipeline"),
                ("2", "Run Document Processing Demo"),
                ("3", "Run Analysis Workflow Demo"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.run_e2e_demo()
            elif choice == "2":
                await self.run_doc_processing_demo()
            elif choice == "3":
                await self.run_analysis_demo()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def run_e2e_demo(self):
        """Run full E2E demo."""
        try:
            confirm = Confirm.ask("[bold yellow]This will run a complete end-to-end demo. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Running E2E demo...") as status:
                    response = await self.clients.post_json("orchestrator/demo/e2e", {})

                if response.get("demo_id"):
                    self.console.print(f"[green]✅ E2E demo started: {response['demo_id']}[/green]")

                    # Monitor progress
                    demo_id = response["demo_id"]
                    while True:
                        import asyncio
                        await asyncio.sleep(2)

                        try:
                            status_response = await self.clients.get_json(f"orchestrator/demo/{demo_id}/status")
                            if status_response.get("completed"):
                                self.console.print("[green]✅ E2E demo completed successfully![/green]")
                                break
                            elif status_response.get("failed"):
                                self.console.print(f"[red]❌ E2E demo failed: {status_response.get('error', 'Unknown error')}[/red]")
                                break
                            else:
                                progress = status_response.get("progress", 0)
                                self.console.print(f"[yellow]⏳ Demo progress: {progress}%[/yellow]")
                        except:
                            continue
                else:
                    self.console.print("[red]❌ Failed to start E2E demo[/red]")
            else:
                self.console.print("[yellow]E2E demo cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error running E2E demo: {e}[/red]")

    async def run_doc_processing_demo(self):
        """Run document processing demo."""
        try:
            with self.console.status("[bold green]Running document processing demo...") as status:
                response = await self.clients.post_json("orchestrator/demo/doc-processing", {})

            if response.get("demo_id"):
                self.console.print(f"[green]✅ Document processing demo started: {response['demo_id']}[/green]")
            else:
                self.console.print("[red]❌ Failed to start document processing demo[/red]")

        except Exception as e:
            self.console.print(f"[red]Error running document processing demo: {e}[/red]")

    async def run_analysis_demo(self):
        """Run analysis workflow demo."""
        try:
            with self.console.status("[bold green]Running analysis demo...") as status:
                response = await self.clients.post_json("orchestrator/demo/analysis", {})

            if response.get("demo_id"):
                self.console.print(f"[green]✅ Analysis demo started: {response['demo_id']}[/green]")
            else:
                self.console.print("[red]❌ Failed to start analysis demo[/red]")

        except Exception as e:
            self.console.print(f"[red]Error running analysis demo: {e}[/red]")

    async def configuration_menu(self):
        """Orchestrator configuration submenu."""
        while True:
            menu = create_menu_table("Orchestrator Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Effective Configuration"),
                ("2", "View Orchestrator Info"),
                ("3", "View Configuration"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_effective_config()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.view_orchestrator_info()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.view_orchestrator_config()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_effective_config(self):
        """View effective configuration."""
        try:
            with self.console.status("[bold green]Fetching effective configuration...") as status:
                response = await self.clients.get_json("orchestrator/config/effective")

            if response.get("config"):
                import json
                config_str = json.dumps(response["config"], indent=2)
                print_panel(self.console, f"[bold]Effective Configuration[/bold]\n\n{config_str}",
                          border_style="cyan")
            else:
                self.console.print("[yellow]No configuration available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching configuration: {e}[/red]")

    async def view_orchestrator_info(self):
        """View orchestrator info."""
        try:
            with self.console.status("[bold green]Fetching orchestrator info...") as status:
                response = await self.clients.get_json("orchestrator/info")

            if response.get("info"):
                info = response["info"]
                content = f"""
[bold]Orchestrator Information[/bold]

Version: {info.get('version', 'unknown')}
Uptime: {info.get('uptime', 'unknown')}
Environment: {info.get('environment', 'unknown')}
Services: {info.get('services_count', 0)}

Features: {', '.join(info.get('features', []))}
"""

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]No orchestrator info available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching orchestrator info: {e}[/red]")

    async def view_orchestrator_config(self):
        """View orchestrator config."""
        try:
            with self.console.status("[bold green]Fetching orchestrator config...") as status:
                response = await self.clients.get_json("orchestrator/config")

            if response.get("config"):
                config = response["config"]
                content = f"""
[bold]Orchestrator Configuration[/bold]

Database: {config.get('database', {}).get('url', 'configured')}
Redis: {config.get('redis', {}).get('url', 'configured')}
Services: {len(config.get('services', {}))} configured

Logging Level: {config.get('logging', {}).get('level', 'unknown')}
Environment: {config.get('environment', 'unknown')}
"""

                print_panel(self.console, content, border_style="yellow")
            else:
                self.console.print("[yellow]No orchestrator config available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching orchestrator config: {e}[/red]")
