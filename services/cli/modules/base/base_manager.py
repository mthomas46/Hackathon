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
from .mixins import MenuMixin, OperationMixin, TableMixin, ValidationMixin, HealthCheckMixin


class BaseManager(MenuMixin, OperationMixin, TableMixin, ValidationMixin, HealthCheckMixin, ABC):
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

    def get_required_services(self) -> List[str]:
        """Return list of services required by this manager.

        Override this method in subclasses to specify which services
        must be running for the manager's features to work.

        Returns:
            List of service names (from ServiceNames constants)
        """
        return []

    async def check_required_services(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all required services.

        Returns:
            Dict mapping service names to health status
        """
        required_services = self.get_required_services()
        if not required_services:
            return {}

        return await self.check_services_health(required_services)

    async def validate_service_dependencies(self) -> bool:
        """Validate that all required services are healthy.

        Returns:
            True if all required services are healthy, False otherwise
        """
        health_results = await self.check_required_services()
        if not health_results:
            return True  # No required services

        unhealthy_services = []
        for service_name, health_data in health_results.items():
            if not self.is_service_healthy(health_data):
                unhealthy_services.append(service_name)

        if unhealthy_services:
            self.display.show_error(
                f"The following required services are not available: {', '.join(unhealthy_services)}"
            )
            self.display.show_info(
                "Please ensure services are running and try again, or check service status in Settings."
            )
            return False

        return True


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

    def create_status_table(self, title: str) -> Table:
        """Create a standard status table."""
        from ..shared_utils import create_enhanced_table
        return create_enhanced_table(title, ["Service", "Status", "Details"])

    def create_workflow_table(self, title: str = "Active Workflows") -> Table:
        """Create a standard workflow table."""
        from ..shared_utils import create_enhanced_table
        return create_enhanced_table(title, ["ID", "Status", "Type", "Progress", "Started"])

    def create_service_table(self, title: str = "Services") -> Table:
        """Create a standard service table."""
        from ..shared_utils import create_enhanced_table
        return create_enhanced_table(title, ["Name", "URL", "Status", "Last Seen"])

    def create_findings_table(self, title: str = "Analysis Findings") -> Table:
        """Create a standard findings table."""
        from ..shared_utils import create_enhanced_table
        return create_enhanced_table(title, ["ID", "Type", "Severity", "Title", "Target"])

    def add_workflow_row(self, table: Table, workflow: Dict[str, Any]) -> None:
        """Add a workflow row to a workflow table."""
        status_color = {
            "running": "yellow",
            "completed": "green",
            "failed": "red",
            "pending": "blue"
        }.get(workflow.get("status", "unknown"), "white")

        table.add_row(
            workflow.get("id", "N/A")[:8],
            f"[{status_color}]{workflow.get('status', 'unknown')}[/{status_color}]",
            workflow.get("type", "unknown"),
            f"{workflow.get('progress', 0)}%",
            workflow.get("started_at", "unknown")
        )

    def add_service_row(self, table: Table, service: Dict[str, Any]) -> None:
        """Add a service row to a service table."""
        status_color = "green" if service.get("status") == "healthy" else "red"
        table.add_row(
            service.get("name", "N/A"),
            service.get("url", "N/A"),
            f"[{status_color}]{service.get('status', 'unknown')}[/{status_color}]",
            service.get("last_seen", "unknown")
        )

    def add_finding_row(self, table: Table, finding: Dict[str, Any]) -> None:
        """Add a finding row to a findings table."""
        severity_color = {
            "critical": "red",
            "high": "red",
            "medium": "yellow",
            "low": "green",
            "info": "blue"
        }.get(finding.get("severity", "unknown"), "white")

        table.add_row(
            finding.get("id", "N/A")[:8],
            finding.get("type", "unknown"),
            f"[{severity_color}]{finding.get('severity', 'unknown')}[/{severity_color}]",
            finding.get("title", "No title")[:50],
            finding.get("target", "unknown")[:30]
        )

    async def monitor_operation(self, operation_id: str, operation_type: str,
                               status_func, success_check, progress_func=None,
                               interval: int = 2) -> bool:
        """Generic monitoring utility for async operations.

        Args:
            operation_id: ID of the operation to monitor
            operation_type: Type of operation (workflow, analysis, etc.)
            status_func: Async function to get status (should return dict with status info)
            success_check: Function to check if operation completed successfully
            progress_func: Optional function to display progress
            interval: Polling interval in seconds

        Returns:
            bool: True if operation completed successfully
        """
        import asyncio

        self.console.print(f"[yellow]Monitoring {operation_type} {operation_id}...[/yellow]")

        while True:
            try:
                await asyncio.sleep(interval)

                status_data = await status_func(operation_id)

                if success_check(status_data):
                    status = status_data.get("status", "unknown")
                    if status == "success" or status == "completed":
                        self.display.show_success(f"{operation_type.title()} {operation_id} completed successfully!")
                    else:
                        self.display.show_error(f"{operation_type.title()} {operation_id} failed: {status_data.get('error', 'Unknown error')}")
                    return status == "success" or status == "completed"
                elif status_data.get("failed"):
                    self.display.show_error(f"{operation_type.title()} {operation_id} failed: {status_data.get('error', 'Unknown error')}")
                    return False
                else:
                    # Still running, show progress if available
                    if progress_func:
                        progress_func(status_data)
                    else:
                        progress = status_data.get("progress", 0)
                        current_step = status_data.get("current_step", "processing")
                        self.console.print(f"[yellow]⏳ Progress: {progress}% - {current_step}[/yellow]")

            except KeyboardInterrupt:
                self.display.show_warning(f"Stopped monitoring {operation_type}")
                return False
            except Exception as e:
                self.display.show_error(f"Error monitoring {operation_type}: {e}")
                return False

    async def api_get_with_status(self, endpoint: str, description: str) -> Optional[Dict[str, Any]]:
        """Make GET request with status message and error handling."""
        with self.console.status(f"[bold green]{description}...[/bold green]") as status:
            try:
                return await self.clients.get_json(endpoint)
            except Exception as e:
                self.display.show_error(f"Error {description}: {e}")
                return None

    async def api_post_with_status(self, endpoint: str, data: Dict[str, Any],
                                  description: str, success_msg: str = None) -> Optional[Dict[str, Any]]:
        """Make POST request with status message and error handling."""
        with self.console.status(f"[bold green]{description}...[/bold green]") as status:
            try:
                result = await self.clients.post_json(endpoint, data)
                if success_msg:
                    self.display.show_success(success_msg)
                return result
            except Exception as e:
                self.display.show_error(f"Error {description}: {e}")
                return None

    async def api_operation_with_confirm(self, endpoint: str, data: Dict[str, Any],
                                        description: str, confirm_msg: str,
                                        success_msg: str) -> bool:
        """Perform API operation with user confirmation."""
        if not await self.confirm_action(confirm_msg):
            self.display.show_info(f"{description} cancelled.")
            return False

        result = await self.api_post_with_status(endpoint, data, description, success_msg)
        return result is not None

    async def run_menu_loop(self, title: str, menu_items: Optional[List[tuple[str, str]]] = None,
                           back_option: str = "b") -> None:
        """Standard menu loop implementation - ELIMINATES CODE DUPLICATION.

        Args:
            title: Menu title
            menu_items: List of (choice, description) tuples. If None, calls get_main_menu()
            back_option: Option to exit menu (default: 'b')
        """
        # Use provided menu_items or get them from the manager
        items = menu_items if menu_items is not None else await self.get_main_menu()

        # Delegate to mixin for the actual menu loop
        await self.run_submenu_loop(title, items, back_option)

    async def handle_submenu_choice(self, choice: str) -> bool:
        """Handle submenu choice by delegating to handle_choice with service validation."""
        # Check service dependencies before allowing menu progression
        if not await self.validate_service_dependencies():
            return False

        return await self.handle_choice(choice)
