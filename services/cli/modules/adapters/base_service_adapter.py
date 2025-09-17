"""
Base Service Adapter

Provides a standardized interface for all service interactions through the CLI.
This creates a unified pattern for service communication, health monitoring,
and feature access across the entire ecosystem.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


class ServiceStatus(Enum):
    """Standard service status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy" 
    UNKNOWN = "unknown"
    DEGRADED = "degraded"


@dataclass
class ServiceInfo:
    """Standard service information structure"""
    name: str
    port: int
    version: str
    status: ServiceStatus
    description: str
    features: List[str]
    dependencies: List[str] = None
    endpoints: Dict[str, str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.endpoints is None:
            self.endpoints = {}


@dataclass
class CommandResult:
    """Standard command result structure"""
    success: bool
    data: Any = None
    message: str = ""
    error: str = ""
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseServiceAdapter(ABC):
    """
    Base class for all service adapters.
    
    Provides standardized interface for:
    - Health checking
    - Feature discovery
    - Command execution
    - Result formatting
    - Error handling
    """
    
    def __init__(self, service_name: str, base_url: str, console: Console, clients: Any):
        self.service_name = service_name
        self.base_url = base_url
        self.console = console
        self.clients = clients
        self._service_info: Optional[ServiceInfo] = None
    
    @abstractmethod
    def get_service_info(self) -> ServiceInfo:
        """Get standardized service information"""
        pass
    
    @abstractmethod
    async def health_check(self) -> CommandResult:
        """Perform standardized health check"""
        pass
    
    @abstractmethod
    async def get_available_commands(self) -> List[Tuple[str, str, str]]:
        """Get list of available commands: (name, description, usage)"""
        pass
    
    @abstractmethod
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute a service-specific command"""
        pass
    
    # Standard helper methods
    async def ping(self) -> CommandResult:
        """Basic connectivity test"""
        try:
            import time
            start_time = time.time()
            url = f"{self.base_url}/health"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            if response:
                return CommandResult(
                    success=True,
                    data=response,
                    message=f"{self.service_name} is reachable",
                    execution_time=execution_time
                )
            else:
                return CommandResult(
                    success=False,
                    error=f"{self.service_name} is not responding",
                    execution_time=execution_time
                )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Connection failed: {str(e)}"
            )
    
    def display_service_info(self) -> None:
        """Display formatted service information"""
        info = self.get_service_info()
        
        # Create info panel
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Property", style="bold blue")
        info_table.add_column("Value")
        
        info_table.add_row("Service", info.name)
        info_table.add_row("Port", str(info.port))
        info_table.add_row("Version", info.version)
        info_table.add_row("Status", info.status.value)
        info_table.add_row("Description", info.description)
        
        self.console.print(Panel(info_table, title=f"[bold green]{info.name} Information[/bold green]"))
        
        # Display features
        if info.features:
            features_table = Table(show_header=True)
            features_table.add_column("Features", style="cyan")
            for feature in info.features:
                features_table.add_row(feature)
            self.console.print(Panel(features_table, title="Available Features"))
    
    def display_result(self, result: CommandResult) -> None:
        """Display formatted command result"""
        if result.success:
            self.console.print(f"✅ [green]{result.message}[/green]")
            if result.data:
                self.console.print_json(json.dumps(result.data, indent=2))
        else:
            self.console.print(f"❌ [red]{result.error}[/red]")
        
        if result.execution_time > 0:
            self.console.print(f"⏱️  Execution time: {result.execution_time:.3f}s")
    
    async def test_all_endpoints(self) -> Dict[str, CommandResult]:
        """Test all available endpoints for the service"""
        results = {}
        
        # Test health endpoint
        results["health"] = await self.health_check()
        
        # Test ping
        results["ping"] = await self.ping()
        
        # Test service-specific commands
        commands = await self.get_available_commands()
        for command_name, _, _ in commands:
            try:
                result = await self.execute_command(command_name)
                results[command_name] = result
            except Exception as e:
                results[command_name] = CommandResult(
                    success=False,
                    error=f"Command test failed: {str(e)}"
                )
        
        return results
