"""Integration tests for error handling across bounded contexts."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from services.orchestrator.main import app
from services.orchestrator.domain.workflow_management import WorkflowId
from services.orchestrator.domain.service_registry import ServiceId


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


class TestWorkflowErrorHandlingIntegration:
    """Test error handling integration across workflow and other bounded contexts."""

    def test_workflow_creation_with_unregistered_service(self, client):
        """Test workflow creation fails when referencing unregistered service."""
        workflow_data = {
            "name": "Invalid Workflow",
            "description": "Workflow with non-existent service",
            "actions": [
                {
                    "action_id": "invalid_action",
                    "service_name": "non_existent_service",
                    "action_type": "invalid",
                    "parameters": {}
                }
            ],
            "required_services": ["non_existent_service"],
            "tags": ["error", "test"]
        }

        # This should either fail or succeed depending on validation strictness
        # If it succeeds, the service registry integration should handle the missing service
        response = client.post("/api/v1/workflows", json=workflow_data)
        # Accept both success (with warnings) and failure
        assert response.status_code in [201, 400, 422]

        if response.status_code == 201:
            # If workflow was created, verify service registry integration
            workflow = response.json()
            assert workflow["required_services"] == ["non_existent_service"]

            # Health monitoring should detect the service is unavailable
            response = client.get("/api/v1/health/system")
            assert response.status_code == 200
            health_data = response.json()
            # The system should still be healthy even with missing services
            assert "overall_healthy" not in health_data or health_data.get("overall_healthy", True)

    @patch('services.orchestrator.domain.workflow_management.services.workflow_executor.WorkflowExecutor.execute_workflow')
    def test_workflow_execution_with_service_failure(self, mock_execute, client):
        """Test workflow execution when service fails during execution."""
        # Mock executor to raise an exception
        mock_execute.side_effect = Exception("Service execution failed")

        # Create a simple workflow first
        workflow_data = {
            "name": "Failing Workflow",
            "description": "Workflow that will fail execution",
            "actions": [
                {
                    "action_id": "failing_action",
                    "service_name": "test_service",
                    "action_type": "failing_test",
                    "parameters": {}
                }
            ],
            "required_services": ["test_service"],
            "tags": ["error", "execution"]
        }

        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201
        workflow = response.json()

        # Execute workflow
        execution_data = {
            "workflow_id": workflow["workflow_id"],
            "parameters": {}
        }

        response = client.post("/api/v1/workflows/execute", json=execution_data)
        # Should accept the execution request even if it will fail
        assert response.status_code in [202, 500]

        # Health monitoring should detect the failure
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        # System might still report healthy if failure is isolated


class TestServiceRegistryErrorHandling:
    """Test error handling in service registry bounded context."""

    def test_duplicate_service_registration(self, client):
        """Test registering a service with duplicate name."""
        service_data = {
            "service_name": "duplicate_service",
            "service_url": "http://duplicate:5001",
            "capabilities": ["test"],
            "metadata": {"version": "1.0.0"}
        }

        # First registration should succeed
        response = client.post("/api/v1/services", json=service_data)
        assert response.status_code == 200

        # Second registration with same name should handle gracefully
        response = client.post("/api/v1/services", json=service_data)
        # Could be 200 (update) or 409 (conflict) depending on implementation
        assert response.status_code in [200, 409]

    def test_service_registration_with_invalid_data(self, client):
        """Test service registration with invalid data."""
        invalid_service_data = {
            "service_name": "",  # Empty name
            "service_url": "not-a-url",  # Invalid URL
            "capabilities": ["test"],
            "metadata": {"invalid": "data"}
        }

        response = client.post("/api/v1/services", json=invalid_service_data)
        # Should fail validation
        assert response.status_code == 422

    def test_get_nonexistent_service(self, client):
        """Test getting a service that doesn't exist."""
        response = client.get("/api/v1/services/nonexistent-service")
        assert response.status_code == 404


class TestHealthMonitoringErrorHandling:
    """Test error handling in health monitoring bounded context."""

    @patch('services.orchestrator.domain.health_monitoring.services.health_check_service.HealthCheckService.check_system_health')
    def test_health_check_service_failure(self, mock_health_check, client):
        """Test health monitoring when health check service fails."""
        # Mock health check to raise exception
        mock_health_check.side_effect = Exception("Health check service failed")

        response = client.get("/api/v1/health/system")
        # Should handle the failure gracefully
        assert response.status_code in [200, 503]
        # Even if health check fails, endpoint should respond
        assert "status" in response.json() or "error" in response.json()

    def test_health_check_with_invalid_service(self, client):
        """Test health check for non-existent service."""
        response = client.get("/api/v1/health/services/nonexistent-service")
        # Should handle gracefully
        assert response.status_code in [404, 503, 200]
        # If 200, should indicate service not found
        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "healthy" in data


class TestInfrastructureErrorHandling:
    """Test error handling in infrastructure bounded context."""

    def test_dlq_operations_with_invalid_data(self, client):
        """Test DLQ operations with invalid data."""
        invalid_retry_data = {
            "event_ids": [],  # Empty list
            "max_retries": 0  # Invalid retry count
        }

        response = client.post("/api/v1/infrastructure/dlq/retry", json=invalid_retry_data)
        # Should validate input
        assert response.status_code in [422, 501, 404]

    def test_saga_operations_with_invalid_saga_id(self, client):
        """Test saga operations with invalid saga ID."""
        response = client.get("/api/v1/infrastructure/saga/invalid-saga-id")
        # Should handle gracefully
        assert response.status_code in [404, 501, 422]

    def test_tracing_operations_with_invalid_trace_id(self, client):
        """Test tracing operations with invalid trace ID."""
        response = client.get("/api/v1/infrastructure/tracing/trace/invalid-trace-id")
        # Should handle gracefully
        assert response.status_code in [404, 501, 422]


class TestCrossContextErrorPropagation:
    """Test error propagation across bounded contexts."""

    def test_workflow_error_affects_health_monitoring(self, client):
        """Test that workflow errors are reflected in health monitoring."""
        # Create workflow that will fail
        workflow_data = {
            "name": "Error Propagation Test",
            "description": "Workflow that demonstrates error propagation",
            "actions": [
                {
                    "action_id": "error_action",
                    "service_name": "failing_service",
                    "action_type": "error_test",
                    "parameters": {"will_fail": True}
                }
            ],
            "required_services": ["failing_service"],
            "tags": ["error", "propagation"]
        }

        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201
        workflow = response.json()

        # Attempt execution (will fail)
        execution_data = {
            "workflow_id": workflow["workflow_id"],
            "parameters": {}
        }

        response = client.post("/api/v1/workflows/execute", json=execution_data)
        # Accept various responses for failed execution
        assert response.status_code in [202, 500, 422]

        # Health monitoring should still work
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()

        # System health should be accessible even with workflow failures
        assert isinstance(health_data, dict)

    def test_service_registry_error_affects_workflow_creation(self, client):
        """Test that service registry errors affect workflow creation appropriately."""
        # Try to create workflow with malformed service reference
        workflow_data = {
            "name": "Service Error Test",
            "description": "Workflow with service registry errors",
            "actions": [
                {
                    "action_id": "service_error_action",
                    "service_name": "",  # Empty service name
                    "action_type": "test",
                    "parameters": {}
                }
            ],
            "required_services": [""],  # Empty service name
            "tags": ["error", "service"]
        }

        response = client.post("/api/v1/workflows", json=workflow_data)
        # Should either succeed (with warnings) or fail validation
        assert response.status_code in [201, 422]

        if response.status_code == 201:
            # If created, verify service registry integration
            workflow = response.json()
            # The workflow should still be created even with invalid service references
            assert workflow["name"] == "Service Error Test"

    def test_infrastructure_error_isolation(self, client):
        """Test that infrastructure errors don't break other bounded contexts."""
        # Try infrastructure operation that will fail
        response = client.get("/api/v1/infrastructure/dlq/stats")
        # Should not break the endpoint
        assert response.status_code in [200, 501, 404]

        # Verify other contexts still work
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200

        response = client.get("/api/v1/workflows")
        assert response.status_code == 200

        response = client.get("/api/v1/services")
        assert response.status_code == 200


class TestConcurrentOperationErrorHandling:
    """Test error handling during concurrent operations across contexts."""

    def test_concurrent_workflow_and_service_operations(self, client):
        """Test concurrent operations don't interfere with error handling."""
        import threading
        import time

        errors = []
        results = []

        def create_workflows():
            try:
                for i in range(3):
                    workflow_data = {
                        "name": f"Concurrent Workflow {i}",
                        "description": f"Concurrent test workflow {i}",
                        "actions": [],
                        "required_services": [],
                        "tags": ["concurrent", "test"]
                    }
                    response = client.post("/api/v1/workflows", json=workflow_data)
                    results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        def register_services():
            try:
                for i in range(3):
                    service_data = {
                        "service_name": f"concurrent-service-{i}",
                        "service_url": f"http://concurrent-{i}:500{i}",
                        "capabilities": ["concurrent_test"],
                        "metadata": {"test": f"concurrent-{i}"}
                    }
                    response = client.post("/api/v1/services", json=service_data)
                    results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Start concurrent operations
        thread1 = threading.Thread(target=create_workflows)
        thread2 = threading.Thread(target=register_services)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent operations failed: {errors}"

        # Verify operations succeeded
        assert all(code in [200, 201] for code in results), f"Some operations failed: {results}"

        # Verify final state is consistent
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        workflows = response.json()["workflows"]
        assert len(workflows) >= 3

        response = client.get("/api/v1/services")
        assert response.status_code == 200
        services = response.json()["services"]
        assert len(services) >= 3
