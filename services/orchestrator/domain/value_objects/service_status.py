"""Service status value object."""

from enum import Enum


class ServiceStatus(Enum):
    """Enumeration of possible service statuses."""

    UNKNOWN = "unknown"
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    FAILED = "failed"

    def is_healthy(self) -> bool:
        """Check if this status represents a healthy state."""
        return self in [ServiceStatus.ACTIVE, ServiceStatus.REGISTERED]

    def is_unhealthy(self) -> bool:
        """Check if this status represents an unhealthy state."""
        return self in [ServiceStatus.FAILED, ServiceStatus.DEGRADED]
