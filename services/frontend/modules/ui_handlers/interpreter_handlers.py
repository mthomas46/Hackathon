"""Interpreter UI handlers for Frontend service.

Handles interpreter service visualization, including natural language
query interpretation, intent recognition, and workflow execution.
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
from ..interpreter_monitor import interpreter_monitor


class InterpreterUIHandlers:
    """Handles interpreter UI rendering."""

    @staticmethod
    def handle_interpreter_dashboard() -> HTMLResponse:
        """Render interpreter service monitoring dashboard."""
        try:
            clients = get_frontend_clients()

            # Get interpreter status and cached data
            status_data = interpreter_monitor.get_interpreter_status()
            interpretation_history = interpreter_monitor.get_interpretation_history(limit=20)
            execution_history = interpreter_monitor.get_execution_history(limit=20)

            # Build context for template
            context = {
                "health": status_data.get("health", {}),
                "intents": status_data.get("intents", []),
                "interpretation_stats": status_data.get("interpretation_stats", {}),
                "execution_stats": status_data.get("execution_stats", {}),
                "recent_interpretations": interpretation_history,
                "recent_executions": execution_history,
                "last_updated": status_data.get("last_updated", "Never")
            }

            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interpreter Dashboard - LLM Documentation Ecosystem</title>
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
        .interpretation-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .interpretation-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .interpretation-query {
            font-weight: 500;
            margin: 10px 0;
            color: #495057;
        }
        .interpretation-intent {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
        }
        .interpretation-workflow {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
            max-height: 150px;
            overflow-y: auto;
        }
        .execution-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #28a745;
        }
        .execution-item.failed {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .execution-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        .execution-query {
            font-weight: 500;
            margin: 10px 0;
            color: #495057;
        }
        .execution-results {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 12px;
            max-height: 200px;
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
        .badge.success {
            background: #28a745;
        }
        .badge.failed {
            background: #dc3545;
        }
        .badge.high {
            background: #28a745;
        }
        .badge.medium {
            background: #ffc107;
            color: black;
        }
        .badge.low {
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
        .intents-section {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .intent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        .intent-item {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
        }
        .intent-name {
            font-weight: bold;
            color: #495057;
            margin-bottom: 8px;
        }
        .intent-description {
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
        }
        .intent-examples {
            font-size: 12px;
            color: #666;
            margin-top: 8px;
        }
        .intent-examples ul {
            margin: 5px 0;
            padding-left: 20px;
        }
        .confidence-bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin: 5px 0;
        }
        .confidence-fill {
            height: 100%;
            background: #17a2b8;
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Interpreter Dashboard</h1>
            <p>Monitor natural language processing and workflow generation</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="refreshStatus()">Refresh Status</button>
            <button class="btn secondary" onclick="loadIntents()">Load Supported Intents</button>
            <button class="btn success" onclick="loadHistory()">Load Full History</button>
        </div>

        <div id="status-container">
            <!-- Status will be loaded here -->
        </div>

        <div id="intents-container" class="intents-section" style="display: none;">
            <h3>Supported Intents</h3>
            <div id="intents-grid" class="intent-grid">
                <!-- Intents will be loaded here -->
            </div>
        </div>

        <div class="test-section">
            <h3>Test Query Interpretation</h3>
            <form class="test-form" onsubmit="interpretQuery(event)">
                <div class="form-group">
                    <label for="test-query">Natural Language Query:</label>
                    <textarea id="test-query" placeholder="e.g., analyze this document for security issues">analyze this document for security issues</textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="session-id">Session ID (optional):</label>
                        <input type="text" id="session-id" placeholder="session_123">
                    </div>
                    <div class="form-group">
                        <label for="user-id">User ID (optional):</label>
                        <input type="text" id="user-id" placeholder="user_456">
                    </div>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" id="execute-workflow">
                    <label for="execute-workflow">Execute workflow after interpretation</label>
                </div>
                <button type="submit" class="btn">Interpret Query</button>
            </form>
            <div id="interpretation-result" style="margin-top: 20px;"></div>
        </div>

        <div id="interpretations-container">
            <!-- Recent interpretations will be loaded here -->
        </div>

        <div id="executions-container">
            <!-- Recent executions will be loaded here -->
        </div>
    </div>

    <script>
        let interpreterData = {
            status: {},
            intents: [],
            interpretations: [],
            executions: [],
            interpretation_stats: {},
            execution_stats: {}
        };

        async function loadInterpreterStatus() {
            try {
                const response = await fetch('/api/interpreter/status');
                const data = await response.json();

                if (data.success) {
                    interpreterData = data.data;
                    renderInterpreterStatus();
                    renderRecentInterpretations();
                    renderRecentExecutions();
                } else {
                    document.getElementById('status-container').innerHTML =
                        '<div class="error">Failed to load interpreter status: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Failed to load interpreter status: ' + error.message + '</div>';
            }
        }

        function renderInterpreterStatus() {
            const health = interpreterData.status || {};
            const interpStats = interpreterData.interpretation_stats || {};
            const execStats = interpreterData.execution_stats || {};

            let html = '<div class="status-grid">';

            // Service health
            const isHealthy = health.status === 'healthy';
            html += `
                <div class="status-card ${isHealthy ? 'healthy' : 'unhealthy'}">
                    <div class="status-label">Service Status</div>
                    <div class="status-value">${health.status || 'Unknown'}</div>
                    <div>Natural Language Processor</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Total Interpretations</div>
                    <div class="status-value">${interpStats.total_interpretations || 0}</div>
                    <div>All time</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Avg Confidence</div>
                    <div class="status-value">${interpStats.average_confidence || 0}%</div>
                    <div>Recognition accuracy</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Total Executions</div>
                    <div class="status-value">${execStats.total_executions || 0}</div>
                    <div>Workflow runs</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Execution Success</div>
                    <div class="status-value">${execStats.success_rate || 0}%</div>
                    <div>Workflow completion rate</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Avg Execution Time</div>
                    <div class="status-value">${execStats.average_execution_time || 0}s</div>
                    <div>Workflow duration</div>
                </div>
            `;

            html += '</div>';

            // Detailed metrics
            if (interpStats.total_interpretations > 0) {
                html += '<h4>Interpretation Statistics</h4><div class="metric-grid">';

                html += `
                    <div class="metric-item">
                        <div class="metric-label">Unique Intents</div>
                        <div class="metric-value">${interpStats.unique_intents || 0}</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Avg Steps/Workflow</div>
                        <div class="metric-value">${execStats.average_steps_completed || 0}</div>
                    </div>
                `;

                html += '</div>';

                // Intents detected
                if (interpStats.intents_detected && interpStats.intents_detected.length > 0) {
                    html += '<h4>Intents Detected</h4><div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;">';
                    interpStats.intents_detected.forEach(intent => {
                        html += `<span class="badge">${intent}</span>`;
                    });
                    html += '</div>';
                }
            }

            document.getElementById('status-container').innerHTML = html;
        }

        function renderRecentInterpretations() {
            const interpretations = interpreterData.interpretations || [];

            if (interpretations.length === 0) {
                document.getElementById('interpretations-container').innerHTML = '';
                return;
            }

            let html = '<h4>Recent Interpretations</h4>';

            interpretations.forEach(interp => {
                const timestamp = new Date(interp.timestamp).toLocaleString();
                const confidence = interp.confidence || 0;
                const intent = interp.intent || {};

                let confidenceClass = 'low';
                if (confidence >= 0.8) confidenceClass = 'high';
                else if (confidence >= 0.6) confidenceClass = 'medium';

                html += `
                    <div class="interpretation-item">
                        <div class="interpretation-meta">
                            <span><strong>ID:</strong> ${interp.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span class="badge ${confidenceClass}">Confidence: ${Math.round(confidence * 100)}%</span>
                        </div>
                        <div class="interpretation-query">${interp.query}</div>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${confidence * 100}%"></div>
                        </div>
                        ${intent.name ? `
                            <div class="interpretation-intent">${JSON.stringify(intent, null, 2)}</div>
                        ` : ''}
                        ${interp.workflow && Object.keys(interp.workflow).length > 0 ? `
                            <div class="interpretation-workflow">${JSON.stringify(interp.workflow, null, 2)}</div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('interpretations-container').innerHTML = html;
        }

        function renderRecentExecutions() {
            const executions = interpreterData.executions || [];

            if (executions.length === 0) {
                document.getElementById('executions-container').innerHTML = '';
                return;
            }

            let html = '<h4>Recent Workflow Executions</h4>';

            executions.forEach(exec => {
                const timestamp = new Date(exec.timestamp).toLocaleString();
                const success = exec.success;
                const executionTime = exec.execution_time || 0;
                const stepsCompleted = exec.steps_completed || 0;

                html += `
                    <div class="execution-item ${success ? '' : 'failed'}">
                        <div class="execution-meta">
                            <span><strong>ID:</strong> ${exec.id}</span>
                            <span><strong>Time:</strong> ${timestamp}</span>
                            <span class="badge ${success ? 'success' : 'failed'}">${success ? 'SUCCESS' : 'FAILED'}</span>
                            <span><strong>Steps:</strong> ${stepsCompleted}</span>
                            <span><strong>Duration:</strong> ${executionTime.toFixed(2)}s</span>
                        </div>
                        <div class="execution-query">${exec.query}</div>
                        ${exec.results ? `
                            <div class="execution-results">${JSON.stringify(exec.results, null, 2)}</div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('executions-container').innerHTML = html;
        }

        async function loadIntents() {
            try {
                const response = await fetch('/api/interpreter/intents');
                const data = await response.json();

                if (data.success) {
                    interpreterData.intents = data.data;
                    renderSupportedIntents();
                    document.getElementById('intents-container').style.display = 'block';
                } else {
                    alert('Failed to load intents: ' + data.message);
                }
            } catch (error) {
                alert('Failed to load intents: ' + error.message);
            }
        }

        function renderSupportedIntents() {
            const intents = interpreterData.intents || [];

            if (intents.length === 0) {
                document.getElementById('intents-grid').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px; grid-column: 1 / -1;">No intents available</div>';
                return;
            }

            let html = '';

            intents.forEach(intent => {
                const examples = intent.examples || [];
                html += `
                    <div class="intent-item">
                        <div class="intent-name">${intent.name}</div>
                        <div class="intent-description">${intent.description || 'No description available'}</div>
                        ${examples.length > 0 ? `
                            <div class="intent-examples">
                                <strong>Examples:</strong>
                                <ul>
                                    ${examples.slice(0, 3).map(example => `<li>${example}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                `;
            });

            document.getElementById('intents-grid').innerHTML = html;
        }

        async function interpretQuery(event) {
            event.preventDefault();

            const query = document.getElementById('test-query').value;
            const sessionId = document.getElementById('session-id').value;
            const userId = document.getElementById('user-id').value;
            const executeWorkflow = document.getElementById('execute-workflow').checked;

            if (!query.trim()) {
                alert('Please enter a query');
                return;
            }

            const resultDiv = document.getElementById('interpretation-result');
            resultDiv.innerHTML = '<div style="color: #666;">Processing query...</div>';

            try {
                const endpoint = executeWorkflow ? '/api/interpreter/execute' : '/api/interpreter/interpret';
                const payload = { query: query.trim() };

                if (sessionId.trim()) {
                    payload.session_id = sessionId.trim();
                }
                if (userId.trim()) {
                    payload.user_id = userId.trim();
                }

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.success) {
                    let resultHtml = `
                        <div style="color: #28a745; margin-bottom: 10px;">✓ Query ${executeWorkflow ? 'executed' : 'interpreted'} successfully!</div>
                    `;

                    if (data.intent) {
                        resultHtml += `
                            <div><strong>Intent:</strong> ${data.intent.name || 'Unknown'}</div>
                            <div><strong>Confidence:</strong> ${Math.round((data.confidence || 0) * 100)}%</div>
                            <div class="interpretation-intent">${JSON.stringify(data.intent, null, 2)}</div>
                        `;
                    }

                    if (data.workflow) {
                        resultHtml += `
                            <div><strong>Generated Workflow:</strong></div>
                            <div class="interpretation-workflow">${JSON.stringify(data.workflow, null, 2)}</div>
                        `;
                    }

                    if (data.results) {
                        resultHtml += `
                            <div><strong>Execution Results:</strong></div>
                            <div class="execution-results">${JSON.stringify(data.results, null, 2)}</div>
                        `;
                    }

                    resultDiv.innerHTML = resultHtml;
                } else {
                    resultDiv.innerHTML = `
                        <div style="color: #dc3545;">✗ Query processing failed: ${data.error || 'Unknown error'}</div>
                    `;
                }

                // Refresh status to show new interpretation/execution
                loadInterpreterStatus();

            } catch (error) {
                resultDiv.innerHTML = `<div style="color: #dc3545;">✗ Error: ${error.message}</div>`;
            }
        }

        async function loadHistory() {
            try {
                const [interpResponse, execResponse] = await Promise.all([
                    fetch('/api/interpreter/interpretations?limit=50'),
                    fetch('/api/interpreter/executions?limit=50')
                ]);

                const interpData = await interpResponse.json();
                const execData = await execResponse.json();

                if (interpData.success) {
                    interpreterData.interpretations = interpData.data;
                    renderRecentInterpretations();
                }

                if (execData.success) {
                    interpreterData.executions = execData.data;
                    renderRecentExecutions();
                }

            } catch (error) {
                alert('Failed to load full history: ' + error.message);
            }
        }

        function refreshStatus() {
            loadInterpreterStatus();
        }

        // Load initial data
        loadInterpreterStatus();
    </script>
</body>
</html>
"""
            return create_html_response(html, "Interpreter Dashboard")
        except Exception as e:
            return handle_frontend_error("render interpreter dashboard", e, **build_frontend_context("render_interpreter_dashboard"))
