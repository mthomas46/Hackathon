"""Service Health Value Object"""

from typing import Optional, Dict, Any
from datetime import datetime

from .health_status import HealthStatus
from .health_check_result import HealthCheckResult


class ServiceHealth:
    """Value object representing the health status of a service."""

    def __init__(
        self,
        service_name: str,
        status: HealthStatus,
        last_check: Optional[datetime] = None,
        check_result: Optional[HealthCheckResult] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._service_name = service_name.strip()
        self._status = status
        self._last_check = last_check or datetime.utcnow()
        self._check_result = check_result
        self._metadata = metadata or {}

        self._validate()

    def _validate(self):
        """Validate service health data."""
        if not self._service_name:
            raise ValueError("Service name cannot be empty")

    @property
    def service_name(self) -> str:
        """Get the service name."""
        return self._service_name

    @property
    def status(self) -> HealthStatus:
        """Get the health status."""
        return self._status

    @property
    def last_check(self) -> datetime:
        """Get the last check timestamp."""
        return self._last_check

    @property
    def check_result(self) -> Optional[HealthCheckResult]:
        """Get the last check result."""
        return self._check_result

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the service metadata."""
        return self._metadata.copy()

    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self._status.is_healthy

    @property
    def is_operational(self) -> bool:
        """Check if service is operational."""
        return self._status.is_operational

    def update_status(
        self,
        status: HealthStatus,
        check_result: Optional[HealthCheckResult] = None
    ):
        """Update the service health status."""
        self._status = status
        self._last_check = datetime.utcnow()
        if check_result:
            self._check_result = check_result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "service_name": self._service_name,
            "status": self._status.value,
            "last_check": self._last_check.isoformat(),
            "is_healthy": self.is_healthy,
            "is_operational": self.is_operational,
            "metadata": self._metadata
        }

        if self._check_result:
            result["last_result"] = self._check_result.to_dict()

        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ServiceHealth):
            return NotImplemented
        return (self._service_name == other._service_name and
                self._status == other._status)

    def __repr__(self) -> str:
        return f"ServiceHealth(service_name='{self._service_name}', status={self._status})"
