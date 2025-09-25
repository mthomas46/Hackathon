"""Consolidated observability utilities for monitoring and tracing.

Combines distributed tracing and logging functionality.
"""

import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from starlette.requests import Request


class TraceStatus(Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class TraceSpan:
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    service_name: str
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: TraceStatus = TraceStatus.STARTED
    tags: Dict[str, Any] = None
    logs: List[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        """Initialize default values for tags and logs."""
        if self.tags is None:
            self.tags = {}
        if self.logs is None:
            self.logs = []


class DistributedTracer:
    """Distributed tracing manager for cross-service operations."""

    def __init__(
        self,
        service_name: str,
        redis_host: str = "redis",
        traces_key: str = "traces:spans",
        max_spans: int = 10000,
        retention_hours: int = 24,
    ):
        self.service_name = service_name
        self.redis_host = redis_host
        self.traces_key = traces_key
        self.max_spans = max_spans
        self.retention_hours = retention_hours
        self._active_spans: Dict[str, TraceSpan] = {}

    def start_span(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ) -> TraceSpan:
        """Start a new trace span for operation tracking.

        Args:
            operation_name: Name of the operation being traced
            trace_id: Optional trace ID (generated if not provided)
            parent_span_id: Optional parent span ID for nested operations
            tags: Optional initial tags for the span

        Returns:
            TraceSpan: The created span object
        """
        if not trace_id:
            trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        now = time.time()
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            service_name=self.service_name,
            operation_name=operation_name,
            start_time=now,
            tags=tags or {},
        )
        self._active_spans[span_id] = span
        return span

    def finish_span(
        self,
        span_id: str,
        status: TraceStatus = TraceStatus.COMPLETED,
        error: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ):
        """Finish a trace span and record completion metrics.

        Args:
            span_id: ID of the span to finish
            status: Completion status of the span
            error: Optional error message if span failed
            tags: Additional tags to add to the span
        """
        if span_id not in self._active_spans:
            return
        span = self._active_spans[span_id]
        now = time.time()
        span.end_time = now
        span.duration = now - span.start_time
        span.status = status
        span.error = error
        if tags:
            span.tags.update(tags)
        del self._active_spans[span_id]

    def add_span_log(
        self,
        span_id: str,
        message: str,
        level: str = "info",
        fields: Optional[Dict[str, Any]] = None,
    ):
        """Add a log entry to a trace span.

        Args:
            span_id: ID of the span to add log to
            message: Log message
            level: Log level (info, warning, error, etc.)
            fields: Additional structured fields for the log entry
        """
        if span_id not in self._active_spans:
            return
        span = self._active_spans[span_id]
        log_entry = {
            "timestamp": time.time(),
            "message": message,
            "level": level,
            "fields": fields or {},
        }
        span.logs.append(log_entry)

    def add_span_tag(self, span_id: str, key: str, value: Any):
        """Add a tag to a trace span.

        Args:
            span_id: ID of the span to add tag to
            key: Tag key
            value: Tag value
        """
        if span_id not in self._active_spans:
            return
        span = self._active_spans[span_id]
        span.tags[key] = value


class TraceContext:
    """Context manager for automatic span management."""

    def __init__(
        self,
        tracer: DistributedTracer,
        operation_name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ):
        self.tracer = tracer
        self.operation_name = operation_name
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        self.tags = tags
        self.span: Optional[TraceSpan] = None

    def __enter__(self) -> TraceSpan:
        """Enter the trace context and start the span.

        Returns:
            TraceSpan: The created span object
        """
        self.span = self.tracer.start_span(
            self.operation_name, self.trace_id, self.parent_span_id, self.tags
        )
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the trace context and finish the span.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if self.span:
            if exc_type:
                self.tracer.finish_span(
                    self.span.span_id, TraceStatus.FAILED, str(exc_val)
                )
            else:
                self.tracer.finish_span(self.span.span_id)


class CorrelationIDMiddleware:
    """Middleware for propagating correlation IDs across services."""

    def __init__(self, tracer: DistributedTracer):
        self.tracer = tracer

    async def process_request(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        span = self.tracer.start_span(
            f"{request.method} {request.url.path}", correlation_id
        )
        self.tracer.add_span_tag(span.span_id, "http.method", request.method)
        self.tracer.add_span_tag(span.span_id, "http.url", str(request.url))
        try:
            response = await call_next(request)
            self.tracer.add_span_tag(
                span.span_id, "http.status_code", response.status_code
            )
            self.tracer.finish_span(span.span_id)
            return response
        except Exception as e:
            self.tracer.finish_span(span.span_id, TraceStatus.FAILED, str(e))
            raise


# Note: Logging functionality moved to shared/logging.py to avoid duplication
