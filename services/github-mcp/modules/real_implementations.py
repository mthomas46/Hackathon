"""Real implementations for GitHub MCP tools.

Handles delegation to actual GitHub services via source-agent.
"""
from typing import Dict, Any
from fastapi import HTTPException
from services.shared.integrations.clients.clients import ServiceClients


class RealImplementations:
    """Real implementations that delegate to external services."""

    def __init__(self):
        self.endpoint_map = {
            "github.search_repos": ("source-agent", "github/search"),
            "github.get_repo": ("source-agent", "github/repo"),
            "github.list_prs": ("source-agent", "github/prs"),
            "github.get_pr_diff": ("source-agent", "github/pr/diff"),
        }

    async def invoke_tool(self, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a tool using real implementations."""
        if tool not in self.endpoint_map:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool}")

        svc_name, path = self.endpoint_map[tool]
        clients = ServiceClients(timeout=30)
        # Compose URL like "source-agent/..."
        url = f"{svc_name}/{path}"
        return await clients.post_json(url, args)


# Create singleton instance
real_implementations = RealImplementations()
