"""Tracing Service Domain Service"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..value_objects.distributed_trace import DistributedTrace
from ..value_objects.trace_span import TraceSpan
from ..value_objects.trace_status import TraceStatus


class TracingService:
    """Domain service for managing distributed tracing."""

    def __init__(self):
        """Initialize tracing service."""
        self._active_traces: Dict[str, DistributedTrace] = {}
        self._completed_traces: Dict[str, DistributedTrace] = {}

    def start_trace(
        self,
        root_service: str,
        root_operation: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DistributedTrace:
        """Start a new distributed trace."""
        trace = DistributedTrace(
            trace_id=trace_id,
            root_service=root_service,
            root_operation=root_operation,
            status=TraceStatus.ACTIVE,
            metadata=metadata
        )

        self._active_traces[trace.trace_id] = trace
        return trace

    def create_span(
        self,
        trace_id: str,
        service_name: str,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> Optional[TraceSpan]:
        """Create a new span in an existing trace."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            return None

        span = TraceSpan(
            parent_span_id=parent_span_id,
            service_name=service_name,
            operation_name=operation_name,
            tags=tags
        )

        trace.add_span(span)
        return span

    def finish_span(self, trace_id: str, span_id: str) -> bool:
        """Finish a span in a trace."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            return False

        for span in trace.spans:
            if span.span_id == span_id:
                span.finish()
                return True

        return False

    def complete_trace(
        self,
        trace_id: str,
        status: TraceStatus = TraceStatus.COMPLETED
    ) -> bool:
        """Complete a distributed trace."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            return False

        trace.complete(status)

        # Move to completed traces
        del self._active_traces[trace_id]
        self._completed_traces[trace_id] = trace

        return True

    def get_trace(self, trace_id: str) -> Optional[DistributedTrace]:
        """Get a trace by ID."""
        return self._active_traces.get(trace_id) or self._completed_traces.get(trace_id)

    def list_active_traces(
        self,
        service_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DistributedTrace]:
        """List active traces with optional filtering."""
        traces = list(self._active_traces.values())

        if service_filter:
            traces = [t for t in traces if t.root_service == service_filter]

        # Sort by creation time (newest first)
        traces.sort(key=lambda t: t.created_at, reverse=True)

        start_idx = offset
        end_idx = start_idx + limit
        return traces[start_idx:end_idx]

    def list_completed_traces(
        self,
        service_filter: Optional[str] = None,
        status_filter: Optional[TraceStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DistributedTrace]:
        """List completed traces with optional filtering."""
        traces = list(self._completed_traces.values())

        if service_filter:
            traces = [t for t in traces if t.root_service == service_filter]

        if status_filter:
            traces = [t for t in traces if t.status == status_filter]

        # Sort by completion time (newest first)
        traces.sort(key=lambda t: t.completed_at or t.created_at, reverse=True)

        start_idx = offset
        end_idx = start_idx + limit
        return traces[start_idx:end_idx]

    def get_service_traces(
        self,
        service_name: str,
        active_only: bool = False,
        limit: int = 50
    ) -> List[DistributedTrace]:
        """Get traces for a specific service."""
        traces = []

        # Check active traces
        for trace in self._active_traces.values():
            if any(span.service_name == service_name for span in trace.spans):
                traces.append(trace)

        # Check completed traces if not active_only
        if not active_only:
            for trace in self._completed_traces.values():
                if any(span.service_name == service_name for span in trace.spans):
                    traces.append(trace)

        # Sort by creation time (newest first)
        traces.sort(key=lambda t: t.created_at, reverse=True)

        return traces[:limit]

    def get_tracing_stats(self) -> Dict[str, Any]:
        """Get tracing statistics."""
        active_traces = list(self._active_traces.values())
        completed_traces = list(self._completed_traces.values())

        total_completed = len(completed_traces)
        successful_traces = len([t for t in completed_traces if t.status == TraceStatus.COMPLETED])
        failed_traces = len([t for t in completed_traces if t.status == TraceStatus.FAILED])

        # Calculate average spans per trace
        total_spans = sum(len(t.spans) for t in active_traces + completed_traces)
        total_traces = len(active_traces) + len(completed_traces)
        avg_spans_per_trace = total_spans / total_traces if total_traces > 0 else 0

        # Calculate average trace duration
        completed_durations = [
            t.duration_microseconds for t in completed_traces
            if t.duration_microseconds is not None
        ]
        avg_duration = sum(completed_durations) / len(completed_durations) if completed_durations else None

        return {
            "active_traces": len(active_traces),
            "completed_traces": total_completed,
            "successful_traces": successful_traces,
            "failed_traces": failed_traces,
            "total_spans": total_spans,
            "avg_spans_per_trace": avg_spans_per_trace,
            "avg_trace_duration_microseconds": avg_duration
        }

    def cleanup_old_traces(self, max_age_hours: int = 24) -> int:
        """Clean up old completed traces. Returns count removed."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        traces_to_remove = []

        for trace_id, trace in self._completed_traces.items():
            if trace.completed_at and trace.completed_at < cutoff_time:
                traces_to_remove.append(trace_id)

        for trace_id in traces_to_remove:
            del self._completed_traces[trace_id]

        return len(traces_to_remove)
