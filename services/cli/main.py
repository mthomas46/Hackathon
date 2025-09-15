"""Service: CLI Service

Commands:
- interactive: Start interactive CLI mode with menu-driven interface
- get-prompt <category> <name>: Retrieve and display a specific prompt
- health: Check health status of all ecosystem services
- list-prompts: List all available prompts with optional category filtering
- test-integration: Run comprehensive integration tests across all services

Power User Commands:
- analyze-docs [--type TYPE] [--criteria JSON]: Mass document analysis
- quality-recalc [--type TYPE] [--threshold FLOAT]: Bulk quality recalculation
- bulk-export --format FORMAT [--criteria JSON]: Bulk document export
- bulk-import --file FILE --format FORMAT: Bulk document import
- notify-owners --criteria JSON --message TEXT: Notify document owners
- workflow-run --type TYPE [--config JSON]: Run orchestrator workflows
- redis-info: Display Redis server information
- dlq-stats: Show dead letter queue statistics
- saga-monitor: Monitor active sagas
- tracing-search --criteria JSON: Search distributed traces
- interpret-query "QUERY": Interpret a natural language query
- execute-workflow "QUERY": Interpret and execute a workflow from query
- list-intents: Show all supported query intents
- discover-service --name NAME --url URL [--spec FILE] [--dry-run]: Discover and register service endpoints
- store-memory --type TYPE --key KEY --summary TEXT [--data JSON]: Store operational context in memory
- list-memory [--type TYPE] [--key KEY] [--limit N]: List stored memory items
- detect-content CONTENT [--keywords KW1,KW2]: Analyze content for security risks
- suggest-models CONTENT: Get AI model recommendations based on content sensitivity
- secure-summarize CONTENT [--override-policy]: Generate secure summary with policy enforcement
- ensemble-summarize CONTENT --providers PROVIDERS: Generate summaries using multiple AI providers
- test-provider PROVIDER: Test connectivity to an AI provider
- analyze-code CONTENT [--language LANG] [--repo REPO]: Analyze code for API endpoints and patterns
- scan-security CONTENT [--keywords KW1,KW2]: Scan code for security vulnerabilities
- update-owner --id ID [--owner NAME] [--team TEAM]: Update owner information
- resolve-owners OWNER1,OWNER2: Resolve owners to notification targets
- send-notification --channel CHANNEL --target TARGET --title TITLE --message MESSAGE: Send notification
- view-dlq [--limit N]: View failed notifications in dead letter queue
- submit-log --service SERVICE --level LEVEL --message MESSAGE: Submit a log entry
- query-logs [--service SERVICE] [--level LEVEL] [--limit N]: Query stored logs
- log-stats: View log statistics and analytics
- invoke-ai --prompt PROMPT [--template TEMPLATE] [--format FORMAT]: Invoke AI model with optional template
- ai-templates: List available AI response templates
- ai-history [--limit N]: View recent AI invocation history
- analyze-docs DOC_IDS [--detectors DETECTORS]: Analyze documents for consistency and issues
- get-findings [--severity SEVERITY] [--type TYPE] [--limit N]: Retrieve analysis findings
- generate-report --type TYPE: Generate analysis reports (summary/trends/quality)
- view-config [--service SERVICE]: View service configuration files
- set-env VAR VALUE: Set environment variable
- get-env: Show current environment variables
- validate-config: Validate configuration files and environment variables
- scale-service SERVICE REPLICAS: Scale a service to specified number of replicas
- deployment-status: View current deployment and scaling status
- deploy-service SERVICE IMAGE [--strategy STRATEGY]: Deploy service with new image
- view-dashboards: List available monitoring dashboards
- view-alerts: Show active monitoring alerts
- view-slo-status: Display SLO/SLA compliance status
- view-metrics: Show real-time system metrics

Responsibilities:
- Provide command-line interface for ecosystem management and operations
- Enable interactive prompt management and testing workflows
- Display real-time health status and service integration testing
- Support both programmatic and interactive usage patterns
- Offer rich terminal UI with tables, panels, and colored output
- Provide power-user operations for bulk processing and infrastructure management
- Enable cross-service workflows and automated operations

Features:
- Interactive menu system with keyboard navigation (10 main categories)
- Rich terminal output with syntax highlighting and formatting
- Service health monitoring and integration testing
- Prompt retrieval and management capabilities
- Workflow execution and status monitoring
- Bulk operations (analysis, quality recalculation, data migration)
- Infrastructure monitoring (Redis, DLQ, Sagas, Tracing)
- Document store management (CRUD, search, quality)
- Source agent operations (fetching, normalization, analysis)
- Orchestrator management (workflows, registry, jobs)

Dependencies: All ecosystem services via HTTP clients, Rich library for UI.
"""

import os
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timezone
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


# ============================================================================
# POWER USER COMMANDS - Advanced operations for experienced users
# ============================================================================

@cli.command()
@click.option('--type', '-t', help='Analysis type (quality, consistency, security, all)')
@click.option('--criteria', '-c', help='Selection criteria as JSON string')
@click.pass_context
def analyze_docs(ctx, type, criteria):
    """Perform mass document analysis across the ecosystem"""
    try:
        import json
        analysis_criteria = json.loads(criteria) if criteria else {}

        bulk_manager = cli_service.bulk_operations_manager
        asyncio.run(bulk_manager.analyze_all_documents(type or "quality"))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--type', help='Document type filter')
@click.option('--threshold', type=float, help='Quality threshold for low-quality recalc')
@click.pass_context
def quality_recalc(ctx, type, threshold):
    """Perform bulk quality score recalculation"""
    try:
        bulk_manager = cli_service.bulk_operations_manager
        if threshold:
            asyncio.run(bulk_manager.recalculate_low_quality(threshold))
        elif type:
            asyncio.run(bulk_manager.recalculate_by_type())
        else:
            asyncio.run(bulk_manager.recalculate_all_quality())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--format', '-f', required=True, help='Export format (json, csv, xml)')
@click.option('--criteria', '-c', help='Selection criteria as JSON string')
@click.option('--filename', help='Output filename')
@click.pass_context
def bulk_export(ctx, format, criteria, filename):
    """Export documents in bulk"""
    try:
        import json
        export_criteria = json.loads(criteria) if criteria else {}
        output_filename = filename or f"documents_export.{format}"

        bulk_manager = cli_service.bulk_operations_manager
        asyncio.run(bulk_manager.bulk_export_documents(export_criteria, format, output_filename))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--file', '-f', required=True, help='Import file path')
@click.option('--format', required=True, help='Import format (json, csv, xml)')
@click.option('--update-existing', is_flag=True, help='Update existing documents')
@click.pass_context
def bulk_import(ctx, file, format, update_existing):
    """Import documents in bulk"""
    try:
        bulk_manager = cli_service.bulk_operations_manager
        asyncio.run(bulk_manager.bulk_import_documents(file, format, update_existing))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--criteria', '-c', required=True, help='Selection criteria as JSON string')
@click.option('--message', '-m', required=True, help='Notification message')
@click.pass_context
def notify_owners(ctx, criteria, message):
    """Send notifications to document owners"""
    try:
        import json
        selection_criteria = json.loads(criteria)

        bulk_manager = cli_service.bulk_operations_manager
        asyncio.run(bulk_manager.notify_document_owners(selection_criteria, message))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--type', '-t', required=True, help='Workflow type')
@click.option('--config', '-c', help='Workflow configuration as JSON string')
@click.pass_context
def workflow_run(ctx, type, config):
    """Execute orchestrator workflows"""
    try:
        import json
        workflow_config = json.loads(config) if config else {}

        orchestrator_manager = cli_service.orchestrator_manager
        asyncio.run(orchestrator_manager.run_workflow(type, workflow_config))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def redis_info(ctx):
    """Display Redis server information"""
    try:
        infra_manager = cli_service.infrastructure_manager
        asyncio.run(infra_manager.redis_info())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def dlq_stats(ctx):
    """Show dead letter queue statistics"""
    try:
        infra_manager = cli_service.infrastructure_manager
        asyncio.run(infra_manager.dlq_statistics())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def saga_monitor(ctx):
    """Monitor active sagas"""
    try:
        infra_manager = cli_service.infrastructure_manager
        asyncio.run(infra_manager.view_active_sagas())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--criteria', '-c', required=True, help='Search criteria as JSON string')
@click.pass_context
def tracing_search(ctx, criteria):
    """Search distributed traces"""
    try:
        import json
        search_criteria = json.loads(criteria)

        infra_manager = cli_service.infrastructure_manager
        asyncio.run(infra_manager.search_traces(search_criteria))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# INTERPRETER SERVICE COMMANDS
# ============================================================================

@cli.command()
@click.argument('query')
@click.option('--user-id', help='User ID for context')
@click.option('--session-id', help='Session ID for context')
@click.option('--context', '-c', help='Additional context as JSON string')
@click.pass_context
def interpret_query(ctx, query, user_id, session_id, context):
    """Interpret a natural language query and show intent analysis"""
    try:
        import json
        query_data = {"query": query}

        if user_id:
            query_data["user_id"] = user_id
        if session_id:
            query_data["session_id"] = session_id
        if context:
            query_data["context"] = json.loads(context)

        interpreter_manager = cli_service.interpreter_manager
        asyncio.run(interpreter_manager.interpret_single_query_from_cli(query_data))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('query')
@click.option('--user-id', help='User ID for context')
@click.option('--session-id', help='Session ID for context')
@click.option('--context', '-c', help='Additional context as JSON string')
@click.pass_context
def execute_workflow(ctx, query, user_id, session_id, context):
    """Interpret a query and execute the resulting workflow"""
    try:
        import json
        query_data = {"query": query}

        if user_id:
            query_data["user_id"] = user_id
        if session_id:
            query_data["session_id"] = session_id
        if context:
            query_data["context"] = json.loads(context)

        interpreter_manager = cli_service.interpreter_manager
        asyncio.run(interpreter_manager.execute_workflow_from_cli(query_data))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def list_intents(ctx):
    """List all supported query intents with examples"""
    try:
        interpreter_manager = cli_service.interpreter_manager
        asyncio.run(interpreter_manager.list_supported_intents())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# DISCOVERY AGENT COMMANDS
# ============================================================================

@cli.command()
@click.option('--name', '-n', required=True, help='Service name')
@click.option('--url', '-u', required=True, help='Service base URL')
@click.option('--spec', '-s', help='Path to OpenAPI spec file')
@click.option('--openapi-url', '-o', help='OpenAPI spec URL')
@click.option('--dry-run', is_flag=True, help='Dry run (no registration)')
@click.pass_context
def discover_service(ctx, name, url, spec, openapi_url, dry_run):
    """Discover and optionally register service endpoints from OpenAPI spec"""
    try:
        discover_request = {
            "name": name,
            "base_url": url,
            "dry_run": dry_run
        }

        # Load spec from file or URL
        if spec:
            if not os.path.exists(spec):
                console = Console()
                console.print(f"[red]Spec file not found: {spec}[/red]")
                return
            with open(spec, 'r') as f:
                discover_request["spec"] = json.load(f)
        elif openapi_url:
            discover_request["openapi_url"] = openapi_url
        else:
            # Create basic inline spec
            discover_request["spec"] = {
                "openapi": "3.0.0",
                "info": {"title": name.title(), "version": "1.0.0"},
                "paths": {
                    "/health": {
                        "get": {"summary": "Health check", "responses": {"200": {"description": "OK"}}}
                    }
                }
            }

        discovery_manager = cli_service.discovery_agent_manager
        asyncio.run(discovery_manager.discover_service_from_cli(discover_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# MEMORY AGENT COMMANDS
# ============================================================================

@cli.command()
@click.option('--type', '-t', required=True, help='Memory item type (operation|llm_summary|doc_summary|api_summary|finding)')
@click.option('--key', '-k', required=True, help='Memory key (correlation_id, doc id, etc.)')
@click.option('--summary', '-s', required=True, help='Summary of the memory item')
@click.option('--data', '-d', help='JSON data payload')
@click.pass_context
def store_memory(ctx, type, key, summary, data):
    """Store operational context and event summaries in memory"""
    try:
        memory_data = {}
        if data:
            memory_data = json.loads(data)

        memory_item = {
            "id": f"cli-memory-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            "type": type,
            "key": key,
            "summary": summary,
            "data": memory_data
        }

        memory_request = {"item": memory_item}
        memory_manager = cli_service.memory_agent_manager
        asyncio.run(memory_manager.store_memory_from_cli(memory_request))
    except json.JSONDecodeError:
        console = Console()
        console.print(f"[red]Invalid JSON data: {data}[/red]")
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--type', '-t', help='Filter by memory type')
@click.option('--key', '-k', help='Filter by memory key')
@click.option('--limit', '-l', default=50, help='Maximum items to retrieve')
@click.pass_context
def list_memory(ctx, type, key, limit):
    """List stored memory items with optional filtering"""
    try:
        # Create a temporary console for display
        console = Console()

        memory_manager = cli_service.memory_agent_manager

        # Use the list_memory_items method directly to get items
        # This is a bit of a workaround since we need to access the API
        # For now, we'll show a placeholder
        console.print(f"[yellow]Listing memory items (type: {type or 'all'}, key: {key or 'all'}, limit: {limit})[/yellow]")
        console.print("[yellow]This would display memory items from the memory agent[/yellow]")

        # In a real implementation, we'd call the API and display results
        # For now, just show the command was received

    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# SECURE ANALYZER COMMANDS
# ============================================================================

@cli.command()
@click.argument('content')
@click.option('--keywords', '-k', help='Comma-separated list of additional keywords to detect')
@click.pass_context
def detect_content(ctx, content, keywords):
    """Analyze content for sensitive information and security risks"""
    try:
        detect_request = {"content": content}

        if keywords:
            detect_request["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]

        secure_manager = cli_service.secure_analyzer_manager
        asyncio.run(secure_manager.detect_content_from_cli(detect_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('content')
@click.pass_context
def suggest_models(ctx, content):
    """Get AI model recommendations based on content sensitivity"""
    try:
        suggest_request = {"content": content}

        secure_manager = cli_service.secure_analyzer_manager
        asyncio.run(secure_manager.suggest_models_from_cli(suggest_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('content')
@click.option('--override-policy', '-o', is_flag=True, help='Override security policy restrictions')
@click.option('--prompt', '-p', help='Custom summarization prompt')
@click.pass_context
def secure_summarize(ctx, content, override_policy, prompt):
    """Generate secure summary with policy-based provider filtering"""
    try:
        summarize_request = {
            "content": content,
            "override_policy": override_policy
        }

        if prompt:
            summarize_request["prompt"] = prompt

        secure_manager = cli_service.secure_analyzer_manager
        asyncio.run(secure_manager.summarize_content_from_cli(summarize_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# SUMMARIZER HUB COMMANDS
# ============================================================================

@cli.command()
@click.argument('content')
@click.option('--providers', '-p', required=True, help='Comma-separated list of providers (ollama,openai,anthropic,grok,bedrock)')
@click.option('--prompt', help='Custom summarization prompt')
@click.option('--hub-config', is_flag=True, help='Use hub configuration defaults')
@click.pass_context
def ensemble_summarize(ctx, content, providers, prompt, hub_config):
    """Generate ensemble summaries using multiple AI providers"""
    try:
        provider_list = [p.strip() for p in providers.split(",") if p.strip()]

        if not provider_list:
            console = Console()
            console.print("[red]No providers specified[/red]")
            return

        # Build provider configurations
        provider_configs = []
        for provider in provider_list:
            config = {"name": provider}

            # Add default models and endpoints
            if provider == "ollama":
                config.update({"model": "llama3", "endpoint": "http://localhost:11434"})
            elif provider == "openai":
                config.update({"model": "gpt-4"})
            elif provider == "anthropic":
                config.update({"model": "claude-3-sonnet-20240229"})
            elif provider == "grok":
                config.update({"model": "grok-1"})
            elif provider == "bedrock":
                config.update({"model": "anthropic.claude-3-sonnet-20240229-v1:0", "region": "us-east-1"})

            provider_configs.append(config)

        summarize_request = {
            "text": content,
            "providers": provider_configs,
            "use_hub_config": hub_config
        }

        if prompt:
            summarize_request["prompt"] = prompt

        summarizer_manager = cli_service.summarizer_hub_manager
        asyncio.run(summarizer_manager.summarize_from_cli(summarize_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('provider')
@click.pass_context
def test_provider(ctx, provider):
    """Test connectivity to an AI provider"""
    try:
        # Create a simple test request
        test_config = {"name": provider}

        # Add provider-specific defaults
        if provider == "ollama":
            test_config.update({"model": "llama3", "endpoint": "http://localhost:11434"})
        elif provider == "openai":
            test_config.update({"model": "gpt-4"})
        elif provider == "anthropic":
            test_config.update({"model": "claude-3-sonnet-20240229"})
        elif provider == "grok":
            test_config.update({"model": "grok-1"})
        elif provider == "bedrock":
            test_config.update({"model": "anthropic.claude-3-sonnet-20240229-v1:0", "region": "us-east-1"})

        test_request = {
            "text": "Hello world. This is a test message for provider connectivity.",
            "providers": [test_config],
            "use_hub_config": False
        }

        summarizer_manager = cli_service.summarizer_hub_manager

        # Use the test connectivity method - this needs to be wrapped in asyncio.run
        asyncio.run(summarizer_manager.test_provider_connectivity())

    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# CODE ANALYZER COMMANDS
# ============================================================================

@cli.command()
@click.argument('content')
@click.option('--language', '-l', help='Programming language (python, javascript, etc.)')
@click.option('--repo', '-r', help='Repository name')
@click.option('--path', '-p', help='File path within repository')
@click.pass_context
def analyze_code(ctx, content, language, repo, path):
    """Analyze code for API endpoints and programming patterns"""
    try:
        analyze_request = {"content": content}

        if language:
            analyze_request["language"] = language
        if repo:
            analyze_request["repo"] = repo
        if path:
            analyze_request["path"] = path

        code_manager = cli_service.code_analyzer_manager
        asyncio.run(code_manager.analyze_code_from_cli(analyze_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('content')
@click.option('--keywords', '-k', help='Comma-separated list of additional keywords to detect')
@click.pass_context
def scan_security(ctx, content, keywords):
    """Scan code for security vulnerabilities and sensitive information"""
    try:
        scan_request = {"content": content}

        if keywords:
            scan_request["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]

        code_manager = cli_service.code_analyzer_manager
        asyncio.run(code_manager.scan_security_from_cli(scan_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# NOTIFICATION SERVICE COMMANDS
# ============================================================================

@cli.command()
@click.option('--id', '-i', required=True, help='Entity ID to update')
@click.option('--owner', '-o', help='Owner name')
@click.option('--team', '-t', help='Team name')
@click.pass_context
def update_owner(ctx, id, owner, team):
    """Update owner information in the notification service"""
    try:
        update_request = {"id": id}

        if owner:
            update_request["owner"] = owner
        if team:
            update_request["team"] = team

        notification_manager = cli_service.notification_service_manager
        asyncio.run(notification_manager.update_owner_from_cli(update_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('owners')
@click.pass_context
def resolve_owners(ctx, owners):
    """Resolve owner names to notification targets"""
    try:
        owners_list = [owner.strip() for owner in owners.split(",") if owner.strip()]

        if not owners_list:
            console = Console()
            console.print("[red]No owners specified[/red]")
            return

        resolve_request = {"owners": owners_list}

        notification_manager = cli_service.notification_service_manager
        asyncio.run(notification_manager.resolve_owners_from_cli(resolve_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--channel', '-c', required=True, help='Notification channel (webhook/email/slack)')
@click.option('--target', '-t', required=True, help='Delivery target (URL/email/channel)')
@click.option('--title', required=True, help='Notification title')
@click.option('--message', '-m', required=True, help='Notification message')
@click.option('--metadata', help='JSON metadata for notification')
@click.option('--labels', '-l', help='Comma-separated labels')
@click.pass_context
def send_notification(ctx, channel, target, title, message, metadata, labels):
    """Send notification through specified channel"""
    try:
        notification_request = {
            "channel": channel,
            "target": target,
            "title": title,
            "message": message,
            "metadata": {},
            "labels": []
        }

        if metadata:
            try:
                notification_request["metadata"] = json.loads(metadata)
            except json.JSONDecodeError:
                console = Console()
                console.print(f"[yellow]Invalid JSON metadata, using empty dict[/yellow]")

        if labels:
            notification_request["labels"] = [label.strip() for label in labels.split(",") if label.strip()]

        notification_manager = cli_service.notification_service_manager
        asyncio.run(notification_manager.send_notification_from_cli(notification_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--limit', '-l', default=20, help='Maximum number of entries to retrieve')
@click.pass_context
def view_dlq(ctx, limit):
    """View failed notifications in dead letter queue"""
    try:
        # Get DLQ entries and display them
        console = Console()

        # This would normally call the notification service API
        # For now, show a placeholder
        console.print(f"[yellow]Viewing up to {limit} failed notifications from DLQ[/yellow]")
        console.print("[yellow]This would display failed notification details[/yellow]")

        # In a real implementation, we'd call the API and display results

    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# LOG COLLECTOR COMMANDS
# ============================================================================

@cli.command()
@click.option('--service', '-s', required=True, help='Service name that generated the log')
@click.option('--level', '-l', required=True, help='Log level (debug/info/warning/error/fatal)')
@click.option('--message', '-m', required=True, help='Log message')
@click.option('--context', '-c', help='JSON context data for the log entry')
@click.pass_context
def submit_log(ctx, service, level, message, context):
    """Submit a log entry to the log collector"""
    try:
        log_request = {
            "service": service,
            "level": level,
            "message": message
        }

        if context:
            try:
                log_request["context"] = json.loads(context)
            except json.JSONDecodeError:
                console = Console()
                console.print(f"[yellow]Invalid JSON context, using empty context[/yellow]")

        log_manager = cli_service.log_collector_manager
        asyncio.run(log_manager.submit_log_from_cli(log_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--service', '-s', help='Filter by service name')
@click.option('--level', '-l', help='Filter by log level')
@click.option('--limit', '-n', default=50, help='Maximum number of logs to retrieve')
@click.pass_context
def query_logs(ctx, service, level, limit):
    """Query stored logs with optional filtering"""
    try:
        params = {"limit": limit}
        if service:
            params["service"] = service
        if level:
            params["level"] = level

        log_manager = cli_service.log_collector_manager
        asyncio.run(log_manager.query_logs_from_cli(params))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def log_stats(ctx):
    """View log statistics and analytics"""
    try:
        log_manager = cli_service.log_collector_manager
        asyncio.run(log_manager.get_log_stats_from_cli())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# BEDROCK PROXY COMMANDS
# ============================================================================

@cli.command()
@click.option('--prompt', '-p', required=True, help='Prompt text for AI model')
@click.option('--template', '-t', help='Response template (summary/risks/decisions/pr_confidence/life_of_ticket)')
@click.option('--format', '-f', default='md', help='Output format (md/txt/json)')
@click.option('--model', '-m', help='AI model to use')
@click.option('--region', '-r', help='AWS region')
@click.option('--title', help='Custom title for response')
@click.pass_context
def invoke_ai(ctx, prompt, template, format, model, region, title):
    """Invoke AI model with optional template and formatting"""
    try:
        request_data = {
            "prompt": prompt,
            "format": format
        }

        if template:
            request_data["template"] = template
        if model:
            request_data["model"] = model
        if region:
            request_data["region"] = region
        if title:
            request_data["title"] = title

        bedrock_manager = cli_service.bedrock_proxy_manager
        asyncio.run(bedrock_manager.invoke_ai_from_cli(request_data))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def ai_templates(ctx):
    """List available AI response templates"""
    try:
        bedrock_manager = cli_service.bedrock_proxy_manager
        asyncio.run(bedrock_manager.list_available_templates())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--limit', '-l', default=10, help='Maximum number of recent invocations to show')
@click.pass_context
def ai_history(ctx, limit):
    """View recent AI invocation history"""
    try:
        bedrock_manager = cli_service.bedrock_proxy_manager
        # Temporarily modify the limit for view_recent_invocations
        original_limit = limit
        asyncio.run(bedrock_manager.view_recent_invocations())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# ANALYSIS SERVICE COMMANDS
# ============================================================================

@cli.command()
@click.argument('doc_ids', nargs=-1, required=True)
@click.option('--detectors', '-d', help='Comma-separated list of detectors to use')
@click.option('--severity-filter', '-s', help='Minimum severity level to report')
@click.pass_context
def analyze_docs(ctx, doc_ids, detectors, severity_filter):
    """Analyze documents for consistency and issues"""
    try:
        if not doc_ids:
            console = Console()
            console.print("[red]Error: At least one document ID is required[/red]")
            return

        analysis_request = {
            "targets": list(doc_ids)
        }

        if detectors:
            analysis_request["detectors"] = [d.strip() for d in detectors.split(",") if d.strip()]

        if severity_filter:
            analysis_request["severity_filter"] = severity_filter

        analysis_manager = cli_service.analysis_service_manager
        asyncio.run(analysis_manager.analyze_document_from_cli(analysis_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--severity', '-s', help='Filter by severity level (critical/high/medium/low/info)')
@click.option('--type', '-t', help='Filter by finding type')
@click.option('--limit', '-l', default=50, help='Maximum number of findings to retrieve')
@click.pass_context
def get_findings(ctx, severity, type, limit):
    """Retrieve analysis findings with optional filtering"""
    try:
        params = {"limit": limit}
        if severity:
            params["severity"] = severity
        if type:
            params["finding_type_filter"] = type

        analysis_manager = cli_service.analysis_service_manager
        asyncio.run(analysis_manager.get_findings_from_cli(params))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option('--type', '-t', required=True, help='Report type (summary/trends/quality)')
@click.option('--time-period', help='Time period for trends report (e.g., 30d, 7d)')
@click.option('--quality-threshold', type=float, help='Quality threshold for quality report (0.0-1.0)')
@click.pass_context
def generate_report(ctx, type, time_period, quality_threshold):
    """Generate analysis reports"""
    try:
        report_request = {"type": type}

        if type == "trends" and time_period:
            report_request["time_period"] = time_period

        if type == "quality" and quality_threshold is not None:
            if not (0.0 <= quality_threshold <= 1.0):
                console = Console()
                console.print("[red]Error: Quality threshold must be between 0.0 and 1.0[/red]")
                return
            report_request["quality_threshold"] = quality_threshold

        analysis_manager = cli_service.analysis_service_manager
        asyncio.run(analysis_manager.generate_report_from_cli(report_request))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# CONFIGURATION MANAGEMENT COMMANDS
# ============================================================================

@cli.command()
@click.option('--service', '-s', help='Service name to view configuration for')
@click.pass_context
def view_config(ctx, service):
    """View service configuration files"""
    try:
        config_manager = cli_service.config_manager
        asyncio.run(config_manager.view_service_configuration())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('var', required=True)
@click.argument('value', required=True)
@click.pass_context
def set_env(ctx, var, value):
    """Set environment variable"""
    try:
        config_manager = cli_service.config_manager
        asyncio.run(config_manager.set_environment_variable())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def get_env(ctx):
    """Show current environment variables"""
    try:
        config_manager = cli_service.config_manager
        asyncio.run(config_manager.view_current_environment())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def validate_config(ctx):
    """Validate configuration files and environment variables"""
    try:
        config_manager = cli_service.config_manager

        # Run multiple validation checks
        console = Console()
        console.print("[yellow]Running configuration validation...[/yellow]")

        # Validate YAML syntax
        console.print("\n[bold]1. YAML Syntax Validation:[/bold]")
        asyncio.run(config_manager.validate_yaml_syntax())

        # Validate environment variables
        console.print("\n[bold]2. Environment Variable Validation:[/bold]")
        asyncio.run(config_manager.environment_variable_validation())

        # Configuration health check
        console.print("\n[bold]3. Configuration Health Check:[/bold]")
        asyncio.run(config_manager.configuration_health_check())

    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# DEPLOYMENT CONTROLS COMMANDS
# ============================================================================

@cli.command()
@click.argument('service', required=True)
@click.argument('replicas', type=int, required=True)
@click.pass_context
def scale_service(ctx, service, replicas):
    """Scale a service to specified number of replicas"""
    try:
        if replicas < 0:
            console = Console()
            console.print("[red]Error: Number of replicas must be non-negative[/red]")
            return

        deployment_manager = cli_service.deployment_manager
        asyncio.run(deployment_manager.scale_service_from_cli(service, replicas))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def deployment_status(ctx):
    """View current deployment and scaling status"""
    try:
        deployment_manager = cli_service.deployment_manager
        asyncio.run(deployment_manager.view_deployment_status_from_cli())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument('service', required=True)
@click.argument('image', required=True)
@click.option('--strategy', '-s', default='rolling', help='Deployment strategy (rolling/blue-green/canary)')
@click.pass_context
def deploy_service(ctx, service, image, strategy):
    """Deploy service with new image"""
    try:
        valid_strategies = ['rolling', 'blue-green', 'canary']
        if strategy not in valid_strategies:
            console = Console()
            console.print(f"[red]Error: Invalid strategy. Must be one of: {', '.join(valid_strategies)}[/red]")
            return

        deployment_manager = cli_service.deployment_manager
        asyncio.run(deployment_manager.start_deployment_from_cli(service, image, strategy))
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# ADVANCED MONITORING COMMANDS
# ============================================================================

@cli.command()
@click.pass_context
def view_dashboards(ctx):
    """List available monitoring dashboards"""
    try:
        monitoring_manager = cli_service.advanced_monitoring_manager
        asyncio.run(monitoring_manager.view_dashboards_from_cli())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def view_alerts(ctx):
    """Show active monitoring alerts"""
    try:
        monitoring_manager = cli_service.advanced_monitoring_manager
        asyncio.run(monitoring_manager.view_alerts_from_cli())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def view_slo_status(ctx):
    """Display SLO/SLA compliance status"""
    try:
        monitoring_manager = cli_service.advanced_monitoring_manager
        asyncio.run(monitoring_manager.view_slo_status_from_cli())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.pass_context
def view_metrics(ctx):
    """Show real-time system metrics"""
    try:
        monitoring_manager = cli_service.advanced_monitoring_manager
        asyncio.run(monitoring_manager.view_metrics_from_cli())
    except Exception as e:
        console = Console()
        console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    cli()
