"""Trace Status Value Object"""

from enum import Enum


class TraceStatus(Enum):
    """Enumeration of possible distributed trace statuses."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

    @property
    def is_final(self) -> bool:
        """Check if trace is in final state."""
        return self in (TraceStatus.COMPLETED, TraceStatus.FAILED, TraceStatus.TIMEOUT)

    @property
    def is_successful(self) -> bool:
        """Check if trace completed successfully."""
        return self == TraceStatus.COMPLETED

    def __str__(self) -> str:
        return self.value
