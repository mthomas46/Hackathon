"""Event Handlers - Event processing and handling infrastructure."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Type
from abc import ABC, abstractmethod
from functools import wraps

from .event_bus import DomainEvent, EventEnvelope, EventType


logger = logging.getLogger(__name__)


class EventHandler(ABC):
    """Abstract base class for event handlers."""

    def __init__(self, event_types: Optional[List[EventType]] = None):
        """Initialize event handler."""
        self.event_types = event_types or []
        self._stats = {
            'events_handled': 0,
            'errors_count': 0,
            'processing_time': 0.0
        }

    @abstractmethod
    async def handle(self, event: DomainEvent, envelope: EventEnvelope) -> None:
        """Handle the event."""
        pass

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if handler can handle this event type."""
        return not self.event_types or event.event_type in self.event_types

    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return self._stats.copy()

    def reset_stats(self) -> None:
        """Reset handler statistics."""
        self._stats = {
            'events_handled': 0,
            'errors_count': 0,
            'processing_time': 0.0
        }


class AsyncEventHandler(EventHandler):
    """Async event handler with timing and error handling."""

    async def handle(self, event: DomainEvent, envelope: EventEnvelope) -> None:
        """Handle event with timing and error handling."""
        start_time = asyncio.get_event_loop().time()

        try:
            await self._handle_event(event, envelope)
            self._stats['events_handled'] += 1

        except Exception as e:
            self._stats['errors_count'] += 1
            logger.error(
                f"Error handling event {event.event_id}: {e}",
                exc_info=True,
                extra={
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'correlation_id': event.correlation_id
                }
            )
            raise
        finally:
            processing_time = asyncio.get_event_loop().time() - start_time
            self._stats['processing_time'] += processing_time

    @abstractmethod
    async def _handle_event(self, event: DomainEvent, envelope: EventEnvelope) -> None:
        """Handle the actual event."""
        pass


class FunctionEventHandler(EventHandler):
    """Event handler that wraps a function."""

    def __init__(self, func: Callable, event_types: Optional[List[EventType]] = None):
        """Initialize function handler."""
        super().__init__(event_types)
        self.func = func

    async def handle(self, event: DomainEvent, envelope: EventEnvelope) -> None:
        """Handle event by calling the function."""
        start_time = asyncio.get_event_loop().time()

        try:
            if asyncio.iscoroutinefunction(self.func):
                await self.func(event, envelope)
            else:
                # Run sync function in thread pool
                await asyncio.get_event_loop().run_in_executor(None, self.func, event, envelope)

            self._stats['events_handled'] += 1

        except Exception as e:
            self._stats['errors_count'] += 1
            logger.error(
                f"Error in function handler for event {event.event_id}: {e}",
                exc_info=True,
                extra={
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'handler': str(self.func)
                }
            )
            raise
        finally:
            processing_time = asyncio.get_event_loop().time() - start_time
            self._stats['processing_time'] += processing_time


class ChainedEventHandler(EventHandler):
    """Event handler that chains multiple handlers."""

    def __init__(self, handlers: List[EventHandler]):
        """Initialize chained handler."""
        super().__init__()
        self.handlers = handlers

    async def handle(self, event: DomainEvent, envelope: EventEnvelope) -> None:
        """Handle event through all chained handlers."""
        start_time = asyncio.get_event_loop().time()

        try:
            for handler in self.handlers:
                if handler.can_handle(event):
                    await handler.handle(event, envelope)

            self._stats['events_handled'] += 1

        except Exception as e:
            self._stats['errors_count'] += 1
            logger.error(
                f"Error in chained handler for event {event.event_id}: {e}",
                exc_info=True,
                extra={
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'handler_count': len(self.handlers)
                }
            )
            raise
        finally:
            processing_time = asyncio.get_event_loop().time() - start_time
            self._stats['processing_time'] += processing_time

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if any handler can handle this event."""
        return any(handler.can_handle(event) for handler in self.handlers)


class ConditionalEventHandler(EventHandler):
    """Event handler that only handles events meeting certain conditions."""

    def __init__(
        self,
        handler: EventHandler,
        condition: Callable[[DomainEvent, EventEnvelope], bool]
    ):
        """Initialize conditional handler."""
        super().__init__(handler.event_types)
        self.handler = handler
        self.condition = condition

    async def handle(self, event: DomainEvent, envelope: EventEnvelope) -> None:
        """Handle event if condition is met."""
        if not self.condition(event, envelope):
            return

        start_time = asyncio.get_event_loop().time()

        try:
            await self.handler.handle(event, envelope)
            self._stats['events_handled'] += 1

        except Exception as e:
            self._stats['errors_count'] += 1
            logger.error(
                f"Error in conditional handler for event {event.event_id}: {e}",
                exc_info=True
            )
            raise
        finally:
            processing_time = asyncio.get_event_loop().time() - start_time
            self._stats['processing_time'] += processing_time

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if handler can handle this event type."""
        return self.handler.can_handle(event)


class RetryEventHandler(EventHandler):
    """Event handler with retry capability."""

    def __init__(
        self,
        handler: EventHandler,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        """Initialize retry handler."""
        super().__init__(handler.event_types)
        self.handler = handler
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor

    async def handle(self, event: DomainEvent, envelope: EventEnvelope) -> None:
        """Handle event with retry logic."""
        last_exception = None
        current_delay = self.retry_delay

        for attempt in range(self.max_retries + 1):
            try:
                await self.handler.handle(event, envelope)
                self._stats['events_handled'] += 1
                return

            except Exception as e:
                last_exception = e
                self._stats['errors_count'] += 1

                if attempt < self.max_retries:
                    logger.warning(
                        f"Handler failed for event {event.event_id}, retrying in {current_delay}s "
                        f"(attempt {attempt + 1}/{self.max_retries + 1})",
                        extra={
                            'event_id': event.event_id,
                            'attempt': attempt + 1,
                            'max_retries': self.max_retries,
                            'delay': current_delay
                        }
                    )

                    await asyncio.sleep(current_delay)
                    current_delay *= self.backoff_factor
                else:
                    logger.error(
                        f"Handler failed permanently for event {event.event_id} after {self.max_retries + 1} attempts",
                        exc_info=True,
                        extra={
                            'event_id': event.event_id,
                            'total_attempts': self.max_retries + 1
                        }
                    )

        # All retries exhausted
        raise last_exception


class EventHandlerRegistry:
    """Registry for managing event handlers."""

    def __init__(self):
        """Initialize handler registry."""
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._handler_classes: Dict[str, Type[EventHandler]] = {}

    def register_handler(
        self,
        name: str,
        handler: EventHandler,
        topics: Optional[List[str]] = None
    ) -> None:
        """Register an event handler."""
        if topics is None:
            # Auto-determine topics based on event types
            topics = self._get_topics_for_handler(handler)

        for topic in topics:
            if topic not in self._handlers:
                self._handlers[topic] = []
            self._handlers[topic].append(handler)

        logger.info(f"Registered handler '{name}' for topics: {topics}")

    def register_handler_class(
        self,
        name: str,
        handler_class: Type[EventHandler],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register an event handler class."""
        self._handler_classes[name] = handler_class

        if config:
            config['handler_name'] = name

        logger.info(f"Registered handler class '{name}': {handler_class.__name__}")

    def create_handler(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[EventHandler]:
        """Create handler instance from registered class."""
        if name not in self._handler_classes:
            return None

        handler_class = self._handler_classes[name]
        config = config or {}

        try:
            return handler_class(**config)
        except Exception as e:
            logger.error(f"Failed to create handler '{name}': {e}")
            return None

    def get_handlers_for_topic(self, topic: str) -> List[EventHandler]:
        """Get all handlers for a topic."""
        return self._handlers.get(topic, []).copy()

    def get_handlers_for_event(self, event: DomainEvent, topic: str) -> List[EventHandler]:
        """Get handlers that can handle a specific event."""
        handlers = self.get_handlers_for_topic(topic)
        return [h for h in handlers if h.can_handle(event)]

    def remove_handler(self, name: str, topic: str) -> bool:
        """Remove a handler from a topic."""
        if topic in self._handlers:
            original_count = len(self._handlers[topic])
            # Note: This is a simplified removal - in practice you'd need
            # to identify handlers by a unique identifier
            self._handlers[topic] = [
                h for h in self._handlers[topic]
                if not hasattr(h, '_name') or getattr(h, '_name') != name
            ]

            removed = len(self._handlers[topic]) < original_count
            if removed:
                logger.info(f"Removed handler '{name}' from topic '{topic}'")
            return removed

        return False

    def get_registered_topics(self) -> List[str]:
        """Get all registered topics."""
        return list(self._handlers.keys())

    def get_handler_stats(self) -> Dict[str, Any]:
        """Get statistics for all handlers."""
        stats = {}

        for topic, handlers in self._handlers.items():
            topic_stats = []
            for handler in handlers:
                handler_stats = handler.get_stats()
                handler_stats['handler_type'] = handler.__class__.__name__
                topic_stats.append(handler_stats)

            stats[topic] = {
                'handler_count': len(handlers),
                'handlers': topic_stats
            }

        return stats

    def reset_all_stats(self) -> None:
        """Reset statistics for all handlers."""
        for handlers in self._handlers.values():
            for handler in handlers:
                handler.reset_stats()

        logger.info("Reset statistics for all event handlers")

    def _get_topics_for_handler(self, handler: EventHandler) -> List[str]:
        """Get appropriate topics for a handler based on its event types."""
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

        topics = set()
        for event_type in handler.event_types:
            topic = topic_map.get(event_type, 'general.events')
            topics.add(topic)

        return list(topics) if topics else ['general.events']


# Decorator for creating event handlers
def event_handler(event_types: Optional[List[EventType]] = None):
    """Decorator to create event handler from function."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Attach metadata for handler creation
        wrapper._is_event_handler = True
        wrapper._event_types = event_types
        wrapper._handler_name = func.__name__

        return wrapper

    return decorator


def create_handler_from_function(func: Callable) -> FunctionEventHandler:
    """Create event handler from decorated function."""
    if hasattr(func, '_is_event_handler'):
        return FunctionEventHandler(func, getattr(func, '_event_types', None))
    else:
        return FunctionEventHandler(func)
