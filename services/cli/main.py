"""CLI Service - Interactive Command Line Interface for LLM Documentation Ecosystem."""

import os
from typing import Dict, Any, List, Optional
import asyncio
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# ============================================================================
# SHARED MODULES - Leveraging centralized functionality for consistency
# ============================================================================
from services.shared.health import register_health_endpoints
from services.shared.constants_new import ServiceNames, ErrorCodes

# ============================================================================
# LOCAL MODULES - Service-specific functionality
# ============================================================================
from .modules.shared_utils import (
    get_cli_clients,
    handle_cli_error,
    create_cli_success_response,
    build_cli_context,
    create_menu_table,
    add_menu_rows,
    print_panel,
    get_service_health_url,
    create_service_health_table,
    create_workflow_status_table,
    create_prompt_table,
    create_search_results_table,
    create_integration_test_table,
    validate_prompt_data,
    extract_variables_from_content,
    format_prompt_details,
    format_analytics_display,
    parse_tags_input,
    create_health_status_display,
    log_cli_metrics
)
from .modules.cli_commands import CLICommands
from .modules.prompt_manager import PromptManager
from .modules.workflow_manager import WorkflowManager


# ============================================================================
# CLI SERVICE - Using modular architecture
# ============================================================================

# Use CLICommands as the main CLI handler
cli_service = CLICommands()

# ============================================================================
# CLI COMMANDS - Using modular CLI service
# ============================================================================

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """LLM Documentation Ecosystem CLI"""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    ctx.obj['cli_service'] = cli_service

@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive CLI mode"""
    asyncio.run(cli_service.run())

@cli.command()
@click.argument('category')
@click.argument('name')
@click.option('--content', '-c', help='Content variable value')
@click.pass_context
def get_prompt(ctx, category, name, content):
    """Get and display a prompt"""
    async def _get_prompt():
        try:
            variables = {}
            if content:
                variables['content'] = content

            response = await cli_service.clients.get_json(f"prompt-store/prompts/search/{category}/{name}", **variables)

            console = Console()
            console.print(f"[bold green]Prompt: {category}.{name}[/bold green]")
            console.print(response.get('prompt', 'No prompt found'))

        except Exception as e:
            console = Console()
            from services.shared.responses import create_error_response
            error_response = create_error_response(
                "Failed to retrieve prompt",
                error_code=ErrorCodes.PROMPT_RETRIEVAL_FAILED,
                details={"category": category, "name": name, "error": str(e)}
            )
            console.print(f"[red]Error: {error_response['message']}[/red]")
            console.print(f"[dim]Error Code: {error_response['error_code']}[/dim]")

    asyncio.run(_get_prompt())

@cli.command()
@click.pass_context
def health(ctx):
    """Check service health"""
    asyncio.run(cli_service.display_health_status())

@cli.command()
@click.option('--category', '-c', help='Filter by category')
@click.pass_context
def list_prompts(ctx, category):
    """List available prompts"""
    prompt_manager = PromptManager(cli_service.console, cli_service.clients)
    asyncio.run(prompt_manager.list_prompts())

@cli.command()
@click.pass_context
def test_integration(ctx):
    """Test service integration"""
    asyncio.run(cli_service.test_integration())

if __name__ == "__main__":
    cli()
