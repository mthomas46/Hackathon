"""Discovery Agent UI handlers for Frontend service.

Handles discovery agent service visualization, including endpoint
registration monitoring, OpenAPI parsing, and service discovery operations.
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
from ..discovery_agent_monitor import discovery_agent_monitor


class DiscoveryAgentUIHandlers:
    """Handles discovery agent UI rendering."""

    @staticmethod
    def handle_discovery_agent_dashboard() -> HTMLResponse:
        """Render discovery agent service monitoring dashboard."""
        try:
            clients = get_frontend_clients()

            # Get discovery agent status and cached data
            status_data = discovery_agent_monitor.get_discovery_status()
            discovery_history = discovery_agent_monitor.get_discovery_history(limit=20)

            # Build context for template
            context = {
                "health": status_data.get("health", {}),
                "discovery_stats": status_data.get("discovery_stats", {}),
                "recent_discoveries": discovery_history,
                "last_updated": status_data.get("last_updated", "Never")
            }

            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Discovery Agent Dashboard - LLM Documentation Ecosystem</title>
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
        .discovery-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .discovery-item.completed {
            border-left-color: #28a745;
            background: #f8fff8;
        }
        .discovery-item.failed {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .discovery-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .discovery-service {
            font-weight: 500;
            margin: 10px 0;
            color: #495057;
        }
        .discovery-endpoints {
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
        .badge {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 2px 5px 2px 0;
        }
        .badge.completed {
            background: #28a745;
        }
        .badge.failed {
            background: #dc3545;
        }
        .badge.dry-run {
            background: #ffc107;
            color: black;
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
        .form-group select {
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
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
        .services-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0;
        }
        .service-tag {
            background: #e9ecef;
            color: #495057;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Discovery Agent Dashboard</h1>
            <p>Monitor OpenAPI endpoint discovery and service registration operations</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="refreshStatus()">Refresh Status</button>
            <button class="btn secondary" onclick="loadHistory()">Load Full History</button>
        </div>

        <div id="status-container">
            <!-- Status will be loaded here -->
        </div>

        <div class="test-section">
            <h3>Discover Service Endpoints</h3>
            <form class="test-form" onsubmit="discoverService(event)">
                <div class="form-row">
                    <div class="form-group">
                        <label for="service-url">Service URL:</label>
                        <input type="url" id="service-url" placeholder="http://service:port" required>
                    </div>
                    <div class="form-group">
                        <label for="service-name">Service Name (optional):</label>
                        <input type="text" id="service-name" placeholder="e.g., github-agent">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="spec-url">OpenAPI Spec URL (optional):</label>
                        <input type="url" id="spec-url" placeholder="http://service:port/openapi.json">
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" id="dry-run">
                        <label for="dry-run">Dry Run (test without registration)</label>
                    </div>
                </div>
                <button type="submit" class="btn">Discover Endpoints</button>
            </form>
            <div id="discovery-result" style="margin-top: 20px;"></div>
        </div>

        <div id="discoveries-container">
            <!-- Recent discoveries will be loaded here -->
        </div>
    </div>

    <script>
        let discoveryData = {
            status: {},
            discoveries: [],
            discovery_stats: {}
        };

        async function loadDiscoveryStatus() {
            try {
                const response = await fetch('/api/discovery-agent/status');
                const data = await response.json();

                if (data.success) {
                    discoveryData = data.data;
                    renderDiscoveryStatus();
                    renderRecentDiscoveries();
                } else {
                    document.getElementById('status-container').innerHTML =
                        '<div class="error">Failed to load discovery status: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Failed to load discovery status: ' + error.message + '</div>';
            }
        }

        function renderDiscoveryStatus() {
            const health = discoveryData.status || {};
            const stats = discoveryData.discovery_stats || {};

            let html = '<div class="status-grid">';

            // Service health
            const isHealthy = health.status === 'healthy';
            html += `
                <div class="status-card ${isHealthy ? 'healthy' : 'unhealthy'}">
                    <div class="status-label">Service Status</div>
                    <div class="status-value">${health.status || 'Unknown'}</div>
                    <div>Discovery Agent</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Total Discoveries</div>
                    <div class="status-value">${stats.total_discoveries || 0}</div>
                    <div>All time</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Success Rate</div>
                    <div class="status-value">${stats.success_rate || 0}%</div>
                    <div>Discovery success</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Services Found</div>
                    <div class="status-value">${stats.unique_services || 0}</div>
                    <div>Unique services</div>
                </div>
            `;

            html += '</div>';

            // Detailed metrics
            if (stats.total_discoveries > 0) {
                html += '<h4>Discovery Statistics</h4><div class="metric-grid">';

                html += `
                    <div class="metric-item">
                        <div class="metric-label">Successful</div>
                        <div class="metric-value">${stats.successful_discoveries || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Failed</div>
                        <div class="metric-value">${stats.failed_discoveries || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Total Endpoints</div>
                        <div class="metric-value">${stats.total_endpoints_discovered || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Dry Runs</div>
                        <div class="metric-value">${stats.dry_run_count || 0}</div>
                    </div>
                `;

                html += '</div>';

                // Services discovered
                if (stats.services_discovered && stats.services_discovered.length > 0) {
                    html += '<h4>Services Discovered</h4><div class="services-list">';
                    stats.services_discovered.forEach(service => {
                        html += `<span class="service-tag">${service}</span>`;
                    });
                    html += '</div>';
                }
            }

            document.getElementById('status-container').innerHTML = html;
        }

        function renderRecentDiscoveries() {
            const discoveries = discoveryData.discoveries || [];

            if (discoveries.length === 0) {
                document.getElementById('discoveries-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No discoveries recorded yet</div>';
                return;
            }

            let html = '<h4>Recent Discoveries</h4>';

            discoveries.forEach(discovery => {
                const timestamp = new Date(discovery.timestamp).toLocaleString();
                const status = discovery.status || 'unknown';
                const endpoints = discovery.endpoints_discovered || 0;
                const hasResponse = discovery.response && typeof discovery.response === 'object';

                html += `
                    <div class="discovery-item ${status}">
                        <div class="discovery-meta">
                            <span><strong>ID:</strong> ${discovery.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span class="badge ${status}">${status.toUpperCase()}</span>
                            ${discovery.dry_run ? '<span class="badge dry-run">DRY RUN</span>' : ''}
                            <span><strong>Endpoints:</strong> ${endpoints}</span>
                        </div>
                        <div class="discovery-service">
                            <strong>${discovery.service_name}</strong> - ${discovery.service_url}
                        </div>
                        ${discovery.spec_url ? `<div><strong>Spec:</strong> ${discovery.spec_url}</div>` : ''}
                        ${hasResponse ? `
                            <div class="discovery-endpoints">${JSON.stringify(discovery.response, null, 2)}</div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('discoveries-container').innerHTML = html;
        }

        async function discoverService(event) {
            event.preventDefault();

            const serviceUrl = document.getElementById('service-url').value;
            const serviceName = document.getElementById('service-name').value;
            const specUrl = document.getElementById('spec-url').value;
            const dryRun = document.getElementById('dry-run').checked;

            if (!serviceUrl.trim()) {
                alert('Please enter a service URL');
                return;
            }

            const resultDiv = document.getElementById('discovery-result');
            resultDiv.innerHTML = '<div style="color: #666;">Discovering endpoints...</div>';

            try {
                const payload = {
                    service_url: serviceUrl,
                    dry_run: dryRun
                };

                if (serviceName.trim()) {
                    payload.service_name = serviceName.trim();
                }
                if (specUrl.trim()) {
                    payload.spec_url = specUrl.trim();
                }

                const response = await fetch('/api/discovery-agent/discover', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    resultDiv.innerHTML = `
                        <div style="color: #28a745; margin-bottom: 10px;">✓ Discovery completed successfully!</div>
                        <div><strong>Discovery ID:</strong> ${data.discovery_id}</div>
                        <div><strong>Endpoints Found:</strong> ${data.endpoints_discovered}</div>
                        <div class="discovery-endpoints">${JSON.stringify(data.response, null, 2)}</div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div style="color: #dc3545;">✗ Discovery failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new discovery
                loadDiscoveryStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div style="color: #dc3545;">✗ Error: ${error.message}</div>`;
            }
        }

        async function loadHistory() {
            try {
                const response = await fetch('/api/discovery-agent/history?limit=50');
                const data = await response.json();

                if (data.success) {
                    discoveryData.discoveries = data.data;
                    renderRecentDiscoveries();
                } else {
                    alert('Failed to load full history: ' + data.message);
                }
            } catch (error) {
                alert('Failed to load full history: ' + error.message);
            }
        }

        function refreshStatus() {
            loadDiscoveryStatus();
        }

        // Load initial data
        loadDiscoveryStatus();
    </script>
</body>
</html>
"""
            return create_html_response(html, "Discovery Agent Dashboard")
        except Exception as e:
            return handle_frontend_error("render discovery agent dashboard", e, **build_frontend_context("render_discovery_agent_dashboard"))
