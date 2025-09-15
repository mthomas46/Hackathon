"""Source Agent UI handlers for Frontend service.

Handles source agent service visualization, including document fetching,
data normalization, and code analysis operations across GitHub, Jira, and Confluence.
"""
from typing import Dict, Any
from fastapi.responses import HTMLResponse

from ..shared_utils import (
    get_frontend_clients,
    fetch_service_data,
    create_html_response,
    handle_frontend_error,
    build_frontend_context
)
from ..source_agent_monitor import source_agent_monitor


class SourceAgentUIHandlers:
    """Handles source agent UI rendering."""

    @staticmethod
    def handle_source_agent_dashboard() -> HTMLResponse:
        """Render source agent service monitoring dashboard."""
        try:
            clients = get_frontend_clients()

            # Get source agent status and cached data
            status_data = source_agent_monitor.get_source_status()
            fetch_history = source_agent_monitor.get_fetch_history(limit=20)
            normalization_history = source_agent_monitor.get_normalization_history(limit=20)
            analysis_history = source_agent_monitor.get_analysis_history(limit=20)

            # Build context for template
            context = {
                "health": status_data.get("health", {}),
                "sources": status_data.get("sources", {}),
                "operation_stats": status_data.get("operation_stats", {}),
                "recent_fetches": fetch_history,
                "recent_normalizations": normalization_history,
                "recent_analyses": analysis_history,
                "last_updated": status_data.get("last_updated", "Never")
            }

            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Source Agent Dashboard - LLM Documentation Ecosystem</title>
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
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #17a2b8;
        }
        .status-card.healthy {
            border-left-color: #28a745;
            background: #f8fff8;
        }
        .status-card.unhealthy {
            border-left-color: #dc3545;
            background: #fff5f5;
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
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
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
        .btn.success {
            background: #28a745;
        }
        .btn.success:hover {
            background: #1e7e34;
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
        .fetch-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .fetch-item.success {
            border-left-color: #28a745;
            background: #f8fff8;
        }
        .fetch-item.failed {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .fetch-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .fetch-content {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
            max-height: 100px;
            overflow-y: auto;
        }
        .normalization-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .normalization-item.success {
            border-left-color: #28a745;
            background: #f8fff8;
        }
        .normalization-item.failed {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .normalization-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .analysis-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .analysis-item.success {
            border-left-color: #28a745;
            background: #f8fff8;
        }
        .analysis-item.failed {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .analysis-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .analysis-content {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
            max-height: 120px;
            overflow-y: auto;
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
        .badge.github {
            background: #24292f;
        }
        .badge.jira {
            background: #0052cc;
        }
        .badge.confluence {
            background: #172b4d;
        }
        .badge.success {
            background: #28a745;
        }
        .badge.failed {
            background: #dc3545;
        }
        .badge.endpoint {
            background: #17a2b8;
        }
        .badge.pattern {
            background: #6c757d;
        }
        .test-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .test-form {
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
        }
        .form-group label {
            font-weight: 500;
            margin-bottom: 5px;
            color: #495057;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
        }
        .form-group textarea {
            min-height: 80px;
            resize: vertical;
        }
        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
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
            color: #28a745;
            background: #d4edda;
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
        .tab-container {
            margin: 20px 0;
        }
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .tab-btn {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .tab-btn.active {
            background: #17a2b8;
            color: white;
            border-color: #17a2b8;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .source-info {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .source-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        .source-card {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .source-name {
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }
        .capability-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .capability-list li {
            background: #e9ecef;
            color: #495057;
            padding: 4px 8px;
            margin: 2px 0;
            border-radius: 12px;
            font-size: 12px;
            display: inline-block;
            margin-right: 5px;
        }
        .document-preview {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            max-height: 150px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        .endpoints-list {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            max-height: 120px;
            overflow-y: auto;
        }
        .endpoint-item {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 8px;
            margin: 5px 0;
            font-family: monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Source Agent Dashboard</h1>
            <p>Monitor document fetching, normalization, and code analysis across GitHub, Jira, and Confluence</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="refreshStatus()">Refresh Status</button>
            <button class="btn secondary" onclick="loadHistory()">Load Full History</button>
        </div>

        <div id="status-container">
            <!-- Status will be loaded here -->
        </div>

        <div class="source-info">
            <h3>Supported Sources</h3>
            <div id="sources-info">
                <!-- Sources will be loaded here -->
            </div>
        </div>

        <div class="tab-container">
            <div class="tab-buttons">
                <button class="tab-btn active" onclick="showTab('fetch')">Document Fetching</button>
                <button class="tab-btn" onclick="showTab('normalize')">Data Normalization</button>
                <button class="tab-btn" onclick="showTab('analyze')">Code Analysis</button>
            </div>

            <div id="fetch-tab" class="tab-content active">
                <div class="test-section">
                    <h3>Fetch Document</h3>
                    <form class="test-form" onsubmit="fetchDocument(event)">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="fetch-source">Source:</label>
                                <select id="fetch-source">
                                    <option value="github">GitHub</option>
                                    <option value="jira">Jira</option>
                                    <option value="confluence">Confluence</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="fetch-identifier">Identifier:</label>
                                <input type="text" id="fetch-identifier" placeholder="owner:repo or issue-key or page-id" value="microsoft:vscode">
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="fetch-scope">Scope (JSON, optional):</label>
                            <textarea id="fetch-scope" placeholder='{"include_readme": true, "include_prs": false}'>{"include_readme": true}</textarea>
                        </div>
                        <button type="submit" class="btn">Fetch Document</button>
                    </form>
                    <div id="fetch-result" style="margin-top: 20px;"></div>
                </div>

                <div id="fetches-container">
                    <!-- Recent fetches will be loaded here -->
                </div>
            </div>

            <div id="normalize-tab" class="tab-content">
                <div class="test-section">
                    <h3>Normalize Data</h3>
                    <form class="test-form" onsubmit="normalizeData(event)">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="normalize-source">Source:</label>
                                <select id="normalize-source">
                                    <option value="github">GitHub</option>
                                    <option value="jira">Jira</option>
                                    <option value="confluence">Confluence</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="normalize-correlation-id">Correlation ID (optional):</label>
                                <input type="text" id="normalize-correlation-id" placeholder="trace-123">
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="normalize-data">Raw Data (JSON):</label>
                            <textarea id="normalize-data" placeholder='{"type": "pr", "number": 123, "title": "Add feature", "body": "PR description..."}'>{
  "type": "pr",
  "number": 123,
  "title": "Add new feature",
  "body": "This PR adds a new feature to improve user experience.",
  "html_url": "https://github.com/owner/repo/pull/123",
  "base": {"repo": {"full_name": "owner/repo"}}
}</textarea>
                        </div>
                        <button type="submit" class="btn">Normalize Data</button>
                    </form>
                    <div id="normalize-result" style="margin-top: 20px;"></div>
                </div>

                <div id="normalizations-container">
                    <!-- Recent normalizations will be loaded here -->
                </div>
            </div>

            <div id="analyze-tab" class="tab-content">
                <div class="test-section">
                    <h3>Analyze Code</h3>
                    <form class="test-form" onsubmit="analyzeCode(event)">
                        <div class="form-group">
                            <label for="analyze-text">Code Text:</label>
                            <textarea id="analyze-text" placeholder="Paste code to analyze for API endpoints...">@app.get("/users")
async def get_users():
    return {"users": []}

@app.post("/users")
async def create_user(user: UserCreate):
    return {"user": user}

class UserAPI:
    @staticmethod
    def find_by_id(user_id: int):
        return {"user": {"id": user_id}}</textarea>
                        </div>
                        <button type="submit" class="btn">Analyze Code</button>
                    </form>
                    <div id="analyze-result" style="margin-top: 20px;"></div>
                </div>

                <div id="analyses-container">
                    <!-- Recent analyses will be loaded here -->
                </div>
            </div>
        </div>
    </div>

    <script>
        let sourceData = {
            status: {},
            sources: {},
            operation_stats: {},
            fetches: [],
            normalizations: [],
            analyses: [],
            last_updated: null
        };

        async function loadSourceStatus() {
            try {
                const response = await fetch('/api/source-agent/status');
                const data = await response.json();

                if (data.success) {
                    sourceData = data.data;
                    renderSourceStatus();
                    renderSourcesInfo();
                    renderRecentFetches();
                    renderRecentNormalizations();
                    renderRecentAnalyses();
                } else {
                    document.getElementById('status-container').innerHTML =
                        '<div class="error">Failed to load source agent status: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Failed to load source agent status: ' + error.message + '</div>';
            }
        }

        function renderSourceStatus() {
            const health = sourceData.status || {};
            const stats = sourceData.operation_stats || {};

            let html = '<div class="status-grid">';

            // Service health
            const isHealthy = health.status === 'healthy';
            html += `
                <div class="status-card ${isHealthy ? 'healthy' : 'unhealthy'}">
                    <div class="status-label">Service Status</div>
                    <div class="status-value">${health.status || 'Unknown'}</div>
                    <div>Source Agent</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Total Operations</div>
                    <div class="status-value">${stats.total_operations || 0}</div>
                    <div>All sources</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Success Rate</div>
                    <div class="status-value">${stats.success_rate || 0}%</div>
                    <div>Operation success</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Fetch Operations</div>
                    <div class="status-value">${stats.fetch_operations || 0}</div>
                    <div>Document fetches</div>
                </div>
            `;

            html += '</div>';

            // Additional statistics
            if (stats.total_operations > 0) {
                html += '<h4>Operation Statistics</h4><div class="metric-grid">';

                html += `
                    <div class="metric-item">
                        <div class="metric-label">Normalizations</div>
                        <div class="metric-value">${stats.normalization_operations || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Code Analyses</div>
                        <div class="metric-value">${stats.analysis_operations || 0}</div>
                    </div>
                `;

                html += '</div>';

                // Source distribution
                if (stats.source_distribution) {
                    html += '<h4>Source Distribution</h4><div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;">';
                    Object.entries(stats.source_distribution).forEach(([source, count]) => {
                        const sourceClass = source.toLowerCase();
                        html += `<span class="badge ${sourceClass}">${source}: ${count}</span>`;
                    });
                    html += '</div>';
                }
            }

            document.getElementById('status-container').innerHTML = html;
        }

        function renderSourcesInfo() {
            const sources = sourceData.sources || {};
            const sourcesList = sources.sources || [];
            const capabilities = sources.capabilities || {};

            if (sourcesList.length === 0) {
                document.getElementById('sources-info').innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">No sources information available</div>';
                return;
            }

            let html = '<div class="source-grid">';

            sourcesList.forEach(source => {
                const sourceCaps = capabilities[source] || [];
                const sourceClass = source.toLowerCase();

                html += `
                    <div class="source-card">
                        <div class="source-name">
                            <span class="badge ${sourceClass}">${source.toUpperCase()}</span>
                        </div>
                        <ul class="capability-list">
                            ${sourceCaps.map(cap => `<li>${cap.replace('_', ' ')}</li>`).join('')}
                        </ul>
                    </div>
                `;
            });

            html += '</div>';

            document.getElementById('sources-info').innerHTML = html;
        }

        function renderRecentFetches() {
            const fetches = sourceData.fetches || [];

            if (fetches.length === 0) {
                document.getElementById('fetches-container').innerHTML = '';
                return;
            }

            let html = '<h4>Recent Document Fetches</h4>';

            fetches.forEach(fetch => {
                const timestamp = new Date(fetch.timestamp).toLocaleString();
                const success = fetch.success;
                const source = fetch.source || 'unknown';

                html += `
                    <div class="fetch-item ${success ? 'success' : 'failed'}">
                        <div class="fetch-meta">
                            <span><strong>ID:</strong> ${fetch.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span><span class="badge ${source.toLowerCase()}">${source.toUpperCase()}</span></span>
                            <span><strong>Identifier:</strong> ${fetch.identifier || 'Unknown'}</span>
                            <span class="badge ${success ? 'success' : 'failed'}">${success ? 'SUCCESS' : 'FAILED'}</span>
                        </div>
                        ${fetch.scope ? `
                            <div class="fetch-content">Scope: ${JSON.stringify(fetch.scope, null, 2)}</div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('fetches-container').innerHTML = html;
        }

        function renderRecentNormalizations() {
            const normalizations = sourceData.normalizations || [];

            if (normalizations.length === 0) {
                document.getElementById('normalizations-container').innerHTML = '';
                return;
            }

            let html = '<h4>Recent Data Normalizations</h4>';

            normalizations.forEach(normalization => {
                const timestamp = new Date(normalization.timestamp).toLocaleString();
                const success = normalization.success;
                const source = normalization.source || 'unknown';
                const envelopeId = normalization.envelope_id;

                html += `
                    <div class="normalization-item ${success ? 'success' : 'failed'}">
                        <div class="normalization-meta">
                            <span><strong>ID:</strong> ${normalization.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span><span class="badge ${source.toLowerCase()}">${source.toUpperCase()}</span></span>
                            <span><strong>Envelope:</strong> ${envelopeId || 'N/A'}</span>
                            <span class="badge ${success ? 'success' : 'failed'}">${success ? 'SUCCESS' : 'FAILED'}</span>
                        </div>
                    </div>
                `;
            });

            document.getElementById('normalizations-container').innerHTML = html;
        }

        function renderRecentAnalyses() {
            const analyses = sourceData.analyses || [];

            if (analyses.length === 0) {
                document.getElementById('analyses-container').innerHTML = '';
                return;
            }

            let html = '<h4>Recent Code Analyses</h4>';

            analyses.forEach(analysis => {
                const timestamp = new Date(analysis.timestamp).toLocaleString();
                const success = analysis.success;
                const endpointCount = analysis.endpoint_count || 0;
                const patterns = analysis.patterns_found || [];

                html += `
                    <div class="analysis-item ${success ? 'success' : 'failed'}">
                        <div class="analysis-meta">
                            <span><strong>ID:</strong> ${analysis.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span><strong>Code Length:</strong> ${analysis.code_length} chars</span>
                            <span><strong>Endpoints:</strong> ${endpointCount}</span>
                            <span class="badge ${success ? 'success' : 'failed'}">${success ? 'SUCCESS' : 'FAILED'}</span>
                        </div>
                        ${patterns.length > 0 ? `
                            <div style="margin-top: 8px;">
                                <strong>Patterns:</strong> ${patterns.map(pattern => `<span class="badge pattern">${pattern}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('analyses-container').innerHTML = html;
        }

        async function fetchDocument(event) {
            event.preventDefault();

            const source = document.getElementById('fetch-source').value;
            const identifier = document.getElementById('fetch-identifier').value;
            const scopeText = document.getElementById('fetch-scope').value;

            if (!identifier) {
                alert('Please enter an identifier');
                return;
            }

            let scope = {};
            if (scopeText.trim()) {
                try {
                    scope = JSON.parse(scopeText);
                } catch (e) {
                    alert('Invalid JSON in scope: ' + e.message);
                    return;
                }
            }

            const resultDiv = document.getElementById('fetch-result');
            resultDiv.innerHTML = '<div style="color: #666;">Fetching document...</div>';

            try {
                const payload = { source, identifier, scope };

                const response = await fetch('/api/source-agent/fetch', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    const document = data.document || {};
                    resultDiv.innerHTML = `
                        <div class="success">
                            <strong>✓ Document Fetched Successfully</strong>
                        </div>
                        <div><strong>Fetch ID:</strong> ${data.fetch_id}</div>
                        <div><strong>Source:</strong> <span class="badge ${source.toLowerCase()}">${source.toUpperCase()}</span></div>
                        <div class="document-preview">${JSON.stringify(document, null, 2)}</div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="error">✗ Fetch failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new fetch
                loadSourceStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div class="error">✗ Error: ${error.message}</div>`;
            }
        }

        async function normalizeData(event) {
            event.preventDefault();

            const source = document.getElementById('normalize-source').value;
            const correlationId = document.getElementById('normalize-correlation-id').value;
            const dataText = document.getElementById('normalize-data').value;

            if (!dataText) {
                alert('Please enter data to normalize');
                return;
            }

            let data = {};
            try {
                data = JSON.parse(dataText);
            } catch (e) {
                alert('Invalid JSON in data: ' + e.message);
                return;
            }

            const resultDiv = document.getElementById('normalize-result');
            resultDiv.innerHTML = '<div style="color: #666;">Normalizing data...</div>';

            try {
                const payload = { source, data, correlation_id: correlationId || undefined };

                const response = await fetch('/api/source-agent/normalize', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    const envelope = data.envelope || {};
                    resultDiv.innerHTML = `
                        <div class="success">
                            <strong>✓ Data Normalized Successfully</strong>
                        </div>
                        <div><strong>Normalization ID:</strong> ${data.normalization_id}</div>
                        <div><strong>Source:</strong> <span class="badge ${source.toLowerCase()}">${source.toUpperCase()}</span></div>
                        <div class="document-preview">${JSON.stringify(envelope, null, 2)}</div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="error">✗ Normalization failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new normalization
                loadSourceStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div class="error">✗ Error: ${error.message}</div>`;
            }
        }

        async function analyzeCode(event) {
            event.preventDefault();

            const text = document.getElementById('analyze-text').value;

            if (!text) {
                alert('Please enter code to analyze');
                return;
            }

            const resultDiv = document.getElementById('analyze-result');
            resultDiv.innerHTML = '<div style="color: #666;">Analyzing code...</div>';

            try {
                const payload = { text };

                const response = await fetch('/api/source-agent/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    const endpointCount = data.endpoint_count || 0;
                    const patterns = data.patterns_found || [];
                    const analysis = data.analysis || '';

                    resultDiv.innerHTML = `
                        <div class="success">
                            <strong>✓ Code Analyzed Successfully</strong>
                        </div>
                        <div><strong>Analysis ID:</strong> ${data.analysis_id}</div>
                        <div><strong>Endpoints Found:</strong> <span class="badge endpoint">${endpointCount}</span></div>
                        ${patterns.length > 0 ? `
                            <div><strong>Patterns:</strong> ${patterns.map(pattern => `<span class="badge pattern">${pattern}</span>`).join('')}</div>
                        ` : ''}
                        <div class="analysis-content">${analysis}</div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="error">✗ Analysis failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new analysis
                loadSourceStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div class="error">✗ Error: ${error.message}</div>`;
            }
        }

        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }

        async function loadHistory() {
            try {
                const [fetchResponse, normalizeResponse, analyzeResponse] = await Promise.all([
                    fetch('/api/source-agent/fetches?limit=50'),
                    fetch('/api/source-agent/normalizations?limit=50'),
                    fetch('/api/source-agent/analyses?limit=50')
                ]);

                const fetchData = await fetchResponse.json();
                const normalizeData = await normalizeResponse.json();
                const analyzeData = await analyzeResponse.json();

                if (fetchData.success) {
                    sourceData.fetches = fetchData.data;
                    renderRecentFetches();
                }

                if (normalizeData.success) {
                    sourceData.normalizations = normalizeData.data;
                    renderRecentNormalizations();
                }

                if (analyzeData.success) {
                    sourceData.analyses = analyzeData.data;
                    renderRecentAnalyses();
                }

            } catch (error) {
                alert('Failed to load full history: ' + error.message);
            }
        }

        function refreshStatus() {
            loadSourceStatus();
        }

        // Load initial data
        loadSourceStatus();
    </script>
</body>
</html>
"""
            return create_html_response(html, "Source Agent Dashboard")
        except Exception as e:
            return handle_frontend_error("render source agent dashboard", e, **build_frontend_context("render_source_agent_dashboard"))
