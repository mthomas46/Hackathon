"""Settings Manager module for CLI service.

Provides settings and configuration management including
service status checking and system diagnostics.
"""

from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from services.shared.core.constants_new import ServiceNames
from ...base.base_manager import BaseManager


class SettingsManager(BaseManager):
    """Manager for settings and system diagnostics."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)
        self.all_services = [
            ServiceNames.ORCHESTRATOR,
            ServiceNames.PROMPT_STORE,
            ServiceNames.SOURCE_AGENT,
            ServiceNames.ANALYSIS_SERVICE,
            ServiceNames.DOC_STORE,
            ServiceNames.DISCOVERY_AGENT,
            ServiceNames.INTERPRETER,
            ServiceNames.FRONTEND,
            ServiceNames.SUMMARIZER_HUB,
            ServiceNames.SECURE_ANALYZER,
            ServiceNames.MEMORY_AGENT,
            ServiceNames.CODE_ANALYZER,
            ServiceNames.LOG_COLLECTOR,
            ServiceNames.NOTIFICATION_SERVICE
        ]

    async def get_main_menu(self) -> List[Tuple[str, str]]:
        """Return the main menu items for settings operations."""
        return [
            ("1", "Check Service Status - View health of all services"),
            ("2", "Check Specific Service - Test individual service connectivity"),
            ("3", "System Diagnostics - Comprehensive system health check"),
            ("4", "Service Dependencies - View which services depend on others"),
            ("5", "Configuration Overview - Display current settings")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle a menu choice. Return True to continue, False to exit."""
        if choice == "1":
            await self.check_all_services_status()
        elif choice == "2":
            await self.check_specific_service()
        elif choice == "3":
            await self.system_diagnostics()
        elif choice == "4":
            await self.show_service_dependencies()
        elif choice == "5":
            await self.show_configuration()
        else:
            self.display.show_error("Invalid option. Please try again.")
        return True

    async def check_all_services_status(self) -> None:
        """Check and display the status of all services."""
        self.display.show_info("Checking status of all services...")

        health_results = await self.check_services_health(self.all_services)
        await self.display_service_health_table(health_results, "Complete Service Health Status")

        # Show summary
        healthy_count = sum(1 for result in health_results.values() if self.is_service_healthy(result))
        total_count = len(health_results)

        if healthy_count == total_count:
            self.display.show_success(f"All {total_count} services are healthy and running!")
        else:
            unhealthy_count = total_count - healthy_count
            self.display.show_warning(f"{healthy_count}/{total_count} services are healthy. {unhealthy_count} services are unreachable.")

    async def check_specific_service(self) -> None:
        """Check the status of a specific service selected by the user."""
        # Create a menu of services to choose from
        service_options = []
        for i, service_name in enumerate(self.all_services, 1):
            service_options.append((str(i), f"{service_name}"))

        service_options.append(("b", "Back to Settings"))

        while True:
            table = Table(title="Select Service to Check", border_style="cyan")
            table.add_column("Option", style="cyan", no_wrap=True)
            table.add_column("Service", style="white")

            for option, service in service_options:
                table.add_row(option, service)

            self.console.print(table)

            choice = Prompt.ask("[bold green]Select service[/bold green]").strip().lower()

            if choice == "b" or choice == "back":
                break
            elif choice.isdigit():
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(self.all_services):
                        service_name = self.all_services[index]
                        await self._check_single_service(service_name)
                        break
                    else:
                        self.display.show_error("Invalid service number.")
                except ValueError:
                    self.display.show_error("Invalid input. Please enter a number.")
            else:
                self.display.show_error("Invalid option. Please try again.")

    async def _check_single_service(self, service_name: str) -> None:
        """Check and display the status of a single service."""
        self.display.show_info(f"Checking status of {service_name}...")

        health_data = await self.check_service_health(service_name)

        table = Table(title=f"{service_name} Status", border_style="blue")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")
        table.add_column("URL", style="yellow")

        status_display, details = self.format_health_status(service_name, health_data)
        health_url = self._get_service_health_url(service_name)

        table.add_row(service_name, status_display, details, health_url)
        self.console.print(table)

        if self.is_service_healthy(health_data):
            self.display.show_success(f"✅ {service_name} is healthy and responding!")
        else:
            self.display.show_error(f"❌ {service_name} is not reachable.")
            self.display.show_info("Check that the service is running and network connectivity is available.")

    async def system_diagnostics(self) -> None:
        """Perform comprehensive system diagnostics."""
        self.display.show_info("Running comprehensive system diagnostics...")

        # Check all services
        health_results = await self.check_services_health(self.all_services)

        # Analyze results
        healthy_services = []
        unhealthy_services = []
        unreachable_services = []

        for service_name, health_data in health_results.items():
            if self.is_service_healthy(health_data):
                healthy_services.append(service_name)
            else:
                status = health_data.get("status")
                if status == "unreachable":
                    unreachable_services.append(service_name)
                else:
                    unhealthy_services.append(service_name)

        # Display results
        self.console.print("\n[bold blue]System Diagnostics Results:[/bold blue]")

        if healthy_services:
            self.console.print(f"[green]✅ Healthy Services ({len(healthy_services)}):[/green]")
            for service in healthy_services:
                self.console.print(f"  • {service}")

        if unreachable_services:
            self.console.print(f"[red]❌ Unreachable Services ({len(unreachable_services)}):[/red]")
            for service in unreachable_services:
                health_data = health_results[service]
                error = health_data.get("error", "Unknown error")
                self.console.print(f"  • {service}: {error}")

        if unhealthy_services:
            self.console.print(f"[yellow]⚠️ Unhealthy Services ({len(unhealthy_services)}):[/yellow]")
            for service in unhealthy_services:
                self.console.print(f"  • {service}")

        # Overall assessment
        total_services = len(self.all_services)
        healthy_count = len(healthy_services)

        self.console.print(f"\n[bold]Overall Status: {healthy_count}/{total_services} services operational[/bold]")

        if healthy_count == total_services:
            self.display.show_success("🎉 All systems operational! The ecosystem is fully functional.")
        elif healthy_count >= total_services * 0.8:  # 80% healthy
            self.display.show_warning("⚠️ Most systems operational. Some services may be unavailable.")
        else:
            self.display.show_error("❌ Critical systems unavailable. Ecosystem functionality is limited.")

    async def show_service_dependencies(self) -> None:
        """Show service dependency relationships."""
        self.display.show_info("Service Dependencies Overview")
        self.display.show_info("This shows which services are required by different CLI managers.")

        # For now, show a simple dependency map
        # In the future, this could be dynamically determined from manager get_required_services() methods
        dependencies = {
            "OrchestratorManager": ["Orchestrator", "Doc Store"],
            "AnalysisManager": ["Analysis Service", "Doc Store"],
            "SourceAgentManager": ["Source Agent"],
            "PromptManager": ["Prompt Store"],
            "DiscoveryAgentManager": ["Discovery Agent"],
            "SummarizerHubManager": ["Summarizer Hub"],
            "SecureAnalyzerManager": ["Secure Analyzer"],
            "InterpreterManager": ["Interpreter"],
            "MemoryAgentManager": ["Memory Agent"],
            "CodeAnalyzerManager": ["Code Analyzer"],
            "DeploymentManager": ["Orchestrator"],  # Infrastructure services
            "LogCollectorManager": ["Log Collector"],
            "NotificationServiceManager": ["Notification Service"]
        }

        table = Table(title="CLI Manager Dependencies", border_style="cyan")
        table.add_column("Manager", style="cyan", no_wrap=True)
        table.add_column("Required Services", style="white")

        for manager, services in dependencies.items():
            table.add_row(manager, ", ".join(services))

        self.console.print(table)

        self.display.show_info("Note: Managers will check these dependencies before allowing menu progression.")
        self.display.show_info("If required services are unavailable, you'll see an error message and cannot proceed.")

    async def show_configuration(self) -> None:
        """Show current configuration overview."""
        self.display.show_info("Current Configuration Overview")

        config_info = [
            ("Service Clients", "Configured for all ecosystem services"),
            ("Health Check Timeout", "5 seconds per service"),
            ("Cache TTL", "300 seconds (5 minutes)"),
            ("Async Operations", "Enabled for all service calls"),
            ("Error Handling", "Graceful degradation with user feedback"),
            ("Menu Validation", "Service dependency checks enabled")
        ]

        table = Table(title="Configuration Settings", border_style="green")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        for setting, value in config_info:
            table.add_row(setting, value)

        self.console.print(table)

        self.display.show_info("These settings ensure robust operation and user experience.")
        self.display.show_info("Service dependency validation prevents errors when services are unavailable.")
