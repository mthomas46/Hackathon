"""Event system for GitHub MCP service.

Handles integration events and downstream service notifications.
"""
from typing import Dict, Any
from services.shared.integrations.clients.clients import ServiceClients


class EventSystem:
    """Handles downstream integrations and event emissions."""

    async def maybe_emit_events(self, tool: str, result: Dict[str, Any]) -> None:
        """Emit events to downstream services based on tool results."""
        clients = ServiceClients(timeout=15)
        try:
            if tool == "github.get_pr_diff" and result.get("diff"):
                await clients.post_json("code-analyzer/analyze/text", {"content": result["diff"]})
            if tool == "github.get_repo" and result.get("full_name"):
                await clients.post_json("doc_store/documents", {
                    "content": f"Repository: {result['full_name']}",
                    "metadata": {"repo": result["full_name"], "stars": result.get("stars", 0)}
                })
        except Exception:
            # Best-effort integrations; ignore failures in fire-and-forget style
            pass


# Create singleton instance
event_system = EventSystem()
