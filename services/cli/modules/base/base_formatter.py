"""Base formatter class for CLI display formatting."""

from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.layout import Layout


class BaseFormatter(ABC):
    """Base class for CLI display formatters."""

    def __init__(self, console: Console):
        self.console = console

    def create_table(self, title: str, columns: List[str], styles: Optional[List[str]] = None) -> Table:
        """Create a styled table."""
        table = Table(title=title)

        if styles is None:
            styles = ["cyan", "white", "green", "yellow", "magenta"]

        for i, column in enumerate(columns):
            style = styles[i % len(styles)]
            table.add_column(column, style=style)

        return table

    def add_table_rows(self, table: Table, rows: List[List[str]], max_rows: Optional[int] = None):
        """Add rows to table with optional limiting."""
        display_rows = rows[:max_rows] if max_rows else rows

        for row in display_rows:
            table.add_row(*row)

        if max_rows and len(rows) > max_rows:
            table.add_row(*["[dim]...[/dim]"] * len(rows[0]))
            table.add_row(*[f"[dim]+{len(rows) - max_rows} more[/dim]"] + [""] * (len(rows[0]) - 1))

    def show_panel(self, content: str, title: Optional[str] = None,
                   border_style: str = "blue", expand: bool = False):
        """Show content in a styled panel."""
        panel = Panel(content, title=title, border_style=border_style, expand=expand)
        self.console.print(panel)

    def show_success(self, message: str):
        """Show success message."""
        self.console.print(f"[green]✅ {message}[/green]")

    def show_error(self, message: str):
        """Show error message."""
        self.console.print(f"[red]❌ {message}[/red]")

    def show_warning(self, message: str):
        """Show warning message."""
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")

    def show_info(self, message: str):
        """Show info message."""
        self.console.print(f"[blue]ℹ️  {message}[/blue]")

    def format_dict(self, data: Dict[str, Any], title: Optional[str] = None) -> str:
        """Format a dictionary for display."""
        if not data:
            return "[dim]No data available[/dim]"

        lines = []
        if title:
            lines.append(f"[bold]{title}:[/bold]")

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"  [cyan]{key}:[/cyan]")
                for k, v in value.items():
                    lines.append(f"    {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"  [cyan]{key}:[/cyan] [{len(value)} items]")
                for i, item in enumerate(value[:3]):  # Show first 3
                    lines.append(f"    {i+1}. {item}")
                if len(value) > 3:
                    lines.append(f"    [dim]... and {len(value)-3} more[/dim]")
            else:
                lines.append(f"  [cyan]{key}:[/cyan] {value}")

        return "\n".join(lines)

    def format_list(self, items: List[Any], title: Optional[str] = None) -> str:
        """Format a list for display."""
        if not items:
            return "[dim]No items available[/dim]"

        lines = []
        if title:
            lines.append(f"[bold]{title} ({len(items)} items):[/bold]")

        for i, item in enumerate(items, 1):
            if isinstance(item, dict):
                lines.append(f"  {i}. {item.get('name', item.get('id', str(item)))}")
            else:
                lines.append(f"  {i}. {item}")

        return "\n".join(lines)

    def create_columns(self, items: List[str], equal: bool = True) -> Columns:
        """Create a column layout."""
        return Columns(items, equal=equal)

    def create_layout(self) -> Layout:
        """Create a basic layout."""
        return Layout()

    @abstractmethod
    def format_service_status(self, service_name: str, status_data: Dict[str, Any]) -> str:
        """Format service status information."""
        pass

    @abstractmethod
    def format_operation_result(self, operation: str, result: Any) -> str:
        """Format operation result for display."""
        pass
