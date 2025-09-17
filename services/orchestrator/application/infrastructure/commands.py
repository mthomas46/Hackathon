"""Infrastructure Application Commands"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from ...domain.infrastructure import SagaInstance, DistributedTrace, TraceSpan


@dataclass
class StartSagaCommand:
    """Command to start a new saga."""
    saga_type: str
    correlation_id: str
    steps: List[Dict[str, Any]]


@dataclass
class ExecuteSagaStepCommand:
    """Command to execute a saga step."""
    saga_id: str
    step_id: str


@dataclass
class CompensateSagaCommand:
    """Command to compensate a saga."""
    saga_id: str
    failed_step_id: str


@dataclass
class CompleteSagaCommand:
    """Command to complete a saga."""
    saga_id: str


@dataclass
class StartTraceCommand:
    """Command to start a distributed trace."""
    trace_id: str
    service_name: str
    operation_name: str
    parent_span_id: Optional[str] = None


@dataclass
class AddTraceSpanCommand:
    """Command to add a span to a trace."""
    trace_id: str
    span_id: str
    service_name: str
    operation_name: str
    start_time: str
    duration_ms: Optional[float] = None
    tags: Optional[Dict[str, Any]] = None


@dataclass
class CompleteTraceCommand:
    """Command to complete a trace."""
    trace_id: str
    end_time: str


@dataclass
class RetryEventCommand:
    """Command to retry failed events."""
    event_ids: List[str]
    max_retries: int = 3


@dataclass
class ArchiveEventCommand:
    """Command to archive processed events."""
    event_ids: List[str]


@dataclass
class PublishEventCommand:
    """Command to publish an event to the event stream."""
    event_type: str
    event_data: Dict[str, Any]
    correlation_id: Optional[str] = None
