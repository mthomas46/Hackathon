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

    @staticmethod
    def handle_workflows_status() -> HTMLResponse:
        """Render workflow and job status monitoring page."""
        try:
            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workflow & Job Status - LLM Documentation Ecosystem</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #007bff;
        }
        .status-card.error {
            border-left-color: #dc3545;
        }
        .status-card.success {
            border-left-color: #28a745;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-value {
            font-weight: bold;
            color: #007bff;
        }
        .workflows-list {
            margin-top: 20px;
        }
        .workflow-item {
            background: #f8f9fa;
            margin: 10px 0;
            padding: 10px;
            border-radius: 4px;
            border-left: 3px solid #007bff;
        }
        .workflow-item.completed {
            border-left-color: #28a745;
        }
        .workflow-item.failed {
            border-left-color: #dc3545;
        }
        .workflow-item.running {
            border-left-color: #ffc107;
        }
        .refresh-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            background: #0056b3;
        }
        .loading {
            text-align: center;
            color: #666;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Workflow & Job Status Monitor</h1>
            <p>Real-time monitoring of active workflows and jobs</p>
            <button class="refresh-btn" onclick="refreshStatus()">Refresh Status</button>
        </div>

        <div id="status-container">
            <div class="loading">Loading workflow and job status...</div>
        </div>
    </div>

    <script>
        let statusData = null;

        async function fetchStatus() {
            try {
                const response = await fetch('/api/workflows/jobs/status');
                const data = await response.json();
                statusData = data;
                renderStatus(data);
            } catch (error) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Failed to load status: ' + error.message + '</div>';
            }
        }

        function renderStatus(data) {
            if (!data.success) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Error: ' + data.message + '</div>';
                return;
            }

            const status = data.data;
            const summary = status.summary || {};

            let html = '<div class="status-grid">';

            // Summary metrics
            html += `
                <div class="status-card success">
                    <h3>Workflow Summary</h3>
                    <div class="metric">
                        <span>Total Available:</span>
                        <span class="metric-value">${summary.total_workflows_available || 0}</span>
                    </div>
                    <div class="metric">
                        <span>Active:</span>
                        <span class="metric-value">${summary.active_workflows || 0}</span>
                    </div>
                    <div class="metric">
                        <span>Completed:</span>
                        <span class="metric-value">${summary.completed_workflows || 0}</span>
                    </div>
                    <div class="metric">
                        <span>Failed:</span>
                        <span class="metric-value">${summary.failed_workflows || 0}</span>
                    </div>
                </div>
            `;

            // Infrastructure status
            html += `
                <div class="status-card">
                    <h3>Infrastructure</h3>
                    <div class="metric">
                        <span>Active Sagas:</span>
                        <span class="metric-value">${summary.active_sagas || 0}</span>
                    </div>
                    <div class="metric">
                        <span>Total Services:</span>
                        <span class="metric-value">${summary.total_services || 0}</span>
                    </div>
                </div>
            `;

            html += '</div>';

            // Recent workflow history
            if (status.workflows && status.workflows.history && Array.isArray(status.workflows.history)) {
                html += '<h3>Recent Workflow History</h3><div class="workflows-list">';
                status.workflows.history.slice(0, 10).forEach(workflow => {
                    const statusClass = (workflow.status || 'unknown').toLowerCase();
                    html += `
                        <div class="workflow-item ${statusClass}">
                            <strong>${workflow.workflow_id || 'Unknown'}</strong>
                            <div>Status: ${workflow.status || 'Unknown'}</div>
                            <div>Started: ${workflow.timestamp || 'Unknown'}</div>
                        </div>
                    `;
                });
                html += '</div>';
            }

            // Service registry
            if (status.infrastructure && status.infrastructure.services && Array.isArray(status.infrastructure.services)) {
                html += '<h3>Registered Services</h3><div class="workflows-list">';
                status.infrastructure.services.forEach(service => {
                    html += `
                        <div class="workflow-item">
                            <strong>${service.name || 'Unknown'}</strong>
                            <div>URL: ${service.url || 'Unknown'}</div>
                            <div>Status: ${service.status || 'Unknown'}</div>
                        </div>
                    `;
                });
                html += '</div>';
            }

            document.getElementById('status-container').innerHTML = html;
        }

        function refreshStatus() {
            document.getElementById('status-container').innerHTML =
                '<div class="loading">Loading workflow and job status...</div>';
            fetchStatus();
        }

        // Auto-refresh every 30 seconds
        setInterval(fetchStatus, 30000);

        // Initial load
        fetchStatus();
    </script>
</body>
</html>
            """
            return create_html_response(html, "Workflow & Job Status Monitor")
        except Exception as e:
            return handle_frontend_error("render workflows status page", e, **build_frontend_context("render_workflows_status"))

    @staticmethod
    def handle_summarizer_status() -> HTMLResponse:
        """Render summarizer hub status and process monitoring page."""
        try:
            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Summarizer Hub Status - LLM Documentation Ecosystem</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #28a745;
        }
        .status-card.error {
            border-left-color: #dc3545;
        }
        .status-card.warning {
            border-left-color: #ffc107;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-value {
            font-weight: bold;
            color: #28a745;
        }
        .jobs-list, .prompts-list, .models-list {
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        .job-item, .prompt-item, .model-item {
            background: #f8f9fa;
            margin: 8px 0;
            padding: 12px;
            border-radius: 6px;
            border-left: 3px solid #28a745;
            font-size: 14px;
        }
        .job-item.completed {
            border-left-color: #28a745;
        }
        .job-item.failed {
            border-left-color: #dc3545;
        }
        .prompt-preview {
            font-style: italic;
            color: #666;
            margin: 5px 0;
        }
        .model-stats {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
        }
        .refresh-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            background: #218838;
        }
        .loading {
            text-align: center;
            color: #666;
            padding: 40px;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #dee2e6;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            border-bottom-color: #28a745;
            color: #28a745;
            font-weight: bold;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .consistency-analysis {
            background: #e9ecef;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 13px;
        }
        .provider-badges {
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            margin-top: 5px;
        }
        .badge {
            background: #007bff;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Summarizer Hub Status Monitor</h1>
            <p>Real-time monitoring of summarization processes, prompts, and models</p>
            <button class="refresh-btn" onclick="refreshStatus()">Refresh Status</button>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('overview')">Overview</div>
            <div class="tab" onclick="showTab('jobs')">Recent Jobs</div>
            <div class="tab" onclick="showTab('prompts')">Prompts</div>
            <div class="tab" onclick="showTab('models')">Models</div>
        </div>

        <div id="status-container">
            <div class="loading">Loading summarizer hub status...</div>
        </div>
    </div>

    <script>
        let statusData = null;

        function showTab(tabName) {
            // Update tab styling
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }

        async function fetchStatus() {
            try {
                const response = await fetch('/api/summarizer/status');
                const data = await response.json();
                statusData = data;
                renderStatus(data);
            } catch (error) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Failed to load summarizer status: ' + error.message + '</div>';
            }
        }

        function renderStatus(data) {
            if (!data.success) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Error: ' + data.message + '</div>';
                return;
            }

            const status = data.data;
            const cached = status.cached_data || {};
            const live = status.live_data || {};
            const summary = status.summary || {};

            let html = '';

            // Overview Tab
            html += '<div id="overview-content" class="tab-content active">';

            // Service Status and Summary
            html += '<div class="status-grid">';
            html += `
                <div class="status-card ${live.service_status && live.service_status.status === 'healthy' ? 'success' : 'error'}">
                    <h3>Service Status</h3>
                    <div class="metric">
                        <span>Status:</span>
                        <span class="metric-value">${live.service_status ? live.service_status.status : 'Unknown'}</span>
                    </div>
                    <div class="metric">
                        <span>Version:</span>
                        <span class="metric-value">${live.service_status ? live.service_status.version || 'N/A' : 'N/A'}</span>
                    </div>
                </div>
            `;

            html += `
                <div class="status-card">
                    <h3>Job Summary</h3>
                    <div class="metric">
                        <span>Total Jobs:</span>
                        <span class="metric-value">${summary.total_cached_jobs || 0}</span>
                    </div>
                    <div class="metric">
                        <span>Active Prompts:</span>
                        <span class="metric-value">${summary.active_prompts || 0}</span>
                    </div>
                    <div class="metric">
                        <span>Models Tracked:</span>
                        <span class="metric-value">${summary.models_tracked || 0}</span>
                    </div>
                </div>
            `;

            const perf = cached.performance_metrics || {};
            html += `
                <div class="status-card">
                    <h3>Performance</h3>
                    <div class="metric">
                        <span>Avg Execution Time:</span>
                        <span class="metric-value">${perf.average_execution_time || 0}s</span>
                    </div>
                    <div class="metric">
                        <span>Most Used Provider:</span>
                        <span class="metric-value">${perf.most_used_provider || 'None'}</span>
                    </div>
                </div>
            `;

            html += '</div></div>';

            // Recent Jobs Tab
            html += '<div id="jobs-content" class="tab-content">';
            if (cached.job_history && cached.job_history.length > 0) {
                html += '<h3>Recent Summarization Jobs</h3><div class="jobs-list">';
                cached.job_history.slice(0, 20).forEach(job => {
                    const providersHtml = job.providers.map(p => `<span class="badge">${p}</span>`).join('');
                    html += `
                        <div class="job-item completed">
                            <strong>Job ${job.job_id}</strong>
                            <div>Text Length: ${job.text_length} chars</div>
                            <div class="provider-badges">Providers: ${providersHtml}</div>
                            <div>Execution Time: ${job.execution_time || 'N/A'}s</div>
                            <div>Timestamp: ${new Date(job.timestamp).toLocaleString()}</div>
                        </div>
                    `;
                });
                html += '</div>';
            } else {
                html += '<p>No job history available</p>';
            }
            html += '</div>';

            // Prompts Tab
            html += '<div id="prompts-content" class="tab-content">';
            if (cached.active_prompts && cached.active_prompts.length > 0) {
                html += '<h3>Active Prompts</h3><div class="prompts-list">';
                cached.active_prompts.forEach(prompt => {
                    const providersHtml = prompt.providers.map(p => `<span class="badge">${p}</span>`).join('');
                    const modelsHtml = prompt.models.map(m => `<span class="badge">${m}</span>`).join('');
                    html += `
                        <div class="prompt-item">
                            <div class="prompt-preview">"${prompt.text}"</div>
                            <div>Usage Count: ${prompt.usage_count}</div>
                            <div class="provider-badges">Providers: ${providersHtml}</div>
                            <div class="provider-badges">Models: ${modelsHtml}</div>
                            <div>Last Used: ${new Date(prompt.last_used).toLocaleString()}</div>
                        </div>
                    `;
                });
                html += '</div>';
            } else {
                html += '<p>No prompt data available</p>';
            }
            html += '</div>';

            // Models Tab
            html += '<div id="models-content" class="tab-content">';
            if (cached.model_usage && cached.model_usage.length > 0) {
                html += '<h3>Model Usage Statistics</h3><div class="models-list">';
                cached.model_usage.forEach(model => {
                    html += `
                        <div class="model-item">
                            <strong>${model.provider}:${model.model}</strong>
                            <div class="model-stats">
                                <span>Usage: ${model.usage_count}</span>
                                <span>Avg Time: ${model.average_execution_time.toFixed(2)}s</span>
                                <span>Last Used: ${new Date(model.last_used).toLocaleString()}</span>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
            } else {
                html += '<p>No model usage data available</p>';
            }
            html += '</div>';

            document.getElementById('status-container').innerHTML = html;
        }

        function refreshStatus() {
            document.getElementById('status-container').innerHTML =
                '<div class="loading">Loading summarizer hub status...</div>';
            fetchStatus();
        }

        // Auto-refresh every 30 seconds
        setInterval(fetchStatus, 30000);

        // Initial load
        fetchStatus();
    </script>
</body>
</html>
            """
            return create_html_response(html, "Summarizer Hub Status Monitor")
        except Exception as e:
            return handle_frontend_error("render summarizer status page", e, **build_frontend_context("render_summarizer_status"))

    @staticmethod
    def handle_logs_dashboard() -> HTMLResponse:
        """Render logs dashboard for visualization and troubleshooting."""
        try:
            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Logs Dashboard - LLM Documentation Ecosystem</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            border-left: 4px solid #17a2b8;
        }
        .stat-card.error {
            border-left-color: #dc3545;
        }
        .stat-card.warning {
            border-left-color: #ffc107;
        }
        .stat-card.success {
            border-left-color: #28a745;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #17a2b8;
            margin: 5px 0;
        }
        .stat-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .logs-container {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            height: 600px;
            overflow-y: auto;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 12px;
            line-height: 1.4;
        }
        .log-entry {
            margin: 2px 0;
            padding: 4px 8px;
            border-radius: 3px;
            border-left: 3px solid transparent;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .log-entry.debug { border-left-color: #6c757d; background: rgba(108, 117, 125, 0.1); }
        .log-entry.info { border-left-color: #007bff; background: rgba(0, 123, 255, 0.1); }
        .log-entry.warning { border-left-color: #ffc107; background: rgba(255, 193, 7, 0.1); }
        .log-entry.error { border-left-color: #dc3545; background: rgba(220, 53, 69, 0.1); }
        .log-entry.fatal { border-left-color: #6f42c1; background: rgba(111, 66, 193, 0.1); }
        .log-timestamp {
            color: #666;
            margin-right: 10px;
        }
        .log-service {
            color: #007bff;
            font-weight: bold;
            margin-right: 10px;
        }
        .log-level {
            padding: 1px 4px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
            margin-right: 10px;
        }
        .log-level.debug { background: #6c757d; color: white; }
        .log-level.info { background: #007bff; color: white; }
        .log-level.warning { background: #ffc107; color: black; }
        .log-level.error { background: #dc3545; color: white; }
        .log-level.fatal { background: #6f42c1; color: white; }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .control-group {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        select, input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn:hover {
            background: #0056b3;
        }
        .btn.secondary {
            background: #6c757d;
        }
        .btn.secondary:hover {
            background: #545b62;
        }
        .btn.danger {
            background: #dc3545;
        }
        .btn.danger:hover {
            background: #c82333;
        }
        .insights-panel {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .insight {
            color: #856404;
            margin: 5px 0;
            font-weight: 500;
        }
        .live-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #dc3545;
            margin-left: 10px;
            animation: pulse 2s infinite;
        }
        .live-indicator.active {
            background: #28a745;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #dee2e6;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            border-bottom-color: #17a2b8;
            color: #17a2b8;
            font-weight: bold;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .pattern-analysis {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .pattern-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .pattern-item {
            background: white;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #dee2e6;
        }
        .loading {
            text-align: center;
            color: #666;
            padding: 40px;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Logs Dashboard <span class="live-indicator" id="live-indicator"></span></h1>
            <p>Real-time log monitoring and troubleshooting dashboard</p>
        </div>

        <div class="controls">
            <div class="control-group">
                <label>Service:</label>
                <select id="service-filter">
                    <option value="">All Services</option>
                </select>
            </div>
            <div class="control-group">
                <label>Level:</label>
                <select id="level-filter">
                    <option value="">All Levels</option>
                    <option value="debug">Debug</option>
                    <option value="info">Info</option>
                    <option value="warning">Warning</option>
                    <option value="error">Error</option>
                    <option value="fatal">Fatal</option>
                </select>
            </div>
            <div class="control-group">
                <label>Limit:</label>
                <input type="number" id="limit-input" value="100" min="10" max="500">
            </div>
            <button class="btn" onclick="refreshLogs()">Refresh Logs</button>
            <button class="btn secondary" onclick="toggleStreaming()">Start Streaming</button>
            <button class="btn danger" onclick="clearLogs()">Clear Display</button>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('logs')">Live Logs</div>
            <div class="tab" onclick="showTab('stats')">Statistics</div>
            <div class="tab" onclick="showTab('patterns')">Patterns</div>
        </div>

        <div id="logs-content" class="tab-content active">
            <div id="insights-container"></div>
            <div id="logs-container" class="logs-container">
                <div class="loading">Loading logs...</div>
            </div>
        </div>

        <div id="stats-content" class="tab-content">
            <div id="stats-container" class="loading">Loading statistics...</div>
        </div>

        <div id="patterns-content" class="tab-content">
            <div id="patterns-container" class="loading">Loading pattern analysis...</div>
        </div>
    </div>

    <script>
        let logsData = [];
        let statsData = {};
        let isStreaming = false;
        let eventSource = null;

        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }

        async function fetchLogsStatus() {
            try {
                const service = document.getElementById('service-filter').value;
                const level = document.getElementById('level-filter').value;
                const limit = document.getElementById('limit-input').value;

                const params = new URLSearchParams();
                if (service) params.append('service', service);
                if (level) params.append('level', level);
                if (limit) params.append('limit', limit);

                const response = await fetch(`/api/logs/status?${params}`);
                const data = await response.json();

                if (data.success) {
                    logsData = data.data;
                    renderLogs(data.data);
                    renderInsights(data.data);
                    updateServiceFilter(data.data);
                    updateLiveIndicator(true);
                } else {
                    showError('Failed to fetch logs: ' + data.message);
                }
            } catch (error) {
                showError('Failed to fetch logs: ' + error.message);
                updateLiveIndicator(false);
            }
        }

        async function fetchLogsDirect() {
            try {
                const service = document.getElementById('service-filter').value;
                const level = document.getElementById('level-filter').value;
                const limit = document.getElementById('limit-input').value;

                const params = new URLSearchParams();
                if (service) params.append('service', service);
                if (level) params.append('level', level);
                if (limit) params.append('limit', limit);

                const response = await fetch(`/api/logs/fetch?${params}`);
                const data = await response.json();

                if (data.success) {
                    logsData.logs = data.data.logs;
                    renderLogs({logs: data.data.logs, summary: logsData.summary || {}});
                } else {
                    showError('Failed to fetch logs: ' + data.message);
                }
            } catch (error) {
                showError('Failed to fetch logs: ' + error.message);
            }
        }

        async function fetchStats() {
            try {
                const response = await fetch('/api/logs/stats');
                const data = await response.json();

                if (data.success) {
                    statsData = data.data;
                    renderStats(data.data);
                } else {
                    document.getElementById('stats-container').innerHTML =
                        '<div class="error">Failed to load statistics: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('stats-container').innerHTML =
                    '<div class="error">Failed to load statistics: ' + error.message + '</div>';
            }
        }

        function renderLogs(data) {
            const logs = data.logs || [];
            const summary = data.summary || {};

            let html = '';

            if (logs.length === 0) {
                html = '<div style="text-align: center; color: #666; padding: 40px;">No logs available</div>';
            } else {
                logs.forEach(log => {
                    const level = (log.level || 'info').toLowerCase();
                    const timestamp = log.timestamp ? new Date(log.timestamp).toLocaleString() : 'Unknown';
                    const service = log.service || 'unknown';
                    const message = log.message || '';

                    html += `
                        <div class="log-entry ${level}">
                            <span class="log-timestamp">${timestamp}</span>
                            <span class="log-service">[${service}]</span>
                            <span class="log-level ${level}">${level}</span>
                            <span class="log-message">${message}</span>
                        </div>
                    `;
                });
            }

            document.getElementById('logs-container').innerHTML = html;

            // Auto-scroll to bottom
            const container = document.getElementById('logs-container');
            container.scrollTop = container.scrollHeight;
        }

        function renderInsights(data) {
            const analysis = data.analysis || {};
            const insights = analysis.insights || [];

            if (insights.length === 0) {
                document.getElementById('insights-container').innerHTML = '';
                return;
            }

            let html = '<div class="insights-panel"><h4>System Insights</h4>';
            insights.forEach(insight => {
                html += `<div class="insight">• ${insight}</div>`;
            });
            html += '</div>';

            document.getElementById('insights-container').innerHTML = html;
        }

        function renderStats(stats) {
            const byLevel = stats.by_level || {};
            const byService = stats.by_service || {};
            const errorsByService = stats.errors_by_service || {};
            const topServices = stats.top_services || [];

            let html = '<div class="stats-grid">';

            // Total count
            html += `
                <div class="stat-card">
                    <div class="stat-label">Total Logs</div>
                    <div class="stat-value">${stats.count || 0}</div>
                </div>
            `;

            // By level
            Object.entries(byLevel).forEach(([level, count]) => {
                const levelClass = level.toLowerCase();
                html += `
                    <div class="stat-card ${levelClass}">
                        <div class="stat-label">${level.toUpperCase()}</div>
                        <div class="stat-value">${count}</div>
                    </div>
                `;
            });

            html += '</div>';

            // Top services
            if (topServices.length > 0) {
                html += '<h4>Top Services by Log Volume</h4><div class="stats-grid">';
                topServices.forEach(([service, count]) => {
                    html += `
                        <div class="stat-card">
                            <div class="stat-label">${service}</div>
                            <div class="stat-value">${count}</div>
                        </div>
                    `;
                });
                html += '</div>';
            }

            document.getElementById('stats-container').innerHTML = html;
        }

        function renderPatterns(data) {
            const analysis = data.analysis || {};
            const patterns = analysis.patterns || {};

            let html = '<div class="pattern-analysis"><h4>Log Pattern Analysis</h4><div class="pattern-grid">';

            // Error rate
            const errorRate = patterns.error_rate || 0;
            html += `
                <div class="pattern-item">
                    <strong>Error Rate</strong><br>
                    ${errorRate.toFixed(1)}% of all logs
                </div>
            `;

            // Active services
            const activeServices = patterns.services_active || [];
            html += `
                <div class="pattern-item">
                    <strong>Active Services</strong><br>
                    ${activeServices.length} services logging
                </div>
            `;

            html += '</div>';

            // Frequent messages
            const frequentMessages = patterns.frequent_messages || [];
            if (frequentMessages.length > 0) {
                html += '<h4>Most Frequent Messages</h4><div class="pattern-grid">';
                frequentMessages.slice(0, 6).forEach(item => {
                    html += `
                        <div class="pattern-item">
                            <strong>${item.count} occurrences</strong><br>
                            <small>${item.message}</small>
                        </div>
                    `;
                });
                html += '</div>';
            }

            html += '</div>';
            document.getElementById('patterns-container').innerHTML = html;
        }

        function updateServiceFilter(data) {
            const services = data.summary?.services || [];
            const select = document.getElementById('service-filter');

            // Preserve current selection
            const currentValue = select.value;

            // Clear existing options except "All Services"
            select.innerHTML = '<option value="">All Services</option>';

            // Add service options
            services.forEach(service => {
                const option = document.createElement('option');
                option.value = service;
                option.textContent = service;
                if (service === currentValue) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        }

        function updateLiveIndicator(isLive) {
            const indicator = document.getElementById('live-indicator');
            if (isLive) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        }

        function showError(message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = message;
            document.getElementById('logs-container').prepend(errorDiv);

            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.parentNode.removeChild(errorDiv);
                }
            }, 5000);
        }

        function refreshLogs() {
            if (isStreaming) {
                toggleStreaming(); // Stop streaming first
            }
            fetchLogsDirect();
        }

        function toggleStreaming() {
            const btn = document.querySelector('button[onclick="toggleStreaming()"]');

            if (isStreaming) {
                // Stop streaming
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                }
                isStreaming = false;
                btn.textContent = 'Start Streaming';
                btn.classList.remove('danger');
                btn.classList.add('secondary');
                updateLiveIndicator(false);
            } else {
                // Start streaming
                startStreaming();
                btn.textContent = 'Stop Streaming';
                btn.classList.remove('secondary');
                btn.classList.add('danger');
            }
        }

        function startStreaming() {
            const service = document.getElementById('service-filter').value;
            const level = document.getElementById('level-filter').value;

            let url = '/api/logs/stream';
            const params = [];
            if (service) params.push(`service=${service}`);
            if (level) params.push(`level=${level}`);
            if (params.length > 0) {
                url += '?' + params.join('&');
            }

            eventSource = new EventSource(url);

            eventSource.onmessage = function(event) {
                try {
                    const logEntry = JSON.parse(event.data);
                    addLogEntry(logEntry);
                    updateLiveIndicator(true);
                } catch (e) {
                    console.error('Failed to parse log entry:', e);
                }
            };

            eventSource.onerror = function(error) {
                console.error('EventSource error:', error);
                showError('Lost connection to log stream');
                updateLiveIndicator(false);
            };

            isStreaming = true;
        }

        function addLogEntry(logEntry) {
            if (logEntry.error) {
                showError(logEntry.error);
                return;
            }

            // Add to our logs array
            logsData.logs = logsData.logs || [];
            logsData.logs.push(logEntry);

            // Keep only recent logs
            if (logsData.logs.length > 500) {
                logsData.logs = logsData.logs.slice(-500);
            }

            // Re-render
            renderLogs(logsData);
        }

        function clearLogs() {
            logsData.logs = [];
            document.getElementById('logs-container').innerHTML =
                '<div style="text-align: center; color: #666; padding: 40px;">Logs cleared</div>';
        }

        // Load initial data
        fetchLogsStatus();
        fetchStats();

        // Set up tab switching to load content
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('tab')) {
                const tabName = e.target.textContent.toLowerCase().replace(' ', '');
                if (tabName === 'patterns' && document.getElementById('patterns-container').innerHTML.includes('Loading')) {
                    renderPatterns(logsData);
                }
            }
        });
    </script>
</body>
</html>
            """
            return create_html_response(html, "Logs Dashboard")
        except Exception as e:
            return handle_frontend_error("render logs dashboard", e, **build_frontend_context("render_logs_dashboard"))

    @staticmethod
    def handle_doc_store_browser() -> HTMLResponse:
        """Render doc-store data browser for document exploration."""
        try:
            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Doc Store Browser - LLM Documentation Ecosystem</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        .summary-card.analyses {
            border-left-color: #28a745;
        }
        .summary-card.quality {
            border-left-color: #ffc107;
        }
        .summary-card.style {
            border-left-color: #6f42c1;
        }
        .summary-value {
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
            margin: 10px 0;
        }
        .summary-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #dee2e6;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            border-bottom-color: #007bff;
            color: #007bff;
            font-weight: bold;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .control-group {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        select, input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn:hover {
            background: #0056b3;
        }
        .btn.secondary {
            background: #6c757d;
        }
        .btn.secondary:hover {
            background: #545b62;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .data-table th,
        .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .data-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        .data-table tr:hover {
            background: #f8f9fa;
        }
        .document-content {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
        }
        .metadata-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin: 10px 0;
        }
        .metadata-item {
            background: #e9ecef;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 13px;
        }
        .metadata-label {
            font-weight: bold;
            color: #495057;
        }
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin: 20px 0;
        }
        .page-btn {
            padding: 8px 12px;
            border: 1px solid #dee2e6;
            background: white;
            border-radius: 4px;
            cursor: pointer;
        }
        .page-btn.active {
            background: #007bff;
            color: white;
            border-color: #007bff;
        }
        .page-btn.disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .search-container {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            align-items: center;
        }
        .search-input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .loading {
            text-align: center;
            color: #666;
            padding: 40px;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .quality-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .metric-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #ffc107;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #ffc107;
            margin: 5px 0;
        }
        .metric-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
        }
        .code-example {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            white-space: pre-wrap;
        }
        .language-badge {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Doc Store Data Browser</h1>
            <p>Explore and browse stored documents, analyses, and quality metrics</p>
        </div>

        <div id="summary-container" class="loading">Loading summary...</div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('documents')">Documents</div>
            <div class="tab" onclick="showTab('analyses')">Analyses</div>
            <div class="tab" onclick="showTab('quality')">Quality</div>
            <div class="tab" onclick="showTab('style')">Style Examples</div>
        </div>

        <div id="documents-content" class="tab-content active">
            <div class="controls">
                <div class="control-group">
                    <label>Limit:</label>
                    <select id="doc-limit">
                        <option value="10">10</option>
                        <option value="20" selected>20</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                    </select>
                </div>
                <button class="btn" onclick="loadDocuments()">Load Documents</button>
                <button class="btn secondary" onclick="refreshDocuments()">Refresh</button>
            </div>
            <div id="documents-container" class="loading">Loading documents...</div>
        </div>

        <div id="analyses-content" class="tab-content">
            <div class="controls">
                <div class="control-group">
                    <label>Document ID:</label>
                    <input type="text" id="analysis-doc-id" placeholder="Filter by document ID">
                </div>
                <div class="control-group">
                    <label>Limit:</label>
                    <select id="analysis-limit">
                        <option value="10">10</option>
                        <option value="20" selected>20</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                    </select>
                </div>
                <button class="btn" onclick="loadAnalyses()">Load Analyses</button>
                <button class="btn secondary" onclick="refreshAnalyses()">Refresh</button>
            </div>
            <div id="analyses-container" class="loading">Loading analyses...</div>
        </div>

        <div id="quality-content" class="tab-content">
            <button class="btn" onclick="loadQualityMetrics()">Load Quality Metrics</button>
            <div id="quality-container" class="loading">Loading quality metrics...</div>
        </div>

        <div id="style-content" class="tab-content">
            <button class="btn" onclick="loadStyleExamples()">Load Style Examples</button>
            <div id="style-container" class="loading">Loading style examples...</div>
        </div>
    </div>

    <script>
        let currentDocOffset = 0;
        let currentAnalysisOffset = 0;

        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }

        async function loadSummary() {
            try {
                const response = await fetch('/api/doc-store/status');
                const data = await response.json();

                if (data.success) {
                    renderSummary(data.data);
                } else {
                    document.getElementById('summary-container').innerHTML =
                        '<div class="error">Failed to load summary: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('summary-container').innerHTML =
                    '<div class="error">Failed to load summary: ' + error.message + '</div>';
            }
        }

        function renderSummary(summary) {
            let html = '<div class="summary-grid">';

            // Documents
            html += `
                <div class="summary-card">
                    <div class="summary-label">Total Documents</div>
                    <div class="summary-value">${summary.total_documents || 0}</div>
                    <div>Categories: ${summary.categories?.length || 0}</div>
                </div>
            `;

            // Analyses
            html += `
                <div class="summary-card analyses">
                    <div class="summary-label">Total Analyses</div>
                    <div class="summary-value">${summary.total_analyses || 0}</div>
                    <div>Linked to documents</div>
                </div>
            `;

            // Quality
            const quality = summary.quality_metrics || {};
            html += `
                <div class="summary-card quality">
                    <div class="summary-label">Quality Score</div>
                    <div class="summary-value">${quality.overall_score || 'N/A'}</div>
                    <div>Stale docs: ${summary.stale_documents?.length || 0}</div>
                </div>
            `;

            // Style examples
            html += `
                <div class="summary-card style">
                    <div class="summary-label">Languages</div>
                    <div class="summary-value">${summary.languages?.length || 0}</div>
                    <div>Programming languages</div>
                </div>
            `;

            html += '</div>';
            document.getElementById('summary-container').innerHTML = html;
        }

        async function loadDocuments() {
            const limit = document.getElementById('doc-limit').value;
            document.getElementById('documents-container').innerHTML = 'Loading documents...';

            try {
                const response = await fetch(`/api/doc-store/documents?limit=${limit}&offset=${currentDocOffset}`);
                const data = await response.json();

                if (data.success) {
                    renderDocuments(data.data);
                } else {
                    document.getElementById('documents-container').innerHTML =
                        '<div class="error">Failed to load documents: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('documents-container').innerHTML =
                    '<div class="error">Failed to load documents: ' + error.message + '</div>';
            }
        }

        function renderDocuments(data) {
            const documents = data.documents || [];

            if (documents.length === 0) {
                document.getElementById('documents-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No documents found</div>';
                return;
            }

            let html = '<table class="data-table"><thead><tr>';
            html += '<th>ID</th><th>Title</th><th>Category</th><th>Created</th><th>Actions</th>';
            html += '</tr></thead><tbody>';

            documents.forEach(doc => {
                const created = doc.created_at ? new Date(doc.created_at).toLocaleString() : 'Unknown';
                const title = doc.metadata?.title || doc.id || 'Untitled';
                const category = doc.metadata?.category || 'Uncategorized';

                html += `
                    <tr>
                        <td>${doc.id}</td>
                        <td>${title}</td>
                        <td>${category}</td>
                        <td>${created}</td>
                        <td><button class="btn" onclick="viewDocument('${doc.id}')">View</button></td>
                    </tr>
                `;
            });

            html += '</tbody></table>';

            // Pagination
            const total = data.total || 0;
            const limit = data.limit || 20;
            const hasNext = (currentDocOffset + limit) < total;
            const hasPrev = currentDocOffset > 0;

            html += '<div class="pagination">';
            html += `<button class="page-btn ${hasPrev ? '' : 'disabled'}" onclick="prevDocPage()">Previous</button>`;
            html += `<span>Page ${Math.floor(currentDocOffset / limit) + 1} of ${Math.ceil(total / limit)}</span>`;
            html += `<button class="page-btn ${hasNext ? '' : 'disabled'}" onclick="nextDocPage()">Next</button>`;
            html += '</div>';

            document.getElementById('documents-container').innerHTML = html;
        }

        async function loadAnalyses() {
            const docId = document.getElementById('analysis-doc-id').value;
            const limit = document.getElementById('analysis-limit').value;
            document.getElementById('analyses-container').innerHTML = 'Loading analyses...';

            let url = `/api/doc-store/analyses?limit=${limit}&offset=${currentAnalysisOffset}`;
            if (docId) url += `&document_id=${docId}`;

            try {
                const response = await fetch(url);
                const data = await response.json();

                if (data.success) {
                    renderAnalyses(data.data);
                } else {
                    document.getElementById('analyses-container').innerHTML =
                        '<div class="error">Failed to load analyses: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('analyses-container').innerHTML =
                    '<div class="error">Failed to load analyses: ' + error.message + '</div>';
            }
        }

        function renderAnalyses(data) {
            const analyses = data.analyses || [];

            if (analyses.length === 0) {
                document.getElementById('analyses-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No analyses found</div>';
                return;
            }

            let html = '<table class="data-table"><thead><tr>';
            html += '<th>ID</th><th>Document ID</th><th>Analyzer</th><th>Score</th><th>Created</th>';
            html += '</tr></thead><tbody>';

            analyses.forEach(analysis => {
                const created = analysis.created_at ? new Date(analysis.created_at).toLocaleString() : 'Unknown';

                html += `
                    <tr>
                        <td>${analysis.id}</td>
                        <td>${analysis.document_id || 'N/A'}</td>
                        <td>${analysis.analyzer || 'Unknown'}</td>
                        <td>${analysis.score || 'N/A'}</td>
                        <td>${created}</td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
            document.getElementById('analyses-container').innerHTML = html;
        }

        async function loadQualityMetrics() {
            document.getElementById('quality-container').innerHTML = 'Loading quality metrics...';

            try {
                const response = await fetch('/api/doc-store/quality');
                const data = await response.json();

                if (data.success) {
                    renderQualityMetrics(data.data);
                } else {
                    document.getElementById('quality-container').innerHTML =
                        '<div class="error">Failed to load quality metrics: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('quality-container').innerHTML =
                    '<div class="error">Failed to load quality metrics: ' + error.message + '</div>';
            }
        }

        function renderQualityMetrics(data) {
            const quality = data.quality || {};

            let html = '<div class="quality-metrics">';

            // Add key metrics
            Object.entries(quality).forEach(([key, value]) => {
                if (typeof value === 'number') {
                    html += `
                        <div class="metric-item">
                            <div class="metric-label">${key.replace(/_/g, ' ')}</div>
                            <div class="metric-value">${value}</div>
                        </div>
                    `;
                }
            });

            html += '</div>';

            // Stale documents list
            if (quality.stale_documents && quality.stale_documents.length > 0) {
                html += '<h4>Stale Documents</h4><div class="data-table" style="margin-top: 10px;">';
                html += '<table><thead><tr><th>Document ID</th><th>Last Updated</th></tr></thead><tbody>';

                quality.stale_documents.forEach(doc => {
                    const updated = doc.last_updated ? new Date(doc.last_updated).toLocaleString() : 'Unknown';
                    html += `<tr><td>${doc.id}</td><td>${updated}</td></tr>`;
                });

                html += '</tbody></table></div>';
            }

            document.getElementById('quality-container').innerHTML = html;
        }

        async function loadStyleExamples() {
            document.getElementById('style-container').innerHTML = 'Loading style examples...';

            try {
                const response = await fetch('/api/doc-store/style-examples');
                const data = await response.json();

                if (data.success) {
                    renderStyleExamples(data.data);
                } else {
                    document.getElementById('style-container').innerHTML =
                        '<div class="error">Failed to load style examples: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('style-container').innerHTML =
                    '<div class="error">Failed to load style examples: ' + error.message + '</div>';
            }
        }

        function renderStyleExamples(data) {
            const examples = data.style_examples || {};

            let html = '';

            Object.entries(examples).forEach(([language, example]) => {
                html += `<h4><span class="language-badge">${language}</span></h4>`;
                html += '<div class="code-example">';
                html += example.example || 'No example available';
                html += '</div>';
            });

            if (html === '') {
                html = '<div style="text-align: center; color: #666; padding: 40px;">No style examples available</div>';
            }

            document.getElementById('style-container').innerHTML = html;
        }

        async function viewDocument(docId) {
            try {
                const response = await fetch(`/api/doc-store/documents/${docId}`);
                const data = await response.json();

                if (data.success && data.data.document) {
                    showDocumentModal(data.data.document);
                } else {
                    alert('Failed to load document: ' + (data.message || 'Unknown error'));
                }
            } catch (error) {
                alert('Failed to load document: ' + error.message);
            }
        }

        function showDocumentModal(document) {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.7); z-index: 1000; display: flex;
                align-items: center; justify-content: center;
            `;

            const content = document.createElement('div');
            content.style.cssText = `
                background: white; padding: 20px; border-radius: 8px;
                max-width: 80%; max-height: 80%; overflow-y: auto;
            `;

            content.innerHTML = `
                <h3>Document: ${document.id}</h3>
                <div class="metadata-grid">
                    ${Object.entries(document.metadata || {}).map(([key, value]) =>
                        `<div class="metadata-item"><span class="metadata-label">${key}:</span> ${value}</div>`
                    ).join('')}
                </div>
                <h4>Content:</h4>
                <div class="document-content">${document.content || 'No content available'}</div>
                <button class="btn" onclick="this.parentElement.parentElement.remove()">Close</button>
            `;

            modal.appendChild(content);
            document.body.appendChild(modal);
        }

        function prevDocPage() {
            const limit = parseInt(document.getElementById('doc-limit').value);
            if (currentDocOffset >= limit) {
                currentDocOffset -= limit;
                loadDocuments();
            }
        }

        function nextDocPage() {
            const limit = parseInt(document.getElementById('doc-limit').value);
            currentDocOffset += limit;
            loadDocuments();
        }

        function refreshDocuments() {
            currentDocOffset = 0;
            loadDocuments();
        }

        function refreshAnalyses() {
            currentAnalysisOffset = 0;
            loadAnalyses();
        }

        // Load initial data
        loadSummary();
    </script>
</body>
</html>
            """
            return create_html_response(html, "Doc Store Data Browser")
        except Exception as e:
            return handle_frontend_error("render doc-store browser", e, **build_frontend_context("render_doc_store_browser"))

    @staticmethod
    def handle_prompt_store_browser() -> HTMLResponse:
        """Render prompt-store data browser for prompt exploration."""
        try:
            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prompt Store Browser - LLM Documentation Ecosystem</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #28a745;
        }
        .summary-card.analytics {
            border-left-color: #007bff;
        }
        .summary-value {
            font-size: 2em;
            font-weight: bold;
            color: #28a745;
            margin: 10px 0;
        }
        .summary-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #dee2e6;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            border-bottom-color: #28a745;
            color: #28a745;
            font-weight: bold;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .control-group {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        select, input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn:hover {
            background: #218838;
        }
        .btn.secondary {
            background: #6c757d;
        }
        .btn.secondary:hover {
            background: #545b62;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .data-table th,
        .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .data-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        .data-table tr:hover {
            background: #f8f9fa;
        }
        .prompt-content {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }
        .prompt-template {
            background: #e9ecef;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            white-space: pre-wrap;
        }
        .metadata-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin: 10px 0;
        }
        .metadata-item {
            background: #e9ecef;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 13px;
        }
        .metadata-label {
            font-weight: bold;
            color: #495057;
        }
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin: 20px 0;
        }
        .page-btn {
            padding: 8px 12px;
            border: 1px solid #dee2e6;
            background: white;
            border-radius: 4px;
            cursor: pointer;
        }
        .page-btn.active {
            background: #28a745;
            color: white;
            border-color: #28a745;
        }
        .page-btn.disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .analytics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .analytics-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        .analytics-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #007bff;
            margin: 5px 0;
        }
        .analytics-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
        }
        .usage-chart {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .category-filter {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }
        .category-btn {
            padding: 6px 12px;
            border: 1px solid #dee2e6;
            background: white;
            border-radius: 20px;
            cursor: pointer;
            font-size: 13px;
        }
        .category-btn.active {
            background: #28a745;
            color: white;
            border-color: #28a745;
        }
        .loading {
            text-align: center;
            color: #666;
            padding: 40px;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .version-badge {
            display: inline-block;
            background: #ffc107;
            color: black;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 11px;
            margin-left: 5px;
        }
        .category-badge {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 11px;
            margin: 2px 5px 2px 0;
        }
        .template-vars {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-size: 13px;
        }
        .template-vars strong {
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Prompt Store Data Browser</h1>
            <p>Explore and browse stored prompts, analytics, and performance metrics</p>
        </div>

        <div id="summary-container" class="loading">Loading summary...</div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('prompts')">Prompts</div>
            <div class="tab" onclick="showTab('analytics')">Analytics</div>
        </div>

        <div id="prompts-content" class="tab-content active">
            <div class="controls">
                <div class="control-group">
                    <label>Category:</label>
                    <select id="category-filter">
                        <option value="">All Categories</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Limit:</label>
                    <select id="prompt-limit">
                        <option value="10">10</option>
                        <option value="20" selected>20</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                    </select>
                </div>
                <button class="btn" onclick="loadPrompts()">Load Prompts</button>
                <button class="btn secondary" onclick="refreshPrompts()">Refresh</button>
            </div>
            <div id="prompts-container" class="loading">Loading prompts...</div>
        </div>

        <div id="analytics-content" class="tab-content">
            <button class="btn" onclick="loadAnalytics()">Load Analytics</button>
            <div id="analytics-container" class="loading">Loading analytics...</div>
        </div>
    </div>

    <script>
        let currentPromptOffset = 0;

        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }

        async function loadSummary() {
            try {
                const response = await fetch('/api/prompt-store/status');
                const data = await response.json();

                if (data.success) {
                    renderSummary(data.data);
                    updateCategoryFilter(data.data);
                } else {
                    document.getElementById('summary-container').innerHTML =
                        '<div class="error">Failed to load summary: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('summary-container').innerHTML =
                    '<div class="error">Failed to load summary: ' + error.message + '</div>';
            }
        }

        function renderSummary(summary) {
            let html = '<div class="summary-grid">';

            // Prompts
            html += `
                <div class="summary-card">
                    <div class="summary-label">Total Prompts</div>
                    <div class="summary-value">${summary.total_prompts || 0}</div>
                    <div>Categories: ${summary.categories?.length || 0}</div>
                </div>
            `;

            // Analytics
            const analytics = summary.analytics || {};
            html += `
                <div class="summary-card analytics">
                    <div class="summary-label">Usage Metrics</div>
                    <div class="summary-value">${analytics.total_usage || 0}</div>
                    <div>A/B tests: ${analytics.ab_test_count || 0}</div>
                </div>
            `;

            html += '</div>';
            document.getElementById('summary-container').innerHTML = html;
        }

        function updateCategoryFilter(summary) {
            const categories = summary.categories || [];
            const select = document.getElementById('category-filter');

            // Clear existing options except "All Categories"
            select.innerHTML = '<option value="">All Categories</option>';

            // Add category options
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                select.appendChild(option);
            });
        }

        async function loadPrompts() {
            const category = document.getElementById('category-filter').value;
            const limit = document.getElementById('prompt-limit').value;
            document.getElementById('prompts-container').innerHTML = 'Loading prompts...';

            let url = `/api/prompt-store/prompts?limit=${limit}&offset=${currentPromptOffset}`;
            if (category) url += `&category=${category}`;

            try {
                const response = await fetch(url);
                const data = await response.json();

                if (data.success) {
                    renderPrompts(data.data);
                } else {
                    document.getElementById('prompts-container').innerHTML =
                        '<div class="error">Failed to load prompts: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('prompts-container').innerHTML =
                    '<div class="error">Failed to load prompts: ' + error.message + '</div>';
            }
        }

        function renderPrompts(data) {
            const prompts = data.prompts || [];

            if (prompts.length === 0) {
                document.getElementById('prompts-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No prompts found</div>';
                return;
            }

            let html = '<table class="data-table"><thead><tr>';
            html += '<th>Name</th><th>Category</th><th>Version</th><th>Template</th><th>Actions</th>';
            html += '</tr></thead><tbody>';

            prompts.forEach(prompt => {
                const isTemplate = prompt.template_vars && prompt.template_vars.length > 0;
                const templateIndicator = isTemplate ? ' <span class="version-badge">Template</span>' : '';

                html += `
                    <tr>
                        <td>${prompt.name || 'Unnamed'}${templateIndicator}</td>
                        <td><span class="category-badge">${prompt.category || 'Uncategorized'}</span></td>
                        <td>${prompt.version || '1.0'}</td>
                        <td>${isTemplate ? 'Yes' : 'No'}</td>
                        <td><button class="btn" onclick="viewPrompt('${prompt.id}')">View</button></td>
                    </tr>
                `;
            });

            html += '</tbody></table>';

            // Pagination
            const total = data.total || 0;
            const limit = data.limit || 20;
            const hasNext = (currentPromptOffset + limit) < total;
            const hasPrev = currentPromptOffset > 0;

            html += '<div class="pagination">';
            html += `<button class="page-btn ${hasPrev ? '' : 'disabled'}" onclick="prevPromptPage()">Previous</button>`;
            html += `<span>Page ${Math.floor(currentPromptOffset / limit) + 1} of ${Math.ceil(total / limit)}</span>`;
            html += `<button class="page-btn ${hasNext ? '' : 'disabled'}" onclick="nextPromptPage()">Next</button>`;
            html += '</div>';

            document.getElementById('prompts-container').innerHTML = html;
        }

        async function loadAnalytics() {
            document.getElementById('analytics-container').innerHTML = 'Loading analytics...';

            try {
                const response = await fetch('/api/prompt-store/analytics');
                const data = await response.json();

                if (data.success) {
                    renderAnalytics(data.data);
                } else {
                    document.getElementById('analytics-container').innerHTML =
                        '<div class="error">Failed to load analytics: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('analytics-container').innerHTML =
                    '<div class="error">Failed to load analytics: ' + error.message + '</div>';
            }
        }

        function renderAnalytics(data) {
            const analytics = data.analytics || {};

            let html = '<div class="analytics-grid">';

            // Key metrics
            Object.entries(analytics).forEach(([key, value]) => {
                if (typeof value === 'number' && value > 0) {
                    html += `
                        <div class="analytics-item">
                            <div class="analytics-label">${key.replace(/_/g, ' ')}</div>
                            <div class="analytics-value">${value}</div>
                        </div>
                    `;
                }
            });

            html += '</div>';

            // Usage chart placeholder
            html += `
                <div class="usage-chart">
                    <h4>Prompt Usage Over Time</h4>
                    <p>Usage analytics and performance metrics would be visualized here with charts and graphs.</p>
                    <p><strong>Note:</strong> This is a read-only browser. Full analytics dashboards would include interactive charts, time-series data, and A/B testing comparisons.</p>
                </div>
            `;

            document.getElementById('analytics-container').innerHTML = html;
        }

        async function viewPrompt(promptId) {
            // For this demo, we'll show a mock prompt since we don't have direct prompt retrieval
            // In a real implementation, you'd fetch the prompt by ID
            const mockPrompt = {
                id: promptId,
                name: "Sample Prompt",
                category: "documentation",
                version: "1.0",
                content: "You are a helpful documentation assistant. Please help with the following task:\\n\\n{{task}}\\n\\nProvide clear, concise, and accurate documentation.",
                template_vars: ["task"],
                description: "A general-purpose documentation assistant prompt template."
            };

            showPromptModal(mockPrompt);
        }

        function showPromptModal(prompt) {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.7); z-index: 1000; display: flex;
                align-items: center; justify-content: center;
            `;

            const content = document.createElement('div');
            content.style.cssText = `
                background: white; padding: 20px; border-radius: 8px;
                max-width: 80%; max-height: 80%; overflow-y: auto;
            `;

            let varsHtml = '';
            if (prompt.template_vars && prompt.template_vars.length > 0) {
                varsHtml = `
                    <div class="template-vars">
                        <strong>Template Variables:</strong> ${prompt.template_vars.join(', ')}
                    </div>
                `;
            }

            content.innerHTML = `
                <h3>Prompt: ${prompt.name}</h3>
                <div class="metadata-grid">
                    <div class="metadata-item"><span class="metadata-label">ID:</span> ${prompt.id}</div>
                    <div class="metadata-item"><span class="metadata-label">Category:</span> ${prompt.category}</div>
                    <div class="metadata-item"><span class="metadata-label">Version:</span> ${prompt.version}</div>
                </div>
                ${varsHtml}
                <h4>Prompt Content:</h4>
                <div class="prompt-content">${prompt.content}</div>
                ${prompt.description ? `<p><strong>Description:</strong> ${prompt.description}</p>` : ''}
                <button class="btn" onclick="this.parentElement.parentElement.remove()">Close</button>
            `;

            modal.appendChild(content);
            document.body.appendChild(modal);
        }

        function prevPromptPage() {
            const limit = parseInt(document.getElementById('prompt-limit').value);
            if (currentPromptOffset >= limit) {
                currentPromptOffset -= limit;
                loadPrompts();
            }
        }

        function nextPromptPage() {
            const limit = parseInt(document.getElementById('prompt-limit').value);
            currentPromptOffset += limit;
            loadPrompts();
        }

        function refreshPrompts() {
            currentPromptOffset = 0;
            loadPrompts();
        }

        // Load initial data
        loadSummary();
    </script>
</body>
</html>
            """
            return create_html_response(html, "Prompt Store Data Browser")
        except Exception as e:
            return handle_frontend_error("render prompt-store browser", e, **build_frontend_context("render_prompt_store_browser"))

    @staticmethod
    def handle_orchestrator_monitor() -> HTMLResponse:
        """Render orchestrator monitoring dashboard."""
        try:
            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Orchestrator Monitor - LLM Documentation Ecosystem</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #17a2b8;
        }
        .status-card.redis {
            border-left-color: #dc3545;
        }
        .status-card.config {
            border-left-color: #28a745;
        }
        .status-card.workflows {
            border-left-color: #ffc107;
        }
        .status-card.error {
            border-left-color: #6c757d;
        }
        .status-value {
            font-size: 2em;
            font-weight: bold;
            color: #17a2b8;
            margin: 10px 0;
        }
        .status-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #dee2e6;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            border-bottom-color: #17a2b8;
            color: #17a2b8;
            font-weight: bold;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .control-group {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .btn {
            background: #17a2b8;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn:hover {
            background: #138496;
        }
        .btn.secondary {
            background: #6c757d;
        }
        .btn.secondary:hover {
            background: #545b62;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .data-table th,
        .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .data-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        .data-table tr:hover {
            background: #f8f9fa;
        }
        .config-section {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
        }
        .config-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }
        .config-item:last-child {
            border-bottom: none;
        }
        .config-key {
            font-weight: bold;
            color: #495057;
        }
        .config-value {
            color: #007bff;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
        }
        .redis-channels {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .channel-card {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #dc3545;
        }
        .channel-name {
            font-size: 1.2em;
            font-weight: bold;
            color: #dc3545;
            margin-bottom: 10px;
        }
        .channel-description {
            color: #666;
            margin-bottom: 15px;
        }
        .channel-metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        .workflow-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .workflow-name {
            font-size: 1.1em;
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }
        .workflow-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
        }
        .health-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #dc3545;
            margin-right: 8px;
        }
        .health-indicator.healthy {
            background: #28a745;
        }
        .loading {
            text-align: center;
            color: #666;
            padding: 40px;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #17a2b8;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #17a2b8;
            margin: 5px 0;
        }
        .metric-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
        }
        .code-block {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            margin: 10px 0;
        }
        .badge {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 2px 5px 2px 0;
        }
        .badge.redis {
            background: #dc3545;
        }
        .badge.config {
            background: #28a745;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Orchestrator Monitor</h1>
            <p>Monitor Redis pub/sub activity, service configuration, and workflow execution</p>
        </div>

        <div id="summary-container" class="loading">Loading orchestrator status...</div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('overview')">Overview</div>
            <div class="tab" onclick="showTab('redis')">Redis Activity</div>
            <div class="tab" onclick="showTab('config')">Configuration</div>
            <div class="tab" onclick="showTab('workflows')">Workflows</div>
        </div>

        <div id="overview-content" class="tab-content active">
            <div class="controls">
                <button class="btn" onclick="loadOverview()">Refresh Overview</button>
            </div>
            <div id="overview-container" class="loading">Loading overview...</div>
        </div>

        <div id="redis-content" class="tab-content">
            <div class="controls">
                <button class="btn" onclick="loadRedisActivity()">Load Redis Activity</button>
                <button class="btn secondary" onclick="refreshRedis()">Refresh</button>
            </div>
            <div id="redis-container" class="loading">Loading Redis activity...</div>
        </div>

        <div id="config-content" class="tab-content">
            <div class="controls">
                <button class="btn" onclick="loadConfig()">Load Configuration</button>
                <button class="btn secondary" onclick="refreshConfig()">Refresh</button>
            </div>
            <div id="config-container" class="loading">Loading configuration...</div>
        </div>

        <div id="workflows-content" class="tab-content">
            <div class="controls">
                <button class="btn" onclick="loadWorkflows()">Load Workflows</button>
                <button class="btn secondary" onclick="refreshWorkflows()">Refresh</button>
            </div>
            <div id="workflows-container" class="loading">Loading workflows...</div>
        </div>
    </div>

    <script>
        let orchestratorData = {};

        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }

        async function loadSummary() {
            try {
                const response = await fetch('/api/orchestrator/health');
                const data = await response.json();

                if (data.success) {
                    const health = data.data;
                    const isHealthy = health.orchestrator_healthy;

                    document.getElementById('summary-container').innerHTML = `
                        <div class="status-grid">
                            <div class="status-card ${isHealthy ? '' : 'error'}">
                                <div class="status-label">Service Health</div>
                                <div class="status-value">
                                    <span class="health-indicator ${isHealthy ? 'healthy' : ''}"></span>
                                    ${isHealthy ? 'Healthy' : 'Unhealthy'}
                                </div>
                                <div>Service: ${health.service || 'Unknown'}</div>
                                <div>Version: ${health.version || 'Unknown'}</div>
                            </div>
                            <div class="status-card redis">
                                <div class="status-label">Redis Status</div>
                                <div class="status-value">Active</div>
                                <div>Pub/Sub Channels: 2</div>
                                <div>Last Activity: Monitoring</div>
                            </div>
                            <div class="status-card config">
                                <div class="status-label">Configuration</div>
                                <div class="status-value">Loaded</div>
                                <div>Peer Orchestrators: Configured</div>
                                <div>Service Discovery: Enabled</div>
                            </div>
                            <div class="status-card workflows">
                                <div class="status-label">Workflows</div>
                                <div class="status-value">3</div>
                                <div>Available Workflows</div>
                                <div>Execution Monitoring</div>
                            </div>
                        </div>
                    `;
                } else {
                    document.getElementById('summary-container').innerHTML =
                        '<div class="error">Failed to load summary: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('summary-container').innerHTML =
                    '<div class="error">Failed to load summary: ' + error.message + '</div>';
            }
        }

        async function loadOverview() {
            document.getElementById('overview-container').innerHTML = 'Loading overview...';

            try {
                const response = await fetch('/api/orchestrator/status');
                const data = await response.json();

                if (data.success) {
                    renderOverview(data.data);
                } else {
                    document.getElementById('overview-container').innerHTML =
                        '<div class="error">Failed to load overview: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('overview-container').innerHTML =
                    '<div class="error">Failed to load overview: ' + error.message + '</div>';
            }
        }

        function renderOverview(data) {
            let html = '';

            // Quick metrics
            html += '<div class="metric-grid">';

            if (data.config && data.config.metrics) {
                const metrics = data.config.metrics;
                html += `
                    <div class="metric-item">
                        <div class="metric-label">Active Workflows</div>
                        <div class="metric-value">${metrics.active_workflows || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Total Services</div>
                        <div class="metric-value">${metrics.total_services || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Routes</div>
                        <div class="metric-value">${metrics.routes_count || 0}</div>
                    </div>
                `;
            }

            if (data.pubsub_activity) {
                const pubsub = data.pubsub_activity;
                html += `
                    <div class="metric-item">
                        <div class="metric-label">Total Events</div>
                        <div class="metric-value">${pubsub.estimated_total_events || 0}</div>
                    </div>
                `;
            }

            html += '</div>';

            // Recent activity
            if (data.workflows && data.workflows.recent_history) {
                const recent = data.workflows.recent_history.slice(0, 5);
                if (recent.length > 0) {
                    html += '<h4>Recent Workflow Activity</h4>';
                    recent.forEach(workflow => {
                        html += `
                            <div class="workflow-item">
                                <div class="workflow-name">${workflow.workflow_type || 'Unknown Workflow'}</div>
                                <div class="workflow-meta">
                                    <span>Status: ${workflow.status || 'Unknown'}</span>
                                    <span>Started: ${workflow.timestamp || 'Unknown'}</span>
                                </div>
                            </div>
                        `;
                    });
                }
            }

            document.getElementById('overview-container').innerHTML = html;
        }

        async function loadRedisActivity() {
            document.getElementById('redis-container').innerHTML = 'Loading Redis activity...';

            try {
                const response = await fetch('/api/orchestrator/redis-activity');
                const data = await response.json();

                if (data.success) {
                    renderRedisActivity(data.data);
                } else {
                    document.getElementById('redis-container').innerHTML =
                        '<div class="error">Failed to load Redis activity: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('redis-container').innerHTML =
                    '<div class="error">Failed to load Redis activity: ' + error.message + '</div>';
            }
        }

        function renderRedisActivity(data) {
            const channels = data.channels || {};

            let html = '<div class="redis-channels">';

            Object.entries(channels).forEach(([channelName, channelData]) => {
                const activity = channelData.estimated_activity || 0;
                const lastActivity = channelData.last_activity ?
                    new Date(channelData.last_activity).toLocaleString() : 'Never';

                html += `
                    <div class="channel-card">
                        <div class="channel-name">${channelName.replace(/_/g, ' ')}</div>
                        <div class="channel-description">${channelData.description || 'No description available'}</div>
                        <div class="channel-metric">
                            <span>Estimated Activity:</span>
                            <span>${activity} events</span>
                        </div>
                        <div class="channel-metric">
                            <span>Last Activity:</span>
                            <span>${lastActivity}</span>
                        </div>
                    </div>
                `;
            });

            html += '</div>';

            // Event timeline (if available)
            if (data.infrastructure_events && data.infrastructure_events.events) {
                const events = data.infrastructure_events.events.slice(0, 10);
                if (events.length > 0) {
                    html += '<h4>Recent Events</h4><div class="data-table">';
                    html += '<table><thead><tr><th>Event Type</th><th>Timestamp</th><th>Details</th></tr></thead><tbody>';

                    events.forEach(event => {
                        const timestamp = event.timestamp ?
                            new Date(event.timestamp).toLocaleString() : 'Unknown';
                        html += `
                            <tr>
                                <td><span class="badge redis">${event.type || 'Unknown'}</span></td>
                                <td>${timestamp}</td>
                                <td>${JSON.stringify(event.payload || {}).substring(0, 100)}...</td>
                            </tr>
                        `;
                    });

                    html += '</tbody></table></div>';
                }
            }

            document.getElementById('redis-container').innerHTML = html;
        }

        async function loadConfig() {
            document.getElementById('config-container').innerHTML = 'Loading configuration...';

            try {
                const response = await fetch('/api/orchestrator/config');
                const data = await response.json();

                if (data.success) {
                    renderConfig(data.data);
                } else {
                    document.getElementById('config-container').innerHTML =
                        '<div class="error">Failed to load config: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('config-container').innerHTML =
                    '<div class="error">Failed to load config: ' + error.message + '</div>';
            }
        }

        function renderConfig(data) {
            let html = '';

            // Service Info
            if (data.info) {
                html += '<h4>Service Information</h4><div class="config-section">';
                Object.entries(data.info).forEach(([key, value]) => {
                    html += `<div class="config-item"><span class="config-key">${key}:</span> <span class="config-value">${value}</span></div>`;
                });
                html += '</div>';
            }

            // Configuration
            if (data.config) {
                html += '<h4>Configuration Settings</h4><div class="config-section">';
                Object.entries(data.config).forEach(([key, value]) => {
                    const displayValue = typeof value === 'object' ? JSON.stringify(value) : String(value);
                    html += `<div class="config-item"><span class="config-key">${key}:</span> <span class="config-value">${displayValue}</span></div>`;
                });
                html += '</div>';
            }

            // Metrics
            if (data.metrics) {
                html += '<h4>Service Metrics</h4><div class="config-section">';
                Object.entries(data.metrics).forEach(([key, value]) => {
                    html += `<div class="config-item"><span class="config-key">${key}:</span> <span class="config-value">${value}</span></div>`;
                });
                html += '</div>';
            }

            document.getElementById('config-container').innerHTML = html;
        }

        async function loadWorkflows() {
            document.getElementById('workflows-container').innerHTML = 'Loading workflows...';

            try {
                const response = await fetch('/api/orchestrator/workflows');
                const data = await response.json();

                if (data.success) {
                    renderWorkflows(data.data);
                } else {
                    document.getElementById('workflows-container').innerHTML =
                        '<div class="error">Failed to load workflows: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('workflows-container').innerHTML =
                    '<div class="error">Failed to load workflows: ' + error.message + '</div>';
            }
        }

        function renderWorkflows(data) {
            let html = '';

            // Available workflows
            if (data.available_workflows) {
                html += '<h4>Available Workflows</h4>';
                Object.values(data.available_workflows).forEach(workflow => {
                    html += `
                        <div class="workflow-item">
                            <div class="workflow-name">${workflow.name || 'Unnamed Workflow'}</div>
                            <div>${workflow.description || 'No description'}</div>
                            <div class="workflow-meta">
                                <span>Duration: ${workflow.estimated_duration || 'Unknown'}s</span>
                                <span>Services: ${workflow.required_services?.length || 0}</span>
                            </div>
                        </div>
                    `;
                });
            }

            // Workflow statistics
            if (data.workflow_stats) {
                const stats = data.workflow_stats;
                html += '<h4>Workflow Statistics</h4><div class="metric-grid">';
                html += `
                    <div class="metric-item">
                        <div class="metric-label">Total Executions</div>
                        <div class="metric-value">${stats.total_workflows || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Success Rate</div>
                        <div class="metric-value">${stats.success_rate ? stats.success_rate.toFixed(1) + '%' : 'N/A'}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Avg Duration</div>
                        <div class="metric-value">${stats.average_duration || 0}s</div>
                    </div>
                `;
                html += '</div>';
            }

            // Recent history
            if (data.recent_history && data.recent_history.length > 0) {
                html += '<h4>Recent Executions</h4>';
                data.recent_history.slice(0, 10).forEach(workflow => {
                    const statusClass = workflow.status === 'completed' ? 'success' :
                                      workflow.status === 'failed' ? 'error' : '';
                    html += `
                        <div class="workflow-item">
                            <div class="workflow-name ${statusClass}">${workflow.workflow_type || 'Unknown'}</div>
                            <div class="workflow-meta">
                                <span>Status: <span class="badge ${statusClass}">${workflow.status || 'Unknown'}</span></span>
                                <span>Started: ${workflow.timestamp || 'Unknown'}</span>
                                <span>Duration: ${workflow.duration || 'N/A'}s</span>
                            </div>
                        </div>
                    `;
                });
            }

            document.getElementById('workflows-container').innerHTML = html;
        }

        // Helper functions
        function refreshRedis() { loadRedisActivity(); }
        function refreshConfig() { loadConfig(); }
        function refreshWorkflows() { loadWorkflows(); }

        // Load initial data
        loadSummary();
    </script>
</body>
</html>
            """
            return create_html_response(html, "Orchestrator Monitor")
        except Exception as e:
            return handle_frontend_error("render orchestrator monitor", e, **build_frontend_context("render_orchestrator_monitor"))

    @staticmethod
    def handle_analysis_dashboard() -> HTMLResponse:
        """Render analysis service dashboard."""
        try:
            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Dashboard - LLM Documentation Ecosystem</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #17a2b8;
        }
        .status-card.error {
            border-left-color: #dc3545;
        }
        .status-card.warning {
            border-left-color: #ffc107;
        }
        .status-card.success {
            border-left-color: #28a745;
        }
        .status-value {
            font-size: 2em;
            font-weight: bold;
            color: #17a2b8;
            margin: 10px 0;
        }
        .status-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #dee2e6;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            border-bottom-color: #17a2b8;
            color: #17a2b8;
            font-weight: bold;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .control-group {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        select, input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .btn {
            background: #17a2b8;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn:hover {
            background: #138496;
        }
        .btn.secondary {
            background: #6c757d;
        }
        .btn.secondary:hover {
            background: #545b62;
        }
        .btn.danger {
            background: #dc3545;
        }
        .btn.danger:hover {
            background: #c82333;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .data-table th,
        .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .data-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }
        .data-table tr:hover {
            background: #f8f9fa;
        }
        .finding-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .finding-item.crit { border-left-color: #dc3545; }
        .finding-item.high { border-left-color: #fd7e14; }
        .finding-item.med { border-left-color: #ffc107; }
        .finding-item.low { border-left-color: #28a745; }
        .finding-title {
            font-size: 1.1em;
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }
        .finding-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
        }
        .finding-description {
            color: #495057;
            margin-bottom: 10px;
        }
        .finding-evidence {
            background: #e9ecef;
            padding: 10px;
            border-radius: 4px;
            font-size: 13px;
            margin-bottom: 10px;
        }
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin: 20px 0;
        }
        .page-btn {
            padding: 8px 12px;
            border: 1px solid #dee2e6;
            background: white;
            border-radius: 4px;
            cursor: pointer;
        }
        .page-btn.active {
            background: #17a2b8;
            color: white;
            border-color: #17a2b8;
        }
        .page-btn.disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .analysis-form {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #495057;
        }
        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #17a2b8;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #17a2b8;
            margin: 5px 0;
        }
        .metric-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
        }
        .loading {
            text-align: center;
            color: #666;
            padding: 40px;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .success {
            color: #155724;
            background: #d4edda;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .analysis-result {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .analysis-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .summary-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #dee2e6;
            text-align: center;
        }
        .summary-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #17a2b8;
            margin: 5px 0;
        }
        .summary-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
        }
        .document-link {
            background: #e9ecef;
            padding: 8px 12px;
            border-radius: 4px;
            margin: 5px;
            display: inline-block;
            text-decoration: none;
            color: #495057;
            border: 1px solid #ced4da;
        }
        .document-link:hover {
            background: #dee2e6;
        }
        .badge {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 2px 5px 2px 0;
        }
        .badge.crit { background: #dc3545; }
        .badge.high { background: #fd7e14; }
        .badge.med { background: #ffc107; color: black; }
        .badge.low { background: #28a745; }
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
            display: none;
            align-items: center;
            justify-content: center;
        }
        .modal.active {
            display: flex;
        }
        .modal-content {
            background: white;
            padding: 20px;
            border-radius: 8px;
            max-width: 80%;
            max-height: 80%;
            overflow-y: auto;
        }
        .close-btn {
            float: right;
            background: #dc3545;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Analysis Dashboard</h1>
            <p>Monitor analysis results, findings, and document quality assessments</p>
        </div>

        <div id="summary-container" class="loading">Loading analysis status...</div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('findings')">Findings</div>
            <div class="tab" onclick="showTab('run-analysis')">Run Analysis</div>
            <div class="tab" onclick="showTab('reports')">Reports</div>
            <div class="tab" onclick="showTab('history')">History</div>
        </div>

        <div id="findings-content" class="tab-content active">
            <div class="controls">
                <div class="control-group">
                    <label>Severity:</label>
                    <select id="severity-filter">
                        <option value="">All Severities</option>
                        <option value="crit">Critical</option>
                        <option value="high">High</option>
                        <option value="med">Medium</option>
                        <option value="low">Low</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Type:</label>
                    <select id="type-filter">
                        <option value="">All Types</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Limit:</label>
                    <select id="findings-limit">
                        <option value="20">20</option>
                        <option value="50" selected>50</option>
                        <option value="100">100</option>
                    </select>
                </div>
                <button class="btn" onclick="loadFindings()">Load Findings</button>
                <button class="btn secondary" onclick="refreshFindings()">Refresh</button>
            </div>
            <div id="findings-container" class="loading">Loading findings...</div>
        </div>

        <div id="run-analysis-content" class="tab-content">
            <div class="analysis-form">
                <h3>Run New Analysis</h3>
                <form id="analysis-form">
                    <div class="form-group">
                        <label for="targets">Document IDs/URLs (one per line):</label>
                        <textarea id="targets" placeholder="Enter document IDs or API URLs, one per line"></textarea>
                    </div>
                    <div class="form-group">
                        <label for="analysis-type">Analysis Type:</label>
                        <select id="analysis-type">
                            <option value="consistency">Consistency</option>
                            <option value="reporting">Reporting</option>
                            <option value="combined">Combined</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="options">Options (JSON):</label>
                        <textarea id="options" placeholder='{"key": "value"}'></textarea>
                    </div>
                    <button type="submit" class="btn">Run Analysis</button>
                </form>
            </div>
            <div id="analysis-result" style="display: none;"></div>
        </div>

        <div id="reports-content" class="tab-content">
            <div class="controls">
                <button class="btn" onclick="loadConfluenceReport()">Confluence Consolidation</button>
                <button class="btn" onclick="loadJiraReport()">Jira Staleness</button>
                <button class="btn secondary" onclick="generateSummaryReport()">Summary Report</button>
            </div>
            <div id="reports-container" class="loading">Select a report to load...</div>
        </div>

        <div id="history-content" class="tab-content">
            <button class="btn" onclick="loadAnalysisHistory()">Load Analysis History</button>
            <div id="history-container" class="loading">Loading analysis history...</div>
        </div>
    </div>

    <div id="modal" class="modal">
        <div class="modal-content">
            <button class="close-btn" onclick="closeModal()">×</button>
            <div id="modal-content"></div>
        </div>
    </div>

    <script>
        let currentFindingsOffset = 0;
        let currentAnalysisOffset = 0;

        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }

        async function loadSummary() {
            try {
                const response = await fetch('/api/analysis/status');
                const data = await response.json();

                if (data.success) {
                    renderSummary(data.data);
                } else {
                    document.getElementById('summary-container').innerHTML =
                        '<div class="error">Failed to load summary: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('summary-container').innerHTML =
                    '<div class="error">Failed to load summary: ' + error.message + '</div>';
            }
        }

        function renderSummary(data) {
            const stats = data.analysis_stats || {};
            const detectors = data.detectors || [];

            let html = '<div class="status-grid">';

            // Analysis stats
            html += `
                <div class="status-card">
                    <div class="status-label">Total Analyses</div>
                    <div class="status-value">${stats.total_analyses || 0}</div>
                    <div>Executed</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Total Findings</div>
                    <div class="status-value">${stats.total_findings || 0}</div>
                    <div>Detected Issues</div>
                </div>
                <div class="status-card success">
                    <div class="status-label">Detectors</div>
                    <div class="status-value">${detectors.length}</div>
                    <div>Available</div>
                </div>
            `;

            html += '</div>';

            // Severity breakdown
            if (stats.severity_breakdown) {
                html += '<h4>Finding Severity Breakdown</h4><div class="metric-grid">';
                Object.entries(stats.severity_breakdown).forEach(([severity, count]) => {
                    const severityClass = severity.toLowerCase();
                    html += `
                        <div class="metric-item">
                            <div class="metric-label">${severity.toUpperCase()}</div>
                            <div class="metric-value">${count}</div>
                        </div>
                    `;
                });
                html += '</div>';
            }

            document.getElementById('summary-container').innerHTML = html;
        }

        async function loadFindings() {
            const severity = document.getElementById('severity-filter').value;
            const findingType = document.getElementById('type-filter').value;
            const limit = document.getElementById('findings-limit').value;

            document.getElementById('findings-container').innerHTML = 'Loading findings...';

            let url = `/api/analysis/findings?limit=${limit}&offset=${currentFindingsOffset}`;
            if (severity) url += `&severity=${severity}`;
            if (findingType) url += `&finding_type=${findingType}`;

            try {
                const response = await fetch(url);
                const data = await response.json();

                if (data.success) {
                    renderFindings(data.data);
                    updateTypeFilter(data.data);
                } else {
                    document.getElementById('findings-container').innerHTML =
                        '<div class="error">Failed to load findings: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('findings-container').innerHTML =
                    '<div class="error">Failed to load findings: ' + error.message + '</div>';
            }
        }

        function renderFindings(data) {
            const findings = data.findings || [];
            const total = data.total || 0;
            const limit = data.limit || 20;

            if (findings.length === 0) {
                document.getElementById('findings-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No findings found</div>';
                return;
            }

            let html = '';

            findings.forEach(finding => {
                const severityClass = finding.severity || 'low';
                const detectedAt = finding.detected_at ? new Date(finding.detected_at).toLocaleString() : 'Unknown';

                html += `
                    <div class="finding-item ${severityClass}" onclick="showFindingDetails('${finding.id}')">
                        <div class="finding-title">${finding.title || finding.description || 'Untitled Finding'}</div>
                        <div class="finding-meta">
                            <span><span class="badge ${severityClass}">${finding.severity || 'low'}</span></span>
                            <span><span class="badge">${finding.type || 'unknown'}</span></span>
                            <span>Detected: ${detectedAt}</span>
                        </div>
                        <div class="finding-description">${finding.description || 'No description available'}</div>
                        ${finding.suggestion ? `<div><strong>Suggestion:</strong> ${finding.suggestion}</div>` : ''}
                    </div>
                `;
            });

            // Pagination
            const hasNext = (currentFindingsOffset + limit) < total;
            const hasPrev = currentFindingsOffset > 0;

            html += '<div class="pagination">';
            html += `<button class="page-btn ${hasPrev ? '' : 'disabled'}" onclick="prevFindingsPage()">Previous</button>`;
            html += `<span>Page ${Math.floor(currentFindingsOffset / limit) + 1} of ${Math.ceil(total / limit)}</span>`;
            html += `<button class="page-btn ${hasNext ? '' : 'disabled'}" onclick="nextFindingsPage()">Next</button>`;
            html += '</div>';

            document.getElementById('findings-container').innerHTML = html;
        }

        function updateTypeFilter(data) {
            // This would populate the type filter with available finding types
            // For now, we'll add some common types
            const select = document.getElementById('type-filter');
            const currentValue = select.value;

            const types = ['missing_doc', 'contradiction', 'drift', 'stale', 'broken_link', 'schema_mismatch'];
            select.innerHTML = '<option value="">All Types</option>';

            types.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type.replace(/_/g, ' ');
                if (type === currentValue) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        }

        async function runAnalysis(event) {
            event.preventDefault();

            const targets = document.getElementById('targets').value.split('\\n').filter(t => t.trim());
            const analysisType = document.getElementById('analysis-type').value;
            let options = {};

            try {
                const optionsText = document.getElementById('options').value.trim();
                if (optionsText) {
                    options = JSON.parse(optionsText);
                }
            } catch (e) {
                alert('Invalid JSON in options field');
                return;
            }

            if (targets.length === 0) {
                alert('Please enter at least one target');
                return;
            }

            document.getElementById('analysis-result').innerHTML = '<div class="loading">Running analysis...</div>';
            document.getElementById('analysis-result').style.display = 'block';

            try {
                const response = await fetch('/api/analysis/run', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        targets: targets,
                        analysis_type: analysisType,
                        options: options
                    })
                });

                const data = await response.json();

                if (data.success) {
                    renderAnalysisResult(data.data);
                } else {
                    document.getElementById('analysis-result').innerHTML =
                        '<div class="error">Analysis failed: ' + (data.message || 'Unknown error') + '</div>';
                }
            } catch (error) {
                document.getElementById('analysis-result').innerHTML =
                    '<div class="error">Analysis failed: ' + error.message + '</div>';
            }
        }

        function renderAnalysisResult(data) {
            const result = data.results || {};

            let html = '<div class="analysis-result">';
            html += '<h4>Analysis Results</h4>';

            html += '<div class="analysis-summary">';
            html += `
                <div class="summary-item">
                    <div class="summary-label">Analysis ID</div>
                    <div class="summary-value">${data.analysis_id || 'N/A'}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Findings</div>
                    <div class="summary-value">${data.findings_count || 0}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Targets</div>
                    <div class="summary-value">${data.results?.targets?.length || 0}</div>
                </div>
            `;
            html += '</div>';

            if (result.findings && result.findings.length > 0) {
                html += '<h5>Findings:</h5>';
                result.findings.forEach(finding => {
                    const severityClass = finding.severity || 'low';
                    html += `
                        <div class="finding-item ${severityClass}">
                            <div class="finding-title">${finding.title || finding.description || 'Finding'}</div>
                            <div class="finding-description">${finding.description || 'No description'}</div>
                        </div>
                    `;
                });
            }

            html += '</div>';
            document.getElementById('analysis-result').innerHTML = html;
        }

        async function loadConfluenceReport() {
            document.getElementById('reports-container').innerHTML = 'Loading Confluence report...';

            try {
                const response = await fetch('/api/analysis/reports/confluence_consolidation');
                const data = await response.json();

                if (data.success) {
                    renderReport(data.data, 'Confluence Consolidation');
                } else {
                    document.getElementById('reports-container').innerHTML =
                        '<div class="error">Failed to load report: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('reports-container').innerHTML =
                    '<div class="error">Failed to load report: ' + error.message + '</div>';
            }
        }

        async function loadJiraReport() {
            document.getElementById('reports-container').innerHTML = 'Loading Jira report...';

            try {
                const response = await fetch('/api/analysis/reports/jira_staleness');
                const data = await response.json();

                if (data.success) {
                    renderReport(data.data, 'Jira Staleness');
                } else {
                    document.getElementById('reports-container').innerHTML =
                        '<div class="error">Failed to load report: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('reports-container').innerHTML =
                    '<div class="error">Failed to load report: ' + error.message + '</div>';
            }
        }

        async function generateSummaryReport() {
            document.getElementById('reports-container').innerHTML = 'Generating summary report...';

            try {
                const response = await fetch('/api/analysis/reports/summary');
                const data = await response.json();

                if (data.success) {
                    renderReport(data.data, 'Summary Report');
                } else {
                    document.getElementById('reports-container').innerHTML =
                        '<div class="error">Failed to generate report: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('reports-container').innerHTML =
                    '<div class="error">Failed to generate report: ' + error.message + '</div>';
            }
        }

        function renderReport(data, title) {
            let html = `<h4>${title}</h4>`;

            if (typeof data === 'object') {
                html += '<div class="analysis-result"><pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
            } else {
                html += '<div class="analysis-result"><p>' + String(data) + '</p></div>';
            }

            document.getElementById('reports-container').innerHTML = html;
        }

        async function loadAnalysisHistory() {
            document.getElementById('history-container').innerHTML = 'Loading analysis history...';

            try {
                const response = await fetch('/api/analysis/history');
                const data = await response.json();

                if (data.success) {
                    renderAnalysisHistory(data.data.history);
                } else {
                    document.getElementById('history-container').innerHTML =
                        '<div class="error">Failed to load history: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('history-container').innerHTML =
                    '<div class="error">Failed to load history: ' + error.message + '</div>';
            }
        }

        function renderAnalysisHistory(history) {
            if (!history || history.length === 0) {
                document.getElementById('history-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No analysis history available</div>';
                return;
            }

            let html = '<table class="data-table"><thead><tr>';
            html += '<th>Analysis ID</th><th>Type</th><th>Targets</th><th>Findings</th><th>Timestamp</th><th>Actions</th>';
            html += '</tr></thead><tbody>';

            history.forEach(analysis => {
                const timestamp = analysis.timestamp ? new Date(analysis.timestamp).toLocaleString() : 'Unknown';
                const targets = analysis.targets || [];
                const findingsCount = analysis.findings ? analysis.findings.length : 0;

                html += `
                    <tr>
                        <td>${analysis.id}</td>
                        <td>${analysis.analysis_type || 'Unknown'}</td>
                        <td>${targets.length} targets</td>
                        <td>${findingsCount} findings</td>
                        <td>${timestamp}</td>
                        <td><button class="btn" onclick="viewAnalysis('${analysis.id}')">View</button></td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
            document.getElementById('history-container').innerHTML = html;
        }

        async function viewAnalysis(analysisId) {
            try {
                const response = await fetch(`/api/analysis/results/${analysisId}`);
                const data = await response.json();

                if (data.success) {
                    showAnalysisModal(data.data);
                } else {
                    alert('Failed to load analysis: ' + (data.message || 'Unknown error'));
                }
            } catch (error) {
                alert('Failed to load analysis: ' + error.message);
            }
        }

        async function showFindingDetails(findingId) {
            try {
                const response = await fetch(`/api/analysis/findings/${findingId}`);
                const data = await response.json();

                if (data.success) {
                    showFindingModal(data.data);
                } else {
                    alert('Failed to load finding: ' + (data.message || 'Unknown error'));
                }
            } catch (error) {
                alert('Failed to load finding: ' + error.message);
            }
        }

        function showAnalysisModal(data) {
            const analysis = data.analysis || {};
            const documents = data.linked_documents || [];

            let html = `<h3>Analysis: ${analysis.id}</h3>`;
            html += `<p><strong>Type:</strong> ${analysis.analysis_type || 'Unknown'}</p>`;
            html += `<p><strong>Timestamp:</strong> ${analysis.timestamp || 'Unknown'}</p>`;
            html += `<p><strong>Targets:</strong> ${analysis.targets ? analysis.targets.join(', ') : 'None'}</p>`;

            if (documents.length > 0) {
                html += '<h4>Linked Documents:</h4>';
                documents.forEach(doc => {
                    html += `<div class="document-link" onclick="viewDocument('${doc.id}')">${doc.id}</div>`;
                });
            }

            if (analysis.findings && analysis.findings.length > 0) {
                html += '<h4>Findings:</h4>';
                analysis.findings.forEach(finding => {
                    const severityClass = finding.severity || 'low';
                    html += `
                        <div class="finding-item ${severityClass}">
                            <div class="finding-title">${finding.title || finding.description || 'Finding'}</div>
                            <div class="finding-description">${finding.description || 'No description'}</div>
                        </div>
                    `;
                });
            }

            document.getElementById('modal-content').innerHTML = html;
            document.getElementById('modal').classList.add('active');
        }

        function showFindingModal(data) {
            const finding = data.finding || {};

            let html = `<h3>Finding: ${finding.id}</h3>`;
            html += `<p><strong>Type:</strong> ${finding.type || 'Unknown'}</p>`;
            html += `<p><strong>Severity:</strong> ${finding.severity || 'Unknown'}</p>`;
            html += `<p><strong>Title:</strong> ${finding.title || 'No title'}</p>`;
            html += `<p><strong>Description:</strong> ${finding.description || 'No description'}</p>`;

            if (finding.suggestion) {
                html += `<p><strong>Suggestion:</strong> ${finding.suggestion}</p>`;
            }

            if (finding.evidence && finding.evidence.length > 0) {
                html += '<h4>Evidence:</h4><div class="finding-evidence">';
                finding.evidence.forEach(evidence => {
                    html += `<div>• ${evidence}</div>`;
                });
                html += '</div>';
            }

            if (data.analysis_id) {
                html += `<p><strong>From Analysis:</strong> ${data.analysis_id}</p>`;
            }

            document.getElementById('modal-content').innerHTML = html;
            document.getElementById('modal').classList.add('active');
        }

        function viewDocument(docId) {
            // This would open the document browser
            window.open(`/doc-store/browser?doc=${docId}`, '_blank');
        }

        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }

        function prevFindingsPage() {
            const limit = parseInt(document.getElementById('findings-limit').value);
            if (currentFindingsOffset >= limit) {
                currentFindingsOffset -= limit;
                loadFindings();
            }
        }

        function nextFindingsPage() {
            const limit = parseInt(document.getElementById('findings-limit').value);
            currentFindingsOffset += limit;
            loadFindings();
        }

        function refreshFindings() {
            currentFindingsOffset = 0;
            loadFindings();
        }

        // Event listeners
        document.getElementById('analysis-form').addEventListener('submit', runAnalysis);

        // Load initial data
        loadSummary();
    </script>
</body>
</html>
            """
            return create_html_response(html, "Analysis Dashboard")
        except Exception as e:
            return handle_frontend_error("render analysis dashboard", e, **build_frontend_context("render_analysis_dashboard"))

    @staticmethod
    def handle_services_overview() -> HTMLResponse:
        """Render comprehensive services overview dashboard."""
        try:
            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Services Overview - LLM Documentation Ecosystem</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1800px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .service-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #17a2b8;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .service-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .service-card.unhealthy {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .service-card.warning {
            border-left-color: #ffc107;
            background: #fffbf0;
        }
        .service-card.success {
            border-left-color: #28a745;
            background: #f8fff8;
        }
        .service-name {
            font-size: 1.4em;
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }
        .service-description {
            color: #666;
            margin-bottom: 15px;
            font-size: 0.9em;
        }
        .service-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }
        .metric-item {
            background: white;
            padding: 8px 12px;
            border-radius: 6px;
            text-align: center;
            border: 1px solid #dee2e6;
        }
        .metric-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #17a2b8;
            display: block;
        }
        .metric-label {
            font-size: 0.8em;
            color: #666;
            text-transform: uppercase;
        }
        .service-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .btn {
            background: #17a2b8;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: #138496;
        }
        .btn.secondary {
            background: #6c757d;
        }
        .btn.secondary:hover {
            background: #545b62;
        }
        .btn.small {
            padding: 4px 8px;
            font-size: 11px;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 6px;
        }
        .status-indicator.healthy {
            background: #28a745;
        }
        .status-indicator.unhealthy {
            background: #dc3545;
        }
        .status-indicator.warning {
            background: #ffc107;
        }
        .status-indicator.unknown {
            background: #6c757d;
        }
        .service-status {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .last-updated {
            font-size: 0.8em;
            color: #666;
            margin-top: 10px;
        }
        .loading {
            text-align: center;
            color: #666;
            padding: 40px;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .system-health {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
        }
        .health-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .health-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        .health-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #17a2b8;
            margin: 5px 0;
        }
        .health-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
        }
        .refresh-controls {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .badge {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 10px;
            margin: 2px 4px 2px 0;
        }
        .badge.has-viz {
            background: #28a745;
        }
        .badge.no-viz {
            background: #ffc107;
            color: black;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Services Overview</h1>
            <p>Comprehensive monitoring and visualization of all ecosystem services</p>
        </div>

        <div class="refresh-controls">
            <button class="btn" onclick="refreshAllServices()">Refresh All Services</button>
            <button class="btn secondary" onclick="loadSystemHealth()">Load System Health</button>
        </div>

        <div id="system-health-container" class="loading">Loading system health...</div>

        <div id="services-container" class="loading">Loading services...</div>
    </div>

    <script>
        let servicesData = {};
        let systemHealth = {};

        async function loadSystemHealth() {
            document.getElementById('system-health-container').innerHTML = 'Loading system health...';

            try {
                const response = await fetch('/api/orchestrator/health');
                const data = await response.json();

                if (data.success) {
                    systemHealth = data.data;
                    renderSystemHealth();
                } else {
                    document.getElementById('system-health-container').innerHTML =
                        '<div class="error">Failed to load system health: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('system-health-container').innerHTML =
                    '<div class="error">Failed to load system health: ' + error.message + '</div>';
            }
        }

        function renderSystemHealth() {
            const isHealthy = systemHealth.orchestrator_healthy;
            const serviceCount = systemHealth.service ? 1 : 0; // Simplified

            let html = '<div class="system-health">';
            html += '<h3>System Health Overview</h3>';
            html += '<div class="health-summary">';

            html += `
                <div class="health-item">
                    <div class="health-label">Overall Status</div>
                    <div class="health-value">
                        <span class="status-indicator ${isHealthy ? 'healthy' : 'unhealthy'}"></span>
                        ${isHealthy ? 'Healthy' : 'Issues Detected'}
                    </div>
                </div>
                <div class="health-item">
                    <div class="health-label">Services Monitored</div>
                    <div class="health-value">${serviceCount}</div>
                </div>
                <div class="health-item">
                    <div class="health-label">Last Checked</div>
                    <div class="health-value">${new Date(systemHealth.last_checked).toLocaleString()}</div>
                </div>
            `;

            html += '</div></div>';
            document.getElementById('system-health-container').innerHTML = html;
        }

        async function loadServicesOverview() {
            document.getElementById('services-container').innerHTML = 'Loading services...';

            try {
                // Load multiple service statuses in parallel
                const servicePromises = [
                    loadServiceStatus('doc-store', '/api/doc-store/status'),
                    loadServiceStatus('prompt-store', '/api/prompt-store/status'),
                    loadServiceStatus('analysis-service', '/api/analysis/status'),
                    loadServiceStatus('orchestrator', '/api/orchestrator/status'),
                    loadServiceStatus('summarizer-hub', '/api/summarizer/status'),
                    loadServiceStatus('log-collector', '/api/logs/status'),
                    // Add other services that may not have full APIs yet
                    createServiceCard('bedrock-proxy', {healthy: false, description: 'AI invocation proxy service'}),
                    createServiceCard('code-analyzer', {healthy: false, description: 'Code analysis and security scanning'}),
                    createServiceCard('discovery-agent', {healthy: false, description: 'Document and resource discovery'}),
                    createServiceCard('github-mcp', {healthy: false, description: 'GitHub Model Context Protocol'}),
                    createServiceCard('interpreter', {healthy: false, description: 'Natural language intent processing'}),
                    createServiceCard('memory-agent', {healthy: false, description: 'Operational memory management'}),
                    createServiceCard('notification-service', {healthy: false, description: 'Notification and alert management'}),
                    createServiceCard('secure-analyzer', {healthy: false, description: 'Security analysis and suggestions'}),
                    createServiceCard('source-agent', {healthy: false, description: 'Source code and document fetching'})
                ];

                const services = await Promise.all(servicePromises);
                renderServicesGrid(services.filter(s => s)); // Filter out nulls

            } catch (error) {
                document.getElementById('services-container').innerHTML =
                    '<div class="error">Failed to load services: ' + error.message + '</div>';
            }
        }

        async function loadServiceStatus(serviceName, apiEndpoint) {
            try {
                const response = await fetch(apiEndpoint);
                const data = await response.json();

                if (data.success) {
                    return {
                        name: serviceName,
                        status: data.data,
                        hasVisualization: true,
                        lastUpdated: new Date().toISOString()
                    };
                }
            } catch (error) {
                // Service not available
            }
            return null;
        }

        function createServiceCard(serviceName, defaults) {
            return {
                name: serviceName,
                status: defaults,
                hasVisualization: false,
                lastUpdated: new Date().toISOString()
            };
        }

        function renderServicesGrid(services) {
            let html = '<div class="services-grid">';

            services.forEach(service => {
                const status = service.status || {};
                const isHealthy = status.healthy !== false; // Assume healthy if not explicitly false
                const hasViz = service.hasVisualization;

                let cardClass = 'service-card';
                if (!isHealthy) cardClass += ' unhealthy';
                else if (hasViz) cardClass += ' success';

                html += `<div class="${cardClass}">`;

                // Service header
                html += `<div class="service-name">${formatServiceName(service.name)}</div>`;
                html += `<div class="service-description">${status.description || 'Service description not available'}</div>`;

                // Status indicator
                const statusClass = isHealthy ? 'healthy' : 'unhealthy';
                const statusText = isHealthy ? 'Operational' : 'Issues';
                html += `<div class="service-status">`;
                html += `<span class="status-indicator ${statusClass}"></span>`;
                html += `${statusText}`;
                html += `<span class="badge ${hasViz ? 'has-viz' : 'no-viz'}">${hasViz ? 'Has Viz' : 'No Viz'}</span>`;
                html += `</div>`;

                // Metrics (if available)
                if (status.analysis_stats || status.workflow_stats || status.invocation_stats) {
                    html += '<div class="service-metrics">';

                    if (status.analysis_stats) {
                        const stats = status.analysis_stats;
                        html += `
                            <div class="metric-item">
                                <span class="metric-value">${stats.total_analyses || 0}</span>
                                <span class="metric-label">Analyses</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-value">${stats.total_findings || 0}</span>
                                <span class="metric-label">Findings</span>
                            </div>
                        `;
                    }

                    if (status.workflow_stats) {
                        const stats = status.workflow_stats;
                        html += `
                            <div class="metric-item">
                                <span class="metric-value">${stats.total_workflows || 0}</span>
                                <span class="metric-label">Workflows</span>
                            </div>
                        `;
                    }

                    if (status.invocation_stats) {
                        const stats = status.invocation_stats;
                        html += `
                            <div class="metric-item">
                                <span class="metric-value">${stats.total_invocations || 0}</span>
                                <span class="metric-label">Invocations</span>
                            </div>
                        `;
                    }

                    html += '</div>';
                }

                // Actions
                html += '<div class="service-actions">';

                if (hasViz) {
                    const dashboardUrl = getServiceDashboardUrl(service.name);
                    if (dashboardUrl) {
                        html += `<a href="${dashboardUrl}" class="btn">Dashboard</a>`;
                    }
                    html += `<button class="btn secondary small" onclick="refreshService('${service.name}')">Refresh</button>`;
                } else {
                    html += `<button class="btn secondary small" onclick="checkService('${service.name}')">Check Status</button>`;
                }

                html += '</div>';

                // Last updated
                html += `<div class="last-updated">Last updated: ${new Date(service.lastUpdated).toLocaleString()}</div>`;

                html += '</div>';
            });

            html += '</div>';
            document.getElementById('services-container').innerHTML = html;
        }

        function formatServiceName(name) {
            return name.split('-').map(word =>
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
        }

        function getServiceDashboardUrl(serviceName) {
            const dashboards = {
                'doc-store': '/doc-store/browser',
                'prompt-store': '/prompt-store/browser',
                'analysis-service': '/analysis/dashboard',
                'orchestrator': '/orchestrator/monitor',
                'summarizer-hub': '/summarizer/status',
                'log-collector': '/logs/dashboard'
            };
            return dashboards[serviceName];
        }

        async function refreshService(serviceName) {
            // Refresh individual service status
            const apiEndpoint = getServiceApiEndpoint(serviceName);
            if (apiEndpoint) {
                await loadServiceStatus(serviceName, apiEndpoint);
                await loadServicesOverview(); // Reload all
            }
        }

        function getServiceApiEndpoint(serviceName) {
            const endpoints = {
                'doc-store': '/api/doc-store/status',
                'prompt-store': '/api/prompt-store/status',
                'analysis-service': '/api/analysis/status',
                'orchestrator': '/api/orchestrator/status',
                'summarizer-hub': '/api/summarizer/status',
                'log-collector': '/api/logs/status'
            };
            return endpoints[serviceName];
        }

        async function checkService(serviceName) {
            // Basic health check for services without full APIs
            alert(`Service ${serviceName} health check not implemented yet.`);
        }

        async function refreshAllServices() {
            await loadSystemHealth();
            await loadServicesOverview();
        }

        // Load initial data
        loadSystemHealth();
        loadServicesOverview();
    </script>
</body>
</html>
            """
            return create_html_response(html, "Services Overview")
        except Exception as e:
            return handle_frontend_error("render services overview", e, **build_frontend_context("render_services_overview"))


# Create singleton instance
ui_handlers = UIHandlers()
