"""
Interactive CLI Overlay - Enhanced user experience for CLI operations

This module provides an overlay on the existing CLI system using questionary
for more interactive menu experiences while preserving all existing functionality.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .base.base_manager import BaseManager


class InteractiveOverlay:
    """Overlay class providing enhanced interactive CLI experiences."""

    def __init__(self, console: Console):
        self.console = console
        self.use_interactive = True  # Toggle for fallback to original system

    async def enhanced_menu_loop(
        self,
        manager: BaseManager,
        title: str,
        menu_items: Optional[List[Tuple[str, str]]] = None,
        back_option: str = "b"
    ) -> None:
        """Enhanced menu loop with questionary for better UX."""

        # Get menu items from manager if not provided
        items = menu_items if menu_items is not None else await manager.get_main_menu()

        # Add back option
        display_items = [f"{key}: {desc}" for key, desc in items]
        display_items.append(f"{back_option}: Back")

        while True:
            try:
                # Create enhanced menu display
                self._show_enhanced_menu_header(title, items)

                # Use questionary for interactive selection
                if self.use_interactive:
                    choice_display = await self._questionary_select(
                        f"Select option for {title}:",
                        display_items
                    )

                    # Extract choice key from display string
                    choice = choice_display.split(':')[0].strip()
                else:
                    # Fallback to original method
                    choice = await self._fallback_selection(display_items, back_option)

                # Handle choice
                if choice.lower() in [back_option.lower(), "back"]:
                    break

                # Validate service dependencies before proceeding
                if not await manager.validate_service_dependencies():
                    continue

                # Handle the choice
                if await manager.handle_submenu_choice(choice):
                    # Show success feedback
                    if choice not in ["h", "help"]:
                        await self._show_success_feedback()

            except KeyboardInterrupt:
                self.console.print("\n[yellow]⚠️  Operation interrupted by user[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]❌ Error: {e}[/red]")
                if not self.use_interactive:
                    break

    async def _questionary_select(self, message: str, choices: List[str]) -> str:
        """Use questionary for interactive selection."""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.select(message, choices=choices).ask()
            )
            return result
        except Exception:
            # Fallback if questionary fails
            self.use_interactive = False
            return choices[0].split(':')[0].strip()

    async def _fallback_selection(self, display_items: List[str], back_option: str) -> str:
        """Fallback to original selection method."""
        from rich.prompt import Prompt

        # Show numbered list
        for i, item in enumerate(display_items, 1):
            self.console.print(f"{i}. {item}")

        while True:
            choice = Prompt.ask("[bold green]Select option number[/bold green]").strip()

            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(display_items):
                    return display_items[index].split(':')[0].strip()

            self.console.print("[red]Invalid selection. Please try again.[/red]")

    def _show_enhanced_menu_header(self, title: str, items: List[Tuple[str, str]]) -> None:
        """Show enhanced menu header with service status."""
        # Create a rich panel with menu information
        menu_info = Text()
        menu_info.append(f"\n{title}\n", style="bold cyan")
        menu_info.append("=" * len(title) + "\n\n", style="cyan")

        for key, desc in items:
            menu_info.append(f"  {key}", style="bold green")
            menu_info.append(f" → {desc}\n", style="white")

        panel = Panel(
            menu_info,
            title="[bold blue]Interactive Menu[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(panel)

    async def _show_success_feedback(self) -> None:
        """Show success feedback after operation."""
        try:
            # Quick success indicator
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.print("✅ Operation completed successfully!", style="bold green")
            )
            await asyncio.sleep(0.5)  # Brief pause
        except Exception:
            # Fallback
            self.console.print("[green]✅ Operation completed successfully![/green]")
            from rich.prompt import Prompt
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    async def service_health_check_prompt(self, manager: BaseManager) -> bool:
        """Interactive service health check with user guidance."""

        health_results = await manager.check_required_services()

        if not health_results:
            return True  # No required services

        # Check if all services are healthy
        unhealthy_services = []
        for service_name, health_data in health_results.items():
            if not manager.is_service_healthy(health_data):
                unhealthy_services.append(service_name)

        if not unhealthy_services:
            return True  # All services healthy

        # Show interactive health status
        self._show_service_health_warning(unhealthy_services, health_results, manager)

        # Interactive options
        options = [
            "Check service status in Settings menu",
            "Continue anyway (may cause errors)",
            "Go back to main menu"
        ]

        try:
            choice = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.select(
                    "What would you like to do?",
                    choices=options,
                    default=options[0]
                ).ask()
            )

            if "Settings" in choice:
                return False  # Will redirect to settings
            elif "Continue" in choice:
                return True   # Proceed despite warnings
            else:
                return False  # Go back

        except Exception:
            # Fallback
            self.console.print("[yellow]⚠️  Some required services are unavailable.[/yellow]")
            self.console.print("[cyan]💡 Check service status in Settings menu (press 's')[/cyan]")
            return False

    def _show_service_health_warning(
        self,
        unhealthy_services: List[str],
        health_results: Dict[str, Dict[str, Any]],
        manager: BaseManager
    ) -> None:
        """Show detailed service health warning."""

        warning_text = Text()
        warning_text.append("⚠️  Service Dependency Warning\n", style="bold yellow")
        warning_text.append("=" * 30 + "\n\n", style="yellow")

        warning_text.append("The following required services are not available:\n", style="red")

        for service in unhealthy_services:
            health_data = health_results[service]
            error = health_data.get("error", "Unknown error")
            warning_text.append(f"  • {service}: {error}\n", style="red")

        warning_text.append("\nThis may cause operations to fail.\n", style="yellow")

        panel = Panel(
            warning_text,
            title="[bold red]Service Health Check[/bold red]",
            border_style="red",
            padding=(1, 2)
        )

        self.console.print(panel)


# Global overlay instance
interactive_overlay = None

def get_interactive_overlay(console: Console) -> InteractiveOverlay:
    """Get or create the global interactive overlay instance."""
    global interactive_overlay
    if interactive_overlay is None:
        interactive_overlay = InteractiveOverlay(console)
    return interactive_overlay
