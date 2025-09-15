"""Secure Analyzer UI handlers for Frontend service.

Handles secure analyzer service visualization, including content detection,
policy enforcement, and secure summarization monitoring.
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
from ..secure_analyzer_monitor import secure_analyzer_monitor


class SecureAnalyzerUIHandlers:
    """Handles secure analyzer UI rendering."""

    @staticmethod
    def handle_secure_analyzer_dashboard() -> HTMLResponse:
        """Render secure analyzer service monitoring dashboard."""
        try:
            clients = get_frontend_clients()

            # Get secure analyzer status and cached data
            status_data = secure_analyzer_monitor.get_secure_status()
            detection_history = secure_analyzer_monitor.get_detection_history(limit=20)
            suggestion_history = secure_analyzer_monitor.get_suggestion_history(limit=20)
            summary_history = secure_analyzer_monitor.get_summary_history(limit=20)

            # Build context for template
            context = {
                "health": status_data.get("health", {}),
                "analysis_stats": status_data.get("analysis_stats", {}),
                "recent_detections": detection_history,
                "recent_suggestions": suggestion_history,
                "recent_summaries": summary_history,
                "last_updated": status_data.get("last_updated", "Never")
            }

            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Analyzer Dashboard - LLM Documentation Ecosystem</title>
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
        .status-card.circuit-open {
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
        .btn.success {
            background: #28a745;
        }
        .btn.success:hover {
            background: #1e7e34;
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
        .detection-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .detection-item.sensitive {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .detection-item.safe {
            border-left-color: #28a745;
            background: #f8fff8;
        }
        .detection-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .detection-content {
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
        .suggestion-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .suggestion-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .suggestion-models {
            margin: 10px 0;
        }
        .suggestion-text {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-style: italic;
        }
        .summary-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .summary-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .summary-content {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
            max-height: 120px;
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
        .badge.sensitive {
            background: #dc3545;
        }
        .badge.safe {
            background: #28a745;
        }
        .badge.pii {
            background: #e83e8c;
        }
        .badge.secrets {
            background: #fd7e14;
        }
        .badge.credentials {
            background: #20c997;
        }
        .badge.bedrock {
            background: #6c757d;
        }
        .badge.ollama {
            background: #17a2b8;
        }
        .badge.openai {
            background: #28a745;
        }
        .badge.anthropic {
            background: #dc3545;
        }
        .badge.grok {
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
        .form-row.checkbox-row {
            display: flex;
            align-items: center;
            gap: 10px;
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
        .success {
            color: #28a745;
            background: #d4edda;
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
        .security-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .security-indicator.safe {
            background: #28a745;
        }
        .security-indicator.sensitive {
            background: #dc3545;
        }
        .security-indicator.unknown {
            background: #ffc107;
        }
        .confidence-bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            margin: 5px 0;
            overflow: hidden;
        }
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%);
            border-radius: 4px;
        }
        .tab-container {
            margin: 20px 0;
        }
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab-btn {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .tab-btn.active {
            background: #17a2b8;
            color: white;
            border-color: #17a2b8;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .model-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0;
        }
        .model-tag {
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
            <h1>Secure Analyzer Dashboard</h1>
            <p>Monitor content security analysis, policy enforcement, and secure summarization</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="refreshStatus()">Refresh Status</button>
            <button class="btn secondary" onclick="loadHistory()">Load Full History</button>
        </div>

        <div id="status-container">
            <!-- Status will be loaded here -->
        </div>

        <div class="tab-container">
            <div class="tab-buttons">
                <button class="tab-btn active" onclick="showTab('detect')">Content Detection</button>
                <button class="tab-btn" onclick="showTab('suggest')">Model Suggestions</button>
                <button class="tab-btn" onclick="showTab('summarize')">Secure Summaries</button>
            </div>

            <div id="detect-tab" class="tab-content active">
                <div class="test-section">
                    <h3>Detect Sensitive Content</h3>
                    <form class="test-form" onsubmit="detectContent(event)">
                        <div class="form-group">
                            <label for="detect-content">Content to Analyze:</label>
                            <textarea id="detect-content" placeholder="Enter text to check for sensitive information (PII, secrets, credentials)...">This document contains user email: john.doe@example.com and API key: sk-1234567890abcdef</textarea>
                        </div>
                        <div class="form-group">
                            <label for="detect-keywords">Additional Keywords (comma-separated, optional):</label>
                            <input type="text" id="detect-keywords" placeholder="secret, internal, confidential">
                        </div>
                        <div class="form-group">
                            <label for="detect-keyword-doc">Keyword Document URL (optional):</label>
                            <input type="text" id="detect-keyword-doc" placeholder="https://example.com/keywords.txt">
                        </div>
                        <button type="submit" class="btn">Detect Sensitive Content</button>
                    </form>
                    <div id="detection-result" style="margin-top: 20px;"></div>
                </div>

                <div id="detections-container">
                    <!-- Recent detections will be loaded here -->
                </div>
            </div>

            <div id="suggest-tab" class="tab-content">
                <div class="test-section">
                    <h3>Get Model Suggestions</h3>
                    <form class="test-form" onsubmit="suggestModels(event)">
                        <div class="form-group">
                            <label for="suggest-content">Content to Analyze:</label>
                            <textarea id="suggest-content" placeholder="Enter text to get AI model recommendations based on security analysis...">This report contains sensitive customer data including PII and confidential business information.</textarea>
                        </div>
                        <div class="form-group">
                            <label for="suggest-keywords">Additional Keywords (comma-separated, optional):</label>
                            <input type="text" id="suggest-keywords" placeholder="confidential, proprietary, pii">
                        </div>
                        <div class="form-group">
                            <label for="suggest-keyword-doc">Keyword Document URL (optional):</label>
                            <input type="text" id="suggest-keyword-doc" placeholder="https://example.com/keywords.txt">
                        </div>
                        <button type="submit" class="btn">Get Model Suggestions</button>
                    </form>
                    <div id="suggestion-result" style="margin-top: 20px;"></div>
                </div>

                <div id="suggestions-container">
                    <!-- Recent suggestions will be loaded here -->
                </div>
            </div>

            <div id="summarize-tab" class="tab-content">
                <div class="test-section">
                    <h3>Generate Secure Summary</h3>
                    <form class="test-form" onsubmit="secureSummarize(event)">
                        <div class="form-group">
                            <label for="summarize-content">Content to Summarize:</label>
                            <textarea id="summarize-content" placeholder="Enter text to generate a secure, policy-compliant summary...">This document contains sensitive information including customer PII, API keys, and proprietary business data that should only be processed by secure AI models.</textarea>
                        </div>
                        <div class="form-row checkbox-row">
                            <div class="checkbox-group">
                                <input type="checkbox" id="override-policy">
                                <label for="override-policy">Override Policy</label>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="summarize-keywords">Additional Keywords (comma-separated, optional):</label>
                            <input type="text" id="summarize-keywords" placeholder="sensitive, confidential, pii">
                        </div>
                        <div class="form-group">
                            <label for="summarize-prompt">Custom Prompt (optional):</label>
                            <textarea id="summarize-prompt" placeholder="Custom summarization prompt...">Focus on security risks and sensitive information in this content.</textarea>
                        </div>
                        <button type="submit" class="btn">Generate Secure Summary</button>
                    </form>
                    <div id="summary-result" style="margin-top: 20px;"></div>
                </div>

                <div id="summaries-container">
                    <!-- Recent summaries will be loaded here -->
                </div>
            </div>
        </div>
    </div>

    <script>
        let secureData = {
            status: {},
            detections: [],
            suggestions: [],
            summaries: [],
            analysis_stats: {},
            last_updated: null
        };

        async function loadSecureStatus() {
            try {
                const response = await fetch('/api/secure-analyzer/status');
                const data = await response.json();

                if (data.success) {
                    secureData = data.data;
                    renderSecureStatus();
                    renderRecentDetections();
                    renderRecentSuggestions();
                    renderRecentSummaries();
                } else {
                    document.getElementById('status-container').innerHTML =
                        '<div class="error">Failed to load secure analyzer status: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Failed to load secure analyzer status: ' + error.message + '</div>';
            }
        }

        function renderSecureStatus() {
            const health = secureData.status || {};
            const stats = secureData.analysis_stats || {};

            let html = '<div class="status-grid">';

            // Service health and circuit breaker
            const circuitOpen = health.circuit_breaker_open;
            const statusClass = circuitOpen ? 'circuit-open' : 'healthy';

            html += `
                <div class="status-card ${statusClass}">
                    <div class="status-label">Service Status</div>
                    <div class="status-value">${health.status || 'Unknown'}</div>
                    <div>Secure Analyzer</div>
                </div>
                <div class="status-card ${circuitOpen ? 'warning' : 'healthy'}">
                    <div class="status-label">Circuit Breaker</div>
                    <div class="status-value">${circuitOpen ? 'OPEN' : 'CLOSED'}</div>
                    <div>Fault Protection</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Total Detections</div>
                    <div class="status-value">${stats.total_detections || 0}</div>
                    <div>Content Analyzed</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Sensitive Content</div>
                    <div class="status-value">${stats.sensitive_content_detected || 0}</div>
                    <div>Security Risks Found</div>
                </div>
            `;

            html += '</div>';

            // Additional statistics
            if (stats.total_detections > 0) {
                html += '<h4>Analysis Statistics</h4><div class="metric-grid">';

                html += `
                    <div class="metric-item">
                        <div class="metric-label">Detection Rate</div>
                        <div class="metric-value">${stats.detection_accuracy || 0}%</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Model Suggestions</div>
                        <div class="metric-value">${stats.total_suggestions || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Secure Summaries</div>
                        <div class="metric-value">${stats.total_summaries || 0}</div>
                    </div>
                `;

                html += '</div>';
            }

            document.getElementById('status-container').innerHTML = html;
        }

        function renderRecentDetections() {
            const detections = secureData.detections || [];

            if (detections.length === 0) {
                document.getElementById('detections-container').innerHTML = '';
                return;
            }

            let html = '<h4>Recent Content Detections</h4>';

            detections.forEach(detection => {
                const timestamp = new Date(detection.timestamp).toLocaleString();
                const sensitive = detection.sensitive;
                const matches = detection.matches || [];
                const topics = detection.topics || [];

                html += `
                    <div class="detection-item ${sensitive ? 'sensitive' : 'safe'}">
                        <div class="detection-meta">
                            <span><strong>ID:</strong> ${detection.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span><strong>Length:</strong> ${detection.content_length} chars</span>
                            <span>
                                <span class="security-indicator ${sensitive ? 'sensitive' : 'safe'}"></span>
                                ${sensitive ? 'SENSITIVE' : 'SAFE'}
                            </span>
                        </div>
                        <div class="detection-content">${detection.content_preview || 'Content preview not available'}</div>
                        ${matches.length > 0 ? `
                            <div style="margin-top: 8px;">
                                <strong>Matches:</strong> ${matches.map(match => `<span class="badge">${match}</span>`).join('')}
                            </div>
                        ` : ''}
                        ${topics.length > 0 ? `
                            <div style="margin-top: 8px;">
                                <strong>Topics:</strong> ${topics.map(topic => `<span class="badge ${topic.toLowerCase()}">${topic}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('detections-container').innerHTML = html;
        }

        function renderRecentSuggestions() {
            const suggestions = secureData.suggestions || [];

            if (suggestions.length === 0) {
                document.getElementById('suggestions-container').innerHTML = '';
                return;
            }

            let html = '<h4>Recent Model Suggestions</h4>';

            suggestions.forEach(suggestion => {
                const timestamp = new Date(suggestion.timestamp).toLocaleString();
                const sensitive = suggestion.sensitive;
                const models = suggestion.allowed_models || [];

                html += `
                    <div class="suggestion-item">
                        <div class="suggestion-meta">
                            <span><strong>ID:</strong> ${suggestion.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span><strong>Length:</strong> ${suggestion.content_length} chars</span>
                            <span>
                                <span class="security-indicator ${sensitive ? 'sensitive' : 'safe'}"></span>
                                ${sensitive ? 'RESTRICTED' : 'OPEN'}
                            </span>
                        </div>
                        <div class="suggestion-models">
                            <strong>Allowed Models:</strong>
                            <div class="model-list">
                                ${models.map(model => `<span class="model-tag">${model}</span>`).join('')}
                            </div>
                        </div>
                        ${suggestion.suggestion ? `
                            <div class="suggestion-text">${suggestion.suggestion}</div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('suggestions-container').innerHTML = html;
        }

        function renderRecentSummaries() {
            const summaries = secureData.summaries || [];

            if (summaries.length === 0) {
                document.getElementById('summaries-container').innerHTML = '';
                return;
            }

            let html = '<h4>Recent Secure Summaries</h4>';

            summaries.forEach(summary => {
                const timestamp = new Date(summary.timestamp).toLocaleString();
                const confidence = summary.confidence || 0;
                const provider = summary.provider_used || 'unknown';
                const policyEnforced = summary.policy_enforced;

                html += `
                    <div class="summary-item">
                        <div class="summary-meta">
                            <span><strong>ID:</strong> ${summary.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span><strong>Provider:</strong> <span class="badge ${provider.toLowerCase()}">${provider}</span></span>
                            <span><strong>Policy:</strong> ${policyEnforced ? 'ENFORCED' : 'OVERRIDDEN'}</span>
                        </div>
                        <div style="margin: 10px 0;">
                            <strong>Confidence:</strong> ${confidence.toFixed(2)}
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${confidence * 100}%;"></div>
                            </div>
                        </div>
                        <div class="summary-content">${summary.summary_preview || 'Summary preview not available'}</div>
                        ${summary.topics_detected && summary.topics_detected.length > 0 ? `
                            <div style="margin-top: 8px;">
                                <strong>Topics Detected:</strong> ${summary.topics_detected.map(topic => `<span class="badge ${topic.toLowerCase()}">${topic}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('summaries-container').innerHTML = html;
        }

        async function detectContent(event) {
            event.preventDefault();

            const content = document.getElementById('detect-content').value;
            const keywordsText = document.getElementById('detect-keywords').value;
            const keywordDoc = document.getElementById('detect-keyword-doc').value;

            if (!content) {
                alert('Please enter content to analyze');
                return;
            }

            const keywords = keywordsText ? keywordsText.split(',').map(k => k.trim()).filter(k => k) : [];

            const resultDiv = document.getElementById('detection-result');
            resultDiv.innerHTML = '<div style="color: #666;">Analyzing content for sensitive information...</div>';

            try {
                const payload = {
                    content: content,
                    keywords: keywords,
                    keyword_document: keywordDoc || undefined
                };

                const response = await fetch('/api/secure-analyzer/detect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    const sensitive = data.sensitive;
                    const matches = data.matches || [];
                    const topics = data.topics || [];

                    resultDiv.innerHTML = `
                        <div class="${sensitive ? 'error' : 'success'}">
                            <strong>Analysis Result:</strong>
                            <span class="security-indicator ${sensitive ? 'sensitive' : 'safe'}"></span>
                            ${sensitive ? 'SENSITIVE CONTENT DETECTED' : 'CONTENT APPEARS SAFE'}
                        </div>
                        <div><strong>Detection ID:</strong> ${data.detection_id}</div>
                        ${matches.length > 0 ? `
                            <div><strong>Matches Found:</strong> ${matches.map(match => `<span class="badge">${match}</span>`).join('')}</div>
                        ` : ''}
                        ${topics.length > 0 ? `
                            <div><strong>Security Topics:</strong> ${topics.map(topic => `<span class="badge ${topic.toLowerCase()}">${topic}</span>`).join('')}</div>
                        ` : ''}
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="error">✗ Detection failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new detection
                loadSecureStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div class="error">✗ Error: ${error.message}</div>`;
            }
        }

        async function suggestModels(event) {
            event.preventDefault();

            const content = document.getElementById('suggest-content').value;
            const keywordsText = document.getElementById('suggest-keywords').value;
            const keywordDoc = document.getElementById('suggest-keyword-doc').value;

            if (!content) {
                alert('Please enter content to analyze');
                return;
            }

            const keywords = keywordsText ? keywordsText.split(',').map(k => k.trim()).filter(k => k) : [];

            const resultDiv = document.getElementById('suggestion-result');
            resultDiv.innerHTML = '<div style="color: #666;">Analyzing content and generating model suggestions...</div>';

            try {
                const payload = {
                    content: content,
                    keywords: keywords,
                    keyword_document: keywordDoc || undefined
                };

                const response = await fetch('/api/secure-analyzer/suggest', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    const sensitive = data.sensitive;
                    const models = data.allowed_models || [];

                    resultDiv.innerHTML = `
                        <div class="${sensitive ? 'error' : 'success'}">
                            <strong>Content Analysis:</strong>
                            <span class="security-indicator ${sensitive ? 'sensitive' : 'safe'}"></span>
                            ${sensitive ? 'SENSITIVE - RESTRICTED MODELS' : 'SAFE - ALL MODELS ALLOWED'}
                        </div>
                        <div><strong>Suggestion ID:</strong> ${data.suggestion_id}</div>
                        <div><strong>Allowed Models:</strong></div>
                        <div class="model-list">
                            ${models.map(model => `<span class="model-tag">${model}</span>`).join('')}
                        </div>
                        ${data.suggestion ? `<div class="suggestion-text">${data.suggestion}</div>` : ''}
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="error">✗ Suggestion failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new suggestion
                loadSecureStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div class="error">✗ Error: ${error.message}</div>`;
            }
        }

        async function secureSummarize(event) {
            event.preventDefault();

            const content = document.getElementById('summarize-content').value;
            const overridePolicy = document.getElementById('override-policy').checked;
            const keywordsText = document.getElementById('summarize-keywords').value;
            const prompt = document.getElementById('summarize-prompt').value;

            if (!content) {
                alert('Please enter content to summarize');
                return;
            }

            const keywords = keywordsText ? keywordsText.split(',').map(k => k.trim()).filter(k => k) : [];

            const resultDiv = document.getElementById('summary-result');
            resultDiv.innerHTML = '<div style="color: #666;">Generating secure summary with policy enforcement...</div>';

            try {
                const payload = {
                    content: content,
                    override_policy: overridePolicy,
                    keywords: keywords,
                    prompt: prompt || undefined
                };

                const response = await fetch('/api/secure-analyzer/summarize', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    const provider = data.provider_used || 'unknown';
                    const confidence = data.confidence || 0;
                    const policyEnforced = data.policy_enforced;

                    resultDiv.innerHTML = `
                        <div class="success">
                            <strong>✓ Secure Summary Generated</strong>
                        </div>
                        <div><strong>Summary ID:</strong> ${data.summary_id}</div>
                        <div><strong>Provider Used:</strong> <span class="badge ${provider.toLowerCase()}">${provider}</span></div>
                        <div><strong>Policy Enforced:</strong> ${policyEnforced ? 'YES' : 'NO (OVERRIDDEN)'}</div>
                        <div style="margin: 10px 0;">
                            <strong>Confidence:</strong> ${confidence.toFixed(2)}
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${confidence * 100}%;"></div>
                            </div>
                        </div>
                        <div class="summary-content">${data.summary}</div>
                        ${data.topics_detected && data.topics_detected.length > 0 ? `
                            <div style="margin-top: 8px;">
                                <strong>Topics Detected:</strong> ${data.topics_detected.map(topic => `<span class="badge ${topic.toLowerCase()}">${topic}</span>`).join('')}
                            </div>
                        ` : ''}
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="error">✗ Summary generation failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new summary
                loadSecureStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div class="error">✗ Error: ${error.message}</div>`;
            }
        }

        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }

        async function loadHistory() {
            try {
                const [detectResponse, suggestResponse, summaryResponse] = await Promise.all([
                    fetch('/api/secure-analyzer/detections?limit=50'),
                    fetch('/api/secure-analyzer/suggestions?limit=50'),
                    fetch('/api/secure-analyzer/summaries?limit=50')
                ]);

                const detectData = await detectResponse.json();
                const suggestData = await suggestResponse.json();
                const summaryData = await summaryResponse.json();

                if (detectData.success) {
                    secureData.detections = detectData.data;
                    renderRecentDetections();
                }

                if (suggestData.success) {
                    secureData.suggestions = suggestData.data;
                    renderRecentSuggestions();
                }

                if (summaryData.success) {
                    secureData.summaries = summaryData.data;
                    renderRecentSummaries();
                }

            } catch (error) {
                alert('Failed to load full history: ' + error.message);
            }
        }

        function refreshStatus() {
            loadSecureStatus();
        }

        // Load initial data
        loadSecureStatus();
    </script>
</body>
</html>
"""
            return create_html_response(html, "Secure Analyzer Dashboard")
        except Exception as e:
            return handle_frontend_error("render secure analyzer dashboard", e, **build_frontend_context("render_secure_analyzer_dashboard"))
