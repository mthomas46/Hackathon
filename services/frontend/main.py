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

Responsibilities:
- Provide HTML UI for viewing documentation consistency findings and reports
- Aggregate data from multiple backend services (Reporting, Consistency Engine, Doc Store)
- Render interactive dashboards for document quality metrics and analysis
- Support filtering and searching across documentation collections
- Display owner coverage and staleness reports for Jira tickets
- Show topic collections and duplicate document clusters

Dependencies: Reporting, Consistency Engine, Doc Store services; shared render helpers.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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



if __name__ == "__main__":
    """Run the Frontend service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )