"""Event type value object."""

from enum import Enum


class EventType(Enum):
    """Enumeration of possible event types."""

    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_CANCELLED = "workflow_cancelled"

    SERVICE_REGISTERED = "service_registered"
    SERVICE_HEALTH_CHECK = "service_health_check"
    SERVICE_FAILED = "service_failed"

    JOB_QUEUED = "job_queued"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
