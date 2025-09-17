"""Event Router - Routes events to appropriate handlers based on rules."""

import asyncio
import re
from typing import Any, Dict, List, Optional, Callable, Pattern
from abc import ABC, abstractmethod

from .event_bus import DomainEvent, EventEnvelope, EventType
from .event_handlers import EventHandler, EventHandlerRegistry


class EventRouter(ABC):
    """Abstract base class for event routers."""

    def __init__(self, handler_registry: EventHandlerRegistry):
        """Initialize event router."""
        self.handler_registry = handler_registry

    @abstractmethod
    async def route_event(self, envelope: EventEnvelope) -> List[EventHandler]:
        """Route event to appropriate handlers."""
        pass

    @abstractmethod
    def add_route(self, pattern: str, handler: EventHandler) -> None:
        """Add routing rule."""
        pass

    @abstractmethod
    def remove_route(self, pattern: str) -> bool:
        """Remove routing rule."""
        pass


class TopicBasedEventRouter(EventRouter):
    """Routes events based on topic patterns."""

    def __init__(self, handler_registry: EventHandlerRegistry):
        """Initialize topic-based router."""
        super().__init__(handler_registry)
        self.routes: Dict[str, List[EventHandler]] = {}
        self._compiled_patterns: Dict[str, Pattern] = {}

    async def route_event(self, envelope: EventEnvelope) -> List[EventHandler]:
        """Route event based on topic."""
        matching_handlers = []

        for pattern, handlers in self.routes.items():
            if self._matches_pattern(envelope.topic, pattern):
                # Get handlers that can handle this event type
                capable_handlers = self.handler_registry.get_handlers_for_event(
                    envelope.event, envelope.topic
                )

                # Filter to only those registered for this pattern
                for handler in handlers:
                    if handler in capable_handlers:
                        matching_handlers.append(handler)

        return matching_handlers

    def add_route(self, pattern: str, handler: EventHandler) -> None:
        """Add topic-based routing rule."""
        if pattern not in self.routes:
            self.routes[pattern] = []

        if handler not in self.routes[pattern]:
            self.routes[pattern].append(handler)

        # Compile regex pattern for efficiency
        self._compile_pattern(pattern)

    def remove_route(self, pattern: str) -> bool:
        """Remove routing rule."""
        if pattern in self.routes:
            del self.routes[pattern]
            self._compiled_patterns.pop(pattern, None)
            return True
        return False

    def _matches_pattern(self, topic: str, pattern: str) -> bool:
        """Check if topic matches pattern."""
        compiled_pattern = self._compiled_patterns.get(pattern)
        if compiled_pattern:
            return bool(compiled_pattern.match(topic))

        # Fallback to simple wildcard matching
        return self._simple_match(topic, pattern)

    def _compile_pattern(self, pattern: str) -> None:
        """Compile regex pattern from wildcard pattern."""
        # Convert wildcard pattern to regex
        regex_pattern = re.escape(pattern)
        regex_pattern = regex_pattern.replace(r'\*', '.*')
        regex_pattern = f"^{regex_pattern}$"

        try:
            self._compiled_patterns[pattern] = re.compile(regex_pattern, re.IGNORECASE)
        except re.error:
            # If regex compilation fails, remove the pattern
            self._compiled_patterns.pop(pattern, None)

    def _simple_match(self, topic: str, pattern: str) -> bool:
        """Simple wildcard matching fallback."""
        # Handle exact match
        if pattern == topic:
            return True

        # Handle wildcard patterns
        if '*' in pattern:
            # Convert to regex for matching
            regex_pattern = pattern.replace('*', '.*')
            return bool(re.match(f"^{regex_pattern}$", topic, re.IGNORECASE))

        return False

    def get_routes(self) -> Dict[str, List[str]]:
        """Get all routing rules."""
        return {
            pattern: [h.__class__.__name__ for h in handlers]
            for pattern, handlers in self.routes.items()
        }


class TypeBasedEventRouter(EventRouter):
    """Routes events based on event type."""

    def __init__(self, handler_registry: EventHandlerRegistry):
        """Initialize type-based router."""
        super().__init__(handler_registry)
        self.type_routes: Dict[EventType, List[EventHandler]] = {}

    async def route_event(self, envelope: EventEnvelope) -> List[EventHandler]:
        """Route event based on event type."""
        event_type = envelope.event.event_type
        handlers = self.type_routes.get(event_type, [])

        # Filter to handlers that can actually handle this event
        capable_handlers = []
        for handler in handlers:
            if handler.can_handle(envelope.event):
                capable_handlers.append(handler)

        return capable_handlers

    def add_route(self, event_type: str, handler: EventHandler) -> None:
        """Add event type-based routing rule."""
        # Convert string to EventType if needed
        if isinstance(event_type, str):
            try:
                event_type = EventType(event_type)
            except ValueError:
                raise ValueError(f"Invalid event type: {event_type}")

        if event_type not in self.type_routes:
            self.type_routes[event_type] = []

        if handler not in self.type_routes[event_type]:
            self.type_routes[event_type].append(handler)

    def remove_route(self, event_type: str) -> bool:
        """Remove routing rule."""
        if isinstance(event_type, str):
            try:
                event_type = EventType(event_type)
            except ValueError:
                return False

        if event_type in self.type_routes:
            del self.type_routes[event_type]
            return True
        return False

    def get_routes(self) -> Dict[str, List[str]]:
        """Get all routing rules."""
        return {
            event_type.value: [h.__class__.__name__ for h in handlers]
            for event_type, handlers in self.type_routes.items()
        }


class CompositeEventRouter(EventRouter):
    """Combines multiple routing strategies."""

    def __init__(self, handler_registry: EventHandlerRegistry):
        """Initialize composite router."""
        super().__init__(handler_registry)
        self.routers: List[EventRouter] = []

    def add_router(self, router: EventRouter) -> None:
        """Add a router to the composite."""
        self.routers.append(router)

    async def route_event(self, envelope: EventEnvelope) -> List[EventHandler]:
        """Route event through all routers."""
        all_handlers = []

        for router in self.routers:
            handlers = await router.route_event(envelope)
            # Avoid duplicates
            for handler in handlers:
                if handler not in all_handlers:
                    all_handlers.append(handler)

        return all_handlers

    def add_route(self, pattern: str, handler: EventHandler) -> None:
        """Add route to all routers that support it."""
        for router in self.routers:
            try:
                router.add_route(pattern, handler)
            except (AttributeError, ValueError):
                # Router doesn't support this type of route
                continue

    def remove_route(self, pattern: str) -> bool:
        """Remove route from all routers."""
        removed = False
        for router in self.routers:
            try:
                if router.remove_route(pattern):
                    removed = True
            except (AttributeError, ValueError):
                continue
        return removed

    def get_routes(self) -> Dict[str, Any]:
        """Get routes from all routers."""
        routes = {}
        for i, router in enumerate(self.routers):
            router_name = router.__class__.__name__
            routes[router_name] = router.get_routes()
        return routes


class ConditionalEventRouter(EventRouter):
    """Routes events based on conditions."""

    def __init__(
        self,
        handler_registry: EventHandlerRegistry,
        condition: Callable[[EventEnvelope], bool]
    ):
        """Initialize conditional router."""
        super().__init__(handler_registry)
        self.condition = condition
        self.true_router: Optional[EventRouter] = None
        self.false_router: Optional[EventRouter] = None

    def set_true_router(self, router: EventRouter) -> None:
        """Set router for when condition is true."""
        self.true_router = router

    def set_false_router(self, router: EventRouter) -> None:
        """Set router for when condition is false."""
        self.false_router = router

    async def route_event(self, envelope: EventEnvelope) -> List[EventHandler]:
        """Route event based on condition."""
        if self.condition(envelope):
            return await self.true_router.route_event(envelope) if self.true_router else []
        else:
            return await self.false_router.route_event(envelope) if self.false_router else []

    def add_route(self, pattern: str, handler: EventHandler) -> None:
        """Add route to both routers."""
        if self.true_router:
            self.true_router.add_route(pattern, handler)
        if self.false_router:
            self.false_router.add_route(pattern, handler)

    def remove_route(self, pattern: str) -> bool:
        """Remove route from both routers."""
        removed_true = self.true_router.remove_route(pattern) if self.true_router else False
        removed_false = self.false_router.remove_route(pattern) if self.false_router else False
        return removed_true or removed_false


class EventRouterFactory:
    """Factory for creating event routers."""

    @staticmethod
    def create_topic_router(handler_registry: EventHandlerRegistry) -> TopicBasedEventRouter:
        """Create topic-based router."""
        return TopicBasedEventRouter(handler_registry)

    @staticmethod
    def create_type_router(handler_registry: EventHandlerRegistry) -> TypeBasedEventRouter:
        """Create type-based router."""
        return TypeBasedEventRouter(handler_registry)

    @staticmethod
    def create_composite_router(handler_registry: EventHandlerRegistry) -> CompositeEventRouter:
        """Create composite router with both topic and type routing."""
        composite = CompositeEventRouter(handler_registry)
        composite.add_router(TopicBasedEventRouter(handler_registry))
        composite.add_router(TypeBasedEventRouter(handler_registry))
        return composite

    @staticmethod
    def create_conditional_router(
        handler_registry: EventHandlerRegistry,
        condition: Callable[[EventEnvelope], bool]
    ) -> ConditionalEventRouter:
        """Create conditional router."""
        return ConditionalEventRouter(handler_registry, condition)


class EventDispatcher:
    """Dispatches events to handlers using routers."""

    def __init__(self, router: EventRouter):
        """Initialize event dispatcher."""
        self.router = router
        self._processing_stats = {
            'events_processed': 0,
            'handlers_called': 0,
            'processing_time': 0.0,
            'errors_count': 0
        }

    async def dispatch(self, envelope: EventEnvelope) -> Dict[str, Any]:
        """Dispatch event to appropriate handlers."""
        start_time = asyncio.get_event_loop().time()

        try:
            # Route event to handlers
            handlers = await self.router.route_event(envelope)

            if not handlers:
                return {
                    'status': 'no_handlers',
                    'handlers_called': 0,
                    'processing_time': 0.0
                }

            # Call all handlers
            handler_results = []
            for handler in handlers:
                try:
                    await handler.handle(envelope.event, envelope)
                    handler_results.append({
                        'handler': handler.__class__.__name__,
                        'status': 'success'
                    })
                except Exception as e:
                    handler_results.append({
                        'handler': handler.__class__.__name__,
                        'status': 'error',
                        'error': str(e)
                    })
                    self._processing_stats['errors_count'] += 1

            processing_time = asyncio.get_event_loop().time() - start_time

            # Update stats
            self._processing_stats['events_processed'] += 1
            self._processing_stats['handlers_called'] += len(handlers)
            self._processing_stats['processing_time'] += processing_time

            return {
                'status': 'processed',
                'handlers_called': len(handlers),
                'processing_time': processing_time,
                'handler_results': handler_results
            }

        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            self._processing_stats['errors_count'] += 1

            return {
                'status': 'error',
                'error': str(e),
                'processing_time': processing_time,
                'handlers_called': 0
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics."""
        return self._processing_stats.copy()

    def reset_stats(self) -> None:
        """Reset dispatcher statistics."""
        self._processing_stats = {
            'events_processed': 0,
            'handlers_called': 0,
            'processing_time': 0.0,
            'errors_count': 0
        }


# Common routing conditions
class RoutingConditions:
    """Common routing conditions."""

    @staticmethod
    def event_type_is(event_type: EventType) -> Callable[[EventEnvelope], bool]:
        """Condition that matches specific event type."""
        return lambda envelope: envelope.event.event_type == event_type

    @staticmethod
    def topic_matches(pattern: str) -> Callable[[EventEnvelope], bool]:
        """Condition that matches topic pattern."""
        def condition(envelope: EventEnvelope) -> bool:
            return bool(re.match(pattern, envelope.topic, re.IGNORECASE))
        return condition

    @staticmethod
    def priority_above(level: int) -> Callable[[EventEnvelope], bool]:
        """Condition that matches events above priority level."""
        return lambda envelope: envelope.event.priority.value >= level

    @staticmethod
    def has_metadata_key(key: str) -> Callable[[EventEnvelope], bool]:
        """Condition that matches events with specific metadata key."""
        return lambda envelope: key in envelope.event.metadata

    @staticmethod
    def metadata_value_equals(key: str, value: Any) -> Callable[[EventEnvelope], bool]:
        """Condition that matches events with specific metadata value."""
        return lambda envelope: envelope.event.metadata.get(key) == value

    @staticmethod
    def and_conditions(*conditions: Callable[[EventEnvelope], bool]) -> Callable[[EventEnvelope], bool]:
        """Combine conditions with AND logic."""
        return lambda envelope: all(condition(envelope) for condition in conditions)

    @staticmethod
    def or_conditions(*conditions: Callable[[EventEnvelope], bool]) -> Callable[[EventEnvelope], bool]:
        """Combine conditions with OR logic."""
        return lambda envelope: any(condition(envelope) for condition in conditions)
