"""Command bus for CQRS pattern with event publishing."""

import logging
from typing import Dict, Type, Any, Optional, List
from abc import ABC, abstractmethod
from uuid import uuid4

from ..handlers.command_handlers import (
    CreateDocumentCommandHandler,
    UpdateDocumentCommandHandler,
    PerformAnalysisCommandHandler,
    CreateFindingCommandHandler,
    UpdateFindingCommandHandler,
    DeleteDocumentCommandHandler
)
from ..handlers.commands import (
    CreateDocumentCommand,
    UpdateDocumentCommand,
    PerformAnalysisCommand,
    CreateFindingCommand,
    UpdateFindingCommand,
    DeleteDocumentCommand
)
from ..events import EventBus, ApplicationEvent


logger = logging.getLogger(__name__)


class CommandBus:
    """Command bus for dispatching commands to handlers with event publishing."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize command bus with empty handler registry."""
        self._handlers: Dict[Type, Any] = {}
        self.event_bus = event_bus
        self._command_events: Dict[str, List[ApplicationEvent]] = {}

    def register_handler(self, command_type: Type, handler: Any) -> None:
        """Register a command handler."""
        self._handlers[command_type] = handler

    async def send(self, command: Any) -> Any:
        """Send a command to its handler and publish resulting events."""
        command_type = type(command)
        command_id = getattr(command, 'command_id', str(uuid4()))

        if command_type not in self._handlers:
            raise ValueError(f"No handler registered for command: {command_type.__name__}")

        try:
            # Execute command
            handler = self._handlers[command_type]
            result = await handler.handle(command)

            # Publish events if available
            await self._publish_command_events(command, result, command_id)

            logger.info(f"Command executed successfully: {command_type.__name__} ({command_id})")
            return result

        except Exception as e:
            # Publish failure event
            await self._publish_command_failure_event(command, e, command_id)
            logger.error(f"Command failed: {command_type.__name__} ({command_id}): {e}", exc_info=True)
            raise

    async def _publish_command_events(self, command: Any, result: Any, command_id: str) -> None:
        """Publish events resulting from command execution."""
        if not self.event_bus:
            return

        events_to_publish = []

        # Extract events from result if available
        if hasattr(result, 'events') and result.events:
            events_to_publish.extend(result.events)

        # Create standard command completion event
        from ..events.application_events import AnalysisCompletedEvent

        completion_event = AnalysisCompletedEvent(
            event_id=str(uuid4()),
            correlation_id=command_id,
            document_id=getattr(command, 'document_id', ''),
            analysis_type=getattr(command, 'analysis_type', 'command'),
            result={'command_type': command.__class__.__name__, 'success': True},
            execution_time_seconds=0.0,  # Could be tracked
            findings_count=0,
            metadata={
                'command_id': command_id,
                'user_id': getattr(command, 'user_id', None),
                'session_id': getattr(command, 'session_id', None)
            }
        )
        events_to_publish.append(completion_event)

        # Publish all events
        for event in events_to_publish:
            await self.event_bus.publish(event)

        # Store events for this command
        self._command_events[command_id] = events_to_publish

    async def _publish_command_failure_event(self, command: Any, error: Exception, command_id: str) -> None:
        """Publish command failure event."""
        if not self.event_bus:
            return

        from ..events.application_events import AnalysisFailedEvent

        failure_event = AnalysisFailedEvent(
            event_id=str(uuid4()),
            correlation_id=command_id,
            document_id=getattr(command, 'document_id', ''),
            analysis_type=getattr(command, 'analysis_type', 'command'),
            error_message=str(error),
            error_code=error.__class__.__name__,
            retry_count=getattr(command, 'retry_count', 0),
            metadata={
                'command_id': command_id,
                'command_type': command.__class__.__name__,
                'user_id': getattr(command, 'user_id', None),
                'session_id': getattr(command, 'session_id', None)
            }
        )

        await self.event_bus.publish(failure_event)

    def get_command_events(self, command_id: str) -> List[ApplicationEvent]:
        """Get events published for a specific command."""
        return self._command_events.get(command_id, [])

    def clear_command_events(self, command_id: str) -> None:
        """Clear events for a specific command."""
        self._command_events.pop(command_id, None)

    def register_default_handlers(self,
                                  create_document_handler: CreateDocumentCommandHandler,
                                  update_document_handler: UpdateDocumentCommandHandler,
                                  perform_analysis_handler: PerformAnalysisCommandHandler,
                                  create_finding_handler: CreateFindingCommandHandler,
                                  update_finding_handler: UpdateFindingCommandHandler,
                                  delete_document_handler: DeleteDocumentCommandHandler) -> None:
        """Register all default command handlers."""
        self.register_handler(CreateDocumentCommand, create_document_handler)
        self.register_handler(UpdateDocumentCommand, update_document_handler)
        self.register_handler(PerformAnalysisCommand, perform_analysis_handler)
        self.register_handler(CreateFindingCommand, create_finding_handler)
        self.register_handler(UpdateFindingCommand, update_finding_handler)
        self.register_handler(DeleteDocumentCommand, delete_document_handler)

    def get_registered_commands(self) -> list[str]:
        """Get list of registered command types."""
        return [cmd.__name__ for cmd in self._handlers.keys()]

    def has_handler(self, command_type: Type) -> bool:
        """Check if a handler is registered for the command type."""
        return command_type in self._handlers
