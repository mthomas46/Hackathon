"""Services Overview UI handlers for Frontend service.

Handles comprehensive services overview dashboard.
"""
from typing import Dict, Any
from fastapi.responses import HTMLResponse

from ..shared_utils import (
    create_html_response,
    handle_frontend_error,
    build_frontend_context
)


class ServicesOverviewUIHandlers:
    """Handles services overview UI rendering."""

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

            html += \`
                <div class="health-item">
                    <div class="health-label">Overall Status</div>
                    <div class="health-value">
                        <span class="status-indicator {{isHealthy ? 'healthy' : 'unhealthy'}"></span>
                        {{isHealthy ? 'Healthy' : 'Issues Detected'}
                    </div>
                </div>
                <div class="health-item">
                    <div class="health-label">Services Monitored</div>
                    <div class="health-value">{{serviceCount}</div>
                </div>
                <div class="health-item">
                    <div class="health-label">Last Checked</div>
                    <div class="health-value">{{new Date(systemHealth.last_checked).toLocaleString()}</div>
                </div>
            \`;

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
                    loadServiceStatus('code-analyzer', '/api/code-analyzer/status'),
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

                html += \`<div class="{{cardClass}">\`;

                // Service header
                html += \`<div class="service-name">{{formatServiceName(service.name)}</div>\`;
                html += \`<div class="service-description">{{status.description || 'Service description not available'}</div>\`;

                // Status indicator
                const statusClass = isHealthy ? 'healthy' : 'unhealthy';
                const statusText = isHealthy ? 'Operational' : 'Issues';
                html += \`<div class="service-status">\`;
                html += \`<span class="status-indicator {{statusClass}"></span>\`;
                html += \`{{statusText}\`;
                html += \`<span class="badge {{hasViz ? 'has-viz' : 'no-viz'}">{{hasViz ? 'Has Viz' : 'No Viz'}</span>\`;
                html += \`</div>\`;

                // Metrics (if available)
                if (status.analysis_stats || status.workflow_stats || status.invocation_stats) {
                    html += '<div class="service-metrics">';

                    if (status.analysis_stats) {
                        const stats = status.analysis_stats;
                        html += \`
                            <div class="metric-item">
                                <span class="metric-value">{{stats.total_analyses || 0}</span>
                                <span class="metric-label">Analyses</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-value">{{stats.total_findings || 0}</span>
                                <span class="metric-label">Findings</span>
                            </div>
                        \`;
                    }

                    if (status.workflow_stats) {
                        const stats = status.workflow_stats;
                        html += \`
                            <div class="metric-item">
                                <span class="metric-value">{{stats.total_workflows || 0}</span>
                                <span class="metric-label">Workflows</span>
                            </div>
                        \`;
                    }

                    if (status.invocation_stats) {
                        const stats = status.invocation_stats;
                        html += \`
                            <div class="metric-item">
                                <span class="metric-value">{{stats.total_invocations || 0}</span>
                                <span class="metric-label">Invocations</span>
                            </div>
                        \`;
                    }

                    html += '</div>';
                }

                // Actions
                html += '<div class="service-actions">';

                if (hasViz) {
                    const dashboardUrl = getServiceDashboardUrl(service.name);
                    if (dashboardUrl) {
                        html += \`<a href="{{dashboardUrl}" class="btn">Dashboard</a>\`;
                    }
                    html += \`<button class="btn secondary small" onclick="refreshService('{{service.name}')">Refresh</button>\`;
                } else {
                    html += \`<button class="btn secondary small" onclick="checkService('{{service.name}')">Check Status</button>\`;
                }

                html += '</div>';

                // Last updated
                html += \`<div class="last-updated">Last updated: {{new Date(service.lastUpdated).toLocaleString()}</div>\`;

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
                'log-collector': '/logs/dashboard',
                'code-analyzer': '/code-analyzer/dashboard'
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
            alert(\`Service {{serviceName} health check not implemented yet.\`);
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
