"""Event Bus - Core event publishing infrastructure."""

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ...application.services import ApplicationService, ServiceContext


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventType(Enum):
    """Standard event types."""
    SYSTEM_HEALTH_CHECK = "system_health_check"
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_DELETED = "document_deleted"
    FINDING_CREATED = "finding_created"
    FINDING_UPDATED = "finding_updated"
    WORKFLOW_TRIGGERED = "workflow_triggered"
    NOTIFICATION_SENT = "notification_sent"
    CACHE_INVALIDATED = "cache_invalidated"
    METRICS_UPDATED = "metrics_updated"


@dataclass
class DomainEvent:
    """Base domain event class."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SYSTEM_HEALTH_CHECK
    correlation_id: Optional[str] = None
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL

    def __post_init__(self):
        """Validate event after initialization."""
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'correlation_id': self.correlation_id,
            'aggregate_id': self.aggregate_id,
            'aggregate_type': self.aggregate_type,
            'timestamp': self.timestamp.isoformat(),
            'version': self.version,
            'metadata': self.metadata,
            'priority': self.priority.value,
            'event_class': self.__class__.__name__
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DomainEvent':
        """Create event from dictionary."""
        # Handle event type conversion
        if isinstance(data.get('event_type'), str):
            try:
                data['event_type'] = EventType(data['event_type'])
            except ValueError:
                data['event_type'] = EventType.SYSTEM_HEALTH_CHECK

        # Handle priority conversion
        if isinstance(data.get('priority'), int):
            try:
                data['priority'] = EventPriority(data['priority'])
            except ValueError:
                data['priority'] = EventPriority.NORMAL

        # Handle timestamp conversion
        if isinstance(data.get('timestamp'), str):
            try:
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            except ValueError:
                data['timestamp'] = datetime.utcnow()

        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EventEnvelope:
    """Event envelope for transport."""
    event: DomainEvent
    topic: str
    partition_key: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        """Initialize envelope."""
        if self.headers is None:
            self.headers = {}
        if self.partition_key is None and self.event.aggregate_id:
            self.partition_key = self.event.aggregate_id

    def increment_retry(self) -> bool:
        """Increment retry count and return if should retry."""
        self.retry_count += 1
        return self.retry_count <= self.max_retries


class EventBus(ABC):
    """Abstract event bus interface."""

    @abstractmethod
    async def publish(self, event: Union[DomainEvent, EventEnvelope], topic: Optional[str] = None) -> None:
        """Publish an event."""
        pass

    @abstractmethod
    async def publish_batch(self, events: List[Union[DomainEvent, EventEnvelope]], topic: Optional[str] = None) -> None:
        """Publish multiple events."""
        pass

    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable, **kwargs) -> None:
        """Subscribe to events on a topic."""
        pass

    @abstractmethod
    async def unsubscribe(self, topic: str, handler: Callable) -> None:
        """Unsubscribe from events on a topic."""
        pass

    @abstractmethod
    async def get_subscriber_count(self, topic: str) -> int:
        """Get number of subscribers for a topic."""
        pass

    @abstractmethod
    async def get_topics(self) -> List[str]:
        """Get all available topics."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        pass


class EventPublisher:
    """Event publisher interface."""

    def __init__(self, event_bus: EventBus):
        """Initialize publisher."""
        self.event_bus = event_bus

    async def publish_event(
        self,
        event: DomainEvent,
        topic: Optional[str] = None,
        partition_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """Publish an event with envelope."""
        if topic is None:
            topic = self._get_default_topic(event)

        envelope = EventEnvelope(
            event=event,
            topic=topic,
            partition_key=partition_key,
            headers=headers or {}
        )

        await self.event_bus.publish(envelope)

    async def publish_events_batch(
        self,
        events: List[DomainEvent],
        topic: Optional[str] = None,
        partition_key: Optional[str] = None
    ) -> None:
        """Publish multiple events."""
        envelopes = []
        for event in events:
            event_topic = topic or self._get_default_topic(event)
            envelope = EventEnvelope(
                event=event,
                topic=event_topic,
                partition_key=partition_key
            )
            envelopes.append(envelope)

        await self.event_bus.publish_batch(envelopes, topic)

    def _get_default_topic(self, event: DomainEvent) -> str:
        """Get default topic for event type."""
        # Map event types to topics
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


class EventSubscriber:
    """Event subscriber interface."""

    def __init__(self, event_bus: EventBus):
        """Initialize subscriber."""
        self.event_bus = event_bus
        self.handlers: Dict[str, List[Callable]] = {}

    async def subscribe_to_topic(
        self,
        topic: str,
        handler: Callable,
        event_types: Optional[List[EventType]] = None,
        **kwargs
    ) -> None:
        """Subscribe to a topic with optional event type filtering."""
        async def filtered_handler(envelope: EventEnvelope):
            """Filter events by type before handling."""
            if event_types and envelope.event.event_type not in event_types:
                return
            await handler(envelope)

        await self.event_bus.subscribe(topic, filtered_handler, **kwargs)
        if topic not in self.handlers:
            self.handlers[topic] = []
        self.handlers[topic].append(handler)

    async def subscribe_to_event_type(
        self,
        event_type: EventType,
        handler: Callable,
        topic: Optional[str] = None,
        **kwargs
    ) -> None:
        """Subscribe to specific event types."""
        if topic is None:
            # Use default topic mapping
            publisher = EventPublisher(self.event_bus)
            dummy_event = DomainEvent(event_type=event_type)
            topic = publisher._get_default_topic(dummy_event)

        await self.subscribe_to_topic(topic, handler, [event_type], **kwargs)

    async def unsubscribe_from_topic(self, topic: str, handler: Callable) -> None:
        """Unsubscribe from a topic."""
        if topic in self.handlers:
            self.handlers[topic].remove(handler)
            if not self.handlers[topic]:
                del self.handlers[topic]

        await self.event_bus.unsubscribe(topic, handler)

    def get_subscription_count(self) -> int:
        """Get total number of subscriptions."""
        return sum(len(handlers) for handlers in self.handlers.values())


class EventPublishingService(ApplicationService):
    """Event publishing service for infrastructure layer."""

    def __init__(
        self,
        event_bus: EventBus,
        dead_letter_queue: Optional[Any] = None,
        retry_policy: Optional[Dict[str, Any]] = None
    ):
        """Initialize event publishing service."""
        super().__init__("event_publishing_service")
        self.event_bus = event_bus
        self.dead_letter_queue = dead_letter_queue
        self.retry_policy = retry_policy or {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 60.0,
            'backoff_factor': 2.0
        }

        self.publisher = EventPublisher(event_bus)
        self.subscriber = EventSubscriber(event_bus)

        # Statistics
        self.events_published = 0
        self.events_failed = 0
        self.events_retried = 0
        self.dead_letter_count = 0

    async def publish_event(
        self,
        event: DomainEvent,
        topic: Optional[str] = None,
        context: Optional[ServiceContext] = None
    ) -> None:
        """Publish an event with retry logic."""
        async with self.operation_context("publish_event", context):
            try:
                await self.publisher.publish_event(event, topic)
                self.events_published += 1

                self.logger.info(
                    f"Event published: {event.event_type.value}",
                    extra={
                        'event_id': event.event_id,
                        'event_type': event.event_type.value,
                        'topic': topic,
                        'correlation_id': event.correlation_id
                    }
                )

            except Exception as e:
                self.events_failed += 1
                self.logger.error(
                    f"Failed to publish event: {event.event_type.value}",
                    exc_info=True,
                    extra={
                        'event_id': event.event_id,
                        'event_type': event.event_type.value,
                        'error': str(e)
                    }
                )

                # Send to dead letter queue if available
                if self.dead_letter_queue:
                    await self._send_to_dead_letter_queue(event, str(e))
                else:
                    raise

    async def publish_events_batch(
        self,
        events: List[DomainEvent],
        topic: Optional[str] = None,
        context: Optional[ServiceContext] = None
    ) -> None:
        """Publish multiple events with batch processing."""
        async with self.operation_context("publish_events_batch", context):
            try:
                await self.publisher.publish_events_batch(events, topic)
                self.events_published += len(events)

                self.logger.info(
                    f"Batch events published: {len(events)} events",
                    extra={
                        'event_count': len(events),
                        'topic': topic,
                        'event_types': [e.event_type.value for e in events[:5]]  # First 5 for logging
                    }
                )

            except Exception as e:
                self.events_failed += len(events)
                self.logger.error(
                    f"Failed to publish batch events: {len(events)} events",
                    exc_info=True,
                    extra={
                        'event_count': len(events),
                        'error': str(e)
                    }
                )
                raise

    async def subscribe_to_events(
        self,
        topic: str,
        handler: Callable,
        event_types: Optional[List[EventType]] = None,
        context: Optional[ServiceContext] = None
    ) -> None:
        """Subscribe to events on a topic."""
        async with self.operation_context("subscribe_to_events", context):
            await self.subscriber.subscribe_to_topic(topic, handler, event_types)

            self.logger.info(
                f"Subscribed to events on topic: {topic}",
                extra={
                    'topic': topic,
                    'event_types': [et.value for et in event_types] if event_types else None
                }
            )

    async def subscribe_to_event_type(
        self,
        event_type: EventType,
        handler: Callable,
        topic: Optional[str] = None,
        context: Optional[ServiceContext] = None
    ) -> None:
        """Subscribe to specific event types."""
        async with self.operation_context("subscribe_to_event_type", context):
            await self.subscriber.subscribe_to_event_type(event_type, handler, topic)

            self.logger.info(
                f"Subscribed to event type: {event_type.value}",
                extra={
                    'event_type': event_type.value,
                    'topic': topic
                }
            )

    async def _send_to_dead_letter_queue(self, event: DomainEvent, error: str) -> None:
        """Send failed event to dead letter queue."""
        try:
            if self.dead_letter_queue:
                await self.dead_letter_queue.add_event(event, error)
                self.dead_letter_count += 1

                self.logger.warning(
                    f"Event sent to dead letter queue: {event.event_type.value}",
                    extra={
                        'event_id': event.event_id,
                        'event_type': event.event_type.value,
                        'error': error
                    }
                )
        except Exception as dlq_error:
            self.logger.error(
                f"Failed to send event to dead letter queue: {dlq_error}",
                exc_info=True
            )

    async def get_statistics(self) -> Dict[str, Any]:
        """Get event publishing statistics."""
        return {
            'events_published': self.events_published,
            'events_failed': self.events_failed,
            'events_retried': self.events_retried,
            'dead_letter_count': self.dead_letter_count,
            'subscription_count': self.subscriber.get_subscription_count(),
            'success_rate': (self.events_published / max(1, self.events_published + self.events_failed))
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = await super().health_check()

        # Add event publishing specific health info
        try:
            stats = await self.get_statistics()
            bus_health = await self.event_bus.health_check()

            health['event_publishing'] = {
                'statistics': stats,
                'event_bus_health': bus_health,
                'dead_letter_queue_available': self.dead_letter_queue is not None
            }

        except Exception as e:
            health['event_publishing'] = {'error': str(e)}

        return health
