"""CLI Service monitoring infrastructure for Frontend service.

Provides terminal pass-through capabilities for CLI service operations,
enabling full CLI functionality through web interface.
"""
from typing import Dict, Any, List, Optional
import asyncio
import subprocess
import threading
import queue
import time
from datetime import datetime

from services.shared.utilities import utc_now
from .shared_utils import get_cli_url, get_frontend_clients


class CLIMonitor:
    """Monitor for CLI service with terminal pass-through capabilities."""

    def __init__(self):
        self._command_history = []
        self._active_sessions = {}
        self._cache_ttl = 60  # Cache for 60 seconds for CLI status

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = getattr(self, f"_{cache_key}_updated", None)
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def execute_cli_command(self, command: str, args: Optional[List[str]] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a CLI command and return the result."""
        try:
            # Build the command
            cmd_args = ["python", "services/cli/main.py", command]
            if args:
                cmd_args.extend(args)

            # Create a subprocess to run the CLI command
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="."
            )

            # Wait for the command to complete
            stdout, stderr = await process.communicate()

            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')

            result = {
                "command": command,
                "args": args or [],
                "return_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "success": process.returncode == 0,
                "timestamp": utc_now().isoformat()
            }

            # Store in history
            self._command_history.append(result)
            # Keep only last 100 commands
            if len(self._command_history) > 100:
                self._command_history = self._command_history[-100:]

            return result

        except Exception as e:
            error_result = {
                "command": command,
                "args": args or [],
                "return_code": -1,
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "success": False,
                "timestamp": utc_now().isoformat()
            }

            # Store error in history
            self._command_history.append(error_result)

            return error_result

    async def get_cli_health(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get CLI service health status."""
        if not force_refresh and self.is_cache_fresh("health"):
            return getattr(self, "_health_cache", {})

        try:
            # Try to run a simple CLI health command
            result = await self.execute_cli_command("health")

            health_data = {
                "status": "healthy" if result["success"] else "unhealthy",
                "last_check": utc_now().isoformat(),
                "cli_available": result["success"],
                "health_output": result["stdout"],
                "error_output": result["stderr"]
            }

            self._health_cache = health_data
            self._health_updated = utc_now()

            return health_data

        except Exception as e:
            return {
                "status": "unhealthy",
                "last_check": utc_now().isoformat(),
                "cli_available": False,
                "error": str(e)
            }

    async def get_available_commands(self) -> Dict[str, Any]:
        """Get list of available CLI commands."""
        return {
            "commands": [
                {
                    "name": "interactive",
                    "description": "Start interactive TUI workflow",
                    "usage": "interactive"
                },
                {
                    "name": "get-prompt",
                    "description": "Retrieve and render a prompt",
                    "usage": "get-prompt <category> <name> [--content <content>]"
                },
                {
                    "name": "health",
                    "description": "Check service health across the stack",
                    "usage": "health"
                },
                {
                    "name": "list-prompts",
                    "description": "List available prompts",
                    "usage": "list-prompts [--category <category>]"
                },
                {
                    "name": "test-integration",
                    "description": "Run cross-service checks from CLI",
                    "usage": "test-integration"
                }
            ],
            "interactive_menus": [
                "Prompt Management",
                "A/B Testing",
                "Workflow Orchestration",
                "Analytics & Monitoring",
                "Service Health Check",
                "Service Actions & Bulk Ops",
                "Test Service Integration"
            ]
        }

    async def get_command_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent command execution history."""
        return self._command_history[-limit:] if self._command_history else []

    def clear_command_history(self) -> bool:
        """Clear the command execution history."""
        self._command_history = []
        return True

    async def get_prompt_list(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get list of available prompts via CLI."""
        try:
            args = []
            if category:
                args.extend(["--category", category])

            result = await self.execute_cli_command("list-prompts", args)

            return {
                "success": result["success"],
                "output": result["stdout"],
                "error": result["stderr"],
                "category": category
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "category": category
            }

    async def get_prompt_details(self, category: str, name: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Get specific prompt details via CLI."""
        try:
            args = [category, name]
            if content:
                args.extend(["--content", content])

            result = await self.execute_cli_command("get-prompt", args)

            return {
                "success": result["success"],
                "output": result["stdout"],
                "error": result["stderr"],
                "category": category,
                "name": name,
                "content": content
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "category": category,
                "name": name
            }

    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests via CLI."""
        try:
            result = await self.execute_cli_command("test-integration")

            return {
                "success": result["success"],
                "output": result["stdout"],
                "error": result["stderr"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
cli_monitor = CLIMonitor()
