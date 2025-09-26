"""Event repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..entities.event import Event
from ..value_objects.event_id import EventId
from ..value_objects.event_type import EventType


class EventRepository(ABC):
    """Abstract repository for event persistence."""

    @abstractmethod
    async def save(self, event: Event) -> None:
        """Save an event."""
        pass

    @abstractmethod
    async def find_by_id(self, event_id: EventId) -> Optional[Event]:
        """Find an event by ID."""
        pass

    @abstractmethod
    async def find_by_type(self, event_type: EventType) -> List[Event]:
        """Find events by type."""
        pass

    @abstractmethod
    async def find_by_source(self, source: str) -> List[Event]:
        """Find events by source."""
        pass

    @abstractmethod
    async def find_since(self, since: datetime) -> List[Event]:
        """Find events since a specific time."""
        pass

    @abstractmethod
    async def find_all(self) -> List[Event]:
        """Find all events."""
        pass
