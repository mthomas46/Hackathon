"""Shared utilities for CLI service modules.

This module contains common utilities used across all CLI modules
to eliminate code duplication and ensure consistency.
"""

import os
from typing import Dict, Any, Optional, List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Import shared utilities
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames, ErrorCodes
from services.shared.error_handling import ServiceException, ValidationException
from services.shared.responses import create_success_response, create_error_response
from services.shared.logging import fire_and_forget
from services.shared.utilities import utc_now

# Global configuration for CLI service
_DEFAULT_TIMEOUT = 30
_DEFAULT_USER = os.environ.get("USER", "cli_user")

def get_default_timeout() -> int:
    """Get default service client timeout."""
    return _DEFAULT_TIMEOUT

def get_default_user() -> str:
    """Get default CLI user."""
    return _DEFAULT_USER

def get_cli_clients(timeout: int = _DEFAULT_TIMEOUT) -> ServiceClients:
    """Create and return a ServiceClients instance with proper timeout."""
    return ServiceClients(timeout=timeout)

def handle_cli_error(operation: str, error: Exception, **context) -> Dict[str, Any]:
    """Standardized error handling for CLI operations.

    Logs the error and returns a standardized error response.
    """
    fire_and_forget("error", f"CLI {operation} error: {error}", ServiceNames.CLI, context)
    return create_error_response(
        f"Failed to {operation}",
        error_code=ErrorCodes.INTERNAL_ERROR,
        details={"error": str(error), **context}
    )

def create_cli_success_response(operation: str, data: Any, **context) -> Dict[str, Any]:
    """Standardized success response for CLI operations.

    Returns a consistent success response format.
    """
    return create_success_response(f"CLI {operation} successful", data, **context)

def build_cli_context(operation: str, **additional) -> Dict[str, Any]:
    """Build context dictionary for CLI operations.

    Provides consistent context for logging and responses.
    """
    context = {
        "operation": operation,
        "service": ServiceNames.CLI
    }
    context.update(additional)
    return context

def create_menu_table(title: str, columns: List[str]) -> Table:
    """Create a standardized menu table with consistent styling."""
    table = Table(title=title, show_header=False, border_style="blue")
    for col in columns:
        if col == "Option":
            table.add_column(col, style="cyan", no_wrap=True)
        else:
            table.add_column(col, style="white")
    return table

def add_menu_rows(table: Table, rows: List[Tuple[str, str]]) -> None:
    """Add rows to a menu table."""
    for option, description in rows:
        table.add_row(option, description)

def print_panel(console: Console, content: str, title: str = "", border_style: str = "blue") -> None:
    """Print a formatted panel to the console."""
    panel = Panel.fit(content, title=title, border_style=border_style)
    console.print(panel)

def get_service_health_url(clients: ServiceClients, service_name: str) -> str:
    """Get the health check URL for a specific service."""
    # Use the service client's URL generation methods
    url_map = {
        ServiceNames.ORCHESTRATOR: f"{clients.orchestrator_url()}/health",
        ServiceNames.ANALYSIS_SERVICE: f"{clients.analysis_service_url()}/health",
        ServiceNames.DOC_STORE: f"{clients.doc_store_url()}/health",
        ServiceNames.SOURCE_AGENT: f"{clients.source_agent_url()}/health",
        ServiceNames.PROMPT_STORE: f"{clients.prompt_store_url()}/health",
        ServiceNames.DISCOVERY_AGENT: f"{clients.discovery_agent_url()}/health",
        ServiceNames.INTERPRETER: f"{clients.interpreter_url()}/health",
        ServiceNames.FRONTEND: f"{clients.frontend_url()}/health",
    }

    # For services not in the enum, construct URL
    if service_name not in url_map:
        base_url = getattr(clients, f"{service_name.replace('-', '_')}_url", lambda: "http://localhost:5000")()
        return f"{base_url}/health"

    return url_map.get(service_name, f"http://localhost:5000/health")

def create_service_health_table(services: List[str], clients: ServiceClients) -> Table:
    """Create a formatted table for service health status."""
    table = Table(title="Service Health Status", border_style="green")
    table.add_column("Service", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("URL", style="yellow")

    for service in services:
        url = get_service_health_url(clients, service)
        table.add_row(service, "Checking...", url)

    return table

def create_workflow_status_table() -> Table:
    """Create a formatted table for workflow status."""
    table = Table(title="Active Workflows", border_style="blue")
    table.add_column("Workflow ID", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Service", style="yellow")
    table.add_column("Progress", style="magenta")
    return table

def create_prompt_table(prompts: List[Dict[str, Any]]) -> Table:
    """Create a formatted table for displaying prompts."""
    table = Table(title="Available Prompts")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Category", style="green")
    table.add_column("Version", style="yellow")
    table.add_column("Tags", style="magenta")

    for prompt in prompts:
        tags = ", ".join(prompt.get("tags", []))
        table.add_row(
            prompt.get("id", "")[:8],
            prompt.get("name", ""),
            prompt.get("category", ""),
            str(prompt.get("version", 1)),
            tags
        )

    return table

def create_search_results_table(query: str, prompts: List[Dict[str, Any]]) -> Table:
    """Create a formatted table for search results."""
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("Name", style="white")
    table.add_column("Category", style="green")
    table.add_column("Description", style="dim white")

    for prompt in prompts:
        table.add_row(
            prompt.get("name", ""),
            prompt.get("category", ""),
            prompt.get("description", "")[:50]
        )

    return table

def create_integration_test_table() -> Table:
    """Create a formatted table for integration test results."""
    table = Table(title="Integration Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")
    return table

def sanitize_cli_input(input_str: str, max_length: int = 1000) -> str:
    """Sanitize CLI input to prevent injection attacks."""
    if not isinstance(input_str, str):
        return ""

    import re
    # Remove potentially dangerous characters and patterns
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)
    # Remove shell metacharacters that could be used for command injection
    sanitized = re.sub(r'[;&|`$()<>]', '', sanitized)
    # Remove potential script injection patterns
    sanitized = re.sub(r'[<>\"\'`]', '', sanitized)

    return sanitized.strip()[:max_length]

def validate_prompt_data(name: str, category: str, content: str) -> None:
    """Validate prompt creation/update data with security checks."""
    # Sanitize inputs first
    safe_name = sanitize_cli_input(name)
    safe_category = sanitize_cli_input(category)
    safe_content = sanitize_cli_input(content)

    if not safe_name:
        raise ValidationException(
            "Prompt name is required",
            {"name": ["Cannot be empty or contain invalid characters"]}
        )

    if not safe_category:
        raise ValidationException(
            "Prompt category is required",
            {"category": ["Cannot be empty or contain invalid characters"]}
        )

    if not safe_content:
        raise ValidationException(
            "Prompt content is required",
            {"content": ["Cannot be empty or contain invalid characters"]}
        )

    # Length validation to prevent DoS attacks
    if len(safe_name) > 100:
        raise ValidationException(
            "Prompt name too long",
            {"name": ["Maximum 100 characters allowed"]}
        )
    if len(safe_category) > 50:
        raise ValidationException(
            "Prompt category too long",
            {"category": ["Maximum 50 characters allowed"]}
        )
    if len(safe_content) > 10000:
        raise ValidationException(
            "Prompt content too long",
            {"content": ["Maximum 10,000 characters allowed"]}
        )

def extract_variables_from_content(content: str) -> List[str]:
    """Extract variable placeholders from prompt content."""
    import re
    variables = re.findall(r'\{([^}]+)\}', content)
    return list(set(variables))  # Remove duplicates

def format_prompt_details(prompt_data: Dict[str, Any]) -> str:
    """Format prompt details for display."""
    return (f"[bold cyan]Prompt Details[/bold cyan]\n\n"
            f"[bold]ID:[/bold] {prompt_data.get('id', 'N/A')}\n"
            f"[bold]Name:[/bold] {prompt_data.get('name', 'N/A')}\n"
            f"[bold]Category:[/bold] {prompt_data.get('category', 'N/A')}\n"
            f"[bold]Version:[/bold] {prompt_data.get('version', 'N/A')}\n\n"
            f"[bold]Content:[/bold]\n{prompt_data.get('content', 'N/A')}")

def format_analytics_display(analytics_data: Dict[str, Any]) -> str:
    """Format analytics data for display."""
    return (f"[bold cyan]System Analytics[/bold cyan]\n\n"
            f"[bold]Total Prompts:[/bold] {analytics_data.get('total_prompts', 0)}\n"
            f"[bold]Active Prompts:[/bold] {analytics_data.get('active_prompts', 0)}\n"
            f"[bold]Total Usage:[/bold] {analytics_data.get('total_usage', 0)}\n"
            f"[bold]Avg Performance:[/bold] {analytics_data.get('avg_performance', 0):.2f}")

def parse_tags_input(tags_input: str) -> List[str]:
    """Parse comma-separated tags input."""
    if not tags_input or not tags_input.strip():
        return []

    return [tag.strip() for tag in tags_input.split(",") if tag.strip()]

def create_health_status_display(service_name: str, health_data: Dict[str, Any]) -> Tuple[str, str]:
    """Create display strings for health status."""
    status = health_data.get("status", "unknown")

    if status == "healthy":
        status_display = "[green]✓ Healthy[/green]"
        details = "OK"
    elif status == "unhealthy":
        status_display = "[red]✗ Unhealthy[/red]"
        details = health_data.get("error", "Unknown error")
    else:
        status_display = "[yellow]? Unknown[/yellow]"
        details = f"Status: {status}"

    return status_display, details

def log_cli_metrics(operation: str, duration: float, success: bool, **additional) -> None:
    """Log CLI operation metrics."""
    context = {
        "operation": operation,
        "duration_ms": duration * 1000,
        "success": success,
        "service": ServiceNames.CLI
    }
    context.update(additional)
    fire_and_forget("info", f"CLI operation completed: {operation}", ServiceNames.CLI, context)
