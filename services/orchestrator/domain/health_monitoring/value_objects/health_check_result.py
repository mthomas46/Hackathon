"""Health Check Result Value Object"""

from typing import Optional, Dict, Any
from datetime import datetime

from .health_status import HealthStatus


class HealthCheckResult:
    """Value object representing the result of a health check."""

    def __init__(
        self,
        status: HealthStatus,
        message: str,
        timestamp: Optional[datetime] = None,
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        self._status = status
        self._message = message.strip()
        self._timestamp = timestamp or datetime.utcnow()
        self._details = details or {}
        self._response_time_ms = response_time_ms
        self._error_message = error_message.strip() if error_message else None

        self._validate()

    def _validate(self):
        """Validate health check result data."""
        if not self._message:
            raise ValueError("Message cannot be empty")

    @property
    def status(self) -> HealthStatus:
        """Get the health status."""
        return self._status

    @property
    def message(self) -> str:
        """Get the result message."""
        return self._message

    @property
    def timestamp(self) -> datetime:
        """Get the timestamp."""
        return self._timestamp

    @property
    def details(self) -> Dict[str, Any]:
        """Get the result details."""
        return self._details.copy()

    @property
    def response_time_ms(self) -> Optional[float]:
        """Get the response time in milliseconds."""
        return self._response_time_ms

    @property
    def error_message(self) -> Optional[str]:
        """Get the error message if any."""
        return self._error_message

    @property
    def is_successful(self) -> bool:
        """Check if the health check was successful."""
        return self._status.is_healthy

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "status": self._status.value,
            "message": self._message,
            "timestamp": self._timestamp.isoformat(),
            "details": self._details
        }

        if self._response_time_ms is not None:
            result["response_time_ms"] = self._response_time_ms

        if self._error_message:
            result["error_message"] = self._error_message

        return result

    @classmethod
    def success(
        cls,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[float] = None
    ) -> 'HealthCheckResult':
        """Create a successful health check result."""
        return cls(
            status=HealthStatus.HEALTHY,
            message=message,
            details=details,
            response_time_ms=response_time_ms
        )

    @classmethod
    def failure(
        cls,
        message: str,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[float] = None
    ) -> 'HealthCheckResult':
        """Create a failed health check result."""
        return cls(
            status=HealthStatus.UNHEALTHY,
            message=message,
            details=details,
            response_time_ms=response_time_ms,
            error_message=error_message
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HealthCheckResult):
            return NotImplemented
        return (self._status == other._status and
                self._message == other._message and
                self._error_message == other._error_message)

    def __repr__(self) -> str:
        return f"HealthCheckResult(status={self._status}, message='{self._message}')"
