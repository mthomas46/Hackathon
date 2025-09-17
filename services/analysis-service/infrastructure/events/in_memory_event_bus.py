"""In-Memory Event Bus - Lightweight event bus for testing and development."""

import asyncio
from typing import Any, Dict, List, Optional, Callable, Union
from collections import defaultdict

from .event_bus import (
    EventBus, EventPublisher, EventSubscriber,
    DomainEvent, EventEnvelope
)


class InMemoryEventBus(EventBus):
    """In-memory event bus for testing and development."""

    def __init__(self):
        """Initialize in-memory event bus."""
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._published_events: List[EventEnvelope] = []
        self._max_stored_events = 1000  # Keep last 1000 events for inspection

        # Statistics
        self.messages_published = 0
        self.messages_received = 0
        self.errors_count = 0

    async def publish(self, event: Union[DomainEvent, EventEnvelope], topic: Optional[str] = None) -> None:
        """Publish an event in memory."""
        try:
            # Convert to envelope if needed
            if isinstance(event, DomainEvent):
                if topic is None:
                    topic = self._get_default_topic(event)
                envelope = EventEnvelope(event=event, topic=topic)
            else:
                envelope = event

            # Store event for inspection
            self._published_events.append(envelope)
            if len(self._published_events) > self._max_stored_events:
                self._published_events.pop(0)

            # Deliver to subscribers
            await self._deliver_event(envelope)

            self.messages_published += 1

        except Exception as e:
            self.errors_count += 1
            raise RuntimeError(f"Failed to publish event: {e}") from e

    async def publish_batch(self, events: List[Union[DomainEvent, EventEnvelope]], topic: Optional[str] = None) -> None:
        """Publish multiple events in batch."""
        try:
            envelopes = []

            for event in events:
                if isinstance(event, DomainEvent):
                    event_topic = topic or self._get_default_topic(event)
                    envelope = EventEnvelope(event=event, topic=event_topic)
                else:
                    envelope = event

                envelopes.append(envelope)

            # Store events
            for envelope in envelopes:
                self._published_events.append(envelope)

            if len(self._published_events) > self._max_stored_events:
                # Keep only the most recent events
                self._published_events = self._published_events[-self._max_stored_events:]

            # Deliver to subscribers
            for envelope in envelopes:
                await self._deliver_event(envelope)

            self.messages_published += len(events)

        except Exception as e:
            self.errors_count += 1
            raise RuntimeError(f"Failed to publish batch events: {e}") from e

    async def _deliver_event(self, envelope: EventEnvelope) -> None:
        """Deliver event to subscribers."""
        if envelope.topic not in self._handlers:
            return

        # Create tasks for all handlers
        tasks = []
        for handler in self._handlers[envelope.topic]:
            task = asyncio.create_task(self._safe_handle(handler, envelope))
            tasks.append(task)

        # Wait for all handlers to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            self.messages_received += len(tasks)

    async def _safe_handle(self, handler: Callable, envelope: EventEnvelope) -> None:
        """Safely handle event with error handling."""
        try:
            await handler(envelope)
        except Exception as e:
            self.errors_count += 1
            print(f"Error in event handler: {e}")

    async def subscribe(self, topic: str, handler: Callable, **kwargs) -> None:
        """Subscribe to events on a topic."""
        self._handlers[topic].append(handler)

    async def unsubscribe(self, topic: str, handler: Callable) -> None:
        """Unsubscribe from events on a topic."""
        if topic in self._handlers:
            try:
                self._handlers[topic].remove(handler)
                # Clean up empty topic lists
                if not self._handlers[topic]:
                    del self._handlers[topic]
            except ValueError:
                pass  # Handler not found

    async def get_subscriber_count(self, topic: str) -> int:
        """Get number of subscribers for a topic."""
        return len(self._handlers.get(topic, []))

    async def get_topics(self) -> List[str]:
        """Get all available topics."""
        return list(self._handlers.keys())

    def get_published_events(self, topic: Optional[str] = None, limit: Optional[int] = None) -> List[EventEnvelope]:
        """Get published events for inspection."""
        events = self._published_events

        if topic:
            events = [e for e in events if e.topic == topic]

        if limit:
            events = events[-limit:]

        return events

    def get_event_count(self, topic: Optional[str] = None) -> int:
        """Get count of published events."""
        if topic:
            return len([e for e in self._published_events if e.topic == topic])
        return len(self._published_events)

    def clear_published_events(self) -> None:
        """Clear stored published events."""
        self._published_events.clear()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            'status': 'healthy',
            'in_memory': True,
            'active_topics': len(self._handlers),
            'total_subscribers': sum(len(handlers) for handlers in self._handlers.values()),
            'stored_events': len(self._published_events),
            'max_stored_events': self._max_stored_events,
            'messages_published': self.messages_published,
            'messages_received': self.messages_received,
            'errors_count': self.errors_count
        }

    def _get_default_topic(self, event: DomainEvent) -> str:
        """Get default topic for event type."""
        from .event_bus import EventType

        topic_map = {
            EventType.ANALYSIS_STARTED: 'analysis.events',
            EventType.ANALYSIS_COMPLETED: 'analysis.events',
            EventType.ANALYSIS_FAILED: 'analysis.events',
            EventType.DOCUMENT_CREATED: 'document.events',
            EventType.DOCUMENT_UPDATED: 'document.events',
            EventType.DOCUMENT_DELETED: 'document.events',
            EventType.FINDING_CREATED: 'finding.events',
            EventType.FINDING_UPDATED: 'finding.events',
            EventType.WORKFLOW_TRIGGERED: 'workflow.events',
            EventType.NOTIFICATION_SENT: 'notification.events',
            EventType.CACHE_INVALIDATED: 'cache.events',
            EventType.METRICS_UPDATED: 'metrics.events',
            EventType.SYSTEM_HEALTH_CHECK: 'system.events'
        }

        return topic_map.get(event.event_type, 'general.events')


class InMemoryEventPublisher(EventPublisher):
    """In-memory event publisher."""

    def __init__(self):
        """Initialize in-memory event publisher."""
        event_bus = InMemoryEventBus()
        super().__init__(event_bus)


class InMemoryEventSubscriber(EventSubscriber):
    """In-memory event subscriber."""

    def __init__(self):
        """Initialize in-memory event subscriber."""
        event_bus = InMemoryEventBus()
        super().__init__(event_bus)


class SharedInMemoryEventBus(InMemoryEventBus):
    """Shared in-memory event bus for cross-service communication in testing."""

    _instance: Optional['SharedInMemoryEventBus'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        """Initialize shared instance."""
        if SharedInMemoryEventBus._instance is None:
            super().__init__()
            SharedInMemoryEventBus._instance = self
        else:
            # Copy state from existing instance
            self._handlers = SharedInMemoryEventBus._instance._handlers
            self._published_events = SharedInMemoryEventBus._instance._published_events
            self._max_stored_events = SharedInMemoryEventBus._instance._max_stored_events
            self.messages_published = SharedInMemoryEventBus._instance.messages_published
            self.messages_received = SharedInMemoryEventBus._instance.messages_received
            self.errors_count = SharedInMemoryEventBus._instance.errors_count

    @classmethod
    def get_instance(cls) -> 'SharedInMemoryEventBus':
        """Get shared instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    async def create_shared_instance(cls) -> 'SharedInMemoryEventBus':
        """Create shared instance with async safety."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def reset_shared_state(self) -> None:
        """Reset shared state for testing."""
        self._handlers.clear()
        self._published_events.clear()
        self.messages_published = 0
        self.messages_received = 0
        self.errors_count = 0


class TestEventBus(InMemoryEventBus):
    """Enhanced in-memory event bus for testing with additional features."""

    def __init__(self):
        """Initialize test event bus."""
        super().__init__()
        self._event_history: List[Dict[str, Any]] = []
        self._handler_call_history: List[Dict[str, Any]] = []

    async def _deliver_event(self, envelope: EventEnvelope) -> None:
        """Deliver event with call tracking."""
        # Record delivery attempt
        self._event_history.append({
            'event_id': envelope.event.event_id,
            'event_type': envelope.event.event_type.value,
            'topic': envelope.topic,
            'timestamp': envelope.event.timestamp.isoformat(),
            'subscriber_count': len(self._handlers.get(envelope.topic, []))
        })

        await super()._deliver_event(envelope)

    async def _safe_handle(self, handler: Callable, envelope: EventEnvelope) -> None:
        """Track handler calls."""
        # Record handler call
        self._handler_call_history.append({
            'event_id': envelope.event.event_id,
            'topic': envelope.topic,
            'handler': str(handler),
            'timestamp': asyncio.get_event_loop().time()
        })

        await super()._safe_handle(handler, envelope)

    def get_event_history(self) -> List[Dict[str, Any]]:
        """Get event delivery history."""
        return self._event_history.copy()

    def get_handler_call_history(self) -> List[Dict[str, Any]]:
        """Get handler call history."""
        return self._handler_call_history.copy()

    def get_event_by_id(self, event_id: str) -> Optional[EventEnvelope]:
        """Get event by ID from published events."""
        for event in self._published_events:
            if event.event.event_id == event_id:
                return event
        return None

    def get_events_by_type(self, event_type: str) -> List[EventEnvelope]:
        """Get events by type."""
        return [
            event for event in self._published_events
            if event.event.event_type.value == event_type
        ]

    def get_events_by_topic(self, topic: str) -> List[EventEnvelope]:
        """Get events by topic."""
        return [event for event in self._published_events if event.topic == topic]

    def assert_event_published(self, event_type: str, topic: Optional[str] = None) -> bool:
        """Assert that an event was published."""
        events = self.get_events_by_type(event_type)
        if topic:
            events = [e for e in events if e.topic == topic]
        return len(events) > 0

    def assert_event_handled(self, event_id: str) -> bool:
        """Assert that an event was handled."""
        return any(call['event_id'] == event_id for call in self._handler_call_history)

    def clear_history(self) -> None:
        """Clear event and handler history."""
        self._event_history.clear()
        self._handler_call_history.clear()
        super().clear_published_events()
