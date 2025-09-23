#!/usr/bin/env python3
"""
Phase 3 Interactive CLI Enhancements Demo

Showcases the advanced features added in Phase 3:
- Custom questionary styling
- Enhanced user guidance and tips
- Configurable interactive preferences
- Improved service health check integration
"""

import asyncio
import os
import sys

# Add the project directory to the path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

try:
    import questionary

    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False
    print("❌ Questionary not available - Phase 3 features require questionary")

from rich.console import Console


async def demo_phase3_enhancements():
    """Demonstrate Phase 3 interactive CLI enhancements."""
    console = Console()

    console.print("\n[bold blue]🚀 Phase 3: Interactive CLI Enhancements Demo[/bold blue]")
    console.print("=" * 60)

    if not QUESTIONARY_AVAILABLE:
        console.print("\n[red]❌ Phase 3 features require questionary to be installed[/red]")
        console.print("[cyan]Install: pip install questionary==2.0.1[/cyan]")
        return

    console.print("\n[green]✅ Questionary available - Demonstrating Phase 3 features![/green]")

    # Demo 1: Custom Styling
    console.print("\n[bold cyan]🎨 Demo 1: Custom Questionary Styling[/bold cyan]")
    console.print("Phase 3 introduces beautiful custom styling with:")
    console.print("• Purple question marks and pointers")
    console.print("• Orange highlights for selections")
    console.print("• Bold text for important elements")

    try:
        choice = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: questionary.select(
                "Choose your preferred CLI style:",
                choices=["🎨 Full styling (recommended)", "🎯 Minimal styling", "📝 Plain text"],
                style=questionary.Style(
                    [
                        ("qmark", "fg:#673ab7 bold"),  # Purple question mark
                        ("question", "bold"),  # Bold question text
                        ("answer", "fg:#ff5722 bold"),  # Orange answer highlight
                        ("pointer", "fg:#673ab7 bold"),  # Purple pointer
                        ("selected", "fg:#ff5722 bold"),  # Orange selected item
                        ("separator", "fg:#cc5454"),  # Red separator
                    ]
                ),
                use_indicator=True,
                use_shortcuts=True,
            ).ask(),
        )
        console.print(f"[green]Selected: {choice}[/green]")
    except Exception as e:
        console.print(f"[red]Styling demo error: {e}[/red]")

    # Demo 2: Enhanced Service Health Checks
    console.print("\n[bold cyan]🛡️ Demo 2: Enhanced Service Health Integration[/bold cyan]")
    console.print("Phase 3 improves service health warnings with:")
    console.print("• Orange warning styling")
    console.print("• Clear action choices")
    console.print("• Better user guidance")

    # Simulate service health warning
    console.print("\n[yellow]⚠️  Service Dependency Warning[/yellow]")
    console.print("[red]❌ Orchestrator service unavailable[/red]")

    try:
        action = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: questionary.select(
                "⚠️  Service Health Warning - Choose your action:",
                choices=[
                    "Check service status in Settings menu",
                    "Continue anyway (may cause errors)",
                    "Go back to main menu",
                ],
                default="Check service status in Settings menu",
                style=questionary.Style(
                    [
                        ("qmark", "fg:#ff9800 bold"),  # Orange warning question mark
                        ("question", "bold fg:#ff9800"),  # Bold orange question
                        ("answer", "fg:#4caf50 bold"),  # Green answer
                        ("pointer", "fg:#ff9800 bold"),  # Orange pointer
                        ("selected", "fg:#4caf50 bold"),  # Green selected
                        ("separator", "fg:#ff9800"),  # Orange separator
                    ]
                ),
                use_indicator=True,
            ).ask(),
        )

        if "Settings" in action:
            console.print("[green]✅ Redirecting to Settings for service diagnostics...[/green]")
        elif "Continue" in action:
            console.print("[yellow]⚠️  Proceeding despite service warnings...[/yellow]")
        else:
            console.print("[blue]ℹ️  Returning to main menu...[/blue]")

    except Exception as e:
        console.print(f"[red]Health check demo error: {e}[/red]")

    # Demo 3: Success Feedback with Tips
    console.print("\n[bold cyan]💡 Demo 3: Success Feedback & Helpful Tips[/bold cyan]")
    console.print("Phase 3 adds intelligent tips and enhanced feedback:")

    try:
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: questionary.print("✅ Operation completed successfully!", style="bold green")
        )

        # Show a helpful tip (30% chance in real usage)
        import random

        if random.random() < 0.5:  # 50% for demo
            tip = random.choice(
                [
                    "💡 Tip: Press 's' anytime for service health status",
                    "💡 Tip: Use arrow keys for quick navigation",
                    "💡 Tip: Press 'b' to go back to previous menu",
                    "💡 Tip: All interactive menus support keyboard shortcuts",
                ]
            )
            await asyncio.get_event_loop().run_in_executor(None, lambda: questionary.print(tip, style="dim cyan"))

    except Exception as e:
        console.print(f"[green]✅ Operation completed successfully![/green]")
        console.print(f"[red]Enhanced feedback demo error: {e}[/red]")

    # Demo 4: Configuration Options
    console.print("\n[bold cyan]⚙️ Demo 4: Configurable Interactive Preferences[/bold cyan]")
    console.print("Phase 3 allows users to customize their experience:")

    console.print("• show_tips: Enable/disable helpful tips")
    console.print("• use_custom_styling: Enable/disable custom questionary styling")
    console.print("• enable_interactive: Toggle interactive overlay on/off")

    # Show configuration example
    console.print("\n[dim]# Example configuration:[/dim]")
    console.print("[dim]from services.cli.modules.interactive_overlay import configure_interactive_overlay[/dim]")
    console.print("[dim]configure_interactive_overlay(show_tips=True, use_custom_styling=True)[/dim]")

    console.print("\n[bold green]🎉 Phase 3 Interactive CLI Enhancements Complete![/bold green]")

    console.print("\n[bold blue]🚀 What Phase 3 Adds:[/bold blue]")
    console.print("✅ Custom questionary styling with color themes")
    console.print("✅ Enhanced service health check interactions")
    console.print("✅ Intelligent tips and user guidance")
    console.print("✅ Configurable interactive preferences")
    console.print("✅ Improved error handling and feedback")
    console.print("✅ Keyboard shortcuts and navigation hints")

    console.print("\n[bold blue]📊 Complete Interactive CLI Status:[/bold blue]")
    console.print("• Phase 1: ✅ Foundation (Questionary + Overlay)")
    console.print("• Phase 2: ✅ Gradual Rollout (9 managers enabled)")
    console.print("• Phase 3: ✅ Enhancement (Advanced features)")
    console.print("• Total: 🎯 Production-ready interactive CLI experience!")


async def main():
    await demo_phase3_enhancements()


if __name__ == "__main__":
    asyncio.run(main())
