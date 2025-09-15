"""Prompt Store UI handlers for Frontend service.

Handles prompt store browsing and analytics.
"""
from typing import Dict, Any
from fastapi.responses import HTMLResponse

from ..shared_utils import (
    create_html_response,
    handle_frontend_error,
    build_frontend_context
)
from services.frontend.modules.data_browser import (
    get_prompt_store_summary
)


class PromptStoreUIHandlers:
    """Handles prompt store UI rendering."""

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
        select {
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
        .prompt-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .prompt-title {
            font-size: 1.1em;
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }
        .prompt-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .prompt-text {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            margin: 10px 0;
        }
        .prompt-variables {
            background: #e9ecef;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            font-size: 12px;
        }
        .variable-tag {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            margin: 2px 4px 2px 0;
            font-size: 11px;
        }
        .analytics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .analytics-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #17a2b8;
        }
        .analytics-value {
            font-size: 2em;
            font-weight: bold;
            color: #17a2b8;
            margin: 10px 0;
        }
        .analytics-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
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
        .category-section {
            margin: 20px 0;
        }
        .category-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #495057;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 2px solid #17a2b8;
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
        .badge {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 2px 5px 2px 0;
        }
        .badge.category {
            background: #28a745;
        }
        .badge.version {
            background: #ffc107;
            color: black;
        }
        .performance-metrics {
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
            <h1>Prompt Store Browser</h1>
            <p>Explore and manage stored prompts and A/B testing results</p>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('prompts')">Prompts</div>
            <div class="tab" onclick="showTab('analytics')">Analytics</div>
            <div class="tab" onclick="showTab('categories')">Categories</div>
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
                        <option value="20">20</option>
                        <option value="50" selected>50</option>
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

        <div id="categories-content" class="tab-content">
            <button class="btn" onclick="loadCategories()">Load Categories</button>
            <div id="categories-container" class="loading">Loading categories...</div>
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

        async function loadPrompts() {
            const category = document.getElementById('category-filter').value;
            const limit = document.getElementById('prompt-limit').value;

            document.getElementById('prompts-container').innerHTML = 'Loading prompts...';

            let url = \`/api/prompt-store/prompts?limit={{limit}&offset={{currentPromptOffset}\`;
            if (category) url += \`&category={{encodeURIComponent(category)}\`;

            try {
                const response = await fetch(url);
                const data = await response.json();

                if (data.success) {
                    renderPrompts(data.data);
                    updateCategoryFilter(data.data);
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

            let html = '';

            prompts.forEach(prompt => {
                const created = prompt.created_at ? new Date(prompt.created_at).toLocaleString() : 'Unknown';
                const updated = prompt.updated_at ? new Date(prompt.updated_at).toLocaleString() : 'Unknown';
                const variables = prompt.variables || [];

                html += \`
                    <div class="prompt-item" onclick="viewPrompt('{{prompt.id}')">
                        <div class="prompt-title">{{prompt.name || prompt.id}</div>
                        <div class="prompt-meta">
                            <span><span class="badge category">{{prompt.category || 'Uncategorized'}</span></span>
                            <span><span class="badge version">v{{prompt.version || '1.0'}</span></span>
                            <span>Created: {{created}</span>
                            <span>Updated: {{updated}</span>
                            <span>Usage: {{prompt.usage_count || 0}</span>
                        </div>
                        <div class="prompt-text">{{(prompt.text || 'No prompt text').substring(0, 200)}...</div>
                        {{variables.length > 0 ? \`
                            <div class="prompt-variables">
                                <strong>Variables:</strong> {{variables.map(v => \`<span class="variable-tag">{{{{v}}}</span>\`).join('')}
                            </div>
                        \` : ''}
                    </div>
                \`;
            });

            // Pagination
            const hasNext = prompts.length === parseInt(document.getElementById('prompt-limit').value);
            const hasPrev = currentPromptOffset > 0;

            html += '<div class="pagination">';
            html += \`<button class="page-btn {{hasPrev ? '' : 'disabled'}" onclick="prevPromptPage()">Previous</button>\`;
            html += \`<span>Page {{Math.floor(currentPromptOffset / parseInt(document.getElementById('prompt-limit').value)) + 1}</span>\`;
            html += \`<button class="page-btn {{hasNext ? '' : 'disabled'}" onclick="nextPromptPage()">Next</button>\`;
            html += '</div>';

            document.getElementById('prompts-container').innerHTML = html;
        }

        function updateCategoryFilter(data) {
            const prompts = data.prompts || [];
            const categories = new Set();

            prompts.forEach(prompt => {
                if (prompt.category) categories.add(prompt.category);
            });

            const select = document.getElementById('category-filter');
            const currentValue = select.value;

            select.innerHTML = '<option value="">All Categories</option>';

            Array.from(categories).sort().forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                if (category === currentValue) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
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

            // Overview metrics
            html += \`
                <div class="analytics-card">
                    <div class="analytics-label">Total Prompts</div>
                    <div class="analytics-value">{{analytics.total_prompts || 0}</div>
                    <div>Active prompts</div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-label">Categories</div>
                    <div class="analytics-value">{{analytics.total_categories || 0}</div>
                    <div>Organized groups</div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-label">Total Usage</div>
                    <div class="analytics-value">{{analytics.total_usage || 0}</div>
                    <div>Times executed</div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-label">Avg Performance</div>
                    <div class="analytics-value">{{analytics.avg_performance ? analytics.avg_performance.toFixed(2) : 'N/A'}</div>
                    <div>Score out of 10</div>
                </div>
            \`;

            html += '</div>';

            // Category breakdown
            if (analytics.category_breakdown) {
                html += '<h4>Prompt Usage by Category</h4><div class="analytics-grid">';

                Object.entries(analytics.category_breakdown).forEach(([category, stats]) => {
                    html += \`
                        <div class="analytics-card">
                            <div class="analytics-label">{{category}</div>
                            <div class="analytics-value">{{stats.count || 0}</div>
                            <div>Prompts</div>
                            <div style="font-size: 11px; margin-top: 5px;">{{stats.avg_usage || 0} avg usage</div>
                        </div>
                    \`;
                });

                html += '</div>';
            }

            // Performance metrics
            if (analytics.performance_metrics) {
                html += '<h4>Performance Metrics</h4><div class="performance-metrics">';

                Object.entries(analytics.performance_metrics).forEach(([metric, value]) => {
                    html += \`
                        <div class="metric-item">
                            <div class="metric-label">{{metric.replace(/_/g, ' ')}</div>
                            <div class="metric-value">{{typeof value === 'number' ? value.toFixed(2) : value}</div>
                        </div>
                    \`;
                });

                html += '</div>';
            }

            document.getElementById('analytics-container').innerHTML = html;
        }

        async function loadCategories() {
            document.getElementById('categories-container').innerHTML = 'Loading categories...';

            try {
                // Get all prompts to analyze categories
                const response = await fetch('/api/prompt-store/prompts?limit=1000');
                const data = await response.json();

                if (data.success) {
                    renderCategories(data.data);
                } else {
                    document.getElementById('categories-container').innerHTML =
                        '<div class="error">Failed to load categories: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('categories-container').innerHTML =
                    '<div class="error">Failed to load categories: ' + error.message + '</div>';
            }
        }

        function renderCategories(data) {
            const prompts = data.prompts || [];
            const categories = {};

            // Group prompts by category
            prompts.forEach(prompt => {
                const category = prompt.category || 'Uncategorized';
                if (!categories[category]) {
                    categories[category] = [];
                }
                categories[category].push(prompt);
            });

            if (Object.keys(categories).length === 0) {
                document.getElementById('categories-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No categories found</div>';
                return;
            }

            let html = '';

            Object.entries(categories).forEach(([categoryName, categoryPrompts]) => {
                const totalUsage = categoryPrompts.reduce((sum, p) => sum + (p.usage_count || 0), 0);
                const avgPerformance = categoryPrompts.reduce((sum, p) => sum + (p.performance_score || 0), 0) / categoryPrompts.length;

                html += \`
                    <div class="category-section">
                        <div class="category-title">
                            {{categoryName} ({{categoryPrompts.length} prompts)
                            <span style="float: right; font-size: 14px; color: #666;">
                                Total Usage: {{totalUsage} |
                                Avg Performance: {{avgPerformance ? avgPerformance.toFixed(1) : 'N/A'}
                            </span>
                        </div>
                \`;

                categoryPrompts.forEach(prompt => {
                    const created = prompt.created_at ? new Date(prompt.created_at).toLocaleString() : 'Unknown';

                    html += \`
                        <div class="prompt-item" onclick="viewPrompt('{{prompt.id}')">
                            <div class="prompt-title">{{prompt.name || prompt.id}</div>
                            <div class="prompt-meta">
                                <span><span class="badge version">v{{prompt.version || '1.0'}</span></span>
                                <span>Created: {{created}</span>
                                <span>Usage: {{prompt.usage_count || 0}</span>
                                <span>Performance: {{prompt.performance_score || 'N/A'}</span>
                            </div>
                            <div class="prompt-text">{{(prompt.text || 'No prompt text').substring(0, 150)}...</div>
                        </div>
                    \`;
                });

                html += '</div>';
            });

            document.getElementById('categories-container').innerHTML = html;
        }

        function viewPrompt(promptId) {
            // Could open a modal or navigate to prompt detail view
            alert(\`Prompt details for ID: {{promptId}\\n\\nFeature not yet implemented.\`);
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
    </script>
</body>
</html>
"""
            return create_html_response(html, "Prompt Store Browser")
        except Exception as e:
            return handle_frontend_error("render prompt store browser", e, **build_frontend_context("render_prompt_store_browser"))
