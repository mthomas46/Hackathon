"""Health Status Value Object."""

from enum import Enum


class HealthStatus(str, Enum):
    """
    Health status for Gateway's dependency checks.
    """
    
    HEALTHY = "healthy"            # All systems operational
    DEGRADED = "degraded"          # Some features unavailable
    UNHEALTHY = "unhealthy"        # Critical failures
    UNKNOWN = "unknown"            # Cannot determine status
    
    @property
    def is_operational(self) -> bool:
        """Check if service can handle requests."""
        return self in {
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
        }

