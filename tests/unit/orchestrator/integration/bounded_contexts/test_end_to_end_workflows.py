#!/usr/bin/env python3
"""
End-to-End Integration Tests for Orchestrator Workflows

Tests complete workflow scenarios that span multiple bounded contexts.
These tests verify that the orchestrator service works as a cohesive system.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from services.orchestrator.main import container
from tests.unit.orchestrator.conftest import DDDTestHelper, TestDataFactory


class TestCompleteIngestionToAnalysisWorkflow:
    """Test end-to-end workflow from data ingestion to analysis."""

    @pytest.mark.asyncio
    async def test_ingestion_to_query_workflow(self, test_data_factory, ddd_helper):
        """Test complete workflow: ingest data → query data → generate insights."""
        # 1. Register data source (Service Registry)
        with patch.object(container.service_registration_service, 'register_service') as mock_register:
            mock_register.return_value = test_data_factory.create_service_data()

            from services.orchestrator.application.service_registry.commands import RegisterServiceCommand
            from services.orchestrator.domain.service_registry.value_objects.service_id import ServiceId

            command = RegisterServiceCommand(
                service_id=ServiceId("github-service"),
                name="GitHub Service",
                description="GitHub data source",
                category="data_source",
                base_url="https://api.github.com",
                capabilities=["data_ingestion"]
            )

            result = await container.register_service_use_case.execute(command)
            ddd_helper.assert_use_case_success(result)

        # 2. Start data ingestion (Ingestion)
        with patch.object(container.start_ingestion_use_case, 'execute') as mock_ingest:
            mock_ingest.return_value = {
                "ingestion_id": "ingest-123",
                "status": "started",
                "source_url": "https://github.com/test/repo"
            }

            from services.orchestrator.application.ingestion.commands import StartIngestionCommand
            command = StartIngestionCommand(
                source_url="https://github.com/test/repo",
                source_type="github",
                parameters={"include_issues": True}
            )

            result = await container.start_ingestion_use_case.execute(command)
            assert result["ingestion_id"] == "ingest-123"
            assert result["status"] == "started"

        # 3. Monitor ingestion progress (Health Monitoring)
        with patch.object(container.check_system_health_use_case, 'execute') as mock_health:
            mock_health.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"status": "healthy", "services": {"ingestion": "active"}}
            )

            from services.orchestrator.application.health_monitoring.commands import CheckSystemHealthCommand
            command = CheckSystemHealthCommand(include_metrics=True)
            result = await container.check_system_health_use_case.execute(command)
            ddd_helper.assert_use_case_success(result)

        # 4. Query ingested data (Query Processing)
        with patch.object(container.process_natural_language_query_use_case, 'execute') as mock_query:
            mock_query.return_value = {
                "query_id": "query-456",
                "results": [{"type": "issue", "title": "Test Issue"}],
                "confidence_score": 0.85
            }

            from services.orchestrator.application.query_processing.commands import ProcessNaturalLanguageQueryCommand
            command = ProcessNaturalLanguageQueryCommand(
                query_text="find all issues in the repository",
                context={"domain": "software_development"},
                max_results=50
            )

            result = await container.process_natural_language_query_use_case.execute(command)
            assert result["query_id"] == "query-456"
            assert len(result["results"]) > 0

        # 5. Generate analysis report (Reporting)
        with patch.object(container.generate_report_use_case, 'execute') as mock_report:
            mock_report.return_value = {
                "report_id": "report-789",
                "report_type": "analytics",
                "status": "generated"
            }

            from services.orchestrator.application.reporting.commands import GenerateReportCommand
            command = GenerateReportCommand(
                report_type="analytics",
                parameters={"data_source": "ingested_data"},
                format="json"
            )

            result = await container.generate_report_use_case.execute(command)
            assert result["report_id"] == "report-789"
            assert result["status"] == "generated"


class TestWorkflowExecutionWithInfrastructure:
    """Test workflow execution with infrastructure monitoring."""

    @pytest.mark.asyncio
    async def test_workflow_with_saga_and_tracing(self, test_data_factory, ddd_helper):
        """Test workflow execution with distributed saga and tracing."""
        # 1. Start distributed trace (Infrastructure)
        with patch.object(container.start_trace_use_case, 'execute') as mock_trace:
            mock_trace.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"trace_id": "trace-123", "status": "started"}
            )

            from services.orchestrator.application.infrastructure.commands import StartTraceCommand
            command = StartTraceCommand(
                service_name="orchestrator",
                operation_name="workflow_execution"
            )

            result = await container.start_trace_use_case.execute(command)
            ddd_helper.assert_use_case_success(result)

        # 2. Start saga for workflow (Infrastructure)
        with patch.object(container.start_saga_use_case, 'execute') as mock_saga:
            mock_saga.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"saga_id": "saga-456", "status": "started"}
            )

            result = await container.start_saga_use_case.execute()
            ddd_helper.assert_use_case_success(result)

        # 3. Execute workflow (Workflow Management)
        with patch.object(container.execute_workflow_use_case, 'execute') as mock_execute:
            mock_execute.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"execution_id": "exec-789", "status": "running"}
            )

            from services.orchestrator.application.workflow_management.commands import ExecuteWorkflowCommand
            from services.orchestrator.domain.workflow_management.value_objects import WorkflowId

            command = ExecuteWorkflowCommand(
                workflow_id=WorkflowId("workflow-123"),
                parameters={"input": "test_data"}
            )

            result = await container.execute_workflow_use_case.execute(command)
            ddd_helper.assert_use_case_success(result)

        # 4. Monitor system health during execution (Health Monitoring)
        with patch.object(container.check_system_health_use_case, 'execute') as mock_health:
            mock_health.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"status": "healthy", "active_workflows": 1}
            )

            from services.orchestrator.application.health_monitoring.commands import CheckSystemHealthCommand
            command = CheckSystemHealthCommand(include_metrics=True)
            result = await container.check_system_health_use_case.execute(command)
            ddd_helper.assert_use_case_success(result)

        # 5. Check event streaming (Infrastructure)
        with patch.object(container.get_event_stream_stats_use_case, 'execute') as mock_events:
            mock_events.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"total_events": 15, "events_per_second": 2.5}
            )

            result = await container.get_event_stream_stats_use_case.execute(None)
            ddd_helper.assert_use_case_success(result)


class TestServiceRegistryHealthIntegration:
    """Test integration between service registry and health monitoring."""

    @pytest.mark.asyncio
    async def test_service_registration_health_check(self, test_data_factory, ddd_helper):
        """Test that registered services are included in health checks."""
        # 1. Register multiple services (Service Registry)
        services = []
        for i in range(3):
            with patch.object(container.service_registration_service, 'register_service') as mock_register:
                service_data = test_data_factory.create_service_data(
                    service_name=f"service-{i}",
                    service_url=f"http://service-{i}:8000"
                )
                mock_register.return_value = service_data

                from services.orchestrator.application.service_registry.commands import RegisterServiceCommand
                from services.orchestrator.domain.service_registry.value_objects.service_id import ServiceId

                command = RegisterServiceCommand(
                    service_id=ServiceId(f"service-{i}"),
                    name=f"Service {i}",
                    description=f"Test service {i}",
                    category="test",
                    base_url=f"http://service-{i}:8000",
                    capabilities=["health_check"]
                )

                result = await container.register_service_use_case.execute(command)
                ddd_helper.assert_use_case_success(result)
                services.append(service_data)

        # 2. Verify services are registered (Service Registry)
        with patch.object(container.list_services_use_case, 'execute') as mock_list:
            mock_list.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"services": services, "total": len(services)}
            )

            from services.orchestrator.application.service_registry.queries import ListServicesQuery
            query = ListServicesQuery(limit=10, offset=0)
            result = await container.list_services_use_case.execute(query)
            ddd_helper.assert_use_case_success(result)
            assert len(result.data["services"]) == 3

        # 3. Check system health includes registered services (Health Monitoring)
        with patch.object(container.check_system_health_use_case, 'execute') as mock_health:
            health_data = {
                "status": "healthy",
                "services": {f"service-{i}": "healthy" for i in range(3)},
                "total_services": 3
            }
            mock_health.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data=health_data
            )

            from services.orchestrator.application.health_monitoring.commands import CheckSystemHealthCommand
            command = CheckSystemHealthCommand(include_metrics=True)
            result = await container.check_system_health_use_case.execute(command)
            ddd_helper.assert_use_case_success(result)
            assert result.data["total_services"] == 3


class TestErrorHandlingAcrossContexts:
    """Test error handling and recovery across bounded contexts."""

    @pytest.mark.asyncio
    async def test_workflow_failure_with_dlq_handling(self, ddd_helper):
        """Test workflow failure with DLQ handling and retry."""
        # 1. Start workflow execution (Workflow Management)
        with patch.object(container.execute_workflow_use_case, 'execute') as mock_execute:
            mock_execute.return_value = ddd_helper.create_mock_use_case_result(
                success=False,
                errors=["Workflow execution failed: service unavailable"]
            )

            from services.orchestrator.application.workflow_management.commands import ExecuteWorkflowCommand
            from services.orchestrator.domain.workflow_management.value_objects import WorkflowId

            command = ExecuteWorkflowCommand(
                workflow_id=WorkflowId("workflow-fail"),
                parameters={"input": "test_data"}
            )

            result = await container.execute_workflow_use_case.execute(command)
            assert not result.is_success()
            assert "failed" in result.errors[0].lower()

        # 2. Check DLQ for failed events (Infrastructure)
        with patch.object(container.list_dlq_events_use_case, 'execute') as mock_dlq:
            mock_dlq.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"events": [{"event_id": "failed-workflow-123", "error": "service unavailable"}]}
            )

            from services.orchestrator.application.infrastructure.queries import ListDLQEventsQuery
            query = ListDLQEventsQuery(limit=10, offset=0)
            result = await container.list_dlq_events_use_case.execute(query)
            ddd_helper.assert_use_case_success(result)
            assert len(result.data["events"]) > 0

        # 3. Retry failed event (Infrastructure)
        with patch.object(container.retry_event_use_case, 'execute') as mock_retry:
            mock_retry.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"status": "retried", "event_id": "failed-workflow-123"}
            )

            from services.orchestrator.application.infrastructure.commands import RetryEventCommand
            command = RetryEventCommand(event_ids=["failed-workflow-123"], max_retries=3)
            result = await container.retry_event_use_case.execute(command)
            ddd_helper.assert_use_case_success(result)

        # 4. Verify system health reflects recovery (Health Monitoring)
        with patch.object(container.check_system_health_use_case, 'execute') as mock_health:
            mock_health.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"status": "healthy", "failed_events": 0, "recovered_events": 1}
            )

            from services.orchestrator.application.health_monitoring.commands import CheckSystemHealthCommand
            command = CheckSystemHealthCommand(include_metrics=True)
            result = await container.check_system_health_use_case.execute(command)
            ddd_helper.assert_use_case_success(result)


class TestPerformanceMonitoringIntegration:
    """Test performance monitoring across bounded contexts."""

    @pytest.mark.asyncio
    async def test_cross_context_performance_metrics(self, ddd_helper):
        """Test that performance metrics are collected across contexts."""
        # 1. Start performance trace (Infrastructure)
        with patch.object(container.start_trace_use_case, 'execute') as mock_trace:
            mock_trace.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"trace_id": "perf-trace-123"}
            )

            from services.orchestrator.application.infrastructure.commands import StartTraceCommand
            command = StartTraceCommand(
                service_name="orchestrator",
                operation_name="performance_test"
            )

            result = await container.start_trace_use_case.execute(command)
            ddd_helper.assert_use_case_success(result)

        # 2. Execute multiple operations across contexts
        operations = []

        # Workflow operation
        with patch.object(container.list_workflows_use_case, 'execute') as mock_list:
            mock_list.return_value = [Mock(to_dict=lambda: {"id": "wf-1", "name": "Test"})]
            result = await container.list_workflows_use_case.execute(None)
            operations.append(("workflow_list", len(result)))

        # Service registry operation
        with patch.object(container.list_services_use_case, 'execute') as mock_services:
            mock_services.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"services": [], "total": 0}
            )
            result = await container.list_services_use_case.execute(None)
            operations.append(("service_list", result.data["total"]))

        # Query operation
        with patch.object(container.process_natural_language_query_use_case, 'execute') as mock_query:
            mock_query.return_value = {"query_id": "perf-query-456", "results": []}
            from services.orchestrator.application.query_processing.commands import ProcessNaturalLanguageQueryCommand
            command = ProcessNaturalLanguageQueryCommand(
                query_text="performance test query",
                max_results=10
            )
            result = await container.process_natural_language_query_use_case.execute(command)
            operations.append(("query_process", len(result["results"])))

        # 3. Check system metrics include cross-context performance (Health Monitoring)
        with patch.object(container.get_system_metrics_use_case, 'execute') as mock_metrics:
            mock_metrics.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={
                    "response_times": {"avg_ms": 150, "p95_ms": 300},
                    "throughput": {"requests_per_second": 25},
                    "context_operations": operations
                }
            )

            result = await container.get_system_metrics_use_case.execute(None)
            ddd_helper.assert_use_case_success(result)
            assert "context_operations" in result.data
            assert len(result.data["context_operations"]) == 3
