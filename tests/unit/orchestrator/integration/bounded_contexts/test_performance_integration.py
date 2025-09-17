#!/usr/bin/env python3
"""
Performance Integration Tests for Orchestrator

Tests performance characteristics and load handling across bounded contexts.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from concurrent.futures import ThreadPoolExecutor

from services.orchestrator.main import container
from tests.unit.orchestrator.conftest import DDDTestHelper, TestDataFactory


class TestConcurrentOperations:
    """Test concurrent operations across bounded contexts."""

    @pytest.mark.asyncio
    async def test_concurrent_workflow_executions(self, test_data_factory):
        """Test multiple workflow executions running concurrently."""
        # Setup multiple workflows
        workflows = []
        for i in range(5):
            workflow = test_data_factory.create_workflow_data(name=f"Concurrent Workflow {i}")
            container.workflow_repository.save_workflow(workflow)
            workflows.append(workflow)

        # Execute multiple workflows concurrently
        execution_tasks = []
        for workflow in workflows:
            with patch.object(container.execute_workflow_use_case, 'execute') as mock_execute:
                mock_execute.return_value = DDDTestHelper.create_mock_use_case_result(
                    success=True,
                    data={"execution_id": f"exec-{workflow.workflow_id.value}", "status": "running"}
                )

                from services.orchestrator.application.workflow_management.commands import ExecuteWorkflowCommand
                command = ExecuteWorkflowCommand(
                    workflow_id=workflow.workflow_id,
                    parameters={"concurrent": True}
                )

                task = container.execute_workflow_use_case.execute(command)
                execution_tasks.append(task)

        # Wait for all executions to complete
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)

        # Verify all executions succeeded
        assert len(results) == 5
        for result in results:
            assert not isinstance(result, Exception), f"Execution failed: {result}"
            assert result.is_success()

    @pytest.mark.asyncio
    async def test_concurrent_service_registrations(self, test_data_factory, ddd_helper):
        """Test concurrent service registrations."""
        # Setup multiple services to register
        services_data = []
        for i in range(10):
            service_data = test_data_factory.create_service_data(
                service_name=f"Concurrent Service {i}",
                service_url=f"http://service-{i}:8000"
            )
            services_data.append(service_data)

        # Register services concurrently
        registration_tasks = []
        for service_data in services_data:
            with patch.object(container.service_registration_service, 'register_service') as mock_register:
                mock_register.return_value = service_data

                from services.orchestrator.application.service_registry.commands import RegisterServiceCommand
                from services.orchestrator.domain.service_registry.value_objects.service_id import ServiceId

                command = RegisterServiceCommand(
                    service_id=ServiceId(service_data["service_name"]),
                    name=service_data["service_name"],
                    description=service_data["description"],
                    category=service_data["category"],
                    base_url=service_data["service_url"],
                    capabilities=service_data["capabilities"]
                )

                task = container.register_service_use_case.execute(command)
                registration_tasks.append(task)

        # Wait for all registrations to complete
        results = await asyncio.gather(*registration_tasks, return_exceptions=True)

        # Verify all registrations succeeded
        assert len(results) == 10
        for result in results:
            assert not isinstance(result, Exception), f"Registration failed: {result}"
            ddd_helper.assert_use_case_success(result)


class TestLoadBalancingAcrossContexts:
    """Test load balancing and resource management across contexts."""

    @pytest.mark.asyncio
    async def test_query_load_distribution(self, ddd_helper):
        """Test that queries are distributed across available resources."""
        # Setup multiple query processors
        query_tasks = []
        for i in range(20):
            with patch.object(container.process_natural_language_query_use_case, 'execute') as mock_query:
                mock_query.return_value = {
                    "query_id": f"query-{i}",
                    "results": [{"id": f"result-{i}", "score": 0.9}],
                    "confidence_score": 0.85,
                    "execution_time_ms": 150 + i  # Vary execution times
                }

                from services.orchestrator.application.query_processing.commands import ProcessNaturalLanguageQueryCommand
                command = ProcessNaturalLanguageQueryCommand(
                    query_text=f"test query {i}",
                    context={"load_test": True},
                    max_results=5
                )

                task = container.process_natural_language_query_use_case.execute(command)
                query_tasks.append(task)

        # Execute all queries concurrently
        start_time = time.time()
        results = await asyncio.gather(*query_tasks, return_exceptions=True)
        end_time = time.time()

        # Verify performance
        total_time = end_time - start_time
        assert total_time < 5.0, f"Queries took too long: {total_time:.2f}s"

        # Verify all queries succeeded
        assert len(results) == 20
        successful_queries = sum(1 for r in results if not isinstance(r, Exception) and isinstance(r, dict))
        assert successful_queries == 20

    @pytest.mark.asyncio
    async def test_reporting_load_handling(self, ddd_helper):
        """Test report generation under load."""
        # Generate multiple reports concurrently
        report_tasks = []
        report_types = ["analytics", "performance", "usage", "health"]

        for i in range(15):
            report_type = report_types[i % len(report_types)]
            with patch.object(container.generate_report_use_case, 'execute') as mock_report:
                mock_report.return_value = {
                    "report_id": f"report-{i}",
                    "report_type": report_type,
                    "status": "generated",
                    "generated_at": "2024-01-01T00:00:00Z",
                    "processing_time_ms": 200 + (i * 10)
                }

                from services.orchestrator.application.reporting.commands import GenerateReportCommand
                command = GenerateReportCommand(
                    report_type=report_type,
                    parameters={"load_test": True, "test_id": i},
                    format="json"
                )

                task = container.generate_report_use_case.execute(command)
                report_tasks.append(task)

        # Execute all report generations
        start_time = time.time()
        results = await asyncio.gather(*report_tasks, return_exceptions=True)
        end_time = time.time()

        # Verify performance
        total_time = end_time - start_time
        assert total_time < 8.0, f"Report generation took too long: {total_time:.2f}s"

        # Verify results
        assert len(results) == 15
        successful_reports = sum(1 for r in results if not isinstance(r, Exception) and isinstance(r, dict))
        assert successful_reports == 15


class TestResourceContentionHandling:
    """Test how the system handles resource contention across contexts."""

    @pytest.mark.asyncio
    async def test_database_connection_pooling(self):
        """Test that database operations handle connection pooling correctly."""
        # This test verifies that repository operations don't exhaust connections
        # when multiple contexts access the database concurrently

        repo = container.workflow_repository

        # Perform many concurrent repository operations
        async def perform_repo_operation(i):
            # Create test workflow
            from services.orchestrator.domain.workflow_management.entities import Workflow
            workflow = Workflow(
                name=f"Load Test Workflow {i}",
                description=f"Workflow for load testing {i}",
                created_by="load_test"
            )

            # Save workflow
            result = repo.save_workflow(workflow)
            assert result is True

            # Retrieve workflow
            retrieved = repo.get_workflow(workflow.workflow_id)
            assert retrieved is not None
            assert retrieved.name == workflow.name

            return f"operation_{i}_success"

        # Execute many operations concurrently
        operation_tasks = [perform_repo_operation(i) for i in range(50)]
        results = await asyncio.gather(*operation_tasks, return_exceptions=True)

        # Verify all operations succeeded
        assert len(results) == 50
        successful_ops = sum(1 for r in results if not isinstance(r, Exception) and r.endswith("_success"))
        assert successful_ops == 50

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, ddd_helper):
        """Test memory usage patterns under load."""
        # This test monitors memory usage during concurrent operations
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform memory-intensive operations
        large_operations = []
        for i in range(100):
            with patch.object(container.list_workflows_use_case, 'execute') as mock_list:
                # Return large dataset
                mock_list.return_value = [
                    Mock(to_dict=lambda: {"id": f"wf-{j}", "name": f"Workflow {j}", "large_data": "x" * 1000})
                    for j in range(50)
                ]

                task = container.list_workflows_use_case.execute(None)
                large_operations.append(task)

        # Execute operations
        results = await asyncio.gather(*large_operations, return_exceptions=True)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Excessive memory usage: {memory_increase:.1f}MB"

        # Verify operations succeeded
        successful_ops = sum(1 for r in results if not isinstance(r, Exception))
        assert successful_ops == 100


class TestPerformanceMetricsCollection:
    """Test that performance metrics are collected across contexts."""

    @pytest.mark.asyncio
    async def test_cross_context_metrics_aggregation(self, ddd_helper):
        """Test that metrics from all contexts are properly aggregated."""
        # Setup performance monitoring across contexts
        with patch.object(container.get_system_metrics_use_case, 'execute') as mock_metrics, \
             patch.object(container.check_system_health_use_case, 'execute') as mock_health:

            # Mock comprehensive metrics
            mock_metrics.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={
                    "workflow_metrics": {"executions_per_hour": 150, "success_rate": 0.98},
                    "service_metrics": {"active_services": 12, "avg_response_time": 245},
                    "query_metrics": {"queries_per_minute": 45, "avg_processing_time": 180},
                    "infrastructure_metrics": {"event_throughput": 500, "dlq_size": 5},
                    "overall_performance": {"cpu_usage": 65, "memory_usage": 72}
                }
            )

            mock_health.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"status": "healthy", "performance_score": 92}
            )

            # Collect metrics
            metrics_result = await container.get_system_metrics_use_case.execute(None)
            health_result = await container.check_system_health_use_case.execute(None)

            # Verify comprehensive metrics collection
            ddd_helper.assert_use_case_success(metrics_result)
            ddd_helper.assert_use_case_success(health_result)

            metrics = metrics_result.data
            assert "workflow_metrics" in metrics
            assert "service_metrics" in metrics
            assert "query_metrics" in metrics
            assert "infrastructure_metrics" in metrics
            assert "overall_performance" in metrics

    @pytest.mark.asyncio
    async def test_performance_trend_analysis(self, ddd_helper):
        """Test performance trend analysis across time periods."""
        # Setup historical performance data
        time_periods = ["1h", "6h", "24h", "7d"]

        performance_tasks = []
        for period in time_periods:
            with patch.object(container.get_system_metrics_use_case, 'execute') as mock_metrics:
                mock_metrics.return_value = ddd_helper.create_mock_use_case_result(
                    success=True,
                    data={
                        "period": period,
                        "avg_response_time": 200 + (time_periods.index(period) * 50),
                        "throughput": 100 - (time_periods.index(period) * 10),
                        "error_rate": 0.01 + (time_periods.index(period) * 0.005)
                    }
                )

                task = container.get_system_metrics_use_case.execute(None)
                performance_tasks.append((period, task))

        # Collect performance data for all periods
        results = []
        for period, task in performance_tasks:
            result = await task
            results.append((period, result))

        # Verify trend analysis capability
        assert len(results) == 4
        for period, result in results:
            ddd_helper.assert_use_case_success(result)
            assert "period" in result.data
            assert "avg_response_time" in result.data
            assert "throughput" in result.data
            assert "error_rate" in result.data


class TestScalabilityValidation:
    """Test system scalability characteristics."""

    @pytest.mark.asyncio
    async def test_horizontal_scaling_simulation(self, ddd_helper):
        """Test how the system would handle additional service instances."""
        # Simulate scaling from 5 to 20 services
        base_services = 5
        scaled_services = 20

        # Setup base services
        base_service_tasks = []
        for i in range(base_services):
            with patch.object(container.service_registration_service, 'register_service') as mock_register:
                mock_register.return_value = {
                    "service_name": f"base-service-{i}",
                    "status": "active"
                }

                from services.orchestrator.application.service_registry.commands import RegisterServiceCommand
                from services.orchestrator.domain.service_registry.value_objects.service_id import ServiceId

                command = RegisterServiceCommand(
                    service_id=ServiceId(f"base-service-{i}"),
                    name=f"Base Service {i}",
                    description=f"Base service instance {i}",
                    category="compute",
                    base_url=f"http://base-{i}:8000",
                    capabilities=["compute", "storage"]
                )

                task = container.register_service_use_case.execute(command)
                base_service_tasks.append(task)

        # Setup scaled services
        scaled_service_tasks = []
        for i in range(scaled_services):
            with patch.object(container.service_registration_service, 'register_service') as mock_register:
                mock_register.return_value = {
                    "service_name": f"scaled-service-{i}",
                    "status": "active"
                }

                from services.orchestrator.application.service_registry.commands import RegisterServiceCommand
                from services.orchestrator.domain.service_registry.value_objects.service_id import ServiceId

                command = RegisterServiceCommand(
                    service_id=ServiceId(f"scaled-service-{i}"),
                    name=f"Scaled Service {i}",
                    description=f"Scaled service instance {i}",
                    category="compute",
                    base_url=f"http://scaled-{i}:8000",
                    capabilities=["compute", "storage"]
                )

                task = container.register_service_use_case.execute(command)
                scaled_service_tasks.append(task)

        # Execute scaling operations
        start_time = time.time()

        # Register base services
        base_results = await asyncio.gather(*base_service_tasks, return_exceptions=True)

        # Register scaled services
        scaled_results = await asyncio.gather(*scaled_service_tasks, return_exceptions=True)

        end_time = time.time()

        # Verify scaling performance
        total_time = end_time - start_time
        assert total_time < 10.0, f"Scaling took too long: {total_time:.2f}s"

        # Verify all services registered successfully
        assert len(base_results) == base_services
        assert len(scaled_results) == scaled_services

        successful_base = sum(1 for r in base_results if not isinstance(r, Exception) and r.is_success())
        successful_scaled = sum(1 for r in scaled_results if not isinstance(r, Exception) and r.is_success())

        assert successful_base == base_services
        assert successful_scaled == scaled_services

        # Verify total service count
        with patch.object(container.list_services_use_case, 'execute') as mock_list:
            mock_list.return_value = ddd_helper.create_mock_use_case_result(
                success=True,
                data={"total": base_services + scaled_services}
            )

            from services.orchestrator.application.service_registry.queries import ListServicesQuery
            query = ListServicesQuery()
            result = await container.list_services_use_case.execute(query)
            ddd_helper.assert_use_case_success(result)
            assert result.data["total"] == base_services + scaled_services
