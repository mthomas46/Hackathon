"""
Discovery Agent Service Adapter for CLI interaction
Handles service discovery, registration, and ecosystem mapping
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .base_service_adapter import BaseServiceAdapter, ServiceInfo, ServiceStatus, CommandResult


class DiscoveryAgentAdapter(BaseServiceAdapter):
    """
    Adapter for Discovery Agent service - handles service discovery and registration
    """
    
    def __init__(self, console: Console, clients: Any, base_url: str):
        super().__init__(console, clients, base_url)
        self.service_info = ServiceInfo(
            name="discovery_agent",
            version="1.0.0",
            description="Service discovery and registration management",
            endpoints=[
                "/health",
                "/services",
                "/services/{service_id}",
                "/register",
                "/discover",
                "/status",
                "/topology"
            ],
            dependencies=["redis", "network"]
        )
    
    def get_available_commands(self) -> List[str]:
        """Return list of available commands for this service"""
        return [
            "status",
            "services",
            "discover",
            "register",
            "unregister",
            "topology",
            "health-check",
            "stats"
        ]
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute a command against the Discovery Agent service"""
        command_map = {
            "status": self._get_status,
            "services": self._list_services,
            "discover": self._discover_services,
            "register": self._register_service,
            "unregister": self._unregister_service,
            "topology": self._get_topology,
            "health-check": self._health_check_services,
            "stats": self._get_stats
        }
        
        if command not in command_map:
            return CommandResult(
                success=False,
                error=f"Unknown command: {command}. Available: {', '.join(self.get_available_commands())}"
            )
        
        return await command_map[command](**kwargs)
    
    # Private command implementations
    async def _get_status(self) -> CommandResult:
        """Get Discovery Agent service status"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/status"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Discovery Agent status retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get Discovery Agent status: {str(e)}"
            )
    
    async def _list_services(self, service_type: Optional[str] = None) -> CommandResult:
        """List discovered services"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/services"
            params = {}
            if service_type:
                params["type"] = service_type
            
            response = await self.clients.get_json(url, params=params)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {len(response.get('services', []))} services",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list services: {str(e)}"
            )
    
    async def _discover_services(self, query: Optional[str] = None) -> CommandResult:
        """Discover services in the ecosystem"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/discover"
            payload = {}
            if query:
                payload["query"] = query
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Discovery completed: {len(response.get('discovered', []))} services found",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to discover services: {str(e)}"
            )
    
    async def _register_service(self, name: str, url: str, service_type: str = "unknown", metadata: Optional[Dict] = None) -> CommandResult:
        """Register a new service"""
        try:
            start_time = time.time()
            register_url = f"{self.base_url}/register"
            payload = {
                "name": name,
                "url": url,
                "type": service_type,
                "metadata": metadata or {}
            }
            
            response = await self.clients.post_json(register_url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Service registered successfully: {name}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to register service {name}: {str(e)}"
            )
    
    async def _unregister_service(self, service_id: str) -> CommandResult:
        """Unregister a service"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/services/{service_id}"
            response = await self.clients.delete_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Service unregistered: {service_id}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to unregister service {service_id}: {str(e)}"
            )
    
    async def _get_topology(self) -> CommandResult:
        """Get service topology and relationships"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/topology"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Service topology retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get topology: {str(e)}"
            )
    
    async def _health_check_services(self) -> CommandResult:
        """Perform health checks on all registered services"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/health-check"
            response = await self.clients.post_json(url, {})
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Health check completed on all services",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to perform health checks: {str(e)}"
            )
    
    async def _get_stats(self) -> CommandResult:
        """Get Discovery Agent statistics"""
        try:
            start_time = time.time()
            
            # Get basic status
            status_response = await self.clients.get_json(f"{self.base_url}/status")
            
            # Try to get service count
            services_response = await self.clients.get_json(f"{self.base_url}/services")
            service_count = len(services_response.get("services", [])) if services_response else 0
            
            # Try to get topology information
            topology_response = await self.clients.get_json(f"{self.base_url}/topology")
            
            execution_time = time.time() - start_time
            
            stats = {
                "status": status_response,
                "registered_services": service_count,
                "topology": topology_response,
                "service_uptime": status_response.get("uptime", "unknown") if status_response else "unknown"
            }
            
            return CommandResult(
                success=True,
                data=stats,
                message="Discovery Agent statistics retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get Discovery Agent stats: {str(e)}"
            )
    
    def format_response(self, result: CommandResult, command: str) -> None:
        """Format and display the command result"""
        if not result.success:
            self.console.print(f"[red]❌ Error: {result.error}[/red]")
            return
        
        # Command-specific formatting
        if command == "status":
            self._format_status_response(result.data)
        elif command == "services":
            self._format_services_response(result.data)
        elif command == "discover":
            self._format_discovery_response(result.data)
        elif command == "topology":
            self._format_topology_response(result.data)
        elif command == "health-check":
            self._format_health_check_response(result.data)
        elif command == "stats":
            self._format_stats_response(result.data)
        else:
            # Generic formatting
            self.console.print(f"[green]✅ {result.message}[/green]")
            if result.data:
                self.console.print(Panel(str(result.data), title="Response Data", border_style="blue"))
        
        if result.execution_time:
            self.console.print(f"[dim]⏱️  Execution time: {result.execution_time:.3f}s[/dim]")
    
    def _format_status_response(self, data: Dict[str, Any]) -> None:
        """Format status response"""
        if not data:
            self.console.print("[yellow]⚠️  No status data available[/yellow]")
            return
            
        table = Table(title="🔍 Discovery Agent Status", border_style="green")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            table.add_row(str(key), str(value))
        
        self.console.print(table)
    
    def _format_services_response(self, data: Dict[str, Any]) -> None:
        """Format services list response"""
        services = data.get("services", [])
        if not services:
            self.console.print("[yellow]🔍 No services found[/yellow]")
            return
        
        table = Table(title="🔍 Discovered Services", border_style="blue")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("URL", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Last Seen", style="dim")
        
        for service in services:
            status_color = "green" if service.get("status") == "healthy" else "red"
            table.add_row(
                service.get("name", "N/A"),
                service.get("type", "unknown"),
                service.get("url", "N/A"),
                f"[{status_color}]{service.get('status', 'unknown')}[/{status_color}]",
                service.get("last_seen", "N/A")
            )
        
        self.console.print(table)
        
        self.console.print(f"[dim]Total services: {len(services)}[/dim]")
    
    def _format_discovery_response(self, data: Dict[str, Any]) -> None:
        """Format discovery results"""
        discovered = data.get("discovered", [])
        if not discovered:
            self.console.print("[yellow]🔍 No new services discovered[/yellow]")
            return
        
        table = Table(title="🔍 New Services Discovered", border_style="cyan")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("URL", style="yellow")
        table.add_column("Confidence", style="magenta")
        
        for service in discovered:
            confidence = service.get("confidence", 0)
            confidence_color = "green" if confidence > 0.8 else "yellow" if confidence > 0.5 else "red"
            
            table.add_row(
                service.get("name", "N/A"),
                service.get("type", "unknown"),
                service.get("url", "N/A"),
                f"[{confidence_color}]{confidence:.2f}[/{confidence_color}]"
            )
        
        self.console.print(table)
        
        self.console.print(f"[dim]Discovered: {len(discovered)} new services[/dim]")
    
    def _format_topology_response(self, data: Dict[str, Any]) -> None:
        """Format topology response"""
        if not data:
            self.console.print("[yellow]🌐 No topology data available[/yellow]")
            return
        
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        
        # Display nodes
        if nodes:
            table = Table(title="🌐 Service Topology - Nodes", border_style="blue")
            table.add_column("Service", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Connections", style="yellow")
            table.add_column("Status", style="magenta")
            
            for node in nodes:
                connection_count = len([e for e in edges if e.get("source") == node.get("id") or e.get("target") == node.get("id")])
                status_color = "green" if node.get("status") == "healthy" else "red"
                
                table.add_row(
                    node.get("name", "N/A"),
                    node.get("type", "unknown"),
                    str(connection_count),
                    f"[{status_color}]{node.get('status', 'unknown')}[/{status_color}]"
                )
            
            self.console.print(table)
        
        # Display connections
        if edges:
            self.console.print(Panel.fit(
                f"🔗 Service Connections: {len(edges)} total\n" +
                "\n".join([f"  {edge.get('source', 'unknown')} → {edge.get('target', 'unknown')}" for edge in edges[:10]]) +
                (f"\n  ... and {len(edges) - 10} more" if len(edges) > 10 else ""),
                title="Service Connections",
                border_style="cyan"
            ))
    
    def _format_health_check_response(self, data: Dict[str, Any]) -> None:
        """Format health check results"""
        results = data.get("results", [])
        if not results:
            self.console.print("[yellow]❤️  No health check results[/yellow]")
            return
        
        table = Table(title="❤️  Service Health Check Results", border_style="green")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Response Time", style="yellow")
        table.add_column("Details", style="dim")
        
        healthy_count = 0
        for result in results:
            status = result.get("status", "unknown")
            if status == "healthy":
                healthy_count += 1
                status_display = "[green]✅ Healthy[/green]"
            else:
                status_display = "[red]❌ Unhealthy[/red]"
            
            table.add_row(
                result.get("service", "N/A"),
                status_display,
                f"{result.get('response_time', 0):.3f}s",
                result.get("details", "")[:30] + "..." if len(result.get("details", "")) > 30 else result.get("details", "")
            )
        
        self.console.print(table)
        
        self.console.print(f"[dim]Health Summary: {healthy_count}/{len(results)} services healthy ({healthy_count/len(results)*100:.1f}%)[/dim]")
    
    def _format_stats_response(self, data: Dict[str, Any]) -> None:
        """Format statistics response"""
        topology = data.get("topology", {})
        node_count = len(topology.get("nodes", [])) if topology else 0
        edge_count = len(topology.get("edges", [])) if topology else 0
        
        self.console.print(Panel.fit(
            f"📊 Discovery Agent Statistics\n\n"
            f"🔍 Registered Services: {data.get('registered_services', 'N/A')}\n"
            f"🌐 Topology Nodes: {node_count}\n"
            f"🔗 Service Connections: {edge_count}\n"
            f"⏰ Uptime: {data.get('service_uptime', 'N/A')}\n"
            f"🟢 Status: {data.get('status', {}).get('status', 'unknown') if data.get('status') else 'unknown'}",
            title="Discovery Agent Stats",
            border_style="green"
        ))
