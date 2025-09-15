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
- GET /doc-store/browser: Doc-store data browser for document exploration
- GET /prompt-store/browser: Prompt-store data browser for prompt exploration
- GET /code-analyzer/dashboard: Code analyzer service dashboard

Endpoints (API):
- GET /api/workflows/jobs/status: Active workflows and jobs status for visualization
- GET /api/code-analyzer/status: Get comprehensive code analyzer service status
- POST /api/code-analyzer/analyze-text: Analyze text content for code quality and issues
- POST /api/code-analyzer/analyze-files: Analyze multiple files for code quality and issues
- POST /api/code-analyzer/security-scan: Perform security scan on code
- POST /api/code-analyzer/style-check: Check code style compliance
- GET /api/code-analyzer/style-examples: Get code style examples
- GET /api/code-analyzer/history: Get code analyzer analysis history

Responsibilities:
- Provide HTML UI for viewing documentation consistency findings and reports
- Aggregate data from multiple backend services (Reporting, Consistency Engine, Doc Store, Orchestrator, Log Collector, Prompt Store, Analysis Service, Code Analyzer)
- Render interactive dashboards for document quality metrics and analysis
- Support filtering and searching across documentation collections
- Display owner coverage and staleness reports for Jira tickets
- Show topic collections and duplicate document clusters
- Provide API endpoints for workflow and job monitoring and visualization
- Enable read-only browsing and exploration of stored documents and prompts
- Support data discovery through search, filtering, and pagination interfaces
- Enable code analysis, security scanning, and style checking capabilities
- Provide interactive code quality assessment and vulnerability detection

Dependencies: Reporting, Consistency Engine, Doc Store, Orchestrator, Log Collector, Prompt Store, Analysis Service, Code Analyzer; shared render helpers.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import Optional
import os

# ============================================================================
# SHARED MODULES - Leveraging centralized functionality for consistency
# ============================================================================
from services.shared.health import register_health_endpoints
from services.shared.constants_new import ServiceNames, EnvVars
from services.shared.utilities import setup_common_middleware
from services.shared.error_handling import install_error_handlers

# ============================================================================
# LOCAL MODULES - Service-specific functionality
# ============================================================================
from .modules.shared_utils import (
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
from .modules.ui_handlers import ui_handlers
from .modules.summarizer_cache import get_cached_summarizer_data, record_summarizer_job
from .modules.log_cache import (
    get_cached_logs_data,
    fetch_logs_from_collector,
    fetch_log_stats_from_collector,
    stream_logs,
    analyze_log_patterns
)
from .modules.data_browser import (
    data_browser,
    get_doc_store_summary,
    get_prompt_store_summary
)
from .modules.orchestrator_monitor import (
    orchestrator_monitor,
    get_orchestrator_summary
)
from .modules.analysis_monitor import analysis_monitor
from .modules.bedrock_proxy_monitor import bedrock_proxy_monitor
from .modules.code_analyzer_monitor import code_analyzer_monitor

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

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.FRONTEND)
install_error_handlers(app)

# Register standardized health endpoints
register_health_endpoints(app, ServiceNames.FRONTEND, SERVICE_VERSION)


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


@app.get("/")
async def index():
    """Render the main frontend index page.

    Returns the main dashboard HTML page with navigation links to all
    available UI views for documentation analysis and reporting.
    """
    return ui_handlers.handle_index()


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


@app.get("/doc-store/browser")
async def ui_doc_store_browser():
    """Render doc-store data browser for document exploration.

    Provides a read-only interface for browsing documents, analyses,
    quality metrics, and style examples stored in the doc-store.
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


@app.get("/api/doc-store/status")
async def get_doc_store_status():
    """Get comprehensive doc-store status and summary for visualization.

    Returns cached document data, analyses, quality metrics, and style examples
    for dashboard visualization and data browsing.
    """
    try:
        summary = get_doc_store_summary()

        return create_frontend_success_response(
            "doc-store status retrieved",
            summary,
            **build_frontend_context("get_doc_store_status")
        )

    except Exception as e:
        return handle_frontend_error("get doc-store status", e, **build_frontend_context("get_doc_store_status"))


@app.get("/api/doc-store/documents")
async def get_doc_store_documents(
    limit: int = 20,
    offset: int = 0,
    force_refresh: bool = False
):
    """Get documents from doc-store with pagination.

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
        return handle_frontend_error("get doc-store documents", e, **build_frontend_context("get_doc_store_documents"))


@app.get("/api/doc-store/documents/{doc_id}")
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
        return handle_frontend_error("get doc-store document", e, **build_frontend_context("get_doc_store_document"))


@app.get("/api/doc-store/analyses")
async def get_doc_store_analyses(
    document_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    force_refresh: bool = False
):
    """Get analyses from doc-store with optional filtering.

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
        return handle_frontend_error("get doc-store analyses", e, **build_frontend_context("get_doc_store_analyses"))


@app.get("/api/doc-store/quality")
async def get_doc_store_quality(force_refresh: bool = False):
    """Get document quality metrics and analysis.

    Retrieves quality metrics, stale documents, and other health indicators.
    """
    try:
        result = await data_browser.get_doc_store_quality(force_refresh=force_refresh)

        return create_frontend_success_response(
            "doc-store quality metrics retrieved",
            result,
            **build_frontend_context("get_doc_store_quality")
        )

    except Exception as e:
        return handle_frontend_error("get doc-store quality", e, **build_frontend_context("get_doc_store_quality"))


@app.get("/api/doc-store/style-examples")
async def get_doc_store_style_examples(force_refresh: bool = False):
    """Get style examples by programming language.

    Retrieves code documentation style examples for different languages.
    """
    try:
        result = await data_browser.get_doc_store_style_examples(force_refresh=force_refresh)

        return create_frontend_success_response(
            "doc-store style examples retrieved",
            result,
            **build_frontend_context("get_doc_store_style_examples")
        )

    except Exception as e:
        return handle_frontend_error("get doc-store style examples", e, **build_frontend_context("get_doc_store_style_examples"))


@app.get("/api/doc-store/search")
async def search_doc_store(q: str, limit: int = 20):
    """Search documents in doc-store.

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
        return handle_frontend_error("search doc-store", e, **build_frontend_context("search_doc_store"))


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


if __name__ == "__main__":
    """Run the Frontend service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )