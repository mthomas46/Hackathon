"""Event Bus - Central hub for event-driven communication."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from uuid import uuid4

from .event_publisher import EventPublisher, InMemoryEventPublisher
from .event_subscriber import EventSubscriber, EventHandler
from .application_events import ApplicationEvent


logger = logging.getLogger(__name__)


class EventBus:
    """Central event bus for application-wide event communication."""

    def __init__(
        self,
        publisher: Optional[EventPublisher] = None,
        subscriber: Optional[EventSubscriber] = None
    ):
        """Initialize event bus."""
        self.publisher = publisher or InMemoryEventPublisher()
        self.subscriber = subscriber or EventSubscriber()
        self._running = False

    async def start(self) -> None:
        """Start the event bus."""
        self._running = True
        await self.subscriber.start()
        logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop the event bus."""
        self._running = False
        await self.subscriber.stop()
        await self.publisher.close()
        logger.info("Event bus stopped")

    async def publish(self, event: ApplicationEvent) -> None:
        """Publish an event to all subscribers and external systems."""
        if not self._running:
            logger.warning("Event bus is not running, event not published")
            return

        try:
            # Publish to external systems
            await self.publisher.publish(event)

            # Publish to internal subscribers
            await self.subscriber.publish(event)

            logger.debug(f"Event published: {event.event_type.value} ({event.event_id})")

        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}", exc_info=True)
            raise

    async def publish_batch(self, events: List[ApplicationEvent]) -> None:
        """Publish multiple events."""
        if not self._running:
            logger.warning("Event bus is not running, events not published")
            return

        try:
            # Publish to external systems
            await self.publisher.publish_batch(events)

            # Publish to internal subscribers
            for event in events:
                await self.subscriber.publish(event)

            logger.debug(f"Batch published: {len(events)} events")

        except Exception as e:
            logger.error(f"Failed to publish batch: {e}", exc_info=True)
            raise

    async def subscribe(self, handler: EventHandler) -> None:
        """Subscribe a handler to events."""
        await self.subscriber.subscribe(handler)

    async def unsubscribe(self, handler: EventHandler) -> None:
        """Unsubscribe a handler from events."""
        await self.subscriber.unsubscribe(handler)

    def is_running(self) -> bool:
        """Check if event bus is running."""
        return self._running

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            'running': self._running,
            'publisher_type': self.publisher.__class__.__name__,
            'subscriber_handler_count': sum(
                self.subscriber.get_handler_count(event_type)
                for event_type in self.subscriber.handlers.keys()
            ),
            'event_types_handled': len(self.subscriber.handlers)
        }


class CQRSIntegration:
    """Integration layer between CQRS and Event Bus."""

    def __init__(self, event_bus: EventBus):
        """Initialize CQRS integration."""
        self.event_bus = event_bus
        self.command_handlers: Dict[str, callable] = {}
        self.query_handlers: Dict[str, callable] = {}

    def register_command_handler(self, command_type: str, handler: callable) -> None:
        """Register a command handler."""
        self.command_handlers[command_type] = handler

    def register_query_handler(self, query_type: str, handler: callable) -> None:
        """Register a query handler."""
        self.query_handlers[query_type] = handler

    async def handle_command(self, command: Any) -> Any:
        """Handle a command and publish resulting events."""
        command_type = command.__class__.__name__

        if command_type not in self.command_handlers:
            raise ValueError(f"No handler registered for command: {command_type}")

        handler = self.command_handlers[command_type]

        try:
            # Execute command
            result = await handler(command)

            # Publish events if command was successful
            if hasattr(result, 'events') and result.events:
                for event in result.events:
                    await self.event_bus.publish(event)

            return result

        except Exception as e:
            # Publish failure event
            failure_event = self._create_command_failure_event(command, e)
            await self.event_bus.publish(failure_event)
            raise

    async def handle_query(self, query: Any) -> Any:
        """Handle a query."""
        query_type = query.__class__.__name__

        if query_type not in self.query_handlers:
            raise ValueError(f"No handler registered for query: {query_type}")

        handler = self.query_handlers[query_type]
        return await handler(query)

    def _create_command_failure_event(self, command: Any, error: Exception) -> ApplicationEvent:
        """Create a command failure event."""
        from .application_events import AnalysisFailedEvent

        return AnalysisFailedEvent(
            event_id=str(uuid4()),
            correlation_id=getattr(command, 'correlation_id', None),
            document_id=getattr(command, 'document_id', ''),
            analysis_type=getattr(command, 'analysis_type', ''),
            error_message=str(error),
            error_code=error.__class__.__name__,
            metadata={
                'command_type': command.__class__.__name__,
                'command_data': str(command)
            }
        )


class EventSourcingIntegration:
    """Integration layer for event sourcing."""

    def __init__(self, event_bus: EventBus, event_store=None):
        """Initialize event sourcing integration."""
        self.event_bus = event_bus
        self.event_store = event_store
        self.aggregate_events: Dict[str, List[ApplicationEvent]] = {}

    async def save_events(self, aggregate_id: str, events: List[ApplicationEvent]) -> None:
        """Save events for an aggregate."""
        if self.event_store:
            await self.event_store.save_events(aggregate_id, events)

        # Store in memory for quick access
        if aggregate_id not in self.aggregate_events:
            self.aggregate_events[aggregate_id] = []
        self.aggregate_events[aggregate_id].extend(events)

        # Publish events
        for event in events:
            await self.event_bus.publish(event)

    async def load_events(self, aggregate_id: str) -> List[ApplicationEvent]:
        """Load events for an aggregate."""
        if self.event_store:
            return await self.event_store.load_events(aggregate_id)

        return self.aggregate_events.get(aggregate_id, [])

    async def replay_events(self, aggregate_id: str, handler: callable) -> None:
        """Replay events for an aggregate."""
        events = await self.load_events(aggregate_id)

        for event in events:
            await handler(event)


class EventBusFactory:
    """Factory for creating event bus instances."""

    @staticmethod
    def create_simple() -> EventBus:
        """Create simple in-memory event bus."""
        return EventBus()

    @staticmethod
    def create_with_handlers(handlers: List[EventHandler]) -> EventBus:
        """Create event bus with pre-registered handlers."""
        event_bus = EventBus()
        subscriber = event_bus.subscriber

        async def setup_handlers():
            for handler in handlers:
                await subscriber.subscribe(handler)

        # Note: This would need to be called after event loop is running
        return event_bus

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> EventBus:
        """Create event bus from configuration."""
        from .event_publisher import EventPublisherFactory
        from .event_subscriber import EventHandlerFactory

        # Create publisher
        publisher_config = config.get('publisher', {'type': 'in_memory'})
        publisher = EventPublisherFactory.create_from_config(publisher_config)

        # Create subscriber
        subscriber = EventSubscriber(
            max_workers=config.get('subscriber', {}).get('max_workers', 5)
        )

        # Create handlers
        handler_config = config.get('handlers', {})
        handlers = EventHandlerFactory.create_handlers_from_config(handler_config)

        event_bus = EventBus(publisher, subscriber)

        # Store handlers for later subscription
        event_bus._pending_handlers = handlers

        return event_bus

    @staticmethod
    async def start_event_bus(event_bus: EventBus) -> None:
        """Start event bus and subscribe handlers."""
        await event_bus.start()

        # Subscribe pending handlers
        if hasattr(event_bus, '_pending_handlers'):
            for handler in event_bus._pending_handlers:
                await event_bus.subscribe(handler)
            del event_bus._pending_handlers
