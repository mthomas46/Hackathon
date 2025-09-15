"""Doc Store UI handlers for Frontend service.

Handles document store browsing and exploration.
"""
from typing import Dict, Any
from fastapi.responses import HTMLResponse

from ..shared_utils import (
    get_frontend_clients,
    create_html_response,
    handle_frontend_error,
    build_frontend_context
)
from services.frontend.modules.data_browser import (
    get_doc_store_summary
)


class DocStoreUIHandlers:
    """Handles doc store UI rendering."""

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
        input, select {
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
        .document-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .document-title {
            font-size: 1.1em;
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }
        .document-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .document-content {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 10px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            max-height: 200px;
            overflow-y: auto;
            margin-top: 10px;
        }
        .quality-metrics {
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
        .search-results {
            margin-top: 20px;
        }
        .analysis-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
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
        .badge.quality-good {
            background: #28a745;
        }
        .badge.quality-medium {
            background: #ffc107;
            color: black;
        }
        .badge.quality-poor {
            background: #dc3545;
        }
        .code-example {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .code-language {
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }
        .code-content {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Doc Store Browser</h1>
            <p>Explore and manage stored documents</p>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('documents')">Documents</div>
            <div class="tab" onclick="showTab('search')">Search</div>
            <div class="tab" onclick="showTab('quality')">Quality</div>
            <div class="tab" onclick="showTab('analyses')">Analyses</div>
            <div class="tab" onclick="showTab('styles')">Code Styles</div>
        </div>

        <div id="documents-content" class="tab-content active">
            <div class="controls">
                <div class="control-group">
                    <label>Limit:</label>
                    <select id="doc-limit">
                        <option value="20">20</option>
                        <option value="50" selected>50</option>
                        <option value="100">100</option>
                    </select>
                </div>
                <button class="btn" onclick="loadDocuments()">Load Documents</button>
                <button class="btn secondary" onclick="refreshDocuments()">Refresh</button>
            </div>
            <div id="documents-container" class="loading">Loading documents...</div>
        </div>

        <div id="search-content" class="tab-content">
            <div class="controls">
                <div class="control-group">
                    <label>Search:</label>
                    <input type="text" id="search-query" placeholder="Enter search query...">
                </div>
                <div class="control-group">
                    <label>Limit:</label>
                    <select id="search-limit">
                        <option value="20">20</option>
                        <option value="50" selected>50</option>
                        <option value="100">100</option>
                    </select>
                </div>
                <button class="btn" onclick="searchDocuments()">Search</button>
                <button class="btn secondary" onclick="clearSearch()">Clear</button>
            </div>
            <div id="search-container" class="loading">Ready to search...</div>
        </div>

        <div id="quality-content" class="tab-content">
            <button class="btn" onclick="loadQualityMetrics()">Load Quality Metrics</button>
            <div id="quality-container" class="loading">Loading quality metrics...</div>
        </div>

        <div id="analyses-content" class="tab-content">
            <div class="controls">
                <div class="control-group">
                    <label>Document ID:</label>
                    <input type="text" id="analysis-doc-id" placeholder="Optional: specific document ID">
                </div>
                <div class="control-group">
                    <label>Limit:</label>
                    <select id="analysis-limit">
                        <option value="20">20</option>
                        <option value="50" selected>50</option>
                        <option value="100">100</option>
                    </select>
                </div>
                <button class="btn" onclick="loadAnalyses()">Load Analyses</button>
                <button class="btn secondary" onclick="refreshAnalyses()">Refresh</button>
            </div>
            <div id="analyses-container" class="loading">Loading analyses...</div>
        </div>

        <div id="styles-content" class="tab-content">
            <button class="btn" onclick="loadStyleExamples()">Load Style Examples</button>
            <div id="styles-container" class="loading">Loading code style examples...</div>
        </div>
    </div>

    <script>
        let currentDocOffset = 0;
        let currentSearchOffset = 0;
        let currentAnalysisOffset = 0;

        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }

        async function loadDocuments() {
            const limit = document.getElementById('doc-limit').value;
            document.getElementById('documents-container').innerHTML = 'Loading documents...';

            try {
                const response = await fetch(\`/api/doc-store/documents?limit={{limit}&offset={{currentDocOffset}\`);
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

            let html = '';

            documents.forEach(doc => {
                const qualityClass = getQualityBadgeClass(doc.quality_score || 0);
                const created = doc.created_at ? new Date(doc.created_at).toLocaleString() : 'Unknown';

                html += \`
                    <div class="document-item" onclick="viewDocument('{{doc.id}')">
                        <div class="document-title">{{doc.title || doc.id}</div>
                        <div class="document-meta">
                            <span>ID: {{doc.id}</span>
                            <span>Type: {{doc.doc_type || 'Unknown'}</span>
                            <span>Created: {{created}</span>
                            <span><span class="badge {{qualityClass}">Quality: {{doc.quality_score || 'N/A'}</span></span>
                        </div>
                        <div class="document-content">{{(doc.content || 'No content preview').substring(0, 200)}...</div>
                    </div>
                \`;
            });

            // Pagination
            const hasNext = documents.length === parseInt(document.getElementById('doc-limit').value);
            const hasPrev = currentDocOffset > 0;

            html += '<div class="pagination">';
            html += \`<button class="page-btn {{hasPrev ? '' : 'disabled'}" onclick="prevDocPage()">Previous</button>\`;
            html += \`<span>Page {{Math.floor(currentDocOffset / parseInt(document.getElementById('doc-limit').value)) + 1}</span>\`;
            html += \`<button class="page-btn {{hasNext ? '' : 'disabled'}" onclick="nextDocPage()">Next</button>\`;
            html += '</div>';

            document.getElementById('documents-container').innerHTML = html;
        }

        async function searchDocuments() {
            const query = document.getElementById('search-query').value.trim();
            const limit = document.getElementById('search-limit').value;

            if (!query) {
                alert('Please enter a search query');
                return;
            }

            document.getElementById('search-container').innerHTML = 'Searching...';

            try {
                const response = await fetch(\`/api/doc-store/search?q={{encodeURIComponent(query)}&limit={{limit}\`);
                const data = await response.json();

                if (data.success) {
                    renderSearchResults(data.data, query);
                } else {
                    document.getElementById('search-container').innerHTML =
                        '<div class="error">Search failed: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('search-container').innerHTML =
                    '<div class="error">Search failed: ' + error.message + '</div>';
            }
        }

        function renderSearchResults(data, query) {
            const results = data.results || [];

            let html = \`<h4>Search Results for "{{query}"</h4>\`;

            if (results.length === 0) {
                html += '<div style="text-align: center; color: #666; padding: 40px;">No documents found matching your query</div>';
            } else {
                html += '<div class="search-results">';
                results.forEach(result => {
                    const relevance = result.relevance ? (result.relevance * 100).toFixed(1) + '%' : 'N/A';

                    html += \`
                        <div class="document-item" onclick="viewDocument('{{result.id}')">
                            <div class="document-title">{{result.title || result.id}</div>
                            <div class="document-meta">
                                <span>ID: {{result.id}</span>
                                <span>Relevance: {{relevance}</span>
                                <span>Type: {{result.doc_type || 'Unknown'}</span>
                            </div>
                            <div class="document-content">{{(result.content || '').substring(0, 300)}...</div>
                        </div>
                    \`;
                });
                html += '</div>';
            }

            document.getElementById('search-container').innerHTML = html;
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
            const metrics = data.metrics || {};

            let html = '<div class="quality-metrics">';

            Object.entries(metrics).forEach(([metric, value]) => {
                const displayValue = typeof value === 'number' ? value.toLocaleString() : value;
                html += \`
                    <div class="metric-item">
                        <div class="metric-label">{{metric.replace(/_/g, ' ')}</div>
                        <div class="metric-value">{{displayValue}</div>
                    </div>
                \`;
            });

            html += '</div>';

            // Additional insights
            if (data.insights) {
                html += '<h4>Quality Insights</h4><div class="quality-metrics">';

                data.insights.forEach(insight => {
                    html += \`
                        <div class="metric-item">
                            <div class="metric-label">{{insight.category}</div>
                            <div class="metric-value">{{insight.count}</div>
                            <div style="font-size: 11px; margin-top: 5px;">{{insight.description}</div>
                        </div>
                    \`;
                });

                html += '</div>';
            }

            document.getElementById('quality-container').innerHTML = html;
        }

        async function loadAnalyses() {
            const docId = document.getElementById('analysis-doc-id').value.trim();
            const limit = document.getElementById('analysis-limit').value;

            document.getElementById('analyses-container').innerHTML = 'Loading analyses...';

            let url = \`/api/doc-store/analyses?limit={{limit}&offset={{currentAnalysisOffset}\`;
            if (docId) url += \`&document_id={{docId}\`;

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

            let html = '';

            analyses.forEach(analysis => {
                const created = analysis.created_at ? new Date(analysis.created_at).toLocaleString() : 'Unknown';

                html += \`
                    <div class="analysis-item">
                        <div class="document-title">Analysis {{analysis.id}</div>
                        <div class="document-meta">
                            <span>Document: {{analysis.document_id || 'N/A'}</span>
                            <span>Type: {{analysis.analysis_type || 'Unknown'}</span>
                            <span>Created: {{created}</span>
                            <span>Score: {{analysis.score || 'N/A'}</span>
                        </div>
                        <div class="document-content">{{analysis.summary || 'No summary available'}</div>
                    </div>
                \`;
            });

            // Pagination
            const hasNext = analyses.length === parseInt(document.getElementById('analysis-limit').value);
            const hasPrev = currentAnalysisOffset > 0;

            html += '<div class="pagination">';
            html += \`<button class="page-btn {{hasPrev ? '' : 'disabled'}" onclick="prevAnalysisPage()">Previous</button>\`;
            html += \`<span>Page {{Math.floor(currentAnalysisOffset / parseInt(document.getElementById('analysis-limit').value)) + 1}</span>\`;
            html += \`<button class="page-btn {{hasNext ? '' : 'disabled'}" onclick="nextAnalysisPage()">Next</button>\`;
            html += '</div>';

            document.getElementById('analyses-container').innerHTML = html;
        }

        async function loadStyleExamples() {
            document.getElementById('styles-container').innerHTML = 'Loading style examples...';

            try {
                const response = await fetch('/api/doc-store/style-examples');
                const data = await response.json();

                if (data.success) {
                    renderStyleExamples(data.data);
                } else {
                    document.getElementById('styles-container').innerHTML =
                        '<div class="error">Failed to load style examples: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('styles-container').innerHTML =
                    '<div class="error">Failed to load style examples: ' + error.message + '</div>';
            }
        }

        function renderStyleExamples(data) {
            const examples = data.examples || {};

            if (Object.keys(examples).length === 0) {
                document.getElementById('styles-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No style examples available</div>';
                return;
            }

            let html = '';

            Object.entries(examples).forEach(([language, styles]) => {
                html += \`<h4>{{language.charAt(0).toUpperCase() + language.slice(1)} Code Styles</h4>\`;

                Object.entries(styles).forEach(([styleName, example]) => {
                    html += \`
                        <div class="code-example">
                            <div class="code-language">{{styleName} Style</div>
                            <div class="code-content">{{example}</div>
                        </div>
                    \`;
                });
            });

            document.getElementById('styles-container').innerHTML = html;
        }

        function getQualityBadgeClass(score) {
            if (score >= 0.8) return 'quality-good';
            if (score >= 0.6) return 'quality-medium';
            return 'quality-poor';
        }

        function viewDocument(docId) {
            // Navigate to document detail view
            window.open(\`/api/doc-store/documents/{{docId}\`, '_blank');
        }

        function clearSearch() {
            document.getElementById('search-query').value = '';
            document.getElementById('search-container').innerHTML = 'Ready to search...';
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

        function prevAnalysisPage() {
            const limit = parseInt(document.getElementById('analysis-limit').value);
            if (currentAnalysisOffset >= limit) {
                currentAnalysisOffset -= limit;
                loadAnalyses();
            }
        }

        function nextAnalysisPage() {
            const limit = parseInt(document.getElementById('analysis-limit').value);
            currentAnalysisOffset += limit;
            loadAnalyses();
        }

        // Helper functions
        function refreshDocuments() { currentDocOffset = 0; loadDocuments(); }
        function refreshAnalyses() { currentAnalysisOffset = 0; loadAnalyses(); }
    </script>
</body>
</html>
"""
            return create_html_response(html, "Doc Store Browser")
        except Exception as e:
            return handle_frontend_error("render doc store browser", e, **build_frontend_context("render_doc_store_browser"))
