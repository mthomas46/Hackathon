#!/usr/bin/env python3
"""
Domain Layer Tests for Infrastructure Value Objects

Tests the core domain value objects for infrastructure monitoring including DLQ, sagas, tracing, and event streaming.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from services.orchestrator.domain.infrastructure.value_objects import (
    EventStatus, SagaStatus, TraceStatus,
    DLQEvent, SagaInstance, SagaStep, TraceSpan, DistributedTrace
)
from services.orchestrator.domain.infrastructure.services import (
    DLQService, SagaService, TracingService, EventStreamingService
)


class TestEventStatus:
    """Test EventStatus enum."""

    def test_event_status_values(self):
        """Test event status enum values."""
        assert EventStatus.PENDING.value == "pending"
        assert EventStatus.PROCESSING.value == "processing"
        assert EventStatus.COMPLETED.value == "completed"
        assert EventStatus.FAILED.value == "failed"
        assert EventStatus.RETRIED.value == "retried"
        assert EventStatus.DLQ.value == "dlq"
        assert EventStatus.EXPIRED.value == "expired"

    def test_is_final_property(self):
        """Test is_final property."""
        assert EventStatus.COMPLETED.is_final is True
        assert EventStatus.DLQ.is_final is True
        assert EventStatus.EXPIRED.is_final is True
        assert EventStatus.PENDING.is_final is False
        assert EventStatus.FAILED.is_final is False

    def test_can_retry_property(self):
        """Test can_retry property."""
        assert EventStatus.FAILED.can_retry is True
        assert EventStatus.RETRIED.can_retry is True
        assert EventStatus.COMPLETED.can_retry is False
        assert EventStatus.DLQ.can_retry is False


class TestSagaStatus:
    """Test SagaStatus enum."""

    def test_saga_status_values(self):
        """Test saga status enum values."""
        assert SagaStatus.PENDING.value == "pending"
        assert SagaStatus.STARTED.value == "started"
        assert SagaStatus.COMPENSATING.value == "compensating"
        assert SagaStatus.COMPLETED.value == "completed"
        assert SagaStatus.FAILED.value == "failed"
        assert SagaStatus.ABORTED.value == "aborted"

    def test_is_active_property(self):
        """Test is_active property."""
        assert SagaStatus.STARTED.is_active is True
        assert SagaStatus.COMPENSATING.is_active is True
        assert SagaStatus.PENDING.is_active is False
        assert SagaStatus.COMPLETED.is_active is False

    def test_is_final_property(self):
        """Test is_final property."""
        assert SagaStatus.COMPLETED.is_final is True
        assert SagaStatus.FAILED.is_final is True
        assert SagaStatus.ABORTED.is_final is True
        assert SagaStatus.STARTED.is_final is False

    def test_is_successful_property(self):
        """Test is_successful property."""
        assert SagaStatus.COMPLETED.is_successful is True
        assert SagaStatus.FAILED.is_successful is False
        assert SagaStatus.STARTED.is_successful is False


class TestTraceStatus:
    """Test TraceStatus enum."""

    def test_trace_status_values(self):
        """Test trace status enum values."""
        assert TraceStatus.ACTIVE.value == "active"
        assert TraceStatus.COMPLETED.value == "completed"
        assert TraceStatus.FAILED.value == "failed"
        assert TraceStatus.TIMEOUT.value == "timeout"

    def test_is_final_property(self):
        """Test is_final property."""
        assert TraceStatus.COMPLETED.is_final is True
        assert TraceStatus.FAILED.is_final is True
        assert TraceStatus.TIMEOUT.is_final is True
        assert TraceStatus.ACTIVE.is_final is False

    def test_is_successful_property(self):
        """Test is_successful property."""
        assert TraceStatus.COMPLETED.is_successful is True
        assert TraceStatus.FAILED.is_successful is False
        assert TraceStatus.ACTIVE.is_successful is False


class TestDLQEvent:
    """Test DLQEvent value object."""

    def test_create_dlq_event(self):
        """Test creating a DLQ event."""
        original_timestamp = datetime.utcnow()

        dlq_event = DLQEvent(
            event_id="event-123",
            event_type="user.created",
            event_data={"user_id": 123, "name": "John"},
            failure_reason="Database connection failed",
            original_timestamp=original_timestamp,
            correlation_id="corr-456",
            service_name="user-service",
            error_details={"error_code": "DB_ERROR"}
        )

        assert dlq_event.event_id == "event-123"
        assert dlq_event.event_type == "user.created"
        assert dlq_event.failure_reason == "Database connection failed"
        assert dlq_event.correlation_id == "corr-456"
        assert dlq_event.service_name == "user-service"
        assert dlq_event.can_retry is True
        assert dlq_event.retry_count == 0

    def test_retry_functionality(self):
        """Test retry functionality."""
        dlq_event = DLQEvent(
            event_id="event-123",
            event_type="user.created",
            event_data={"user_id": 123},
            failure_reason="Connection failed",
            original_timestamp=datetime.utcnow()
        )

        # Should be able to retry initially
        assert dlq_event.can_retry is True
        assert dlq_event.increment_retry_count() is True
        assert dlq_event.retry_count == 1

        # Should exhaust retries after max_retries
        dlq_event._max_retries = 1
        assert dlq_event.increment_retry_count() is False
        assert dlq_event.can_retry is False

    def test_to_dict(self):
        """Test converting DLQ event to dictionary."""
        dlq_event = DLQEvent(
            event_id="event-123",
            event_type="user.created",
            event_data={"user_id": 123},
            failure_reason="Connection failed",
            original_timestamp=datetime.utcnow()
        )

        data = dlq_event.to_dict()

        assert data["event_id"] == "event-123"
        assert data["event_type"] == "user.created"
        assert data["failure_reason"] == "Connection failed"
        assert data["can_retry"] is True
        assert "dlq_timestamp" in data
        assert "age_seconds" in data


class TestSagaInstance:
    """Test SagaInstance value object."""

    def test_create_saga_instance(self):
        """Test creating a saga instance."""
        steps = [
            SagaStep("step1", "service1", "create_user"),
            SagaStep("step2", "service2", "send_email", "delete_user")
        ]

        saga = SagaInstance(
            saga_type="user_registration",
            correlation_id="corr-123",
            steps=steps,
            metadata={"user_id": 123}
        )

        assert saga.saga_type == "user_registration"
        assert saga.correlation_id == "corr-123"
        assert len(saga.steps) == 2
        assert saga.status == SagaStatus.PENDING
        assert saga.current_step is None

    def test_saga_lifecycle(self):
        """Test saga lifecycle."""
        steps = [SagaStep("step1", "service1", "create_user")]
        saga = SagaInstance("test_saga", "corr-123", steps)

        # Start saga
        saga.start()
        assert saga.status == SagaStatus.STARTED
        assert saga.started_at is not None
        assert saga.current_step.step_id == "step1"

        # Complete step
        saga.complete_step("step1")
        assert saga.steps[0].status == "completed"

        # Complete saga
        saga.complete()
        assert saga.status == SagaStatus.COMPLETED
        assert saga.completed_at is not None

    def test_saga_failure_and_compensation(self):
        """Test saga failure and compensation."""
        steps = [
            SagaStep("step1", "service1", "create_user", "delete_user"),
            SagaStep("step2", "service2", "send_email")
        ]
        saga = SagaInstance("test_saga", "corr-123", steps)

        saga.start()
        saga.fail_step("step1", "Database error")

        # Should start compensation phase but stay in STARTED status until compensation completes
        assert saga.status == SagaStatus.STARTED  # Compensation is triggered but saga is still active
        assert saga.steps[0].status == "failed"   # First step should be marked as failed

    def test_to_dict(self):
        """Test converting saga to dictionary."""
        steps = [SagaStep("step1", "service1", "create_user")]
        saga = SagaInstance("test_saga", "corr-123", steps)

        data = saga.to_dict()

        assert data["saga_type"] == "test_saga"
        assert data["correlation_id"] == "corr-123"
        assert len(data["steps"]) == 1
        assert data["status"] == "pending"


class TestTraceSpan:
    """Test TraceSpan value object."""

    def test_create_trace_span(self):
        """Test creating a trace span."""
        start_time = datetime.utcnow()

        span = TraceSpan(
            span_id="span-123",
            service_name="user-service",
            operation_name="create_user",
            parent_span_id="parent-456",
            tags={"user_id": 123}
        )

        assert span.span_id == "span-123"
        assert span.service_name == "user-service"
        assert span.operation_name == "create_user"
        assert span.parent_span_id == "parent-456"
        assert span.tags == {"user_id": 123}
        assert span.end_time is None

    def test_finish_span(self):
        """Test finishing a span."""
        span = TraceSpan(span_id="span-123", service_name="service1", operation_name="operation1")

        assert span.end_time is None

        span.finish()

        assert span.end_time is not None
        assert span.duration_microseconds is not None

    def test_add_log(self):
        """Test adding logs to span."""
        span = TraceSpan(span_id="span-123", service_name="service1", operation_name="operation1")

        span.log("Starting operation", fields={"param": "value"})

        assert len(span.logs) == 1
        assert span.logs[0]["event"] == "Starting operation"
        assert span.logs[0]["fields"] == {"param": "value"}

    def test_to_dict(self):
        """Test converting span to dictionary."""
        span = TraceSpan(span_id="span-123", service_name="service1", operation_name="operation1", tags={"key": "value"})
        span.finish()

        data = span.to_dict()

        assert data["span_id"] == "span-123"
        assert data["service_name"] == "service1"
        assert data["operation_name"] == "operation1"
        assert data["start_time"] is not None
        assert data["tags"] == {"key": "value"}
        assert "start_time" in data
        assert "end_time" in data
        assert "duration_microseconds" in data


class TestDistributedTrace:
    """Test DistributedTrace value object."""

    def test_create_distributed_trace(self):
        """Test creating a distributed trace."""
        trace = DistributedTrace(
            trace_id="trace-123",
            root_service="api-gateway",
            root_operation="handle_request",
            metadata={"request_id": "req-456"}
        )

        assert trace.trace_id == "trace-123"
        assert trace.root_service == "api-gateway"
        assert trace.root_operation == "handle_request"
        assert trace.status == TraceStatus.ACTIVE
        assert len(trace.spans) == 0

    def test_add_and_complete_trace(self):
        """Test adding spans and completing trace."""
        trace = DistributedTrace("trace-123", "service1", "operation1")

        span1 = TraceSpan(span_id="span1", service_name="service1", operation_name="operation1")
        span2 = TraceSpan(span_id="span2", service_name="service2", operation_name="operation2", parent_span_id="span1")

        trace.add_span(span1)
        trace.add_span(span2)

        assert trace.span_count == 2
        assert trace.service_count == 2

        # Complete spans and trace
        span1.finish()
        span2.finish()
        trace.complete()

        assert trace.status == TraceStatus.COMPLETED
        assert trace.duration_microseconds is not None

    def test_get_spans_by_service(self):
        """Test getting spans by service."""
        trace = DistributedTrace("trace-123", "service1", "operation1")

        span1 = TraceSpan("span1", service_name="service1", operation_name="op1")
        span2 = TraceSpan("span2", service_name="service2", operation_name="op2")
        span3 = TraceSpan("span3", service_name="service1", operation_name="op3")

        trace.add_span(span1)
        trace.add_span(span2)
        trace.add_span(span3)

        service1_spans = trace.get_spans_by_service("service1")
        assert len(service1_spans) == 2

        service2_spans = trace.get_spans_by_service("service2")
        assert len(service2_spans) == 1


