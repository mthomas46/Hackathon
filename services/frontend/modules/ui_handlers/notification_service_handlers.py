"""Notification Service UI handlers for Frontend service.

Handles notification service visualization, including owner resolution,
notification delivery monitoring, and dead letter queue management.
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
from ..notification_service_monitor import notification_service_monitor


class NotificationServiceUIHandlers:
    """Handles notification service UI rendering."""

    @staticmethod
    def handle_notification_service_dashboard() -> HTMLResponse:
        """Render notification service monitoring dashboard."""
        try:
            clients = get_frontend_clients()

            # Get notification service status and cached data
            status_data = notification_service_monitor.get_notification_status()
            notification_history = notification_service_monitor.get_notification_history(limit=20)
            resolution_history = notification_service_monitor.get_owner_resolution_history(limit=20)

            # Build context for template
            context = {
                "health": status_data.get("health", {}),
                "dlq": status_data.get("dlq", {}),
                "notification_stats": status_data.get("notification_stats", {}),
                "recent_notifications": notification_history,
                "recent_resolutions": resolution_history,
                "last_updated": status_data.get("last_updated", "Never")
            }

            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notification Service Dashboard - LLM Documentation Ecosystem</title>
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
        .status-card.warning {
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
        .notification-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .notification-item.success {
            border-left-color: #28a745;
            background: #f8fff8;
        }
        .notification-item.failed {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .notification-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .notification-content {
            margin: 10px 0;
        }
        .notification-title {
            font-weight: 500;
            color: #495057;
            margin-bottom: 5px;
        }
        .notification-message {
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
        .resolution-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #6c757d;
        }
        .resolution-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .resolution-owners {
            margin: 10px 0;
        }
        .resolution-targets {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
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
        .badge.slack {
            background: #4a154b;
        }
        .badge.email {
            background: #dc3545;
        }
        .badge.webhook {
            background: #28a745;
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
        .dlq-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .dlq-item {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #dc3545;
        }
        .dlq-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
        }
        .dlq-error {
            color: #dc3545;
            font-weight: 500;
            margin: 10px 0;
        }
        .dlq-payload {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
            max-height: 150px;
            overflow-y: auto;
        }
        .owners-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0;
        }
        .owner-tag {
            background: #e9ecef;
            color: #495057;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
        }
        .targets-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0;
        }
        .target-tag {
            background: #d4edda;
            color: #155724;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Notification Service Dashboard</h1>
            <p>Monitor owner resolution, notification delivery, and dead letter queue</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="refreshStatus()">Refresh Status</button>
            <button class="btn secondary" onclick="loadDLQ()">Load DLQ</button>
            <button class="btn success" onclick="loadHistory()">Load Full History</button>
        </div>

        <div id="status-container">
            <!-- Status will be loaded here -->
        </div>

        <div id="dlq-container" class="dlq-section" style="display: none;">
            <h3>Dead Letter Queue</h3>
            <div id="dlq-items">
                <!-- DLQ items will be loaded here -->
            </div>
        </div>

        <div class="test-section">
            <h3>Test Owner Resolution</h3>
            <form class="test-form" onsubmit="resolveOwners(event)">
                <div class="form-group">
                    <label for="test-owners">Owner Names (comma-separated):</label>
                    <input type="text" id="test-owners" placeholder="devops, alerts@example.com, frontend-team" value="devops, frontend-team">
                </div>
                <button type="submit" class="btn">Resolve Owners</button>
            </form>
            <div id="resolution-result" style="margin-top: 20px;"></div>
        </div>

        <div class="test-section">
            <h3>Send Test Notification</h3>
            <form class="test-form" onsubmit="sendNotification(event)">
                <div class="form-row">
                    <div class="form-group">
                        <label for="notify-channel">Channel:</label>
                        <select id="notify-channel">
                            <option value="webhook">Webhook</option>
                            <option value="email">Email</option>
                            <option value="slack">Slack</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="notify-target">Target:</label>
                        <input type="text" id="notify-target" placeholder="https://hooks.slack.com/... or email@domain.com">
                    </div>
                </div>
                <div class="form-group">
                    <label for="notify-title">Title:</label>
                    <input type="text" id="notify-title" placeholder="Alert Title" value="Test Notification">
                </div>
                <div class="form-group">
                    <label for="notify-message">Message:</label>
                    <textarea id="notify-message" placeholder="Notification message content...">This is a test notification from the dashboard.</textarea>
                </div>
                <div class="form-group">
                    <label for="notify-labels">Labels (comma-separated, optional):</label>
                    <input type="text" id="notify-labels" placeholder="urgent, test, alert">
                </div>
                <button type="submit" class="btn">Send Notification</button>
            </form>
            <div id="notification-result" style="margin-top: 20px;"></div>
        </div>

        <div id="notifications-container">
            <!-- Recent notifications will be loaded here -->
        </div>

        <div id="resolutions-container">
            <!-- Recent owner resolutions will be loaded here -->
        </div>
    </div>

    <script>
        let notificationData = {
            status: {},
            dlq: [],
            notifications: [],
            resolutions: [],
            notification_stats: {},
            last_updated: null
        };

        async function loadNotificationStatus() {
            try {
                const response = await fetch('/api/notification-service/status');
                const data = await response.json();

                if (data.success) {
                    notificationData = data.data;
                    renderNotificationStatus();
                    renderRecentNotifications();
                    renderRecentResolutions();
                } else {
                    document.getElementById('status-container').innerHTML =
                        '<div class="error">Failed to load notification status: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Failed to load notification status: ' + error.message + '</div>';
            }
        }

        function renderNotificationStatus() {
            const health = notificationData.status || {};
            const stats = notificationData.notification_stats || {};
            const dlq = notificationData.dlq || {};

            let html = '<div class="status-grid">';

            // Service health
            const isHealthy = health.status === 'healthy';
            html += `
                <div class="status-card ${isHealthy ? 'healthy' : 'unhealthy'}">
                    <div class="status-label">Service Status</div>
                    <div class="status-value">${health.status || 'Unknown'}</div>
                    <div>Notification Service</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Total Notifications</div>
                    <div class="status-value">${stats.total_notifications || 0}</div>
                    <div>All time</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Success Rate</div>
                    <div class="status-value">${stats.success_rate || 0}%</div>
                    <div>Delivery success</div>
                </div>
                <div class="status-card warning">
                    <div class="status-label">DLQ Items</div>
                    <div class="status-value">${dlq.items ? dlq.items.length : 0}</div>
                    <div>Failed notifications</div>
                </div>
            `;

            html += '</div>';

            // Additional statistics
            if (stats.total_notifications > 0) {
                html += '<h4>Notification Statistics</h4><div class="metric-grid">';

                html += `
                    <div class="metric-item">
                        <div class="metric-label">Successful</div>
                        <div class="metric-value">${stats.successful_notifications || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Failed</div>
                        <div class="metric-value">${stats.failed_notifications || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Owner Resolutions</div>
                        <div class="metric-value">${stats.total_owner_resolutions || 0}</div>
                    </div>
                `;

                html += '</div>';

                // Channels used
                if (stats.channels_used && stats.channels_used.length > 0) {
                    html += '<h4>Channels Used</h4><div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;">';
                    stats.channels_used.forEach(channel => {
                        const channelClass = channel.toLowerCase();
                        html += `<span class="badge ${channelClass}">${channel.toUpperCase()}</span>`;
                    });
                    html += '</div>';
                }
            }

            document.getElementById('status-container').innerHTML = html;
        }

        function renderRecentNotifications() {
            const notifications = notificationData.notifications || [];

            if (notifications.length === 0) {
                document.getElementById('notifications-container').innerHTML = '';
                return;
            }

            let html = '<h4>Recent Notifications</h4>';

            notifications.forEach(notification => {
                const timestamp = new Date(notification.timestamp).toLocaleString();
                const success = notification.success;
                const channel = notification.channel || 'unknown';

                html += `
                    <div class="notification-item ${success ? 'success' : 'failed'}">
                        <div class="notification-meta">
                            <span><strong>ID:</strong> ${notification.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span class="badge ${channel.toLowerCase()}">${channel.toUpperCase()}</span>
                            <span class="badge ${success ? 'success' : 'failed'}">${success ? 'DELIVERED' : 'FAILED'}</span>
                        </div>
                        <div class="notification-content">
                            <div class="notification-title">${notification.title || 'No title'}</div>
                            <div class="notification-message">${notification.message || 'No message'}</div>
                            ${notification.labels && notification.labels.length > 0 ? `
                                <div style="margin-top: 8px;">
                                    ${notification.labels.map(label => `<span class="badge">${label}</span>`).join('')}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                `;
            });

            document.getElementById('notifications-container').innerHTML = html;
        }

        function renderRecentResolutions() {
            const resolutions = notificationData.resolutions || [];

            if (resolutions.length === 0) {
                document.getElementById('resolutions-container').innerHTML = '';
                return;
            }

            let html = '<h4>Recent Owner Resolutions</h4>';

            resolutions.forEach(resolution => {
                const timestamp = new Date(resolution.timestamp).toLocaleString();
                const owners = resolution.owners_requested || [];
                const targets = resolution.resolved_targets || {};

                html += `
                    <div class="resolution-item">
                        <div class="resolution-meta">
                            <span><strong>ID:</strong> ${resolution.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span><strong>Resolved:</strong> ${resolution.resolution_count || 0} targets</span>
                        </div>
                        <div class="resolution-owners">
                            <strong>Requested Owners:</strong>
                            <div class="owners-list">
                                ${owners.map(owner => `<span class="owner-tag">${owner}</span>`).join('')}
                            </div>
                        </div>
                        <div class="resolution-targets">
                            <strong>Resolved Targets:</strong>
                            ${JSON.stringify(targets, null, 2)}
                        </div>
                    </div>
                `;
            });

            document.getElementById('resolutions-container').innerHTML = html;
        }

        async function loadDLQ() {
            try {
                const response = await fetch('/api/notification-service/dlq');
                const data = await response.json();

                if (data.success) {
                    renderDLQ(data.data);
                    document.getElementById('dlq-container').style.display = 'block';
                } else {
                    alert('Failed to load DLQ: ' + data.message);
                }
            } catch (error) {
                alert('Failed to load DLQ: ' + error.message);
            }
        }

        function renderDLQ(dlqItems) {
            if (!dlqItems || dlqItems.length === 0) {
                document.getElementById('dlq-items').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No items in dead letter queue</div>';
                return;
            }

            let html = '';

            dlqItems.forEach(item => {
                html += `
                    <div class="dlq-item">
                        <div class="dlq-meta">
                            <span><strong>Channel:</strong> ${item.channel || 'Unknown'}</span>
                            <span><strong>Target:</strong> ${item.target || 'Unknown'}</span>
                            <span><strong>Failed at:</strong> ${item.timestamp ? new Date(item.timestamp).toLocaleString() : 'Unknown'}</span>
                        </div>
                        <div class="dlq-error">Error: ${item.error || 'Unknown error'}</div>
                        <div class="dlq-payload">${JSON.stringify(item.payload || item, null, 2)}</div>
                    </div>
                `;
            });

            document.getElementById('dlq-items').innerHTML = html;
        }

        async function resolveOwners(event) {
            event.preventDefault();

            const ownersText = document.getElementById('test-owners').value;
            const owners = ownersText.split(',').map(o => o.trim()).filter(o => o);

            if (owners.length === 0) {
                alert('Please enter at least one owner name');
                return;
            }

            const resultDiv = document.getElementById('resolution-result');
            resultDiv.innerHTML = '<div style="color: #666;">Resolving owners...</div>';

            try {
                const payload = { owners: owners };

                const response = await fetch('/api/notification-service/resolve-owners', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    resultDiv.innerHTML = `
                        <div style="color: #28a745; margin-bottom: 10px;">✓ Owner resolution completed!</div>
                        <div><strong>Resolution ID:</strong> ${data.resolution_id}</div>
                        <div><strong>Targets Found:</strong> ${data.resolution_count}</div>
                        <div class="resolution-targets">${JSON.stringify(data.resolved_targets, null, 2)}</div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div style="color: #dc3545;">✗ Owner resolution failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new resolution
                loadNotificationStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div style="color: #dc3545;">✗ Error: ${error.message}</div>`;
            }
        }

        async function sendNotification(event) {
            event.preventDefault();

            const channel = document.getElementById('notify-channel').value;
            const target = document.getElementById('notify-target').value;
            const title = document.getElementById('notify-title').value;
            const message = document.getElementById('notify-message').value;
            const labelsText = document.getElementById('notify-labels').value;

            if (!target || !title || !message) {
                alert('Please fill in channel, target, title, and message');
                return;
            }

            const labels = labelsText ? labelsText.split(',').map(l => l.trim()).filter(l => l) : [];

            const resultDiv = document.getElementById('notification-result');
            resultDiv.innerHTML = '<div style="color: #666;">Sending notification...</div>';

            try {
                const payload = {
                    channel: channel,
                    target: target,
                    title: title,
                    message: message,
                    labels: labels
                };

                const response = await fetch('/api/notification-service/send', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    resultDiv.innerHTML = `
                        <div style="color: #28a745; margin-bottom: 10px;">✓ Notification sent successfully!</div>
                        <div><strong>Notification ID:</strong> ${data.notification_id}</div>
                        <div class="notification-message">${JSON.stringify(data.response, null, 2)}</div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div style="color: #dc3545;">✗ Notification failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new notification
                loadNotificationStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div style="color: #dc3545;">✗ Error: ${error.message}</div>`;
            }
        }

        async function loadHistory() {
            try {
                const [notifyResponse, resolveResponse] = await Promise.all([
                    fetch('/api/notification-service/notifications?limit=50'),
                    fetch('/api/notification-service/resolutions?limit=50')
                ]);

                const notifyData = await notifyResponse.json();
                const resolveData = await resolveResponse.json();

                if (notifyData.success) {
                    notificationData.notifications = notifyData.data;
                    renderRecentNotifications();
                }

                if (resolveData.success) {
                    notificationData.resolutions = resolveData.data;
                    renderRecentResolutions();
                }

            } catch (error) {
                alert('Failed to load full history: ' + error.message);
            }
        }

        function refreshStatus() {
            loadNotificationStatus();
        }

        // Load initial data
        loadNotificationStatus();
    </script>
</body>
</html>
"""
            return create_html_response(html, "Notification Service Dashboard")
        except Exception as e:
            return handle_frontend_error("render notification service dashboard", e, **build_frontend_context("render_notification_service_dashboard"))
