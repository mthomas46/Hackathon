"""GitHub MCP UI handlers for Frontend service.

Handles github-mcp service visualization, including tool invocation
monitoring, GitHub operations, and MCP tool testing.
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
from ..github_mcp_monitor import github_mcp_monitor


class GithubMcpUIHandlers:
    """Handles github-mcp UI rendering."""

    @staticmethod
    def handle_github_mcp_dashboard() -> HTMLResponse:
        """Render github-mcp service monitoring dashboard."""
        try:
            clients = get_frontend_clients()

            # Get github-mcp status and cached data
            status_data = github_mcp_monitor.get_mcp_status()
            invocation_history = github_mcp_monitor.get_invocation_history(limit=20)

            # Build context for template
            context = {
                "health": status_data.get("health", {}),
                "info": status_data.get("info", {}),
                "tool_stats": status_data.get("tool_stats", {}),
                "recent_invocations": invocation_history,
                "last_updated": status_data.get("last_updated", "Never")
            }

            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub MCP Dashboard - LLM Documentation Ecosystem</title>
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
        .status-card.mock {
            border-left-color: #ffc107;
            background: #fffbf0;
        }
        .status-card.real {
            border-left-color: #007bff;
            background: #f0f8ff;
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
        .invocation-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .invocation-item.success {
            border-left-color: #28a745;
            background: #f8fff8;
        }
        .invocation-item.failed {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .invocation-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .invocation-tool {
            font-weight: 500;
            margin: 10px 0;
            color: #495057;
        }
        .invocation-args {
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
        .invocation-result {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
            max-height: 150px;
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
        .badge.success {
            background: #28a745;
        }
        .badge.failed {
            background: #dc3545;
        }
        .badge.mock {
            background: #ffc107;
            color: black;
        }
        .badge.real {
            background: #007bff;
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
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 8px;
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
        .tools-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .tool-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        .tool-item {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
        }
        .tool-name {
            font-weight: bold;
            color: #495057;
            margin-bottom: 8px;
        }
        .tool-description {
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
        }
        .tool-meta {
            display: flex;
            gap: 10px;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>GitHub MCP Dashboard</h1>
            <p>Monitor GitHub MCP tool invocations and GitHub data operations</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="refreshStatus()">Refresh Status</button>
            <button class="btn secondary" onclick="loadHistory()">Load Full History</button>
            <button class="btn success" onclick="loadTools()">Load Available Tools</button>
        </div>

        <div id="status-container">
            <!-- Status will be loaded here -->
        </div>

        <div id="tools-container" class="tools-section" style="display: none;">
            <h3>Available GitHub MCP Tools</h3>
            <div id="tools-grid" class="tool-grid">
                <!-- Tools will be loaded here -->
            </div>
        </div>

        <div class="test-section">
            <h3>Test Tool Invocation</h3>
            <form class="test-form" onsubmit="invokeTool(event)">
                <div class="form-row">
                    <div class="form-group">
                        <label for="tool-name">Tool Name:</label>
                        <input type="text" id="tool-name" placeholder="e.g., github.search_repos" required>
                    </div>
                    <div class="form-group">
                        <label for="tool-args">Arguments (JSON):</label>
                        <textarea id="tool-args" placeholder='{"q": "docs", "limit": 2}'>{"q": "docs", "limit": 2}</textarea>
                    </div>
                </div>
                <div class="form-row">
                    <div class="checkbox-group">
                        <input type="checkbox" id="use-mock" checked>
                        <label for="use-mock">Use Mock Mode</label>
                    </div>
                    <div class="form-group">
                        <label for="correlation-id">Correlation ID (optional):</label>
                        <input type="text" id="correlation-id" placeholder="Optional tracking ID">
                    </div>
                </div>
                <button type="submit" class="btn">Invoke Tool</button>
            </form>
            <div id="invocation-result" style="margin-top: 20px;"></div>
        </div>

        <div id="invocations-container">
            <!-- Recent invocations will be loaded here -->
        </div>
    </div>

    <script>
        let mcpData = {
            status: {},
            tools: [],
            invocations: [],
            tool_stats: {}
        };

        async function loadMcpStatus() {
            try {
                const response = await fetch('/api/github-mcp/status');
                const data = await response.json();

                if (data.success) {
                    mcpData = data.data;
                    renderMcpStatus();
                    renderRecentInvocations();
                } else {
                    document.getElementById('status-container').innerHTML =
                        '<div class="error">Failed to load MCP status: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Failed to load MCP status: ' + error.message + '</div>';
            }
        }

        function renderMcpStatus() {
            const health = mcpData.status || {};
            const info = mcpData.info || {};
            const stats = mcpData.tool_stats || {};

            let html = '<div class="status-grid">';

            // Service health
            const isHealthy = health.status === 'healthy';
            html += `
                <div class="status-card ${isHealthy ? 'healthy' : 'unhealthy'}">
                    <div class="status-label">Service Status</div>
                    <div class="status-value">${health.status || 'Unknown'}</div>
                    <div>GitHub MCP Service</div>
                </div>
                <div class="status-card ${info.mock_mode_default ? 'mock' : 'real'}">
                    <div class="status-label">Default Mode</div>
                    <div class="status-value">${info.mock_mode_default ? 'Mock' : 'Real'}</div>
                    <div>Execution mode</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Read Only</div>
                    <div class="status-value">${info.read_only ? 'Yes' : 'No'}</div>
                    <div>Write operations blocked</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Toolsets</div>
                    <div class="status-value">${info.toolsets ? info.toolsets.length : 0}</div>
                    <div>Active toolsets</div>
                </div>
            `;

            html += '</div>';

            // Configuration details
            if (info.toolsets && info.toolsets.length > 0) {
                html += '<h4>Configuration</h4><div class="metric-grid">';

                html += `
                    <div class="metric-item">
                        <div class="metric-label">Toolsets</div>
                        <div class="metric-value">${info.toolsets.join(', ')}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Dynamic Toolsets</div>
                        <div class="metric-value">${info.dynamic_toolsets ? 'Enabled' : 'Disabled'}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">GitHub Host</div>
                        <div class="metric-value">${info.github_host || 'github.com'}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Token Present</div>
                        <div class="metric-value">${info.token_present ? 'Yes' : 'No'}</div>
                    </div>
                `;

                html += '</div>';
            }

            // Tool statistics
            if (stats.total_invocations > 0) {
                html += '<h4>Tool Usage Statistics</h4><div class="metric-grid">';

                html += `
                    <div class="metric-item">
                        <div class="metric-label">Total Invocations</div>
                        <div class="metric-value">${stats.total_invocations || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Success Rate</div>
                        <div class="metric-value">${stats.success_rate || 0}%</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Tools Used</div>
                        <div class="metric-value">${stats.unique_tools_used || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Mock Mode Count</div>
                        <div class="metric-value">${stats.mock_mode_count || 0}</div>
                    </div>
                `;

                html += '</div>';
            }

            document.getElementById('status-container').innerHTML = html;
        }

        function renderRecentInvocations() {
            const invocations = mcpData.invocations || [];

            if (invocations.length === 0) {
                document.getElementById('invocations-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No tool invocations recorded yet</div>';
                return;
            }

            let html = '<h4>Recent Tool Invocations</h4>';

            invocations.forEach(inv => {
                const timestamp = new Date(inv.timestamp).toLocaleString();
                const success = inv.success;
                const mockMode = inv.mock_mode;

                html += `
                    <div class="invocation-item ${success ? 'success' : 'failed'}">
                        <div class="invocation-meta">
                            <span><strong>ID:</strong> ${inv.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span class="badge ${success ? 'success' : 'failed'}">${success ? 'SUCCESS' : 'FAILED'}</span>
                            <span class="badge ${mockMode ? 'mock' : 'real'}">${mockMode ? 'MOCK' : 'REAL'}</span>
                        </div>
                        <div class="invocation-tool">
                            <strong>Tool:</strong> ${inv.tool}
                        </div>
                        ${inv.arguments ? `
                            <div class="invocation-args">${JSON.stringify(inv.arguments, null, 2)}</div>
                        ` : ''}
                        ${inv.result ? `
                            <div class="invocation-result">${JSON.stringify(inv.result, null, 2)}</div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('invocations-container').innerHTML = html;
        }

        async function loadTools() {
            try {
                const response = await fetch('/api/github-mcp/tools');
                const data = await response.json();

                if (data.success) {
                    mcpData.tools = data.data;
                    renderAvailableTools();
                    document.getElementById('tools-container').style.display = 'block';
                } else {
                    alert('Failed to load tools: ' + data.message);
                }
            } catch (error) {
                alert('Failed to load tools: ' + error.message);
            }
        }

        function renderAvailableTools() {
            const tools = mcpData.tools || [];

            if (tools.length === 0) {
                document.getElementById('tools-grid').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px; grid-column: 1 / -1;">No tools available</div>';
                return;
            }

            let html = '';

            tools.forEach(tool => {
                html += `
                    <div class="tool-item">
                        <div class="tool-name">${tool.name}</div>
                        <div class="tool-description">${tool.description || 'No description available'}</div>
                        <div class="tool-meta">
                            <span><strong>Toolset:</strong> ${tool.toolset || 'Unknown'}</span>
                            <span><strong>Type:</strong> ${tool.type || 'Unknown'}</span>
                        </div>
                    </div>
                `;
            });

            document.getElementById('tools-grid').innerHTML = html;
        }

        async function invokeTool(event) {
            event.preventDefault();

            const toolName = document.getElementById('tool-name').value;
            const argsText = document.getElementById('tool-args').value;
            const useMock = document.getElementById('use-mock').checked;
            const correlationId = document.getElementById('correlation-id').value;

            if (!toolName.trim()) {
                alert('Please enter a tool name');
                return;
            }

            let arguments;
            try {
                arguments = argsText.trim() ? JSON.parse(argsText) : {};
            } catch (e) {
                alert('Invalid JSON in arguments: ' + e.message);
                return;
            }

            const resultDiv = document.getElementById('invocation-result');
            resultDiv.innerHTML = '<div style="color: #666;">Invoking tool...</div>';

            try {
                const payload = {
                    tool_name: toolName,
                    arguments: arguments,
                    mock: useMock
                };

                if (correlationId.trim()) {
                    payload.correlation_id = correlationId.trim();
                }

                const response = await fetch('/api/github-mcp/invoke', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    resultDiv.innerHTML = `
                        <div style="color: #28a745; margin-bottom: 10px;">✓ Tool invocation successful!</div>
                        <div><strong>Tool:</strong> ${data.tool}</div>
                        <div><strong>Invocation ID:</strong> ${data.invocation_id}</div>
                        <div class="invocation-result">${JSON.stringify(data.result, null, 2)}</div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div style="color: #dc3545;">✗ Tool invocation failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new invocation
                loadMcpStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div style="color: #dc3545;">✗ Error: ${error.message}</div>`;
            }
        }

        async function loadHistory() {
            try {
                const response = await fetch('/api/github-mcp/history?limit=50');
                const data = await response.json();

                if (data.success) {
                    mcpData.invocations = data.data;
                    renderRecentInvocations();
                } else {
                    alert('Failed to load full history: ' + data.message);
                }
            } catch (error) {
                alert('Failed to load full history: ' + error.message);
            }
        }

        function refreshStatus() {
            loadMcpStatus();
        }

        // Load initial data
        loadMcpStatus();
    </script>
</body>
</html>
"""
            return create_html_response(html, "GitHub MCP Dashboard")
        except Exception as e:
            return handle_frontend_error("render github-mcp dashboard", e, **build_frontend_context("render_github_mcp_dashboard"))
