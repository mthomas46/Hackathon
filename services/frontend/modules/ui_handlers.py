"""UI handlers for Frontend service.

Handles the complex logic for different UI pages and endpoints.
"""
from typing import Dict, Any, Optional
from fastapi.responses import HTMLResponse

from .shared_utils import (
    get_frontend_clients,
    fetch_service_data,
    create_html_response,
    handle_frontend_error,
    build_frontend_context,
    validate_frontend_request,
    sanitize_input
)
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


class UIHandlers:
    """Handles UI page rendering and data fetching."""

    @staticmethod
    def handle_index() -> HTMLResponse:
        """Render the main frontend index page."""
        try:
            html = render_index()
            return create_html_response(html, "LLM Documentation Ecosystem")
        except Exception as e:
            return handle_frontend_error("render index page", e, **build_frontend_context("render_index"))

    @staticmethod
    def handle_owner_coverage() -> HTMLResponse:
        """Render owner coverage report page."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("orchestrator", "/reports/owner_coverage", clients=clients)
            cov = data.get("coverage", {})
            html = render_owner_coverage_table(cov)
            return create_html_response(html, "Owner Coverage Report")
        except Exception as e:
            return handle_frontend_error("fetch owner coverage", e, **build_frontend_context("owner_coverage"))

    @staticmethod
    def handle_topics() -> HTMLResponse:
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

    @staticmethod
    def handle_confluence_consolidation() -> HTMLResponse:
        """Render Confluence consolidation report page."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("orchestrator", "/reports/confluence/consolidation", clients=clients)
            items = data.get("items", [])
            html = render_consolidation_list(items)
            return create_html_response(html, "Confluence Consolidation Report")
        except Exception as e:
            return handle_frontend_error("fetch confluence consolidation", e, **build_frontend_context("confluence_consolidation"))

    @staticmethod
    def handle_jira_staleness(min_confidence: float = 0.0, min_duplicate_confidence: float = 0.0, limit: int = 50, summarize: bool = False) -> HTMLResponse:
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

    @staticmethod
    def handle_duplicate_clusters() -> HTMLResponse:
        """Render duplicate clusters report page."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("reporting", "/reports/duplicates/clusters", clients=clients)
            clusters = data.get("clusters", [])
            html = render_clusters(clusters)
            return create_html_response(html, "Duplicate Clusters Report")
        except Exception as e:
            return handle_frontend_error("fetch duplicate clusters", e, **build_frontend_context("duplicate_clusters"))

    @staticmethod
    def handle_search(q: str = "kubernetes") -> HTMLResponse:
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

    @staticmethod
    def handle_docs_quality() -> HTMLResponse:
        """Render document quality analysis page."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("doc-store", "/documents/quality", clients=clients)
            items = data.get("items", [])
            html = render_docs_quality(items)
            return create_html_response(html, "Document Quality Analysis")
        except Exception as e:
            return handle_frontend_error("fetch document quality", e, **build_frontend_context("docs_quality"))

    @staticmethod
    def handle_findings() -> HTMLResponse:
        """Render findings page with all current findings."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("consistency-engine", "/findings", clients=clients)
            items = data.get("findings", [])
            html = render_findings(items)
            return create_html_response(html, "Current Findings")
        except Exception as e:
            return handle_frontend_error("fetch findings", e, **build_frontend_context("findings"))

    @staticmethod
    def handle_findings_by_severity() -> HTMLResponse:
        """Render findings grouped by severity level."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("reporting", "/reports/trends", clients=clients)
            items = data.get("by_severity", {})
            html = render_counts("Findings by Severity", items)
            return create_html_response(html, "Findings by Severity")
        except Exception as e:
            return handle_frontend_error("fetch findings by severity", e, **build_frontend_context("findings_severity"))

    @staticmethod
    def handle_findings_by_type() -> HTMLResponse:
        """Render findings grouped by type."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("reporting", "/reports/trends", clients=clients)
            items = data.get("by_type", {})
            html = render_counts("Findings by Type", items)
            return create_html_response(html, "Findings by Type")
        except Exception as e:
            return handle_frontend_error("fetch findings by type", e, **build_frontend_context("findings_type"))

    @staticmethod
    def handle_report() -> HTMLResponse:
        """Render comprehensive report page with all metrics."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("reporting", "/reports/generate", clients=clients)
            html = render_report_page(data)
            return create_html_response(html, "Comprehensive Report")
        except Exception as e:
            return handle_frontend_error("generate report", e, **build_frontend_context("generate_report"))


# Create singleton instance
ui_handlers = UIHandlers()
