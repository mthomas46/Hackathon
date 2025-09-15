"""Code Analyzer UI handlers for Frontend service.

Handles code analyzer service visualization.
"""
from typing import Dict, Any
from fastapi.responses import HTMLResponse

from ..shared_utils import (
    create_html_response,
    handle_frontend_error,
    build_frontend_context
)
from services.frontend.modules.code_analyzer_monitor import code_analyzer_monitor


class CodeAnalyzerUIHandlers:
    """Handles code analyzer UI rendering."""

    @staticmethod
    def handle_code_analyzer_dashboard() -> HTMLResponse:
        """Render code analyzer service dashboard."""
        try:
            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Analyzer Dashboard - LLM Documentation Ecosystem</title>
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
        textarea, input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        textarea {
            min-height: 200px;
            resize: vertical;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
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
        .analysis-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .analysis-title {
            font-size: 1.1em;
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }
        .analysis-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .analysis-result {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            margin-top: 10px;
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
            color: #155724;
            background: #d4edda;
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
        .badge.security {
            background: #dc3545;
        }
        .badge.analysis {
            background: #28a745;
        }
        .badge.style {
            background: #ffc107;
            color: black;
        }
        .analysis-form {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #495057;
        }
        .security-result {
            background: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #dc3545;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Code Analyzer Dashboard</h1>
            <p>Analyze code for quality, security, and style issues</p>
        </div>

        <div id="summary-container" class="loading">Loading analyzer status...</div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('analyze-text')">Analyze Text</div>
            <div class="tab" onclick="showTab('analyze-files')">Analyze Files</div>
            <div class="tab" onclick="showTab('security-scan')">Security Scan</div>
            <div class="tab" onclick="showTab('style-check')">Style Check</div>
            <div class="tab" onclick="showTab('history')">Analysis History</div>
        </div>

        <div id="analyze-text-content" class="tab-content active">
            <div class="analysis-form">
                <h3>Analyze Text</h3>
                <form id="text-analysis-form">
                    <div class="form-group">
                        <label for="analysis-text">Code Text:</label>
                        <textarea id="analysis-text" placeholder="Paste your code here..."></textarea>
                    </div>
                    <div class="form-group">
                        <label for="text-analysis-type">Analysis Type:</label>
                        <select id="text-analysis-type">
                            <option value="general">General Analysis</option>
                            <option value="security">Security Focus</option>
                            <option value="performance">Performance Focus</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">Analyze Text</button>
                </form>
            </div>
            <div id="text-analysis-result" style="display: none;"></div>
        </div>

        <div id="analyze-files-content" class="tab-content">
            <div class="analysis-form">
                <h3>Analyze Files</h3>
                <form id="files-analysis-form">
                    <div class="form-group">
                        <label for="file-paths">File Paths (one per line):</label>
                        <textarea id="file-paths" placeholder="Enter file paths, one per line..."></textarea>
                    </div>
                    <div class="form-group">
                        <label for="files-analysis-type">Analysis Type:</label>
                        <select id="files-analysis-type">
                            <option value="general">General Analysis</option>
                            <option value="security">Security Focus</option>
                            <option value="performance">Performance Focus</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">Analyze Files</button>
                </form>
            </div>
            <div id="files-analysis-result" style="display: none;"></div>
        </div>

        <div id="security-scan-content" class="tab-content">
            <div class="analysis-form">
                <h3>Security Scan</h3>
                <form id="security-scan-form">
                    <div class="form-group">
                        <label for="security-code">Code to Scan:</label>
                        <textarea id="security-code" placeholder="Paste code to scan for security issues..."></textarea>
                    </div>
                    <button type="submit" class="btn">Run Security Scan</button>
                </form>
            </div>
            <div id="security-scan-result" style="display: none;"></div>
        </div>

        <div id="style-check-content" class="tab-content">
            <div class="controls">
                <div class="control-group">
                    <label>Style:</label>
                    <select id="style-type">
                        <option value="google">Google</option>
                        <option value="pep8">PEP 8</option>
                        <option value="linux">Linux Kernel</option>
                    </select>
                </div>
                <button class="btn" onclick="loadStyleExamples()">Load Examples</button>
            </div>
            <div class="analysis-form">
                <h3>Style Check</h3>
                <form id="style-check-form">
                    <div class="form-group">
                        <label for="style-code">Code to Check:</label>
                        <textarea id="style-code" placeholder="Paste code to check style..."></textarea>
                    </div>
                    <button type="submit" class="btn">Check Style</button>
                </form>
            </div>
            <div id="style-examples" style="display: none;"></div>
            <div id="style-check-result" style="display: none;"></div>
        </div>

        <div id="history-content" class="tab-content">
            <button class="btn" onclick="loadAnalysisHistory()">Load Analysis History</button>
            <div id="history-container" class="loading">Loading analysis history...</div>
        </div>
    </div>

    <script>
        async function loadSummary() {
            document.getElementById('summary-container').innerHTML = 'Loading analyzer status...';

            try {
                const response = await fetch('/api/code-analyzer/status');
                const data = await response.json();

                if (data.success) {
                    renderSummary(data.data);
                } else {
                    document.getElementById('summary-container').innerHTML =
                        '<div class="error">Failed to load analyzer status: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('summary-container').innerHTML =
                    '<div class="error">Failed to load analyzer status: ' + error.message + '</div>';
            }
        }

        function renderSummary(data) {
            const stats = data.analysis_stats || {};

            let html = '<div class="metric-grid">';

            html += \`
                <div class="metric-item">
                    <div class="metric-label">Total Analyses</div>
                    <div class="metric-value">{{stats.total_analyses || 0}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Security Scans</div>
                    <div class="metric-value">{{stats.total_security_scans || 0}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Style Checks</div>
                    <div class="metric-value">{{stats.total_style_checks || 0}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Available Styles</div>
                    <div class="metric-value">{{data.available_styles?.length || 0}</div>
                </div>
            \`;

            html += '</div>';

            // Analysis types breakdown
            if (stats.analysis_types) {
                html += '<h4>Analysis Types</h4><div class="metric-grid">';

                Object.entries(stats.analysis_types).forEach(([type, count]) => {
                    html += \`
                        <div class="metric-item">
                            <div class="metric-label">{{type}</div>
                            <div class="metric-value">{{count}</div>
                        </div>
                    \`;
                });

                html += '</div>';
            }

            document.getElementById('summary-container').innerHTML = html;
        }

        async function analyzeText(event) {
            event.preventDefault();

            const text = document.getElementById('analysis-text').value.trim();
            const analysisType = document.getElementById('text-analysis-type').value;

            if (!text) {
                alert('Please enter some code to analyze');
                return;
            }

            document.getElementById('text-analysis-result').innerHTML = '<div class="loading">Analyzing text...</div>';
            document.getElementById('text-analysis-result').style.display = 'block';

            try {
                const response = await fetch('/api/code-analyzer/analyze-text', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: text,
                        analysis_type: analysisType
                    })
                });

                const data = await response.json();

                if (data.success) {
                    renderAnalysisResult(data.data, 'text-analysis-result');
                } else {
                    document.getElementById('text-analysis-result').innerHTML =
                        '<div class="error">Analysis failed: ' + (data.message || 'Unknown error') + '</div>';
                }
            } catch (error) {
                document.getElementById('text-analysis-result').innerHTML =
                    '<div class="error">Analysis failed: ' + error.message + '</div>';
            }
        }

        async function analyzeFiles(event) {
            event.preventDefault();

            const filePaths = document.getElementById('file-paths').value.split('\\n').filter(p => p.trim());
            const analysisType = document.getElementById('files-analysis-type').value;

            if (filePaths.length === 0) {
                alert('Please enter at least one file path');
                return;
            }

            document.getElementById('files-analysis-result').innerHTML = '<div class="loading">Analyzing files...</div>';
            document.getElementById('files-analysis-result').style.display = 'block';

            try {
                const response = await fetch('/api/code-analyzer/analyze-files', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        files: filePaths,
                        analysis_type: analysisType
                    })
                });

                const data = await response.json();

                if (data.success) {
                    renderAnalysisResult(data.data, 'files-analysis-result');
                } else {
                    document.getElementById('files-analysis-result').innerHTML =
                        '<div class="error">Analysis failed: ' + (data.message || 'Unknown error') + '</div>';
                }
            } catch (error) {
                document.getElementById('files-analysis-result').innerHTML =
                    '<div class="error">Analysis failed: ' + error.message + '</div>';
            }
        }

        async function runSecurityScan(event) {
            event.preventDefault();

            const code = document.getElementById('security-code').value.trim();

            if (!code) {
                alert('Please enter some code to scan');
                return;
            }

            document.getElementById('security-scan-result').innerHTML = '<div class="loading">Running security scan...</div>';
            document.getElementById('security-scan-result').style.display = 'block';

            try {
                const response = await fetch('/api/code-analyzer/security-scan', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        code: code
                    })
                });

                const data = await response.json();

                if (data.success) {
                    renderSecurityResult(data.data);
                } else {
                    document.getElementById('security-scan-result').innerHTML =
                        '<div class="error">Security scan failed: ' + (data.message || 'Unknown error') + '</div>';
                }
            } catch (error) {
                document.getElementById('security-scan-result').innerHTML =
                    '<div class="error">Security scan failed: ' + error.message + '</div>';
            }
        }

        async function runStyleCheck(event) {
            event.preventDefault();

            const code = document.getElementById('style-code').value.trim();
            const style = document.getElementById('style-type').value;

            if (!code) {
                alert('Please enter some code to check');
                return;
            }

            document.getElementById('style-check-result').innerHTML = '<div class="loading">Checking style...</div>';
            document.getElementById('style-check-result').style.display = 'block';

            try {
                const response = await fetch('/api/code-analyzer/style-check', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        code: code,
                        style: style
                    })
                });

                const data = await response.json();

                if (data.success) {
                    renderStyleResult(data.data);
                } else {
                    document.getElementById('style-check-result').innerHTML =
                        '<div class="error">Style check failed: ' + (data.message || 'Unknown error') + '</div>';
                }
            } catch (error) {
                document.getElementById('style-check-result').innerHTML =
                    '<div class="error">Style check failed: ' + error.message + '</div>';
            }
        }

        function renderAnalysisResult(data, containerId) {
            const result = data.result || {};

            let html = '<div class="analysis-result">';
            html += '<h4>Analysis Results</h4>';
            html += \`<div><strong>Analysis ID:</strong> {{data.analysis_id || 'N/A'}</div>\`;

            if (result.issues && result.issues.length > 0) {
                html += '<h5>Issues Found:</h5>';
                result.issues.forEach(issue => {
                    const severityClass = issue.severity || 'info';
                    html += \`
                        <div class="analysis-item">
                            <div class="analysis-title">{{issue.title || 'Issue'}</div>
                            <div class="analysis-meta">
                                <span><span class="badge {{severityClass}">{{issue.severity || 'info'}</span></span>
                                <span>Line: {{issue.line || 'N/A'}</span>
                                <span>Type: {{issue.type || 'unknown'}</span>
                            </div>
                            <div>{{issue.description || 'No description'}</div>
                            {{issue.suggestion ? \`<div><strong>Suggestion:</strong> {{issue.suggestion}</div>\` : ''}
                        </div>
                    \`;
                });
            } else {
                html += '<div>No issues found in the analysis.</div>';
            }

            html += '</div>';
            document.getElementById(containerId).innerHTML = html;
        }

        function renderSecurityResult(data) {
            const result = data.result || {};

            let html = '<div class="analysis-result">';
            html += '<h4>Security Scan Results</h4>';
            html += \`<div><strong>Scan ID:</strong> {{data.scan_id || 'N/A'}</div>\`;

            if (result.vulnerabilities && result.vulnerabilities.length > 0) {
                html += '<h5>Security Vulnerabilities Found:</h5>';
                result.vulnerabilities.forEach(vuln => {
                    const severityClass = vuln.severity || 'high';
                    html += \`
                        <div class="security-result">
                            <div class="analysis-title">{{vuln.title || 'Vulnerability'}</div>
                            <div class="analysis-meta">
                                <span><span class="badge security {{severityClass}">{{vuln.severity || 'high'}</span></span>
                                <span>CWE: {{vuln.cwe || 'N/A'}</span>
                                <span>Confidence: {{vuln.confidence || 'N/A'}</span>
                            </div>
                            <div>{{vuln.description || 'No description'}</div>
                            {{vuln.impact ? \`<div><strong>Impact:</strong> {{vuln.impact}</div>\` : ''}
                            {{vuln.recommendation ? \`<div><strong>Recommendation:</strong> {{vuln.recommendation}</div>\` : ''}
                        </div>
                    \`;
                });
            } else {
                html += '<div>No security vulnerabilities found.</div>';
            }

            html += '</div>';
            document.getElementById('security-scan-result').innerHTML = html;
        }

        function renderStyleResult(data) {
            const result = data.result || {};

            let html = '<div class="analysis-result">';
            html += '<h4>Style Check Results</h4>';
            html += \`<div><strong>Check ID:</strong> {{data.check_id || 'N/A'}</div>\`;
            html += \`<div><strong>Style:</strong> {{data.style || 'Unknown'}</div>\`;

            if (result.violations && result.violations.length > 0) {
                html += '<h5>Style Violations:</h5>';
                result.violations.forEach(violation => {
                    html += \`
                        <div class="analysis-item">
                            <div class="analysis-title">{{violation.rule || 'Rule Violation'}</div>
                            <div class="analysis-meta">
                                <span>Line: {{violation.line || 'N/A'}</span>
                                <span>Column: {{violation.column || 'N/A'}</span>
                            </div>
                            <div>{{violation.message || 'No message'}</div>
                            {{violation.fix ? \`<div><strong>Suggested Fix:</strong> {{violation.fix}</div>\` : ''}
                        </div>
                    \`;
                });
            } else {
                html += '<div>Code follows style guidelines.</div>';
            }

            html += '</div>';
            document.getElementById('style-check-result').innerHTML = html;
        }

        async function loadStyleExamples() {
            document.getElementById('style-examples').innerHTML = 'Loading style examples...';
            document.getElementById('style-examples').style.display = 'block';

            try {
                const response = await fetch('/api/code-analyzer/style-examples');
                const data = await response.json();

                if (data.success) {
                    renderStyleExamples(data.data);
                } else {
                    document.getElementById('style-examples').innerHTML =
                        '<div class="error">Failed to load style examples: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('style-examples').innerHTML =
                    '<div class="error">Failed to load style examples: ' + error.message + '</div>';
            }
        }

        function renderStyleExamples(data) {
            const examples = data.examples || {};

            let html = '';

            Object.entries(examples).forEach(([language, styles]) => {
                html += \`<h4>{{language.charAt(0).toUpperCase() + language.slice(1)} Style Examples</h4>\`;

                Object.entries(styles).forEach(([styleName, example]) => {
                    html += \`
                        <div class="code-example">
                            <div class="code-language">{{styleName} Style</div>
                            <div class="code-content">{{example}</div>
                        </div>
                    \`;
                });
            });

            document.getElementById('style-examples').innerHTML = html;
        }

        async function loadAnalysisHistory() {
            document.getElementById('history-container').innerHTML = 'Loading analysis history...';

            try {
                const response = await fetch('/api/code-analyzer/history');
                const data = await response.json();

                if (data.success) {
                    renderAnalysisHistory(data.data);
                } else {
                    document.getElementById('history-container').innerHTML =
                        '<div class="error">Failed to load history: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('history-container').innerHTML =
                    '<div class="error">Failed to load history: ' + error.message + '</div>';
            }
        }

        function renderAnalysisHistory(data) {
            const history = data.history || [];

            if (history.length === 0) {
                document.getElementById('history-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No analysis history available</div>';
                return;
            }

            let html = '<table class="data-table"><thead><tr>';
            html += '<th>Analysis ID</th><th>Type</th><th>Timestamp</th><th>Result</th><th>Actions</th>';
            html += '</tr></thead><tbody>';

            history.forEach(analysis => {
                const timestamp = analysis.timestamp ? new Date(analysis.timestamp).toLocaleString() : 'Unknown';
                const hasIssues = analysis.result?.issues?.length > 0;
                const resultText = hasIssues ? \`{{analysis.result.issues.length} issues\` : 'Clean';

                html += \`
                    <tr>
                        <td>{{analysis.id}</td>
                        <td><span class="badge analysis">{{analysis.type || 'unknown'}</span></td>
                        <td>{{timestamp}</td>
                        <td>{{resultText}</td>
                        <td><button class="btn" onclick="viewAnalysis('{{analysis.id}')">View</button></td>
                    </tr>
                \`;
            });

            html += '</tbody></table>';
            document.getElementById('history-container').innerHTML = html;
        }

        function viewAnalysis(analysisId) {
            // Could implement modal to show full analysis details
            alert(\`Analysis details for ID: {{analysisId}\\n\\nFeature not yet implemented.\`);
        }

        // Tab switching
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }

        // Form event listeners
        document.getElementById('text-analysis-form').addEventListener('submit', analyzeText);
        document.getElementById('files-analysis-form').addEventListener('submit', analyzeFiles);
        document.getElementById('security-scan-form').addEventListener('submit', runSecurityScan);
        document.getElementById('style-check-form').addEventListener('submit', runStyleCheck);

        // Load initial data
        loadSummary();
    </script>
</body>
</html>
"""
            return create_html_response(html, "Code Analyzer Dashboard")
        except Exception as e:
            return handle_frontend_error("render code analyzer dashboard", e, **build_frontend_context("render_code_analyzer_dashboard"))
