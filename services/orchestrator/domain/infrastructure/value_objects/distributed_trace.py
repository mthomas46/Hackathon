"""Distributed Trace Value Object"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

from .trace_status import TraceStatus
from .trace_span import TraceSpan


class DistributedTrace:
    """Value object representing a complete distributed trace across services."""

    def __init__(
        self,
        trace_id: Optional[str] = None,
        root_service: str = "",
        root_operation: str = "",
        status: TraceStatus = TraceStatus.ACTIVE,
        spans: Optional[List[TraceSpan]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._trace_id = trace_id or str(uuid4())
        self._root_service = root_service.strip()
        self._root_operation = root_operation.strip()
        self._status = status
        self._spans = spans or []
        self._metadata = metadata or {}
        self._created_at = datetime.utcnow()
        self._completed_at: Optional[datetime] = None

        self._validate()

    def _validate(self):
        """Validate distributed trace data."""
        if not self._trace_id:
            raise ValueError("Trace ID cannot be empty")

    @property
    def trace_id(self) -> str:
        """Get the trace ID."""
        return self._trace_id

    @property
    def root_service(self) -> str:
        """Get the root service name."""
        return self._root_service

    @property
    def root_operation(self) -> str:
        """Get the root operation name."""
        return self._root_operation

    @property
    def status(self) -> TraceStatus:
        """Get the trace status."""
        return self._status

    @property
    def spans(self) -> List[TraceSpan]:
        """Get all spans in the trace."""
        return self._spans.copy()

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the trace metadata."""
        return self._metadata.copy()

    @property
    def created_at(self) -> datetime:
        """Get the creation timestamp."""
        return self._created_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get the completion timestamp."""
        return self._completed_at

    @property
    def duration_microseconds(self) -> Optional[int]:
        """Get the total trace duration in microseconds."""
        if not self._spans:
            return None

        earliest_start = min(span.start_time for span in self._spans)
        latest_end = max(span.end_time or span.start_time for span in self._spans)

        return int((latest_end - earliest_start).total_seconds() * 1_000_000)

    @property
    def service_count(self) -> int:
        """Get the number of unique services in the trace."""
        return len(set(span.service_name for span in self._spans if span.service_name))

    @property
    def span_count(self) -> int:
        """Get the total number of spans."""
        return len(self._spans)

    def add_span(self, span: TraceSpan):
        """Add a span to the trace."""
        self._spans.append(span)

    def complete(self, status: TraceStatus = TraceStatus.COMPLETED):
        """Complete the trace."""
        self._status = status
        self._completed_at = datetime.utcnow()

        # Finish any unfinished spans
        for span in self._spans:
            if span.end_time is None:
                span.finish(self._completed_at)

    def get_spans_by_service(self, service_name: str) -> List[TraceSpan]:
        """Get all spans for a specific service."""
        return [span for span in self._spans if span.service_name == service_name]

    def get_root_span(self) -> Optional[TraceSpan]:
        """Get the root span of the trace."""
        # Root span has no parent
        root_spans = [span for span in self._spans if span.parent_span_id is None]
        return root_spans[0] if root_spans else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "trace_id": self._trace_id,
            "root_service": self._root_service,
            "root_operation": self._root_operation,
            "status": self._status.value,
            "spans": [span.to_dict() for span in self._spans],
            "metadata": self._metadata,
            "created_at": self._created_at.isoformat(),
            "service_count": self.service_count,
            "span_count": self.span_count
        }

        if self._completed_at:
            result["completed_at"] = self._completed_at.isoformat()
            result["duration_microseconds"] = self.duration_microseconds

        return result

    def __repr__(self) -> str:
        return f"DistributedTrace(trace_id='{self._trace_id}', status={self._status}, spans={len(self._spans)})"
