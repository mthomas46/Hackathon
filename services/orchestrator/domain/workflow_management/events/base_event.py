"""Base Domain Event"""

from abc import ABC
from typing import Any, Dict
from datetime import datetime
import uuid


class DomainEvent(ABC):
    """Base class for all domain events."""

    def __init__(self, event_type: str, aggregate_id: str, event_data: Dict[str, Any]):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.event_data = event_data
        self.timestamp = datetime.utcnow()
        self.version = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "event_data": self.event_data,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version
        }
