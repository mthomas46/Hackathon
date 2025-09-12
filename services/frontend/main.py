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
    try:
        html = render_index()
        return create_html_response(html, "LLM Documentation Ecosystem")
    except Exception as e:
        return handle_frontend_error("render index page", e, **build_frontend_context("render_index"))


@app.get("/owner-coverage")
async def ui_owner_coverage():
    """Render owner coverage report page."""
    try:
        clients = get_frontend_clients()
        data = fetch_service_data("orchestrator", "/reports/owner_coverage", clients=clients)
        cov = data.get("coverage", {})
        html = render_owner_coverage_table(cov)
        return create_html_response(html, "Owner Coverage Report")
    except Exception as e:
        return handle_frontend_error("fetch owner coverage", e, **build_frontend_context("owner_coverage"))


@app.get("/topics")
async def ui_topics():
    """Render topics overview page with document freshness analysis."""
    try:
        clients = get_frontend_clients()
        data = fetch_service_data("doc-store", "/documents/quality", clients=clients)
        items = data.get("items", [])

        topics = {
            "kubernetes": [],
            "openapi": [],
            "redis": [],
            "postgres": [],
            "fastapi": [],
        }

        for item in items:
            meta = item.get("metadata") or {}
            title = (meta.get("title") or meta.get("name") or "").lower()
            for topic in topics.keys():
                if topic in title:
                    stale_days = item.get("stale_days", 0)
                    freshness = "fresh" if stale_days < 60 else ("stale" if stale_days > 180 else "aging")
                    topics[topic].append((item.get("id"), freshness))

        html = render_topics_html(topics)
        return create_html_response(html, "Topics Overview")
    except Exception as e:
        return handle_frontend_error("fetch topics data", e, **build_frontend_context("topics"))


@app.get("/confluence/consolidation")
async def ui_confluence_consolidation():
    """Render Confluence consolidation report page."""
    try:
        clients = get_frontend_clients()
        data = fetch_service_data("orchestrator", "/reports/confluence/consolidation", clients=clients)
        items = data.get("items", [])
        html = render_consolidation_list(items)
        return create_html_response(html, "Confluence Consolidation Report")
    except Exception as e:
        return handle_frontend_error("fetch confluence consolidation", e, **build_frontend_context("confluence_consolidation"))


@app.get("/reports/jira/staleness")
async def ui_jira_staleness(min_confidence: float = 0.0, min_duplicate_confidence: float = 0.0, limit: int = 50, summarize: bool = False):
    """Render Jira staleness report page with filtering options."""
    try:
        validate_frontend_request({"min_confidence": min_confidence, "min_duplicate_confidence": min_duplicate_confidence, "limit": limit})

        endpoint = "/reports/jira/staleness"
        params = {
            "min_confidence": min_confidence,
            "min_duplicate_confidence": min_duplicate_confidence,
            "limit": limit,
            "summarize": "true" if summarize else "false"
        }

        clients = get_frontend_clients()
        data = fetch_service_data("orchestrator", endpoint, params=params, clients=clients)
        items = data.get("items", [])
        html = render_consolidation_list(items)
        return create_html_response(html, "Jira Staleness Report")
    except Exception as e:
        context = build_frontend_context("jira_staleness", min_confidence=min_confidence, limit=limit)
        return handle_frontend_error("fetch jira staleness", e, **context)


@app.get("/duplicates/clusters")
async def ui_duplicate_clusters():
    """Render duplicate clusters report page."""
    try:
        clients = get_frontend_clients()
        data = fetch_service_data("reporting", "/reports/duplicates/clusters", clients=clients)
        clusters = data.get("clusters", [])
        html = render_clusters(clusters)
        return create_html_response(html, "Duplicate Clusters Report")
    except Exception as e:
        return handle_frontend_error("fetch duplicate clusters", e, **build_frontend_context("duplicate_clusters"))


@app.get("/search")
async def ui_search(q: str = "kubernetes"):
    """Render search results page for document queries."""
    try:
        # Sanitize user input to prevent XSS attacks
        safe_q = sanitize_input(q)
        validate_frontend_request({"q": safe_q}, ["q"])

        params = {"q": safe_q}
        clients = get_frontend_clients()
        data = fetch_service_data("doc-store", "/search", params=params, clients=clients)
        items = data.get("items", [])
        html = render_search_results(safe_q, items)
        return create_html_response(html, f"Search Results for '{safe_q}'")
    except Exception as e:
        context = build_frontend_context("search", query=safe_q)
        return handle_frontend_error("perform search", e, **context)


@app.get("/docs/quality")
async def ui_docs_quality():
    """Render document quality analysis page."""
    try:
        clients = get_frontend_clients()
        data = fetch_service_data("doc-store", "/documents/quality", clients=clients)
        items = data.get("items", [])
        html = render_docs_quality(items)
        return create_html_response(html, "Document Quality Analysis")
    except Exception as e:
        return handle_frontend_error("fetch document quality", e, **build_frontend_context("docs_quality"))


@app.get("/findings")
async def ui_findings():
    """Render findings page with all current findings."""
    try:
        clients = get_frontend_clients()
        data = fetch_service_data("consistency-engine", "/findings", clients=clients)
        items = data.get("findings", [])
        html = render_findings(items)
        return create_html_response(html, "Current Findings")
    except Exception as e:
        return handle_frontend_error("fetch findings", e, **build_frontend_context("findings"))


@app.get("/findings/by-severity")
async def ui_findings_by_severity():
    """Render findings grouped by severity level."""
    try:
        clients = get_frontend_clients()
        data = fetch_service_data("reporting", "/reports/trends", clients=clients)
        items = data.get("by_severity", {})
        html = render_counts("Findings by Severity", items)
        return create_html_response(html, "Findings by Severity")
    except Exception as e:
        return handle_frontend_error("fetch findings by severity", e, **build_frontend_context("findings_severity"))


@app.get("/findings/by-type")
async def ui_findings_by_type():
    """Render findings grouped by type."""
    try:
        clients = get_frontend_clients()
        data = fetch_service_data("reporting", "/reports/trends", clients=clients)
        items = data.get("by_type", {})
        html = render_counts("Findings by Type", items)
        return create_html_response(html, "Findings by Type")
    except Exception as e:
        return handle_frontend_error("fetch findings by type", e, **build_frontend_context("findings_type"))


@app.get("/report")
async def ui_report():
    """Render comprehensive report page with all metrics."""
    try:
        clients = get_frontend_clients()
        data = fetch_service_data("reporting", "/reports/generate", clients=clients)
        html = render_report_page(data)
        return create_html_response(html, "Comprehensive Report")
    except Exception as e:
        return handle_frontend_error("generate report", e, **build_frontend_context("generate_report"))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)