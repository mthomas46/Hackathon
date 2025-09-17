#!/usr/bin/env python3
"""
Domain Layer Tests for Infrastructure Services

Tests the core domain services for infrastructure monitoring including DLQ, sagas, tracing, and event streaming.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from services.orchestrator.domain.infrastructure.services import (
    DLQService, SagaService, TracingService, EventStreamingService
)


class TestDLQService:
    """Test DLQService domain service."""

    @pytest.fixture
    def dlq_service(self):
        """Create DLQ service for testing."""
        return DLQService()

    def test_add_and_get_dlq_event(self, dlq_service):
        """Test adding and retrieving DLQ events."""
        dlq_event = dlq_service.add_to_dlq(
            event_id="event-123",
            event_type="user.created",
            event_data={"user_id": 123},
            failure_reason="Database connection failed",
            correlation_id="corr-456"
        )

        # Get by DLQ ID
        retrieved = dlq_service.get_dlq_event(dlq_event.dlq_id)
        assert retrieved == dlq_event

        # Get by original event ID
        retrieved_by_original = dlq_service.get_event_by_original_id("event-123")
        assert retrieved_by_original == dlq_event

    def test_list_dlq_events_with_filters(self, dlq_service):
        """Test listing DLQ events with filters."""
        # Add multiple events
        dlq_service.add_to_dlq("event1", "user.created", {}, "Error 1", service_name="user-service")
        dlq_service.add_to_dlq("event2", "order.created", {}, "Error 2", service_name="order-service")
        dlq_service.add_to_dlq("event3", "user.updated", {}, "Error 3", service_name="user-service")

        # List all
        all_events = dlq_service.list_dlq_events()
        assert len(all_events) == 3

        # Filter by event type
        user_events = dlq_service.list_dlq_events(event_type_filter="user.created")
        assert len(user_events) == 1

        # Filter by service
        service_events = dlq_service.list_dlq_events(service_filter="user-service")
        assert len(service_events) == 2

    def test_retry_dlq_events(self, dlq_service):
        """Test retrying DLQ events."""
        dlq_event = dlq_service.add_to_dlq("event1", "test", {}, "Error")

        result = dlq_service.retry_dlq_events([dlq_event.dlq_id])

        assert result["retried"] == [dlq_event.dlq_id]
        assert dlq_event.retry_count == 1

    def test_remove_from_dlq(self, dlq_service):
        """Test removing events from DLQ."""
        dlq_event = dlq_service.add_to_dlq("event1", "test", {}, "Error")

        result = dlq_service.remove_from_dlq([dlq_event.dlq_id])

        assert result["removed"] == [dlq_event.dlq_id]
        assert dlq_service.get_dlq_event(dlq_event.dlq_id) is None

    def test_get_dlq_stats(self, dlq_service):
        """Test getting DLQ statistics."""
        dlq_service.add_to_dlq("event1", "user.created", {}, "Error 1", service_name="user-service")
        dlq_service.add_to_dlq("event2", "order.created", {}, "Error 2", service_name="order-service")

        stats = dlq_service.get_dlq_stats()

        assert stats["total_events"] == 2
        assert stats["events_by_type"]["user.created"] == 1
        assert stats["events_by_service"]["user-service"] == 1
        assert "oldest_event" in stats
        assert "newest_event" in stats


class TestSagaService:
    """Test SagaService domain service."""

    @pytest.fixture
    def saga_service(self):
        """Create saga service for testing."""
        return SagaService()

    def test_create_and_start_saga(self, saga_service):
        """Test creating and starting a saga."""
        steps = [
            {"step_id": "step1", "service_name": "service1", "operation": "create_user"},
            {"step_id": "step2", "service_name": "service2", "operation": "send_email"}
        ]

        saga = saga_service.create_saga("user_registration", "corr-123", steps)

        assert saga.saga_type == "user_registration"
        assert saga.correlation_id == "corr-123"
        assert len(saga.steps) == 2

        # Start saga
        success = saga_service.start_saga(saga.saga_id)
        assert success is True
        assert saga.status == SagaStatus.STARTED

    def test_saga_execution_flow(self, saga_service):
        """Test complete saga execution flow."""
        steps = [{"step_id": "step1", "service_name": "service1", "operation": "create_user"}]
        saga = saga_service.create_saga("test_saga", "corr-123", steps)

        saga_service.start_saga(saga.saga_id)
        saga_service.complete_saga_step(saga.saga_id, "step1")
        saga_service.complete_saga(saga.saga_id)

        # Should be moved to completed sagas
        completed_saga = saga_service.get_saga(saga.saga_id)
        assert completed_saga.status == SagaStatus.COMPLETED

    def test_saga_failure_and_compensation(self, saga_service):
        """Test saga failure and compensation."""
        steps = [{"step_id": "step1", "service_name": "service1", "operation": "create_user"}]
        saga = saga_service.create_saga("test_saga", "corr-123", steps)

        saga_service.start_saga(saga.saga_id)
        saga_service.fail_saga_step(saga.saga_id, "step1", "Database error")

        # Should trigger compensation and fail
        failed_saga = saga_service.get_saga(saga.saga_id)
        assert failed_saga.status == SagaStatus.FAILED

    def test_list_sagas(self, saga_service):
        """Test listing sagas."""
        # Create multiple sagas
        saga1 = saga_service.create_saga("type1", "corr1", [{"step_id": "step1", "service_name": "service1", "operation": "op1"}])
        saga2 = saga_service.create_saga("type2", "corr2", [{"step_id": "step1", "service_name": "service1", "operation": "op1"}])

        # List active sagas
        active_sagas = saga_service.list_active_sagas()
        assert len(active_sagas) == 2

        # List by type
        type1_sagas = saga_service.list_active_sagas(saga_type_filter="type1")
        assert len(type1_sagas) == 1
        assert type1_sagas[0].saga_type == "type1"


class TestTracingService:
    """Test TracingService domain service."""

    @pytest.fixture
    def tracing_service(self):
        """Create tracing service for testing."""
        return TracingService()

    def test_start_and_complete_trace(self, tracing_service):
        """Test starting and completing a trace."""
        trace = tracing_service.start_trace("api-gateway", "handle_request", "trace-123")

        assert trace.trace_id == "trace-123"
        assert trace.root_service == "api-gateway"
        assert trace.status == TraceStatus.ACTIVE

        # Create and finish spans
        span1 = tracing_service.create_span("trace-123", "service1", "operation1")
        span2 = tracing_service.create_span("trace-123", "service2", "operation2", span1.span_id)

        assert span1 is not None
        assert span2 is not None
        assert span2.parent_span_id == span1.span_id

        # Finish spans and complete trace
        tracing_service.finish_span("trace-123", span1.span_id)
        tracing_service.finish_span("trace-123", span2.span_id)
        success = tracing_service.complete_trace("trace-123")

        assert success is True

        # Should be moved to completed traces
        completed_trace = tracing_service.get_trace("trace-123")
        assert completed_trace.status == TraceStatus.COMPLETED

    def test_get_service_traces(self, tracing_service):
        """Test getting traces for a specific service."""
        # Create traces with different services
        trace1 = tracing_service.start_trace("service1", "op1", "trace1")
        trace2 = tracing_service.start_trace("service2", "op2", "trace2")

        # Add spans
        tracing_service.create_span("trace1", "service1", "operation1")
        tracing_service.create_span("trace2", "service2", "operation2")
        tracing_service.create_span("trace2", "service1", "operation3")  # Service1 also in trace2

        # Complete traces
        tracing_service.complete_trace("trace1")
        tracing_service.complete_trace("trace2")

        # Get traces for service1
        service_traces = tracing_service.get_service_traces("service1", active_only=False)

        assert len(service_traces) == 2  # Both traces contain service1

    def test_get_tracing_stats(self, tracing_service):
        """Test getting tracing statistics."""
        # Create some traces
        trace1 = tracing_service.start_trace("service1", "op1")
        trace2 = tracing_service.start_trace("service2", "op2")

        tracing_service.create_span(trace1.trace_id, "service1", "op1")
        tracing_service.create_span(trace2.trace_id, "service2", "op2")

        stats = tracing_service.get_tracing_stats()

        assert stats["active_traces"] == 2
        assert stats["completed_traces"] == 0
        assert stats["total_spans"] == 2


class TestEventStreamingService:
    """Test EventStreamingService domain service."""

    @pytest.fixture
    def event_service(self):
        """Create event streaming service for testing."""
        return EventStreamingService()

    def test_publish_and_get_event_history(self, event_service):
        """Test publishing events and retrieving history."""
        # Publish events
        event_id1 = event_service.publish_event("user.created", {"user_id": 123}, "corr-1")
        event_id2 = event_service.publish_event("user.updated", {"user_id": 123}, "corr-1")
        event_id3 = event_service.publish_event("order.created", {"order_id": 456}, "corr-2")

        # Get all events
        history = event_service.get_event_history()
        assert len(history["events"]) == 3
        assert history["total"] == 3

        # Filter by correlation ID
        corr_history = event_service.get_event_history(correlation_id="corr-1")
        assert len(corr_history["events"]) == 2

        # Filter by event type
        type_history = event_service.get_event_history(event_type="user.created")
        assert len(type_history["events"]) == 1

    def test_replay_events(self, event_service):
        """Test replaying events."""
        event_service.publish_event("user.created", {"user_id": 123}, "corr-1")
        event_service.publish_event("order.created", {"order_id": 456}, "corr-2")

        # Replay user events
        result = event_service.replay_events(event_types=["user.created"])

        assert result["events_processed"] == 1
        assert result["event_types"] == ["user.created"]

    def test_clear_events(self, event_service):
        """Test clearing events."""
        event_service.publish_event("user.created", {"user_id": 123})
        event_service.publish_event("order.created", {"order_id": 456})

        # Clear all events
        result = event_service.clear_events()

        assert result["cleared_count"] == 2

        # Verify events are cleared
        history = event_service.get_event_history()
        assert len(history["events"]) == 0

    def test_get_event_stats(self, event_service):
        """Test getting event statistics."""
        # Empty stats
        stats = event_service.get_event_stats()
        assert stats["total_events"] == 0

        # Add events
        event_service.publish_event("user.created", {"user_id": 123})
        event_service.publish_event("user.created", {"user_id": 456})
        event_service.publish_event("order.created", {"order_id": 789})

        stats = event_service.get_event_stats()
        assert stats["total_events"] == 3
        assert stats["events_by_type"]["user.created"] == 2
        assert stats["events_by_type"]["order.created"] == 1
        assert "oldest_event" in stats
        assert "newest_event" in stats
