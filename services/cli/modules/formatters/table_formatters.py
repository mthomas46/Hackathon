"""Table formatting utilities for CLI display."""

from typing import Dict, Any, List, Optional
from rich.table import Table
from rich.console import Console


class TableFormatter:
    """Formatter for creating and displaying tables."""

    def __init__(self, console: Console):
        self.console = console

    def create_service_health_table(self, health_data: Dict[str, Dict[str, Any]]) -> Table:
        """Create a table showing service health status."""
        table = Table(title="Service Health Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")

        for service, data in health_data.items():
            status_display, details = self._format_health_status(service, data)
            table.add_row(service, status_display, details)

        return table

    def create_workflow_table(self, workflows: List[Dict[str, Any]]) -> Table:
        """Create a table showing workflow information."""
        table = Table(title="Workflow Status")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Status", style="green")
        table.add_column("Created", style="yellow")

        for workflow in workflows:
            status = workflow.get('status', 'unknown')
            status_display = self._format_status(status)

            table.add_row(
                workflow.get('id', ''),
                workflow.get('name', ''),
                status_display,
                workflow.get('created_at', '')
            )

        return table

    def create_analysis_table(self, analyses: List[Dict[str, Any]]) -> Table:
        """Create a table showing analysis results."""
        table = Table(title="Analysis Results")
        table.add_column("ID", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Status", style="green")
        table.add_column("Findings", style="yellow")

        for analysis in analyses:
            status = analysis.get('status', 'unknown')
            status_display = self._format_status(status)
            findings_count = len(analysis.get('findings', []))

            table.add_row(
                analysis.get('id', ''),
                analysis.get('type', ''),
                status_display,
                str(findings_count)
            )

        return table

    def create_config_table(self, configs: List[Dict[str, Any]]) -> Table:
        """Create a table showing configuration information."""
        table = Table(title="Configuration Files")
        table.add_column("Service", style="cyan")
        table.add_column("File", style="white")
        table.add_column("Type", style="green")
        table.add_column("Size", style="yellow")

        for config in configs:
            table.add_row(
                config.get('service', ''),
                config.get('filename', ''),
                config.get('type', ''),
                config.get('size', '')
            )

        return table

    def _format_health_status(self, service: str, data: Dict[str, Any]) -> tuple[str, str]:
        """Format health status for display."""
        status = data.get('status', 'unknown')

        if status == 'healthy':
            status_display = "[green]✓ Healthy[/green]"
            details = "OK"
        elif status == 'unhealthy':
            status_display = "[red]✗ Unhealthy[/red]"
            details = data.get('error', 'Unknown error')
        else:
            status_display = "[yellow]? Unknown[/yellow]"
            details = f"Status: {status}"

        return status_display, details

    def _format_status(self, status: str) -> str:
        """Format status string for display."""
        status = status.lower()
        if status == 'completed' or status == 'success':
            return "[green]✓ Completed[/green]"
        elif status == 'running' or status == 'in_progress':
            return "[blue]⟳ Running[/blue]"
        elif status == 'failed' or status == 'error':
            return "[red]✗ Failed[/red]"
        elif status == 'pending':
            return "[yellow]⏳ Pending[/yellow]"
        else:
            return f"[dim]{status}[/dim]"
