"""
Rich terminal feedback utilities.

Provides beautiful terminal output for user-facing operations.
"""

from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax
from rich import box

console = Console()


def print_banner(title: str, subtitle: Optional[str] = None) -> None:
    """
    Print a banner with title.
    
    Args:
        title: Main title
        subtitle: Optional subtitle
    """
    if subtitle:
        text = f"[bold cyan]{title}[/bold cyan]\n[dim]{subtitle}[/dim]"
    else:
        text = f"[bold cyan]{title}[/bold cyan]"
    
    console.print(Panel(text, box=box.DOUBLE, expand=False))


def print_section(title: str) -> None:
    """
    Print a section divider.
    
    Args:
        title: Section title
    """
    console.rule(f"[bold blue]{title}[/bold blue]")


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]✅ {message}[/bold green]")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[bold red]❌ {message}[/bold red]")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[cyan]ℹ️  {message}[/cyan]")


def print_table(
    title: str,
    columns: List[str],
    rows: List[List[Any]],
    show_lines: bool = False
) -> None:
    """
    Print a formatted table.
    
    Args:
        title: Table title
        columns: Column headers
        rows: Table rows
        show_lines: Show row lines
    """
    table = Table(title=title, show_lines=show_lines, box=box.ROUNDED)
    
    for column in columns:
        table.add_column(column, style="cyan")
    
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    
    console.print(table)


def print_tree_structure(title: str, data: Dict[str, Any]) -> None:
    """
    Print a tree structure.
    
    Args:
        title: Tree title
        data: Nested dictionary to display
    """
    tree = Tree(f"[bold]{title}[/bold]")
    
    def add_branch(parent, data_dict):
        for key, value in data_dict.items():
            if isinstance(value, dict):
                branch = parent.add(f"[cyan]{key}[/cyan]")
                add_branch(branch, value)
            elif isinstance(value, list):
                branch = parent.add(f"[cyan]{key}[/cyan]")
                for item in value:
                    branch.add(f"[dim]{item}[/dim]")
            else:
                parent.add(f"[cyan]{key}[/cyan]: {value}")
    
    add_branch(tree, data)
    console.print(tree)


def print_code(code: str, language: str = "python", title: Optional[str] = None) -> None:
    """
    Print syntax-highlighted code.
    
    Args:
        code: Code to display
        language: Programming language
        title: Optional code title
    """
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    
    if title:
        console.print(Panel(syntax, title=title, box=box.ROUNDED))
    else:
        console.print(syntax)


def print_statistics(stats: Dict[str, Any], title: str = "Statistics") -> None:
    """
    Print statistics in a formatted panel.
    
    Args:
        stats: Statistics dictionary
        title: Statistics title
    """
    lines = []
    for key, value in stats.items():
        # Format key
        formatted_key = key.replace("_", " ").title()
        
        # Format value
        if isinstance(value, float):
            formatted_value = f"{value:.2f}"
        elif isinstance(value, int):
            formatted_value = f"{value:,}"
        else:
            formatted_value = str(value)
        
        lines.append(f"[cyan]{formatted_key}[/cyan]: [bold]{formatted_value}[/bold]")
    
    console.print(Panel("\n".join(lines), title=title, box=box.ROUNDED))


def print_progress_summary(
    operation: str,
    total: int,
    successful: int,
    failed: int,
    duration_seconds: float
) -> None:
    """
    Print operation progress summary.
    
    Args:
        operation: Operation name
        total: Total items
        successful: Successful items
        failed: Failed items
        duration_seconds: Operation duration
    """
    success_rate = (successful / total * 100) if total > 0 else 0
    
    stats = {
        "operation": operation,
        "total": total,
        "successful": successful,
        "failed": failed,
        "success_rate": f"{success_rate:.1f}%",
        "duration": f"{duration_seconds:.2f}s",
        "throughput": f"{total / duration_seconds:.1f} items/s" if duration_seconds > 0 else "N/A"
    }
    
    print_statistics(stats, "Operation Summary")


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask user to confirm an action.
    
    Args:
        message: Confirmation message
        default: Default response
    
    Returns:
        User's response
    """
    default_str = "Y/n" if default else "y/N"
    response = console.input(f"[yellow]❓ {message} [{default_str}][/yellow]: ")
    
    if not response:
        return default
    
    return response.lower() in ['y', 'yes']


def print_health_status(
    service: str,
    healthy: bool,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Print health status for a service.
    
    Args:
        service: Service name
        healthy: Health status
        details: Optional health details
    """
    status = "[bold green]✅ Healthy[/bold green]" if healthy else "[bold red]❌ Unhealthy[/bold red]"
    console.print(f"{service}: {status}")
    
    if details:
        for key, value in details.items():
            console.print(f"  [dim]{key}:[/dim] {value}")

