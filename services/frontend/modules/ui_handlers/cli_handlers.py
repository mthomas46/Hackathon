"""CLI Service UI handlers for Frontend service.

Handles terminal pass-through interface for CLI service operations,
providing a web-based terminal for full CLI functionality.
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
from ..cli_monitor import cli_monitor


class CLIUIHandlers:
    """Handles CLI UI rendering and terminal interface."""

    @staticmethod
    def handle_cli_terminal() -> HTMLResponse:
        """Render CLI terminal interface."""
        try:
            clients = get_frontend_clients()

            # Get available commands for the interface
            commands_info = cli_monitor.get_available_commands()

            # Build context for template
            context = {
                "commands": commands_info.get("commands", []),
                "interactive_menus": commands_info.get("interactive_menus", [])
            }

            html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLI Terminal - LLM Documentation Ecosystem</title>
    <style>
        body {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
            margin: 0;
            padding: 0;
            background-color: #1e1e1e;
            color: #f8f8f2;
            height: 100vh;
            overflow: hidden;
        }
        .container {
            display: flex;
            height: 100vh;
        }
        .sidebar {
            width: 300px;
            background-color: #2d2d2d;
            border-right: 1px solid #404040;
            padding: 20px;
            overflow-y: auto;
        }
        .terminal {
            flex: 1;
            display: flex;
            flex-direction: column;
            background-color: #1e1e1e;
        }
        .terminal-header {
            background-color: #2d2d2d;
            padding: 10px 20px;
            border-bottom: 1px solid #404040;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .terminal-output {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background-color: #1e1e1e;
            font-size: 14px;
            line-height: 1.4;
        }
        .terminal-input-area {
            background-color: #2d2d2d;
            border-top: 1px solid #404040;
            padding: 15px 20px;
        }
        .command-input {
            width: 100%;
            background-color: #1e1e1e;
            border: 1px solid #404040;
            color: #f8f8f2;
            padding: 10px 15px;
            font-family: inherit;
            font-size: 14px;
            border-radius: 4px;
        }
        .command-input:focus {
            outline: none;
            border-color: #007acc;
        }
        .btn {
            background: #007acc;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin: 5px;
        }
        .btn:hover {
            background: #005999;
        }
        .btn.secondary {
            background: #6c757d;
        }
        .btn.secondary:hover {
            background: #545b62;
        }
        .btn.danger {
            background: #dc3545;
        }
        .btn.danger:hover {
            background: #c82333;
        }
        .sidebar-section {
            margin-bottom: 25px;
        }
        .sidebar-title {
            color: #007acc;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 16px;
        }
        .command-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .command-item {
            background: #3c3c3c;
            margin: 5px 0;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .command-item:hover {
            background: #4c4c4c;
        }
        .command-name {
            font-weight: bold;
            color: #007acc;
        }
        .command-desc {
            font-size: 12px;
            color: #cccccc;
            margin-top: 4px;
        }
        .command-usage {
            font-size: 11px;
            color: #888888;
            font-style: italic;
            margin-top: 2px;
        }
        .menu-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .menu-item {
            background: #3c3c3c;
            margin: 3px 0;
            padding: 6px 10px;
            border-radius: 3px;
            font-size: 13px;
            color: #f8f8f2;
        }
        .output-line {
            margin: 2px 0;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .output-line.command {
            color: #007acc;
            font-weight: bold;
        }
        .output-line.success {
            color: #28a745;
        }
        .output-line.error {
            color: #dc3545;
        }
        .output-line.info {
            color: #17a2b8;
        }
        .output-line.warning {
            color: #ffc107;
            color: black;
        }
        .command-history {
            max-height: 200px;
            overflow-y: auto;
            background: #2d2d2d;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
        }
        .history-item {
            background: #1e1e1e;
            margin: 5px 0;
            padding: 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }
        .history-item:hover {
            background: #3c3c3c;
        }
        .history-command {
            color: #007acc;
            font-weight: bold;
        }
        .history-time {
            color: #888888;
            font-size: 11px;
        }
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-indicator.healthy {
            background: #28a745;
        }
        .status-indicator.unhealthy {
            background: #dc3545;
        }
        .status-indicator.unknown {
            background: #ffc107;
        }
        .loading {
            color: #888888;
            font-style: italic;
        }
        .hidden {
            display: none;
        }
        .terminal-controls {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .quick-commands {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }
        .quick-btn {
            background: #3c3c3c;
            color: #f8f8f2;
            border: 1px solid #555;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }
        .quick-btn:hover {
            background: #4c4c4c;
        }
        .tab-container {
            margin: 15px 0;
        }
        .tab-buttons {
            display: flex;
            gap: 5px;
            margin-bottom: 10px;
        }
        .tab-btn {
            background: #3c3c3c;
            border: 1px solid #555;
            color: #f8f8f2;
            padding: 6px 12px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 13px;
        }
        .tab-btn.active {
            background: #007acc;
            border-color: #007acc;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .help-text {
            background: #2d2d2d;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 15px;
            margin: 15px 0;
            font-size: 13px;
            color: #cccccc;
        }
        .help-text h4 {
            color: #007acc;
            margin-top: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-section">
                <div class="sidebar-title">CLI Status</div>
                <div id="cli-status">
                    <span class="status-indicator unknown"></span>
                    Checking CLI status...
                </div>
            </div>

            <div class="sidebar-section">
                <div class="sidebar-title">Available Commands</div>
                <ul class="command-list" id="command-list">
                    <!-- Commands will be loaded here -->
                </ul>
            </div>

            <div class="sidebar-section">
                <div class="sidebar-title">Interactive Menus</div>
                <ul class="menu-list" id="menu-list">
                    <!-- Menus will be loaded here -->
                </ul>
            </div>

            <div class="sidebar-section">
                <div class="sidebar-title">Quick Actions</div>
                <div class="quick-commands">
                    <button class="quick-btn" onclick="runCommand('health')">Health Check</button>
                    <button class="quick-btn" onclick="runCommand('test-integration')">Test Integration</button>
                    <button class="quick-btn" onclick="runCommand('list-prompts')">List Prompts</button>
                    <button class="quick-btn" onclick="clearTerminal()">Clear</button>
                </div>
            </div>

            <div class="sidebar-section">
                <div class="sidebar-title">Command History</div>
                <div class="command-history" id="command-history">
                    <!-- History will be loaded here -->
                </div>
                <button class="btn secondary" style="width: 100%; margin-top: 10px;" onclick="clearHistory()">Clear History</button>
            </div>
        </div>

        <!-- Terminal -->
        <div class="terminal">
            <div class="terminal-header">
                <div>
                    <span class="status-indicator healthy"></span>
                    LLM Documentation Ecosystem CLI Terminal
                </div>
                <div class="terminal-controls">
                    <button class="btn" onclick="refreshStatus()">Refresh Status</button>
                    <button class="btn secondary" onclick="showHelp()">Help</button>
                </div>
            </div>

            <div class="terminal-output" id="terminal-output">
                <div class="output-line info">Welcome to the LLM Documentation Ecosystem CLI Terminal!</div>
                <div class="output-line info">Type commands or use the sidebar to interact with the system.</div>
                <div class="output-line info">Use 'help' for available commands or click the Help button.</div>
                <div class="output-line">&nbsp;</div>
            </div>

            <div class="terminal-input-area">
                <form onsubmit="executeCommand(event)">
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span style="color: #007acc; font-weight: bold;">$</span>
                        <input
                            type="text"
                            id="command-input"
                            class="command-input"
                            placeholder="Enter CLI command (e.g., 'health', 'list-prompts', 'get-prompt summarization default')"
                            autocomplete="off"
                        >
                        <button type="submit" class="btn">Execute</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Help Modal -->
    <div id="help-modal" class="help-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center;">
        <div style="background: #2d2d2d; border-radius: 8px; padding: 30px; max-width: 600px; max-height: 80vh; overflow-y: auto;">
            <h3 style="color: #007acc; margin-top: 0;">CLI Terminal Help</h3>
            <div class="help-text">
                <h4>Available Commands</h4>
                <p><strong>health</strong> - Check health status of all ecosystem services</p>
                <p><strong>list-prompts [--category CATEGORY]</strong> - List all available prompts, optionally filtered by category</p>
                <p><strong>get-prompt CATEGORY NAME [--content CONTENT]</strong> - Retrieve and display a specific prompt</p>
                <p><strong>test-integration</strong> - Run comprehensive integration tests across all services</p>
                <p><strong>interactive</strong> - Start interactive mode (not supported in web terminal)</p>

                <h4>Examples</h4>
                <p><code>health</code> - Show service health status</p>
                <p><code>list-prompts --category analysis</code> - List analysis prompts</p>
                <p><code>get-prompt summarization default --content "hello world"</code> - Get a prompt with content</p>

                <h4>Interactive Features</h4>
                <p>• Use the sidebar to browse available commands and menus</p>
                <p>• Click on command items to auto-fill the input</p>
                <p>• Use quick action buttons for common commands</p>
                <p>• Command history shows recent executions</p>
            </div>
            <button class="btn" onclick="hideHelp()">Close</button>
        </div>
    </div>

    <script>
        let commandHistory = [];
        let currentCommand = '';

        async function loadCLIStatus() {
            try {
                const response = await fetch('/api/cli/status');
                const data = await response.json();

                const statusDiv = document.getElementById('cli-status');
                if (data.success) {
                    const status = data.health.status;
                    const indicatorClass = status === 'healthy' ? 'healthy' : 'unhealthy';
                    statusDiv.innerHTML = `
                        <span class="status-indicator ${indicatorClass}"></span>
                        CLI ${status.charAt(0).toUpperCase() + status.slice(1)}
                    `;
                } else {
                    statusDiv.innerHTML = `
                        <span class="status-indicator unhealthy"></span>
                        CLI Unavailable
                    `;
                }
            } catch (error) {
                document.getElementById('cli-status').innerHTML = `
                    <span class="status-indicator unhealthy"></span>
                    CLI Error
                `;
            }
        }

        function loadCommands() {
            // This would normally fetch from the API, but for now we'll hardcode
            const commands = [
                { name: 'health', description: 'Check service health', usage: 'health' },
                { name: 'list-prompts', description: 'List available prompts', usage: 'list-prompts [--category CATEGORY]' },
                { name: 'get-prompt', description: 'Retrieve a prompt', usage: 'get-prompt CATEGORY NAME [--content CONTENT]' },
                { name: 'test-integration', description: 'Run integration tests', usage: 'test-integration' }
            ];

            const menus = [
                'Prompt Management',
                'Workflow Orchestration',
                'Analytics & Monitoring',
                'Service Health Check',
                'Service Actions & Bulk Ops',
                'Test Service Integration'
            ];

            const commandList = document.getElementById('command-list');
            commands.forEach(cmd => {
                const li = document.createElement('li');
                li.className = 'command-item';
                li.onclick = () => fillCommand(cmd.usage);
                li.innerHTML = `
                    <div class="command-name">${cmd.name}</div>
                    <div class="command-desc">${cmd.description}</div>
                    <div class="command-usage">${cmd.usage}</div>
                `;
                commandList.appendChild(li);
            });

            const menuList = document.getElementById('menu-list');
            menus.forEach(menu => {
                const li = document.createElement('li');
                li.className = 'menu-item';
                li.textContent = menu;
                menuList.appendChild(li);
            });
        }

        function fillCommand(command) {
            document.getElementById('command-input').value = command;
            document.getElementById('command-input').focus();
        }

        async function executeCommand(event) {
            event.preventDefault();

            const commandInput = document.getElementById('command-input');
            const command = commandInput.value.trim();

            if (!command) return;

            // Add to terminal output
            addToTerminal(`$ ${command}`, 'command');

            // Clear input
            commandInput.value = '';

            // Show loading
            addToTerminal('Executing command...', 'loading');

            try {
                const response = await fetch('/api/cli/execute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ command: command })
                });

                const data = await response.json();

                // Remove loading line
                removeLastLine();

                if (data.success) {
                    const result = data.result;

                    // Add command result to terminal
                    if (result.stdout) {
                        addToTerminal(result.stdout, 'success');
                    }
                    if (result.stderr) {
                        addToTerminal(result.stderr, 'error');
                    }

                    if (result.return_code !== 0) {
                        addToTerminal(`Command exited with code ${result.return_code}`, 'error');
                    }
                } else {
                    addToTerminal(`Error: ${data.error || 'Unknown error'}`, 'error');
                }

                // Update history
                loadCommandHistory();

            } catch (error) {
                removeLastLine();
                addToTerminal(`Network error: ${error.message}`, 'error');
            }

            // Refresh status
            loadCLIStatus();
        }

        async function runCommand(command) {
            document.getElementById('command-input').value = command;
            const fakeEvent = { preventDefault: () => {} };
            await executeCommand(fakeEvent);
        }

        function addToTerminal(text, type = 'info') {
            const output = document.getElementById('terminal-output');
            const lines = text.split('\\n');

            lines.forEach(line => {
                const lineDiv = document.createElement('div');
                lineDiv.className = `output-line ${type}`;
                lineDiv.textContent = line;
                output.appendChild(lineDiv);
            });

            // Scroll to bottom
            output.scrollTop = output.scrollHeight;
        }

        function removeLastLine() {
            const output = document.getElementById('terminal-output');
            const lines = output.querySelectorAll('.output-line');
            if (lines.length > 0) {
                lines[lines.length - 1].remove();
            }
        }

        function clearTerminal() {
            document.getElementById('terminal-output').innerHTML = `
                <div class="output-line info">Terminal cleared. Welcome back!</div>
                <div class="output-line">&nbsp;</div>
            `;
        }

        async function loadCommandHistory() {
            try {
                const response = await fetch('/api/cli/history');
                const data = await response.json();

                const historyDiv = document.getElementById('command-history');
                historyDiv.innerHTML = '';

                if (data.success && data.history.length > 0) {
                    data.history.slice(-10).forEach(item => {
                        const itemDiv = document.createElement('div');
                        itemDiv.className = 'history-item';
                        itemDiv.onclick = () => fillCommand(item.command + (item.args.length ? ' ' + item.args.join(' ') : ''));

                        const timestamp = new Date(item.timestamp).toLocaleTimeString();
                        itemDiv.innerHTML = `
                            <div class="history-command">${item.command}</div>
                            <div class="history-time">${timestamp}</div>
                        `;
                        historyDiv.appendChild(itemDiv);
                    });
                } else {
                    historyDiv.innerHTML = '<div style="color: #888; font-style: italic;">No command history</div>';
                }
            } catch (error) {
                document.getElementById('command-history').innerHTML = '<div style="color: #888; font-style: italic;">Error loading history</div>';
            }
        }

        async function clearHistory() {
            try {
                const response = await fetch('/api/cli/history/clear', { method: 'POST' });
                const data = await response.json();

                if (data.success) {
                    loadCommandHistory();
                    addToTerminal('Command history cleared', 'info');
                } else {
                    addToTerminal('Failed to clear history', 'error');
                }
            } catch (error) {
                addToTerminal('Error clearing history: ' + error.message, 'error');
            }
        }

        function showHelp() {
            document.getElementById('help-modal').style.display = 'flex';
        }

        function hideHelp() {
            document.getElementById('help-modal').style.display = 'none';
        }

        function refreshStatus() {
            loadCLIStatus();
            loadCommandHistory();
        }

        // Close help modal when clicking outside
        document.getElementById('help-modal').addEventListener('click', function(event) {
            if (event.target === this) {
                hideHelp();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', function(event) {
            if (event.ctrlKey && event.key === 'l') {
                event.preventDefault();
                clearTerminal();
            }
            if (event.key === 'ArrowUp') {
                // Could implement command history navigation here
            }
        });

        // Load initial data
        loadCLIStatus();
        loadCommands();
        loadCommandHistory();

        // Auto-refresh status every 30 seconds
        setInterval(refreshStatus, 30000);
    </script>
</body>
</html>
"""
            return create_html_response(html, "CLI Terminal")
        except Exception as e:
            return handle_frontend_error("render CLI terminal", e, **build_frontend_context("render_cli_terminal"))
