"""GitHub MCP monitoring infrastructure for Frontend service.

Provides visualization and monitoring capabilities for github-mcp
service tool invocations and GitHub data operations.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.shared.utilities import utc_now
from .shared_utils import get_github_mcp_url, get_frontend_clients


class GithubMcpMonitor:
    """Monitor for github-mcp service tool invocations and GitHub operations."""

    def __init__(self):
        self._tool_invocations = []
        self._cache_ttl = 30  # Cache for 30 seconds

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = getattr(self, f"_{cache_key}_updated", None)
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_mcp_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive github-mcp service status."""
        if not force_refresh and self.is_cache_fresh("status"):
            return getattr(self, "_status_cache", {})

        try:
            clients = get_frontend_clients()
            mcp_url = get_github_mcp_url()

            # Get health and info status
            health_response = await clients.get_json(f"{mcp_url}/health")
            info_response = await clients.get_json(f"{mcp_url}/info")

            status_data = {
                "health": health_response,
                "info": info_response,
                "tool_stats": self._calculate_tool_stats(),
                "recent_invocations": self._tool_invocations[-10:] if self._tool_invocations else [],  # Last 10 invocations
                "last_updated": utc_now().isoformat()
            }

            self._status_cache = status_data
            self._status_updated = utc_now()

            return status_data

        except Exception as e:
            return {
                "error": str(e),
                "health": {},
                "info": {},
                "tool_stats": {},
                "recent_invocations": [],
                "last_updated": utc_now().isoformat()
            }

    async def get_available_tools(self, toolsets: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of available GitHub MCP tools."""
        try:
            clients = get_frontend_clients()
            mcp_url = get_github_mcp_url()

            # Build URL with optional toolsets query parameter
            url = f"{mcp_url}/tools"
            if toolsets:
                url += f"?toolsets={toolsets}"

            tools_response = await clients.get_json(url)
            return tools_response if isinstance(tools_response, list) else []

        except Exception as e:
            return []

    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any], mock: Optional[bool] = None, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Invoke a GitHub MCP tool and cache the result."""
        try:
            clients = get_frontend_clients()
            mcp_url = get_github_mcp_url()

            payload = {
                "arguments": arguments or {}
            }

            if mock is not None:
                payload["mock"] = mock
            if correlation_id:
                payload["correlation_id"] = correlation_id

            response = await clients.post_json(f"{mcp_url}/tools/{tool_name}/invoke", payload)

            if response.get("success") or "result" in response:
                # Cache the invocation
                invocation_result = {
                    "id": f"invocation_{utc_now().isoformat()}",
                    "timestamp": utc_now().isoformat(),
                    "tool": tool_name,
                    "arguments": arguments,
                    "mock_mode": mock,
                    "correlation_id": correlation_id,
                    "success": response.get("success", True),
                    "result": response.get("result", response),
                    "response": response
                }

                self._tool_invocations.insert(0, invocation_result)  # Add to front

                # Keep only last 50 invocations
                if len(self._tool_invocations) > 50:
                    self._tool_invocations = self._tool_invocations[:50]

                return {
                    "success": True,
                    "invocation_id": invocation_result["id"],
                    "tool": tool_name,
                    "result": response
                }

            return {
                "success": False,
                "error": "Tool invocation failed",
                "tool": tool_name,
                "result": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "result": None
            }

    def _calculate_tool_stats(self) -> Dict[str, Any]:
        """Calculate statistics from cached tool invocations."""
        if not self._tool_invocations:
            return {
                "total_invocations": 0,
                "successful_invocations": 0,
                "failed_invocations": 0,
                "unique_tools_used": 0,
                "mock_mode_count": 0,
                "real_mode_count": 0
            }

        total = len(self._tool_invocations)
        successful = sum(1 for inv in self._tool_invocations if inv.get("success"))
        failed = total - successful
        mock_count = sum(1 for inv in self._tool_invocations if inv.get("mock_mode"))
        real_count = total - mock_count

        # Unique tools
        tools = set()
        for invocation in self._tool_invocations:
            if invocation.get("tool"):
                tools.add(invocation["tool"])

        return {
            "total_invocations": total,
            "successful_invocations": successful,
            "failed_invocations": failed,
            "success_rate": round((successful / total) * 100, 1) if total > 0 else 0,
            "unique_tools_used": len(tools),
            "tools_used": list(tools),
            "mock_mode_count": mock_count,
            "real_mode_count": real_count
        }

    def get_invocation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent tool invocation history."""
        return self._tool_invocations[:limit]


# Global instance
github_mcp_monitor = GithubMcpMonitor()
