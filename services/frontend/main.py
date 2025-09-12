"""Frontend Service

Minimal HTML UI to surface findings and trigger reports via
Consistency Engine and Reporting services.

Endpoints (HTML):
- GET /, /findings, /report, /findings/by-severity, /findings/by-type
- /search, /docs/quality, /confluence/consolidation, /topics, /owner-coverage
- /reports/jira/staleness, /duplicates/clusters

Dependencies: Reporting, Consistency Engine, Doc Store; shared render helpers in services/frontend/utils.py.
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


# ============================================================================
# APP INITIALIZATION - Using shared patterns for consistency
# ============================================================================

# Initialize FastAPI app with shared middleware and error handlers
app = FastAPI(title="Frontend", version="1.0.0")

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.FRONTEND)
install_error_handlers(app)

# Register standardized health endpoints
register_health_endpoints(app, ServiceNames.FRONTEND, "1.0.0")


@app.get("/info")
async def info():
    """Get service information and configuration."""
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
    """Get effective configuration from environment."""
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
    """Get frontend service metrics."""
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
    """Render the main frontend index page."""
    return ui_handlers.handle_index()


@app.get("/owner-coverage")
async def ui_owner_coverage():
    """Render owner coverage report page."""
    return ui_handlers.handle_owner_coverage()


@app.get("/topics")
async def ui_topics():
    """Render topics overview page with document freshness analysis."""
    return ui_handlers.handle_topics()


@app.get("/confluence/consolidation")
async def ui_confluence_consolidation():
    """Render Confluence consolidation report page."""
    return ui_handlers.handle_confluence_consolidation()


@app.get("/reports/jira/staleness")
async def ui_jira_staleness(min_confidence: float = 0.0, min_duplicate_confidence: float = 0.0, limit: int = 50, summarize: bool = False):
    """Render Jira staleness report page with filtering options."""
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)