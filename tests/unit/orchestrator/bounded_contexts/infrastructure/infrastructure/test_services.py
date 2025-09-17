#!/usr/bin/env python3
"""
Infrastructure Layer Tests for All Bounded Contexts

Tests repositories, external services, and infrastructure components.
Consolidated into single file following DRY principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from services.orchestrator.infrastructure.persistence.in_memory import (
    InMemoryWorkflowRepository, InMemoryWorkflowExecutionRepository
)
from services.orchestrator.infrastructure.persistence.service_registry_repository import (
    InMemoryServiceRepository
)
from services.orchestrator.domain.infrastructure.services import (
    DLQService, SagaService, TracingService, EventStreamingService
)
from tests.unit.orchestrator.test_base import (
    BaseInfrastructureTest, WorkflowManagementTestMixin,
    ServiceRegistryTestMixin
)


class TestInMemoryWorkflowRepository(BaseInfrastructureTest, WorkflowManagementTestMixin):
    """Test InMemoryWorkflowRepository."""

    def get_repository_class(self):
        return InMemoryWorkflowRepository

    def test_save_and_get_workflow(self):
        """Test saving and retrieving a workflow."""
        repo = self.setup_repository()
        workflow = self.create_test_workflow()

        # Save
        result = repo.save_workflow(workflow)
        self.assert_repository_operation_success(result, True)

        # Get
        retrieved = repo.get_workflow(workflow.workflow_id)
        assert retrieved == workflow

    def test_list_workflows_with_filters(self):
        """Test listing workflows with filters."""
        repo = self.setup_repository()

        # Create test workflows
        wf1 = self.create_test_workflow(name="Test Workflow 1", tags=["tag1"])
        wf2 = self.create_test_workflow(name="Test Workflow 2", tags=["tag2"])
        repo.save_workflow(wf1)
        repo.save_workflow(wf2)

        # List with filter
        results = repo.list_workflows(name_filter="Workflow 1")
        assert len(results) == 1
        assert results[0] == wf1

    def test_update_workflow(self):
        """Test updating a workflow."""
        repo = self.setup_repository()
        workflow = self.create_test_workflow()
        repo.save_workflow(workflow)

        # Update
        workflow.name = "Updated Name"
        result = repo.update_workflow(workflow)
        self.assert_repository_operation_success(result, True)

        # Verify
        retrieved = repo.get_workflow(workflow.workflow_id)
        assert retrieved.name == "Updated Name"

    def test_delete_workflow(self):
        """Test deleting a workflow."""
        repo = self.setup_repository()
        workflow = self.create_test_workflow()
        repo.save_workflow(workflow)

        # Delete
        result = repo.delete_workflow(workflow.workflow_id)
        self.assert_repository_operation_success(result, True)

        # Verify
        retrieved = repo.get_workflow(workflow.workflow_id)
        assert retrieved is None


class TestInMemoryWorkflowExecutionRepository(BaseInfrastructureTest, WorkflowManagementTestMixin):
    """Test InMemoryWorkflowExecutionRepository."""

    def get_repository_class(self):
        return InMemoryWorkflowExecutionRepository

    def test_save_and_get_execution(self):
        """Test saving and retrieving a workflow execution."""
        repo = self.setup_repository()
        workflow = self.create_test_workflow()
        execution = self.create_test_execution(workflow)

        # Save
        result = repo.save_execution(execution)
        self.assert_repository_operation_success(result, True)

        # Get
        retrieved = repo.get_execution(execution.execution_id)
        assert retrieved == execution

    def test_list_executions_with_filters(self):
        """Test listing executions with filters."""
        repo = self.setup_repository()

        # Create test data
        wf1 = self.create_test_workflow()
        wf2 = self.create_test_workflow()
        exec1 = self.create_test_execution(wf1, status="completed")
        exec2 = self.create_test_execution(wf2, status="running")

        repo.save_execution(exec1)
        repo.save_execution(exec2)

        # List with status filter
        results = repo.list_executions(status_filter="completed")
        assert len(results) == 1
        assert results[0] == exec1


class TestInMemoryServiceRepository(BaseInfrastructureTest, ServiceRegistryTestMixin):
    """Test InMemoryServiceRepository."""

    def get_repository_class(self):
        return InMemoryServiceRepository

    def test_save_and_get_service(self):
        """Test saving and retrieving a service."""
        repo = self.setup_repository()
        service = self.create_test_service()

        # Save
        result = repo.save_service(service)
        self.assert_repository_operation_success(result, True)

        # Get
        retrieved = repo.get_service(service.service_id)
        assert retrieved == service

    def test_list_services(self):
        """Test listing all services."""
        repo = self.setup_repository()

        # Create test services
        svc1 = self.create_test_service(name="Service 1")
        svc2 = self.create_test_service(name="Service 2")
        repo.save_service(svc1)
        repo.save_service(svc2)

        # List
        results = repo.list_services()
        assert len(results) == 2
        assert svc1 in results
        assert svc2 in results

    def test_update_service(self):
        """Test updating a service."""
        repo = self.setup_repository()
        service = self.create_test_service()
        repo.save_service(service)

        # Update
        service.description = "Updated Description"
        result = repo.update_service(service)
        self.assert_repository_operation_success(result, True)

        # Verify
        retrieved = repo.get_service(service.service_id)
        assert retrieved.description == "Updated Description"

    def test_delete_service(self):
        """Test deleting a service."""
        repo = self.setup_repository()
        service = self.create_test_service()
        repo.save_service(service)

        # Delete
        result = repo.delete_service(service.service_id)
        self.assert_repository_operation_success(result, True)

        # Verify
        retrieved = repo.get_service(service.service_id)
        assert retrieved is None


class TestDLQService:
    """Test DLQService domain service."""

    def setup_method(self):
        """Setup test fixtures."""
        self.service = DLQService()

    def test_get_stats(self):
        """Test getting DLQ statistics."""
        stats = self.service.get_stats()
        assert isinstance(stats, dict)
        assert "total_events" in stats
        assert "failed_events" in stats

    def test_add_event(self):
        """Test adding an event to DLQ."""
        event_data = {"event_id": "test-123", "error": "Test error"}
        result = self.service.add_event(event_data)
        assert result is True

    def test_retry_event(self):
        """Test retrying an event from DLQ."""
        event_id = "test-123"
        result = self.service.retry_event(event_id)
        # May return False if event doesn't exist, but shouldn't error
        assert isinstance(result, bool)

    def test_clear_events(self):
        """Test clearing events from DLQ."""
        result = self.service.clear_events(before_timestamp="2024-01-01T00:00:00Z")
        assert isinstance(result, int)  # Should return count of cleared events


class TestSagaService:
    """Test SagaService domain service."""

    def setup_method(self):
        """Setup test fixtures."""
        self.service = SagaService()

    def test_start_saga(self):
        """Test starting a new saga."""
        saga_data = {"name": "Test Saga", "steps": []}
        saga_id = self.service.start_saga(saga_data)
        assert isinstance(saga_id, str)
        assert len(saga_id) > 0

    def test_get_saga(self):
        """Test getting a saga by ID."""
        saga_data = {"name": "Test Saga", "steps": []}
        saga_id = self.service.start_saga(saga_data)

        saga = self.service.get_saga(saga_id)
        assert saga is not None
        assert saga["saga_id"] == saga_id

    def test_execute_step(self):
        """Test executing a saga step."""
        saga_data = {"name": "Test Saga", "steps": []}
        saga_id = self.service.start_saga(saga_data)

        step_data = {"action": "test_action", "parameters": {}}
        result = self.service.execute_step(saga_id, step_data)
        assert isinstance(result, bool)

    def test_complete_saga(self):
        """Test completing a saga."""
        saga_data = {"name": "Test Saga", "steps": []}
        saga_id = self.service.start_saga(saga_data)

        result = self.service.complete_saga(saga_id)
        assert isinstance(result, bool)


class TestTracingService:
    """Test TracingService domain service."""

    def setup_method(self):
        """Setup test fixtures."""
        self.service = TracingService()

    def test_start_trace(self):
        """Test starting a new trace."""
        trace_data = {
            "service_name": "test_service",
            "operation_name": "test_operation"
        }
        trace_id = self.service.start_trace(trace_data)
        assert isinstance(trace_id, str)
        assert len(trace_id) > 0

    def test_add_span(self):
        """Test adding a span to a trace."""
        trace_data = {
            "service_name": "test_service",
            "operation_name": "test_operation"
        }
        trace_id = self.service.start_trace(trace_data)

        span_data = {
            "name": "test_span",
            "start_time": "2024-01-01T00:00:00Z",
            "duration_ms": 150
        }
        result = self.service.add_span(trace_id, span_data)
        assert isinstance(result, bool)

    def test_get_trace(self):
        """Test getting a trace by ID."""
        trace_data = {
            "service_name": "test_service",
            "operation_name": "test_operation"
        }
        trace_id = self.service.start_trace(trace_data)

        trace = self.service.get_trace(trace_id)
        assert trace is not None
        assert trace["trace_id"] == trace_id

    def test_list_traces(self):
        """Test listing traces."""
        traces = self.service.list_traces(limit=10)
        assert isinstance(traces, list)


class TestEventStreamingService:
    """Test EventStreamingService domain service."""

    def setup_method(self):
        """Setup test fixtures."""
        self.service = EventStreamingService()

    def test_publish_event(self):
        """Test publishing an event."""
        event_data = {
            "event_type": "test_event",
            "payload": {"message": "test"}
        }
        result = self.service.publish_event(event_data)
        assert isinstance(result, bool)

    def test_get_stats(self):
        """Test getting event streaming statistics."""
        stats = self.service.get_stats()
        assert isinstance(stats, dict)
        assert "total_events" in stats
        assert "events_per_second" in stats

    def test_subscribe_to_events(self):
        """Test subscribing to events."""
        def test_handler(event):
            pass

        result = self.service.subscribe("test_event", test_handler)
        assert isinstance(result, bool)
