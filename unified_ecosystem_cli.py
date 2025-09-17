#!/usr/bin/env python3
"""
Unified Ecosystem CLI

A comprehensive command-line interface for interacting with the entire
LLM Documentation Ecosystem through standardized service adapters.
"""

import asyncio
import sys
import argparse
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
import json

# Mock imports for standalone testing
class MockServiceClients:
    """Mock service client for testing outside container"""
    
    async def get_json(self, url: str):
        """Mock GET request"""
        if "/health" in url:
            return {"status": "healthy", "service": url.split('/')[2].split(':')[0], "version": "1.0.0"}
        elif "/api/analysis/status" in url:
            return {"data": {"service": "analysis-service", "status": "operational", "features": ["analysis"]}}
        return {"mock": "response", "url": url}
    
    async def post_json(self, url: str, data: dict):
        """Mock POST request"""
        return {"success": True, "data": data, "url": url}


class EcosystemCLI:
    """
    Unified CLI for the entire ecosystem
    
    Provides standardized access to all services through a single interface
    """
    
    def __init__(self):
        self.console = Console()
        self.clients = MockServiceClients()  # Use mock for standalone testing
        self.registry = None
    
    async def initialize(self):
        """Initialize the CLI and service registry"""
        self.console.print("[bold blue]🚀 Initializing Unified Ecosystem CLI...[/bold blue]")
        
        # Import and initialize registry
        try:
            sys.path.append('/Users/mykalthomas/Documents/work/Hackathon')
            from services.cli.modules.adapters.service_registry import ServiceRegistry
            self.registry = ServiceRegistry(self.console, self.clients)
            await self.registry.initialize()
        except ImportError as e:
            self.console.print(f"[red]❌ Failed to import service registry: {e}[/red]")
            self.console.print("[yellow]⚠️  Running in standalone mode with mock services[/yellow]")
            self.registry = MockServiceRegistry(self.console)
    
    async def run_interactive(self):
        """Run interactive CLI mode"""
        await self.initialize()
        
        self.console.print(Panel(
            "[bold green]Welcome to the Unified Ecosystem CLI![/bold green]\n\n"
            "This CLI provides standardized access to all services in the\n"
            "LLM Documentation Ecosystem through unified adapters.\n\n"
            "Available commands:\n"
            "• [cyan]health[/cyan] - Check ecosystem health\n"
            "• [cyan]services[/cyan] - List all services\n"
            "• [cyan]service <name> <command>[/cyan] - Execute service command\n"
            "• [cyan]test[/cyan] - Run comprehensive ecosystem test\n"
            "• [cyan]discover[/cyan] - Discover service capabilities\n"
            "• [cyan]exit[/cyan] - Exit CLI",
            title="🌐 Unified Ecosystem CLI"
        ))
        
        while True:
            try:
                command = Prompt.ask("\n[bold cyan]ecosystem>[/bold cyan]", default="help")
                
                if command.lower() in ['exit', 'quit', 'q']:
                    self.console.print("[green]👋 Goodbye![/green]")
                    break
                elif command.lower() in ['help', 'h']:
                    await self.show_help()
                elif command.lower() == 'health':
                    await self.check_ecosystem_health()
                elif command.lower() == 'services':
                    await self.list_services()
                elif command.lower() == 'test':
                    await self.run_comprehensive_test()
                elif command.lower() == 'discover':
                    await self.discover_capabilities()
                elif command.lower().startswith('service '):
                    await self.execute_service_command(command)
                else:
                    self.console.print(f"[red]❌ Unknown command: {command}[/red]")
                    self.console.print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]⚠️  Interrupted by user[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]❌ Error: {e}[/red]")
    
    async def show_help(self):
        """Show help information"""
        help_table = Table(title="📚 Available Commands")
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")
        help_table.add_column("Example", style="dim")
        
        commands = [
            ("health", "Check health of all services", "health"),
            ("services", "List all registered services", "services"),
            ("service <name> <cmd>", "Execute command on specific service", "service analysis-service status"),
            ("test", "Run comprehensive ecosystem test", "test"),
            ("discover", "Discover all service capabilities", "discover"),
            ("help", "Show this help message", "help"),
            ("exit", "Exit the CLI", "exit")
        ]
        
        for cmd, desc, example in commands:
            help_table.add_row(cmd, desc, example)
        
        self.console.print(help_table)
    
    async def check_ecosystem_health(self):
        """Check health of all services"""
        if not self.registry:
            self.console.print("[red]❌ Registry not initialized[/red]")
            return
        
        self.console.print("[bold blue]🔍 Checking ecosystem health...[/bold blue]")
        results = await self.registry.health_check_all()
        
        # Additional summary
        healthy_services = [name for name, result in results.items() if result.success]
        self.console.print(f"\n[green]✅ Healthy services: {len(healthy_services)}/{len(results)}[/green]")
    
    async def list_services(self):
        """List all services with basic info"""
        if not self.registry:
            self.console.print("[red]❌ Registry not initialized[/red]")
            return
        
        services = self.registry.list_services()
        
        table = Table(title="🗂️ Registered Services")
        table.add_column("Service Name", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Priority", justify="center")
        
        for service_name in sorted(services):
            adapter = self.registry.get_adapter(service_name)
            if adapter:
                info = adapter.get_service_info()
                # Get priority from config (simplified)
                priority = "⭐" if "analysis" in service_name or "orchestrator" in service_name else "🔹"
                status = "✅" if info.status.value == "healthy" else "❓"
                table.add_row(service_name, status, priority)
        
        self.console.print(table)
    
    async def execute_service_command(self, full_command: str):
        """Execute command on specific service"""
        parts = full_command.split()
        if len(parts) < 3:
            self.console.print("[red]❌ Usage: service <service_name> <command> [args][/red]")
            return
        
        service_name = parts[1]
        command = parts[2]
        
        if not self.registry:
            self.console.print("[red]❌ Registry not initialized[/red]")
            return
        
        adapter = self.registry.get_adapter(service_name)
        if not adapter:
            self.console.print(f"[red]❌ Service '{service_name}' not found[/red]")
            self.console.print("Use 'services' command to see available services")
            return
        
        self.console.print(f"[blue]🔧 Executing '{command}' on {service_name}...[/blue]")
        result = await adapter.execute_command(command)
        adapter.display_result(result)
    
    async def run_comprehensive_test(self):
        """Run comprehensive ecosystem test"""
        if not self.registry:
            self.console.print("[red]❌ Registry not initialized[/red]")
            return
        
        self.console.print("[bold blue]🧪 Running Comprehensive Ecosystem Test...[/bold blue]")
        
        # Health check all services
        self.console.print("\n1️⃣ Health Check Phase")
        health_results = await self.registry.health_check_all()
        
        # Test service capabilities
        self.console.print("\n2️⃣ Capability Discovery Phase")
        capabilities = await self.registry.discover_service_capabilities()
        
        # Test specific service functionality
        self.console.print("\n3️⃣ Functionality Test Phase")
        
        # Test Analysis Service specifically
        analysis_adapter = self.registry.get_adapter("analysis-service")
        if analysis_adapter:
            self.console.print("  Testing Analysis Service...")
            status_result = await analysis_adapter.execute_command("status")
            analysis_adapter.display_result(status_result)
        
        # Generate test report
        self.console.print("\n📊 Test Summary")
        total_services = len(health_results)
        healthy_services = sum(1 for result in health_results.values() if result.success)
        
        summary_panel = Panel(
            f"Services Tested: {total_services}\n"
            f"Healthy Services: {healthy_services}\n"
            f"Success Rate: {(healthy_services/total_services)*100:.1f}%\n"
            f"Capabilities Discovered: {sum(len(cmds) for cmds in capabilities.values())}",
            title="[bold green]🎯 Test Results[/bold green]"
        )
        self.console.print(summary_panel)
    
    async def discover_capabilities(self):
        """Discover capabilities of all services"""
        if not self.registry:
            self.console.print("[red]❌ Registry not initialized[/red]")
            return
        
        self.console.print("[bold blue]🔍 Discovering service capabilities...[/bold blue]")
        capabilities = await self.registry.discover_service_capabilities()
        
        for service_name, commands in capabilities.items():
            if commands:
                table = Table(title=f"🛠️ {service_name} Commands")
                table.add_column("Command", style="cyan")
                table.add_column("Description", style="white")
                table.add_column("Usage", style="dim")
                
                for cmd_name, description, usage in commands:
                    table.add_row(cmd_name, description, usage)
                
                self.console.print(table)
            else:
                self.console.print(f"[yellow]⚠️  No commands discovered for {service_name}[/yellow]")


class MockServiceRegistry:
    """Mock registry for standalone testing"""
    
    def __init__(self, console):
        self.console = console
        self.services = ["analysis-service", "orchestrator", "doc_store", "source-agent"]
    
    def list_services(self):
        return self.services
    
    def get_adapter(self, name):
        class MockAdapter:
            def get_service_info(self):
                class MockInfo:
                    status = type('Status', (), {'value': 'healthy'})()
                return MockInfo()
            
            async def execute_command(self, cmd):
                class MockResult:
                    success = True
                    message = f"Mock execution of {cmd}"
                    data = {"mock": True}
                    execution_time = 0.1
                return MockResult()
            
            def display_result(self, result):
                self.console.print(f"✅ {result.message}")
        
        return MockAdapter() if name in self.services else None
    
    async def health_check_all(self):
        results = {}
        for service in self.services:
            class MockResult:
                success = True
                message = f"{service} is healthy"
                execution_time = 0.1
            results[service] = MockResult()
        return results
    
    async def discover_service_capabilities(self):
        return {service: [("status", "Get status", "status")] for service in self.services}


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Unified Ecosystem CLI")
    parser.add_argument("--command", help="Command to execute directly")
    parser.add_argument("--service", help="Service to target")
    parser.add_argument("--test", action="store_true", help="Run comprehensive test")
    
    args = parser.parse_args()
    
    cli = EcosystemCLI()
    
    if args.test:
        await cli.initialize()
        await cli.run_comprehensive_test()
    elif args.command:
        await cli.initialize()
        if args.service:
            full_command = f"service {args.service} {args.command}"
            await cli.execute_service_command(full_command)
        else:
            # Execute general command
            if args.command == "health":
                await cli.check_ecosystem_health()
            else:
                print(f"Unknown command: {args.command}")
    else:
        await cli.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
