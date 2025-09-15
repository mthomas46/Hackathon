"""Service: CLI Service

Commands:
- interactive: Start interactive CLI mode with menu-driven interface
- get-prompt <category> <name>: Retrieve and display a specific prompt
- health: Check health status of all ecosystem services
- list-prompts: List all available prompts with optional category filtering
- test-integration: Run comprehensive integration tests across all services

Responsibilities:
- Provide command-line interface for ecosystem management and operations
- Enable interactive prompt management and testing workflows
- Display real-time health status and service integration testing
- Support both programmatic and interactive usage patterns
- Offer rich terminal UI with tables, panels, and colored output

Features:
- Interactive menu system with keyboard navigation
- Rich terminal output with syntax highlighting and formatting
- Service health monitoring and integration testing
- Prompt retrieval and management capabilities
- Workflow execution and status monitoring

Dependencies: All ecosystem services via HTTP clients, Rich library for UI.
"""

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

# Service configuration constants
SERVICE_NAME = "cli"
SERVICE_TITLE = "CLI Service"
SERVICE_VERSION = "1.0.0"

# ============================================================================
# CLI SERVICE - Using modular architecture
# ============================================================================

# Use CLICommands as the main CLI handler
cli_service = CLICommands()

# ============================================================================
# CLI COMMANDS - Using modular CLI service
# ============================================================================

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output with detailed information')
@click.pass_context
def cli(ctx, verbose):
    """LLM Documentation Ecosystem CLI - Interactive command-line interface for ecosystem management"""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    ctx.obj['cli_service'] = cli_service

@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive CLI mode with menu-driven interface for ecosystem operations"""
    asyncio.run(cli_service.run())

@cli.command()
@click.argument('category')
@click.argument('name')
@click.option('--content', '-c', help='Content variable value for prompt template substitution')
@click.pass_context
def get_prompt(ctx, category, name, content):
    """Retrieve and display a prompt from the Prompt Store with optional variable substitution"""
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
    """Check and display health status of all ecosystem services with detailed connectivity information"""
    asyncio.run(cli_service.display_health_status())

@cli.command()
@click.option('--category', '-c', help='Filter prompts by specific category (e.g., analysis, consistency)')
@click.pass_context
def list_prompts(ctx, category):
    """List all available prompts from Prompt Store with optional category filtering"""
    prompt_manager = PromptManager(cli_service.console, cli_service.clients)
    asyncio.run(prompt_manager.list_prompts())

@cli.command()
@click.pass_context
def test_integration(ctx):
    """Run comprehensive integration tests across all ecosystem services to verify connectivity and functionality"""
    asyncio.run(cli_service.test_integration())

if __name__ == "__main__":
    cli()
