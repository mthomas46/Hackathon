#!/usr/bin/env python3
"""
Master Startup Script for LLM Documentation Ecosystem
Starts all services locally with CLI as the main interface
"""

import os
import sys
import asyncio
import signal
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import requests

console = Console()

class ServiceManager:
    """Manages all services in the ecosystem."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.services: Dict[str, Dict] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.service_order = [
            "redis",
            "doc_store",
            "analysis_service",
            "orchestrator",
            "prompt_store",
            "summarizer_hub",
            "architecture_digitizer",
            "bedrock_proxy",
            "github_mcp",
            "interpreter",
            "code_analyzer",
            "secure_analyzer",
            "log_collector",
            "cli"
        ]

    def define_services(self):
        """Define all services with their configurations."""
        base_env = os.environ.copy()
        base_env['PYTHONPATH'] = str(self.project_root)

        self.services = {
            "redis": {
                "name": "Redis",
                "description": "Caching and event infrastructure",
                "command": ["redis-server", "--daemonize", "yes", "--port", "6379"],
                "health_url": None,
                "port": 6379,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "doc_store": {
                "name": "Doc Store",
                "description": "Document storage and management",
                "command": [sys.executable, "-m", "services.doc_store.main"],
                "health_url": "http://localhost:5010/health",
                "port": 5010,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "analysis_service": {
                "name": "Analysis Service",
                "description": "Document analysis and consistency checking",
                "command": [sys.executable, "-m", "services.analysis_service.main_new"],
                "health_url": "http://localhost:5020/health",
                "port": 5020,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "orchestrator": {
                "name": "Orchestrator",
                "description": "Workflow orchestration and service coordination",
                "command": [sys.executable, "-m", "services.orchestrator.main"],
                "health_url": "http://localhost:5099/health/system",
                "port": 5099,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "prompt_store": {
                "name": "Prompt Store",
                "description": "AI prompt management and storage",
                "command": [sys.executable, "-m", "services.prompt_store.main"],
                "health_url": "http://localhost:5110/health",
                "port": 5110,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "summarizer_hub": {
                "name": "Summarizer Hub",
                "description": "Multi-provider AI summarization service",
                "command": [sys.executable, "-m", "services.summarizer_hub.main"],
                "health_url": "http://localhost:5060/health",
                "port": 5060,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "architecture_digitizer": {
                "name": "Architecture Digitizer",
                "description": "System architecture diagram processing",
                "command": [sys.executable, "-m", "services.architecture_digitizer.main"],
                "health_url": "http://localhost:5105/health",
                "port": 5105,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "bedrock_proxy": {
                "name": "Bedrock Proxy",
                "description": "AWS Bedrock AI service proxy",
                "command": [sys.executable, "-m", "services.bedrock_proxy.main"],
                "health_url": "http://localhost:7090/health",
                "port": 7090,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "github_mcp": {
                "name": "GitHub MCP",
                "description": "GitHub Model Context Protocol service",
                "command": [sys.executable, "-m", "services.github_mcp.main"],
                "health_url": "http://localhost:5072/health",
                "port": 5072,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "interpreter": {
                "name": "Interpreter",
                "description": "Natural language processing and query interpretation",
                "command": [sys.executable, "-m", "services.interpreter.main"],
                "health_url": "http://localhost:5120/health",
                "port": 5120,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "code_analyzer": {
                "name": "Code Analyzer",
                "description": "Code analysis and security scanning",
                "command": [sys.executable, "-m", "services.code_analyzer.main"],
                "health_url": "http://localhost:5085/health",
                "port": 5085,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "secure_analyzer": {
                "name": "Secure Analyzer",
                "description": "Content security and policy enforcement",
                "command": [sys.executable, "-m", "services.secure_analyzer.main"],
                "health_url": "http://localhost:5070/health",
                "port": 5070,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "log_collector": {
                "name": "Log Collector",
                "description": "Centralized logging and analytics",
                "command": [sys.executable, "-m", "services.log_collector.main"],
                "health_url": "http://localhost:5080/health",
                "port": 5080,
                "env": base_env.copy(),
                "working_dir": str(self.project_root)
            },
            "cli": {
                "name": "CLI",
                "description": "Command Line Interface for service management",
                "command": [sys.executable, "-m", "services.cli.main", "interactive"],
                "health_url": None,
                "port": None,
                "env": base_env.copy(),
                "working_dir": str(self.project_root),
                "interactive": True
            }
        }

    async def check_service_health(self, service_id: str, timeout: int = 30) -> bool:
        """Check if a service is healthy."""
        service = self.services.get(service_id)
        if not service or not service.get("health_url"):
            return True  # No health check defined, assume healthy

        health_url = service["health_url"]
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                pass
            await asyncio.sleep(2)

        return False

    async def start_service(self, service_id: str, progress_callback=None) -> bool:
        """Start a single service."""
        service = self.services.get(service_id)
        if not service:
            console.print(f"[red]❌ Unknown service: {service_id}[/red]")
            return False

        if progress_callback:
            progress_callback(f"Starting {service['name']}...")

        try:
            # Special handling for Redis
            if service_id == "redis":
                # Check if Redis is already running
                try:
                    response = requests.get("http://localhost:6379", timeout=2)
                    if response.status_code == 200:
                        console.print(f"[green]✅ {service['name']} already running[/green]")
                        return True
                except:
                    pass

            process = subprocess.Popen(
                service["command"],
                env=service["env"],
                cwd=service["working_dir"],
                stdout=subprocess.PIPE if not service.get("interactive") else None,
                stderr=subprocess.PIPE if not service.get("interactive") else None,
                universal_newlines=True
            )

            self.processes[service_id] = process

            # Wait for service to start
            await asyncio.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                # Check health if health URL is defined
                if service.get("health_url"):
                    if await self.check_service_health(service_id, timeout=15):
                        console.print(f"[green]✅ {service['name']} started successfully[/green]")
                        return True
                    else:
                        console.print(f"[yellow]⚠️  {service['name']} started but health check failed[/yellow]")
                        return False
                else:
                    console.print(f"[green]✅ {service['name']} started[/green]")
                    return True
            else:
                stdout, stderr = process.communicate()
                console.print(f"[red]❌ {service['name']} failed to start[/red]")
                if stderr:
                    console.print(f"[red]Error: {stderr}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]❌ Error starting {service['name']}: {e}[/red]")
            return False

    async def start_all_services(self, skip_cli: bool = False):
        """Start all services in dependency order."""
        console.print(Panel.fit(
            "[bold blue]🚀 Starting LLM Documentation Ecosystem[/bold blue]\n"
            "[dim]All services will be started in dependency order[/dim]"
        ))

        self.define_services()

        started_services = []
        failed_services = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Starting services...", total=len(self.service_order))

            for service_id in self.service_order:
                if skip_cli and service_id == "cli":
                    progress.update(task, advance=1, description=f"Skipping CLI...")
                    continue

                service = self.services[service_id]

                def update_progress(description):
                    progress.update(task, description=description)

                success = await self.start_service(service_id, update_progress)

                if success:
                    started_services.append(service_id)
                else:
                    failed_services.append(service_id)

                progress.update(task, advance=1)

        # Summary
        console.print("\n" + "="*60)
        console.print("📊 STARTUP SUMMARY")
        console.print("="*60)

        if started_services:
            console.print(f"[green]✅ Services Started ({len(started_services)}):[/green]")
            for service_id in started_services:
                service = self.services[service_id]
                port_info = f" (port {service['port']})" if service['port'] else ""
                console.print(f"   • {service['name']}{port_info}")

        if failed_services:
            console.print(f"[red]❌ Services Failed ({len(failed_services)}):[/red]")
            for service_id in failed_services:
                service = self.services[service_id]
                console.print(f"   • {service['name']}")

        if skip_cli and "cli" in self.services:
            console.print(f"\n[blue]💻 CLI ready to start manually:[/blue]")
            console.print(f"   cd {self.project_root} && python services/cli/main.py interactive")

        return len(failed_services) == 0

    async def stop_all_services(self):
        """Stop all running services."""
        console.print("\n[bold red]🛑 Stopping all services...[/bold red]")

        stopped_count = 0

        for service_id, process in self.processes.items():
            if process and process.poll() is None:
                service = self.services[service_id]
                console.print(f"🔄 Stopping {service['name']}...")

                try:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                        console.print(f"[green]✅ {service['name']} stopped[/green]")
                        stopped_count += 1
                    except subprocess.TimeoutExpired:
                        console.print(f"[yellow]⚠️  {service['name']} not responding, killing...[/yellow]")
                        process.kill()
                        stopped_count += 1
                except Exception as e:
                    console.print(f"[red]❌ Error stopping {service['name']}: {e}[/red]")

        console.print(f"\n[green]✅ Stopped {stopped_count} services[/green]")

    def display_service_status(self):
        """Display current service status."""
        table = Table(title="Service Status")
        table.add_column("Service", style="cyan")
        table.add_column("Port", style="white")
        table.add_column("Description", style="white")
        table.add_column("Status", style="green")

        for service_id in self.service_order:
            service = self.services[service_id]
            port = service.get("port", "N/A")
            status = "🟢 Running" if service_id in self.processes and self.processes[service_id].poll() is None else "🔴 Stopped"
            table.add_row(service["name"], str(port), service["description"], status)

        console.print(table)

async def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="LLM Documentation Ecosystem Service Manager")
    parser.add_argument("--start", action="store_true", help="Start all services")
    parser.add_argument("--stop", action="store_true", help="Stop all services")
    parser.add_argument("--status", action="store_true", help="Show service status")
    parser.add_argument("--skip-cli", action="store_true", help="Skip starting CLI (for background service mode)")
    parser.add_argument("--service", help="Start only specific service")

    args = parser.parse_args()

    manager = ServiceManager()

    if args.status:
        manager.define_services()
        manager.display_service_status()
        return

    if args.service:
        manager.define_services()
        success = await manager.start_service(args.service)
        if success:
            console.print(f"\n[green]🎉 {args.service} started successfully![/green]")
        else:
            console.print(f"\n[red]❌ Failed to start {args.service}[/red]")
        return

    if args.start:
        try:
            success = await manager.start_all_services(skip_cli=args.skip_cli)
            if success:
                console.print(f"\n[green]🎉 All services started successfully![/green]")
                if not args.skip_cli:
                    console.print(f"\n[blue]💻 CLI is now running. Press Ctrl+C to stop all services.[/blue]")
                    # Keep running to maintain services
                    def signal_handler(signum, frame):
                        console.print(f"\n[yellow]⚠️  Shutdown signal received...[/yellow]")
                        asyncio.create_task(manager.stop_all_services())
                        sys.exit(0)

                    signal.signal(signal.SIGINT, signal_handler)
                    signal.signal(signal.SIGTERM, signal_handler)

                    # Keep the script running
                    while True:
                        await asyncio.sleep(1)
            else:
                console.print(f"\n[red]❌ Some services failed to start[/red]")
                sys.exit(1)
        except KeyboardInterrupt:
            console.print(f"\n[yellow]⚠️  Interrupted by user[/yellow]")
            await manager.stop_all_services()
        except Exception as e:
            console.print(f"\n[red]💥 Unexpected error: {e}[/red]")
            await manager.stop_all_services()
            sys.exit(1)

    elif args.stop:
        await manager.stop_all_services()

    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
