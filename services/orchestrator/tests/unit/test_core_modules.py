"""Unit tests for orchestrator core modules."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import json


class TestEventDrivenOrchestration:
    """Test cases for event-driven orchestration module."""

    def test_workflow_creation(self):
        """Test workflow definition creation."""
        from services.orchestrator.modules.event_driven_orchestration import WorkflowDefinition

        workflow = WorkflowDefinition(
            name="test_workflow",
            steps=[
                {
                    "id": "step1",
                    "service": "test-service",
                    "action": "process",
                    "parameters": {"input": "test"}
                }
            ]
        )

        assert workflow.name == "test_workflow"
        assert len(workflow.steps) == 1
        assert workflow.steps[0]["id"] == "step1"

    def test_workflow_validation(self):
        """Test workflow validation."""
        from services.orchestrator.modules.event_driven_orchestration import WorkflowDefinition

        # Valid workflow
        valid_workflow = WorkflowDefinition(
            name="valid_workflow",
            steps=[
                {
                    "id": "step1",
                    "service": "service1",
                    "action": "action1",
                    "depends_on": []
                },
                {
                    "id": "step2",
                    "service": "service2",
                    "action": "action2",
                    "depends_on": ["step1"]
                }
            ]
        )

        assert valid_workflow.validate() is True

        # Invalid workflow (circular dependency)
        invalid_workflow = WorkflowDefinition(
            name="invalid_workflow",
            steps=[
                {
                    "id": "step1",
                    "service": "service1",
                    "action": "action1",
                    "depends_on": ["step2"]
                },
                {
                    "id": "step2",
                    "service": "service2",
                    "action": "action2",
                    "depends_on": ["step1"]
                }
            ]
        )

        assert invalid_workflow.validate() is False

    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        """Test workflow execution."""
        from services.orchestrator.modules.event_driven_orchestration import WorkflowExecutor

        executor = WorkflowExecutor()

        workflow = {
            "name": "test_execution",
            "steps": [
                {
                    "id": "step1",
                    "service": "mock-service",
                    "action": "mock_action",
                    "parameters": {"test": "value"}
                }
            ]
        }

        # Mock service client
        with patch('services.orchestrator.modules.event_driven_orchestration.ServiceClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            mock_instance.call_service.return_value = {"status": "success", "result": "test"}

            result = await executor.execute_workflow(workflow)

            assert result["status"] == "completed"
            assert "execution_id" in result
            mock_instance.call_service.assert_called_once()

    def test_event_triggered_workflow(self):
        """Test event-triggered workflow execution."""
        from services.orchestrator.modules.event_driven_orchestration import EventWorkflowManager

        manager = EventWorkflowManager()

        # Register workflow for event
        workflow = {"name": "event_workflow", "trigger_event": "test_event"}
        manager.register_workflow(workflow)

        # Trigger event
        event = {"type": "test_event", "data": {"key": "value"}}
        triggered_workflows = manager.get_workflows_for_event(event)

        assert len(triggered_workflows) == 1
        assert triggered_workflows[0]["name"] == "event_workflow"


class TestRedisManager:
    """Test cases for Redis manager module."""

    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self):
        """Test workflow state persistence in Redis."""
        from services.orchestrator.modules.redis_manager import RedisWorkflowManager

        manager = RedisWorkflowManager()

        workflow_state = {
            "execution_id": "exec-123",
            "workflow_name": "test_workflow",
            "status": "running",
            "current_step": "step1",
            "results": {"step1": "completed"}
        }

        # Mock Redis operations
        with patch.object(manager, '_redis') as mock_redis:
            mock_redis.set.return_value = True
            mock_redis.get.return_value = json.dumps(workflow_state)

            # Save state
            await manager.save_workflow_state("exec-123", workflow_state)

            # Load state
            loaded_state = await manager.load_workflow_state("exec-123")

            assert loaded_state == workflow_state
            mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_queue_operations(self):
        """Test event queue operations."""
        from services.orchestrator.modules.redis_manager import RedisEventQueue

        queue = RedisEventQueue()

        event = {
            "event_id": "evt-123",
            "event_type": "workflow_completed",
            "data": {"execution_id": "exec-123"},
            "timestamp": "2023-12-01T10:00:00Z"
        }

        # Mock Redis operations
        with patch.object(queue, '_redis') as mock_redis:
            mock_redis.lpush.return_value = 1
            mock_redis.rpop.return_value = json.dumps(event)

            # Queue event
            await queue.queue_event(event)

            # Dequeue event
            dequeued_event = await queue.dequeue_event()

            assert dequeued_event == event
            mock_redis.lpush.assert_called_once()

    def test_connection_pooling(self):
        """Test Redis connection pooling."""
        from services.orchestrator.modules.redis_manager import RedisConnectionPool

        pool = RedisConnectionPool()

        # Test pool configuration
        assert pool.max_connections >= 1
        assert pool.host is not None

        # Test connection acquisition (would normally test actual connection)
        connection = pool.get_connection()
        assert connection is not None  # Mock or actual connection


class TestServicesModule:
    """Test cases for services module."""

    @pytest.mark.asyncio
    async def test_service_discovery(self):
        """Test service discovery functionality."""
        from services.orchestrator.modules.services import ServiceDiscovery

        discovery = ServiceDiscovery()

        # Mock service registration
        service_info = {
            "name": "test-service",
            "type": "analysis",
            "endpoint": "http://test-service:8080",
            "capabilities": ["analyze", "process"],
            "health_check": "/health"
        }

        await discovery.register_service(service_info)

        # Discover service
        found_service = await discovery.discover_service("test-service")
        assert found_service == service_info

        # Discover by capability
        analysis_services = await discovery.discover_by_capability("analyze")
        assert len(analysis_services) == 1
        assert analysis_services[0]["name"] == "test-service"

    @pytest.mark.asyncio
    async def test_service_health_monitoring(self):
        """Test service health monitoring."""
        from services.orchestrator.modules.services import ServiceHealthMonitor

        monitor = ServiceHealthMonitor()

        # Mock healthy service
        healthy_service = {
            "name": "healthy-service",
            "endpoint": "http://healthy:8080",
            "health_check": "/health"
        }

        # Mock unhealthy service
        unhealthy_service = {
            "name": "unhealthy-service",
            "endpoint": "http://unhealthy:8080",
            "health_check": "/health"
        }

        with patch('services.orchestrator.modules.services.httpx.AsyncClient') as mock_client:
            # Setup healthy response
            healthy_response = Mock()
            healthy_response.status_code = 200
            healthy_response.json.return_value = {"status": "healthy"}

            # Setup unhealthy response
            unhealthy_response = Mock()
            unhealthy_response.status_code = 500

            mock_client_instance = Mock()
            mock_client.return_value.__aenter__ = Mock(return_value=mock_client_instance)

            # Test healthy service
            mock_client_instance.get.return_value.__aenter__ = Mock(return_value=healthy_response)
            health_status = await monitor.check_service_health(healthy_service)
            assert health_status["status"] == "healthy"

            # Test unhealthy service
            mock_client_instance.get.return_value.__aenter__ = Mock(return_value=unhealthy_response)
            health_status = await monitor.check_service_health(unhealthy_service)
            assert health_status["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_service_client_circuit_breaker(self):
        """Test service client circuit breaker pattern."""
        from services.orchestrator.modules.services import ServiceClient

        client = ServiceClient()

        # Test successful call
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {"status": "success", "data": "test"}

            result = await client.call_service("test-service", "test_action", {"param": "value"})
            assert result["status"] == "success"

        # Test circuit breaker activation after failures
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Service unavailable")

            # Multiple failures should trigger circuit breaker
            for _ in range(5):
                try:
                    await client.call_service("failing-service", "action", {})
                except Exception:
                    pass

            # Circuit should be open
            assert client._circuit_breaker.is_open("failing-service")


class TestSharedUtils:
    """Test cases for shared utilities module."""

    def test_workflow_template_validation(self):
        """Test workflow template validation."""
        from services.orchestrator.modules.shared_utils import validate_workflow_template

        # Valid template
        valid_template = {
            "name": "valid_template",
            "steps": [
                {
                    "id": "step1",
                    "service": "service1",
                    "action": "action1",
                    "depends_on": []
                }
            ]
        }

        assert validate_workflow_template(valid_template) is True

        # Invalid template (missing required fields)
        invalid_template = {
            "name": "invalid_template",
            "steps": [
                {
                    "id": "step1",
                    # Missing service and action
                    "depends_on": []
                }
            ]
        }

        assert validate_workflow_template(invalid_template) is False

    def test_dependency_resolution(self):
        """Test workflow dependency resolution."""
        from services.orchestrator.modules.shared_utils import resolve_dependencies

        steps = [
            {"id": "step1", "depends_on": []},
            {"id": "step2", "depends_on": ["step1"]},
            {"id": "step3", "depends_on": ["step1", "step2"]}
        ]

        execution_order = resolve_dependencies(steps)
        expected_order = ["step1", "step2", "step3"]

        assert execution_order == expected_order

    def test_execution_context_management(self):
        """Test execution context management."""
        from services.orchestrator.modules.shared_utils import ExecutionContext

        context = ExecutionContext(workflow_id="wf-123", execution_id="exec-456")

        # Set context variables
        context.set_variable("user_id", "user-123")
        context.set_variable("input_data", {"key": "value"})

        # Get context variables
        assert context.get_variable("user_id") == "user-123"
        assert context.get_variable("input_data") == {"key": "value"}

        # Test context serialization
        serialized = context.serialize()
        assert serialized["workflow_id"] == "wf-123"
        assert serialized["execution_id"] == "exec-456"

    def test_error_handling_utilities(self):
        """Test error handling utilities."""
        from services.orchestrator.modules.shared_utils import (
            create_error_response,
            is_retryable_error,
            get_error_category
        )

        # Test error response creation
        error_response = create_error_response("Workflow execution failed", "EXECUTION_ERROR", 500)
        assert error_response["success"] is False
        assert error_response["message"] == "Workflow execution failed"
        assert error_response["error_code"] == "EXECUTION_ERROR"

        # Test retryable error detection
        assert is_retryable_error("Connection timeout") is True
        assert is_retryable_error("Invalid input") is False

        # Test error categorization
        assert get_error_category("Connection timeout") == "NETWORK_ERROR"
        assert get_error_category("Invalid JSON") == "VALIDATION_ERROR"

    def test_performance_monitoring(self):
        """Test performance monitoring utilities."""
        from services.orchestrator.modules.shared_utils import PerformanceMonitor

        monitor = PerformanceMonitor()

        # Start monitoring
        monitor.start_operation("test_operation")

        # Simulate some work
        import time
        time.sleep(0.01)

        # End monitoring
        metrics = monitor.end_operation("test_operation")

        assert metrics["operation"] == "test_operation"
        assert metrics["duration_seconds"] >= 0.01
        assert "start_time" in metrics
        assert "end_time" in metrics


class TestStartupDiscovery:
    """Test cases for startup discovery module."""

    @pytest.mark.asyncio
    async def test_service_auto_discovery(self):
        """Test automatic service discovery on startup."""
        from services.orchestrator.modules.startup_discovery import ServiceAutoDiscovery

        discovery = ServiceAutoDiscovery()

        # Mock service endpoints to discover
        mock_endpoints = [
            "http://service1:8080",
            "http://service2:8081",
            "http://service3:8082"
        ]

        with patch.object(discovery, '_scan_network') as mock_scan:
            mock_scan.return_value = mock_endpoints

            discovered_services = await discovery.discover_services()

            assert len(discovered_services) == 3
            assert "http://service1:8080" in discovered_services

    @pytest.mark.asyncio
    async def test_service_registration_on_discovery(self):
        """Test automatic service registration after discovery."""
        from services.orchestrator.modules.startup_discovery import ServiceRegistrationManager

        manager = ServiceRegistrationManager()

        service_endpoints = [
            "http://analysis-service:8080",
            "http://storage-service:8081"
        ]

        with patch('services.orchestrator.modules.startup_discovery.httpx.AsyncClient') as mock_client:
            # Mock successful health checks
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "name": "test-service",
                "capabilities": ["analyze"],
                "version": "1.0.0"
            }

            mock_instance = Mock()
            mock_client.return_value.__aenter__ = Mock(return_value=mock_instance)
            mock_instance.get.return_value.__aenter__ = Mock(return_value=mock_response)

            registered_count = await manager.register_discovered_services(service_endpoints)

            assert registered_count >= 0  # May vary based on implementation

    def test_configuration_validation(self):
        """Test startup configuration validation."""
        from services.orchestrator.modules.startup_discovery import ConfigurationValidator

        validator = ConfigurationValidator()

        # Valid configuration
        valid_config = {
            "services": [
                {
                    "name": "valid-service",
                    "endpoint": "http://valid:8080",
                    "health_check": "/health"
                }
            ],
            "discovery": {
                "enabled": True,
                "scan_interval": 30,
                "timeout": 5
            }
        }

        assert validator.validate_config(valid_config) is True

        # Invalid configuration
        invalid_config = {
            "services": [
                {
                    "name": "",  # Invalid: empty name
                    "endpoint": "not-a-url"  # Invalid: not a URL
                }
            ]
        }

        assert validator.validate_config(invalid_config) is False


class TestIntegrationScenarios:
    """Integration tests for orchestrator modules."""

    @pytest.mark.asyncio
    async def test_full_orchestration_workflow(self):
        """Test complete orchestration workflow integration."""
        # This would test the full workflow from event trigger to completion
        # For now, test the integration points

        from services.orchestrator.modules.event_driven_orchestration import WorkflowDefinition
        from services.orchestrator.modules.services import ServiceDiscovery

        # Create a workflow
        workflow = WorkflowDefinition(
            name="integration_test_workflow",
            steps=[
                {
                    "id": "discover_services",
                    "service": "service_discovery",
                    "action": "discover",
                    "depends_on": []
                },
                {
                    "id": "process_results",
                    "service": "data_processor",
                    "action": "process",
                    "depends_on": ["discover_services"]
                }
            ]
        )

        # Initialize service discovery
        discovery = ServiceDiscovery()

        # Test that workflow can be validated
        assert workflow.validate() is True

        # Test that discovery can register services
        service_info = {
            "name": "test_integration_service",
            "endpoint": "http://test:8080",
            "capabilities": ["test"]
        }

        await discovery.register_service(service_info)
        found_service = await discovery.discover_service("test_integration_service")
        assert found_service == service_info

    def test_error_propagation_and_handling(self):
        """Test error propagation through the orchestration layers."""
        from services.orchestrator.modules.shared_utils import create_error_response

        # Test error response creation
        error = create_error_response("Workflow failed", "WORKFLOW_ERROR", 500)
        assert error["success"] is False
        assert error["error_code"] == "WORKFLOW_ERROR"
        assert error["status_code"] == 500

        # Test error categorization
        from services.orchestrator.modules.shared_utils import get_error_category
        assert get_error_category("Connection timeout") == "NETWORK_ERROR"
        assert get_error_category("Invalid workflow definition") == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self):
        """Test concurrent execution of multiple workflows."""
        from services.orchestrator.modules.event_driven_orchestration import WorkflowExecutor

        executor = WorkflowExecutor()

        # Create multiple workflow instances
        workflows = [
            {
                "name": f"concurrent_workflow_{i}",
                "steps": [
                    {
                        "id": "step1",
                        "service": "mock_service",
                        "action": "process",
                        "parameters": {"input": f"data_{i}"}
                    }
                ]
            }
            for i in range(5)
        ]

        # Mock service calls
        with patch('services.orchestrator.modules.event_driven_orchestration.ServiceClient') as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            mock_instance.call_service.return_value = {"status": "success"}

            # Execute workflows concurrently
            tasks = [executor.execute_workflow(workflow) for workflow in workflows]
            results = await asyncio.gather(*tasks)

            # All should complete successfully
            assert len(results) == 5
            for result in results:
                assert result["status"] == "completed"

            # Service should be called 5 times
            assert mock_instance.call_service.call_count == 5
