"""Service: Frontend

Endpoints (HTML):
- GET /: Main dashboard with navigation to all UI pages
- GET /findings: Findings page with all current findings from Consistency Engine
- GET /report: Comprehensive report page with all metrics and visualizations
- GET /findings/by-severity: Findings grouped by severity level
- GET /findings/by-type: Findings grouped by type
- GET /search: Search results page for document queries
- GET /docs/quality: Document quality analysis page with metrics
- GET /confluence/consolidation: Confluence consolidation report page
- GET /topics: Topic collections with document freshness analysis
- GET /owner-coverage: Owner coverage report with team statistics
- GET /reports/jira/staleness: Jira staleness report with filtering options
- GET /duplicates/clusters: Duplicate clusters report page
- GET /workflows/status: Workflow and job status monitoring dashboard
- GET /doc_store/browser: Doc-store data browser for document exploration
- GET /prompt-store/browser: Prompt-store data browser for prompt exploration
- GET /code-analyzer/dashboard: Code analyzer service dashboard
- GET /bedrock-proxy/dashboard: Bedrock proxy service dashboard
- GET /discovery-agent/dashboard: Discovery agent service dashboard
- GET /github-mcp/dashboard: GitHub MCP service dashboard
- GET /interpreter/dashboard: Interpreter service dashboard
- GET /memory-agent/dashboard: Memory agent service dashboard
- GET /notification-service/dashboard: Notification service dashboard
- GET /secure-analyzer/dashboard: Secure analyzer service dashboard
- GET /source-agent/dashboard: Source agent service dashboard
- GET /services/overview: Services overview dashboard
- GET /cli/terminal: CLI terminal interface

Endpoints (API):
- GET /api/workflows/jobs/status: Active workflows and jobs status for visualization
- GET /api/code-analyzer/status: Get comprehensive code analyzer service status
- POST /api/code-analyzer/analyze-text: Analyze text content for code quality and issues
- POST /api/code-analyzer/analyze-files: Analyze multiple files for code quality and issues
- POST /api/code-analyzer/security-scan: Perform security scan on code
- POST /api/code-analyzer/style-check: Check code style compliance
- GET /api/code-analyzer/style-examples: Get code style examples
- GET /api/code-analyzer/history: Get code analyzer analysis history
- GET /api/bedrock-proxy/status: Get comprehensive bedrock proxy service status
- POST /api/bedrock-proxy/invoke: Invoke AI through bedrock proxy and cache results
- GET /api/bedrock-proxy/history: Get bedrock proxy invocation history
- GET /api/discovery-agent/status: Get comprehensive discovery agent service status
- POST /api/discovery-agent/discover: Trigger endpoint discovery for services
- GET /api/discovery-agent/history: Get discovery agent operation history
- GET /api/github-mcp/status: Get comprehensive GitHub MCP service status
- GET /api/github-mcp/tools: Get available GitHub MCP tools
- POST /api/github-mcp/invoke: Invoke GitHub MCP tools and cache results
- GET /api/github-mcp/history: Get GitHub MCP tool invocation history
- GET /api/interpreter/status: Get comprehensive interpreter service status
- GET /api/interpreter/intents: Get supported intents and examples
- POST /api/interpreter/interpret: Interpret natural language queries
- POST /api/interpreter/execute: Interpret and execute workflows
- GET /api/interpreter/interpretations: Get interpretation history
- GET /api/interpreter/executions: Get workflow execution history
- GET /api/memory-agent/status: Get comprehensive memory agent service status
- GET /api/memory-agent/items: Get memory items with filtering
- POST /api/memory-agent/store: Store memory items
- GET /api/memory-agent/history: Get memory item history
- GET /api/notification-service/status: Get comprehensive notification service status
- GET /api/notification-service/dlq: Get dead letter queue entries
- POST /api/notification-service/resolve-owners: Resolve owners to notification targets
- POST /api/notification-service/send: Send test notifications
- GET /api/notification-service/notifications: Get notification delivery history
- GET /api/notification-service/resolutions: Get owner resolution history
- GET /api/secure-analyzer/status: Get comprehensive secure analyzer service status
- POST /api/secure-analyzer/detect: Detect sensitive content in text
- POST /api/secure-analyzer/suggest: Get model suggestions based on content sensitivity
- POST /api/secure-analyzer/summarize: Generate secure summaries with policy enforcement
- GET /api/secure-analyzer/detections: Get content detection history
- GET /api/secure-analyzer/suggestions: Get model suggestion history
- GET /api/secure-analyzer/summaries: Get secure summary history
- GET /api/source-agent/status: Get comprehensive source agent service status
- POST /api/source-agent/fetch: Fetch documents from sources
- POST /api/source-agent/normalize: Normalize data from sources
- POST /api/source-agent/analyze: Analyze code for endpoints and patterns
- GET /api/source-agent/fetches: Get document fetch history
- GET /api/source-agent/normalizations: Get data normalization history
- GET /api/source-agent/analyses: Get code analysis history
- GET /api/services/overview: Get comprehensive services overview
- GET /api/services/overview/{service_name}: Get detailed service health information
- GET /api/cli/status: Get CLI service health status
- POST /api/cli/execute: Execute CLI commands
- GET /api/cli/commands: Get available CLI commands
- GET /api/cli/history: Get CLI command execution history
- POST /api/cli/history/clear: Clear CLI command history
- GET /api/cli/prompts: Get prompts via CLI interface
- GET /api/cli/prompts/{category}/{name}: Get specific prompt details via CLI
- POST /api/cli/test-integration: Run CLI integration tests

Responsibilities:
- Provide HTML UI for viewing documentation consistency findings and reports
- Aggregate data from multiple backend services (Reporting, Consistency Engine, Doc Store, Orchestrator, Log Collector, Prompt Store, Analysis Service, Code Analyzer, Bedrock Proxy, Discovery Agent, GitHub MCP, Interpreter, Memory Agent, Notification Service, Secure Analyzer, Source Agent, CLI Service)
- Render interactive dashboards for document quality metrics and analysis
- Support filtering and searching across documentation collections
- Display owner coverage and staleness reports for Jira tickets
- Show topic collections and duplicate document clusters
- Provide API endpoints for workflow and job monitoring and visualization
- Enable read-only browsing and exploration of stored documents and prompts
- Support data discovery through search, filtering, and pagination interfaces
- Enable code analysis, security scanning, and style checking capabilities
- Provide interactive code quality assessment and vulnerability detection
- Monitor AI invocations and template usage through bedrock proxy service
- Support interactive testing and caching of AI responses for development
- Monitor OpenAPI endpoint discovery and service registration operations
- Support interactive endpoint discovery and orchestrator registration
- Monitor GitHub MCP tool invocations and GitHub data operations
- Support interactive tool testing and MCP service configuration
- Monitor natural language query interpretation and workflow generation
- Support interactive query testing and intent recognition validation
- Monitor operational context and event summary storage
- Support memory item browsing and interactive storage testing
- Monitor owner resolution and notification delivery operations
- Support notification testing and DLQ monitoring
- Monitor content security analysis and policy enforcement
- Support secure content detection and model recommendation testing
- Monitor document fetching, normalization, and code analysis operations
- Support source integration testing across GitHub, Jira, and Confluence
- Provide comprehensive system-wide monitoring and health dashboard
- Aggregate service status across all ecosystem components
- Provide web-based terminal interface for full CLI service functionality
- Enable command execution, history tracking, and interactive CLI operations

Dependencies: Reporting, Consistency Engine, Doc Store, Orchestrator, Log Collector, Prompt Store, Analysis Service, Code Analyzer, Bedrock Proxy, Discovery Agent, GitHub MCP, Interpreter, Memory Agent, Notification Service, Secure Analyzer, Source Agent, CLI Service; shared render helpers.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import os

# ============================================================================
# SHARED MODULES - Leveraging centralized functionality for consistency
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints
from services.shared.core.constants_new import ServiceNames, EnvVars
from services.shared.utilities import setup_common_middleware
from services.shared.utilities.error_handling import install_error_handlers

# ============================================================================
# LOCAL MODULES - Service-specific functionality
# ============================================================================
from services.frontend.modules.shared_utils import (
    get_reporting_url,
    get_doc_store_url,
    get_consistency_engine_url,
    get_orchestrator_url,
    get_summarizer_hub_url,
    get_frontend_clients,
    create_html_response,
    handle_frontend_error,
    create_frontend_success_response,
    build_frontend_context,
    fetch_service_data,
    get_service_url,
    validate_frontend_request,
    sanitize_input
)

# ============================================================================
# UI HANDLERS - Extracted page rendering logic
# ============================================================================
from services.frontend.modules.ui_handlers import ui_handlers
from services.frontend.modules.summarizer_cache import get_cached_summarizer_data, record_summarizer_job
from services.frontend.modules.log_cache import (
    get_cached_logs_data,
    fetch_logs_from_collector,
    fetch_log_stats_from_collector,
    stream_logs,
    analyze_log_patterns
)
from services.frontend.modules.data_browser import (
    data_browser,
    get_doc_store_summary,
    get_prompt_store_summary
)
from services.frontend.modules.orchestrator_monitor import (
    orchestrator_monitor,
    get_orchestrator_summary
)
from services.frontend.modules.analysis_monitor import analysis_monitor
from services.frontend.modules.bedrock_proxy_monitor import bedrock_proxy_monitor
from services.frontend.modules.code_analyzer_monitor import code_analyzer_monitor

# ============================================================================
# RENDER UTILITIES - HTML rendering functions
# ============================================================================
from services.frontend.utils import (
    render_index,
    render_owner_coverage_table,
    render_topics_html,
    render_consolidation_list,
    render_search_results,
    render_docs_quality,
    render_findings,
    render_counts,
    render_report_page,
    render_clusters,
)

# Service configuration constants
SERVICE_NAME = "frontend"
SERVICE_TITLE = "Frontend"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 3000

# ============================================================================
# APP INITIALIZATION - Using shared patterns for consistency
# ============================================================================

# Initialize FastAPI app with shared middleware and error handlers
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="HTML UI service for documentation consistency analysis and reporting"
)

static_dir = os.path.join(os.path.dirname(__file__), "static")

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.FRONTEND)
install_error_handlers(app)

# Register standardized health endpoints
register_health_endpoints(app, ServiceNames.FRONTEND, SERVICE_VERSION)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/info")
async def info():
    """Get service information and configuration.

    Returns detailed service metadata including version, configuration URLs,
    and environment settings for connected services.
    """
    try:
        return create_frontend_success_response(
            "info retrieved",
            {
                "service": ServiceNames.FRONTEND,
                "version": app.version,
                "env": {
                    "REPORTING_URL": get_reporting_url(),
                    "DOC_STORE_URL": get_doc_store_url(),
                    "CONSISTENCY_ENGINE_URL": get_consistency_engine_url(),
                    "ORCHESTRATOR_URL": get_orchestrator_url(),
                    "SUMMARIZER_HUB_URL": get_summarizer_hub_url(),
                    "LOG_COLLECTOR_URL": get_log_collector_url(),
                    "PROMPT_STORE_URL": get_prompt_store_url(),
                    "ANALYSIS_SERVICE_URL": get_analysis_service_url(),
                },
            },
            **build_frontend_context("get_info")
        )
    except Exception as e:
        return handle_frontend_error("get service info", e, **build_frontend_context("get_info"))


@app.get("/config/effective")
async def config_effective():
    """Get effective configuration from environment.

    Returns the resolved configuration values for all dependent services
    (Reporting, Doc Store, Consistency Engine) as determined from environment
    variables or configuration files.
    """
    try:
        config = {
            EnvVars.REPORTING_URL_ENV: get_reporting_url(),
            EnvVars.DOC_STORE_URL_ENV: get_doc_store_url(),
            EnvVars.CONSISTENCY_ENGINE_URL_ENV: get_consistency_engine_url(),
            EnvVars.ORCHESTRATOR_URL_ENV: get_orchestrator_url(),
            EnvVars.SUMMARIZER_HUB_URL_ENV: get_summarizer_hub_url(),
            EnvVars.LOG_COLLECTOR_URL_ENV: get_log_collector_url(),
            EnvVars.PROMPT_STORE_URL_ENV: get_prompt_store_url(),
            EnvVars.ANALYSIS_SERVICE_URL_ENV: get_analysis_service_url(),
        }
        return create_frontend_success_response(
            "config retrieved",
            config,
            **build_frontend_context("get_config")
        )
    except Exception as e:
        return handle_frontend_error("get effective config", e, **build_frontend_context("get_config"))


@app.get("/metrics")
async def metrics():
    """Get frontend service metrics.

    Returns basic service metrics including the number of registered routes
    and service status information for monitoring purposes.
    """
    try:
        return create_frontend_success_response(
            "metrics retrieved",
            {"service": ServiceNames.FRONTEND, "routes": len(app.routes)},
            **build_frontend_context("get_metrics")
        )
    except Exception as e:
        return handle_frontend_error("get metrics", e, **build_frontend_context("get_metrics"))


@app.get("/app/{path:path}")
async def spa_catch_all(path: str):
    print("SPA catch-all route called")
    """Catch-all route for Elm SPA routing.

    Serves index.html for any route under /app so that Elm can handle
    client-side routing for the single-page application.
    """
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/owner-coverage")
async def ui_owner_coverage():
    """Render owner coverage report page.

    Displays a table showing owner coverage statistics by team,
    including percentages for missing owners and low-view documents.
    """
    return ui_handlers.handle_owner_coverage()


@app.get("/topics")
async def ui_topics():
    """Render topics overview page with document freshness analysis.

    Shows topic collections with associated documents and their
    freshness metrics for content management insights.
    """
    return ui_handlers.handle_topics()


@app.get("/confluence/consolidation")
async def ui_confluence_consolidation():
    """Render Confluence consolidation report page.

    Displays consolidation recommendations for Confluence pages
    to reduce duplication and improve content organization.
    """
    return ui_handlers.handle_confluence_consolidation()


@app.get("/reports/jira/staleness")
async def ui_jira_staleness(min_confidence: float = 0.0, min_duplicate_confidence: float = 0.0, limit: int = 50, summarize: bool = False):
    """Render Jira staleness report page with filtering options.

    Shows stale Jira tickets with configurable confidence thresholds.
    Supports filtering by duplicate confidence and result limits.
    """
    return ui_handlers.handle_jira_staleness(min_confidence, min_duplicate_confidence, limit, summarize)


@app.get("/duplicates/clusters")
async def ui_duplicate_clusters():
    """Render duplicate clusters report page."""
    return ui_handlers.handle_duplicate_clusters()


@app.get("/search")
async def ui_search(q: str = "kubernetes"):
    """Render search results page for document queries."""
    return ui_handlers.handle_search(q)


@app.get("/docs/quality")
async def ui_docs_quality():
    """Render document quality analysis page."""
    return ui_handlers.handle_docs_quality()


@app.get("/findings")
async def ui_findings():
    """Render findings page with all current findings."""
    return ui_handlers.handle_findings()


@app.get("/findings/by-severity")
async def ui_findings_by_severity():
    """Render findings grouped by severity level."""
    return ui_handlers.handle_findings_by_severity()


@app.get("/findings/by-type")
async def ui_findings_by_type():
    """Render findings grouped by type."""
    return ui_handlers.handle_findings_by_type()


@app.get("/report")
async def ui_report():
    """Render comprehensive report page with all metrics."""
    return ui_handlers.handle_report()


@app.get("/workflows/status")
async def ui_workflows_status():
    """Render workflow and job status monitoring page.

    Provides a real-time dashboard for monitoring active workflows,
    job progress, and orchestrator performance metrics.
    """
    return ui_handlers.handle_workflows_status()


@app.get("/summarizer/status")
async def ui_summarizer_status():
    """Render summarizer hub status and process monitoring page.

    Provides a dashboard for monitoring summarizer hub jobs, prompts,
    model usage, and performance metrics.
    """
    return ui_handlers.handle_summarizer_status()


@app.get("/logs/dashboard")
async def ui_logs_dashboard():
    """Render logs dashboard for visualization and troubleshooting.

    Provides a comprehensive dashboard for viewing logs, statistics,
    and real-time log streaming for system monitoring and diagnostics.
    """
    return ui_handlers.handle_logs_dashboard()


@app.get("/doc_store/browser")
async def ui_doc_store_browser():
    """Render doc_store data browser for document exploration.

    Provides a read-only interface for browsing documents, analyses,
    quality metrics, and style examples stored in the doc_store.
    """
    return ui_handlers.handle_doc_store_browser()


@app.get("/prompt-store/browser")
async def ui_prompt_store_browser():
    """Render prompt-store data browser for prompt exploration.

    Provides a read-only interface for browsing prompts, analytics,
    and A/B testing results stored in the prompt-store.
    """
    return ui_handlers.handle_prompt_store_browser()


@app.get("/orchestrator/monitor")
async def ui_orchestrator_monitor():
    """Render orchestrator monitoring dashboard.

    Provides comprehensive monitoring of Redis pub/sub activity,
    service configuration, and workflow execution for the orchestrator.
    """
    return ui_handlers.handle_orchestrator_monitor()


@app.get("/analysis/dashboard")
async def ui_analysis_dashboard():
    """Render analysis service dashboard.

    Provides comprehensive visualization of analysis results, findings,
    and cross-service correlations for document quality assessment.
    """
    return ui_handlers.handle_analysis_dashboard()


@app.get("/services/overview")
async def ui_services_overview():
    """Render comprehensive services overview dashboard.

    Provides monitoring and visualization for all services in the ecosystem,
    showing their status, activity, and health across the distributed system.
    """
    return ui_handlers.handle_services_overview()


@app.get("/code-analyzer/dashboard")
async def ui_code_analyzer_dashboard():
    """Render code analyzer service dashboard.

    Provides code analysis, security scanning, and style checking capabilities
    with interactive forms and result visualization.
    """
    return ui_handlers.handle_code_analyzer_dashboard()


@app.get("/bedrock-proxy/dashboard")
async def ui_bedrock_proxy_dashboard():
    """Render bedrock proxy service dashboard.

    Provides AI invocation monitoring, template usage tracking, and
    interactive testing capabilities for the bedrock proxy service.
    """
    return ui_handlers.handle_bedrock_proxy_dashboard()


@app.get("/discovery-agent/dashboard")
async def ui_discovery_agent_dashboard():
    """Render discovery agent service dashboard.

    Provides endpoint discovery monitoring, OpenAPI parsing operations,
    and service registration capabilities for the discovery agent service.
    """
    return ui_handlers.handle_discovery_agent_dashboard()


@app.get("/github-mcp/dashboard")
async def ui_github_mcp_dashboard():
    """Render github-mcp service dashboard.

    Provides GitHub MCP tool monitoring, tool invocation testing,
    and GitHub operations tracking for the GitHub MCP service.
    """
    return ui_handlers.handle_github_mcp_dashboard()


@app.get("/interpreter/dashboard")
async def ui_interpreter_dashboard():
    """Render interpreter service dashboard.

    Provides natural language query interpretation monitoring,
    intent recognition testing, and workflow execution tracking.
    """
    return ui_handlers.handle_interpreter_dashboard()


@app.get("/memory-agent/dashboard")
async def ui_memory_agent_dashboard():
    """Render memory agent service dashboard.

    Provides operational context monitoring, event summary storage,
    and memory item management for the memory agent service.
    """
    return ui_handlers.handle_memory_agent_dashboard()


@app.get("/notification-service/dashboard")
async def ui_notification_service_dashboard():
    """Render notification service dashboard.

    Provides owner resolution monitoring, notification delivery tracking,
    and dead letter queue management for the notification service.
    """
    return ui_handlers.handle_notification_service_dashboard()


@app.get("/secure-analyzer/dashboard")
async def ui_secure_analyzer_dashboard():
    """Render secure analyzer service dashboard.

    Provides content security analysis, policy enforcement monitoring,
    and secure summarization testing for the secure analyzer service.
    """
    return ui_handlers.handle_secure_analyzer_dashboard()


@app.get("/source-agent/dashboard")
async def ui_source_agent_dashboard():
    """Render source agent service dashboard.

    Provides document fetching, data normalization, and code analysis
    monitoring across GitHub, Jira, and Confluence sources.
    """
    return ui_handlers.handle_source_agent_dashboard()


@app.get("/services/overview")
async def ui_services_overview():
    """Render comprehensive services overview dashboard.

    Provides system-wide monitoring and health status for all services
    in the LLM Documentation Ecosystem with categorized views.
    """
    return ui_handlers.handle_services_overview()


@app.get("/cli/terminal")
async def ui_cli_terminal():
    """Render CLI terminal interface.

    Provides a web-based terminal for full CLI service functionality,
    allowing users to execute commands and interact with the ecosystem.
    """
    return ui_handlers.handle_cli_terminal()


@app.get("/api/workflows/jobs/status")
async def get_workflows_jobs_status():
    """Get active workflows and jobs status for visualization.

    Polls the orchestrator service to retrieve information about:
    - Active workflows and their execution status
    - Running jobs and their progress
    - Saga transaction statistics
    - Workflow history and performance metrics

    Returns data suitable for frontend visualization dashboards.
    """
    try:
        clients = get_frontend_clients()
        orchestrator_url = get_orchestrator_url()

        # Collect data from multiple orchestrator endpoints
        status_data = {
            "timestamp": utc_now().isoformat(),
            "workflows": {},
            "jobs": {},
            "infrastructure": {},
            "performance": {}
        }

        # Get available workflows
        try:
            workflows_response = await clients.get_json(f"{orchestrator_url}/workflows")
            status_data["workflows"]["available"] = workflows_response.get("data", {})
        except Exception as e:
            status_data["workflows"]["available"] = {"error": str(e)}

        # Get workflow history
        try:
            history_response = await clients.get_json(f"{orchestrator_url}/workflows/history")
            status_data["workflows"]["history"] = history_response.get("items", [])
        except Exception as e:
            status_data["workflows"]["history"] = {"error": str(e)}

        # Get saga statistics (active transactions)
        try:
            saga_stats = await clients.get_json(f"{orchestrator_url}/infrastructure/saga/stats")
            status_data["infrastructure"]["saga_stats"] = saga_stats.get("data", {})
        except Exception as e:
            status_data["infrastructure"]["saga_stats"] = {"error": str(e)}

        # Get active sagas (if any)
        try:
            # This would typically poll for active saga IDs and get their status
            # For now, we'll just indicate the capability
            status_data["jobs"]["active_sagas"] = []
        except Exception as e:
            status_data["jobs"]["active_sagas"] = {"error": str(e)}

        # Get service registry information
        try:
            registry_response = await clients.get_json(f"{orchestrator_url}/registry")
            status_data["infrastructure"]["services"] = registry_response.get("services", [])
        except Exception as e:
            status_data["infrastructure"]["services"] = {"error": str(e)}

        # Get orchestrator metrics
        try:
            metrics_response = await clients.get_json(f"{orchestrator_url}/metrics")
            status_data["performance"]["orchestrator"] = metrics_response.get("data", {})
        except Exception as e:
            status_data["performance"]["orchestrator"] = {"error": str(e)}

        # Calculate derived status information
        status_data["summary"] = {
            "total_workflows_available": len(status_data["workflows"].get("available", {})),
            "active_workflows": len([w for w in status_data["workflows"].get("history", []) if w.get("status") in ["running", "pending"]]),
            "completed_workflows": len([w for w in status_data["workflows"].get("history", []) if w.get("status") == "completed"]),
            "failed_workflows": len([w for w in status_data["workflows"].get("history", []) if w.get("status") == "failed"]),
            "active_sagas": len(status_data["jobs"].get("active_sagas", [])),
            "total_services": len(status_data["infrastructure"].get("services", []))
        }

        return create_frontend_success_response(
            "workflow and job status retrieved",
            status_data,
            **build_frontend_context("get_workflows_jobs_status")
        )

    except Exception as e:
        return handle_frontend_error("get workflows/jobs status", e, **build_frontend_context("get_workflows_jobs_status"))


@app.get("/api/summarizer/status")
async def get_summarizer_status():
    """Get summarizer hub status, job history, and process information for visualization.

    Returns cached data about previous summarizer jobs, active prompts, model usage,
    and performance metrics for monitoring and visualization purposes.
    """
    try:
        # Get cached data
        cached_data = get_cached_summarizer_data()

        # Try to fetch live data from summarizer hub
        clients = get_frontend_clients()
        summarizer_url = get_summarizer_hub_url()

        live_data = {
            "service_status": {},
            "config": {}
        }

        # Get service health
        try:
            health_response = await clients.get_json(f"{summarizer_url}/health")
            live_data["service_status"] = health_response
        except Exception as e:
            live_data["service_status"] = {"error": str(e), "status": "unreachable"}

        # Combine cached and live data
        status_data = {
            "timestamp": utc_now().isoformat(),
            "cached_data": cached_data,
            "live_data": live_data,
            "summary": {
                "total_cached_jobs": len(cached_data.get("job_history", [])),
                "active_prompts": len(cached_data.get("active_prompts", [])),
                "models_tracked": len(cached_data.get("model_usage", [])),
                "service_healthy": live_data["service_status"].get("status") == "healthy"
            }
        }

        return create_frontend_success_response(
            "summarizer status retrieved",
            status_data,
            **build_frontend_context("get_summarizer_status")
        )

    except Exception as e:
        return handle_frontend_error("get summarizer status", e, **build_frontend_context("get_summarizer_status"))


@app.post("/api/summarizer/record-job")
async def record_summarizer_job_endpoint(job_data: dict):
    """Record a summarizer job for caching and visualization.

    This endpoint is called by the summarizer hub after job completion
    to cache job data for monitoring and visualization.
    """
    try:
        # Record the job in cache
        record_summarizer_job(
            job_id=job_data.get("job_id", f"job_{utc_now().isoformat()}"),
            text_length=job_data.get("text_length", 0),
            providers=job_data.get("providers", []),
            models=job_data.get("models", {}),
            prompt=job_data.get("prompt"),
            execution_time=job_data.get("execution_time"),
            results=job_data.get("results"),
            consistency_analysis=job_data.get("consistency_analysis")
        )

        return create_frontend_success_response(
            "job recorded successfully",
            {"job_id": job_data.get("job_id")},
            **build_frontend_context("record_summarizer_job")
        )

    except Exception as e:
        return handle_frontend_error("record summarizer job", e, **build_frontend_context("record_summarizer_job"))


@app.get("/api/logs/status")
async def get_logs_status():
    """Get comprehensive log status and cached data for visualization.

    Returns cached logs, statistics, and analytics data from the log collector
    service for dashboard visualization and troubleshooting.
    """
    try:
        # Get cached data
        cached_data = get_cached_logs_data()

        # Try to fetch fresh stats from log collector
        try:
            live_stats = await fetch_log_stats_from_collector()
            cached_data["live_stats"] = live_stats
        except Exception as e:
            cached_data["live_stats"] = {"error": str(e)}

        # Analyze patterns in cached logs
        logs = cached_data.get("logs", [])
        cached_data["analysis"] = analyze_log_patterns(logs)

        # Add summary
        cached_data["summary"] = {
            "total_cached_logs": len(logs),
            "has_live_stats": "error" not in cached_data.get("live_stats", {}),
            "insights_count": len(cached_data["analysis"].get("insights", [])),
            "services_count": len(cached_data["summary"].get("services", []))
        }

        return create_frontend_success_response(
            "logs status retrieved",
            cached_data,
            **build_frontend_context("get_logs_status")
        )

    except Exception as e:
        return handle_frontend_error("get logs status", e, **build_frontend_context("get_logs_status"))


@app.get("/api/logs/fetch")
async def fetch_logs(
    service: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100
):
    """Fetch logs from the log collector service with filtering.

    Retrieves fresh logs from the log collector and updates the cache
    for subsequent visualization requests.
    """
    try:
        logs = await fetch_logs_from_collector(service=service, level=level, limit=limit)

        return create_frontend_success_response(
            f"fetched {len(logs)} logs",
            {"logs": logs, "count": len(logs), "filters": {"service": service, "level": level, "limit": limit}},
            **build_frontend_context("fetch_logs")
        )

    except Exception as e:
        return handle_frontend_error("fetch logs", e, **build_frontend_context("fetch_logs"))


@app.get("/api/logs/stream")
async def stream_logs_endpoint(
    service: Optional[str] = None,
    level: Optional[str] = None,
    poll_interval: int = 5
):
    """Stream logs in real-time using Server-Sent Events.

    Provides a continuous stream of new logs for live dashboard updates
    and real-time monitoring capabilities.
    """
    async def generate():
        try:
            async for log_entry in stream_logs(service=service, level=level, poll_interval=poll_interval):
                # Format as Server-Sent Event
                data = json.dumps(log_entry)
                yield f"data: {data}\n\n"
                await asyncio.sleep(0.1)  # Small delay to prevent overwhelming client
        except Exception as e:
            error_data = json.dumps({"error": str(e), "level": "error", "service": "frontend"})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.get("/api/logs/stats")
async def get_logs_stats():
    """Get fresh log statistics from the log collector service.

    Fetches current statistics and analytics from the log collector
    for monitoring and troubleshooting purposes.
    """
    try:
        stats = await fetch_log_stats_from_collector()

        return create_frontend_success_response(
            "log statistics retrieved",
            stats,
            **build_frontend_context("get_logs_stats")
        )

    except Exception as e:
        return handle_frontend_error("get logs stats", e, **build_frontend_context("get_logs_stats"))


@app.get("/api/doc_store/status")
async def get_doc_store_status():
    """Get comprehensive doc_store status and summary for visualization.

    Returns cached document data, analyses, quality metrics, and style examples
    for dashboard visualization and data browsing.
    """
    try:
        summary = get_doc_store_summary()

        return create_frontend_success_response(
            "doc_store status retrieved",
            summary,
            **build_frontend_context("get_doc_store_status")
        )

    except Exception as e:
        return handle_frontend_error("get doc_store status", e, **build_frontend_context("get_doc_store_status"))


@app.get("/api/doc_store/documents")
async def get_doc_store_documents(
    limit: int = 20,
    offset: int = 0,
    force_refresh: bool = False
):
    """Get documents from doc_store with pagination.

    Retrieves documents with metadata for browsing and visualization.
    """
    try:
        result = await data_browser.get_doc_store_documents(
            limit=limit,
            offset=offset,
            force_refresh=force_refresh
        )

        return create_frontend_success_response(
            f"retrieved {len(result['documents'])} documents",
            result,
            **build_frontend_context("get_doc_store_documents")
        )

    except Exception as e:
        return handle_frontend_error("get doc_store documents", e, **build_frontend_context("get_doc_store_documents"))


@app.get("/api/doc_store/documents/{doc_id}")
async def get_doc_store_document(doc_id: str):
    """Get a specific document by ID.

    Retrieves full document content and metadata for detailed viewing.
    """
    try:
        result = await data_browser.get_doc_store_document(doc_id)

        if result["error"]:
            return create_frontend_success_response(
                "document retrieval failed",
                result,
                **build_frontend_context("get_doc_store_document")
            )

        return create_frontend_success_response(
            "document retrieved",
            result,
            **build_frontend_context("get_doc_store_document")
        )

    except Exception as e:
        return handle_frontend_error("get doc_store document", e, **build_frontend_context("get_doc_store_document"))


@app.get("/api/doc_store/analyses")
async def get_doc_store_analyses(
    document_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    force_refresh: bool = False
):
    """Get analyses from doc_store with optional filtering.

    Retrieves analysis results with optional filtering by document ID.
    """
    try:
        result = await data_browser.get_doc_store_analyses(
            document_id=document_id,
            limit=limit,
            offset=offset,
            force_refresh=force_refresh
        )

        return create_frontend_success_response(
            f"retrieved {len(result['analyses'])} analyses",
            result,
            **build_frontend_context("get_doc_store_analyses")
        )

    except Exception as e:
        return handle_frontend_error("get doc_store analyses", e, **build_frontend_context("get_doc_store_analyses"))


@app.get("/api/doc_store/quality")
async def get_doc_store_quality(force_refresh: bool = False):
    """Get document quality metrics and analysis.

    Retrieves quality metrics, stale documents, and other health indicators.
    """
    try:
        result = await data_browser.get_doc_store_quality(force_refresh=force_refresh)

        return create_frontend_success_response(
            "doc_store quality metrics retrieved",
            result,
            **build_frontend_context("get_doc_store_quality")
        )

    except Exception as e:
        return handle_frontend_error("get doc_store quality", e, **build_frontend_context("get_doc_store_quality"))


@app.get("/api/doc_store/style-examples")
async def get_doc_store_style_examples(force_refresh: bool = False):
    """Get style examples by programming language.

    Retrieves code documentation style examples for different languages.
    """
    try:
        result = await data_browser.get_doc_store_style_examples(force_refresh=force_refresh)

        return create_frontend_success_response(
            "doc_store style examples retrieved",
            result,
            **build_frontend_context("get_doc_store_style_examples")
        )

    except Exception as e:
        return handle_frontend_error("get doc_store style examples", e, **build_frontend_context("get_doc_store_style_examples"))


@app.get("/api/doc_store/search")
async def search_doc_store(q: str, limit: int = 20):
    """Search documents in doc_store.

    Performs full-text search across document content and metadata.
    """
    try:
        result = await data_browser.get_doc_store_search(query=q, limit=limit)

        return create_frontend_success_response(
            f"search completed, found {result['total']} results",
            result,
            **build_frontend_context("search_doc_store")
        )

    except Exception as e:
        return handle_frontend_error("search doc_store", e, **build_frontend_context("search_doc_store"))


@app.get("/api/prompt-store/status")
async def get_prompt_store_status():
    """Get comprehensive prompt-store status and summary for visualization.

    Returns cached prompt data, analytics, and A/B testing information
    for dashboard visualization and data browsing.
    """
    try:
        summary = get_prompt_store_summary()

        return create_frontend_success_response(
            "prompt-store status retrieved",
            summary,
            **build_frontend_context("get_prompt_store_status")
        )

    except Exception as e:
        return handle_frontend_error("get prompt-store status", e, **build_frontend_context("get_prompt_store_status"))


@app.get("/api/prompt-store/prompts")
async def get_prompt_store_prompts(
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    force_refresh: bool = False
):
    """Get prompts from prompt-store with optional filtering.

    Retrieves prompts with metadata, optionally filtered by category.
    """
    try:
        result = await data_browser.get_prompt_store_prompts(
            category=category,
            limit=limit,
            offset=offset,
            force_refresh=force_refresh
        )

        return create_frontend_success_response(
            f"retrieved {len(result['prompts'])} prompts",
            result,
            **build_frontend_context("get_prompt_store_prompts")
        )

    except Exception as e:
        return handle_frontend_error("get prompt-store prompts", e, **build_frontend_context("get_prompt_store_prompts"))


@app.get("/api/prompt-store/analytics")
async def get_prompt_store_analytics(force_refresh: bool = False):
    """Get prompt store analytics and usage metrics.

    Retrieves usage statistics, performance metrics, and A/B testing results.
    """
    try:
        result = await data_browser.get_prompt_store_analytics(force_refresh=force_refresh)

        return create_frontend_success_response(
            "prompt-store analytics retrieved",
            result,
            **build_frontend_context("get_prompt_store_analytics")
        )

    except Exception as e:
        return handle_frontend_error("get prompt-store analytics", e, **build_frontend_context("get_prompt_store_analytics"))


@app.get("/api/orchestrator/status")
async def get_orchestrator_status():
    """Get comprehensive orchestrator status and monitoring data.

    Returns configuration, Redis pub/sub activity, and workflow information
    for dashboard visualization and troubleshooting.
    """
    try:
        summary = get_orchestrator_summary()

        return create_frontend_success_response(
            "orchestrator status retrieved",
            summary,
            **build_frontend_context("get_orchestrator_status")
        )

    except Exception as e:
        return handle_frontend_error("get orchestrator status", e, **build_frontend_context("get_orchestrator_status"))


@app.get("/api/orchestrator/config")
async def get_orchestrator_config(force_refresh: bool = False):
    """Get orchestrator service configuration.

    Retrieves effective configuration including Redis settings,
    peer orchestrators, and service discovery configuration.
    """
    try:
        config_data = await orchestrator_monitor.get_orchestrator_config(force_refresh=force_refresh)

        return create_frontend_success_response(
            "orchestrator config retrieved",
            config_data,
            **build_frontend_context("get_orchestrator_config")
        )

    except Exception as e:
        return handle_frontend_error("get orchestrator config", e, **build_frontend_context("get_orchestrator_config"))


@app.get("/api/orchestrator/redis-activity")
async def get_orchestrator_redis_activity(force_refresh: bool = False):
    """Get Redis pub/sub activity information.

    Retrieves information about Redis channels, published events,
    and pub/sub activity patterns for monitoring.
    """
    try:
        activity_data = await orchestrator_monitor.get_redis_pubsub_activity(force_refresh=force_refresh)

        return create_frontend_success_response(
            "orchestrator Redis activity retrieved",
            activity_data,
            **build_frontend_context("get_orchestrator_redis_activity")
        )

    except Exception as e:
        return handle_frontend_error("get orchestrator Redis activity", e, **build_frontend_context("get_orchestrator_redis_activity"))


@app.get("/api/orchestrator/workflows")
async def get_orchestrator_workflows(force_refresh: bool = False):
    """Get orchestrator workflow information.

    Retrieves available workflows, execution history, and workflow statistics
    for monitoring distributed operations.
    """
    try:
        workflow_data = await orchestrator_monitor.get_orchestrator_workflows(force_refresh=force_refresh)

        return create_frontend_success_response(
            "orchestrator workflows retrieved",
            workflow_data,
            **build_frontend_context("get_orchestrator_workflows")
        )

    except Exception as e:
        return handle_frontend_error("get orchestrator workflows", e, **build_frontend_context("get_orchestrator_workflows"))


@app.get("/api/orchestrator/health")
async def get_orchestrator_health():
    """Get orchestrator service health status.

    Provides quick health check information for monitoring dashboards.
    """
    try:
        health_data = await orchestrator_monitor.get_service_health_status()

        return create_frontend_success_response(
            "orchestrator health status retrieved",
            health_data,
            **build_frontend_context("get_orchestrator_health")
        )

    except Exception as e:
        return handle_frontend_error("get orchestrator health", e, **build_frontend_context("get_orchestrator_health"))


@app.get("/api/analysis/status")
async def get_analysis_status():
    """Get comprehensive analysis service status and cached results.

    Returns analysis service status, cached findings, and analysis statistics
    for dashboard visualization and troubleshooting.
    """
    try:
        status_data = await analysis_monitor.get_analysis_status()

        return create_frontend_success_response(
            "analysis status retrieved",
            status_data,
            **build_frontend_context("get_analysis_status")
        )

    except Exception as e:
        return handle_frontend_error("get analysis status", e, **build_frontend_context("get_analysis_status"))


@app.get("/api/analysis/findings")
async def get_analysis_findings(
    severity: Optional[str] = None,
    finding_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    force_refresh: bool = False
):
    """Get analysis findings with filtering and pagination.

    Retrieves findings from analysis service with optional filtering
    by severity and type, supporting pagination.
    """
    try:
        result = await analysis_monitor.get_findings(
            severity=severity,
            finding_type=finding_type,
            limit=limit,
            offset=offset,
            force_refresh=force_refresh
        )

        return create_frontend_success_response(
            f"retrieved {len(result['findings'])} findings",
            result,
            **build_frontend_context("get_analysis_findings")
        )

    except Exception as e:
        return handle_frontend_error("get analysis findings", e, **build_frontend_context("get_analysis_findings"))


@app.get("/api/analysis/results/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """Get detailed analysis result with linked documents.

    Retrieves a specific analysis result with enhanced document information
    and cross-service correlations for deep-dive exploration.
    """
    try:
        result = await analysis_monitor.get_analysis_result(analysis_id)

        if result.get("error"):
            return create_frontend_success_response(
                "analysis result retrieval failed",
                result,
                **build_frontend_context("get_analysis_result")
            )

        return create_frontend_success_response(
            "analysis result retrieved",
            result,
            **build_frontend_context("get_analysis_result")
        )

    except Exception as e:
        return handle_frontend_error("get analysis result", e, **build_frontend_context("get_analysis_result"))


@app.post("/api/analysis/run")
async def run_analysis_endpoint(analysis_request: dict):
    """Run a new analysis and cache the results.

    Executes analysis on specified targets and caches results for visualization.
    Supports different analysis types and options.
    """
    try:
        result = await analysis_monitor.run_analysis(
            targets=analysis_request.get("targets", []),
            analysis_type=analysis_request.get("analysis_type", "consistency"),
            options=analysis_request.get("options", {})
        )

        status_message = "analysis completed successfully" if result["success"] else "analysis failed"
        return create_frontend_success_response(
            status_message,
            result,
            **build_frontend_context("run_analysis")
        )

    except Exception as e:
        return handle_frontend_error("run analysis", e, **build_frontend_context("run_analysis"))


@app.get("/api/analysis/reports/{report_type}")
async def get_analysis_report(report_type: str):
    """Get analysis reports by type.

    Retrieves different types of analysis reports including
    confluence consolidation and Jira staleness reports.
    """
    try:
        report_data = await analysis_monitor.get_reports(report_type=report_type)

        return create_frontend_success_response(
            f"{report_type} report retrieved",
            report_data,
            **build_frontend_context("get_analysis_report")
        )

    except Exception as e:
        return handle_frontend_error("get analysis report", e, **build_frontend_context("get_analysis_report"))


@app.get("/api/analysis/history")
async def get_analysis_history(limit: int = 20):
    """Get analysis execution history.

    Retrieves recent analysis runs with their results and metadata
    for historical analysis and trend identification.
    """
    try:
        history = analysis_monitor.get_analysis_history(limit=limit)

        return create_frontend_success_response(
            f"retrieved {len(history)} analysis runs from history",
            {"history": history, "limit": limit},
            **build_frontend_context("get_analysis_history")
        )

    except Exception as e:
        return handle_frontend_error("get analysis history", e, **build_frontend_context("get_analysis_history"))


@app.get("/api/analysis/findings/{finding_id}")
async def get_finding_details(finding_id: str):
    """Get detailed information about a specific finding.

    Retrieves comprehensive information about a finding including
    its analysis context and related documents.
    """
    try:
        finding_details = analysis_monitor.get_finding_details(finding_id)

        if not finding_details:
            return create_frontend_success_response(
                "finding not found",
                {"finding": None, "error": "Finding not found"},
                **build_frontend_context("get_finding_details")
            )

        return create_frontend_success_response(
            "finding details retrieved",
            finding_details,
            **build_frontend_context("get_finding_details")
        )

    except Exception as e:
        return handle_frontend_error("get finding details", e, **build_frontend_context("get_finding_details"))


# Code Analyzer API endpoints
@app.get("/api/code-analyzer/status")
async def get_code_analyzer_status():
    """Get comprehensive code analyzer service status."""
    try:
        status_data = await code_analyzer_monitor.get_analyzer_status()
        return create_frontend_success_response(
            "code analyzer status retrieved",
            status_data,
            **build_frontend_context("get_code_analyzer_status")
        )
    except Exception as e:
        return handle_frontend_error("get code analyzer status", e, **build_frontend_context("get_code_analyzer_status"))


@app.post("/api/code-analyzer/analyze-text")
async def analyze_text_code(req: dict):
    """Analyze text content for code quality and issues."""
    try:
        result = await code_analyzer_monitor.analyze_text(
            req.get("text", ""),
            req.get("analysis_type", "general")
        )
        return create_frontend_success_response(
            "text analysis completed",
            result,
            **build_frontend_context("analyze_text_code")
        )
    except Exception as e:
        return handle_frontend_error("analyze text code", e, **build_frontend_context("analyze_text_code"))


@app.post("/api/code-analyzer/analyze-files")
async def analyze_files_code(req: dict):
    """Analyze multiple files for code quality and issues."""
    try:
        result = await code_analyzer_monitor.analyze_files(
            req.get("files", []),
            req.get("analysis_type", "general")
        )
        return create_frontend_success_response(
            "files analysis completed",
            result,
            **build_frontend_context("analyze_files_code")
        )
    except Exception as e:
        return handle_frontend_error("analyze files code", e, **build_frontend_context("analyze_files_code"))


@app.post("/api/code-analyzer/security-scan")
async def security_scan_code(req: dict):
    """Perform security scan on code."""
    try:
        result = await code_analyzer_monitor.scan_security(req.get("code", ""))
        return create_frontend_success_response(
            "security scan completed",
            result,
            **build_frontend_context("security_scan_code")
        )
    except Exception as e:
        return handle_frontend_error("security scan code", e, **build_frontend_context("security_scan_code"))


@app.post("/api/code-analyzer/style-check")
async def style_check_code(req: dict):
    """Check code style compliance."""
    try:
        result = await code_analyzer_monitor.check_style(
            req.get("code", ""),
            req.get("style", "google")
        )
        return create_frontend_success_response(
            "style check completed",
            result,
            **build_frontend_context("style_check_code")
        )
    except Exception as e:
        return handle_frontend_error("style check code", e, **build_frontend_context("style_check_code"))


@app.get("/api/code-analyzer/style-examples")
async def get_style_examples():
    """Get code style examples."""
    try:
        # Mock style examples for now
        examples = {
            "python": {
                "google": "# Google style example\\nimport os\\n\\ndef function_name(param1, param2):\\n    \\\"\\\"\\\"Function docstring.\\\"\\\"\\\"\\n    return param1 + param2",
                "pep8": "# PEP 8 style example\\nimport os\\n\\ndef function_name(param1, param2):\\n    \\\"\\\"\\\"Function docstring.\\\"\\\"\\\"\\n    return param1 + param2"
            },
            "javascript": {
                "standard": "// Standard style example\\nfunction functionName(param1, param2) {\\n  // Function body\\n  return param1 + param2;\\n}"
            }
        }
        return create_frontend_success_response(
            "style examples retrieved",
            {"examples": examples},
            **build_frontend_context("get_style_examples")
        )
    except Exception as e:
        return handle_frontend_error("get style examples", e, **build_frontend_context("get_style_examples"))


@app.get("/api/code-analyzer/history")
async def get_code_analyzer_history():
    """Get code analyzer analysis history."""
    try:
        history = code_analyzer_monitor.get_analysis_history()
        return create_frontend_success_response(
            "analysis history retrieved",
            {"history": history},
            **build_frontend_context("get_code_analyzer_history")
        )
    except Exception as e:
        return handle_frontend_error("get code analyzer history", e, **build_frontend_context("get_code_analyzer_history"))


# ============================================================================
# BEDROCK PROXY API ENDPOINTS
# ============================================================================

@app.get("/api/bedrock-proxy/status")
async def get_bedrock_proxy_status():
    """Get comprehensive bedrock proxy service status.

    Returns health information, invocation statistics, and recent activity
    for monitoring the bedrock proxy service.
    """
    try:
        status_data = await bedrock_proxy_monitor.get_proxy_status()
        return create_frontend_success_response(
            "bedrock proxy status retrieved",
            status_data,
            **build_frontend_context("get_bedrock_proxy_status")
        )
    except Exception as e:
        return handle_frontend_error("get bedrock proxy status", e, **build_frontend_context("get_bedrock_proxy_status"))


@app.post("/api/bedrock-proxy/invoke")
async def invoke_bedrock_proxy(req: dict):
    """Invoke AI through the bedrock proxy and cache the result.

    Accepts a prompt and optional template/format parameters to generate
    structured AI responses. Results are cached for monitoring and analysis.
    """
    try:
        prompt = req.get("prompt")
        if not prompt:
            return handle_frontend_error("invoke bedrock proxy", ValueError("Prompt is required"), **build_frontend_context("invoke_bedrock_proxy"))

        result = await bedrock_proxy_monitor.invoke_ai(
            prompt=prompt,
            template=req.get("template"),
            format=req.get("format"),
            title=req.get("title"),
            model=req.get("model"),
            region=req.get("region"),
            **req.get("params", {})
        )

        if result.get("success"):
            return create_frontend_success_response(
                "bedrock proxy invocation completed",
                {
                    "invocation_id": result.get("invocation_id"),
                    "response": result.get("response")
                },
                **build_frontend_context("invoke_bedrock_proxy")
            )
        else:
            return handle_frontend_error("invoke bedrock proxy", Exception(result.get("error", "Unknown error")), **build_frontend_context("invoke_bedrock_proxy"))

    except Exception as e:
        return handle_frontend_error("invoke bedrock proxy", e, **build_frontend_context("invoke_bedrock_proxy"))


@app.get("/api/bedrock-proxy/history")
async def get_bedrock_proxy_history(limit: int = 20):
    """Get bedrock proxy invocation history.

    Returns cached invocation history with optional limit parameter.
    Useful for analyzing usage patterns and troubleshooting.
    """
    try:
        history = bedrock_proxy_monitor.get_invocation_history(limit=limit)
        return create_frontend_success_response(
            "bedrock proxy history retrieved",
            history,
            **build_frontend_context("get_bedrock_proxy_history")
        )
    except Exception as e:
        return handle_frontend_error("get bedrock proxy history", e, **build_frontend_context("get_bedrock_proxy_history"))


# ============================================================================
# DISCOVERY AGENT API ENDPOINTS
# ============================================================================

@app.get("/api/discovery-agent/status")
async def get_discovery_agent_status():
    """Get comprehensive discovery agent service status.

    Returns health information, discovery statistics, and recent activity
    for monitoring the discovery agent service operations.
    """
    try:
        from .modules.discovery_agent_monitor import discovery_agent_monitor
        status_data = await discovery_agent_monitor.get_discovery_status()
        return create_frontend_success_response(
            "discovery agent status retrieved",
            status_data,
            **build_frontend_context("get_discovery_agent_status")
        )
    except Exception as e:
        return handle_frontend_error("get discovery agent status", e, **build_frontend_context("get_discovery_agent_status"))


@app.post("/api/discovery-agent/discover")
async def discover_service_endpoints(req: dict):
    """Trigger endpoint discovery for a service and cache the result.

    Accepts a service URL and optional parameters to discover OpenAPI endpoints
    and optionally register them with the orchestrator. Supports dry-run mode.
    """
    try:
        from .modules.discovery_agent_monitor import discovery_agent_monitor

        service_url = req.get("service_url")
        if not service_url:
            return handle_frontend_error("discover service endpoints", ValueError("service_url is required"), **build_frontend_context("discover_service_endpoints"))

        result = await discovery_agent_monitor.discover_endpoints(
            service_url=service_url,
            service_name=req.get("service_name"),
            dry_run=req.get("dry_run", False),
            spec_url=req.get("spec_url")
        )

        if result.get("success"):
            return create_frontend_success_response(
                "service endpoint discovery completed",
                {
                    "discovery_id": result.get("discovery_id"),
                    "endpoints_discovered": result.get("endpoints_discovered"),
                    "response": result.get("response")
                },
                **build_frontend_context("discover_service_endpoints")
            )
        else:
            return handle_frontend_error("discover service endpoints", Exception(result.get("error", "Unknown error")), **build_frontend_context("discover_service_endpoints"))

    except Exception as e:
        return handle_frontend_error("discover service endpoints", e, **build_frontend_context("discover_service_endpoints"))


@app.get("/api/discovery-agent/history")
async def get_discovery_agent_history(limit: int = 20):
    """Get discovery agent operation history.

    Returns cached discovery history with optional limit parameter.
    Useful for analyzing discovery patterns and troubleshooting.
    """
    try:
        from .modules.discovery_agent_monitor import discovery_agent_monitor
        history = discovery_agent_monitor.get_discovery_history(limit=limit)
        return create_frontend_success_response(
            "discovery agent history retrieved",
            history,
            **build_frontend_context("get_discovery_agent_history")
        )
    except Exception as e:
        return handle_frontend_error("get discovery agent history", e, **build_frontend_context("get_discovery_agent_history"))


# ============================================================================
# GITHUB MCP API ENDPOINTS
# ============================================================================

@app.get("/api/github-mcp/status")
async def get_github_mcp_status():
    """Get comprehensive github-mcp service status.

    Returns health information, configuration details, tool statistics,
    and recent activity for monitoring the GitHub MCP service.
    """
    try:
        from .modules.github_mcp_monitor import github_mcp_monitor
        status_data = await github_mcp_monitor.get_mcp_status()
        return create_frontend_success_response(
            "github-mcp status retrieved",
            status_data,
            **build_frontend_context("get_github_mcp_status")
        )
    except Exception as e:
        return handle_frontend_error("get github-mcp status", e, **build_frontend_context("get_github_mcp_status"))


@app.get("/api/github-mcp/tools")
async def get_github_mcp_tools(toolsets: Optional[str] = None):
    """Get available GitHub MCP tools.

    Returns list of available tools filtered by toolsets when specified.
    Useful for discovering what GitHub operations are available.
    """
    try:
        from .modules.github_mcp_monitor import github_mcp_monitor
        tools = await github_mcp_monitor.get_available_tools(toolsets=toolsets)
        return create_frontend_success_response(
            "github-mcp tools retrieved",
            tools,
            **build_frontend_context("get_github_mcp_tools")
        )
    except Exception as e:
        return handle_frontend_error("get github-mcp tools", e, **build_frontend_context("get_github_mcp_tools"))


@app.post("/api/github-mcp/invoke")
async def invoke_github_mcp_tool(req: dict):
    """Invoke a GitHub MCP tool and cache the result.

    Accepts a tool name and arguments to execute GitHub operations
    through the MCP service. Results are cached for monitoring and analysis.
    """
    try:
        from .modules.github_mcp_monitor import github_mcp_monitor

        tool_name = req.get("tool_name")
        if not tool_name:
            return handle_frontend_error("invoke github-mcp tool", ValueError("tool_name is required"), **build_frontend_context("invoke_github_mcp_tool"))

        result = await github_mcp_monitor.invoke_tool(
            tool_name=tool_name,
            arguments=req.get("arguments", {}),
            mock=req.get("mock"),
            correlation_id=req.get("correlation_id")
        )

        if result.get("success"):
            return create_frontend_success_response(
                "github-mcp tool invoked successfully",
                {
                    "invocation_id": result.get("invocation_id"),
                    "tool": result.get("tool"),
                    "result": result.get("result")
                },
                **build_frontend_context("invoke_github_mcp_tool")
            )
        else:
            return handle_frontend_error("invoke github-mcp tool", Exception(result.get("error", "Unknown error")), **build_frontend_context("invoke_github_mcp_tool"))

    except Exception as e:
        return handle_frontend_error("invoke github-mcp tool", e, **build_frontend_context("invoke_github_mcp_tool"))


@app.get("/api/github-mcp/history")
async def get_github_mcp_history(limit: int = 20):
    """Get GitHub MCP tool invocation history.

    Returns cached tool invocation history with optional limit parameter.
    Useful for analyzing tool usage patterns and troubleshooting.
    """
    try:
        from .modules.github_mcp_monitor import github_mcp_monitor
        history = github_mcp_monitor.get_invocation_history(limit=limit)
        return create_frontend_success_response(
            "github-mcp history retrieved",
            history,
            **build_frontend_context("get_github_mcp_history")
        )
    except Exception as e:
        return handle_frontend_error("get github-mcp history", e, **build_frontend_context("get_github_mcp_history"))


# ============================================================================
# INTERPRETER API ENDPOINTS
# ============================================================================

@app.get("/api/interpreter/status")
async def get_interpreter_status():
    """Get comprehensive interpreter service status.

    Returns health information, supported intents, interpretation statistics,
    and recent activity for monitoring the interpreter service.
    """
    try:
        from .modules.interpreter_monitor import interpreter_monitor
        status_data = await interpreter_monitor.get_interpreter_status()
        return create_frontend_success_response(
            "interpreter status retrieved",
            status_data,
            **build_frontend_context("get_interpreter_status")
        )
    except Exception as e:
        return handle_frontend_error("get interpreter status", e, **build_frontend_context("get_interpreter_status"))


@app.get("/api/interpreter/intents")
async def get_interpreter_intents():
    """Get supported intents and their examples.

    Returns comprehensive information about all supported query intents,
    including example queries, entity extraction patterns, and descriptions.
    """
    try:
        from .modules.interpreter_monitor import interpreter_monitor
        intents = await interpreter_monitor.get_supported_intents()
        return create_frontend_success_response(
            "interpreter intents retrieved",
            intents,
            **build_frontend_context("get_interpreter_intents")
        )
    except Exception as e:
        return handle_frontend_error("get interpreter intents", e, **build_frontend_context("get_interpreter_intents"))


@app.post("/api/interpreter/interpret")
async def interpret_query(req: dict):
    """Interpret a natural language query.

    Accepts a query string and returns intent recognition, entity extraction,
    confidence scoring, and generated workflow without execution.
    """
    try:
        from .modules.interpreter_monitor import interpreter_monitor

        query = req.get("query")
        if not query:
            return handle_frontend_error("interpret query", ValueError("query is required"), **build_frontend_context("interpret_query"))

        result = await interpreter_monitor.interpret_query(
            query=query,
            session_id=req.get("session_id"),
            user_id=req.get("user_id")
        )

        if result.get("success"):
            return create_frontend_success_response(
                "query interpreted successfully",
                {
                    "interpretation_id": result.get("interpretation_id"),
                    "intent": result.get("intent"),
                    "confidence": result.get("confidence"),
                    "workflow": result.get("workflow"),
                    "response": result.get("response")
                },
                **build_frontend_context("interpret_query")
            )
        else:
            return handle_frontend_error("interpret query", Exception(result.get("error", "Unknown error")), **build_frontend_context("interpret_query"))

    except Exception as e:
        return handle_frontend_error("interpret query", e, **build_frontend_context("interpret_query"))


@app.post("/api/interpreter/execute")
async def execute_interpreted_workflow(req: dict):
    """Interpret query and execute the resulting workflow.

    Interprets the user query and immediately executes the generated workflow
    across multiple services, providing end-to-end processing results.
    """
    try:
        from .modules.interpreter_monitor import interpreter_monitor

        query = req.get("query")
        if not query:
            return handle_frontend_error("execute interpreted workflow", ValueError("query is required"), **build_frontend_context("execute_interpreted_workflow"))

        result = await interpreter_monitor.execute_workflow(
            query=query,
            session_id=req.get("session_id"),
            user_id=req.get("user_id")
        )

        if result.get("success"):
            return create_frontend_success_response(
                "workflow executed successfully",
                {
                    "execution_id": result.get("execution_id"),
                    "results": result.get("results"),
                    "execution_time": result.get("execution_time"),
                    "response": result.get("response")
                },
                **build_frontend_context("execute_interpreted_workflow")
            )
        else:
            return handle_frontend_error("execute interpreted workflow", Exception(result.get("error", "Unknown error")), **build_frontend_context("execute_interpreted_workflow"))

    except Exception as e:
        return handle_frontend_error("execute interpreted workflow", e, **build_frontend_context("execute_interpreted_workflow"))


@app.get("/api/interpreter/interpretations")
async def get_interpreter_history(limit: int = 20):
    """Get interpretation history.

    Returns cached query interpretation history with optional limit parameter.
    Useful for analyzing interpretation patterns and confidence trends.
    """
    try:
        from .modules.interpreter_monitor import interpreter_monitor
        history = interpreter_monitor.get_interpretation_history(limit=limit)
        return create_frontend_success_response(
            "interpreter interpretation history retrieved",
            history,
            **build_frontend_context("get_interpreter_history")
        )
    except Exception as e:
        return handle_frontend_error("get interpreter history", e, **build_frontend_context("get_interpreter_history"))


@app.get("/api/interpreter/executions")
async def get_execution_history(limit: int = 20):
    """Get workflow execution history.

    Returns cached workflow execution history with optional limit parameter.
    Useful for analyzing execution success rates and performance metrics.
    """
    try:
        from .modules.interpreter_monitor import interpreter_monitor
        history = interpreter_monitor.get_execution_history(limit=limit)
        return create_frontend_success_response(
            "interpreter execution history retrieved",
            history,
            **build_frontend_context("get_execution_history")
        )
    except Exception as e:
        return handle_frontend_error("get execution history", e, **build_frontend_context("get_execution_history"))


# ============================================================================
# MEMORY AGENT API ENDPOINTS
# ============================================================================

@app.get("/api/memory-agent/status")
async def get_memory_agent_status():
    """Get comprehensive memory agent service status.

    Returns health information, memory statistics, and recent activity
    for monitoring the memory agent service operations.
    """
    try:
        from .modules.memory_agent_monitor import memory_agent_monitor
        status_data = await memory_agent_monitor.get_memory_status()
        return create_frontend_success_response(
            "memory agent status retrieved",
            status_data,
            **build_frontend_context("get_memory_agent_status")
        )
    except Exception as e:
        return handle_frontend_error("get memory agent status", e, **build_frontend_context("get_memory_agent_status"))


@app.get("/api/memory-agent/items")
async def get_memory_agent_items(type: Optional[str] = None, key: Optional[str] = None, limit: int = 25):
    """Get memory items with filtering.

    Returns stored memory items with optional filtering by type and key,
    useful for browsing operational context and event summaries.
    """
    try:
        from .modules.memory_agent_monitor import memory_agent_monitor
        items = await memory_agent_monitor.list_memory_items(type=type, key=key, limit=limit)
        return create_frontend_success_response(
            "memory agent items retrieved",
            items,
            **build_frontend_context("get_memory_agent_items")
        )
    except Exception as e:
        return handle_frontend_error("get memory agent items", e, **build_frontend_context("get_memory_agent_items"))


@app.post("/api/memory-agent/store")
async def store_memory_agent_item(req: dict):
    """Store a memory item.

    Accepts memory item data and stores it in the memory agent's
    operational context storage with TTL-based expiration.
    """
    try:
        from .modules.memory_agent_monitor import memory_agent_monitor

        item_type = req.get("type")
        key = req.get("key")
        value = req.get("value")

        if not item_type or not key or value is None:
            return handle_frontend_error("store memory item", ValueError("type, key, and value are required"), **build_frontend_context("store_memory_agent_item"))

        result = await memory_agent_monitor.store_memory_item(
            item_type=item_type,
            key=key,
            value=value,
            metadata=req.get("metadata")
        )

        if result.get("success"):
            return create_frontend_success_response(
                "memory item stored successfully",
                {
                    "item_id": result.get("item_id"),
                    "response": result.get("response")
                },
                **build_frontend_context("store_memory_agent_item")
            )
        else:
            return handle_frontend_error("store memory item", Exception(result.get("error", "Unknown error")), **build_frontend_context("store_memory_agent_item"))

    except Exception as e:
        return handle_frontend_error("store memory item", e, **build_frontend_context("store_memory_agent_item"))


@app.get("/api/memory-agent/history")
async def get_memory_agent_history(limit: int = 20):
    """Get memory agent item history.

    Returns cached memory item history with optional limit parameter.
    Useful for analyzing memory storage patterns and content.
    """
    try:
        from .modules.memory_agent_monitor import memory_agent_monitor
        history = memory_agent_monitor.get_memory_history(limit=limit)
        return create_frontend_success_response(
            "memory agent history retrieved",
            history,
            **build_frontend_context("get_memory_agent_history")
        )
    except Exception as e:
        return handle_frontend_error("get memory agent history", e, **build_frontend_context("get_memory_agent_history"))


# ============================================================================
# NOTIFICATION SERVICE API ENDPOINTS
# ============================================================================

@app.get("/api/notification-service/status")
async def get_notification_service_status():
    """Get comprehensive notification service status.

    Returns health information, notification statistics, DLQ status,
    and recent activity for monitoring the notification service.
    """
    try:
        from .modules.notification_service_monitor import notification_service_monitor
        status_data = await notification_service_monitor.get_notification_status()
        return create_frontend_success_response(
            "notification service status retrieved",
            status_data,
            **build_frontend_context("get_notification_service_status")
        )
    except Exception as e:
        return handle_frontend_error("get notification service status", e, **build_frontend_context("get_notification_service_status"))


@app.get("/api/notification-service/dlq")
async def get_notification_dlq(limit: int = 50):
    """Get dead letter queue entries.

    Returns failed notification attempts for debugging and monitoring
    delivery issues in the notification service.
    """
    try:
        from .modules.notification_service_monitor import notification_service_monitor
        dlq_entries = await notification_service_monitor.get_dlq_entries(limit=limit)
        return create_frontend_success_response(
            "notification DLQ retrieved",
            dlq_entries,
            **build_frontend_context("get_notification_dlq")
        )
    except Exception as e:
        return handle_frontend_error("get notification DLQ", e, **build_frontend_context("get_notification_dlq"))


@app.post("/api/notification-service/resolve-owners")
async def resolve_notification_owners(req: dict):
    """Resolve owners to notification targets.

    Accepts a list of owner names and returns their resolved notification
    targets (email addresses, webhook URLs, etc.) for bulk operations.
    """
    try:
        from .modules.notification_service_monitor import notification_service_monitor

        owners = req.get("owners", [])
        if not owners or not isinstance(owners, list):
            return handle_frontend_error("resolve owners", ValueError("owners must be a non-empty list"), **build_frontend_context("resolve_notification_owners"))

        result = await notification_service_monitor.resolve_owners(owners)

        if result.get("success"):
            return create_frontend_success_response(
                "owners resolved successfully",
                {
                    "resolution_id": result.get("resolution_id"),
                    "resolved_targets": result.get("resolved_targets"),
                    "resolution_count": result.get("resolution_count"),
                    "response": result.get("response")
                },
                **build_frontend_context("resolve_notification_owners")
            )
        else:
            return handle_frontend_error("resolve owners", Exception(result.get("error", "Unknown error")), **build_frontend_context("resolve_notification_owners"))

    except Exception as e:
        return handle_frontend_error("resolve owners", e, **build_frontend_context("resolve_notification_owners"))


@app.post("/api/notification-service/send")
async def send_test_notification(req: dict):
    """Send a test notification.

    Accepts notification parameters and sends a test notification through
    the specified channel for testing delivery capabilities.
    """
    try:
        from .modules.notification_service_monitor import notification_service_monitor

        channel = req.get("channel")
        target = req.get("target")
        title = req.get("title")
        message = req.get("message")

        if not all([channel, target, title, message]):
            return handle_frontend_error("send notification", ValueError("channel, target, title, and message are required"), **build_frontend_context("send_test_notification"))

        result = await notification_service_monitor.send_notification(
            channel=channel,
            target=target,
            title=title,
            message=message,
            metadata=req.get("metadata"),
            labels=req.get("labels", [])
        )

        if result.get("success"):
            return create_frontend_success_response(
                "notification sent successfully",
                {
                    "notification_id": result.get("notification_id"),
                    "response": result.get("response")
                },
                **build_frontend_context("send_test_notification")
            )
        else:
            return handle_frontend_error("send notification", Exception(result.get("error", "Unknown error")), **build_frontend_context("send_test_notification"))

    except Exception as e:
        return handle_frontend_error("send notification", e, **build_frontend_context("send_test_notification"))


@app.get("/api/notification-service/notifications")
async def get_notification_history(limit: int = 20):
    """Get notification delivery history.

    Returns cached notification delivery history with optional limit parameter.
    Useful for analyzing delivery success rates and troubleshooting.
    """
    try:
        from .modules.notification_service_monitor import notification_service_monitor
        history = notification_service_monitor.get_notification_history(limit=limit)
        return create_frontend_success_response(
            "notification history retrieved",
            history,
            **build_frontend_context("get_notification_history")
        )
    except Exception as e:
        return handle_frontend_error("get notification history", e, **build_frontend_context("get_notification_history"))


@app.get("/api/notification-service/resolutions")
async def get_owner_resolution_history(limit: int = 20):
    """Get owner resolution history.

    Returns cached owner resolution history with optional limit parameter.
    Useful for analyzing resolution patterns and caching effectiveness.
    """
    try:
        from .modules.notification_service_monitor import notification_service_monitor
        history = notification_service_monitor.get_owner_resolution_history(limit=limit)
        return create_frontend_success_response(
            "owner resolution history retrieved",
            history,
            **build_frontend_context("get_owner_resolution_history")
        )
    except Exception as e:
        return handle_frontend_error("get owner resolution history", e, **build_frontend_context("get_owner_resolution_history"))


# ============================================================================
# SECURE ANALYZER API ENDPOINTS
# ============================================================================

@app.get("/api/secure-analyzer/status")
async def get_secure_analyzer_status():
    """Get comprehensive secure analyzer service status.

    Returns health information, analysis statistics, and recent activity
    for monitoring the secure analyzer service operations.
    """
    try:
        from .modules.secure_analyzer_monitor import secure_analyzer_monitor
        status_data = await secure_analyzer_monitor.get_secure_status()
        return create_frontend_success_response(
            "secure analyzer status retrieved",
            status_data,
            **build_frontend_context("get_secure_analyzer_status")
        )
    except Exception as e:
        return handle_frontend_error("get secure analyzer status", e, **build_frontend_context("get_secure_analyzer_status"))


@app.post("/api/secure-analyzer/detect")
async def detect_secure_content(req: dict):
    """Detect sensitive content in provided text.

    Accepts content and optional keywords, returns security analysis
    including detected sensitive information and security topics.
    """
    try:
        from .modules.secure_analyzer_monitor import secure_analyzer_monitor

        content = req.get("content")
        keywords = req.get("keywords", [])
        keyword_document = req.get("keyword_document")

        if not content:
            return handle_frontend_error("detect content", ValueError("content is required"), **build_frontend_context("detect_secure_content"))

        result = await secure_analyzer_monitor.detect_content(
            content=content,
            keywords=keywords,
            keyword_document=keyword_document
        )

        if result.get("success"):
            return create_frontend_success_response(
                "content detection completed",
                {
                    "detection_id": result.get("detection_id"),
                    "sensitive": result.get("sensitive"),
                    "matches": result.get("matches"),
                    "topics": result.get("topics"),
                    "response": result.get("response")
                },
                **build_frontend_context("detect_secure_content")
            )
        else:
            return handle_frontend_error("detect content", Exception(result.get("error", "Unknown error")), **build_frontend_context("detect_secure_content"))

    except Exception as e:
        return handle_frontend_error("detect content", e, **build_frontend_context("detect_secure_content"))


@app.post("/api/secure-analyzer/suggest")
async def suggest_secure_models(req: dict):
    """Get model suggestions based on content sensitivity.

    Accepts content and returns AI model recommendations based on
    security analysis and policy enforcement.
    """
    try:
        from .modules.secure_analyzer_monitor import secure_analyzer_monitor

        content = req.get("content")
        keywords = req.get("keywords", [])
        keyword_document = req.get("keyword_document")

        if not content:
            return handle_frontend_error("suggest models", ValueError("content is required"), **build_frontend_context("suggest_secure_models"))

        result = await secure_analyzer_monitor.suggest_models(
            content=content,
            keywords=keywords,
            keyword_document=keyword_document
        )

        if result.get("success"):
            return create_frontend_success_response(
                "model suggestions generated",
                {
                    "suggestion_id": result.get("suggestion_id"),
                    "sensitive": result.get("sensitive"),
                    "allowed_models": result.get("allowed_models"),
                    "suggestion": result.get("suggestion"),
                    "response": result.get("response")
                },
                **build_frontend_context("suggest_secure_models")
            )
        else:
            return handle_frontend_error("suggest models", Exception(result.get("error", "Unknown error")), **build_frontend_context("suggest_secure_models"))

    except Exception as e:
        return handle_frontend_error("suggest models", e, **build_frontend_context("suggest_secure_models"))


@app.post("/api/secure-analyzer/summarize")
async def generate_secure_summary(req: dict):
    """Generate secure summary with policy enforcement.

    Accepts content and generates summaries using appropriate AI models
    based on security analysis and policy constraints.
    """
    try:
        from .modules.secure_analyzer_monitor import secure_analyzer_monitor

        content = req.get("content")
        providers = req.get("providers", [])
        override_policy = req.get("override_policy", False)
        keywords = req.get("keywords", [])
        keyword_document = req.get("keyword_document")
        prompt = req.get("prompt")

        if not content:
            return handle_frontend_error("generate secure summary", ValueError("content is required"), **build_frontend_context("generate_secure_summary"))

        result = await secure_analyzer_monitor.secure_summarize(
            content=content,
            providers=providers,
            override_policy=override_policy,
            keywords=keywords,
            keyword_document=keyword_document,
            prompt=prompt
        )

        if result.get("success"):
            return create_frontend_success_response(
                "secure summary generated",
                {
                    "summary_id": result.get("summary_id"),
                    "summary": result.get("summary"),
                    "provider_used": result.get("provider_used"),
                    "confidence": result.get("confidence"),
                    "policy_enforced": result.get("policy_enforced"),
                    "topics_detected": result.get("topics_detected"),
                    "response": result.get("response")
                },
                **build_frontend_context("generate_secure_summary")
            )
        else:
            return handle_frontend_error("generate secure summary", Exception(result.get("error", "Unknown error")), **build_frontend_context("generate_secure_summary"))

    except Exception as e:
        return handle_frontend_error("generate secure summary", e, **build_frontend_context("generate_secure_summary"))


@app.get("/api/secure-analyzer/detections")
async def get_detection_history(limit: int = 20):
    """Get content detection history.

    Returns cached detection history with optional limit parameter.
    Useful for analyzing security patterns and detection effectiveness.
    """
    try:
        from .modules.secure_analyzer_monitor import secure_analyzer_monitor
        history = secure_analyzer_monitor.get_detection_history(limit=limit)
        return create_frontend_success_response(
            "detection history retrieved",
            history,
            **build_frontend_context("get_detection_history")
        )
    except Exception as e:
        return handle_frontend_error("get detection history", e, **build_frontend_context("get_detection_history"))


@app.get("/api/secure-analyzer/suggestions")
async def get_suggestion_history(limit: int = 20):
    """Get model suggestion history.

    Returns cached suggestion history with optional limit parameter.
    Useful for analyzing policy enforcement and model selection patterns.
    """
    try:
        from .modules.secure_analyzer_monitor import secure_analyzer_monitor
        history = secure_analyzer_monitor.get_suggestion_history(limit=limit)
        return create_frontend_success_response(
            "suggestion history retrieved",
            history,
            **build_frontend_context("get_suggestion_history")
        )
    except Exception as e:
        return handle_frontend_error("get suggestion history", e, **build_frontend_context("get_suggestion_history"))


@app.get("/api/secure-analyzer/summaries")
async def get_summary_history(limit: int = 20):
    """Get secure summary history.

    Returns cached summary history with optional limit parameter.
    Useful for analyzing summarization effectiveness and policy compliance.
    """
    try:
        from .modules.secure_analyzer_monitor import secure_analyzer_monitor
        history = secure_analyzer_monitor.get_summary_history(limit=limit)
        return create_frontend_success_response(
            "summary history retrieved",
            history,
            **build_frontend_context("get_summary_history")
        )
    except Exception as e:
        return handle_frontend_error("get summary history", e, **build_frontend_context("get_summary_history"))


# ============================================================================
# SOURCE AGENT API ENDPOINTS
# ============================================================================

@app.get("/api/source-agent/status")
async def get_source_agent_status():
    """Get comprehensive source agent service status.

    Returns health information, operation statistics, source capabilities,
    and recent activity for monitoring the source agent service.
    """
    try:
        from .modules.source_agent_monitor import source_agent_monitor
        status_data = await source_agent_monitor.get_source_status()
        return create_frontend_success_response(
            "source agent status retrieved",
            status_data,
            **build_frontend_context("get_source_agent_status")
        )
    except Exception as e:
        return handle_frontend_error("get source agent status", e, **build_frontend_context("get_source_agent_status"))


@app.post("/api/source-agent/fetch")
async def fetch_source_document(req: dict):
    """Fetch document from specified source.

    Accepts source type, identifier, and optional scope parameters
    to fetch documents from GitHub, Jira, or Confluence.
    """
    try:
        from .modules.source_agent_monitor import source_agent_monitor

        source = req.get("source")
        identifier = req.get("identifier")
        scope = req.get("scope", {})

        if not source or not identifier:
            return handle_frontend_error("fetch document", ValueError("source and identifier are required"), **build_frontend_context("fetch_source_document"))

        result = await source_agent_monitor.fetch_document(
            source=source,
            identifier=identifier,
            scope=scope
        )

        if result.get("success"):
            return create_frontend_success_response(
                "document fetched successfully",
                {
                    "fetch_id": result.get("fetch_id"),
                    "source": result.get("source"),
                    "document": result.get("document"),
                    "response": result.get("response")
                },
                **build_frontend_context("fetch_source_document")
            )
        else:
            return handle_frontend_error("fetch document", Exception(result.get("error", "Unknown error")), **build_frontend_context("fetch_source_document"))

    except Exception as e:
        return handle_frontend_error("fetch document", e, **build_frontend_context("fetch_source_document"))


@app.post("/api/source-agent/normalize")
async def normalize_source_data(req: dict):
    """Normalize data from specified source.

    Accepts source type, raw data, and optional correlation ID
    to normalize data from GitHub, Jira, or Confluence into standard format.
    """
    try:
        from .modules.source_agent_monitor import source_agent_monitor

        source = req.get("source")
        data = req.get("data")
        correlation_id = req.get("correlation_id")

        if not source or not data:
            return handle_frontend_error("normalize data", ValueError("source and data are required"), **build_frontend_context("normalize_source_data"))

        result = await source_agent_monitor.normalize_data(
            source=source,
            data=data,
            correlation_id=correlation_id
        )

        if result.get("success"):
            return create_frontend_success_response(
                "data normalized successfully",
                {
                    "normalization_id": result.get("normalization_id"),
                    "source": result.get("source"),
                    "envelope": result.get("envelope"),
                    "response": result.get("response")
                },
                **build_frontend_context("normalize_source_data")
            )
        else:
            return handle_frontend_error("normalize data", Exception(result.get("error", "Unknown error")), **build_frontend_context("normalize_source_data"))

    except Exception as e:
        return handle_frontend_error("normalize data", e, **build_frontend_context("normalize_source_data"))


@app.post("/api/source-agent/analyze")
async def analyze_source_code(req: dict):
    """Analyze code for API endpoints and patterns.

    Accepts code text and performs static analysis to identify
    API endpoints, architectural patterns, and integration points.
    """
    try:
        from .modules.source_agent_monitor import source_agent_monitor

        text = req.get("text")

        if not text:
            return handle_frontend_error("analyze code", ValueError("text is required"), **build_frontend_context("analyze_source_code"))

        result = await source_agent_monitor.analyze_code(text=text)

        if result.get("success"):
            return create_frontend_success_response(
                "code analyzed successfully",
                {
                    "analysis_id": result.get("analysis_id"),
                    "analysis": result.get("analysis"),
                    "endpoint_count": result.get("endpoint_count"),
                    "patterns_found": result.get("patterns_found"),
                    "response": result.get("response")
                },
                **build_frontend_context("analyze_source_code")
            )
        else:
            return handle_frontend_error("analyze code", Exception(result.get("error", "Unknown error")), **build_frontend_context("analyze_source_code"))

    except Exception as e:
        return handle_frontend_error("analyze code", e, **build_frontend_context("analyze_source_code"))


@app.get("/api/source-agent/fetches")
async def get_fetch_history(limit: int = 20):
    """Get document fetch history.

    Returns cached fetch history with optional limit parameter.
    Useful for analyzing fetch success rates and source performance.
    """
    try:
        from .modules.source_agent_monitor import source_agent_monitor
        history = source_agent_monitor.get_fetch_history(limit=limit)
        return create_frontend_success_response(
            "fetch history retrieved",
            history,
            **build_frontend_context("get_fetch_history")
        )
    except Exception as e:
        return handle_frontend_error("get fetch history", e, **build_frontend_context("get_fetch_history"))


@app.get("/api/source-agent/normalizations")
async def get_normalization_history(limit: int = 20):
    """Get data normalization history.

    Returns cached normalization history with optional limit parameter.
    Useful for analyzing normalization success rates and data quality.
    """
    try:
        from .modules.source_agent_monitor import source_agent_monitor
        history = source_agent_monitor.get_normalization_history(limit=limit)
        return create_frontend_success_response(
            "normalization history retrieved",
            history,
            **build_frontend_context("get_normalization_history")
        )
    except Exception as e:
        return handle_frontend_error("get normalization history", e, **build_frontend_context("get_normalization_history"))


@app.get("/api/source-agent/analyses")
async def get_analysis_history(limit: int = 20):
    """Get code analysis history.

    Returns cached analysis history with optional limit parameter.
    Useful for analyzing code patterns and endpoint detection accuracy.
    """
    try:
        from .modules.source_agent_monitor import source_agent_monitor
        history = source_agent_monitor.get_analysis_history(limit=limit)
        return create_frontend_success_response(
            "analysis history retrieved",
            history,
            **build_frontend_context("get_analysis_history")
        )
    except Exception as e:
        return handle_frontend_error("get analysis history", e, **build_frontend_context("get_analysis_history"))


# ============================================================================
# SERVICES OVERVIEW API ENDPOINTS
# ============================================================================

@app.get("/api/services/overview")
async def get_services_overview():
    """Get comprehensive overview of all services in the ecosystem.

    Returns system-wide health metrics, service status, and categorized
    service information for monitoring the entire LLM Documentation Ecosystem.
    """
    try:
        from .modules.services_overview_monitor import services_overview_monitor
        overview_data = await services_overview_monitor.get_services_overview()
        return create_frontend_success_response(
            "services overview retrieved",
            overview_data,
            **build_frontend_context("get_services_overview")
        )
    except Exception as e:
        return handle_frontend_error("get services overview", e, **build_frontend_context("get_services_overview"))


@app.get("/api/services/overview/{service_name}")
async def get_service_health_details(service_name: str):
    """Get detailed health information for a specific service.

    Returns comprehensive health data and status information for the
    specified service, useful for detailed troubleshooting and monitoring.
    """
    try:
        from .modules.services_overview_monitor import services_overview_monitor
        health_data = await services_overview_monitor.get_service_health_details(service_name)
        return create_frontend_success_response(
            f"service {service_name} health details retrieved",
            health_data,
            **build_frontend_context("get_service_health_details")
        )
    except Exception as e:
        return handle_frontend_error("get service health details", e, **build_frontend_context("get_service_health_details"))


# ============================================================================
# CLI SERVICE API ENDPOINTS
# ============================================================================

@app.get("/api/cli/status")
async def get_cli_status():
    """Get CLI service health status.

    Returns health information and availability status for the CLI service,
    including whether the CLI executable is accessible and functional.
    """
    try:
        from .modules.cli_monitor import cli_monitor
        health_data = await cli_monitor.get_cli_health()
        return create_frontend_success_response(
            "CLI status retrieved",
            health_data,
            **build_frontend_context("get_cli_status")
        )
    except Exception as e:
        return handle_frontend_error("get CLI status", e, **build_frontend_context("get_cli_status"))


@app.post("/api/cli/execute")
async def execute_cli_command(req: dict):
    """Execute a CLI command.

    Accepts a command string and optional arguments, executes the CLI command,
    and returns the stdout, stderr, and exit code from the execution.
    """
    try:
        from .modules.cli_monitor import cli_monitor

        command = req.get("command", "").strip()
        raw_args = req.get("args", [])
        session_id = req.get("session_id")

        if not command:
            return handle_frontend_error("execute CLI command", ValueError("command is required"), **build_frontend_context("execute_cli_command"))

        # Parse command string into command and args
        parts = command.split()
        if len(parts) > 1:
            cmd = parts[0]
            args = parts[1:] + raw_args
        else:
            cmd = parts[0]
            args = raw_args

        result = await cli_monitor.execute_cli_command(cmd, args, session_id)

        return create_frontend_success_response(
            "CLI command executed",
            {"result": result},
            **build_frontend_context("execute_cli_command")
        )

    except Exception as e:
        return handle_frontend_error("execute CLI command", e, **build_frontend_context("execute_cli_command"))


@app.get("/api/cli/commands")
async def get_cli_commands():
    """Get available CLI commands and help information.

    Returns a list of all available CLI commands with descriptions
    and usage examples for the web interface.
    """
    try:
        from .modules.cli_monitor import cli_monitor
        commands_data = await cli_monitor.get_available_commands()
        return create_frontend_success_response(
            "CLI commands retrieved",
            commands_data,
            **build_frontend_context("get_cli_commands")
        )
    except Exception as e:
        return handle_frontend_error("get CLI commands", e, **build_frontend_context("get_cli_commands"))


@app.get("/api/cli/history")
async def get_cli_command_history(limit: int = 20):
    """Get CLI command execution history.

    Returns recent command executions with their results, useful for
    auditing CLI usage and troubleshooting command issues.
    """
    try:
        from .modules.cli_monitor import cli_monitor
        history = cli_monitor.get_command_history(limit=limit)
        return create_frontend_success_response(
            "CLI command history retrieved",
            {"history": history},
            **build_frontend_context("get_cli_command_history")
        )
    except Exception as e:
        return handle_frontend_error("get CLI command history", e, **build_frontend_context("get_cli_command_history"))


@app.post("/api/cli/history/clear")
async def clear_cli_command_history():
    """Clear the CLI command execution history.

    Removes all stored command execution history from memory.
    Useful for privacy and performance management.
    """
    try:
        from .modules.cli_monitor import cli_monitor
        success = cli_monitor.clear_command_history()
        return create_frontend_success_response(
            "CLI command history cleared",
            {"cleared": success},
            **build_frontend_context("clear_cli_command_history")
        )
    except Exception as e:
        return handle_frontend_error("clear CLI command history", e, **build_frontend_context("clear_cli_command_history"))


@app.get("/api/cli/prompts")
async def get_cli_prompts(category: Optional[str] = None):
    """Get prompts via CLI interface.

    Uses the CLI service to retrieve prompt listings, providing
    an alternative interface to the prompt store.
    """
    try:
        from .modules.cli_monitor import cli_monitor
        result = await cli_monitor.get_prompt_list(category=category)
        return create_frontend_success_response(
            "prompts retrieved via CLI",
            result,
            **build_frontend_context("get_cli_prompts")
        )
    except Exception as e:
        return handle_frontend_error("get prompts via CLI", e, **build_frontend_context("get_cli_prompts"))


@app.get("/api/cli/prompts/{category}/{name}")
async def get_cli_prompt_details(category: str, name: str, content: Optional[str] = None):
    """Get specific prompt details via CLI interface.

    Uses the CLI service to retrieve individual prompt details,
    including optional content variable substitution.
    """
    try:
        from .modules.cli_monitor import cli_monitor
        result = await cli_monitor.get_prompt_details(category=category, name=name, content=content)
        return create_frontend_success_response(
            "prompt details retrieved via CLI",
            result,
            **build_frontend_context("get_cli_prompt_details")
        )
    except Exception as e:
        return handle_frontend_error("get prompt details via CLI", e, **build_frontend_context("get_cli_prompt_details"))


@app.post("/api/cli/test-integration")
async def run_cli_integration_tests():
    """Run integration tests via CLI interface.

    Executes the CLI service's integration testing functionality,
    providing comprehensive cross-service validation.
    """
    try:
        from .modules.cli_monitor import cli_monitor
        result = await cli_monitor.run_integration_tests()
        return create_frontend_success_response(
            "CLI integration tests completed",
            result,
            **build_frontend_context("run_cli_integration_tests")
        )
    except Exception as e:
        return handle_frontend_error("run CLI integration tests", e, **build_frontend_context("run_cli_integration_tests"))


if __name__ == "__main__":
    """Run the Frontend service directly."""
    import uvicorn
    import os

    # Enable auto-reload in development
    is_dev = os.getenv("ENVIRONMENT", "production") == "development"

    uvicorn.run(
        "main:app" if is_dev else app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info",
        reload=is_dev,
        reload_dirs=["services/frontend"] if is_dev else None
    )
