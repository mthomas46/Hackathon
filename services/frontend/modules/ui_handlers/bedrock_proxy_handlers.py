"""Bedrock Proxy UI handlers for Frontend service.

Handles bedrock proxy service visualization, including AI invocation
monitoring, template usage tracking, and response analytics.
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
from ..bedrock_proxy_monitor import bedrock_proxy_monitor


class BedrockProxyUIHandlers:
    """Handles bedrock proxy UI rendering."""

    @staticmethod
    def handle_bedrock_proxy_dashboard() -> HTMLResponse:
        """Render bedrock proxy service monitoring dashboard."""
        try:
            clients = get_frontend_clients()

            # Get bedrock proxy status and cached data
            status_data = bedrock_proxy_monitor.get_proxy_status()
            invocation_history = bedrock_proxy_monitor.get_invocation_history(limit=20)

            # Build context for template
            context = {
                "status": status_data.get("health", {}),
                "invocation_stats": status_data.get("invocation_stats", {}),
                "recent_invocations": invocation_history,
                "last_updated": status_data.get("last_updated", "Never")
            }

            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bedrock Proxy Dashboard - LLM Documentation Ecosystem</title>
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
        .invocation-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
        }
        .invocation-prompt {
            font-weight: 500;
            margin: 10px 0;
            color: #495057;
        }
        .invocation-response {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
            white-space: pre-wrap;
            max-height: 150px;
            overflow-y: auto;
        }
        .template-badge {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 2px 5px 2px 0;
        }
        .format-badge {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 2px 5px 2px 0;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Bedrock Proxy Dashboard</h1>
            <p>Monitor AI invocations, template usage, and proxy service health</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="refreshStatus()">Refresh Status</button>
            <button class="btn secondary" onclick="loadHistory()">Load Full History</button>
        </div>

        <div id="status-container">
            <!-- Status will be loaded here -->
        </div>

        <div class="test-section">
            <h3>Test AI Invocation</h3>
            <form class="test-form" onsubmit="testInvocation(event)">
                <div class="form-group">
                    <label for="test-prompt">Prompt:</label>
                    <textarea id="test-prompt" placeholder="Enter your prompt here...">Summarize the key features of a documentation system</textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="test-template">Template:</label>
                        <select id="test-template">
                            <option value="">None</option>
                            <option value="summary">Summary</option>
                            <option value="risks">Risks</option>
                            <option value="decisions">Decisions</option>
                            <option value="pr_confidence">PR Confidence</option>
                            <option value="life_of_ticket">Life of Ticket</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="test-format">Format:</label>
                        <select id="test-format">
                            <option value="md">Markdown</option>
                            <option value="txt">Text</option>
                            <option value="json">JSON</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="test-title">Title (optional):</label>
                        <input type="text" id="test-title" placeholder="Custom title">
                    </div>
                </div>
                <button type="submit" class="btn">Test Invocation</button>
            </form>
            <div id="test-result" style="margin-top: 20px;"></div>
        </div>

        <div id="invocations-container">
            <!-- Recent invocations will be loaded here -->
        </div>
    </div>

    <script>
        let proxyData = {
            status: {},
            invocations: [],
            invocation_stats: {}
        };

        async function loadProxyStatus() {
            try {
                const response = await fetch('/api/bedrock-proxy/status');
                const data = await response.json();

                if (data.success) {
                    proxyData = data.data;
                    renderProxyStatus();
                    renderRecentInvocations();
                } else {
                    document.getElementById('status-container').innerHTML =
                        '<div class="error">Failed to load proxy status: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Failed to load proxy status: ' + error.message + '</div>';
            }
        }

        function renderProxyStatus() {
            const health = proxyData.status || {};
            const stats = proxyData.invocation_stats || {};

            let html = '<div class="status-grid">';

            // Service health
            const isHealthy = health.status === 'healthy';
            html += `
                <div class="status-card ${isHealthy ? 'healthy' : 'unhealthy'}">
                    <div class="status-label">Service Status</div>
                    <div class="status-value">${health.status || 'Unknown'}</div>
                    <div>${health.description || 'Bedrock proxy service'}</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Total Invocations</div>
                    <div class="status-value">${stats.total_invocations || 0}</div>
                    <div>All time</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Models Used</div>
                    <div class="status-value">${stats.unique_models || 0}</div>
                    <div>Unique models</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Templates Used</div>
                    <div class="status-value">${stats.unique_templates || 0}</div>
                    <div>Unique templates</div>
                </div>
            `;

            html += '</div>';

            // Model and template usage
            if (stats.models_used && stats.models_used.length > 0) {
                html += '<h4>Model Usage</h4><div class="metric-grid">';
                stats.models_used.forEach(model => {
                    html += `
                        <div class="metric-item">
                            <div class="metric-label">${model}</div>
                            <div class="metric-value">✓</div>
                        </div>
                    `;
                });
                html += '</div>';
            }

            if (stats.templates_used && stats.templates_used.length > 0) {
                html += '<h4>Template Usage</h4><div class="metric-grid">';
                stats.templates_used.forEach(template => {
                    html += `
                        <div class="metric-item">
                            <div class="metric-label">${template}</div>
                            <div class="metric-value">✓</div>
                        </div>
                    `;
                });
                html += '</div>';
            }

            document.getElementById('status-container').innerHTML = html;
        }

        function renderRecentInvocations() {
            const invocations = proxyData.invocations || [];

            if (invocations.length === 0) {
                document.getElementById('invocations-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No invocations recorded yet</div>';
                return;
            }

            let html = '<h4>Recent Invocations</h4>';

            invocations.forEach(inv => {
                const timestamp = new Date(inv.timestamp).toLocaleString();
                const hasResponse = inv.response && typeof inv.response === 'object';

                html += `
                    <div class="invocation-item">
                        <div class="invocation-meta">
                            <span><strong>ID:</strong> ${inv.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            ${inv.template ? `<span class="template-badge">${inv.template}</span>` : ''}
                            ${inv.format ? `<span class="format-badge">${inv.format}</span>` : ''}
                            ${inv.model ? `<span><strong>Model:</strong> ${inv.model}</span>` : ''}
                        </div>
                        <div class="invocation-prompt">${inv.prompt}</div>
                        ${hasResponse ? `
                            <div class="invocation-response">${JSON.stringify(inv.response, null, 2)}</div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('invocations-container').innerHTML = html;
        }

        async function testInvocation(event) {
            event.preventDefault();

            const prompt = document.getElementById('test-prompt').value;
            const template = document.getElementById('test-template').value;
            const format = document.getElementById('test-format').value;
            const title = document.getElementById('test-title').value;

            if (!prompt.trim()) {
                alert('Please enter a prompt');
                return;
            }

            const resultDiv = document.getElementById('test-result');
            resultDiv.innerHTML = '<div style="color: #666;">Testing invocation...</div>';

            try {
                const payload = {
                    prompt: prompt,
                    template: template || undefined,
                    format: format || undefined,
                    title: title || undefined
                };

                // Remove undefined values
                Object.keys(payload).forEach(key => payload[key] === undefined && delete payload[key]);

                const response = await fetch('/api/bedrock-proxy/invoke', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    resultDiv.innerHTML = `
                        <div style="color: #28a745; margin-bottom: 10px;">✓ Invocation successful!</div>
                        <div class="invocation-response">${JSON.stringify(data.response, null, 2)}</div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div style="color: #dc3545;">✗ Invocation failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new invocation
                loadProxyStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div style="color: #dc3545;">✗ Error: ${error.message}</div>`;
            }
        }

        async function loadHistory() {
            try {
                const response = await fetch('/api/bedrock-proxy/history?limit=50');
                const data = await response.json();

                if (data.success) {
                    proxyData.invocations = data.data;
                    renderRecentInvocations();
                } else {
                    alert('Failed to load full history: ' + data.message);
                }
            } catch (error) {
                alert('Failed to load full history: ' + error.message);
            }
        }

        function refreshStatus() {
            loadProxyStatus();
        }

        // Load initial data
        loadProxyStatus();
    </script>
</body>
</html>
"""
            return create_html_response(html, "Bedrock Proxy Dashboard")
        except Exception as e:
            return handle_frontend_error("render bedrock proxy dashboard", e, **build_frontend_context("render_bedrock_proxy_dashboard"))
