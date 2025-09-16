#!/usr/bin/env python3
"""
Interactive CLI Overlay Demo

Demonstrates the enhanced interactive CLI experience using questionary
as an overlay on the existing menu system.
"""

import asyncio
import sys
import os
from rich.console import Console

# Add the project directory to the path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

try:
    import questionary
    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False
    print("⚠️  questionary not available - showing fallback experience")

try:
    from services.cli.modules.interactive_overlay import InteractiveOverlay, get_interactive_overlay
except ImportError:
    print("❌ Interactive overlay not available - showing conceptual demo")
    InteractiveOverlay = None
    get_interactive_overlay = None


class MockManager:
    """Mock manager for demonstration."""

    def __init__(self, console):
        self.console = console
        self.operation_count = 0

    async def get_main_menu(self):
        return [
            ("1", "Document Analysis - Analyze documents for quality and consistency"),
            ("2", "Bulk Operations - Mass operations across document collections"),
            ("3", "Quality Reports - Generate comprehensive quality reports"),
            ("4", "Integration Testing - Test service integrations"),
        ]

    async def validate_service_dependencies(self):
        """Mock service dependency validation."""
        return True

    async def handle_submenu_choice(self, choice: str) -> bool:
        """Mock choice handling."""
        operations = {
            "1": "Running document analysis...",
            "2": "Executing bulk operations...",
            "3": "Generating quality reports...",
            "4": "Running integration tests...",
        }

        if choice in operations:
            self.console.print(f"[green]✅ {operations[choice]}[/green]")
            self.operation_count += 1
            return True

        return False


async def demo_interactive_overlay():
    """Demonstrate the interactive CLI overlay."""
    console = Console()

    console.print("\n[bold blue]🎮 Interactive CLI Overlay Demo[/bold blue]")
    console.print("=" * 50)

    if not QUESTIONARY_AVAILABLE:
        console.print("\n[yellow]⚠️  Questionary not installed - Install for full interactive experience:[/yellow]")
        console.print("   pip install questionary")
        console.print("\n[cyan]📋 Demonstrating fallback experience...[/cyan]")
    else:
        console.print("\n[green]✅ Questionary available - Full interactive experience enabled![/green]")

    # Create overlay and mock manager
    overlay = get_interactive_overlay(console)
    manager = MockManager(console)

    console.print("\n[bold cyan]📋 Demo Scenarios:[/bold cyan]")
    console.print("1. Enhanced interactive menu selection")
    console.print("2. Service health check with user guidance")
    console.print("3. Success feedback and operation flow")

    # Demo 1: Enhanced Menu
    console.print("\n[bold cyan]🎯 Demo 1: Enhanced Interactive Menu[/bold cyan]")
    console.print("The new overlay provides arrow-key navigation and better UX...")

    try:
        # Simulate a quick menu interaction (will timeout for demo)
        await asyncio.wait_for(
            overlay.enhanced_menu_loop(manager, "Document Analysis Manager"),
            timeout=3.0
        )
    except asyncio.TimeoutError:
        console.print("[yellow]⏰ Demo timeout - menu would continue in real usage[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Demo error: {e}[/red]")

    # Demo 2: Service Health Check
    console.print("\n[bold cyan]🛡️ Demo 2: Service Health Check with Guidance[/bold cyan]")

    # Demo 2: Conceptual Service Health Check
    console.print("\n[bold cyan]🛡️ Demo 2: Service Health Check (Conceptual)[/bold cyan]")
    console.print("In real usage, this would show interactive health warnings...")
    console.print("[yellow]⚠️  Service Dependency Warning[/yellow]")
    console.print("[red]❌ Orchestrator service unavailable[/red]")
    console.print("[cyan]💡 Options: Check Settings, Continue anyway, Go back[/cyan]")

    # Show results
    console.print("\n[bold cyan]📊 Demo Results:[/bold cyan]")
    console.print(f"• Operations completed: {manager.operation_count}")
    console.print(f"• Interactive mode: {'Enabled' if QUESTIONARY_AVAILABLE else 'Fallback'}")
    console.print("• Service health checking: Integrated")
    console.print("• Error handling: Graceful fallback")

    console.print("\n[bold green]🎉 Interactive Overlay Demo Complete![/bold green]")

    console.print("\n[bold blue]🔄 Migration Strategy Benefits:[/bold blue]")
    console.print("✅ Zero breaking changes to existing code")
    console.print("✅ Automatic fallback if questionary unavailable")
    console.print("✅ Gradual adoption - menu by menu")
    console.print("✅ All existing functionality preserved")
    console.print("✅ Enhanced UX with minimal effort")

    console.print("\n[bold blue]🚀 Next Steps:[/bold blue]")
    console.print("1. Install questionary: pip install questionary")
    console.print("2. Test overlay on one manager first")
    console.print("3. Gradually migrate other menus")
    console.print("4. Update tests for interactive behavior")
    console.print("5. Consider full TUI migration later with textual")


async def main():
    await demo_interactive_overlay()


if __name__ == "__main__":
    asyncio.run(main())
