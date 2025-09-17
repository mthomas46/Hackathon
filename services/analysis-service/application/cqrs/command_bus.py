"""Command bus for CQRS pattern."""

from typing import Dict, Type, Any
from abc import ABC, abstractmethod

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


class CommandBus:
    """Command bus for dispatching commands to handlers."""

    def __init__(self):
        """Initialize command bus with empty handler registry."""
        self._handlers: Dict[Type, Any] = {}

    def register_handler(self, command_type: Type, handler: Any) -> None:
        """Register a command handler."""
        self._handlers[command_type] = handler

    async def send(self, command: Any) -> Any:
        """Send a command to its handler."""
        command_type = type(command)

        if command_type not in self._handlers:
            raise ValueError(f"No handler registered for command: {command_type.__name__}")

        handler = self._handlers[command_type]
        return await handler.handle(command)

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
