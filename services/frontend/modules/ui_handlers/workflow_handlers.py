"""Workflow UI handlers for Frontend service.

Handles workflow and job status visualization.
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


class WorkflowUIHandlers:
    """Handles workflow and job status UI rendering."""

    @staticmethod
    def handle_workflows_status() -> HTMLResponse:
        """Render workflow and job status monitoring page."""
        try:
            clients = get_frontend_clients()

            # Get workflow and job status data
            workflow_data = fetch_service_data("orchestrator", "/api/workflows/jobs/status", clients=clients)
            active_jobs = workflow_data.get("active_jobs", [])
            workflow_stats = workflow_data.get("workflow_stats", {})
            recent_history = workflow_data.get("recent_history", [])

            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workflow & Job Status - LLM Documentation Ecosystem</title>
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
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #17a2b8;
        }
        .status-card.running {
            border-left-color: #ffc107;
            background: #fffbf0;
        }
        .status-card.completed {
            border-left-color: #28a745;
            background: #f8fff8;
        }
        .status-card.failed {
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
        .job-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #17a2b8;
        }
        .job-item.running {
            border-left-color: #ffc107;
            background: #fffbf0;
        }
        .job-item.completed {
            border-left-color: #28a745;
            background: #f8fff8;
        }
        .job-item.failed {
            border-left-color: #dc3545;
            background: #fff5f5;
        }
        .job-name {
            font-size: 1.1em;
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }
        .job-meta {
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
        }
        .job-progress {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }
        .job-progress-bar {
            height: 100%;
            background: #17a2b8;
            transition: width 0.3s ease;
        }
        .job-progress-bar.completed {
            background: #28a745;
        }
        .job-progress-bar.failed {
            background: #dc3545;
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
        .badge {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin: 2px 5px 2px 0;
        }
        .badge.running {
            background: #ffc107;
            color: black;
        }
        .badge.completed {
            background: #28a745;
        }
        .badge.failed {
            background: #dc3545;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Workflow & Job Status</h1>
            <p>Monitor active workflows and job execution across the ecosystem</p>
        </div>

        <div class="controls">
            <button class="btn" onclick="refreshStatus()">Refresh Status</button>
            <button class="btn secondary" onclick="loadHistory()">Load History</button>
        </div>

        <div id="status-container">
            <!-- Status will be loaded here -->
        </div>

        <div id="jobs-container">
            <!-- Active jobs will be loaded here -->
        </div>
    </div>

    <script>
        let workflowData = {active_jobs: [], workflow_stats: {}, recent_history: []};

        async function loadWorkflowStatus() {
            try {
                const response = await fetch('/api/workflows/jobs/status');
                const data = await response.json();

                if (data.success) {
                    workflowData = data.data;
                    renderWorkflowStatus();
                    renderActiveJobs();
                } else {
                    document.getElementById('status-container').innerHTML =
                        '<div class="error">Failed to load workflow status: ' + data.message + '</div>';
                }
            } catch (error) {
                document.getElementById('status-container').innerHTML =
                    '<div class="error">Failed to load workflow status: ' + error.message + '</div>';
            }
        }

        function renderWorkflowStatus() {
            const stats = workflowData.workflow_stats || {};

            let html = '<div class="status-grid">';

            // Overall statistics
            html += \`
                <div class="status-card">
                    <div class="status-label">Active Workflows</div>
                    <div class="status-value">{{workflowData.active_jobs?.length || 0}</div>
                    <div>Currently Running</div>
                </div>
                <div class="status-card completed">
                    <div class="status-label">Total Completed</div>
                    <div class="status-value">{{stats.total_completed || 0}</div>
                    <div>This Session</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Success Rate</div>
                    <div class="status-value">{{stats.success_rate ? stats.success_rate.toFixed(1) + '%' : 'N/A'}</div>
                    <div>Completion Rate</div>
                </div>
                <div class="status-card failed">
                    <div class="status-label">Failed Jobs</div>
                    <div class="status-value">{{stats.total_failed || 0}</div>
                    <div>Error Count</div>
                </div>
            \`;

            html += '</div>';

            // Detailed metrics
            if (Object.keys(stats).length > 0) {
                html += '<h4>Workflow Performance Metrics</h4><div class="metric-grid">';

                if (stats.average_execution_time) {
                    html += \`
                        <div class="metric-item">
                            <div class="metric-label">Avg Execution Time</div>
                            <div class="metric-value">{{stats.average_execution_time.toFixed(1)}s</div>
                        </div>
                    \`;
                }

                if (stats.longest_running) {
                    html += \`
                        <div class="metric-item">
                            <div class="metric-label">Longest Running</div>
                            <div class="metric-value">{{stats.longest_running}s</div>
                        </div>
                    \`;
                }

                if (stats.most_active_service) {
                    html += \`
                        <div class="metric-item">
                            <div class="metric-label">Most Active Service</div>
                            <div class="metric-value">{{stats.most_active_service}</div>
                        </div>
                    \`;
                }

                html += '</div>';
            }

            document.getElementById('status-container').innerHTML = html;
        }

        function renderActiveJobs() {
            const jobs = workflowData.active_jobs || [];

            if (jobs.length === 0) {
                document.getElementById('jobs-container').innerHTML =
                    '<div style="text-align: center; color: #666; padding: 40px;">No active jobs currently running</div>';
                return;
            }

            let html = '<h4>Active Jobs</h4>';

            jobs.forEach(job => {
                const status = job.status || 'running';
                const progress = job.progress || 0;
                const startTime = job.start_time ? new Date(job.start_time).toLocaleString() : 'Unknown';

                html += \`
                    <div class="job-item {{status}">
                        <div class="job-name">{{job.name || 'Unnamed Job'}</div>
                        <div class="job-meta">
                            <span><span class="badge {{status}">{{status.toUpperCase()}</span></span>
                            <span>Started: {{startTime}</span>
                            <span>Service: {{job.service || 'Unknown'}</span>
                            <span>ID: {{job.id || 'N/A'}</span>
                        </div>
                        <div class="job-progress">
                            <div class="job-progress-bar {{status}" style="width: {{progress}%"></div>
                        </div>
                        <div style="font-size: 12px; color: #666;">
                            Progress: {{progress}% | {{job.current_step || 'Processing...'}
                        </div>
                    </div>
                \`;
            });

            document.getElementById('jobs-container').innerHTML = html;
        }

        async function loadHistory() {
            try {
                const response = await fetch('/api/workflows/jobs/status?include_history=true');
                const data = await response.json();

                if (data.success) {
                    const history = data.data.recent_history || [];
                    renderJobHistory(history);
                }
            } catch (error) {
                alert('Failed to load job history: ' + error.message);
            }
        }

        function renderJobHistory(history) {
            if (!history || history.length === 0) {
                alert('No job history available');
                return;
            }

            let html = '<h4>Job History</h4><table class="data-table">';
            html += '<thead><tr><th>Job Name</th><th>Status</th><th>Start Time</th><th>Duration</th><th>Service</th></tr></thead><tbody>';

            history.forEach(job => {
                const startTime = job.start_time ? new Date(job.start_time).toLocaleString() : 'Unknown';
                const duration = job.duration ? job.duration + 's' : 'N/A';
                const statusClass = job.status === 'completed' ? 'completed' :
                                  job.status === 'failed' ? 'failed' : '';

                html += \`
                    <tr>
                        <td>{{job.name || 'Unnamed'}</td>
                        <td><span class="badge {{statusClass}">{{job.status || 'unknown'}</span></td>
                        <td>{{startTime}</td>
                        <td>{{duration}</td>
                        <td>{{job.service || 'Unknown'}</td>
                    </tr>
                \`;
            });

            html += '</tbody></table>';

            // Replace jobs container with history
            document.getElementById('jobs-container').innerHTML = html;
        }

        function refreshStatus() {
            loadWorkflowStatus();
        }

        // Load initial data
        loadWorkflowStatus();
    </script>
</body>
</html>
"""
            return create_html_response(html, "Workflow & Job Status")
        except Exception as e:
            return handle_frontend_error("render workflows status", e, **build_frontend_context("render_workflows_status"))