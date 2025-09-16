#!/usr/bin/env python3
"""
CLI Service Health Checking Demo

This script demonstrates the new service health checking functionality
in the CLI service. It shows how the system protects users from
accessing features when required services are unavailable.

Usage:
    python scripts/demo_service_health.py

Features Demonstrated:
- Service health checking with timeouts
- Menu protection based on service availability
- Settings menu for service diagnostics
- Graceful error handling and user feedback
"""

import asyncio
from rich.console import Console
from rich.table import Table


def simulate_service_health_response(service_name: str, healthy: bool = True):
    """Simulate a service health response."""
    if healthy:
        return {
            "status": "healthy",
            "response": {"version": "1.0.0", "uptime": 3600},
            "timestamp": asyncio.get_event_loop().time()
        }
    else:
        return {
            "status": "unreachable",
            "error": "Connection refused",
            "timestamp": asyncio.get_event_loop().time()
        }


def format_health_status(service_name: str, health_data: dict) -> tuple[str, str]:
    """Format health status for display."""
    status = health_data.get("status", "unknown")

    if status == "healthy":
        status_display = "[green]✓ Healthy[/green]"
        details = "Service responding normally"
    elif status == "unreachable":
        error = health_data.get("error", "Unknown error")
        status_display = "[red]✗ Unreachable[/red]"
        details = f"Cannot connect: {error}"
    else:
        status_display = "[yellow]? Unknown[/yellow]"
        details = f"Status: {status}"

    return status_display, details


class DemoServiceHealth:
    """Demo class showing service health checking functionality."""

    def __init__(self):
        self.console = Console()
        self.services = [
            "Orchestrator", "Analysis Service", "Doc Store", "Source Agent",
            "Prompt Store", "Discovery Agent", "Interpreter", "Frontend",
            "Summarizer Hub", "Secure Analyzer", "Memory Agent", "Code Analyzer",
            "Log Collector", "Notification Service"
        ]

    async def demo_service_health_checking(self):
        """Demonstrate service health checking functionality."""
        self.console.print("\n[bold blue]🔍 CLI Service Health Checking Demo[/bold blue]")
        self.console.print("=" * 50)

        # Demo 1: Service Health Status Display
        self.console.print("\n[bold cyan]📊 Demo 1: Service Health Status Display[/bold cyan]")
        self.console.print("Simulating a full service health check...")

        # Create a table showing service health
        table = Table(title="Service Health Status", border_style="blue")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")

        # Simulate healthy services
        healthy_services = self.services[:10]  # First 10 are healthy
        unhealthy_services = self.services[10:]  # Last 4 are unhealthy

        for service in healthy_services:
            health_data = simulate_service_health_response(service, healthy=True)
            status_display, details = format_health_status(service, health_data)
            table.add_row(service, status_display, details)

        for service in unhealthy_services:
            health_data = simulate_service_health_response(service, healthy=False)
            status_display, details = format_health_status(service, health_data)
            table.add_row(service, status_display, details)

        self.console.print(table)

        healthy_count = len(healthy_services)
        total_count = len(self.services)
        self.console.print(f"\n[bold]Overall Status: {healthy_count}/{total_count} services operational[/bold]")

        # Demo 2: Service Dependency Validation
        self.console.print("\n[bold cyan]🛡️ Demo 2: Service Dependency Validation[/bold cyan]")

        # Show manager dependencies
        dependencies = {
            "OrchestratorManager": ["Orchestrator", "Doc Store"],
            "AnalysisManager": ["Analysis Service", "Doc Store"],
            "SourceAgentManager": ["Source Agent"],
            "SettingsManager": [],  # No dependencies
        }

        dep_table = Table(title="Manager Dependencies", border_style="green")
        dep_table.add_column("Manager", style="cyan", no_wrap=True)
        dep_table.add_column("Required Services", style="white")

        for manager, services in dependencies.items():
            dep_table.add_row(manager, ", ".join(services) if services else "None")
        self.console.print(dep_table)

        # Demo 3: Menu Protection Scenarios
        self.console.print("\n[bold cyan]🚫 Demo 3: Menu Protection Scenarios[/bold cyan]")

        scenarios = [
            ("✅ OrchestratorManager", ["Orchestrator", "Doc Store"], "All services healthy - access granted"),
            ("❌ AnalysisManager", ["Analysis Service", "Doc Store"], "Analysis Service unreachable - access blocked"),
            ("✅ SettingsManager", [], "No dependencies - access always granted"),
        ]

        for manager, deps, outcome in scenarios:
            self.console.print(f"\n{manager} - Required: {', '.join(deps) if deps else 'None'}")
            self.console.print(f"Result: {outcome}")

            if "blocked" in outcome:
                self.console.print("💡 User sees: 'Required services unavailable. Check Settings for status.'")

        # Demo 4: Settings Menu Options
        self.console.print("\n[bold cyan]⚙️ Demo 4: Settings Menu Options[/bold cyan]")

        settings_options = [
            ("1", "Check Service Status - View health of all services"),
            ("2", "Check Specific Service - Test individual service connectivity"),
            ("3", "System Diagnostics - Comprehensive system health check"),
            ("4", "Service Dependencies - View which services depend on others"),
            ("5", "Configuration Overview - Display current settings")
        ]

        settings_table = Table(title="Settings Menu", border_style="cyan")
        settings_table.add_column("Option", style="cyan", no_wrap=True)
        settings_table.add_column("Description", style="white")

        for option, description in settings_options:
            settings_table.add_row(option, description)

        self.console.print(settings_table)
        self.console.print("\n[bold]Access from main CLI menu: Press 's' for Settings[/bold]")

        self.console.print("\n[bold green]🎉 Demo Complete![/bold green]")
        self.console.print("\nKey Benefits:")
        self.console.print("• ✅ Proactive service health validation")
        self.console.print("• ✅ Graceful error handling and user feedback")
        self.console.print("• ✅ Menu protection prevents errors from unavailable services")
        self.console.print("• ✅ Settings menu provides comprehensive diagnostics")
        self.console.print("• ✅ Service dependency management ensures reliable operations")


async def main():
    """Run the service health checking demo."""
    demo = DemoServiceHealth()
    await demo.demo_service_health_checking()


if __name__ == "__main__":
    asyncio.run(main())
