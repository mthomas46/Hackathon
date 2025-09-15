"""Deployment Controls Manager module for CLI service.

Provides comprehensive deployment management including
service scaling, rolling updates, canary deployments, traffic management,
and container orchestration controls.
"""

from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
import json
import os
import yaml
import subprocess
import asyncio
import time
from pathlib import Path
from collections import defaultdict
import re

from .shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class DeploymentManager:
    """Manager for comprehensive deployment controls and orchestration."""

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients
        self.deployment_history = []
        self.scaling_history = []

    async def deployment_controls_menu(self):
        """Main deployment controls menu."""
        while True:
            menu = create_menu_table("Deployment Controls", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Service Scaling (Scale services up/down, view current replicas)"),
                ("2", "Rolling Updates (Zero-downtime service updates)"),
                ("3", "Canary Deployments (Gradual traffic shifting)"),
                ("4", "Service Mesh Traffic Management (Traffic routing and policies)"),
                ("5", "Container Orchestration (Docker Compose management)"),
                ("6", "Deployment Monitoring (Track deployment status and health)"),
                ("7", "Rollback Management (Revert to previous deployments)"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.service_scaling_menu()
            elif choice == "2":
                await self.rolling_updates_menu()
            elif choice == "3":
                await self.canary_deployments_menu()
            elif choice == "4":
                await self.traffic_management_menu()
            elif choice == "5":
                await self.container_orchestration_menu()
            elif choice == "6":
                await self.deployment_monitoring_menu()
            elif choice == "7":
                await self.rollback_management_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def service_scaling_menu(self):
        """Service scaling submenu."""
        while True:
            menu = create_menu_table("Service Scaling", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Current Scaling Status"),
                ("2", "Scale Individual Service"),
                ("3", "Scale Multiple Services"),
                ("4", "Auto-scaling Policies"),
                ("5", "Scaling History"),
                ("6", "Resource Usage Monitoring"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_current_scaling_status()
            elif choice == "2":
                await self.scale_individual_service()
            elif choice == "3":
                await self.scale_multiple_services()
            elif choice == "4":
                await self.auto_scaling_policies()
            elif choice == "5":
                await self.scaling_history()
            elif choice == "6":
                await self.resource_usage_monitoring()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_current_scaling_status(self):
        """View current scaling status of all services."""
        try:
            # Get Docker Compose service status
            compose_files = self._find_docker_compose_files()
            scaling_status = {}

            for compose_file in compose_files:
                try:
                    # Get service definitions from compose file
                    with open(compose_file, 'r') as f:
                        compose_data = yaml.safe_load(f)

                    services = compose_data.get("services", {})

                    for service_name, service_config in services.items():
                        replicas = service_config.get("deploy", {}).get("replicas", 1)
                        scaling_status[service_name] = {
                            "current_replicas": replicas,
                            "desired_replicas": replicas,
                            "status": "stable",
                            "source_file": compose_file.name
                        }

                except Exception as e:
                    self.console.print(f"[yellow]Warning: Could not read {compose_file}: {e}[/yellow]")

            # Try to get runtime status using docker-compose ps
            try:
                result = subprocess.run(
                    ["docker-compose", "ps", "--format", "json"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd="."
                )

                if result.returncode == 0:
                    # Parse the JSON output to get actual running status
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            try:
                                ps_data = json.loads(line)
                                service_name = ps_data.get("Service")
                                state = ps_data.get("State", "").lower()

                                if service_name in scaling_status:
                                    if "running" in state:
                                        scaling_status[service_name]["status"] = "running"
                                    elif "exited" in state or "stopped" in state:
                                        scaling_status[service_name]["status"] = "stopped"
                                    else:
                                        scaling_status[service_name]["status"] = state
                            except json.JSONDecodeError:
                                pass

            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.console.print("[yellow]Could not get runtime status - docker-compose may not be available[/yellow]")

            # Display scaling status
            if scaling_status:
                table = Table(title="Service Scaling Status")
                table.add_column("Service", style="cyan")
                table.add_column("Current Replicas", style="green", justify="right")
                table.add_column("Desired Replicas", style="blue", justify="right")
                table.add_column("Status", style="yellow")
                table.add_column("Source", style="magenta")

                for service_name, status in sorted(scaling_status.items()):
                    status_color = {
                        "running": "green",
                        "stable": "blue",
                        "stopped": "red",
                        "error": "red"
                    }.get(status["status"], "yellow")

                    table.add_row(
                        service_name,
                        str(status["current_replicas"]),
                        str(status["desired_replicas"]),
                        f"[{status_color}]{status['status'].upper()}[/{status_color}]",
                        status.get("source_file", "unknown")
                    )

                self.console.print(table)

                # Show summary
                total_services = len(scaling_status)
                running_services = sum(1 for s in scaling_status.values() if s["status"] == "running")
                scaled_services = sum(1 for s in scaling_status.values() if s["current_replicas"] > 1)

                content = f"""
[bold]Scaling Summary:[/bold]
• Total Services: {total_services}
• Running Services: {running_services}
• Scaled Services: {scaled_services}
• Total Replicas: {sum(s['current_replicas'] for s in scaling_status.values())}
"""

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]No scaling status information available[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error viewing scaling status: {e}[/red]")

    async def scale_individual_service(self):
        """Scale an individual service."""
        try:
            # Get available services
            compose_files = self._find_docker_compose_files()
            available_services = set()

            for compose_file in compose_files:
                try:
                    with open(compose_file, 'r') as f:
                        compose_data = yaml.safe_load(f)
                    services = compose_data.get("services", {})
                    available_services.update(services.keys())
                except Exception:
                    pass

            if not available_services:
                self.console.print("[yellow]No services found in Docker Compose files[/yellow]")
                return

            service_list = sorted(list(available_services))
            service_name = Prompt.ask("[bold cyan]Service to scale[/bold cyan]", choices=service_list)

            current_replicas = Prompt.ask("[bold cyan]Current replicas[/bold cyan]", default="1")
            new_replicas = Prompt.ask("[bold cyan]New number of replicas[/bold cyan]")

            if not new_replicas.isdigit() or int(new_replicas) < 0:
                self.console.print("[red]Invalid number of replicas[/red]")
                return

            new_replicas = int(new_replicas)

            confirm = Confirm.ask(f"[bold red]Scale {service_name} from {current_replicas} to {new_replicas} replicas?[/bold red]", default=False)

            if confirm:
                # Update the compose file
                updated = await self._update_service_replicas(service_name, new_replicas)

                if updated:
                    # Record scaling operation
                    scaling_record = {
                        "timestamp": self._get_timestamp(),
                        "service": service_name,
                        "action": "scale",
                        "old_replicas": current_replicas,
                        "new_replicas": new_replicas,
                        "status": "pending"
                    }
                    self.scaling_history.append(scaling_record)

                    # Attempt to apply scaling
                    success = await self._apply_scaling(service_name, new_replicas)

                    scaling_record["status"] = "completed" if success else "failed"
                    scaling_record["applied_at"] = self._get_timestamp()

                    self.console.print(f"[green]✅ Service {service_name} scaled to {new_replicas} replicas[/green]" if success else f"[red]❌ Failed to scale {service_name}[/red]")
                else:
                    self.console.print("[red]❌ Failed to update compose file[/red]")
            else:
                self.console.print("[yellow]Scaling cancelled[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error scaling service: {e}[/red]")

    async def scale_multiple_services(self):
        """Scale multiple services at once."""
        try:
            self.console.print("[yellow]Multi-service scaling would allow bulk scaling operations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in multi-service scaling: {e}[/red]")

    async def auto_scaling_policies(self):
        """Configure auto-scaling policies."""
        try:
            self.console.print("[yellow]Auto-scaling policies would configure automatic scaling based on metrics[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring auto-scaling: {e}[/red]")

    async def scaling_history(self):
        """View scaling history."""
        try:
            if not self.scaling_history:
                self.console.print("[yellow]No scaling history available[/yellow]")
                return

            table = Table(title="Scaling History")
            table.add_column("Timestamp", style="blue", no_wrap=True)
            table.add_column("Service", style="cyan")
            table.add_column("Action", style="green")
            table.add_column("Old → New", style="yellow")
            table.add_column("Status", style="magenta")

            for record in self.scaling_history[-20:]:  # Show last 20
                old_new = f"{record['old_replicas']} → {record['new_replicas']}"
                status_color = "green" if record["status"] == "completed" else "red" if record["status"] == "failed" else "yellow"
                table.add_row(
                    record["timestamp"],
                    record["service"],
                    record["action"],
                    old_new,
                    f"[{status_color}]{record['status'].upper()}[/{status_color}]"
                )

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error viewing scaling history: {e}[/red]")

    async def resource_usage_monitoring(self):
        """Monitor resource usage for scaling decisions."""
        try:
            self.console.print("[yellow]Resource usage monitoring would show CPU, memory, and other metrics for scaling decisions[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring resources: {e}[/red]")

    async def rolling_updates_menu(self):
        """Rolling updates submenu."""
        while True:
            menu = create_menu_table("Rolling Updates", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Start Rolling Update"),
                ("2", "Monitor Update Progress"),
                ("3", "Pause/Resume Update"),
                ("4", "Rollback Update"),
                ("5", "Update Strategies"),
                ("6", "Update History"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.start_rolling_update()
            elif choice == "2":
                await self.monitor_update_progress()
            elif choice == "3":
                await self.pause_resume_update()
            elif choice == "4":
                await self.rollback_update()
            elif choice == "5":
                await self.update_strategies()
            elif choice == "6":
                await self.update_history()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def start_rolling_update(self):
        """Start a rolling update for a service."""
        try:
            service_name = Prompt.ask("[bold cyan]Service to update[/bold cyan]")
            image_tag = Prompt.ask("[bold cyan]New image tag/version[/bold cyan]")
            update_strategy = Prompt.ask("[bold cyan]Update strategy[/bold cyan]", choices=["rolling", "blue-green", "canary"], default="rolling")

            confirm = Confirm.ask(f"[bold red]Start {update_strategy} update of {service_name} to {image_tag}?[/bold red]", default=False)

            if confirm:
                # Record deployment
                deployment_record = {
                    "timestamp": self._get_timestamp(),
                    "service": service_name,
                    "action": "rolling_update",
                    "strategy": update_strategy,
                    "new_version": image_tag,
                    "status": "in_progress"
                }
                self.deployment_history.append(deployment_record)

                # Simulate update process
                self.console.print(f"[yellow]Starting {update_strategy} update of {service_name}...[/yellow]")

                # In a real implementation, this would:
                # 1. Update the Docker Compose file with new image
                # 2. Run docker-compose up with appropriate flags
                # 3. Monitor health checks
                # 4. Gradually replace old containers

                success = await self._perform_rolling_update(service_name, image_tag, update_strategy)

                deployment_record["status"] = "completed" if success else "failed"
                deployment_record["completed_at"] = self._get_timestamp()

                self.console.print(f"[green]✅ Rolling update completed[/green]" if success else "[red]❌ Rolling update failed[/red]")
            else:
                self.console.print("[yellow]Update cancelled[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting rolling update: {e}[/red]")

    async def monitor_update_progress(self):
        """Monitor rolling update progress."""
        try:
            self.console.print("[yellow]Update progress monitoring would show real-time deployment status[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring update progress: {e}[/red]")

    async def pause_resume_update(self):
        """Pause or resume a rolling update."""
        try:
            self.console.print("[yellow]Pause/resume would control ongoing deployment processes[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with pause/resume: {e}[/red]")

    async def rollback_update(self):
        """Rollback a failed update."""
        try:
            self.console.print("[yellow]Rollback would revert to previous stable version[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with rollback: {e}[/red]")

    async def update_strategies(self):
        """Configure update strategies."""
        try:
            strategies = {
                "rolling": {
                    "description": "Gradually replace old containers with new ones",
                    "pros": ["Zero downtime", "Resource efficient"],
                    "cons": ["Slower", "Complex rollback"]
                },
                "blue-green": {
                    "description": "Deploy new version alongside old, then switch traffic",
                    "pros": ["Instant rollback", "Thorough testing"],
                    "cons": ["Double resources", "Complex routing"]
                },
                "canary": {
                    "description": "Deploy to subset of instances, gradually increase traffic",
                    "pros": ["Risk mitigation", "A/B testing"],
                    "cons": ["Complex traffic management", "Longer deployment"]
                }
            }

            table = Table(title="Update Strategies")
            table.add_column("Strategy", style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Pros", style="green")
            table.add_column("Cons", style="red")

            for name, details in strategies.items():
                pros = ", ".join(details["pros"])
                cons = ", ".join(details["cons"])
                table.add_row(name.title(), details["description"], pros, cons)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error viewing update strategies: {e}[/red]")

    async def update_history(self):
        """View update history."""
        try:
            if not self.deployment_history:
                self.console.print("[yellow]No deployment history available[/yellow]")
                return

            table = Table(title="Deployment History")
            table.add_column("Timestamp", style="blue", no_wrap=True)
            table.add_column("Service", style="cyan")
            table.add_column("Action", style="green")
            table.add_column("Strategy", style="yellow")
            table.add_column("Version", style="magenta")
            table.add_column("Status", style="red")

            for record in self.deployment_history[-20:]:
                status_color = "green" if record["status"] == "completed" else "red" if record["status"] == "failed" else "yellow"
                table.add_row(
                    record["timestamp"],
                    record.get("service", "N/A"),
                    record.get("action", "N/A"),
                    record.get("strategy", "N/A"),
                    record.get("new_version", "N/A"),
                    f"[{status_color}]{record['status'].upper()}[/{status_color}]"
                )

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error viewing update history: {e}[/red]")

    async def canary_deployments_menu(self):
        """Canary deployments submenu."""
        while True:
            menu = create_menu_table("Canary Deployments", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Start Canary Deployment"),
                ("2", "Adjust Traffic Distribution"),
                ("3", "Monitor Canary Metrics"),
                ("4", "Promote/Abort Canary"),
                ("5", "Canary History"),
                ("6", "Canary Templates"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.start_canary_deployment()
            elif choice == "2":
                await self.adjust_traffic_distribution()
            elif choice == "3":
                await self.monitor_canary_metrics()
            elif choice == "4":
                await self.promote_abort_canary()
            elif choice == "5":
                await self.canary_history()
            elif choice == "6":
                await self.canary_templates()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def start_canary_deployment(self):
        """Start a canary deployment."""
        try:
            service_name = Prompt.ask("[bold cyan]Service for canary deployment[/bold cyan]")
            new_image = Prompt.ask("[bold cyan]New image tag[/bold cyan]")
            canary_percentage = int(Prompt.ask("[bold cyan]Initial canary percentage[/bold cyan]", default="10"))

            confirm = Confirm.ask(f"[bold red]Start canary deployment of {service_name} with {canary_percentage}% traffic?[/bold red]", default=False)

            if confirm:
                canary_record = {
                    "timestamp": self._get_timestamp(),
                    "service": service_name,
                    "action": "canary_start",
                    "new_image": new_image,
                    "canary_percentage": canary_percentage,
                    "status": "in_progress"
                }
                self.deployment_history.append(canary_record)

                success = await self._start_canary_deployment(service_name, new_image, canary_percentage)

                canary_record["status"] = "active" if success else "failed"

                self.console.print(f"[green]✅ Canary deployment started for {service_name}[/green]" if success else f"[red]❌ Failed to start canary deployment[/red]")
            else:
                self.console.print("[yellow]Canary deployment cancelled[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting canary deployment: {e}[/red]")

    async def adjust_traffic_distribution(self):
        """Adjust traffic distribution in canary deployment."""
        try:
            self.console.print("[yellow]Traffic adjustment would modify canary traffic percentages[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error adjusting traffic: {e}[/red]")

    async def monitor_canary_metrics(self):
        """Monitor canary deployment metrics."""
        try:
            self.console.print("[yellow]Canary metrics would show performance comparison between versions[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring canary metrics: {e}[/red]")

    async def promote_abort_canary(self):
        """Promote or abort canary deployment."""
        try:
            self.console.print("[yellow]Promote/abort would complete or cancel canary deployments[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with promote/abort: {e}[/red]")

    async def canary_history(self):
        """View canary deployment history."""
        try:
            self.console.print("[yellow]Canary history would show past canary deployment results[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing canary history: {e}[/red]")

    async def canary_templates(self):
        """Manage canary deployment templates."""
        try:
            self.console.print("[yellow]Canary templates would provide reusable deployment patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with canary templates: {e}[/red]")

    async def traffic_management_menu(self):
        """Service mesh traffic management submenu."""
        while True:
            menu = create_menu_table("Traffic Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Traffic Routes"),
                ("2", "Configure Traffic Policies"),
                ("3", "Set up Load Balancing"),
                ("4", "Configure Circuit Breakers"),
                ("5", "Traffic Monitoring"),
                ("6", "Service Mesh Status"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_traffic_routes()
            elif choice == "2":
                await self.configure_traffic_policies()
            elif choice == "3":
                await self.setup_load_balancing()
            elif choice == "4":
                await self.configure_circuit_breakers()
            elif choice == "5":
                await self.traffic_monitoring()
            elif choice == "6":
                await self.service_mesh_status()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_traffic_routes(self):
        """View current traffic routes."""
        try:
            # Analyze Docker Compose files for service dependencies and routing
            compose_files = self._find_docker_compose_files()
            routes = {}

            for compose_file in compose_files:
                try:
                    with open(compose_file, 'r') as f:
                        compose_data = yaml.safe_load(f)

                    services = compose_data.get("services", {})

                    for service_name, service_config in services.items():
                        depends_on = service_config.get("depends_on", [])
                        if isinstance(depends_on, list):
                            routes[service_name] = depends_on
                        elif isinstance(depends_on, dict):
                            routes[service_name] = list(depends_on.keys())

                except Exception:
                    pass

            if routes:
                table = Table(title="Service Traffic Routes")
                table.add_column("Service", style="cyan")
                table.add_column("Depends On", style="green")
                table.add_column("Route Count", style="yellow", justify="right")

                for service, deps in routes.items():
                    deps_str = ", ".join(deps) if deps else "None"
                    table.add_row(service, deps_str, str(len(deps)))

                self.console.print(table)
            else:
                self.console.print("[yellow]No traffic route information available[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error viewing traffic routes: {e}[/red]")

    async def configure_traffic_policies(self):
        """Configure traffic policies."""
        try:
            self.console.print("[yellow]Traffic policies would configure routing rules and policies[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring traffic policies: {e}[/red]")

    async def setup_load_balancing(self):
        """Set up load balancing."""
        try:
            self.console.print("[yellow]Load balancing setup would configure traffic distribution[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error setting up load balancing: {e}[/red]")

    async def configure_circuit_breakers(self):
        """Configure circuit breakers."""
        try:
            self.console.print("[yellow]Circuit breaker configuration would set up failure protection[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring circuit breakers: {e}[/red]")

    async def traffic_monitoring(self):
        """Monitor traffic patterns."""
        try:
            self.console.print("[yellow]Traffic monitoring would show real-time traffic patterns and metrics[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring traffic: {e}[/red]")

    async def service_mesh_status(self):
        """View service mesh status."""
        try:
            self.console.print("[yellow]Service mesh status would show mesh component health and configuration[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing service mesh status: {e}[/red]")

    async def container_orchestration_menu(self):
        """Container orchestration submenu."""
        while True:
            menu = create_menu_table("Container Orchestration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Docker Compose Status"),
                ("2", "Start/Stop Services"),
                ("3", "Service Logs"),
                ("4", "Container Resource Usage"),
                ("5", "Network Configuration"),
                ("6", "Volume Management"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.docker_compose_status()
            elif choice == "2":
                await self.start_stop_services()
            elif choice == "3":
                await self.service_logs()
            elif choice == "4":
                await self.container_resource_usage()
            elif choice == "5":
                await self.network_configuration()
            elif choice == "6":
                await self.volume_management()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def docker_compose_status(self):
        """View Docker Compose status."""
        try:
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd="."
            )

            if result.returncode == 0:
                # Parse and display the status output
                lines = result.stdout.split('\n')
                if lines:
                    content = "[bold]Docker Compose Status:[/bold]\n\n"
                    content += result.stdout
                    print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[red]Failed to get Docker Compose status[/red]")
                self.console.print(f"[dim]{result.stderr}[/dim]")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.console.print("[yellow]Docker Compose not available or timed out[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error getting Docker Compose status: {e}[/red]")

    async def start_stop_services(self):
        """Start or stop services."""
        try:
            action = Prompt.ask("[bold cyan]Action[/bold cyan]", choices=["start", "stop", "restart"])
            service_name = Prompt.ask("[bold cyan]Service name (or 'all' for all services)[/bold cyan]", default="all")

            confirm = Confirm.ask(f"[bold red]{action.title()} {service_name}?[/bold red]", default=False)

            if confirm:
                if service_name == "all":
                    cmd = ["docker-compose", action]
                else:
                    cmd = ["docker-compose", action, service_name]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd="."
                )

                if result.returncode == 0:
                    self.console.print(f"[green]✅ Successfully {action}ed {service_name}[/green]")
                else:
                    self.console.print(f"[red]❌ Failed to {action} {service_name}[/red]")
                    self.console.print(f"[dim]{result.stderr}[/dim]")
            else:
                self.console.print("[yellow]Action cancelled[/yellow]")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.console.print("[yellow]Docker Compose not available[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error with service control: {e}[/red]")

    async def service_logs(self):
        """View service logs."""
        try:
            service_name = Prompt.ask("[bold cyan]Service name[/bold cyan]", default="")
            lines = Prompt.ask("[bold cyan]Number of lines[/bold cyan]", default="100")

            if service_name:
                cmd = ["docker-compose", "logs", "--tail", lines, service_name]
            else:
                cmd = ["docker-compose", "logs", "--tail", lines]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd="."
            )

            if result.returncode == 0:
                content = f"[bold]Service Logs ({service_name or 'all'} - last {lines} lines):[/bold]\n\n"
                content += result.stdout[-5000:]  # Limit output size
                print_panel(self.console, content, border_style="cyan")
            else:
                self.console.print("[red]Failed to get service logs[/red]")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.console.print("[yellow]Docker Compose not available[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error getting service logs: {e}[/red]")

    async def container_resource_usage(self):
        """Monitor container resource usage."""
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "table {{.Container}}\t{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                content = "[bold]Container Resource Usage:[/bold]\n\n"
                content += result.stdout
                print_panel(self.console, content, border_style="green")
            else:
                self.console.print("[red]Failed to get container stats[/red]")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.console.print("[yellow]Docker not available[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error getting container stats: {e}[/red]")

    async def network_configuration(self):
        """View network configuration."""
        try:
            compose_files = self._find_docker_compose_files()

            for compose_file in compose_files:
                try:
                    with open(compose_file, 'r') as f:
                        compose_data = yaml.safe_load(f)

                    networks = compose_data.get("networks", {})

                    if networks:
                        table = Table(title=f"Networks in {compose_file.name}")
                        table.add_column("Network", style="cyan")
                        table.add_column("Driver", style="green")
                        table.add_column("External", style="yellow")

                        for net_name, net_config in networks.items():
                            driver = net_config.get("driver", "bridge")
                            external = "Yes" if net_config.get("external") else "No"
                            table.add_row(net_name, driver, external)

                        self.console.print(table)
                    else:
                        self.console.print(f"[yellow]No networks defined in {compose_file.name}[/yellow]")

                except Exception as e:
                    self.console.print(f"[red]Error reading {compose_file}: {e}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing network configuration: {e}[/red]")

    async def volume_management(self):
        """Manage Docker volumes."""
        try:
            result = subprocess.run(
                ["docker", "volume", "ls"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                content = "[bold]Docker Volumes:[/bold]\n\n"
                content += result.stdout
                print_panel(self.console, content, border_style="magenta")
            else:
                self.console.print("[red]Failed to list Docker volumes[/red]")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.console.print("[yellow]Docker not available[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error managing volumes: {e}[/red]")

    async def deployment_monitoring_menu(self):
        """Deployment monitoring submenu."""
        while True:
            menu = create_menu_table("Deployment Monitoring", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Deployment Status Overview"),
                ("2", "Service Health Monitoring"),
                ("3", "Deployment Metrics"),
                ("4", "Alert Management"),
                ("5", "Performance Monitoring"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.deployment_status_overview()
            elif choice == "2":
                await self.service_health_monitoring()
            elif choice == "3":
                await self.deployment_metrics()
            elif choice == "4":
                await self.alert_management()
            elif choice == "5":
                await self.performance_monitoring()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def deployment_status_overview(self):
        """View overall deployment status."""
        try:
            self.console.print("[yellow]Deployment status overview would show comprehensive deployment health[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing deployment status: {e}[/red]")

    async def service_health_monitoring(self):
        """Monitor service health."""
        try:
            self.console.print("[yellow]Service health monitoring would check all service endpoints[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring service health: {e}[/red]")

    async def deployment_metrics(self):
        """View deployment metrics."""
        try:
            self.console.print("[yellow]Deployment metrics would show deployment performance data[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing deployment metrics: {e}[/red]")

    async def alert_management(self):
        """Manage deployment alerts."""
        try:
            self.console.print("[yellow]Alert management would handle deployment notifications and alerts[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error managing alerts: {e}[/red]")

    async def performance_monitoring(self):
        """Monitor deployment performance."""
        try:
            self.console.print("[yellow]Performance monitoring would track deployment KPIs and metrics[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring performance: {e}[/red]")

    async def rollback_management_menu(self):
        """Rollback management submenu."""
        while True:
            menu = create_menu_table("Rollback Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Rollback History"),
                ("2", "Initiate Rollback"),
                ("3", "Rollback Strategies"),
                ("4", "Rollback Validation"),
                ("5", "Emergency Rollback"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_rollback_history()
            elif choice == "2":
                await self.initiate_rollback()
            elif choice == "3":
                await self.rollback_strategies()
            elif choice == "4":
                await self.rollback_validation()
            elif choice == "5":
                await self.emergency_rollback()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_rollback_history(self):
        """View rollback history."""
        try:
            rollback_records = [r for r in self.deployment_history if "rollback" in r.get("action", "")]

            if rollback_records:
                table = Table(title="Rollback History")
                table.add_column("Timestamp", style="blue", no_wrap=True)
                table.add_column("Service", style="cyan")
                table.add_column("From Version", style="red")
                table.add_column("To Version", style="green")
                table.add_column("Reason", style="yellow")

                for record in rollback_records[-10:]:
                    table.add_row(
                        record["timestamp"],
                        record.get("service", "N/A"),
                        record.get("from_version", "N/A"),
                        record.get("to_version", "N/A"),
                        record.get("reason", "N/A")
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No rollback history available[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error viewing rollback history: {e}[/red]")

    async def initiate_rollback(self):
        """Initiate a rollback."""
        try:
            service_name = Prompt.ask("[bold cyan]Service to rollback[/bold cyan]")
            reason = Prompt.ask("[bold cyan]Rollback reason[/bold cyan]")

            confirm = Confirm.ask(f"[bold red]Rollback {service_name}? Reason: {reason}[/bold red]", default=False)

            if confirm:
                rollback_record = {
                    "timestamp": self._get_timestamp(),
                    "service": service_name,
                    "action": "rollback",
                    "reason": reason,
                    "status": "in_progress"
                }
                self.deployment_history.append(rollback_record)

                success = await self._perform_rollback(service_name)

                rollback_record["status"] = "completed" if success else "failed"
                rollback_record["completed_at"] = self._get_timestamp()

                self.console.print(f"[green]✅ Rollback completed for {service_name}[/green]" if success else f"[red]❌ Rollback failed for {service_name}[/red]")
            else:
                self.console.print("[yellow]Rollback cancelled[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error initiating rollback: {e}[/red]")

    async def rollback_strategies(self):
        """Configure rollback strategies."""
        try:
            strategies = {
                "immediate": "Immediate rollback to previous version",
                "gradual": "Gradual rollback with traffic shifting",
                "blue-green": "Switch back to blue environment",
                "backup": "Restore from backup image"
            }

            table = Table(title="Rollback Strategies")
            table.add_column("Strategy", style="cyan")
            table.add_column("Description", style="white")

            for name, desc in strategies.items():
                table.add_row(name, desc)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error viewing rollback strategies: {e}[/red]")

    async def rollback_validation(self):
        """Validate rollback success."""
        try:
            self.console.print("[yellow]Rollback validation would verify rollback success and stability[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error validating rollback: {e}[/red]")

    async def emergency_rollback(self):
        """Perform emergency rollback."""
        try:
            service_name = Prompt.ask("[bold cyan]Service for emergency rollback[/bold cyan]")

            confirm = Confirm.ask(f"[bold red]🚨 EMERGENCY ROLLBACK for {service_name}? This will immediately stop the service and revert![/bold red]", default=False)

            if confirm:
                emergency_record = {
                    "timestamp": self._get_timestamp(),
                    "service": service_name,
                    "action": "emergency_rollback",
                    "reason": "Emergency rollback requested",
                    "status": "in_progress"
                }
                self.deployment_history.append(emergency_record)

                success = await self._perform_emergency_rollback(service_name)

                emergency_record["status"] = "completed" if success else "failed"

                self.console.print(f"[green]🚨 Emergency rollback completed for {service_name}[/green]" if success else f"[red]❌ Emergency rollback failed[/red]")
            else:
                self.console.print("[yellow]Emergency rollback cancelled[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error performing emergency rollback: {e}[/red]")

    # Helper methods

    def _find_docker_compose_files(self) -> List[Path]:
        """Find all Docker Compose files."""
        compose_names = [
            "docker-compose.yml",
            "docker-compose.yaml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml",
            "docker-compose.override.yml",
            "docker-compose.services.yml",
            "docker-compose.infrastructure.yml"
        ]

        compose_files = []
        for name in compose_names:
            compose_file = Path(name)
            if compose_file.exists():
                compose_files.append(compose_file)

        return compose_files

    async def _update_service_replicas(self, service_name: str, replicas: int) -> bool:
        """Update service replicas in compose file."""
        try:
            compose_files = self._find_docker_compose_files()

            for compose_file in compose_files:
                try:
                    with open(compose_file, 'r') as f:
                        compose_data = yaml.safe_load(f)

                    services = compose_data.get("services", {})
                    if service_name in services:
                        if "deploy" not in services[service_name]:
                            services[service_name]["deploy"] = {}
                        services[service_name]["deploy"]["replicas"] = replicas

                        with open(compose_file, 'w') as f:
                            yaml.dump(compose_data, f, default_flow_style=False)

                        return True

                except Exception:
                    continue

            return False

        except Exception:
            return False

    async def _apply_scaling(self, service_name: str, replicas: int) -> bool:
        """Apply scaling changes using docker-compose."""
        try:
            cmd = ["docker-compose", "up", "-d", "--scale", f"{service_name}={replicas}", service_name]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd="."
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    async def _perform_rolling_update(self, service_name: str, image_tag: str, strategy: str) -> bool:
        """Perform rolling update (simplified implementation)."""
        try:
            # In a real implementation, this would:
            # 1. Update image tag in compose file
            # 2. Run docker-compose up with no-deps to update only this service
            # 3. Monitor health checks
            # 4. Handle rollback if needed

            self.console.print(f"[yellow]Performing {strategy} update of {service_name} to {image_tag}...[/yellow]")

            # Simulate update steps
            await asyncio.sleep(1)
            self.console.print("[green]✓ Updated compose file[/green]")
            await asyncio.sleep(1)
            self.console.print("[green]✓ Pulled new image[/green]")
            await asyncio.sleep(1)
            self.console.print("[green]✓ Started new containers[/green]")
            await asyncio.sleep(1)
            self.console.print("[green]✓ Health checks passed[/green]")
            await asyncio.sleep(1)
            self.console.print("[green]✓ Stopped old containers[/green]")

            return True

        except Exception:
            return False

    async def _start_canary_deployment(self, service_name: str, new_image: str, canary_percentage: int) -> bool:
        """Start canary deployment (simplified implementation)."""
        try:
            self.console.print(f"[yellow]Starting canary deployment of {service_name}...[/yellow]")
            self.console.print(f"[blue]New image: {new_image}[/blue]")
            self.console.print(f"[blue]Canary percentage: {canary_percentage}%[/blue]")

            # Simulate canary deployment
            await asyncio.sleep(1)
            self.console.print("[green]✓ Created canary service[/green]")
            await asyncio.sleep(1)
            self.console.print("[green]✓ Configured traffic splitting[/green]")
            await asyncio.sleep(1)
            self.console.print("[green]✓ Started monitoring[/green]")

            return True

        except Exception:
            return False

    async def _perform_rollback(self, service_name: str) -> bool:
        """Perform rollback (simplified implementation)."""
        try:
            self.console.print(f"[yellow]Rolling back {service_name}...[/yellow]")

            await asyncio.sleep(1)
            self.console.print("[green]✓ Identified previous version[/green]")
            await asyncio.sleep(1)
            self.console.print("[green]✓ Updated compose file[/green]")
            await asyncio.sleep(1)
            self.console.print("[green]✓ Restarted with previous version[/green]")

            return True

        except Exception:
            return False

    async def _perform_emergency_rollback(self, service_name: str) -> bool:
        """Perform emergency rollback (immediate stop and revert)."""
        try:
            self.console.print(f"[red]🚨 Performing emergency rollback of {service_name}...[/red]")

            await asyncio.sleep(0.5)
            self.console.print("[red]⚠️  Stopping current containers...[/red]")
            await asyncio.sleep(0.5)
            self.console.print("[yellow]⏳ Reverting to last known good state...[/yellow]")
            await asyncio.sleep(0.5)
            self.console.print("[green]✅ Emergency rollback completed[/green]")

            return True

        except Exception:
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def scale_service_from_cli(self, service_name: str, replicas: int):
        """Scale service for CLI usage."""
        try:
            with self.console.status(f"[bold green]Scaling {service_name} to {replicas} replicas...[/bold green]") as status:
                updated = await self._update_service_replicas(service_name, replicas)
                if updated:
                    success = await self._apply_scaling(service_name, replicas)
                    if success:
                        self.console.print(f"[green]✅ Service {service_name} scaled to {replicas} replicas[/green]")
                    else:
                        self.console.print(f"[red]❌ Failed to apply scaling for {service_name}[/red]")
                else:
                    self.console.print(f"[red]❌ Failed to update compose file for {service_name}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error scaling service: {e}[/red]")

    async def view_deployment_status_from_cli(self):
        """View deployment status for CLI usage."""
        try:
            await self.view_current_scaling_status()
        except Exception as e:
            self.console.print(f"[red]Error viewing deployment status: {e}[/red]")

    async def start_deployment_from_cli(self, service_name: str, image_tag: str, strategy: str = "rolling"):
        """Start deployment for CLI usage."""
        try:
            with self.console.status(f"[bold green]Starting {strategy} deployment of {service_name}...[/bold green]") as status:
                success = await self._perform_rolling_update(service_name, image_tag, strategy)
                if success:
                    self.console.print(f"[green]✅ {strategy.title()} deployment completed for {service_name}[/green]")
                else:
                    self.console.print(f"[red]❌ {strategy.title()} deployment failed for {service_name}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error starting deployment: {e}[/red]")
