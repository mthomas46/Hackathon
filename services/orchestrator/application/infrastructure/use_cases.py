"""Infrastructure Application Use Cases"""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from ...domain.infrastructure.services import DLQService, SagaService, TracingService, EventStreamingService
from ...domain.infrastructure import SagaInstance, DistributedTrace, DLQEvent
from .commands import (
    StartSagaCommand, ExecuteSagaStepCommand, CompensateSagaCommand, CompleteSagaCommand,
    StartTraceCommand, AddTraceSpanCommand, CompleteTraceCommand,
    RetryEventCommand, ArchiveEventCommand, PublishEventCommand
)
from .queries import (
    GetSagaQuery, ListSagasQuery, GetTraceQuery, ListTracesQuery,
    GetDLQStatsQuery, ListDLQEventsQuery, GetEventStreamStatsQuery, ListEventStreamQuery
)


class UseCase(ABC):
    """Base use case class."""

    @abstractmethod
    async def execute(self, *args, **kwargs):
        """Execute the use case."""
        pass


class StartSagaUseCase(UseCase):
    """Use case for starting a saga."""

    def __init__(self, saga_service: SagaService):
        self.saga_service = saga_service

    async def execute(self, command: StartSagaCommand) -> SagaInstance:
        """Execute the start saga use case."""
        return self.saga_service.start_saga(
            saga_type=command.saga_type,
            correlation_id=command.correlation_id,
            steps=command.steps
        )


class ExecuteSagaStepUseCase(UseCase):
    """Use case for executing a saga step."""

    def __init__(self, saga_service: SagaService):
        self.saga_service = saga_service

    async def execute(self, command: ExecuteSagaStepCommand) -> SagaInstance:
        """Execute the execute saga step use case."""
        return self.saga_service.execute_step(command.saga_id, command.step_id)


class CompensateSagaUseCase(UseCase):
    """Use case for compensating a saga."""

    def __init__(self, saga_service: SagaService):
        self.saga_service = saga_service

    async def execute(self, command: CompensateSagaCommand) -> SagaInstance:
        """Execute the compensate saga use case."""
        return self.saga_service.compensate_saga(command.saga_id, command.failed_step_id)


class CompleteSagaUseCase(UseCase):
    """Use case for completing a saga."""

    def __init__(self, saga_service: SagaService):
        self.saga_service = saga_service

    async def execute(self, command: CompleteSagaCommand) -> SagaInstance:
        """Execute the complete saga use case."""
        return self.saga_service.complete_saga(command.saga_id)


class GetSagaUseCase(UseCase):
    """Use case for getting a saga."""

    def __init__(self, saga_service: SagaService):
        self.saga_service = saga_service

    async def execute(self, query: GetSagaQuery) -> Optional[SagaInstance]:
        """Execute the get saga use case."""
        return self.saga_service.get_saga(query.saga_id)


class ListSagasUseCase(UseCase):
    """Use case for listing sagas."""

    def __init__(self, saga_service: SagaService):
        self.saga_service = saga_service

    async def execute(self, query: ListSagasQuery) -> List[SagaInstance]:
        """Execute the list sagas use case."""
        return self.saga_service.list_sagas(
            status_filter=query.status_filter,
            saga_type_filter=query.saga_type_filter,
            correlation_id_filter=query.correlation_id_filter,
            limit=query.limit,
            offset=query.offset
        )


class StartTraceUseCase(UseCase):
    """Use case for starting a trace."""

    def __init__(self, tracing_service: TracingService):
        self.tracing_service = tracing_service

    async def execute(self, command: StartTraceCommand) -> DistributedTrace:
        """Execute the start trace use case."""
        return self.tracing_service.start_trace(
            trace_id=command.trace_id,
            service_name=command.service_name,
            operation_name=command.operation_name,
            parent_span_id=command.parent_span_id
        )


class AddTraceSpanUseCase(UseCase):
    """Use case for adding a trace span."""

    def __init__(self, tracing_service: TracingService):
        self.tracing_service = tracing_service

    async def execute(self, command: AddTraceSpanCommand) -> DistributedTrace:
        """Execute the add trace span use case."""
        return self.tracing_service.add_span(
            trace_id=command.trace_id,
            span_id=command.span_id,
            service_name=command.service_name,
            operation_name=command.operation_name,
            start_time=command.start_time,
            duration_ms=command.duration_ms,
            tags=command.tags
        )


class CompleteTraceUseCase(UseCase):
    """Use case for completing a trace."""

    def __init__(self, tracing_service: TracingService):
        self.tracing_service = tracing_service

    async def execute(self, command: CompleteTraceCommand) -> DistributedTrace:
        """Execute the complete trace use case."""
        return self.tracing_service.complete_trace(command.trace_id, command.end_time)


class GetTraceUseCase(UseCase):
    """Use case for getting a trace."""

    def __init__(self, tracing_service: TracingService):
        self.tracing_service = tracing_service

    async def execute(self, query: GetTraceQuery) -> Optional[DistributedTrace]:
        """Execute the get trace use case."""
        return self.tracing_service.get_trace(query.trace_id)


class ListTracesUseCase(UseCase):
    """Use case for listing traces."""

    def __init__(self, tracing_service: TracingService):
        self.tracing_service = tracing_service

    async def execute(self, query: ListTracesQuery) -> List[DistributedTrace]:
        """Execute the list traces use case."""
        return self.tracing_service.list_traces(
            service_filter=query.service_filter,
            operation_filter=query.operation_filter,
            start_time_after=query.start_time_after,
            start_time_before=query.start_time_before,
            limit=query.limit,
            offset=query.offset
        )


class GetDLQStatsUseCase(UseCase):
    """Use case for getting DLQ statistics."""

    def __init__(self, dlq_service: DLQService):
        self.dlq_service = dlq_service

    async def execute(self, query: GetDLQStatsQuery) -> Dict[str, Any]:
        """Execute the get DLQ stats use case."""
        return self.dlq_service.get_stats(query.time_range_hours)


class ListDLQEventsUseCase(UseCase):
    """Use case for listing DLQ events."""

    def __init__(self, dlq_service: DLQService):
        self.dlq_service = dlq_service

    async def execute(self, query: ListDLQEventsQuery) -> List[DLQEvent]:
        """Execute the list DLQ events use case."""
        return self.dlq_service.list_events(
            event_type_filter=query.event_type_filter,
            service_filter=query.service_filter,
            limit=query.limit,
            offset=query.offset
        )


class RetryEventUseCase(UseCase):
    """Use case for retrying events."""

    def __init__(self, dlq_service: DLQService):
        self.dlq_service = dlq_service

    async def execute(self, command: RetryEventCommand) -> Dict[str, Any]:
        """Execute the retry event use case."""
        return self.dlq_service.retry_events(command.event_ids, command.max_retries)


class GetEventStreamStatsUseCase(UseCase):
    """Use case for getting event stream statistics."""

    def __init__(self, event_streaming_service: EventStreamingService):
        self.event_streaming_service = event_streaming_service

    async def execute(self, query: GetEventStreamStatsQuery) -> Dict[str, Any]:
        """Execute the get event stream stats use case."""
        return self.event_streaming_service.get_stats(query.time_range_hours)


class PublishEventUseCase(UseCase):
    """Use case for publishing events."""

    def __init__(self, event_streaming_service: EventStreamingService):
        self.event_streaming_service = event_streaming_service

    async def execute(self, command: PublishEventCommand) -> Dict[str, Any]:
        """Execute the publish event use case."""
        return self.event_streaming_service.publish_event(
            event_type=command.event_type,
            event_data=command.event_data,
            correlation_id=command.correlation_id
        )
