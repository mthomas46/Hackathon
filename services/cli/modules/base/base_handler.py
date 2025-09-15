"""Base handler class for CLI command handling."""

from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from rich.console import Console
from rich.prompt import Prompt, Confirm


class BaseHandler(ABC):
    """Base class for CLI command handlers."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        self.console = console
        self.clients = clients
        self.cache = cache or {}

    @abstractmethod
    async def handle_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Handle a specific command. Return result dict."""
        pass

    async def validate_input(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data against a schema."""
        errors = {}

        for field, rules in schema.items():
            if rules.get('required', False) and field not in data:
                errors[field] = "This field is required"
            elif field in data:
                value = data[field]
                if 'type' in rules:
                    if rules['type'] == 'string' and not isinstance(value, str):
                        errors[field] = "Must be a string"
                    elif rules['type'] == 'int' and not isinstance(value, int):
                        errors[field] = "Must be an integer"
                    elif rules['type'] == 'bool' and not isinstance(value, bool):
                        errors[field] = "Must be a boolean"

                if 'min_length' in rules and isinstance(value, str):
                    if len(value) < rules['min_length']:
                        errors[field] = f"Must be at least {rules['min_length']} characters"

                if 'choices' in rules and value not in rules['choices']:
                    errors[field] = f"Must be one of: {', '.join(rules['choices'])}"

        return errors

    async def get_user_confirmation(self, message: str, default: bool = False) -> bool:
        """Get user confirmation."""
        return Confirm.ask(f"[yellow]{message}[/yellow]", default=default)

    async def get_user_choice(self, prompt: str, choices: List[str]) -> Optional[str]:
        """Get user choice from a list."""
        self.console.print(f"\n[bold]{prompt}:[/bold]")
        for i, choice in enumerate(choices, 1):
            self.console.print(f"  {i}. {choice}")

        while True:
            response = Prompt.ask("Enter number").strip()
            try:
                index = int(response) - 1
                if 0 <= index < len(choices):
                    return choices[index]
                else:
                    self.console.print("[red]Invalid choice[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number[/red]")

    async def handle_errors_gracefully(self, operation: str, error: Exception) -> Dict[str, Any]:
        """Handle errors gracefully and return error response."""
        from ..utils.error_utils import handle_cli_error
        return handle_cli_error(operation, error)

    def log_command(self, command: str, **context):
        """Log command execution."""
        from ..utils.metrics_utils import log_cli_command
        log_cli_command(command, **context)

    async def execute_with_retry(self, coro: Callable, max_retries: int = 3,
                                backoff_factor: float = 1.0) -> Any:
        """Execute coroutine with retry logic."""
        import asyncio

        for attempt in range(max_retries):
            try:
                return await coro()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e

                wait_time = backoff_factor * (2 ** attempt)
                self.console.print(f"[yellow]Attempt {attempt + 1} failed, retrying in {wait_time:.1f}s...[/yellow]")
                await asyncio.sleep(wait_time)

        return None  # Should not reach here
