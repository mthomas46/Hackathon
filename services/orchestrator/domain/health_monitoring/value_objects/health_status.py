"""Health Status Value Object"""

from enum import Enum
from typing import Optional


class HealthStatus(Enum):
    """Enumeration of possible health statuses."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"

    @property
    def is_healthy(self) -> bool:
        """Check if status indicates healthy state."""
        return self in (HealthStatus.HEALTHY,)

    @property
    def is_operational(self) -> bool:
        """Check if status indicates operational state."""
        return self in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)

    @classmethod
    def from_string(cls, value: str) -> 'HealthStatus':
        """Create HealthStatus from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.UNKNOWN

    def __str__(self) -> str:
        return self.value
