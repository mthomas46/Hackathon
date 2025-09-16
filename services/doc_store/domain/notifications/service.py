"""Notifications service for business logic operations.

Handles notification processing and webhook management.
"""
import uuid
from typing import Dict, Any, Optional, List
from ...core.service import BaseService
from ...core.entities import NotificationEvent, Webhook
from .repository import NotificationsRepository


class NotificationsService(BaseService[NotificationEvent]):
    """Service for notification business logic."""

    def __init__(self):
        super().__init__(NotificationsRepository())

    def _validate_entity(self, entity: NotificationEvent) -> None:
        """Validate notification event."""
        if not entity.event_type or not entity.entity_type or not entity.entity_id:
            raise ValueError("Event type, entity type, and entity ID are required")

    def _create_entity_from_data(self, entity_id: str, data: Dict[str, Any]) -> NotificationEvent:
        """Create notification event from data."""
        return NotificationEvent(
            id=entity_id,
            event_type=data['event_type'],
            entity_type=data['entity_type'],
            entity_id=data['entity_id'],
            user_id=data.get('user_id'),
            metadata=data.get('metadata', {})
        )

    def emit_event(self, event_type: str, entity_type: str, entity_id: str,
                  user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> NotificationEvent:
        """Emit a notification event."""
        data = {
            'event_type': event_type,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'user_id': user_id,
            'metadata': metadata or {}
        }
        event = self.create_entity(data)

        # Trigger webhook deliveries (simplified)
        self._trigger_webhooks(event)

        return event

    def _trigger_webhooks(self, event: NotificationEvent) -> None:
        """Trigger webhook deliveries for an event."""
        webhooks = self.repository.get_webhooks_for_event(event.event_type)

        for webhook in webhooks:
            # In a full implementation, this would queue async webhook deliveries
            # For now, we'll just log that webhooks would be triggered
            pass

    def get_event_history(self, event_type: Optional[str] = None, entity_type: Optional[str] = None,
                         entity_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Get notification event history."""
        events = self.repository.get_event_history(event_type, entity_type, entity_id, limit)

        return {
            "events": [event.to_dict() for event in events],
            "total": len(events),
            "filters": {
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": entity_id
            },
            "limit": limit
        }

    def get_notification_stats(self, days_back: int = 7) -> Dict[str, Any]:
        """Get notification statistics."""
        return self.repository.get_notification_stats(days_back)
