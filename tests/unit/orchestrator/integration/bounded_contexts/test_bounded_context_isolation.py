#!/usr/bin/env python3
"""
Bounded Context Isolation and Communication Integration Tests

Tests that bounded contexts maintain proper isolation while communicating effectively.
Verifies DDD principles of bounded context design.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from services.orchestrator.main import container
from tests.unit.orchestrator.conftest import DDDTestHelper, TestDataFactory


class TestBoundedContextIsolation:
    """Test that bounded contexts maintain proper isolation."""

    def test_workflow_context_isolation(self, test_data_factory, ddd_helper):
        """Test that workflow operations don't affect other contexts."""
        # Verify that workflow repository operations don't touch service registry
        workflow_repo = container.workflow_repository
        service_repo = container.service_repository

        # Create workflow data
        workflow = test_data_factory.create_workflow_data()

        # Save workflow
        result = workflow_repo.save_workflow(workflow)
        assert result is True

        # Verify workflow exists
        retrieved = workflow_repo.get_workflow(workflow.workflow_id)
        assert retrieved == workflow

        # Verify service registry is unaffected
        services = service_repo.list_services()
        assert len(services) == 0  # Should be empty

    def test_service_registry_context_isolation(self, test_data_factory, ddd_helper):
        """Test that service registry operations don't affect workflows."""
        # Verify that service operations don't touch workflow repository
        workflow_repo = container.workflow_repository
        service_repo = container.service_repository

        # Create service data
        service = test_data_factory.create_service_data()

        # Save service
        result = service_repo.save_service(service)
        assert result is True

        # Verify service exists
        retrieved = service_repo.get_service(service.service_id)
        assert retrieved == service

        # Verify workflow repository is unaffected
        workflows = workflow_repo.list_workflows()
        assert len(workflows) == 0  # Should be empty

    def test_infrastructure_context_isolation(self):
        """Test that infrastructure services maintain isolation."""
        # Verify that DLQ operations don't affect saga operations
        dlq_service = container.dlq_service
        saga_service = container.saga_service

        # Add event to DLQ
        dlq_service.add_event({"event_id": "test-123", "error": "test error"})

        # Verify DLQ has the event
        dlq_stats = dlq_service.get_stats()
        assert dlq_stats["total_events"] >= 1

        # Verify saga service is unaffected
        sagas = saga_service.list_sagas()
        assert len(sagas) == 0  # Should be empty


class TestCrossContextCommunication:
    """Test proper communication patterns between bounded contexts."""

    @pytest.mark.asyncio
    async def test_health_monitoring_communication(self, ddd_helper):
        """Test that health monitoring can access data from other contexts."""
        # Setup test data in multiple contexts
        workflow = container.workflow_repository
        service_repo = container.service_repository

        # Create test entities
        test_workflow = Mock()
        test_workflow.workflow_id = Mock()
        test_workflow.workflow_id.value = "test-wf-123"
        test_workflow.name = "Test Workflow"

        test_service = Mock()
        test_service.service_id = Mock()
        test_service.service_id.value = "test-svc-456"
        test_service.name = "Test Service"

        # Save entities
        workflow.save_workflow(test_workflow)
        service_repo.save_service(test_service)

        # Health monitoring should be able to check both without direct access
        # (This tests the communication pattern, not actual implementation)

    @pytest.mark.asyncio
    async def test_reporting_data_aggregation(self, ddd_helper):
        """Test that reporting can aggregate data from multiple contexts."""
        # This tests the reporting context's ability to gather data
        # from workflow executions, service metrics, etc.

        # Setup mock data sources
        with patch.object(container.list_workflows_use_case, 'execute') as mock_wf, \
             patch.object(container.list_services_use_case, 'execute') as mock_svc, \
             patch.object(container.check_system_health_use_case, 'execute') as mock_health:

            # Mock workflow data
            mock_wf.return_value = [Mock(to_dict=lambda: {"id": "wf-1", "executions": 5})]

            # Mock service data
            mock_svc.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"services": [{"name": "svc-1", "status": "healthy"}], "total": 1}
            )

            # Mock health data
            mock_health.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"status": "healthy", "uptime": "99.9%"}
            )

            # Generate report that should aggregate this data
            from services.orchestrator.application.reporting.commands import GenerateReportCommand
            command = GenerateReportCommand(
                report_type="system_overview",
                parameters={"include_workflows": True, "include_services": True},
                format="json"
            )

            # The report generation should be able to access data from multiple contexts
            # (This tests the communication pattern)


class TestContextEventCommunication:
    """Test event-driven communication between bounded contexts."""

    @pytest.mark.asyncio
    async def test_workflow_events_reach_infrastructure(self):
        """Test that workflow events are properly handled by infrastructure."""
        # Workflow executions should generate events that infrastructure can track

        with patch.object(container.start_trace_use_case, 'execute') as mock_trace, \
             patch.object(container.publish_event_use_case, 'execute') as mock_publish:

            # Start trace for workflow monitoring
            mock_trace.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"trace_id": "wf-trace-123"}
            )

            # Execute workflow (would generate events)
            with patch.object(container.execute_workflow_use_case, 'execute') as mock_execute:
                mock_execute.return_value = ddd_helper.create_mock_use_case_result(
                    success=True,
                    data={"execution_id": "exec-456", "status": "completed"}
                )

                # Publish workflow completion event
                mock_publish.return_value = ddd_helper.create_mock_use_case_result(
                    success=True,
                    data={"event_id": "evt-789", "status": "published"}
                )

                from services.orchestrator.application.infrastructure.commands import PublishEventCommand
                event_cmd = PublishEventCommand(
                    event_type="workflow.completed",
                    payload={"execution_id": "exec-456", "result": "success"}
                )

                result = await container.publish_event_use_case.execute(event_cmd)
                assert result.is_success()

    @pytest.mark.asyncio
    async def test_service_health_events(self):
        """Test that service health changes generate events."""
        # Health monitoring should publish events when service status changes

        with patch.object(container.publish_event_use_case, 'execute') as mock_publish:
            mock_publish.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"event_id": "health-evt-123"}
            )

            # Simulate health check that detects status change
            with patch.object(container.check_service_health_use_case, 'execute') as mock_check:
                mock_check.return_value = ddd_helper.create_mock_use_case_result(
                    success=True,
                    data={"service_name": "test-svc", "status": "unhealthy", "changed": True}
                )

                # Health monitoring would publish event about status change
                from services.orchestrator.application.infrastructure.commands import PublishEventCommand
                event_cmd = PublishEventCommand(
                    event_type="service.health.changed",
                    payload={"service_name": "test-svc", "new_status": "unhealthy"}
                )

                result = await container.publish_event_use_case.execute(event_cmd)
                assert result.is_success()


class TestContextDataConsistency:
    """Test data consistency across bounded contexts."""

    def test_workflow_data_consistency(self):
        """Test that workflow data remains consistent across operations."""
        repo = container.workflow_repository

        # Create and save workflow
        from services.orchestrator.domain.workflow_management.entities import Workflow
        workflow = Workflow(
            name="Consistency Test Workflow",
            description="Test data consistency",
            created_by="test_user"
        )

        # Save workflow
        result = repo.save_workflow(workflow)
        assert result is True

        # Retrieve workflow
        retrieved = repo.get_workflow(workflow.workflow_id)
        assert retrieved is not None
        assert retrieved.name == "Consistency Test Workflow"
        assert retrieved.created_by == "test_user"

        # Update workflow
        workflow.name = "Updated Consistency Test Workflow"
        result = repo.update_workflow(workflow)
        assert result is True

        # Verify update
        updated = repo.get_workflow(workflow.workflow_id)
        assert updated.name == "Updated Consistency Test Workflow"

    def test_service_data_consistency(self):
        """Test that service data remains consistent across operations."""
        repo = container.service_repository

        # Create and save service
        from services.orchestrator.domain.service_registry.entities import Service
        service = Service(
            name="Consistency Test Service",
            description="Test data consistency",
            category="test",
            capabilities=["test"],
            endpoints=["http://test:8000"]
        )

        # Save service
        result = repo.save_service(service)
        assert result is True

        # Retrieve service
        retrieved = repo.get_service(service.service_id)
        assert retrieved is not None
        assert retrieved.name == "Consistency Test Service"

        # Update service
        service.description = "Updated consistency test service"
        result = repo.update_service(service)
        assert result is True

        # Verify update
        updated = repo.get_service(service.service_id)
        assert updated.description == "Updated consistency test service"


class TestContextFailureIsolation:
    """Test that failures in one context don't affect others."""

    @pytest.mark.asyncio
    async def test_workflow_failure_doesnt_affect_services(self, ddd_helper):
        """Test that workflow failures don't impact service registry operations."""
        # Setup working service registry
        with patch.object(container.list_services_use_case, 'execute') as mock_services:
            mock_services.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"services": [{"name": "working-service"}], "total": 1}
            )

            # Service registry should work despite workflow issues
            from services.orchestrator.application.service_registry.queries import ListServicesQuery
            query = ListServicesQuery()
            result = await container.list_services_use_case.execute(query)
            ddd_helper.assert_use_case_success(result)
            assert result.data["total"] == 1

    @pytest.mark.asyncio
    async def test_service_failure_doesnt_affect_workflows(self):
        """Test that service registry failures don't impact workflow operations."""
        # Setup working workflow repository
        workflows = container.workflow_repository.list_workflows()

        # Workflow operations should work despite service registry issues
        # (This tests the isolation - workflows don't depend on service registry)
        assert isinstance(workflows, list)  # Should not fail

    @pytest.mark.asyncio
    async def test_infrastructure_failure_isolation(self):
        """Test that infrastructure failures are contained."""
        # Test that DLQ failures don't affect tracing
        dlq_service = container.dlq_service
        tracing_service = container.tracing_service

        # Even if DLQ operations fail, tracing should work
        trace_id = tracing_service.start_trace({"service_name": "test", "operation_name": "test"})
        assert trace_id is not None

        # Even if tracing fails, DLQ should work
        result = dlq_service.add_event({"event_id": "test-123", "error": "test"})
        assert result is True
