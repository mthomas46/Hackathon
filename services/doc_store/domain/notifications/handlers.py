"""Notifications handlers for API endpoints.

Handles notification-related HTTP requests and responses.
"""
from typing import Dict, Any, Optional
from ...core.handler import BaseHandler
from .service import NotificationsService


class NotificationsHandlers(BaseHandler):
    """Handlers for notifications API endpoints."""

    def __init__(self):
        super().__init__(NotificationsService())

    async def handle_emit_event(self, event_type: str, entity_type: str, entity_id: str,
                               user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle event emission."""
        event = self.service.emit_event(event_type, entity_type, entity_id, user_id, metadata)

        return await self._handle_request(
            lambda: event.to_dict(),
            operation="emit_event",
            event_type=event_type,
            entity_id=entity_id
        )

    async def handle_get_event_history(self, event_type: Optional[str] = None, entity_type: Optional[str] = None,
                                      entity_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Handle event history retrieval."""
        result = self.service.get_event_history(event_type, entity_type, entity_id, limit)

        return await self._handle_request(
            lambda: result,
            operation="get_event_history",
            total_events=result["total"]
        )

    async def handle_get_notification_stats(self, days_back: int = 7) -> Dict[str, Any]:
        """Handle notification stats request."""
        stats = self.service.get_notification_stats(days_back)

        return await self._handle_request(
            lambda: stats,
            operation="get_notification_stats",
            days_back=days_back
        )
