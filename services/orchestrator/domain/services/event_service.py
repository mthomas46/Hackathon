"""Event domain service."""

from typing import List
from datetime import datetime

from ..entities.event import Event
from ..repositories.event_repository import EventRepository
from ..value_objects.event_id import EventId
from ..value_objects.event_type import EventType


class EventService:
    """Domain service for event publishing and handling."""

    def __init__(self, event_repository: EventRepository):
        self.event_repository = event_repository

    async def publish_event(
        self,
        event_type: EventType,
        source: str,
        data: dict,
        metadata: dict = None
    ) -> Event:
        """Publish a new event."""
        event_id = EventId.generate()
        event = Event(
            id=event_id,
            type=event_type,
            source=source,
            data=data,
            metadata=metadata or {}
        )

        event.validate()
        await self.event_repository.save(event)

        return event

    async def get_event(self, event_id: EventId) -> Event:
        """Get an event by ID."""
        event = await self.event_repository.find_by_id(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        return event

    async def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Get events by type."""
        return await self.event_repository.find_by_type(event_type)

    async def get_events_by_source(self, source: str) -> List[Event]:
        """Get events by source."""
        return await self.event_repository.find_by_source(source)

    async def get_recent_events(self, hours: int = 24) -> List[Event]:
        """Get events from the last N hours."""
        since = datetime.now().replace(hour=datetime.now().hour - hours)
        return await self.event_repository.find_since(since)

    async def get_all_events(self) -> List[Event]:
        """Get all events."""
        return await self.event_repository.find_all()
