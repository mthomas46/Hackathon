"""Event domain entity."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from ..value_objects.event_id import EventId
from ..value_objects.event_type import EventType


@dataclass
class Event:
    """Domain entity representing an event in the system."""

    id: EventId
    type: EventType
    source: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def validate(self) -> None:
        """Validate the event according to domain rules."""
        if not self.source or not self.source.strip():
            raise ValueError("Event source cannot be empty")

        if not self.data:
            raise ValueError("Event must have data")

    def is_workflow_event(self) -> bool:
        """Check if this is a workflow-related event."""
        return self.type.value.startswith('workflow_')

    def is_service_event(self) -> bool:
        """Check if this is a service-related event."""
        return self.type.value.startswith('service_')

    def is_job_event(self) -> bool:
        """Check if this is a job-related event."""
        return self.type.value.startswith('job_')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': str(self.id),
            'type': str(self.type),
            'source': self.source,
            'data': self.data,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
