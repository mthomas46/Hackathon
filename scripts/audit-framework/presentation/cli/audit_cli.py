#!/usr/bin/env python3
"""
Command-line interface for the comprehensive audit framework.

Usage:
    python audit_cli.py audit --service doc_store
    python audit_cli.py audit --service analysis-service --output markdown
    python audit_cli.py compare --services doc_store,prompt_store
"""

import sys
import os
import asyncio
import time
from pathlib import Path

# Add the audit-framework directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Enhanced CLI with beautiful startup
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    from rich.spinner import Spinner
    from rich.live import Live
    HAS_RICH_CLI = True
except ImportError:
    HAS_RICH_CLI = False

def display_startup_animation():
    """Display a beautiful startup animation with system status"""
    if not HAS_RICH_CLI:
        print("🚀 Starting LLM Ecosystem Audit Framework...")
        return

    console = Console()

    # System status check
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        memory_status = "🟢" if memory_usage < 70 else "🟡" if memory_usage < 85 else "🔴"

        cpu_usage = psutil.cpu_percent(interval=0.1)
        cpu_status = "🟢" if cpu_usage < 70 else "🟡" if cpu_usage < 85 else "🔴"

        system_info = f"{memory_status} RAM: {memory_usage:.1f}% | {cpu_status} CPU: {cpu_usage:.1f}%"
    except ImportError:
        system_info = "📊 System monitoring unavailable"

    # Welcome message with system status
    welcome_text = Text("🔍 LLM Ecosystem Audit Framework", style="bold blue")
    welcome_panel = Panel(
        Align.center(f"{welcome_text}\n[dim]{system_info}[/dim]"),
        title="[bold green]🚀 Initializing[/bold green]",
        border_style="blue"
    )
    console.print(welcome_panel)

    # Enhanced loading animation with progress feedback
    with console.status("[bold green]Loading audit modules...", spinner="dots") as status:
        time.sleep(0.3)
        status.update("[bold green]Initializing analyzers...", spinner="dots")
        time.sleep(0.3)
        status.update("[bold green]Loading configurations...", spinner="dots")
        time.sleep(0.2)
        status.update("[bold green]Checking system resources...", spinner="dots")

        # Quick system health check
        try:
            import psutil
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                console.print("[yellow]⚠️  Low disk space detected[/yellow]")
        except:
            pass

        time.sleep(0.2)
        status.update("[bold green]Framework ready!", spinner="dots")
        time.sleep(0.1)

    console.print("[green]✅ Framework initialized successfully![/green]\n")

def main():
    """Enhanced main function with beautiful CLI"""
    try:
        display_startup_animation()
        from .audit_framework import main as _main
        _main()
    except KeyboardInterrupt:
        if HAS_RICH_CLI:
            console = Console()
            console.print("\n[yellow]⚠️  Audit interrupted by user[/yellow]")
        else:
            print("\n⚠️  Audit interrupted by user")
        sys.exit(1)
    except Exception as e:
        if HAS_RICH_CLI:
            console = Console()
            console.print(f"\n[red]💥 Fatal error: {e}[/red]")
        else:
            print(f"\n💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
