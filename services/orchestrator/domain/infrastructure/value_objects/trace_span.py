"""Trace Span Value Object"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4


class TraceSpan:
    """Value object representing a single span in a distributed trace."""

    def __init__(
        self,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        service_name: str = "",
        operation_name: str = "",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        tags: Optional[Dict[str, Any]] = None,
        logs: Optional[List[Dict[str, Any]]] = None
    ):
        self._span_id = span_id or str(uuid4())
        self._parent_span_id = parent_span_id
        self._service_name = service_name.strip()
        self._operation_name = operation_name.strip()
        self._start_time = start_time or datetime.utcnow()
        self._end_time = end_time
        self._tags = tags or {}
        self._logs = logs or []

        self._validate()

    def _validate(self):
        """Validate trace span data."""
        if not self._span_id:
            raise ValueError("Span ID cannot be empty")

    @property
    def span_id(self) -> str:
        """Get the span ID."""
        return self._span_id

    @property
    def parent_span_id(self) -> Optional[str]:
        """Get the parent span ID."""
        return self._parent_span_id

    @property
    def service_name(self) -> str:
        """Get the service name."""
        return self._service_name

    @property
    def operation_name(self) -> str:
        """Get the operation name."""
        return self._operation_name

    @property
    def start_time(self) -> datetime:
        """Get the start time."""
        return self._start_time

    @property
    def end_time(self) -> Optional[datetime]:
        """Get the end time."""
        return self._end_time

    @property
    def duration_microseconds(self) -> Optional[int]:
        """Get the duration in microseconds."""
        if self._end_time:
            return int((self._end_time - self._start_time).total_seconds() * 1_000_000)
        return None

    @property
    def tags(self) -> Dict[str, Any]:
        """Get the span tags."""
        return self._tags.copy()

    @property
    def logs(self) -> List[Dict[str, Any]]:
        """Get the span logs."""
        return self._logs.copy()

    def finish(self, end_time: Optional[datetime] = None):
        """Finish the span."""
        self._end_time = end_time or datetime.utcnow()

    def add_tag(self, key: str, value: Any):
        """Add a tag to the span."""
        self._tags[key] = value

    def log(self, event: str, timestamp: Optional[datetime] = None, fields: Optional[Dict[str, Any]] = None):
        """Add a log entry to the span."""
        log_entry = {
            "event": event,
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            "fields": fields or {}
        }
        self._logs.append(log_entry)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "span_id": self._span_id,
            "service_name": self._service_name,
            "operation_name": self._operation_name,
            "start_time": self._start_time.isoformat(),
            "tags": self._tags,
            "logs": self._logs
        }

        if self._parent_span_id:
            result["parent_span_id"] = self._parent_span_id

        if self._end_time:
            result["end_time"] = self._end_time.isoformat()
            result["duration_microseconds"] = self.duration_microseconds

        return result

    def __repr__(self) -> str:
        return f"TraceSpan(span_id='{self._span_id}', service='{self._service_name}', operation='{self._operation_name}')"
