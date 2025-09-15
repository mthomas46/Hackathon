"""Status formatting utilities for CLI display."""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class StatusFormatter:
    """Formatter for displaying status information."""

    def __init__(self, console: Console):
        self.console = console

    def format_service_status(self, service_name: str, status_data: Dict[str, Any]) -> str:
        """Format service status information for display."""
        status = status_data.get('status', 'unknown')
        timestamp = status_data.get('timestamp', 0)

        if status == 'healthy':
            status_emoji = "✅"
            status_color = "green"
            details = "Service is responding normally"
        elif status == 'unhealthy':
            status_emoji = "❌"
            status_color = "red"
            details = status_data.get('error', 'Service is not responding')
        elif status == 'degraded':
            status_emoji = "⚠️"
            status_color = "yellow"
            details = "Service is experiencing issues"
        else:
            status_emoji = "❓"
            status_color = "dim"
            details = f"Status: {status}"

        return f"[{status_color}]{status_emoji} {service_name}: {details}[/{status_color}]"

    def format_operation_result(self, operation: str, result: Any) -> str:
        """Format operation result for display."""
        if isinstance(result, dict):
            if result.get('success'):
                return f"[green]✅ {operation} completed successfully[/green]"
            else:
                error_msg = result.get('message', 'Unknown error')
                return f"[red]❌ {operation} failed: {error_msg}[/red]"
        elif isinstance(result, bool):
            if result:
                return f"[green]✅ {operation} completed successfully[/green]"
            else:
                return f"[red]❌ {operation} failed[/red]"
        elif isinstance(result, str):
            return f"[blue]ℹ️ {operation}: {result}[/blue]"
        else:
            return f"[blue]ℹ️ {operation} result: {str(result)}[/blue]"

    def format_health_summary(self, health_data: Dict[str, Dict[str, Any]]) -> str:
        """Format a health summary for multiple services."""
        total = len(health_data)
        healthy = sum(1 for data in health_data.values() if data.get('status') == 'healthy')
        unhealthy = total - healthy

        summary = f"Service Health Summary: {healthy}/{total} healthy"
        if unhealthy > 0:
            summary += f" ({unhealthy} unhealthy)"

        return summary

    def format_metrics_summary(self, metrics: Dict[str, Any]) -> str:
        """Format metrics summary for display."""
        lines = ["[bold]System Metrics:[/bold]"]

        for key, value in metrics.items():
            if isinstance(value, float):
                lines.append(f"  {key}: {value:.2f}")
            else:
                lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def format_error_details(self, error: Exception, operation: str) -> str:
        """Format error details for display."""
        error_type = type(error).__name__
        error_msg = str(error)

        details = f"[red]Error during {operation}:[/red]\n"
        details += f"  [bold]Type:[/bold] {error_type}\n"
        details += f"  [bold]Message:[/bold] {error_msg}"

        return details

    def create_status_panel(self, title: str, content: str, status: str = "info") -> Panel:
        """Create a status panel with appropriate styling."""
        colors = {
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "info": "blue"
        }

        color = colors.get(status, "blue")
        return Panel(f"[{color}]{content}[/{color}]", title=f"[{color}]{title}[/{color}]", border_style=color)

    def format_progress_info(self, current: int, total: int, operation: str) -> str:
        """Format progress information."""
        percentage = (current / total * 100) if total > 0 else 0
        return f"[blue]📊 {operation}: {current}/{total} ({percentage:.1f}%)[/blue]"

    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
