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
from .orchestrator_manager import OrchestratorManager
from .analysis_manager import AnalysisManager
from .docstore_manager import DocStoreManager
from .source_agent_manager import SourceAgentManager
from .infrastructure_manager import InfrastructureManager
from .bulk_operations_manager import BulkOperationsManager
from .interpreter_manager import InterpreterManager
from .discovery_agent_manager import DiscoveryAgentManager
from .memory_agent_manager import MemoryAgentManager
from .secure_analyzer_manager import SecureAnalyzerManager
from .summarizer_hub_manager import SummarizerHubManager
from .code_analyzer_manager import CodeAnalyzerManager
from .notification_service_manager import NotificationServiceManager
from .log_collector_manager import LogCollectorManager
from .bedrock_proxy_manager import BedrockProxyManager
from .analysis_service_manager import AnalysisServiceManager
from .config_manager import ConfigManager
from .deployment_manager import DeploymentManager
from .advanced_monitoring_manager import AdvancedMonitoringManager


class CLICommands:
    """Main CLI command handler for the LLM Documentation Ecosystem."""

    def __init__(self):
        self.console = Console()
        self.clients = get_cli_clients()
        self.current_user = os.environ.get("USER", "cli_user")
        self.session_id = f"cli_session_{int(time.time() * 1000)}"

        # Initialize power-user managers
        self.orchestrator_manager = OrchestratorManager(self.console, self.clients)
        self.analysis_manager = AnalysisManager(self.console, self.clients)
        self.docstore_manager = DocStoreManager(self.console, self.clients)
        self.source_agent_manager = SourceAgentManager(self.console, self.clients)
        self.infrastructure_manager = InfrastructureManager(self.console, self.clients)
        self.bulk_operations_manager = BulkOperationsManager(self.console, self.clients)
        self.interpreter_manager = InterpreterManager(self.console, self.clients)
        self.discovery_agent_manager = DiscoveryAgentManager(self.console, self.clients)
        self.memory_agent_manager = MemoryAgentManager(self.console, self.clients)
        self.secure_analyzer_manager = SecureAnalyzerManager(self.console, self.clients)
        self.summarizer_hub_manager = SummarizerHubManager(self.console, self.clients)
        self.code_analyzer_manager = CodeAnalyzerManager(self.console, self.clients)
        self.notification_service_manager = NotificationServiceManager(self.console, self.clients)
        self.log_collector_manager = LogCollectorManager(self.console, self.clients)
        self.bedrock_proxy_manager = BedrockProxyManager(self.console, self.clients)
        self.analysis_service_manager = AnalysisServiceManager(self.console, self.clients)
        self.config_manager = ConfigManager(self.console, self.clients)
        self.deployment_manager = DeploymentManager(self.console, self.clients)
        self.advanced_monitoring_manager = AdvancedMonitoringManager(self.console, self.clients)

    def print_header(self):
        """Print CLI header."""
        print_panel(
            self.console,
            "[bold blue]LLM Documentation Consistency Ecosystem[/bold blue]\n"
            "[dim]Interactive CLI for prompt management and workflow orchestration[/dim]"
        )

    def print_menu(self):
        """Print main menu."""
        menu = create_menu_table("Power User CLI - Main Menu", ["Option", "Description"])
        add_menu_rows(menu, [
            ("1", "Prompt Management"),
            ("2", "Workflow Orchestration"),
            ("3", "Orchestrator Management (Registry, Jobs, Infrastructure)"),
            ("4", "Analysis & Reports (Findings, Detectors, Quality)"),
            ("5", "Document Store (Documents, Analyses, Search)"),
            ("6", "Source Agent (Fetch, Normalize, Code Analysis)"),
            ("7", "Service Health & Monitoring"),
            ("8", "Infrastructure (Redis, DLQ, Sagas, Tracing)"),
                ("9", "Bulk Operations (Mass Analysis, Notifications)"),
                ("10", "Analytics & Testing"),
                ("11", "Interpreter Service (Query Analysis, Workflows)"),
                ("12", "Discovery Agent (API Discovery, Service Registration)"),
                ("13", "Memory Agent (Operational Context, Event Summaries)"),
                ("14", "Secure Analyzer (Content Security, Policy Enforcement)"),
                ("15", "Summarizer Hub (Ensemble AI, Multi-Provider Operations)"),
                ("16", "Code Analyzer (Endpoint Extraction, Security Scanning)"),
                ("17", "Notification Service (Owner Resolution, Delivery, DLQ)"),
                ("18", "Log Collector (Aggregation, Streaming, Pattern Analysis)"),
                ("19", "Bedrock Proxy (AI Model Invocations, Templates, History)"),
                ("20", "Analysis Service (Document Analysis, Findings, Reports)"),
                ("21", "Configuration Management (Configs, Environment, Validation)"),
                ("22", "Deployment Controls (Scaling, Updates, Traffic Management)"),
                ("23", "Advanced Monitoring (Dashboards, Alerts, SLO/SLA)"),
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
        """Main CLI loop."""
        self.print_header()

        while True:
            self.print_menu()
            choice = self.get_choice()

            if choice == "1":
                prompt_manager = PromptManager(self.console, self.clients)
                await prompt_manager.prompt_management_menu()
            elif choice == "2":
                workflow_manager = WorkflowManager(self.console, self.clients)
                await workflow_manager.workflow_orchestration_menu()
            elif choice == "3":
                orchestrator_manager = OrchestratorManager(self.console, self.clients)
                await orchestrator_manager.orchestrator_management_menu()
            elif choice == "4":
                analysis_manager = AnalysisManager(self.console, self.clients)
                await analysis_manager.analysis_reports_menu()
            elif choice == "5":
                docstore_manager = DocStoreManager(self.console, self.clients)
                await docstore_manager.docstore_management_menu()
            elif choice == "6":
                source_agent_manager = SourceAgentManager(self.console, self.clients)
                await source_agent_manager.source_agent_menu()
            elif choice == "7":
                await self.display_health_status()
            elif choice == "8":
                infrastructure_manager = InfrastructureManager(self.console, self.clients)
                await infrastructure_manager.infrastructure_menu()
            elif choice == "9":
                bulk_ops_manager = BulkOperationsManager(self.console, self.clients)
                await bulk_ops_manager.bulk_operations_menu()
            elif choice == "10":
                await self.analytics_testing_menu()
            elif choice == "11":
                await self.interpreter_manager.interpreter_management_menu()
            elif choice == "12":
                await self.discovery_agent_manager.discovery_agent_menu()
            elif choice == "13":
                await self.memory_agent_manager.memory_agent_menu()
            elif choice == "14":
                await self.secure_analyzer_manager.secure_analyzer_menu()
            elif choice == "15":
                await self.summarizer_hub_manager.summarizer_hub_menu()
            elif choice == "16":
                await self.code_analyzer_manager.code_analyzer_menu()
            elif choice == "17":
                await self.notification_service_manager.notification_service_menu()
            elif choice == "18":
                await self.log_collector_manager.log_collector_menu()
            elif choice == "19":
                await self.bedrock_proxy_manager.bedrock_proxy_menu()
            elif choice == "20":
                await self.analysis_service_manager.analysis_service_menu()
            elif choice == "21":
                await self.config_manager.config_management_menu()
            elif choice == "22":
                await self.deployment_manager.deployment_controls_menu()
            elif choice == "23":
                await self.advanced_monitoring_manager.advanced_monitoring_menu()
            elif choice.lower() in ["q", "quit", "exit"]:
                self.console.print("[bold blue]Goodbye! 👋[/bold blue]")
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")
