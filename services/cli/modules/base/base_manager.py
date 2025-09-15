"""Base manager class providing common functionality for all CLI managers."""

from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
import time
import asyncio

from ..utils.cache_utils import CacheManager
from ..utils.api_utils import APIClient
from ..formatters.display_utils import DisplayManager


class BaseManager(ABC):
    """Base class for all CLI managers providing common functionality."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        self.console = console
        self.clients = clients
        self.cache = cache or {}
        self.cache_manager = CacheManager(cache)
        self.api_client = APIClient(clients, console)
        self.display = DisplayManager(console)

    @abstractmethod
    async def get_main_menu(self) -> List[Tuple[str, str]]:
        """Return the main menu items for this manager."""
        pass

    @abstractmethod
    async def handle_choice(self, choice: str) -> bool:
        """Handle a menu choice. Return True to continue, False to exit."""
        pass

    async def run_menu_loop(self, title: str):
        """Run the standard menu loop for this manager."""
        while True:
            try:
                menu_items = await self.get_main_menu()
                self.display.show_menu(title, menu_items)

                choice = Prompt.ask("[bold green]Select option[/bold green]").strip()

                if choice.lower() in ["q", "quit", "exit"]:
                    break
                elif choice.lower() == "b" or choice.lower() == "back":
                    break
                elif await self.handle_choice(choice):
                    # Choice handled successfully, show pause message
                    if choice not in ["h", "help"]:
                        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
                else:
                    self.display.show_error("Invalid option. Please try again.")

            except KeyboardInterrupt:
                self.display.show_warning("Operation interrupted by user")
                break
            except Exception as e:
                self.display.show_error(f"Menu error: {e}")
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    async def confirm_action(self, message: str, default: bool = False) -> bool:
        """Get user confirmation for an action."""
        return Confirm.ask(f"[yellow]{message}[/yellow]", default=default)

    async def get_user_input(self, prompt: str, default: str = "", password: bool = False) -> str:
        """Get user input with optional default and password masking."""
        if password:
            return Prompt.ask(prompt, password=True)
        return Prompt.ask(prompt, default=default) if default else Prompt.ask(prompt)

    async def select_from_list(self, items: List[str], prompt: str = "Select item") -> Optional[str]:
        """Present a numbered list for user selection."""
        if not items:
            self.display.show_warning("No items available")
            return None

        self.console.print(f"\n[bold]{prompt}:[/bold]")
        for i, item in enumerate(items, 1):
            self.console.print(f"  {i}. {item}")

        while True:
            choice = Prompt.ask("Enter number (or 'c' to cancel)").strip()
            if choice.lower() == 'c':
                return None
            try:
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return items[index]
                else:
                    self.display.show_error("Invalid selection")
            except ValueError:
                self.display.show_error("Please enter a valid number")

    async def run_with_progress(self, coro, description: str = "Processing"):
        """Run a coroutine with progress indication."""
        with self.console.status(f"[bold green]{description}...[/bold green]") as status:
            try:
                return await coro
            except Exception as e:
                self.display.show_error(f"Error during {description}: {e}")
                raise

    def log_operation(self, operation: str, **context):
        """Log an operation for analytics."""
        from ..utils.metrics_utils import log_cli_operation
        log_cli_operation(operation, **context)

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        return await self.cache_manager.get(key)

    async def cache_set(self, key: str, value: Any, ttl: int = 300):
        """Set cached value with TTL."""
        await self.cache_manager.set(key, value, ttl)
