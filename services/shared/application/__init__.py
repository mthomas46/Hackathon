"""Application Layer - Use Cases and Business Workflows.

This module contains the application layer components following Domain-Driven Design (DDD)
principles. It orchestrates domain objects to fulfill business use cases.

Key Components:
- Use Cases: Business operation workflows
- Commands: Write operations that change state
- Queries: Read operations that return data
- Command/Query Handlers: Process commands and queries

Usage:
    from services.shared.application import (
        UseCase, Command, Query,
        CommandHandler, QueryHandler
    )
"""

from typing import Any, Dict, List, Optional, Protocol, TypeVar
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class UseCase(ABC):
    """Base class for application use cases."""

    @abstractmethod
    async def execute(self, request: Any) -> Any:
        """Execute the use case with the given request."""
        pass


class Command:
    """Base class for write commands."""
    pass


class Query:
    """Base class for read queries."""
    pass


class CommandHandler(Protocol[T]):
    """Protocol for command handlers."""

    async def handle(self, command: T) -> Any:
        """Handle a command."""
        ...


class QueryHandler(Protocol[T]):
    """Protocol for query handlers."""

    async def handle(self, query: T) -> Any:
        """Handle a query."""
        ...


class ApplicationService:
    """Base class for application services that coordinate domain objects."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _validate_request(self, request: Any) -> None:
        """Validate incoming request."""
        pass

    async def _authorize_request(self, request: Any) -> None:
        """Check authorization for the request."""
        pass
