"""Main UI handlers for Frontend service.

Handles general dashboard functionality and main page rendering.
"""
from typing import Dict, Any, Optional
from fastapi.responses import HTMLResponse

from ..shared_utils import (
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


class MainUIHandlers:
    """Handles main UI page rendering and general dashboard functionality."""

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
            return handle_frontend_error("render owner coverage", e, **build_frontend_context("render_owner_coverage"))

    @staticmethod
    def handle_topics() -> HTMLResponse:
        """Render topics collections page."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("orchestrator", "/reports/topics", clients=clients)
            html = render_topics_html(data)
            return create_html_response(html, "Topics Collections")
        except Exception as e:
            return handle_frontend_error("render topics", e, **build_frontend_context("render_topics"))

    @staticmethod
    def handle_confluence_consolidation() -> HTMLResponse:
        """Render confluence consolidation report page."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("analysis-service", "/reports/confluence/consolidation", clients=clients)
            html = render_consolidation_list(data)
            return create_html_response(html, "Confluence Consolidation Report")
        except Exception as e:
            return handle_frontend_error("render confluence consolidation", e, **build_frontend_context("render_confluence_consolidation"))

    @staticmethod
    def handle_jira_staleness(min_confidence: float = 0.0, min_duplicate_confidence: float = 0.0, limit: int = 50, summarize: bool = False) -> HTMLResponse:
        """Render Jira staleness report page."""
        try:
            validate_frontend_request({
                "min_confidence": min_confidence,
                "min_duplicate_confidence": min_duplicate_confidence,
                "limit": limit
            })

            clients = get_frontend_clients()
            params = {
                "min_confidence": min_confidence,
                "min_duplicate_confidence": min_duplicate_confidence,
                "limit": limit,
                "summarize": summarize
            }

            data = fetch_service_data("analysis-service", "/reports/jira/staleness", clients=clients, params=params)
            html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jira Staleness Report - LLM Documentation Ecosystem</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .filters {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .filter-row {{
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }}
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        label {{
            font-weight: 600;
            color: #495057;
        }}
        input, select {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        .btn {{
            background: #17a2b8;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn:hover {{
            background: #138496;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .data-table th,
        .data-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        .data-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        .data-table tr:hover {{
            background: #f8f9fa;
        }}
        .badge {{
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 2px 5px 2px 0;
        }}
        .badge.high {{
            background: #dc3545;
        }}
        .badge.medium {{
            background: #ffc107;
            color: black;
        }}
        .badge.low {{
            background: #28a745;
        }}
        .stale {{
            background-color: #fff3cd;
        }}
        .very-stale {{
            background-color: #ffeaa7;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Jira Staleness Report</h1>
            <p>Identify stale Jira tickets requiring review or closure</p>
        </div>

        <div class="filters">
            <form id="filter-form">
                <div class="filter-row">
                    <div class="filter-group">
                        <label for="min_confidence">Min Confidence:</label>
                        <input type="number" id="min_confidence" name="min_confidence" step="0.1" min="0" max="1" value="{min_confidence}">
                    </div>
                    <div class="filter-group">
                        <label for="min_duplicate_confidence">Min Duplicate Confidence:</label>
                        <input type="number" id="min_duplicate_confidence" name="min_duplicate_confidence" step="0.1" min="0" max="1" value="{min_duplicate_confidence}">
                    </div>
                    <div class="filter-group">
                        <label for="limit">Limit:</label>
                        <input type="number" id="limit" name="limit" min="1" max="1000" value="{limit}">
                    </div>
                    <div class="filter-group">
                        <label for="summarize">
                            <input type="checkbox" id="summarize" name="summarize" {'checked' if summarize else ''}> Summarize
                        </label>
                    </div>
                    <button type="submit" class="btn">Apply Filters</button>
                </div>
            </form>
        </div>

        <div id="content">
"""

            if summarize:
                # Summary view
                tickets = data.get("tickets", [])
                total = len(tickets)
                stale_count = len([t for t in tickets if t.get("days_since_update", 0) > 90])
                very_stale_count = len([t for t in tickets if t.get("days_since_update", 0) > 180])

                html += f"""
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #17a2b8;">
                    <div style="font-size: 2em; font-weight: bold; color: #17a2b8;">{total}</div>
                    <div style="color: #666;">Total Tickets</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #ffc107;">
                    <div style="font-size: 2em; font-weight: bold; color: #ffc107;">{stale_count}</div>
                    <div style="color: #666;">Stale (>90 days)</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #dc3545;">
                    <div style="font-size: 2em; font-weight: bold; color: #dc3545;">{very_stale_count}</div>
                    <div style="color: #666;">Very Stale (>180 days)</div>
                </div>
            </div>
"""
            else:
                # Detailed table view
                tickets = data.get("tickets", [])
                html += f"""
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Ticket Key</th>
                        <th>Summary</th>
                        <th>Assignee</th>
                        <th>Status</th>
                        <th>Last Updated</th>
                        <th>Days Since Update</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>
"""

                for ticket in tickets:
                    days_since = ticket.get("days_since_update", 0)
                    row_class = ""
                    if days_since > 180:
                        row_class = "very-stale"
                    elif days_since > 90:
                        row_class = "stale"

                    confidence = ticket.get("confidence", 0)
                    confidence_class = "low"
                    if confidence > 0.7:
                        confidence_class = "high"
                    elif confidence > 0.4:
                        confidence_class = "medium"

                    html += f"""
                    <tr class="{row_class}">
                        <td><a href="{ticket.get('url', '#')}" target="_blank">{ticket.get('key', 'N/A')}</a></td>
                        <td>{ticket.get('summary', 'N/A')}</td>
                        <td>{ticket.get('assignee', 'Unassigned')}</td>
                        <td>{ticket.get('status', 'Unknown')}</td>
                        <td>{ticket.get('last_updated', 'Unknown')}</td>
                        <td>{days_since} days</td>
                        <td><span class="badge {confidence_class}">{confidence:.2f}</span></td>
                    </tr>
"""

                html += """
                </tbody>
            </table>
"""

            html += """
        </div>
    </div>

    <script>
        document.getElementById('filter-form').addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const params = new URLSearchParams();

            for (let [key, value] of formData.entries()) {
                if (key === 'summarize') {
                    if (this.querySelector('#summarize').checked) {
                        params.append(key, 'true');
                    }
                } else {
                    params.append(key, value);
                }
            }

            window.location.href = '/reports/jira/staleness?' + params.toString();
        });
    </script>
</body>
</html>
"""
            return create_html_response(html, "Jira Staleness Report")
        except Exception as e:
            return handle_frontend_error("render jira staleness", e, **build_frontend_context("render_jira_staleness"))

    @staticmethod
    def handle_duplicate_clusters() -> HTMLResponse:
        """Render duplicate clusters report page."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("orchestrator", "/reports/duplicate_clusters", clients=clients)
            html = render_clusters(data)
            return create_html_response(html, "Duplicate Clusters Report")
        except Exception as e:
            return handle_frontend_error("render duplicate clusters", e, **build_frontend_context("render_duplicate_clusters"))

    @staticmethod
    def handle_search(q: str = "kubernetes") -> HTMLResponse:
        """Render search results page."""
        try:
            q = sanitize_input(q)
            clients = get_frontend_clients()
            data = fetch_service_data("doc-store", "/search", clients=clients, params={"q": q})
            html = render_search_results(data, q)
            return create_html_response(html, f"Search Results: {q}")
        except Exception as e:
            return handle_frontend_error("render search", e, **build_frontend_context("render_search"))

    @staticmethod
    def handle_docs_quality() -> HTMLResponse:
        """Render document quality analysis page."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("doc-store", "/quality", clients=clients)
            html = render_docs_quality(data)
            return create_html_response(html, "Document Quality Analysis")
        except Exception as e:
            return handle_frontend_error("render docs quality", e, **build_frontend_context("render_docs_quality"))

    @staticmethod
    def handle_findings() -> HTMLResponse:
        """Render findings page."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("consistency-engine", "/findings", clients=clients)
            html = render_findings(data)
            return create_html_response(html, "Findings")
        except Exception as e:
            return handle_frontend_error("render findings", e, **build_frontend_context("render_findings"))

    @staticmethod
    def handle_findings_by_severity() -> HTMLResponse:
        """Render findings grouped by severity."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("consistency-engine", "/findings", clients=clients)
            html = render_counts(data, "severity")
            return create_html_response(html, "Findings by Severity")
        except Exception as e:
            return handle_frontend_error("render findings by severity", e, **build_frontend_context("render_findings_by_severity"))

    @staticmethod
    def handle_findings_by_type() -> HTMLResponse:
        """Render findings grouped by type."""
        try:
            clients = get_frontend_clients()
            data = fetch_service_data("consistency-engine", "/findings", clients=clients)
            html = render_counts(data, "type")
            return create_html_response(html, "Findings by Type")
        except Exception as e:
            return handle_frontend_error("render findings by type", e, **build_frontend_context("render_findings_by_type"))

    @staticmethod
    def handle_report() -> HTMLResponse:
        """Render comprehensive report page."""
        try:
            clients = get_frontend_clients()
            findings_data = fetch_service_data("consistency-engine", "/findings", clients=clients)
            quality_data = fetch_service_data("doc-store", "/quality", clients=clients)
            topics_data = fetch_service_data("orchestrator", "/reports/topics", clients=clients)

            html = render_report_page(findings_data, quality_data, topics_data)
            return create_html_response(html, "Comprehensive Report")
        except Exception as e:
            return handle_frontend_error("render report", e, **build_frontend_context("render_report"))
