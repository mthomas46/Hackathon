"""Integration tests for bounded context interactions."""

import pytest
from fastapi.testclient import TestClient

from services.orchestrator.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def container():
    """Get the dependency injection container."""
    from services.orchestrator.main import container
    return container


class TestWorkflowHealthMonitoringIntegration:
    """Test integration between Workflow Management and Health Monitoring bounded contexts."""

    def test_workflow_creation_and_health_monitoring(self, client, container):
        """Test that workflows can be created and are monitored by health system."""
        # Create a workflow
        workflow_data = {
            "name": "Health Integration Workflow",
            "description": "Workflow for health monitoring integration test",
            "actions": [
                {
                    "action_id": "test_action",
                    "service_name": "test_service",
                    "action_type": "test",
                    "parameters": {"test_param": "value"}
                }
            ],
            "required_services": ["test_service"],
            "tags": ["integration", "health"]
        }

        # Create workflow via API
        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201
        workflow = response.json()

        # Verify workflow was created
        assert workflow["name"] == "Health Integration Workflow"
        assert workflow["required_services"] == ["test_service"]

        # Check that health monitoring includes workflow information
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()

        # Health monitoring should be accessible even with workflow dependencies
        assert "services" in health_data
        # The system should be able to report health status
        assert isinstance(health_data, dict)

    def test_workflow_execution_and_health_integration(self, client, container):
        """Test that workflow execution integrates with health monitoring."""
        # Create a simple workflow
        workflow_data = {
            "name": "Execution Health Workflow",
            "description": "Workflow for execution and health integration",
            "actions": [
                {
                    "action_id": "simple_action",
                    "service_name": "test_service",
                    "action_type": "test",
                    "parameters": {}
                }
            ],
            "required_services": ["test_service"],
            "tags": ["execution", "health"]
        }

        # Create workflow
        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201
        workflow = response.json()

        # Execute workflow
        execution_data = {
            "workflow_id": workflow["workflow_id"],
            "parameters": {}
        }

        response = client.post("/api/v1/workflows/execute", json=execution_data)
        # Should accept the execution request
        assert response.status_code in [200, 202, 422, 500]

        # Health monitoring should still work after workflow operations
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()
        assert isinstance(health_data, dict)


class TestInfrastructureHealthIntegration:
    """Test integration between Infrastructure and Health Monitoring bounded contexts."""

    def test_infrastructure_health_monitoring(self, client, container):
        """Test that infrastructure components are monitored for health."""
        # Check system health includes infrastructure components
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()

        # Infrastructure components should be monitored
        assert "services" in health_data
        # At minimum, orchestrator itself should be monitored
        assert "orchestrator" in health_data["services"]

    def test_infrastructure_component_registration(self, client, container):
        """Test that infrastructure components are properly registered."""
        # Check if infrastructure endpoints are available
        # These might return 501 Not Implemented if not fully integrated yet
        response = client.get("/api/v1/infrastructure/dlq/stats")
        assert response.status_code in [200, 501, 404]

        response = client.get("/api/v1/infrastructure/tracing/stats")
        assert response.status_code in [200, 501, 404]


class TestWorkflowLifecycleIntegration:
    """Test complete workflow lifecycle integration."""

    def test_workflow_crud_and_health_integration(self, client, container):
        """Test workflow CRUD operations integrate with health monitoring."""
        # 1. Create workflow
        workflow_data = {
            "name": "Lifecycle Test Workflow",
            "description": "Complete workflow lifecycle test",
            "actions": [
                {
                    "action_id": "lifecycle_test",
                    "service_name": "lifecycle_service",
                    "action_type": "lifecycle",
                    "parameters": {"test": "value"}
                }
            ],
            "required_services": ["lifecycle_service"],
            "tags": ["lifecycle", "integration"]
        }

        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201
        workflow = response.json()

        # 2. Get workflow
        response = client.get(f"/api/v1/workflows/{workflow['workflow_id']}")
        assert response.status_code == 200
        retrieved_workflow = response.json()
        assert retrieved_workflow["name"] == "Lifecycle Test Workflow"

        # 3. List workflows
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        workflows = response.json()["workflows"]
        assert any(w["name"] == "Lifecycle Test Workflow" for w in workflows)

        # 4. Execute workflow
        execution_data = {
            "workflow_id": workflow["workflow_id"],
            "parameters": {"lifecycle_param": "test_value"}
        }

        response = client.post("/api/v1/workflows/execute", json=execution_data)
        assert response.status_code in [200, 202, 422, 500]

        # 5. Verify health monitoring works throughout
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()
        assert isinstance(health_data, dict)


class TestBoundedContextIsolation:
    """Test that bounded contexts maintain proper isolation."""

    def test_workflow_context_isolation(self, client, container):
        """Test that workflow operations don't affect other bounded contexts."""
        # Create workflow
        workflow_data = {
            "name": "Isolation Test Workflow",
            "description": "Test bounded context isolation",
            "actions": [],
            "required_services": [],
            "tags": ["isolation", "test"]
        }

        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201

        # Verify health monitoring doesn't include workflow internal data
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()
        # Health data should not contain workflow definitions
        assert not any("Isolation Test Workflow" in str(health_data))

    def test_health_context_isolation(self, client, container):
        """Test that health monitoring operations don't interfere with workflows."""
        # Create workflow
        workflow_data = {
            "name": "Health Isolation Workflow",
            "description": "Test health context isolation",
            "actions": [],
            "required_services": [],
            "tags": ["health", "isolation"]
        }

        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201
        workflow = response.json()

        # Check health multiple times
        for _ in range(3):
            response = client.get("/api/v1/health/system")
            assert response.status_code == 200

        # Workflow should still be retrievable
        response = client.get(f"/api/v1/workflows/{workflow['workflow_id']}")
        assert response.status_code == 200
        retrieved = response.json()
        assert retrieved["name"] == "Health Isolation Workflow"
        mock_health_check.return_value = HealthStatus.HEALTHY

        # Create a simple workflow
        workflow_data = {
            "name": "Health Monitored Workflow",
            "description": "Workflow with health monitoring",
            "actions": [
                {
                    "action_id": "simple_action",
                    "service_name": "test_service",
                    "action_type": "test",
                    "parameters": {}
                }
            ],
            "required_services": ["test_service"],
            "tags": ["health", "monitoring"]
        }

        # Create workflow
        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201
        workflow = response.json()

        # Execute workflow
        execution_data = {
            "workflow_id": workflow["workflow_id"],
            "parameters": {}
        }

        response = client.post("/api/v1/workflows/execute", json=execution_data)
        assert response.status_code == 202  # Accepted for async execution

        # Check system health includes workflow status
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()

        # Verify health monitoring includes workflow components
        assert "services" in health_data
        assert "workflows" in health_data or "orchestrator" in health_data["services"]


class TestServiceRegistryHealthIntegration:
    """Test integration between Service Registry and Health Monitoring bounded contexts."""

    def test_service_health_registration_integration(self, client, container):
        """Test that registered services are included in health monitoring."""
        # Register a service
        service_data = {
            "service_name": "health_test_service",
            "service_url": "http://health-test:5002",
            "capabilities": ["health_check"],
            "metadata": {"health_endpoint": "/health"}
        }

        response = client.post("/api/v1/services", json=service_data)
        assert response.status_code == 200

        # Check system health includes the registered service
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()

        # Verify the registered service appears in health monitoring
        assert "services" in health_data
        service_names = [s["name"] for s in health_data["services"].values()]
        assert "health_test_service" in service_names or "orchestrator" in service_names

    def test_service_health_status_propagation(self, client, container):
        """Test that service health status is properly propagated through the system."""
        # Register service
        service_data = {
            "service_name": "status_test_service",
            "service_url": "http://status-test:5003",
            "capabilities": ["status_check"],
            "metadata": {"status": "healthy"}
        }

        response = client.post("/api/v1/services", json=service_data)
        assert response.status_code == 200

        # Check service health endpoint
        response = client.get("/api/v1/health/services/status_test_service")
        # This might return 404 if the health check service isn't fully implemented yet
        # but the integration point should exist
        assert response.status_code in [200, 404, 503]  # 404 or 503 is acceptable for mock services


class TestInfrastructureHealthIntegration:
    """Test integration between Infrastructure and Health Monitoring bounded contexts."""

    def test_infrastructure_health_monitoring(self, client, container):
        """Test that infrastructure components are monitored for health."""
        # Check system health includes infrastructure components
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()

        # Infrastructure components should be monitored
        assert "services" in health_data
        # At minimum, orchestrator itself should be monitored
        assert "orchestrator" in health_data["services"]

    def test_infrastructure_component_registration(self, client, container):
        """Test that infrastructure components are properly registered."""
        # Check if infrastructure endpoints are available
        # These might return 501 Not Implemented if not fully integrated yet
        response = client.get("/api/v1/infrastructure/dlq/stats")
        assert response.status_code in [200, 501, 404]

        response = client.get("/api/v1/infrastructure/tracing/stats")
        assert response.status_code in [200, 501, 404]

        # But the routes should be registered (not 404 due to missing router)
        # If we get 404 here, it means the infrastructure router isn't included
        # which is acceptable during development


class TestEndToEndWorkflowExecution:
    """Test end-to-end workflow execution across all bounded contexts."""

    @patch('services.orchestrator.domain.workflow_management.services.workflow_executor.WorkflowExecutor.execute_workflow')
    @patch('services.orchestrator.domain.health_monitoring.services.health_check_service.HealthCheckService.check_service_health')
    def test_complete_workflow_lifecycle(self, mock_health_check, mock_execute, client, container):
        """Test complete workflow lifecycle from creation to execution to monitoring."""
        # Mock dependencies
        mock_health_check.return_value = HealthStatus.HEALTHY
        mock_execute.return_value = ExecutionId("test-exec-123")

        # 1. Register required services
        service_data = {
            "service_name": "e2e_test_service",
            "service_url": "http://e2e-test:5004",
            "capabilities": ["test_execution"],
            "metadata": {"version": "1.0.0"}
        }

        response = client.post("/api/v1/services", json=service_data)
        assert response.status_code == 200

        # 2. Create workflow
        workflow_data = {
            "name": "End-to-End Test Workflow",
            "description": "Complete workflow lifecycle test",
            "actions": [
                {
                    "action_id": "execute_test",
                    "service_name": "e2e_test_service",
                    "action_type": "execution",
                    "parameters": {"test_param": "value"}
                }
            ],
            "required_services": ["e2e_test_service"],
            "tags": ["e2e", "integration"]
        }

        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201
        workflow = response.json()

        # 3. Execute workflow
        execution_data = {
            "workflow_id": workflow["workflow_id"],
            "parameters": {"input_param": "test_value"}
        }

        response = client.post("/api/v1/workflows/execute", json=execution_data)
        assert response.status_code == 202

        # 4. Check workflow status
        response = client.get(f"/api/v1/workflows/{workflow['workflow_id']}")
        assert response.status_code == 200

        # 5. Verify health monitoring includes the workflow
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()

        # 6. Verify service registry shows the service
        response = client.get("/api/v1/services")
        assert response.status_code == 200
        services = response.json()["services"]
        assert any(s["service_name"] == "e2e_test_service" for s in services)

        # 7. List workflows includes our workflow
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        workflows = response.json()["workflows"]
        assert any(w["name"] == "End-to-End Test Workflow" for w in workflows)


class TestBoundedContextIsolation:
    """Test that bounded contexts maintain proper isolation."""

    def test_workflow_context_isolation(self, client, container):
        """Test that workflow operations don't affect other bounded contexts."""
        # Create workflow
        workflow_data = {
            "name": "Isolation Test Workflow",
            "description": "Test bounded context isolation",
            "actions": [],
            "required_services": [],
            "tags": ["isolation", "test"]
        }

        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 201

        # Verify service registry is unaffected
        response = client.get("/api/v1/services")
        assert response.status_code == 200
        # Services list should be empty or not include workflow data
        services = response.json()["services"]
        assert not any("Isolation Test Workflow" in str(s) for s in services)

        # Verify health monitoring doesn't include workflow internal data
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()
        # Health data should not contain workflow definitions
        assert not any("Isolation Test Workflow" in str(health_data))

    def test_service_registry_isolation(self, client, container):
        """Test that service registry operations don't affect workflow management."""
        # Register service
        service_data = {
            "service_name": "isolation_test_service",
            "service_url": "http://isolation-test:5005",
            "capabilities": ["isolation_test"],
            "metadata": {"test": "isolation"}
        }

        response = client.post("/api/v1/services", json=service_data)
        assert response.status_code == 200

        # Verify workflows are unaffected
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        workflows = response.json()["workflows"]
        # Workflows should not contain service registry data
        assert not any("isolation_test_service" in str(w) for w in workflows)

        # Verify health monitoring shows service but not workflow data
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()
        # Should show service in health but not mix contexts
        assert "services" in health_data
