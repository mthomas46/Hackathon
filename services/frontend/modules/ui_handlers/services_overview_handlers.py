"""Services Overview UI handlers for Frontend service.

Handles comprehensive system-wide monitoring dashboard
showing health and status of all services in the ecosystem.
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
from ..services_overview_monitor import services_overview_monitor


class ServicesOverviewUIHandlers:
    """Handles services overview UI rendering."""

    @staticmethod
    def handle_services_overview() -> HTMLResponse:
        """Render comprehensive services overview dashboard."""
        try:
            clients = get_frontend_clients()

            # Get comprehensive services overview
            overview_data = services_overview_monitor.get_services_overview()

            # Build context for template
            context = {
                "system_metrics": overview_data.get("system_metrics", {}),
                "service_statuses": overview_data.get("service_statuses", {}),
                "categorized_services": overview_data.get("categorized_services", {}),
                "last_updated": overview_data.get("last_updated", "Never")
            }

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
        .system-status {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }
        .system-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            font-size: 0.9em;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .health-indicator {
            display: inline-block;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .health-indicator.healthy {
            background: #28a745;
            box-shadow: 0 0 10px rgba(40, 167, 69, 0.5);
        }
        .health-indicator.degraded {
            background: #ffc107;
            box-shadow: 0 0 10px rgba(255, 193, 7, 0.5);
        }
        .health-indicator.critical {
            background: #dc3545;
            box-shadow: 0 0 10px rgba(220, 53, 69, 0.5);
        }
        .health-indicator.unknown {
            background: #6c757d;
        }
        .categories-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin: 30px 0;
        }
        .category-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 25px;
            border-left: 4px solid #17a2b8;
        }
        .category-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .category-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #495057;
            margin: 0;
        }
        .category-health {
            font-size: 0.9em;
            font-weight: 500;
        }
        .services-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
        }
        .service-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            border: 2px solid #e9ecef;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .service-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .service-card.healthy {
            border-left: 4px solid #28a745;
        }
        .service-card.unhealthy {
            border-left: 4px solid #dc3545;
        }
        .service-card.unknown {
            border-left: 4px solid #6c757d;
        }
        .service-name {
            font-weight: 600;
            color: #495057;
            margin-bottom: 5px;
            font-size: 0.9em;
        }
        .service-status {
            display: flex;
            align-items: center;
            font-size: 0.8em;
            color: #6c757d;
        }
        .service-version {
            font-size: 0.7em;
            color: #adb5bd;
            margin-top: 5px;
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
            justify-content: center;
        }
        .btn {
            background: #17a2b8;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .btn:hover {
            background: #138496;
            transform: translateY(-1px);
        }
        .btn.secondary {
            background: #6c757d;
        }
        .btn.secondary:hover {
            background: #545b62;
        }
        .service-details-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: white;
            border-radius: 12px;
            padding: 30px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
        }
        .modal-close {
            position: absolute;
            top: 15px;
            right: 20px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #6c757d;
        }
        .modal-title {
            margin-top: 0;
            color: #495057;
        }
        .health-details {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            font-family: monospace;
            font-size: 12px;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
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
        .status-card.degraded {
            border-left-color: #ffc107;
            background: #fffbf0;
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
        .progress-bar {
            width: 100%;
            height: 12px;
            background: #e9ecef;
            border-radius: 6px;
            margin: 10px 0;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%);
            border-radius: 6px;
            transition: width 0.5s ease;
        }
        .last-updated {
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 30px;
        }
        .legend {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            font-size: 0.9em;
            color: #495057;
        }
        .category-labels {
            text-align: center;
            margin: 15px 0;
            color: #6c757d;
            font-size: 0.9em;
        }
        .category-labels strong {
            color: #495057;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LLM Documentation Ecosystem - Services Overview</h1>
            <p>Comprehensive system health and service monitoring dashboard</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="refreshOverview()">Refresh Overview</button>
            <button class="btn secondary" onclick="showAllDetails()">View All Details</button>
        </div>

        <div id="system-status">
            <!-- System status will be loaded here -->
        </div>

        <div class="legend">
            <div class="legend-item">
                <span class="health-indicator healthy"></span>
                Healthy
            </div>
            <div class="legend-item">
                <span class="health-indicator degraded"></span>
                Degraded
            </div>
            <div class="legend-item">
                <span class="health-indicator critical"></span>
                Critical
            </div>
            <div class="legend-item">
                <span class="health-indicator unknown"></span>
                Unknown
            </div>
        </div>

        <div id="categories-container">
            <!-- Service categories will be loaded here -->
        </div>

        <div class="last-updated" id="last-updated">
            <!-- Last updated timestamp -->
        </div>
    </div>

    <!-- Service Details Modal -->
    <div id="service-modal" class="service-details-modal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal()">&times;</button>
            <h2 id="modal-title" class="modal-title">Service Details</h2>
            <div id="modal-content">
                <!-- Service details will be loaded here -->
            </div>
        </div>
    </div>

    <script>
        let overviewData = {
            system_metrics: {},
            service_statuses: {},
            categorized_services: {},
            last_updated: null
        };

        async function loadServicesOverview() {
            try {
                const response = await fetch('/api/services/overview');
                const data = await response.json();

                if (data.success) {
                    overviewData = data.data;
                    renderSystemStatus();
                    renderServiceCategories();
                    updateLastUpdated();
                } else {
                    document.getElementById('system-status').innerHTML =
                        '<div style="text-align: center; color: #dc3545; padding: 40px;">Failed to load services overview: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('system-status').innerHTML =
                    '<div style="text-align: center; color: #dc3545; padding: 40px;">Failed to load services overview: ' + error.message + '</div>';
            }
        }

        function renderSystemStatus() {
            const metrics = overviewData.system_metrics || {};
            const systemHealth = metrics.system_health || 'unknown';
            const uptimePercentage = metrics.uptime_percentage || 0;

            let healthClass = 'unknown';
            if (systemHealth === 'healthy') healthClass = 'healthy';
            else if (systemHealth === 'degraded') healthClass = 'degraded';
            else if (systemHealth === 'critical') healthClass = 'critical';

            const html = `
                <div class="system-status">
                    <h2>
                        <span class="health-indicator ${healthClass}"></span>
                        System Health: ${systemHealth.charAt(0).toUpperCase() + systemHealth.slice(1)}
                    </h2>
                    <div class="system-metrics">
                        <div class="metric-card">
                            <div class="metric-label">Total Services</div>
                            <div class="metric-value">${metrics.total_services || 0}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Healthy Services</div>
                            <div class="metric-value">${metrics.healthy_services || 0}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Unhealthy Services</div>
                            <div class="metric-value">${metrics.unhealthy_services || 0}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">System Uptime</div>
                            <div class="metric-value">${uptimePercentage}%</div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${uptimePercentage}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.getElementById('system-status').innerHTML = html;
        }

        function renderServiceCategories() {
            const categories = overviewData.categorized_services || {};
            const categoryLabels = {
                "core_infrastructure": "Core Infrastructure",
                "analysis_services": "Analysis Services",
                "ai_ml_services": "AI/ML Services",
                "integration_services": "Integration Services",
                "operational_services": "Operational Services"
            };

            let html = '';

            for (const [categoryKey, categoryData] of Object.entries(categories)) {
                const categoryName = categoryLabels[categoryKey] || categoryKey;
                const services = categoryData.services || [];
                const healthyCount = categoryData.healthy_count || 0;
                const totalCount = categoryData.total_count || 0;
                const healthPercentage = categoryData.health_percentage || 0;

                let categoryHealth = 'unknown';
                if (healthPercentage === 100) categoryHealth = 'healthy';
                else if (healthPercentage >= 50) categoryHealth = 'degraded';
                else categoryHealth = 'critical';

                html += `
                    <div class="category-card">
                        <div class="category-header">
                            <h3 class="category-title">${categoryName}</h3>
                            <div class="category-health">
                                <span class="health-indicator ${categoryHealth}"></span>
                                ${healthyCount}/${totalCount} healthy (${healthPercentage}%)
                            </div>
                        </div>
                        <div class="services-list">
                `;

                services.forEach(service => {
                    const serviceName = service.name || 'Unknown';
                    const status = service.status || 'unknown';
                    const version = service.version || 'unknown';

                    let statusClass = 'unknown';
                    if (status === 'healthy') statusClass = 'healthy';
                    else if (status === 'unhealthy') statusClass = 'unhealthy';

                    html += `
                        <div class="service-card ${statusClass}" onclick="showServiceDetails('${serviceName}')">
                            <div class="service-name">${serviceName.replace('-', ' ').replace('_', ' ')}</div>
                            <div class="service-status">
                                <span class="health-indicator ${statusClass}"></span>
                                ${status.charAt(0).toUpperCase() + status.slice(1)}
                            </div>
                            <div class="service-version">v${version}</div>
                        </div>
                    `;
                });

                html += `
                        </div>
                    </div>
                `;
            }

            document.getElementById('categories-container').innerHTML = html;
        }

        function updateLastUpdated() {
            const lastUpdated = overviewData.last_updated;
            if (lastUpdated) {
                const date = new Date(lastUpdated);
                document.getElementById('last-updated').textContent =
                    `Last updated: ${date.toLocaleString()}`;
            }
        }

        async function showServiceDetails(serviceName) {
            const modal = document.getElementById('service-modal');
            const modalTitle = document.getElementById('modal-title');
            const modalContent = document.getElementById('modal-content');

            modalTitle.textContent = `${serviceName.replace('-', ' ').replace('_', ' ')} - Service Details`;
            modalContent.innerHTML = '<div style="text-align: center; padding: 40px;">Loading service details...</div>';
            modal.style.display = 'flex';

            try {
                const response = await fetch(`/api/services/overview/${serviceName}`);
                const data = await response.json();

                if (data.success) {
                    const healthData = data.health_data || {};
                    const serviceUrl = data.url || 'Unknown';
                    const endpoint = data.endpoint || 'Unknown';

                    let contentHtml = `
                        <div class="status-grid">
                            <div class="status-card ${healthData.status === 'healthy' ? 'healthy' : 'unhealthy'}">
                                <div class="status-label">Service Status</div>
                                <div class="status-value">${healthData.status || 'Unknown'}</div>
                                <div>Current Health</div>
                            </div>
                            <div class="status-card">
                                <div class="status-label">Service Version</div>
                                <div class="status-value">${healthData.version || 'Unknown'}</div>
                                <div>Software Version</div>
                            </div>
                        </div>
                        <div style="margin: 20px 0;">
                            <strong>Service URL:</strong> ${serviceUrl}<br>
                            <strong>Health Endpoint:</strong> ${endpoint}<br>
                            <strong>Last Checked:</strong> ${data.last_checked ? new Date(data.last_checked).toLocaleString() : 'Never'}
                        </div>
                        <h4>Raw Health Response:</h4>
                        <div class="health-details">${JSON.stringify(healthData, null, 2)}</div>
                    `;

                    modalContent.innerHTML = contentHtml;
                } else {
                    modalContent.innerHTML = `
                        <div style="color: #dc3545; text-align: center; padding: 40px;">
                            Failed to load service details: ${data.error || 'Unknown error'}
                        </div>
                    `;
                }
            } catch (error) {
                modalContent.innerHTML = `
                    <div style="color: #dc3545; text-align: center; padding: 40px;">
                        Error loading service details: ${error.message}
                    </div>
                `;
            }
        }

        function closeModal() {
            document.getElementById('service-modal').style.display = 'none';
        }

        function showAllDetails() {
            // Show details for all services
            const services = Object.keys(overviewData.service_statuses || {});
            if (services.length > 0) {
                showServiceDetails(services[0]); // Show first service as example
            }
        }

        function refreshOverview() {
            loadServicesOverview();
        }

        // Close modal when clicking outside
        document.getElementById('service-modal').addEventListener('click', function(event) {
            if (event.target === this) {
                closeModal();
            }
        });

        // Load initial data
        loadServicesOverview();

        // Auto-refresh every 30 seconds
        setInterval(refreshOverview, 30000);
    </script>
</body>
</html>
"""
            return create_html_response(html, "Services Overview Dashboard")
        except Exception as e:
            return handle_frontend_error("render services overview dashboard", e, **build_frontend_context("render_services_overview_dashboard"))