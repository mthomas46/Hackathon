"""
Main MCP server entry point.

Provides both MCP protocol (stdio) and REST API (HTTP) interfaces.
"""

import asyncio
import sys

import uvicorn

from .utils.logging_config import setup_logging, console
from .utils.terminal_feedback import print_banner
from .utils.preflight import run_preflight_checks


async def main():
    """Main server entry point."""
    # Setup comprehensive logging
    setup_logging(enable_rich=True)
    
    # Print startup banner
    print_banner(
        "ECOSYSTEM MCP SERVER",
        "Intelligent Refactoring Knowledge Base with MCP Integration"
    )
    
    console.print("\n[bold cyan]🔍 Running Preflight Checks[/bold cyan]")
    console.print("=" * 80)
    
    # Run preflight checks
    await run_preflight_checks(fail_fast=True)
    
    console.print("\n[bold green]✅ All Preflight Checks Passed[/bold green]")
    console.print("=" * 80)
    
    # Start REST API server
    console.print("\n[bold cyan]🚀 Starting REST API Server[/bold cyan]")
    console.print(f"[dim]Host:[/dim] 0.0.0.0")
    console.print(f"[dim]Port:[/dim] 8000")
    console.print(f"[dim]Docs:[/dim] http://localhost:8000/docs")
    console.print("=" * 80 + "\n")
    
    config = uvicorn.Config(
        "src.api.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]🛑 Shutting down...[/bold yellow]")


if __name__ == "__main__":
    # Run server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold green]✅ Shutdown complete[/bold green]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]❌ Server failed to start: {e}[/bold red]")
        sys.exit(1)

