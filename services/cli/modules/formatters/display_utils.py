"""Display utilities for CLI formatting."""

from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns


class DisplayManager:
    """Manager for CLI display operations."""

    def __init__(self, console: Console):
        self.console = console

    def show_menu(self, title: str, menu_items: List[Tuple[str, str]]):
        """Display a menu with title and items."""
        table = Table(title=f"[bold blue]{title}[/bold blue]")
        table.add_column("Option", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")

        for option, description in menu_items:
            table.add_row(option, description)

        self.console.print(table)

    def show_table(self, title: str, columns: List[str], rows: List[List[str]],
                   styles: Optional[List[str]] = None, max_rows: Optional[int] = None):
        """Display a table with data."""
        table = Table(title=title)

        if styles is None:
            styles = ["cyan", "white", "green", "yellow", "magenta"]

        for i, column in enumerate(columns):
            style = styles[i % len(styles)]
            table.add_column(column, style=style)

        display_rows = rows[:max_rows] if max_rows else rows

        for row in display_rows:
            table.add_row(*row)

        if max_rows and len(rows) > max_rows:
            table.add_row(*["[dim]...[/dim]"] * len(rows[0]))
            table.add_row(*[f"[dim]+{len(rows) - max_rows} more[/dim]"] + [""] * (len(rows[0]) - 1))

        self.console.print(table)

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

    def show_dict(self, data: Dict[str, Any], title: Optional[str] = None):
        """Display a dictionary in formatted form."""
        if not data:
            self.show_info("No data available")
            return

        content_lines = []
        if title:
            content_lines.append(f"[bold]{title}:[/bold]")

        for key, value in data.items():
            if isinstance(value, dict):
                content_lines.append(f"  [cyan]{key}:[/cyan]")
                for k, v in value.items():
                    content_lines.append(f"    {k}: {v}")
            elif isinstance(value, list):
                content_lines.append(f"  [cyan]{key}:[/cyan] [{len(value)} items]")
                for i, item in enumerate(value[:3]):  # Show first 3
                    content_lines.append(f"    {i+1}. {item}")
                if len(value) > 3:
                    content_lines.append(f"    [dim]... and {len(value)-3} more[/dim]")
            else:
                content_lines.append(f"  [cyan]{key}:[/cyan] {value}")

        content = "\n".join(content_lines)
        self.show_panel(content)

    def show_list(self, items: List[Any], title: Optional[str] = None):
        """Display a list in formatted form."""
        if not items:
            self.show_info("No items available")
            return

        content_lines = []
        if title:
            content_lines.append(f"[bold]{title} ({len(items)} items):[/bold]")

        for i, item in enumerate(items, 1):
            if isinstance(item, dict):
                name = item.get('name', item.get('id', str(item)))
                content_lines.append(f"  {i}. {name}")
            else:
                content_lines.append(f"  {i}. {item}")

        content = "\n".join(content_lines)
        self.show_panel(content)

    def show_columns(self, items: List[str], title: Optional[str] = None):
        """Display items in columns."""
        if title:
            self.console.print(f"[bold]{title}:[/bold]")
        columns = Columns(items, equal=True)
        self.console.print(columns)

    def show_progress(self, description: str = "Processing"):
        """Show a progress indicator (returns context manager)."""
        return self.console.status(f"[bold green]{description}...[/bold green]")

    def show_separator(self):
        """Show a visual separator."""
        self.console.print("[dim]" + "─" * 80 + "[/dim]")

    def clear_screen(self):
        """Clear the console screen."""
        self.console.clear()

    def show_service_status(self, service_name: str, status_data: Dict[str, Any]):
        """Show formatted service status."""
        status = status_data.get('status', 'unknown')

        if status == 'healthy':
            status_display = "[green]✓ Healthy[/green]"
            details = "OK"
        elif status == 'unhealthy':
            status_display = "[red]✗ Unhealthy[/red]"
            details = status_data.get('error', 'Unknown error')
        else:
            status_display = "[yellow]? Unknown[/yellow]"
            details = f"Status: {status}"

        self.console.print(f"{service_name}: {status_display} - {details}")
