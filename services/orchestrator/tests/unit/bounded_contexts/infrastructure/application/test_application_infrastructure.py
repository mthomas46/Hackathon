#!/usr/bin/env python3
"""
Application Layer Tests for Infrastructure

Tests the application layer including use cases for sagas, tracing, DLQ, and event streaming.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from services.orchestrator.application.infrastructure.commands import (
    StartSagaCommand, ExecuteSagaStepCommand, CompleteSagaCommand,
    CompensateSagaCommand, StartTraceCommand, AddTraceSpanCommand,
    CompleteTraceCommand, RetryEventCommand, PublishEventCommand
)
from services.orchestrator.application.infrastructure.queries import (
    GetSagaQuery, ListSagasQuery, GetTraceQuery, ListTracesQuery,
    ListDLQEventsQuery, GetEventStreamStatsQuery
)
from services.orchestrator.application.infrastructure.use_cases import (
    StartSagaUseCase, ExecuteSagaStepUseCase, GetSagaUseCase, ListSagasUseCase,
    StartTraceUseCase, GetTraceUseCase, ListTracesUseCase,
    GetDLQStatsUseCase, ListDLQEventsUseCase, RetryEventUseCase,
    GetEventStreamStatsUseCase, PublishEventUseCase
)
from tests.unit.orchestrator.test_base import BaseApplicationTest


class TestStartSagaUseCase(BaseApplicationTest):
    """Test StartSagaUseCase."""

    def get_use_case_class(self):
        return StartSagaUseCase

    def get_repository_mocks(self):
        return {"saga_service": Mock()}

    @pytest.mark.asyncio
    async def test_start_saga_success(self):
        """Test successful saga start."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["saga_service"]

        # Setup mock
        mock_service.start_saga.return_value = "saga-123"

        # Execute
        command = StartSagaCommand(name="Test Saga", steps=[])
        result = await use_case.execute(command)

        # Assert
        self.assert_use_case_success(result)
        mock_service.start_saga.assert_called_once()


class TestExecuteSagaStepUseCase(BaseApplicationTest):
    """Test ExecuteSagaStepUseCase."""

    def get_use_case_class(self):
        return ExecuteSagaStepUseCase

    def get_repository_mocks(self):
        return {"saga_service": Mock()}

    @pytest.mark.asyncio
    async def test_execute_saga_step_success(self):
        """Test successful saga step execution."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["saga_service"]

        # Setup mock
        mock_service.execute_step.return_value = True

        # Execute
        command = ExecuteSagaStepCommand(saga_id="saga-123", step_data={})
        result = await use_case.execute(command)

        # Assert
        self.assert_use_case_success(result)
        mock_service.execute_step.assert_called_once()


class TestGetSagaUseCase(BaseApplicationTest):
    """Test GetSagaUseCase."""

    def get_use_case_class(self):
        return GetSagaUseCase

    def get_repository_mocks(self):
        return {"saga_service": Mock()}

    @pytest.mark.asyncio
    async def test_get_saga_success(self):
        """Test successful saga retrieval."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["saga_service"]

        # Setup mock
        mock_saga = {"saga_id": "saga-123", "status": "active"}
        mock_service.get_saga.return_value = mock_saga

        # Execute
        query = GetSagaQuery(saga_id="saga-123")
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result, mock_saga)
        mock_service.get_saga.assert_called_once_with("saga-123")


class TestListSagasUseCase(BaseApplicationTest):
    """Test ListSagasUseCase."""

    def get_use_case_class(self):
        return ListSagasUseCase

    def get_repository_mocks(self):
        return {"saga_service": Mock()}

    @pytest.mark.asyncio
    async def test_list_sagas_success(self):
        """Test successful saga listing."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["saga_service"]

        # Setup mock
        mock_sagas = [{"saga_id": "saga-1"}, {"saga_id": "saga-2"}]
        mock_service.list_sagas.return_value = mock_sagas

        # Execute
        query = ListSagasQuery(limit=10, offset=0)
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result, mock_sagas)
        mock_service.list_sagas.assert_called_once()


class TestStartTraceUseCase(BaseApplicationTest):
    """Test StartTraceUseCase."""

    def get_use_case_class(self):
        return StartTraceUseCase

    def get_repository_mocks(self):
        return {"tracing_service": Mock()}

    @pytest.mark.asyncio
    async def test_start_trace_success(self):
        """Test successful trace start."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["tracing_service"]

        # Setup mock
        mock_service.start_trace.return_value = "trace-123"

        # Execute
        command = StartTraceCommand(
            service_name="test_service",
            operation_name="test_operation"
        )
        result = await use_case.execute(command)

        # Assert
        self.assert_use_case_success(result)
        mock_service.start_trace.assert_called_once()


class TestGetTraceUseCase(BaseApplicationTest):
    """Test GetTraceUseCase."""

    def get_use_case_class(self):
        return GetTraceUseCase

    def get_repository_mocks(self):
        return {"tracing_service": Mock()}

    @pytest.mark.asyncio
    async def test_get_trace_success(self):
        """Test successful trace retrieval."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["tracing_service"]

        # Setup mock
        mock_trace = {"trace_id": "trace-123", "status": "active"}
        mock_service.get_trace.return_value = mock_trace

        # Execute
        query = GetTraceQuery(trace_id="trace-123")
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result, mock_trace)
        mock_service.get_trace.assert_called_once_with("trace-123")


class TestListTracesUseCase(BaseApplicationTest):
    """Test ListTracesUseCase."""

    def get_use_case_class(self):
        return ListTracesUseCase

    def get_repository_mocks(self):
        return {"tracing_service": Mock()}

    @pytest.mark.asyncio
    async def test_list_traces_success(self):
        """Test successful trace listing."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["tracing_service"]

        # Setup mock
        mock_traces = [{"trace_id": "trace-1"}, {"trace_id": "trace-2"}]
        mock_service.list_traces.return_value = mock_traces

        # Execute
        query = ListTracesQuery(limit=10, offset=0)
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result, mock_traces)
        mock_service.list_traces.assert_called_once()


class TestGetDLQStatsUseCase(BaseApplicationTest):
    """Test GetDLQStatsUseCase."""

    def get_use_case_class(self):
        return GetDLQStatsUseCase

    def get_repository_mocks(self):
        return {"dlq_service": Mock()}

    @pytest.mark.asyncio
    async def test_get_dlq_stats_success(self):
        """Test successful DLQ stats retrieval."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["dlq_service"]

        # Setup mock
        mock_stats = {"total_events": 10, "failed_events": 3}
        mock_service.get_stats.return_value = mock_stats

        # Execute
        result = await use_case.execute(None)  # No query needed

        # Assert
        self.assert_use_case_success(result, mock_stats)
        mock_service.get_stats.assert_called_once()


class TestListDLQEventsUseCase(BaseApplicationTest):
    """Test ListDLQEventsUseCase."""

    def get_use_case_class(self):
        return ListDLQEventsUseCase

    def get_repository_mocks(self):
        return {"dlq_service": Mock()}

    @pytest.mark.asyncio
    async def test_list_dlq_events_success(self):
        """Test successful DLQ events listing."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["dlq_service"]

        # Setup mock
        mock_events = [{"event_id": "event-1"}, {"event_id": "event-2"}]
        mock_service.list_events.return_value = mock_events

        # Execute
        query = ListDLQEventsQuery(limit=10, offset=0)
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result, mock_events)
        mock_service.list_events.assert_called_once()


class TestRetryEventUseCase(BaseApplicationTest):
    """Test RetryEventUseCase."""

    def get_use_case_class(self):
        return RetryEventUseCase

    def get_repository_mocks(self):
        return {"dlq_service": Mock()}

    @pytest.mark.asyncio
    async def test_retry_event_success(self):
        """Test successful event retry."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["dlq_service"]

        # Setup mock
        mock_service.retry_event.return_value = True

        # Execute
        command = RetryEventCommand(event_ids=["event-123"], max_retries=3)
        result = await use_case.execute(command)

        # Assert
        self.assert_use_case_success(result)
        mock_service.retry_event.assert_called_once()


class TestPublishEventUseCase(BaseApplicationTest):
    """Test PublishEventUseCase."""

    def get_use_case_class(self):
        return PublishEventUseCase

    def get_repository_mocks(self):
        return {"event_streaming_service": Mock()}

    @pytest.mark.asyncio
    async def test_publish_event_success(self):
        """Test successful event publishing."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["event_streaming_service"]

        # Setup mock
        mock_service.publish_event.return_value = True

        # Execute
        command = PublishEventCommand(
            event_type="test_event",
            payload={"message": "test"}
        )
        result = await use_case.execute(command)

        # Assert
        self.assert_use_case_success(result)
        mock_service.publish_event.assert_called_once()


class TestGetEventStreamStatsUseCase(BaseApplicationTest):
    """Test GetEventStreamStatsUseCase."""

    def get_use_case_class(self):
        return GetEventStreamStatsUseCase

    def get_repository_mocks(self):
        return {"event_streaming_service": Mock()}

    @pytest.mark.asyncio
    async def test_get_event_stream_stats_success(self):
        """Test successful event stream stats retrieval."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["event_streaming_service"]

        # Setup mock
        mock_stats = {"total_events": 100, "events_per_second": 5.2}
        mock_service.get_stats.return_value = mock_stats

        # Execute
        query = GetEventStreamStatsQuery()
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result, mock_stats)
        mock_service.get_stats.assert_called_once()
