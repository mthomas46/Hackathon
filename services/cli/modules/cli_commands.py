"""CLI Commands module for the CLI service.

This module contains the main CLI class and command handling logic,
extracted from the main CLI service to improve maintainability.
"""

import os
import time
import signal
import asyncio
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, TaskID
from contextlib import asynccontextmanager

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
from .handlers.service_actions import ServiceActions
from .managers.config.config_manager import ConfigManager
from .managers.config.settings_manager import SettingsManager
from .managers.analysis.analysis_service_manager import AnalysisServiceManager
from .managers.monitoring.advanced_monitoring_manager import AdvancedMonitoringManager
from .managers.services import (
    OrchestratorManager,
    AnalysisManager,
    DocStoreManager,
    SourceAgentManager,
    InfrastructureManager,
    BulkOperationsManager,
    InterpreterManager,
    DiscoveryAgentManager,
    MemoryAgentManager,
    SecureAnalyzerManager,
    SummarizerHubManager,
    CodeAnalyzerManager,
    NotificationServiceManager,
    LogCollectorManager,
    BedrockProxyManager,
    DeploymentManager,
    ArchitectureDigitizerManager
)


class CLICommands:
    """Main CLI command handler for the LLM Documentation Ecosystem."""

    def __init__(self):
        self.console = Console()
        self.clients = get_cli_clients()
        self.current_user = os.environ.get("USER", "cli_user")
        self.session_id = f"cli_session_{int(time.time() * 1000)}"

        # Enhanced caching system with TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes default TTL
        self._interrupt_requested = False

        # Initialize power-user managers
        self.orchestrator_manager = OrchestratorManager(self.console, self.clients, self._cache)
        self.analysis_manager = AnalysisManager(self.console, self.clients, self._cache)
        self.docstore_manager = DocStoreManager(self.console, self.clients, self._cache)
        self.source_agent_manager = SourceAgentManager(self.console, self.clients, self._cache)
        self.infrastructure_manager = InfrastructureManager(self.console, self.clients, self._cache)
        self.bulk_operations_manager = BulkOperationsManager(self.console, self.clients, self._cache)
        self.interpreter_manager = InterpreterManager(self.console, self.clients, self._cache)
        self.discovery_agent_manager = DiscoveryAgentManager(self.console, self.clients, self._cache)
        self.memory_agent_manager = MemoryAgentManager(self.console, self.clients, self._cache)
        self.secure_analyzer_manager = SecureAnalyzerManager(self.console, self.clients, self._cache)
        self.summarizer_hub_manager = SummarizerHubManager(self.console, self.clients, self._cache)
        self.code_analyzer_manager = CodeAnalyzerManager(self.console, self.clients, self._cache)
        self.notification_service_manager = NotificationServiceManager(self.console, self.clients, self._cache)
        self.log_collector_manager = LogCollectorManager(self.console, self.clients, self._cache)
        self.bedrock_proxy_manager = BedrockProxyManager(self.console, self.clients, self._cache)
        self.analysis_service_manager = AnalysisServiceManager(self.console, self.clients, self._cache)
        self.config_manager = ConfigManager(self.console, self.clients, self._cache)
        self.settings_manager = SettingsManager(self.console, self.clients, self._cache)
        self.deployment_manager = DeploymentManager(self.console, self.clients, self._cache)
        self.advanced_monitoring_manager = AdvancedMonitoringManager(self.console, self.clients, self._cache)
        self.architecture_digitizer_manager = ArchitectureDigitizerManager(self.console, self.clients, self._cache)

    def setup_interrupt_handling(self):
        """Setup signal handlers for graceful interrupt handling."""
        def signal_handler(signum, frame):
            self._interrupt_requested = True
            self.console.print("\n[yellow]⚠️  Interrupt received. Cleaning up...[/yellow]")
            # Force exit for immediate termination
            os._exit(1)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value with TTL check."""
        if key in self._cache:
            cached_item = self._cache[key]
            if time.time() - cached_item['timestamp'] < self._cache_ttl:
                return cached_item['data']
            else:
                # Cache expired, remove it
                del self._cache[key]
        return None

    async def cache_set(self, key: str, data: Any):
        """Set cached value with timestamp."""
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

    async def cache_invalidate(self, pattern: str = None):
        """Invalidate cache entries matching pattern."""
        if pattern:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache.clear()

    @asynccontextmanager
    async def progress_context(self, description: str = "Processing"):
        """Context manager for progress indicators."""
        with self.console.status(f"[bold green]{description}...[/bold green]") as status:
            try:
                yield status
            except Exception as e:
                self.console.print(f"[red]Error during {description}: {e}[/red]")
                raise

    async def run_with_progress(self, coro, description: str = "Processing"):
        """Run coroutine with progress indicator."""
        async with self.progress_context(description):
            return await coro

    def print_header(self):
        """Print CLI header."""
        print_panel(
            self.console,
            "[bold blue]LLM Documentation Consistency Ecosystem[/bold blue]\n"
            "[dim]Interactive CLI for prompt management and workflow orchestration[/dim]"
        )

    def print_menu(self):
        """Print main menu with improved organization."""
        # Core Operations
        core_menu = create_menu_table("🔧 Core Operations", ["Option", "Description"])
        add_menu_rows(core_menu, [
            ("1", "Document Store (CRUD, Search, Quality)"),
            ("2", "Analysis & Reports (Findings, Detectors, Quality)"),
            ("3", "Source Agent (Fetch, Normalize, Code Analysis)"),
            ("4", "Architecture Digitizer (Diagram Processing)"),
            ("5", "Workflow Orchestration"),
        ])

        # AI & Intelligence Services
        ai_menu = create_menu_table("🤖 AI & Intelligence", ["Option", "Description"])
        add_menu_rows(ai_menu, [
            ("6", "Interpreter Service (Query Analysis, Workflows)"),
            ("7", "Summarizer Hub (Ensemble AI, Multi-Provider)"),
            ("8", "Bedrock Proxy (AI Invocations, Templates)"),
            ("9", "Secure Analyzer (Content Security, Policies)"),
            ("10", "Code Analyzer (Endpoint Extraction, Scanning)"),
        ])

        # Infrastructure & Operations
        infra_menu = create_menu_table("🏗️ Infrastructure & Operations", ["Option", "Description"])
        add_menu_rows(infra_menu, [
            ("11", "Service Health & Monitoring"),
            ("12", "Orchestrator Management (Registry, Jobs)"),
            ("13", "Infrastructure (Redis, DLQ, Sagas, Tracing)"),
            ("14", "Notification Service (Delivery, DLQ)"),
            ("15", "Log Collector (Aggregation, Analytics)"),
        ])

        # Advanced Features
        advanced_menu = create_menu_table("⚡ Advanced Features", ["Option", "Description"])
        add_menu_rows(advanced_menu, [
            ("16", "Bulk Operations (Mass Analysis, Notifications)"),
            ("17", "Discovery Agent (API Registration)"),
            ("18", "Memory Agent (Context, Summaries)"),
            ("19", "Configuration Management"),
            ("20", "Deployment Controls"),
        ])

        # System Administration
        admin_menu = create_menu_table("⚙️ System Administration", ["Option", "Description"])
        add_menu_rows(admin_menu, [
            ("21", "Advanced Monitoring (Dashboards, SLO/SLA)"),
            ("22", "Analytics & Testing"),
            ("23", "Prompt Management"),
            ("s", "Settings & Service Status"),
            ("c", "Cache Management"),
            ("q", "Quit")
        ])

        # Display all menu sections
        self.console.print(core_menu)
        self.console.print()
        self.console.print(ai_menu)
        self.console.print()
        self.console.print(infra_menu)
        self.console.print()
        self.console.print(advanced_menu)
        self.console.print()
        self.console.print(admin_menu)

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

    async def analytics_testing_menu(self):
        """Combined analytics and testing submenu."""
        while True:
            menu = create_menu_table("Analytics & Testing", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Prompt Store Analytics"),
                ("2", "Run Integration Tests"),
                ("3", "A/B Testing (Coming Soon)"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = self.get_choice()

            if choice == "1":
                await self.analytics_menu()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.test_integration()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                self.ab_testing_menu()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

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
        """Main CLI loop with enhanced error handling and interrupt support."""
        self.print_header()
        self.setup_interrupt_handling()

        try:
            while True:
                if self._interrupt_requested:
                    break

                self.print_menu()
                choice = self.get_choice()

                if choice == "1":
                    await self.docstore_manager.docstore_management_menu()
                elif choice == "2":
                    await self.analysis_manager.analysis_reports_menu()
                elif choice == "3":
                    await self.source_agent_manager.source_agent_menu()
                elif choice == "4":
                    await self.architecture_digitizer_manager.architecture_digitizer_menu()
                elif choice == "5":
                    workflow_manager = WorkflowManager(self.console, self.clients)
                    await workflow_manager.workflow_orchestration_menu()
                elif choice == "6":
                    await self.interpreter_manager.interpreter_management_menu()
                elif choice == "7":
                    await self.summarizer_hub_manager.summarizer_hub_menu()
                elif choice == "8":
                    await self.bedrock_proxy_manager.bedrock_proxy_menu()
                elif choice == "9":
                    await self.secure_analyzer_manager.secure_analyzer_menu()
                elif choice == "10":
                    await self.code_analyzer_manager.code_analyzer_menu()
                elif choice == "11":
                    await self.display_health_status()
                elif choice == "12":
                    await self.orchestrator_manager.orchestrator_management_menu()
                elif choice == "13":
                    await self.infrastructure_manager.infrastructure_menu()
                elif choice == "14":
                    await self.notification_service_manager.notification_service_menu()
                elif choice == "15":
                    await self.log_collector_manager.log_collector_menu()
                elif choice == "16":
                    bulk_ops_manager = BulkOperationsManager(self.console, self.clients)
                    await bulk_ops_manager.bulk_operations_menu()
                elif choice == "17":
                    await self.discovery_agent_manager.discovery_agent_menu()
                elif choice == "18":
                    await self.memory_agent_manager.memory_agent_menu()
                elif choice == "19":
                    await self.config_manager.config_management_menu()
                elif choice == "20":
                    await self.deployment_manager.deployment_controls_menu()
                elif choice == "21":
                    await self.advanced_monitoring_manager.advanced_monitoring_menu()
                elif choice == "22":
                    await self.analytics_testing_menu()
                elif choice == "23":
                    prompt_manager = PromptManager(self.console, self.clients)
                    await prompt_manager.prompt_management_menu()
                elif choice.lower() == "s":
                    await self.settings_manager.run_menu_loop("Settings & Service Status")
                elif choice.lower() == "c":
                    await self.cache_management_menu()
                elif choice.lower() in ["q", "quit", "exit"]:
                    self.console.print("[bold blue]Goodbye! 👋[/bold blue]")
                    break
                else:
                    self.console.print("[red]Invalid option. Please try again.[/red]")

                # Add a small pause between menu interactions
                if not choice.lower() in ["q", "quit", "exit"]:
                    await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Operation interrupted by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]❌ Fatal error: {e}[/red]")
            fire_and_forget("error", f"CLI fatal error: {e}", ServiceNames.CLI)
        finally:
            # Cleanup operations
            self.console.print("[dim]Cleaning up...[/dim]")
            await self.cache_invalidate()  # Clear cache on exit

    async def cache_management_menu(self):
        """Cache management submenu."""
        while True:
            menu = create_menu_table("Cache Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Cache Statistics"),
                ("2", "Clear All Cache"),
                ("3", "Clear Service Cache"),
                ("4", "Set Cache TTL"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = self.get_choice()

            if choice == "1":
                await self._show_cache_stats()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.cache_invalidate()
                self.console.print("[green]✅ All cache cleared[/green]")
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                pattern = Prompt.ask("Service pattern (e.g., 'docstore', 'analysis')")
                await self.cache_invalidate(pattern)
                self.console.print(f"[green]✅ Cache cleared for pattern: {pattern}[/green]")
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                ttl = Prompt.ask("Cache TTL in seconds", default=str(self._cache_ttl))
                try:
                    self._cache_ttl = int(ttl)
                    self.console.print(f"[green]✅ Cache TTL set to {ttl} seconds[/green]")
                except ValueError:
                    self.console.print("[red]❌ Invalid TTL value[/red]")
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def _show_cache_stats(self):
        """Show cache statistics."""
        total_entries = len(self._cache)
        expired_entries = 0
        current_time = time.time()

        for key, item in self._cache.items():
            if current_time - item['timestamp'] >= self._cache_ttl:
                expired_entries += 1

        table = Table(title="Cache Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Total Entries", str(total_entries))
        table.add_row("Expired Entries", str(expired_entries))
        table.add_row("Active Entries", str(total_entries - expired_entries))
        table.add_row("Cache TTL", f"{self._cache_ttl} seconds")

        self.console.print(table)
