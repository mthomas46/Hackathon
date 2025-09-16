"""Mixins for BaseManager to consolidate common functionality.

This module provides mixins that can be used with BaseManager to reduce
code duplication across different manager implementations.
"""

from typing import Dict, Any, List, Optional, Tuple
from abc import ABC
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
import asyncio

from services.shared.constants_new import ServiceNames


class MenuMixin(ABC):
    """Mixin providing common menu handling functionality."""

    async def run_submenu_loop(self, title: str, menu_items: List[Tuple[str, str]],
                              back_option: str = "b") -> None:
        """Standard submenu loop implementation - ELIMINATES CODE DUPLICATION.

        Args:
            title: Menu title
            menu_items: List of (choice, description) tuples
            back_option: Option to exit menu (default: 'b')
        """
        from ..shared_utils import create_menu_table, add_menu_rows

        while True:
            try:
                # Create and display menu
                menu = create_menu_table(title, ["Option", "Description"])
                add_menu_rows(menu, menu_items + [(back_option, "Back")])
                self.console.print(menu)

                choice = Prompt.ask("[bold green]Select option[/bold green]").strip()

                # Handle quit/exit options
                if choice.lower() in ["q", "quit", "exit"]:
                    break
                elif choice.lower() in [back_option.lower(), "back"]:
                    break
                elif await self.handle_submenu_choice(choice):
                    # Choice handled successfully, show pause message for results
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

    async def handle_submenu_choice(self, choice: str) -> bool:
        """Handle submenu choice. Override in subclasses.

        Args:
            choice: The user's menu choice

        Returns:
            True if choice was handled, False otherwise
        """
        return False


class OperationMixin(ABC):
    """Mixin providing common operation handling functionality."""

    async def monitor_operation(self, operation_id: str, operation_type: str,
                              status_func, completion_func,
                              timeout: int = 300) -> Optional[Dict[str, Any]]:
        """Monitor an async operation with progress indication.

        Args:
            operation_id: Unique identifier for the operation
            operation_type: Type of operation (for display)
            status_func: Function to check status
            completion_func: Function to check completion
            timeout: Maximum time to wait in seconds

        Returns:
            Final operation result or None if timeout
        """
        import time

        start_time = time.time()
        last_status = None

        with self.console.status(f"[bold green]Monitoring {operation_type}...[/bold green]") as status:
            while time.time() - start_time < timeout:
                try:
                    current_status = await status_func()

                    # Update status display if changed
                    if current_status != last_status:
                        status.update(f"[bold green]{operation_type}: {current_status}[/bold green]")
                        last_status = current_status

                    # Check if operation is complete
                    if completion_func(current_status):
                        result = await status_func()  # Get final result
                        self.display.show_success(f"{operation_type} completed successfully")
                        return result

                    await asyncio.sleep(2)  # Poll every 2 seconds

                except Exception as e:
                    self.display.show_warning(f"Status check failed: {e}")
                    await asyncio.sleep(5)  # Wait longer on errors

        self.display.show_warning(f"{operation_type} monitoring timed out after {timeout} seconds")
        return None

    async def api_operation_with_confirm(self, endpoint: str, data: Dict[str, Any],
                                       description: str, confirm_msg: str,
                                       success_msg: str) -> bool:
        """Perform API operation with user confirmation.

        Args:
            endpoint: API endpoint
            data: Request data
            description: Operation description for status
            confirm_msg: Confirmation message to show user
            success_msg: Success message to show

        Returns:
            True if operation succeeded, False otherwise
        """
        if not await self.confirm_action(confirm_msg):
            return False

        response = await self.api_post_with_status(endpoint, data, description)
        if response:
            self.display.show_success(success_msg)
            return True
        return False


class TableMixin(ABC):
    """Mixin providing common table creation and population functionality."""

    def create_and_populate_table(self, title: str, headers: List[str],
                                data_rows: List[List[str]]) -> Table:
        """Create a table and populate it with data.

        Args:
            title: Table title
            headers: Column headers
            data_rows: List of data rows

        Returns:
            Populated Rich table
        """
        from ..shared_utils import create_enhanced_table, add_table_rows

        table = create_enhanced_table(title, headers)
        add_table_rows(table, data_rows)
        return table

    def create_status_table_with_data(self, title: str, status_data: Dict[str, Dict[str, Any]]) -> Table:
        """Create a status table populated with service status data.

        Args:
            title: Table title
            status_data: Dict of service_name -> status_info

        Returns:
            Populated status table
        """
        table = self.create_status_table(title)

        for service, data in status_data.items():
            status = data.get("status", "unknown")
            details = data.get("response", {}).get("message", "No details")

            # Color code status
            if status == "healthy":
                status_display = "[green]✓ Healthy[/green]"
            elif status == "unhealthy":
                status_display = "[red]✗ Unhealthy[/red]"
            else:
                status_display = f"[yellow]? {status}[/yellow]"

            self.add_service_row(table, service, status_display, details)

        return table

    def create_workflow_table_with_data(self, title: str, workflows: List[Dict[str, Any]]) -> Table:
        """Create a workflow table populated with workflow data.

        Args:
            title: Table title
            workflows: List of workflow dictionaries

        Returns:
            Populated workflow table
        """
        table = self.create_workflow_table(title)

        for workflow in workflows:
            workflow_id = workflow.get("id", "N/A")
            status = workflow.get("status", "unknown")
            created = workflow.get("created_at", "N/A")

            # Color code status
            if status == "completed":
                status_display = "[green]✓ Completed[/green]"
            elif status == "running":
                status_display = "[blue]⟳ Running[/blue]"
            elif status == "failed":
                status_display = "[red]✗ Failed[/red]"
            else:
                status_display = f"[yellow]? {status}[/yellow]"

            self.add_workflow_row(table, workflow_id, status_display, created)

        return table

    def create_findings_table_with_data(self, title: str, findings: List[Dict[str, Any]]) -> Table:
        """Create a findings table populated with analysis findings.

        Args:
            title: Table title
            findings: List of finding dictionaries

        Returns:
            Populated findings table
        """
        table = self.create_findings_table(title)

        for finding in findings:
            finding_id = finding.get("id", "N/A")
            severity = finding.get("severity", "unknown")
            description = finding.get("description", "No description")[:50] + "..."

            # Color code severity
            if severity == "high":
                severity_display = "[red]🔴 High[/red]"
            elif severity == "medium":
                severity_display = "[yellow]🟡 Medium[/yellow]"
            elif severity == "low":
                severity_display = "[green]🟢 Low[/green]"
            else:
                severity_display = f"[gray]{severity}[/gray]"

            self.add_finding_row(table, finding_id, severity_display, description)

        return table


class ValidationMixin(ABC):
    """Mixin providing common validation and error handling functionality."""

    def validate_required_params(self, params: Dict[str, Any], required: List[str]) -> bool:
        """Validate that required parameters are present.

        Args:
            params: Parameters to validate
            required: List of required parameter names

        Returns:
            True if all required params present, False otherwise
        """
        missing = [key for key in required if key not in params or params[key] is None]

        if missing:
            self.display.show_error(f"Missing required parameters: {', '.join(missing)}")
            return False

        return True

    def validate_enum_value(self, value: str, allowed_values: List[str], param_name: str) -> bool:
        """Validate that a value is in allowed enum values.

        Args:
            value: Value to validate
            allowed_values: List of allowed values
            param_name: Parameter name for error messages

        Returns:
            True if value is valid, False otherwise
        """
        if value not in allowed_values:
            self.display.show_error(
                f"Invalid {param_name}: '{value}'. Must be one of: {', '.join(allowed_values)}"
            )
            return False

        return True

    async def handle_operation_error(self, operation: str, error: Exception,
                                   retry_func=None, max_retries: int = 0) -> bool:
        """Handle operation errors with optional retry logic.

        Args:
            operation: Operation description
            error: The exception that occurred
            retry_func: Optional function to retry
            max_retries: Maximum number of retries

        Returns:
            True if error was handled/recovered, False otherwise
        """
        self.display.show_error(f"{operation} failed: {error}")

        if retry_func and max_retries > 0:
            if await self.confirm_action(f"Retry {operation}?"):
                try:
                    await retry_func()
                    self.display.show_success(f"{operation} succeeded on retry")
                    return True
                except Exception as retry_error:
                    self.display.show_error(f"Retry also failed: {retry_error}")

        return False


class HealthCheckMixin(ABC):
    """Mixin providing service health checking functionality."""

    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check the health of a specific service.

        Args:
            service_name: Name of the service to check

        Returns:
            Dict containing health status information
        """
        try:
            # Get service health URL
            health_url = self._get_service_health_url(service_name)

            # Attempt to connect with timeout
            response = await asyncio.wait_for(
                self.clients.get_json(health_url),
                timeout=5.0  # 5 second timeout
            )

            return {
                "status": "healthy",
                "response": response,
                "timestamp": asyncio.get_event_loop().time()
            }

        except asyncio.TimeoutError:
            return {
                "status": "unreachable",
                "error": "Service timeout (5s)",
                "timestamp": asyncio.get_event_loop().time()
            }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }

    async def check_services_health(self, service_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Check health of multiple services.

        Args:
            service_names: List of service names to check

        Returns:
            Dict mapping service names to health status
        """
        results = {}

        with self.console.status(f"[bold green]Checking {len(service_names)} services...[/bold green]") as status:
            tasks = []
            for service_name in service_names:
                task = asyncio.create_task(self.check_service_health(service_name))
                tasks.append((service_name, task))

            for service_name, task in tasks:
                results[service_name] = await task

        return results

    def _get_service_health_url(self, service_name: str) -> str:
        """Get the health check URL for a service.

        Args:
            service_name: Name of the service

        Returns:
            Health check URL for the service
        """
        # Map service names to their health URLs
        url_map = {
            ServiceNames.ORCHESTRATOR: f"{self.clients.orchestrator_url()}/health",
            ServiceNames.ANALYSIS_SERVICE: f"{self.clients.analysis_service_url()}/health",
            ServiceNames.DOC_STORE: f"{self.clients.doc_store_url()}/health",
            ServiceNames.SOURCE_AGENT: f"{self.clients.source_agent_url()}/health",
            ServiceNames.PROMPT_STORE: f"{self.clients.prompt_store_url()}/health",
            ServiceNames.DISCOVERY_AGENT: f"{self.clients.discovery_agent_url()}/health",
            ServiceNames.INTERPRETER: f"{self.clients.interpreter_url()}/health",
            ServiceNames.FRONTEND: f"{self.clients.frontend_url()}/health",
            ServiceNames.SUMMARIZER_HUB: f"{self.clients.summarizer_hub_url()}/health",
            ServiceNames.SECURE_ANALYZER: f"{self.clients.secure_analyzer_url()}/health",
            ServiceNames.MEMORY_AGENT: f"{self.clients.memory_agent_url()}/health",
            ServiceNames.CODE_ANALYZER: f"{self.clients.code_analyzer_url()}/health",
            ServiceNames.LOG_COLLECTOR: f"{self.clients.log_collector_url()}/health",
            ServiceNames.NOTIFICATION_SERVICE: f"{self.clients.notification_service_url()}/health"
        }

        return url_map.get(service_name, f"http://localhost:5000/health")

    def is_service_healthy(self, health_data: Dict[str, Any]) -> bool:
        """Check if a service health response indicates healthy status.

        Args:
            health_data: Health check response data

        Returns:
            True if service is healthy, False otherwise
        """
        return health_data.get("status") == "healthy"

    def format_health_status(self, service_name: str, health_data: Dict[str, Any]) -> Tuple[str, str]:
        """Format health status for display.

        Args:
            service_name: Name of the service
            health_data: Health check data

        Returns:
            Tuple of (status_display, details)
        """
        status = health_data.get("status", "unknown")

        if status == "healthy":
            status_display = "[green]✓ Healthy[/green]"
            details = "Service responding normally"
        elif status == "unreachable":
            error = health_data.get("error", "Unknown error")
            status_display = "[red]✗ Unreachable[/red]"
            details = f"Cannot connect: {error}"
        else:
            status_display = "[yellow]? Unknown[/yellow]"
            details = f"Status: {status}"

        return status_display, details

    async def display_service_health_table(self, health_results: Dict[str, Dict[str, Any]],
                                          title: str = "Service Health Status") -> None:
        """Display service health results in a formatted table.

        Args:
            health_results: Dict mapping service names to health data
            title: Table title
        """
        table = Table(title=title, border_style="blue")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")

        for service_name, health_data in health_results.items():
            status_display, details = self.format_health_status(service_name, health_data)
            table.add_row(service_name, status_display, details)

        self.console.print(table)
