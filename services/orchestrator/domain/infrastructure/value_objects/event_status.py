"""Event Status Value Object"""

from enum import Enum


class EventStatus(Enum):
    """Enumeration of possible event processing statuses."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRIED = "retried"
    DLQ = "dlq"  # Dead Letter Queue
    EXPIRED = "expired"

    @property
    def is_final(self) -> bool:
        """Check if status indicates final state."""
        return self in (EventStatus.COMPLETED, EventStatus.DLQ, EventStatus.EXPIRED)

    @property
    def can_retry(self) -> bool:
        """Check if event can be retried."""
        return self in (EventStatus.FAILED, EventStatus.RETRIED)

    @property
    def is_successful(self) -> bool:
        """Check if status indicates success."""
        return self == EventStatus.COMPLETED

    def __str__(self) -> str:
        return self.value
