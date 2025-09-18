"""
Unified Service Registry

Central registry for all service adapters in the ecosystem.
Provides standardized discovery, management, and interaction with all services.
"""

from typing import Dict, List, Optional, Any, Tuple
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID

from .base_service_adapter import BaseServiceAdapter, ServiceInfo, ServiceStatus, CommandResult
from .analysis_service_adapter import AnalysisServiceAdapter
from .orchestrator_adapter import OrchestratorAdapter
from .source_agent_adapter import SourceAgentAdapter
from .github_mcp_adapter import GitHubMCPAdapter
from .doc_store_adapter import DocStoreAdapter
from .memory_agent_adapter import MemoryAgentAdapter
from .discovery_agent_adapter import DiscoveryAgentAdapter
from .bedrock_proxy_adapter import BedrockProxyAdapter
from .frontend_adapter import FrontendAdapter
from .interpreter_adapter import InterpreterAdapter


class ServiceRegistry:
    """
    Central registry for all ecosystem services
    
    Manages:
    - Service discovery and registration
    - Unified health monitoring
    - Cross-service command execution
    - Ecosystem-wide testing
    """
    
    def __init__(self, console: Console, clients: Any):
        self.console = console
        self.clients = clients
        self._adapters: Dict[str, BaseServiceAdapter] = {}
        self._service_configs = {
            # Core services
            "analysis-service": {
                "url": "http://hackathon-analysis-service-1:5020",
                "adapter_class": AnalysisServiceAdapter,
                "priority": 1
            },
            "orchestrator": {
                "url": "http://hackathon-orchestrator-1:5099", 
                "adapter_class": OrchestratorAdapter,
                "priority": 1
            },
            "doc_store": {
                "url": "http://hackathon-doc_store-1:5087",
                "adapter_class": DocStoreAdapter,
                "priority": 1
            },
            
            # Agent services
            "source-agent": {
                "url": "http://hackathon-source-agent-1:5000",
                "adapter_class": SourceAgentAdapter,
                "priority": 2
            },
            "memory-agent": {
                "url": "http://hackathon-memory-agent-1:5040",
                "adapter_class": MemoryAgentAdapter,
                "priority": 2
            },
            "discovery-agent": {
                "url": "http://hackathon-discovery-agent-1:5045",
                "adapter_class": DiscoveryAgentAdapter,
                "priority": 2
            },
            
            # Integration services
            "github-mcp": {
                "url": "http://hackathon-github-mcp-1:5072",
                "adapter_class": GitHubMCPAdapter,
                "priority": 2
            },
            "bedrock-proxy": {
                "url": "http://hackathon-bedrock-proxy-1:7090",
                "adapter_class": BedrockProxyAdapter,
                "priority": 3
            },
            
            # Utility services
            "frontend": {
                "url": "http://hackathon-frontend-1:3000",
                "adapter_class": FrontendAdapter,
                "priority": 3
            },
            "prompt_store": {
                "url": "http://hackathon-prompt_store-1:5110",
                "adapter_class": None,
                "priority": 2
            },
            "interpreter": {
                "url": "http://hackathon-interpreter-1:5120",
                "adapter_class": InterpreterAdapter,
                "priority": 2
            },
            
            # Monitoring and logging
            "log-collector": {
                "url": "http://hackathon-log-collector-1:5080",
                "adapter_class": None,
                "priority": 3
            },
            "notification-service": {
                "url": "http://hackathon-notification-service-1:5095",
                "adapter_class": None,
                "priority": 3
            },
            
            # Analysis and security
            "architecture-digitizer": {
                "url": "http://hackathon-architecture-digitizer-1:5105",
                "adapter_class": None,
                "priority": 2
            },
            "secure-analyzer": {
                "url": "http://hackathon-secure-analyzer-1:5070",
                "adapter_class": None,
                "priority": 2
            }
        }
    
    async def initialize(self) -> None:
        """Initialize all service adapters"""
        self.console.print("[bold blue]🚀 Initializing Service Registry...[/bold blue]")
        
        for service_name, config in self._service_configs.items():
            try:
                adapter_class = config["adapter_class"]
                if adapter_class:
                    adapter = adapter_class(service_name, config["url"], self.console, self.clients)
                else:
                    adapter = GenericServiceAdapter(service_name, config["url"], self.console, self.clients)
                
                self._adapters[service_name] = adapter
                self.console.print(f"  ✅ Registered {service_name}")
                
            except Exception as e:
                self.console.print(f"  ❌ Failed to register {service_name}: {e}")
        
        self.console.print(f"[green]✅ Registry initialized with {len(self._adapters)} services[/green]")
    
    def get_adapter(self, service_name: str) -> Optional[BaseServiceAdapter]:
        """Get adapter for specific service"""
        return self._adapters.get(service_name)
    
    def list_services(self) -> List[str]:
        """Get list of all registered services"""
        return list(self._adapters.keys())
    
    async def health_check_all(self) -> Dict[str, CommandResult]:
        """Perform health check on all services"""
        self.console.print("[bold blue]🔍 Performing ecosystem health check...[/bold blue]")
        
        results = {}
        with Progress() as progress:
            task = progress.add_task("Health checking services...", total=len(self._adapters))
            
            # Run health checks in parallel for better performance
            async def check_service(name: str, adapter: BaseServiceAdapter) -> Tuple[str, CommandResult]:
                result = await adapter.health_check()
                progress.advance(task)
                return name, result
            
            # Execute all health checks concurrently
            health_tasks = [
                check_service(name, adapter) 
                for name, adapter in self._adapters.items()
            ]
            
            health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
            
            for result in health_results:
                if isinstance(result, Exception):
                    self.console.print(f"❌ Health check failed with exception: {result}")
                else:
                    name, health_result = result
                    results[name] = health_result
        
        # Display summary
        self._display_health_summary(results)
        return results
    
    def _display_health_summary(self, results: Dict[str, CommandResult]) -> None:
        """Display formatted health check summary"""
        table = Table(title="🏥 Ecosystem Health Summary")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Response Time", justify="right")
        table.add_column("Message", style="dim")
        
        healthy_count = 0
        total_count = len(results)
        
        for service_name, result in results.items():
            if result.success:
                status = "✅ HEALTHY"
                status_style = "green"
                healthy_count += 1
            else:
                status = "❌ UNHEALTHY"
                status_style = "red"
            
            response_time = f"{result.execution_time:.3f}s" if result.execution_time > 0 else "N/A"
            message = result.message or result.error or "No message"
            
            table.add_row(
                service_name,
                f"[{status_style}]{status}[/{status_style}]",
                response_time,
                message[:50] + "..." if len(message) > 50 else message
            )
        
        self.console.print(table)
        
        # Health percentage
        health_percentage = (healthy_count / total_count) * 100 if total_count > 0 else 0
        if health_percentage >= 90:
            health_status = "[green]EXCELLENT[/green]"
        elif health_percentage >= 75:
            health_status = "[yellow]GOOD[/yellow]"
        elif health_percentage >= 50:
            health_status = "[orange]FAIR[/orange]"
        else:
            health_status = "[red]POOR[/red]"
        
        summary_panel = Panel(
            f"Healthy Services: {healthy_count}/{total_count}\n"
            f"Health Percentage: {health_percentage:.1f}%\n"
            f"Overall Status: {health_status}",
            title="[bold]📊 Health Summary[/bold]"
        )
        self.console.print(summary_panel)
    
    async def execute_ecosystem_command(self, service_name: str, command: str, **kwargs) -> CommandResult:
        """Execute command on specific service"""
        adapter = self.get_adapter(service_name)
        if not adapter:
            return CommandResult(
                success=False,
                error=f"Service '{service_name}' not found in registry"
            )
        
        return await adapter.execute_command(command, **kwargs)
    
    async def discover_service_capabilities(self) -> Dict[str, List[Tuple[str, str, str]]]:
        """Discover capabilities of all services"""
        capabilities = {}
        
        for service_name, adapter in self._adapters.items():
            try:
                commands = await adapter.get_available_commands()
                capabilities[service_name] = commands
            except Exception as e:
                self.console.print(f"❌ Failed to discover capabilities for {service_name}: {e}")
                capabilities[service_name] = []
        
        return capabilities
    
    def display_ecosystem_overview(self) -> None:
        """Display comprehensive ecosystem overview"""
        self.console.print(Panel(
            f"[bold blue]🌐 LLM Documentation Ecosystem[/bold blue]\n\n"
            f"Total Services: {len(self._adapters)}\n"
            f"Core Services: {len([s for s, c in self._service_configs.items() if c['priority'] == 1])}\n"
            f"Agent Services: {len([s for s, c in self._service_configs.items() if c['priority'] == 2])}\n"
            f"Utility Services: {len([s for s, c in self._service_configs.items() if c['priority'] == 3])}",
            title="🏗️ Ecosystem Overview"
        ))


class GenericServiceAdapter(BaseServiceAdapter):
    """Generic adapter for services without specialized implementations"""
    
    def get_service_info(self) -> ServiceInfo:
        return ServiceInfo(
            name=self.service_name,
            port=int(self.base_url.split(':')[-1]) if ':' in self.base_url else 80,
            version="unknown",
            status=ServiceStatus.UNKNOWN,
            description=f"Generic service adapter for {self.service_name}",
            features=["Health Check", "Basic Connectivity"]
        )
    
    async def health_check(self) -> CommandResult:
        return await self.ping()
    
    async def get_available_commands(self) -> List[Tuple[str, str, str]]:
        return [
            ("ping", "Test basic connectivity", "ping"),
            ("health", "Check service health", "health")
        ]
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        if command == "ping":
            return await self.ping()
        elif command == "health":
            return await self.health_check()
        else:
            return CommandResult(
                success=False,
                error=f"Command '{command}' not supported by generic adapter"
            )
