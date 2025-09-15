"""Memory Agent UI handlers for Frontend service.

Handles memory agent service visualization, including operational
context storage, event summaries, and memory item management.
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
from ..memory_agent_monitor import memory_agent_monitor


class MemoryAgentUIHandlers:
    """Handles memory agent UI rendering."""

    @staticmethod
    def handle_memory_agent_dashboard() -> HTMLResponse:
        """Render memory agent service monitoring dashboard."""
        try:
            clients = get_frontend_clients()

            # Get memory agent status and cached data
            status_data = memory_agent_monitor.get_memory_status()
            memory_history = memory_agent_monitor.get_memory_history(limit=20)

            # Build context for template
            context = {
                "health": status_data.get("health", {}),
                "memory_stats": status_data.get("memory_stats", {}),
                "recent_items": memory_history,
                "last_updated": status_data.get("last_updated", "Never")
            }

            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memory Agent Dashboard - LLM Documentation Ecosystem</title>
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
        .memory-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .memory-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .memory-key {
            font-weight: 500;
            margin: 10px 0;
            color: #495057;
        }
        .memory-value {
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
        .memory-metadata {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
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
        .badge.summary {
            background: #28a745;
        }
        .badge.event {
            background: #ffc107;
            color: black;
        }
        .badge.context {
            background: #6c757d;
        }
        .badge.finding {
            background: #dc3545;
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
        .filter-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .filter-form {
            display: flex;
            gap: 15px;
            align-items: end;
            flex-wrap: wrap;
        }
        .filter-group {
            display: flex;
            flex-direction: column;
            min-width: 150px;
        }
        .filter-group label {
            font-weight: 500;
            margin-bottom: 5px;
            color: #495057;
            font-size: 14px;
        }
        .filter-group select,
        .filter-group input {
            padding: 6px 10px;
            border: 1px solid #ced4da;
            border-radius: 4px;
        }
        .capacity-bar {
            width: 100%;
            height: 12px;
            background: #e9ecef;
            border-radius: 6px;
            overflow: hidden;
            margin: 5px 0;
        }
        .capacity-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #ffc107 70%, #dc3545 90%);
            transition: width 0.3s ease;
        }
        .capacity-fill.warning {
            background: #ffc107;
        }
        .capacity-fill.danger {
            background: #dc3545;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Memory Agent Dashboard</h1>
            <p>Monitor operational context and event summary storage</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="refreshStatus()">Refresh Status</button>
            <button class="btn secondary" onclick="loadMemoryItems()">Load Recent Items</button>
            <button class="btn success" onclick="loadAllHistory()">Load Full History</button>
        </div>

        <div id="status-container">
            <!-- Status will be loaded here -->
        </div>

        <div class="filter-section">
            <h3>Filter Memory Items</h3>
            <form class="filter-form" onsubmit="filterMemoryItems(event)">
                <div class="filter-group">
                    <label for="filter-type">Type:</label>
                    <select id="filter-type">
                        <option value="">All Types</option>
                        <option value="summary">Summary</option>
                        <option value="event">Event</option>
                        <option value="context">Context</option>
                        <option value="finding">Finding</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-key">Key:</label>
                    <input type="text" id="filter-key" placeholder="Search key...">
                </div>
                <div class="filter-group">
                    <label for="filter-limit">Limit:</label>
                    <select id="filter-limit">
                        <option value="10">10</option>
                        <option value="25">25</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                    </select>
                </div>
                <button type="submit" class="btn">Apply Filter</button>
            </form>
        </div>

        <div class="test-section">
            <h3>Store Memory Item</h3>
            <form class="test-form" onsubmit="storeMemoryItem(event)">
                <div class="form-row">
                    <div class="form-group">
                        <label for="item-type">Type:</label>
                        <select id="item-type" required>
                            <option value="summary">Summary</option>
                            <option value="event">Event</option>
                            <option value="context">Context</option>
                            <option value="finding">Finding</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="item-key">Key:</label>
                        <input type="text" id="item-key" placeholder="unique-key" required>
                    </div>
                </div>
                <div class="form-group">
                    <label for="item-value">Value:</label>
                    <textarea id="item-value" placeholder="Memory item content..." required>Sample memory content for testing</textarea>
                </div>
                <div class="form-group">
                    <label for="item-metadata">Metadata (JSON, optional):</label>
                    <textarea id="item-metadata" placeholder='{"source": "test", "priority": "low"}'></textarea>
                </div>
                <button type="submit" class="btn">Store Item</button>
            </form>
            <div id="store-result" style="margin-top: 20px;"></div>
        </div>

        <div id="memory-container">
            <!-- Memory items will be loaded here -->
        </div>
    </div>

    <script>
        let memoryData = {
            status: {},
            items: [],
            memory_stats: {},
            filters: {
                type: '',
                key: '',
                limit: 25
            }
        };

        async function loadMemoryStatus() {
            try {
                const response = await fetch('/api/memory-agent/status');
                const data = await response.json();

                if (data.success) {
                    memoryData = data.data;
                    renderMemoryStatus();
                    renderRecentItems();
                } else {
                    document.getElementById('status-container').innerHTML =
                        '<div class="error">Failed to load memory status: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Failed to load memory status: ' + error.message + '</div>';
            }
        }

        function renderMemoryStatus() {
            const health = memoryData.status || {};
            const stats = memoryData.memory_stats || {};

            let html = '<div class="status-grid">';

            // Service health
            const isHealthy = health.status === 'healthy';
            const usagePercent = health.memory_usage_percent || 0;
            const capacityClass = usagePercent > 90 ? 'danger' : usagePercent > 70 ? 'warning' : '';

            html += `
                <div class="status-card ${isHealthy ? 'healthy' : 'unhealthy'}">
                    <div class="status-label">Service Status</div>
                    <div class="status-value">${health.status || 'Unknown'}</div>
                    <div>Memory Agent</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Memory Count</div>
                    <div class="status-value">${health.memory_count || 0}</div>
                    <div>Items stored</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Capacity</div>
                    <div class="status-value">${health.memory_capacity || 0}</div>
                    <div>Max items</div>
                </div>
                <div class="status-card ${capacityClass ? 'warning' : ''}">
                    <div class="status-label">Usage</div>
                    <div class="status-value">${usagePercent}%</div>
                    <div class="capacity-bar">
                        <div class="capacity-fill ${capacityClass}" style="width: ${usagePercent}%"></div>
                    </div>
                </div>
            `;

            html += '</div>';

            // Memory statistics
            if (stats.total_items_cached > 0) {
                html += '<h4>Memory Statistics</h4><div class="metric-grid">';

                html += `
                    <div class="metric-item">
                        <div class="metric-label">Cached Items</div>
                        <div class="metric-value">${stats.total_items_cached || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Unique Types</div>
                        <div class="metric-value">${stats.unique_types || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Most Common</div>
                        <div class="metric-value">${stats.most_common_type || 'N/A'}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">TTL (seconds)</div>
                        <div class="metric-value">${health.ttl_seconds || 0}</div>
                    </div>
                `;

                html += '</div>';
            }

            document.getElementById('status-container').innerHTML = html;
        }

        function renderRecentItems() {
            const items = memoryData.items || [];

            if (items.length === 0) {
                document.getElementById('memory-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No memory items to display</div>';
                return;
            }

            let html = '<h4>Memory Items</h4>';

            items.forEach(item => {
                const timestamp = item.timestamp ? new Date(item.timestamp).toLocaleString() : 'Unknown';
                const itemType = item.type || 'unknown';
                const typeClass = itemType.toLowerCase();

                html += `
                    <div class="memory-item">
                        <div class="memory-meta">
                            <span><strong>ID:</strong> ${item.id || 'Unknown'}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span class="badge ${typeClass}">${itemType.toUpperCase()}</span>
                        </div>
                        <div class="memory-key"><strong>Key:</strong> ${item.key || 'No key'}</div>
                        <div class="memory-value">${item.value || 'No value'}</div>
                        ${item.metadata && Object.keys(item.metadata).length > 0 ? `
                            <div class="memory-metadata">${JSON.stringify(item.metadata, null, 2)}</div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('memory-container').innerHTML = html;
        }

        async function filterMemoryItems(event) {
            event.preventDefault();

            const type = document.getElementById('filter-type').value;
            const key = document.getElementById('filter-key').value;
            const limit = document.getElementById('filter-limit').value;

            memoryData.filters = { type, key, limit };

            await loadFilteredItems();
        }

        async function loadFilteredItems() {
            try {
                const filters = memoryData.filters;
                let url = `/api/memory-agent/items?limit=${filters.limit}`;

                if (filters.type) {
                    url += `&type=${filters.type}`;
                }
                if (filters.key) {
                    url += `&key=${filters.key}`;
                }

                const response = await fetch(url);
                const data = await response.json();

                if (data.success) {
                    memoryData.items = data.data;
                    renderRecentItems();
                } else {
                    alert('Failed to load filtered items: ' + data.message);
                }
            } catch (error) {
                alert('Failed to load filtered items: ' + error.message);
            }
        }

        async function storeMemoryItem(event) {
            event.preventDefault();

            const itemType = document.getElementById('item-type').value;
            const itemKey = document.getElementById('item-key').value;
            const itemValue = document.getElementById('item-value').value;
            const metadataText = document.getElementById('item-metadata').value;

            if (!itemType || !itemKey || !itemValue) {
                alert('Please fill in all required fields');
                return;
            }

            let metadata = {};
            if (metadataText.trim()) {
                try {
                    metadata = JSON.parse(metadataText);
                } catch (e) {
                    alert('Invalid JSON in metadata: ' + e.message);
                    return;
                }
            }

            const resultDiv = document.getElementById('store-result');
            resultDiv.innerHTML = '<div style="color: #666;">Storing memory item...</div>';

            try {
                const payload = {
                    type: itemType,
                    key: itemKey,
                    value: itemValue,
                    metadata: metadata
                };

                const response = await fetch('/api/memory-agent/store', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    resultDiv.innerHTML = `
                        <div style="color: #28a745; margin-bottom: 10px;">✓ Memory item stored successfully!</div>
                        <div><strong>Item ID:</strong> ${data.item_id}</div>
                        <div><strong>Response:</strong></div>
                        <div class="memory-value">${JSON.stringify(data.response, null, 2)}</div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div style="color: #dc3545;">✗ Failed to store memory item: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new item
                loadMemoryStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div style="color: #dc3545;">✗ Error: ${error.message}</div>`;
            }
        }

        async function loadMemoryItems() {
            await loadFilteredItems();
        }

        async function loadAllHistory() {
            try {
                const response = await fetch('/api/memory-agent/history?limit=100');
                const data = await response.json();

                if (data.success) {
                    memoryData.items = data.data;
                    renderRecentItems();
                } else {
                    alert('Failed to load full history: ' + data.message);
                }
            } catch (error) {
                alert('Failed to load full history: ' + error.message);
            }
        }

        function refreshStatus() {
            loadMemoryStatus();
        }

        // Load initial data
        loadMemoryStatus();
    </script>
</body>
</html>
"""
            return create_html_response(html, "Memory Agent Dashboard")
        except Exception as e:
            return handle_frontend_error("render memory agent dashboard", e, **build_frontend_context("render_memory_agent_dashboard"))
