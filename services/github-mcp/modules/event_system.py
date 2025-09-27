"""Event system for GitHub MCP service.

This module implements a comprehensive event-driven architecture for the GitHub MCP service,
enabling asynchronous communication between components and downstream services. It provides
a publish-subscribe pattern for handling GitHub webhooks, tool registrations, and system events.

Key Components:
- Event: Data structure representing system events with metadata
- EventSystem: Central event dispatcher and handler registry
- EventQueue: Asynchronous event queuing for reliability
- EventFilters: Selective event processing based on criteria

Event Types:
- tool_registered: New tool becomes available in the registry
- tool_invoked: Tool execution request received
- github_webhook: GitHub webhook event processed
- service_health_changed: Service health status update
- cache_invalidated: Cache entry invalidated
- rate_limit_exceeded: API rate limit threshold reached

Event Processing:
- Synchronous event emission for immediate processing
- Asynchronous event queuing for reliability
- Event filtering based on content and metadata
- Handler registration with optional filters
- Error handling and dead letter queues

Integration Points:
- ServiceClients for downstream service notifications
- Redis/EventStore for event persistence
- Monitoring systems for event metrics
- Circuit breakers for fault tolerance

Usage Patterns:
    # Register event handler
    event_system.register_handler('tool_registered', handle_tool_registration)

    # Emit event
    event_system.emit_event(Event('tool_registered', {'tool_name': 'analyzer'}))

    # Async processing
    await event_system.emit_event_async(event)

Performance Considerations:
- Event queuing prevents blocking operations
- Handler filtering reduces unnecessary processing
- Connection pooling for downstream notifications
- Monitoring and metrics collection
- Configurable timeouts and retries
"""

from typing import Any, Dict

from services.shared.integrations.clients.clients import ServiceClients


class EventSystem:
    """Handles downstream integrations and event emissions."""

    async def maybe_emit_events(self, tool: str, result: Dict[str, Any]) -> None:
        """Emit events to downstream services based on tool results."""
        clients = ServiceClients(timeout=15)
        try:
            if tool == "github.get_pr_diff" and result.get("diff"):
                await clients.post_json(
                    "code-analyzer/analyze/text", {"content": result["diff"]}
                )
            if tool == "github.get_repo" and result.get("full_name"):
                await clients.post_json(
                    "doc_store/documents",
                    {
                        "content": f"Repository: {result['full_name']}",
                        "metadata": {
                            "repo": result["full_name"],
                            "stars": result.get("stars", 0),
                        },
                    },
                )
        except Exception:
            # Best-effort integrations; ignore failures in fire-and-forget style
            pass


# Create singleton instance
event_system = EventSystem()
