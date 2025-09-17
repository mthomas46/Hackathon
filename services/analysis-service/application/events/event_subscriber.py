"""Event Subscriber - Handles application events."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

from .application_events import ApplicationEvent, EventType


logger = logging.getLogger(__name__)


class EventHandler(ABC):
    """Abstract base class for event handlers."""

    @abstractmethod
    async def handle(self, event: ApplicationEvent) -> None:
        """Handle an event."""
        pass

    @property
    @abstractmethod
    def event_types(self) -> List[EventType]:
        """Return list of event types this handler can process."""
        pass


class EventSubscriber:
    """Event subscriber that manages event handlers."""

    def __init__(self, max_workers: int = 5):
        """Initialize subscriber."""
        self.handlers: Dict[EventType, List[EventHandler]] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = False
        self._handler_task: Optional[asyncio.Task] = None

    async def subscribe(self, handler: EventHandler) -> None:
        """Subscribe a handler to events."""
        for event_type in handler.event_types:
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(handler)

        logger.info(f"Subscribed handler {handler.__class__.__name__} to {len(handler.event_types)} event types")

    async def unsubscribe(self, handler: EventHandler) -> None:
        """Unsubscribe a handler from events."""
        for event_type in handler.event_types:
            if event_type in self.handlers:
                self.handlers[event_type] = [
                    h for h in self.handlers[event_type] if h != handler
                ]

        logger.info(f"Unsubscribed handler {handler.__class__.__name__}")

    async def publish(self, event: ApplicationEvent) -> None:
        """Publish event to subscribed handlers."""
        if event.event_type not in self.handlers:
            logger.debug(f"No handlers for event type: {event.event_type.value}")
            return

        handlers = self.handlers[event.event_type]

        # Process handlers concurrently
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._handle_event(handler, event))
            tasks.append(task)

        # Wait for all handlers to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Handler {handlers[i].__class__.__name__} failed for event {event.event_id}: {result}",
                    exc_info=result
                )

    async def _handle_event(self, handler: EventHandler, event: ApplicationEvent) -> None:
        """Handle a single event with a handler."""
        try:
            await handler.handle(event)
        except Exception as e:
            logger.error(
                f"Error in handler {handler.__class__.__name__} for event {event.event_id}: {e}",
                exc_info=True
            )
            raise

    async def start(self) -> None:
        """Start the subscriber."""
        self._running = True
        logger.info("Event subscriber started")

    async def stop(self) -> None:
        """Stop the subscriber."""
        self._running = False
        if self._handler_task:
            self._handler_task.cancel()
            try:
                await self._handler_task
            except asyncio.CancelledError:
                pass

        self.executor.shutdown(wait=True)
        logger.info("Event subscriber stopped")

    def get_handler_count(self, event_type: Optional[EventType] = None) -> int:
        """Get count of handlers for an event type or total."""
        if event_type:
            return len(self.handlers.get(event_type, []))
        return sum(len(handlers) for handlers in self.handlers.values())


# Concrete Event Handlers

class LoggingEventHandler(EventHandler):
    """Event handler that logs events."""

    def __init__(self, log_level: int = logging.INFO):
        """Initialize logging handler."""
        self.log_level = log_level

    @property
    def event_types(self) -> List[EventType]:
        """Handle all event types."""
        return list(EventType)

    async def handle(self, event: ApplicationEvent) -> None:
        """Log the event."""
        logger.log(
            self.log_level,
            f"Event: {event.event_type.value} | ID: {event.event_id} | Correlation: {event.correlation_id}",
            extra={
                'event_type': event.event_type.value,
                'event_id': event.event_id,
                'correlation_id': event.correlation_id,
                'timestamp': event.timestamp.isoformat(),
                'metadata': event.metadata
            }
        )


class MetricsEventHandler(EventHandler):
    """Event handler that collects metrics."""

    def __init__(self):
        """Initialize metrics handler."""
        self.event_counts: Dict[str, int] = {}
        self.processing_times: List[float] = []

    @property
    def event_types(self) -> List[EventType]:
        """Handle all event types."""
        return list(EventType)

    async def handle(self, event: ApplicationEvent) -> None:
        """Collect metrics for the event."""
        event_type = event.event_type.value

        # Count events
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1

        # Track processing time if available
        if hasattr(event, 'execution_time_seconds'):
            self.processing_times.append(event.execution_time_seconds)

        logger.debug(f"Metrics collected for event: {event_type}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return {
            'event_counts': self.event_counts.copy(),
            'total_events': sum(self.event_counts.values()),
            'processing_times': self.processing_times.copy() if self.processing_times else [],
            'avg_processing_time': sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        }


class NotificationEventHandler(EventHandler):
    """Event handler that sends notifications."""

    def __init__(self, notification_service=None):
        """Initialize notification handler."""
        self.notification_service = notification_service

    @property
    def event_types(self) -> List[EventType]:
        """Handle specific event types that require notifications."""
        return [
            EventType.ANALYSIS_FAILED,
            EventType.FINDING_CREATED,
            EventType.WORKFLOW_TRIGGERED
        ]

    async def handle(self, event: ApplicationEvent) -> None:
        """Send notification for the event."""
        if not self.notification_service:
            logger.warning("Notification service not configured")
            return

        # Create notification based on event type
        if event.event_type == EventType.ANALYSIS_FAILED:
            await self._notify_analysis_failed(event)
        elif event.event_type == EventType.FINDING_CREATED:
            await self._notify_finding_created(event)
        elif event.event_type == EventType.WORKFLOW_TRIGGERED:
            await self._notify_workflow_triggered(event)

    async def _notify_analysis_failed(self, event: ApplicationEvent) -> None:
        """Notify about failed analysis."""
        message = f"Analysis failed: {getattr(event, 'error_message', 'Unknown error')}"
        await self.notification_service.send_notification(
            recipient="admin@company.com",
            subject="Analysis Service - Analysis Failed",
            message=message,
            metadata={'event_id': event.event_id}
        )

    async def _notify_finding_created(self, event: ApplicationEvent) -> None:
        """Notify about new finding."""
        severity = getattr(event, 'severity', 'unknown')
        if severity in ['critical', 'high']:
            message = f"High priority finding created: {getattr(event, 'description', '')}"
            await self.notification_service.send_notification(
                recipient="team@company.com",
                subject=f"Analysis Service - {severity.title()} Finding",
                message=message,
                metadata={'event_id': event.event_id}
            )

    async def _notify_workflow_triggered(self, event: ApplicationEvent) -> None:
        """Notify about triggered workflow."""
        message = f"Workflow triggered: {getattr(event, 'trigger_type', 'unknown')}"
        await self.notification_service.send_notification(
            recipient="devops@company.com",
            subject="Analysis Service - Workflow Triggered",
            message=message,
            metadata={'event_id': event.event_id}
        )


class AuditEventHandler(EventHandler):
    """Event handler that creates audit logs."""

    def __init__(self, audit_service=None):
        """Initialize audit handler."""
        self.audit_service = audit_service

    @property
    def event_types(self) -> List[EventType]:
        """Handle all event types for audit."""
        return list(EventType)

    async def handle(self, event: ApplicationEvent) -> None:
        """Create audit entry for the event."""
        if not self.audit_service:
            return

        audit_entry = {
            'event_id': event.event_id,
            'event_type': event.event_type.value,
            'timestamp': event.timestamp.isoformat(),
            'correlation_id': event.correlation_id,
            'user_id': event.metadata.get('user_id'),
            'session_id': event.metadata.get('session_id'),
            'ip_address': event.metadata.get('ip_address'),
            'user_agent': event.metadata.get('user_agent'),
            'details': event.to_dict()
        }

        await self.audit_service.log_event(audit_entry)


class EventHandlerFactory:
    """Factory for creating event handlers."""

    @staticmethod
    def create_logging_handler(log_level: int = logging.INFO) -> EventHandler:
        """Create logging event handler."""
        return LoggingEventHandler(log_level)

    @staticmethod
    def create_metrics_handler() -> EventHandler:
        """Create metrics event handler."""
        return MetricsEventHandler()

    @staticmethod
    def create_notification_handler(notification_service=None) -> EventHandler:
        """Create notification event handler."""
        return NotificationEventHandler(notification_service)

    @staticmethod
    def create_audit_handler(audit_service=None) -> EventHandler:
        """Create audit event handler."""
        return AuditEventHandler(audit_service)

    @staticmethod
    def create_handlers_from_config(config: Dict[str, Any]) -> List[EventHandler]:
        """Create handlers from configuration."""
        handlers = []

        if config.get('logging', {}).get('enabled', True):
            handlers.append(EventHandlerFactory.create_logging_handler(
                config['logging'].get('level', logging.INFO)
            ))

        if config.get('metrics', {}).get('enabled', True):
            handlers.append(EventHandlerFactory.create_metrics_handler())

        if config.get('notifications', {}).get('enabled', False):
            handlers.append(EventHandlerFactory.create_notification_handler(
                config['notifications'].get('service')
            ))

        if config.get('audit', {}).get('enabled', False):
            handlers.append(EventHandlerFactory.create_audit_handler(
                config['audit'].get('service')
            ))

        return handlers
