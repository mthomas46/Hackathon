"""
Frontend Service Adapter for CLI interaction
Handles web interface and user interaction endpoints
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .base_service_adapter import BaseServiceAdapter, ServiceInfo, ServiceStatus, CommandResult


class FrontendAdapter(BaseServiceAdapter):
    """
    Adapter for Frontend service - handles web interface interactions
    """
    
    def __init__(self, console: Console, clients: Any, base_url: str):
        super().__init__(console, clients, base_url)
        self.service_info = ServiceInfo(
            name="frontend",
            version="1.0.0",
            description="Web interface and user interaction service",
            endpoints=[
                "/health",
                "/api/status",
                "/api/config",
                "/api/services",
                "/static",
                "/"
            ],
            dependencies=["fastapi", "static-files"]
        )
    
    def get_available_commands(self) -> List[str]:
        """Return list of available commands for this service"""
        return [
            "status",
            "config",
            "services",
            "pages",
            "assets",
            "test-ui",
            "stats"
        ]
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute a command against the Frontend service"""
        command_map = {
            "status": self._get_status,
            "config": self._get_config,
            "services": self._get_services,
            "pages": self._list_pages,
            "assets": self._check_assets,
            "test-ui": self._test_ui,
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
        """Get Frontend service status"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/api/status"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Frontend status retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get Frontend status: {str(e)}"
            )
    
    async def _get_config(self) -> CommandResult:
        """Get Frontend configuration"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/api/config"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Frontend configuration retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get Frontend config: {str(e)}"
            )
    
    async def _get_services(self) -> CommandResult:
        """Get services available through the frontend"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/api/services"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {len(response.get('services', []))} frontend services",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get frontend services: {str(e)}"
            )
    
    async def _list_pages(self) -> CommandResult:
        """List available frontend pages"""
        try:
            start_time = time.time()
            
            # Check main page
            main_response = await self.clients.get_text(f"{self.base_url}/")
            
            # Common pages to check
            pages = ["/", "/health", "/api/status"]
            available_pages = []
            
            for page in pages:
                try:
                    page_response = await self.clients.get_text(f"{self.base_url}{page}")
                    if page_response:
                        available_pages.append({"path": page, "status": "available"})
                except:
                    available_pages.append({"path": page, "status": "unavailable"})
            
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data={"pages": available_pages},
                message=f"Checked {len(pages)} frontend pages",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list frontend pages: {str(e)}"
            )
    
    async def _check_assets(self) -> CommandResult:
        """Check static assets availability"""
        try:
            start_time = time.time()
            
            # Try to check static assets
            assets_to_check = ["/static/css", "/static/js", "/favicon.ico"]
            asset_status = []
            
            for asset in assets_to_check:
                try:
                    asset_response = await self.clients.get_text(f"{self.base_url}{asset}")
                    status = "available" if asset_response else "not found"
                except:
                    status = "error"
                
                asset_status.append({"path": asset, "status": status})
            
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data={"assets": asset_status},
                message=f"Checked {len(assets_to_check)} static assets",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to check frontend assets: {str(e)}"
            )
    
    async def _test_ui(self) -> CommandResult:
        """Test UI responsiveness"""
        try:
            start_time = time.time()
            
            # Test main page load
            main_page = await self.clients.get_text(f"{self.base_url}/")
            main_load_time = time.time() - start_time
            
            # Test API endpoint
            api_start = time.time()
            api_response = await self.clients.get_json(f"{self.base_url}/health")
            api_load_time = time.time() - api_start
            
            execution_time = time.time() - start_time
            
            test_results = {
                "main_page": {
                    "loaded": bool(main_page),
                    "load_time": main_load_time,
                    "size": len(main_page) if main_page else 0
                },
                "api_health": {
                    "responded": bool(api_response),
                    "load_time": api_load_time
                },
                "overall_status": "pass" if main_page and api_response else "fail"
            }
            
            return CommandResult(
                success=True,
                data=test_results,
                message="UI responsiveness test completed",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to test UI: {str(e)}"
            )
    
    async def _get_stats(self) -> CommandResult:
        """Get Frontend service statistics"""
        try:
            start_time = time.time()
            
            # Get basic health
            health_response = await self.clients.get_json(f"{self.base_url}/health")
            
            # Try to get status
            status_response = await self.clients.get_json(f"{self.base_url}/api/status")
            
            execution_time = time.time() - start_time
            
            stats = {
                "health": health_response,
                "status": status_response,
                "service_uptime": status_response.get("uptime", "unknown") if status_response else "unknown"
            }
            
            return CommandResult(
                success=True,
                data=stats,
                message="Frontend statistics retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get Frontend stats: {str(e)}"
            )
    
    def format_response(self, result: CommandResult, command: str) -> None:
        """Format and display the command result"""
        if not result.success:
            self.console.print(f"[red]❌ Error: {result.error}[/red]")
            return
        
        # Command-specific formatting
        if command == "status":
            self._format_status_response(result.data)
        elif command == "config":
            self._format_config_response(result.data)
        elif command == "services":
            self._format_services_response(result.data)
        elif command == "pages":
            self._format_pages_response(result.data)
        elif command == "assets":
            self._format_assets_response(result.data)
        elif command == "test-ui":
            self._format_ui_test_response(result.data)
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
            
        table = Table(title="🌐 Frontend Status", border_style="green")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            table.add_row(str(key), str(value))
        
        self.console.print(table)
    
    def _format_config_response(self, data: Dict[str, Any]) -> None:
        """Format configuration response"""
        if not data:
            self.console.print("[yellow]⚙️  No configuration data available[/yellow]")
            return
        
        table = Table(title="⚙️  Frontend Configuration", border_style="blue")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
                
            table.add_row(str(key), value_str)
        
        self.console.print(table)
    
    def _format_services_response(self, data: Dict[str, Any]) -> None:
        """Format services response"""
        services = data.get("services", [])
        if not services:
            self.console.print("[yellow]🌐 No frontend services found[/yellow]")
            return
        
        table = Table(title="🌐 Frontend Services", border_style="magenta")
        table.add_column("Name", style="cyan")
        table.add_column("URL", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Type", style="dim")
        
        for service in services:
            if isinstance(service, str):
                table.add_row(service, "N/A", "N/A", "N/A")
            else:
                status_color = "green" if service.get("status") == "active" else "red"
                table.add_row(
                    service.get("name", "N/A"),
                    service.get("url", "N/A"),
                    f"[{status_color}]{service.get('status', 'unknown')}[/{status_color}]",
                    service.get("type", "unknown")
                )
        
        self.console.print(table)
    
    def _format_pages_response(self, data: Dict[str, Any]) -> None:
        """Format pages response"""
        pages = data.get("pages", [])
        if not pages:
            self.console.print("[yellow]📄 No pages checked[/yellow]")
            return
        
        table = Table(title="📄 Frontend Pages", border_style="cyan")
        table.add_column("Path", style="cyan")
        table.add_column("Status", style="green")
        
        for page in pages:
            status = page.get("status", "unknown")
            status_color = "green" if status == "available" else "red"
            status_icon = "✅" if status == "available" else "❌"
            
            table.add_row(
                page.get("path", "N/A"),
                f"{status_icon} [{status_color}]{status}[/{status_color}]"
            )
        
        self.console.print(table)
    
    def _format_assets_response(self, data: Dict[str, Any]) -> None:
        """Format assets response"""
        assets = data.get("assets", [])
        if not assets:
            self.console.print("[yellow]📦 No assets checked[/yellow]")
            return
        
        table = Table(title="📦 Static Assets", border_style="yellow")
        table.add_column("Asset Path", style="cyan")
        table.add_column("Status", style="green")
        
        for asset in assets:
            status = asset.get("status", "unknown")
            status_color = "green" if status == "available" else "red" if status == "error" else "yellow"
            status_icon = "✅" if status == "available" else "❌" if status == "error" else "⚠️"
            
            table.add_row(
                asset.get("path", "N/A"),
                f"{status_icon} [{status_color}]{status}[/{status_color}]"
            )
        
        self.console.print(table)
    
    def _format_ui_test_response(self, data: Dict[str, Any]) -> None:
        """Format UI test response"""
        main_page = data.get("main_page", {})
        api_health = data.get("api_health", {})
        overall = data.get("overall_status", "unknown")
        
        overall_color = "green" if overall == "pass" else "red"
        overall_icon = "✅" if overall == "pass" else "❌"
        
        self.console.print(Panel.fit(
            f"🧪 UI Responsiveness Test\n\n"
            f"📄 Main Page: {'✅' if main_page.get('loaded') else '❌'} "
            f"({main_page.get('load_time', 0):.3f}s, {main_page.get('size', 0)} bytes)\n"
            f"🔗 API Health: {'✅' if api_health.get('responded') else '❌'} "
            f"({api_health.get('load_time', 0):.3f}s)\n"
            f"{overall_icon} Overall: [{overall_color}]{overall.upper()}[/{overall_color}]",
            title="UI Test Results",
            border_style=overall_color
        ))
    
    def _format_stats_response(self, data: Dict[str, Any]) -> None:
        """Format statistics response"""
        health = data.get("health", {})
        status = data.get("status", {})
        
        self.console.print(Panel.fit(
            f"📊 Frontend Statistics\n\n"
            f"🌐 Health: {health.get('status', 'unknown') if health else 'unknown'}\n"
            f"⚙️  Status: {status.get('status', 'unknown') if status else 'unknown'}\n"
            f"⏰ Uptime: {data.get('service_uptime', 'N/A')}\n"
            f"🔗 Base URL: {self.base_url}",
            title="Frontend Stats",
            border_style="green"
        ))
