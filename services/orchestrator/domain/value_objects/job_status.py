"""Job status value object."""

from enum import Enum


class JobStatus(Enum):
    """Enumeration of possible job statuses."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
