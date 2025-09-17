"""DLQ Event Value Object"""

from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

from .event_status import EventStatus


class DLQEvent:
    """Value object representing an event in the Dead Letter Queue."""

    def __init__(
        self,
        event_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        failure_reason: str,
        original_timestamp: datetime,
        retry_count: int = 0,
        max_retries: int = 3,
        correlation_id: Optional[str] = None,
        service_name: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ):
        self._event_id = event_id
        self._event_type = event_type.strip()
        self._event_data = event_data.copy()
        self._failure_reason = failure_reason.strip()
        self._original_timestamp = original_timestamp
        self._retry_count = max(0, retry_count)
        self._max_retries = max(1, max_retries)
        self._correlation_id = correlation_id.strip() if correlation_id else None
        self._service_name = service_name.strip() if service_name else None
        self._error_details = error_details.copy() if error_details else {}
        self._dlq_timestamp = datetime.utcnow()
        self._dlq_id = str(uuid4())

        self._validate()

    def _validate(self):
        """Validate DLQ event data."""
        if not self._event_id:
            raise ValueError("Event ID cannot be empty")

        if not self._event_type:
            raise ValueError("Event type cannot be empty")

        if not self._failure_reason:
            raise ValueError("Failure reason cannot be empty")

    @property
    def event_id(self) -> str:
        """Get the original event ID."""
        return self._event_id

    @property
    def dlq_id(self) -> str:
        """Get the DLQ event ID."""
        return self._dlq_id

    @property
    def event_type(self) -> str:
        """Get the event type."""
        return self._event_type

    @property
    def event_data(self) -> Dict[str, Any]:
        """Get the event data."""
        return self._event_data.copy()

    @property
    def failure_reason(self) -> str:
        """Get the failure reason."""
        return self._failure_reason

    @property
    def original_timestamp(self) -> datetime:
        """Get the original event timestamp."""
        return self._original_timestamp

    @property
    def dlq_timestamp(self) -> datetime:
        """Get the DLQ timestamp."""
        return self._dlq_timestamp

    @property
    def retry_count(self) -> int:
        """Get the retry count."""
        return self._retry_count

    @property
    def max_retries(self) -> int:
        """Get the maximum retry count."""
        return self._max_retries

    @property
    def correlation_id(self) -> Optional[str]:
        """Get the correlation ID."""
        return self._correlation_id

    @property
    def service_name(self) -> Optional[str]:
        """Get the service name."""
        return self._service_name

    @property
    def error_details(self) -> Dict[str, Any]:
        """Get the error details."""
        return self._error_details.copy()

    @property
    def can_retry(self) -> bool:
        """Check if event can be retried."""
        return self._retry_count < self._max_retries

    @property
    def age_seconds(self) -> float:
        """Get the age of the DLQ event in seconds."""
        return (datetime.utcnow() - self._dlq_timestamp).total_seconds()

    def increment_retry_count(self) -> bool:
        """Increment retry count. Returns True if can retry, False if exhausted."""
        if self.can_retry:
            self._retry_count += 1
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "dlq_id": self._dlq_id,
            "event_id": self._event_id,
            "event_type": self._event_type,
            "event_data": self._event_data,
            "failure_reason": self._failure_reason,
            "original_timestamp": self._original_timestamp.isoformat(),
            "dlq_timestamp": self._dlq_timestamp.isoformat(),
            "retry_count": self._retry_count,
            "max_retries": self._max_retries,
            "correlation_id": self._correlation_id,
            "service_name": self._service_name,
            "error_details": self._error_details,
            "can_retry": self.can_retry,
            "age_seconds": self.age_seconds
        }

    def __repr__(self) -> str:
        return f"DLQEvent(dlq_id='{self._dlq_id}', event_id='{self._event_id}', event_type='{self._event_type}')"
