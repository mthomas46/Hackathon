"""System Health Value Object"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .health_status import HealthStatus
from .service_health import ServiceHealth


class SystemHealth:
    """Value object representing the overall health status of the system."""

    def __init__(
        self,
        overall_status: HealthStatus,
        service_health: List[ServiceHealth],
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._overall_status = overall_status
        self._service_health = service_health.copy()
        self._timestamp = timestamp or datetime.utcnow()
        self._metadata = metadata or {}

    @property
    def overall_status(self) -> HealthStatus:
        """Get the overall system health status."""
        return self._overall_status

    @property
    def service_health(self) -> List[ServiceHealth]:
        """Get the health status of all services."""
        return self._service_health.copy()

    @property
    def timestamp(self) -> datetime:
        """Get the health check timestamp."""
        return self._timestamp

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the system health metadata."""
        return self._metadata.copy()

    @property
    def healthy_services_count(self) -> int:
        """Get the count of healthy services."""
        return len([s for s in self._service_health if s.is_healthy])

    @property
    def total_services_count(self) -> int:
        """Get the total count of services."""
        return len(self._service_health)

    @property
    def unhealthy_services(self) -> List[ServiceHealth]:
        """Get the list of unhealthy services."""
        return [s for s in self._service_health if not s.is_healthy]

    def get_service_health(self, service_name: str) -> ServiceHealth:
        """Get health status for a specific service."""
        for service in self._service_health:
            if service.service_name == service_name:
                return service
        # Return unknown health if service not found
        from .service_health import ServiceHealth
        return ServiceHealth(service_name, HealthStatus.UNKNOWN)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "overall_status": self._overall_status.value,
            "overall_healthy": self._overall_status.is_healthy,
            "timestamp": self._timestamp.isoformat(),
            "services": {
                service.service_name: service.to_dict()
                for service in self._service_health
            },
            "summary": {
                "total_services": self.total_services_count,
                "healthy_services": self.healthy_services_count,
                "unhealthy_services": len(self.unhealthy_services)
            },
            "metadata": self._metadata
        }

    @classmethod
    def from_service_health_list(
        cls,
        service_health_list: List[ServiceHealth],
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'SystemHealth':
        """Create SystemHealth from a list of service health statuses."""
        # Determine overall status based on service health
        if all(s.is_healthy for s in service_health_list):
            overall_status = HealthStatus.HEALTHY
        elif any(s.status == HealthStatus.UNHEALTHY for s in service_health_list):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s.status == HealthStatus.DEGRADED for s in service_health_list):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNKNOWN

        return cls(
            overall_status=overall_status,
            service_health=service_health_list,
            metadata=metadata
        )

    def __repr__(self) -> str:
        return f"SystemHealth(overall_status={self._overall_status}, services={len(self._service_health)})"
