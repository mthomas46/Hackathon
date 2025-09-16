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

    def __init__(self, console: Console, enable_interactive: bool = True):
        self.console = console
        self.use_interactive = enable_interactive  # Toggle for fallback to original system

        # Configuration for user preferences
        self.show_tips = True
        self.use_custom_styling = True
        self.auto_health_checks = True

        # Performance enhancements
        self.menu_cache = {}  # Cache rendered menus
        self.health_cache = {}  # Cache service health status
        self.cache_ttl = 300  # 5 minute cache TTL
        self.last_cache_update = 0

        # Advanced UX features
        self.command_history = []
        self.favorites = set()
        self.usage_stats = {}

    async def enhanced_menu_loop(
        self,
        manager: BaseManager,
        title: str,
        menu_items: Optional[List[Tuple[str, str]]] = None,
        back_option: str = "b",
        enable_shortcuts: bool = True,
        enable_search: bool = True,
        enable_cache: bool = True
    ) -> None:
        """Enhanced menu loop with questionary for better UX."""

        # Performance: Async menu loading with caching
        items = await self._load_menu_items_cached(manager, title, menu_items, enable_cache)

        # Add back option
        display_items = [f"{key}: {desc}" for key, desc in items]
        display_items.append(f"{back_option}: Back")

        # Create keyboard shortcuts mapping
        shortcuts = {}
        if enable_shortcuts:
            for key, desc in items:
                if len(key) == 1 and key.isalnum():
                    shortcuts[key.lower()] = key
                    shortcuts[key.upper()] = key

        while True:
            try:
                # Create enhanced menu display with shortcuts info
                self._show_enhanced_menu_header(title, items, enable_shortcuts, enable_search)

                # Use questionary for interactive selection (with built-in shortcuts)
                if self.use_interactive:
                    choice_display = await self._questionary_select(
                        f"Select option for {title}:",
                        display_items
                    )
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
                    # Show success feedback with operation name
                    if choice not in ["h", "help"]:
                        await self._show_success_feedback(f"Menu selection ({choice})")

            except KeyboardInterrupt:
                self.console.print("\n[yellow]⚠️  Operation interrupted by user[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]❌ Error: {e}[/red]")
                if not self.use_interactive:
                    break

    async def _questionary_select(self, message: str, choices: List[str]) -> str:
        """Use questionary for interactive selection with enhanced styling."""
        try:
            # Create enhanced questionary selection with custom styling (if enabled)
            if self.use_custom_styling:
                style = questionary.Style([
                    ('qmark', 'fg:#673ab7 bold'),       # Purple question mark
                    ('question', 'bold'),               # Bold question text
                    ('answer', 'fg:#ff5722 bold'),      # Orange answer highlight
                    ('pointer', 'fg:#673ab7 bold'),     # Purple pointer
                    ('selected', 'fg:#ff5722 bold'),    # Orange selected item
                    ('separator', 'fg:#cc5454'),        # Red separator
                    ('instruction', ''),                # Default instruction text
                ])
            else:
                style = None

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.select(
                    message,
                    choices=choices,
                    style=style,
                    use_indicator=True,
                    use_shortcuts=True
                ).ask()
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

    def _show_enhanced_menu_header(self, title: str, items: List[Tuple[str, str]],
                                  enable_shortcuts: bool = True, enable_search: bool = True) -> None:
        """Show enhanced menu header with service status and keyboard shortcuts."""
        # Create a rich panel with menu information
        menu_info = Text()
        menu_info.append(f"\n{title}\n", style="bold cyan")
        menu_info.append("=" * len(title) + "\n\n", style="cyan")

        for key, desc in items:
            menu_info.append(f"  {key}", style="bold green")
            menu_info.append(f" → {desc}\n", style="white")

        # Add navigation guide with visual enhancements
        guide_parts = []
        guide_parts.append("💡 Navigation: ↑↓ arrows, Enter to select")

        if enable_shortcuts:
            guide_parts.append("Type option key directly")

        guide_parts.append("'b' for back")

        if enable_search:
            guide_parts.append("'/' to search")

        menu_info.append(f"\n[dim]{' | '.join(guide_parts)}[/dim]", style="dim cyan")

        # Add usage stats and favorites indicators
        if self.usage_stats:
            popular = self.get_popular_commands(1)
            if popular:
                menu_info.append(f"\n[dim]⭐ Popular: {popular[0]}[/dim]", style="dim yellow")

        # Add cache status indicator
        if enable_cache:
            # Check cache status synchronously
            current_time = asyncio.get_event_loop().time()
            cache_fresh = current_time - self.last_cache_update < self.cache_ttl
            cache_status = "🟢" if cache_fresh else "🟡"
            menu_info.append(f" [dim]{cache_status} Cached[/dim]", style="dim green")

        panel = Panel(
            menu_info,
            title="[bold blue]🎮 Interactive Menu[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        )

        self.console.print(panel)

    async def _load_menu_items_cached(self, manager: BaseManager, title: str,
                                    menu_items: Optional[List[Tuple[str, str]]], enable_cache: bool) -> List[Tuple[str, str]]:
        """Load menu items with caching for better performance."""
        cache_key = f"{title}_{manager.__class__.__name__}"

        # Check cache if enabled
        if enable_cache and cache_key in self.menu_cache:
            cached_time, cached_items = self.menu_cache[cache_key]
            if asyncio.get_event_loop().time() - cached_time < self.cache_ttl:
                return cached_items

        # Load fresh menu items
        items = menu_items if menu_items is not None else await manager.get_main_menu()

        # Cache the result if enabled
        if enable_cache:
            self.menu_cache[cache_key] = (asyncio.get_event_loop().time(), items)

        return items

    async def _check_cache_validity(self) -> bool:
        """Check if caches need to be invalidated."""
        current_time = asyncio.get_event_loop().time()
        if current_time - self.last_cache_update > self.cache_ttl:
            self.menu_cache.clear()
            self.health_cache.clear()
            self.last_cache_update = current_time
            return False
        return True

    def add_to_favorites(self, manager_name: str, menu_item: str):
        """Add a menu item to favorites for quick access."""
        self.favorites.add(f"{manager_name}:{menu_item}")

    def is_favorite(self, manager_name: str, menu_item: str) -> bool:
        """Check if a menu item is favorited."""
        return f"{manager_name}:{menu_item}" in self.favorites

    def record_command_usage(self, command: str):
        """Record command usage for analytics."""
        self.command_history.append({
            'command': command,
            'timestamp': asyncio.get_event_loop().time(),
            'count': self.usage_stats.get(command, 0) + 1
        })
        self.usage_stats[command] = self.usage_stats.get(command, 0) + 1

    def get_popular_commands(self, limit: int = 5) -> List[str]:
        """Get most popular commands based on usage."""
        return sorted(self.usage_stats.keys(),
                     key=lambda x: self.usage_stats[x],
                     reverse=True)[:limit]

    async def _show_success_feedback(self, operation: str = "Operation") -> None:
        """Show enhanced success feedback after operation with visual indicators."""
        try:
            # Show success indicator
            self.show_status_indicator("success", f"{operation} completed successfully!")

            # Record command usage for analytics
            self.record_command_usage(operation)

            # Show helpful tip (if enabled)
            if self.show_tips:
                tips = [
                    "💡 Tip: Press 's' anytime for service health status",
                    "💡 Tip: Use arrow keys for quick navigation",
                    "💡 Tip: Press 'b' to go back to previous menu",
                    "💡 Tip: All interactive menus support keyboard shortcuts"
                ]

                # Show a random tip occasionally
                import random
                if random.random() < 0.3:  # 30% chance
                    tip = random.choice(tips)
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: questionary.print(tip, style="dim cyan")
                    )

            await asyncio.sleep(0.8)  # Brief pause for user to read
        except Exception:
            # Enhanced fallback with visual indicators
            self.show_status_indicator("success", "Operation completed successfully!")

            # Show tip in fallback mode too
            import random
            if self.show_tips and random.random() < 0.2:  # 20% chance in fallback
                self.show_status_indicator("info", "Tip: Press 's' for service health status")

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
                    "⚠️  Service Health Warning - Choose your action:",
                    choices=options,
                    default=options[0],
                    style=questionary.Style([
                        ('qmark', 'fg:#ff9800 bold'),       # Orange warning question mark
                        ('question', 'bold fg:#ff9800'),    # Bold orange question
                        ('answer', 'fg:#4caf50 bold'),      # Green answer
                        ('pointer', 'fg:#ff9800 bold'),     # Orange pointer
                        ('selected', 'fg:#4caf50 bold'),    # Green selected
                        ('separator', 'fg:#ff9800'),        # Orange separator
                    ]),
                    use_indicator=True
                ).ask()
            )

            if "Settings" in choice:
                await self._show_loading_spinner("Redirecting to Settings...")
                self.console.print("[green]✅ Redirecting to Settings for service diagnostics...[/green]")
                return False  # Will redirect to settings
            elif "Continue" in choice:
                self.console.print("[yellow]⚠️  Proceeding despite service warnings...[/yellow]")
                return True   # Proceed despite warnings
            else:
                self.console.print("[blue]ℹ️  Returning to main menu...[/blue]")
                return False  # Go back

        except Exception:
            # Enhanced fallback with better guidance
            self.console.print("[yellow]⚠️  Service Dependency Warning[/yellow]")
            self.console.print("[red]❌ Some required services are not available[/red]")
            self.console.print("[cyan]💡 Recommended: Check service status in Settings menu[/cyan]")
            self.console.print("[dim]   Run: python3 run_cli.py interactive → press 's'[/dim]")
            return False

    async def _show_loading_spinner(self, message: str, duration: float = 1.0):
        """Show a loading spinner with message."""
        try:
            from rich.spinner import Spinner
            from rich.live import Live

            spinner = Spinner("dots", text=f"[cyan]{message}[/cyan]")
            with Live(spinner, refresh_per_second=10, console=self.console):
                await asyncio.sleep(duration)
        except Exception:
            # Fallback to simple message
            self.console.print(f"[cyan]{message}[/cyan]")
            await asyncio.sleep(duration * 0.5)

    async def _show_progress_bar(self, operation: str, total: int = 100):
        """Show a progress bar for long-running operations."""
        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(f"[cyan]{operation}...", total=total)

                for i in range(total):
                    await asyncio.sleep(0.02)  # Simulate work
                    progress.update(task, advance=1)

        except Exception:
            # Fallback to simple spinner
            await self._show_loading_spinner(operation, 2.0)

    def show_status_indicator(self, status: str, message: str):
        """Show color-coded status indicators."""
        status_indicators = {
            "success": ("✅", "green"),
            "warning": ("⚠️", "yellow"),
            "error": ("❌", "red"),
            "info": ("ℹ️", "blue"),
            "loading": ("⏳", "cyan"),
            "cached": ("🟢", "green"),
            "stale": ("🟡", "yellow")
        }

        icon, color = status_indicators.get(status, ("❓", "white"))
        self.console.print(f"[{color}]{icon} {message}[/{color}]")

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

def get_interactive_overlay(console: Console, enable_interactive: bool = True,
                           show_tips: bool = True, use_custom_styling: bool = True) -> InteractiveOverlay:
    """Get or create the global interactive overlay instance with configuration options.

    Args:
        console: Rich console instance
        enable_interactive: Whether to use interactive features (default: True)
        show_tips: Whether to show helpful tips (default: True)
        use_custom_styling: Whether to use custom questionary styling (default: True)

    Returns:
        Configured InteractiveOverlay instance
    """
    global interactive_overlay
    if interactive_overlay is None:
        interactive_overlay = InteractiveOverlay(
            console=console,
            enable_interactive=enable_interactive
        )
        interactive_overlay.show_tips = show_tips
        interactive_overlay.use_custom_styling = use_custom_styling

    return interactive_overlay

def configure_interactive_overlay(show_tips: bool = True, use_custom_styling: bool = True) -> None:
    """Configure the global interactive overlay settings.

    Args:
        show_tips: Whether to show helpful tips
        use_custom_styling: Whether to use custom questionary styling
    """
    global interactive_overlay
    if interactive_overlay is not None:
        interactive_overlay.show_tips = show_tips
        interactive_overlay.use_custom_styling = use_custom_styling
