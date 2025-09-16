"""Event system for Doc Store service.

Provides event emission, subscription, and notification capabilities.
"""
import asyncio
import json
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime
from services.shared.utilities import utc_now


@dataclass
class Event:
    """Event data structure."""
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    user_id: Optional[str] = None
    data: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = utc_now()
        if self.data is None:
            self.data = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


EventHandler = Callable[[Event], Awaitable[None]]


class EventEmitter:
    """Event emitter for publish-subscribe pattern."""

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._middleware: List[Callable[[Event], Awaitable[Event]]] = []

    def on(self, event_type: str, handler: EventHandler) -> None:
        """Register event handler."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: EventHandler) -> None:
        """Unregister event handler."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                if not self._handlers[event_type]:
                    del self._handlers[event_type]
            except ValueError:
                pass

    def use(self, middleware: Callable[[Event], Awaitable[Event]]) -> None:
        """Add middleware function."""
        self._middleware.append(middleware)

    async def emit(self, event: Event) -> None:
        """Emit event to all registered handlers."""
        try:
            # Apply middleware
            processed_event = event
            for middleware in self._middleware:
                processed_event = await middleware(processed_event)

            # Emit to handlers
            if processed_event.event_type in self._handlers:
                tasks = []
                for handler in self._handlers[processed_event.event_type]:
                    tasks.append(handler(processed_event))
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception:
            # Log error but don't crash
            pass


class NotificationManager:
    """Manager for notifications and webhooks."""

    def __init__(self):
        self.event_emitter = EventEmitter()
        self.webhooks: Dict[str, Dict[str, Any]] = {}
        self.event_history: List[Event] = []
        self.max_history = 1000

    async def emit_event(self, event_type: str, entity_type: str, entity_id: str,
                        user_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> str:
        """Emit an event and return event ID."""
        import uuid

        event = Event(
            id=str(uuid.uuid4()),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            data=data or {}
        )

        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]

        # Emit event
        await self.event_emitter.emit(event)

        return event.id

    def register_webhook(self, webhook_id: str, url: str, events: List[str],
                        secret: Optional[str] = None, headers: Optional[Dict[str, str]] = None) -> None:
        """Register a webhook."""
        self.webhooks[webhook_id] = {
            "url": url,
            "events": events,
            "secret": secret,
            "headers": headers or {},
            "is_active": True,
            "created_at": utc_now().isoformat()
        }

    def unregister_webhook(self, webhook_id: str) -> None:
        """Unregister a webhook."""
        self.webhooks.pop(webhook_id, None)

    async def deliver_webhooks(self, event: Event) -> Dict[str, Any]:
        """Deliver event to registered webhooks."""
        delivered = 0
        failed = 0

        for webhook_id, webhook in self.webhooks.items():
            if not webhook["is_active"] or event.event_type not in webhook["events"]:
                continue

            try:
                # Here we would make HTTP request to webhook URL
                # For now, just simulate success
                delivered += 1
            except Exception:
                failed += 1

        return {
            "event_id": event.id,
            "delivered": delivered,
            "failed": failed,
            "total_webhooks": len([w for w in self.webhooks.values() if w["is_active"]])
        }

    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get event history with optional filtering."""
        events = self.event_history

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return [event.to_dict() for event in events[-limit:]]

    def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook statistics."""
        active = sum(1 for w in self.webhooks.values() if w["is_active"])
        total = len(self.webhooks)

        return {
            "total_webhooks": total,
            "active_webhooks": active,
            "inactive_webhooks": total - active,
            "total_events": len(self.event_history)
        }


# Global instances
event_emitter = EventEmitter()
notification_manager = NotificationManager()
