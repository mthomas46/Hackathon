"""CLI Commands module for the CLI service.

This module contains the main CLI class and command handling logic,
extracted from the main CLI service to improve maintainability.
"""

import os
import time
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget

from .shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    get_service_health_url,
    create_health_status_display,
    log_cli_metrics
)
from .service_actions import ServiceActions


class CLICommands:
    """Main CLI command handler for the LLM Documentation Ecosystem."""

    def __init__(self):
        self.console = Console()
        self.clients = get_cli_clients()
        self.current_user = os.environ.get("USER", "cli_user")
        self.session_id = f"cli_session_{int(time.time() * 1000)}"

    def print_header(self):
        """Print CLI header."""
        print_panel(
            self.console,
            "[bold blue]LLM Documentation Consistency Ecosystem[/bold blue]\n"
            "[dim]Interactive CLI for prompt management and workflow orchestration[/dim]"
        )

    def print_menu(self):
        """Print main menu."""
        menu = create_menu_table("Main Menu", ["Option", "Description"])
        add_menu_rows(menu, [
            ("1", "Prompt Management"),
            ("2", "A/B Testing"),
            ("3", "Workflow Orchestration"),
            ("4", "Analytics & Monitoring"),
            ("5", "Service Health Check"),
            ("6", "Service Actions (API-driven) & Bulk Ops"),
            ("7", "Test Service Integration"),
            ("q", "Quit")
        ])
        self.console.print(menu)

    def get_choice(self, prompt: str = "Select option") -> str:
        """Get user choice with validation."""
        return Prompt.ask(f"[bold green]{prompt}[/bold green]")

    async def check_service_health(self) -> Dict[str, Any]:
        """Check health of all services."""
        services = {
            service_name: get_service_health_url(self.clients, service_name)
            for service_name in [
                ServiceNames.ORCHESTRATOR,
                ServiceNames.PROMPT_STORE,
                ServiceNames.SOURCE_AGENT,
                ServiceNames.ANALYSIS_SERVICE,
                ServiceNames.DOC_STORE
            ]
        }

        results = {}
        with self.console.status("[bold green]Checking service health...") as status:
            for service_name, url in services.items():
                try:
                    response = await self.clients.get_json(url)
                    results[service_name] = {
                        "status": "healthy",
                        "response": response,
                        "timestamp": time.time()
                    }
                except Exception as e:
                    results[service_name] = {
                        "status": "unhealthy",
                        "error": str(e),
                        "timestamp": time.time()
                    }

        return results

    async def display_health_status(self):
        """Display service health status."""
        health_data = await self.check_service_health()

        table = Table(title="Service Health Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")

        for service, data in health_data.items():
            status_display, details = create_health_status_display(service, data)
            table.add_row(service, status_display, details)

        self.console.print(table)

    async def analytics_menu(self):
        """Analytics submenu."""
        try:
            response = await self.clients.get_json("prompt-store/analytics")
            content = format_analytics_display(response)
            print_panel(self.console, content, border_style="cyan")
        except Exception as e:
            self.console.print(f"[red]Error fetching analytics: {e}[/red]")

    def ab_testing_menu(self):
        """Placeholder for A/B testing menu."""
        self.console.print("[yellow]A/B Testing menu coming soon![/yellow]")

    async def test_integration(self) -> Dict[str, Any]:
        """Test integration between all services."""
        self.console.print("\n[bold green]Testing Service Integration[/bold green]")

        integration_tests = [
            ("Prompt Store Health", self._test_prompt_store_integration),
            ("Interpreter Integration", self._test_interpreter_integration),
            ("Orchestrator Integration", self._test_orchestrator_integration),
            ("Analysis Service Integration", self._test_analysis_integration),
            ("Cross-Service Workflow", self._test_cross_service_workflow)
        ]

        results = {}
        for test_name, test_func in integration_tests:
            try:
                self.console.print(f"🔄 Testing {test_name}...")
                result = await test_func()
                results[test_name] = result
                status = "[green]✅ PASS[/green]" if result else "[red]❌ FAIL[/red]"
                self.console.print(f"   {status}")
            except Exception as e:
                results[test_name] = False
                self.console.print(f"   [red]❌ ERROR: {e}[/red]")

        # Summary
        passed = sum(1 for r in results.values() if r)
        total = len(results)

        self.console.print(f"\n[bold]Integration Test Summary: {passed}/{total} passed[/bold]")

        if passed == total:
            self.console.print("[green]🎉 All services are properly integrated![/green]")
        else:
            self.console.print("[yellow]⚠️  Some integration issues detected.[/yellow]")

        return results

    async def _test_prompt_store_integration(self) -> bool:
        """Test Prompt Store integration."""
        try:
            health = await self.clients.get_json("prompt-store/health")
            if health.get("status") != "healthy":
                return False
            prompts = await self.clients.get_json("prompt-store/prompts?limit=1")
            return "prompts" in prompts
        except:
            return False

    async def _test_interpreter_integration(self) -> bool:
        """Test Interpreter integration."""
        try:
            health = await self.clients.get_json("interpreter/health")
            if health.get("status") != "healthy":
                return False
            result = await self.clients.post_json("interpreter/interpret", {
                "query": "analyze this document"
            })
            return "intent" in result
        except:
            return False

    async def _test_orchestrator_integration(self) -> bool:
        """Test Orchestrator integration."""
        try:
            health = await self.clients.get_json("orchestrator/health/system")
            return "overall_healthy" in health
        except:
            return False

    async def _test_analysis_integration(self) -> bool:
        """Test Analysis Service integration."""
        try:
            health = await self.clients.get_json("analysis-service/integration/health")
            return "integrations" in health
        except:
            return False

    async def _test_cross_service_workflow(self) -> bool:
        """Test cross-service workflow execution."""
        try:
            result = await self.clients.post_json("orchestrator/query", {
                "query": "show me system status"
            })
            return "interpretation" in result
        except:
            return False

    async def run(self):
        """Main CLI loop."""
        self.print_header()

        while True:
            self.print_menu()
            choice = self.get_choice()

            if choice == "1":
                prompt_manager = PromptManager(self.console, self.clients)
                await prompt_manager.prompt_management_menu()
            elif choice == "2":
                self.ab_testing_menu()
            elif choice == "3":
                workflow_manager = WorkflowManager(self.console, self.clients)
                await workflow_manager.workflow_orchestration_menu()
            elif choice == "4":
                await self.analytics_menu()
            elif choice == "5":
                await self.display_health_status()
            elif choice == "6":
                actions = ServiceActions(self.console, self.clients)
                await actions.run()
            elif choice == "7":
                await self.test_integration()
            elif choice.lower() in ["q", "quit", "exit"]:
                self.console.print("[bold blue]Goodbye! 👋[/bold blue]")
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")
