"""Performance and load testing integration across bounded contexts."""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient

from services.orchestrator.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


class TestWorkflowPerformanceIntegration:
    """Test workflow performance under load across bounded contexts."""

    def test_bulk_workflow_creation_performance(self, client):
        """Test creating multiple workflows and their performance impact."""
        start_time = time.time()

        # Create multiple workflows
        workflow_count = 10
        created_workflows = []

        for i in range(workflow_count):
            workflow_data = {
                "name": f"Bulk Workflow {i}",
                "description": f"Performance test workflow {i}",
                "actions": [
                    {
                        "action_id": f"action_{i}",
                        "service_name": "test_service",
                        "action_type": "performance_test",
                        "parameters": {"index": i}
                    }
                ],
                "required_services": ["test_service"],
                "tags": ["performance", "bulk"]
            }

            response = client.post("/api/v1/workflows", json=workflow_data)
            assert response.status_code == 201
            created_workflows.append(response.json())

        creation_time = time.time() - start_time
        avg_creation_time = creation_time / workflow_count

        # Performance assertions
        assert avg_creation_time < 1.0, f"Average workflow creation time too slow: {avg_creation_time}s"
        assert creation_time < 5.0, f"Total creation time too slow: {creation_time}s"

        # Verify all workflows were created
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        workflows = response.json()["workflows"]
        assert len(workflows) >= workflow_count

        # Verify health monitoring isn't impacted
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_time = time.time() - start_time
        assert health_time < 2.0, "Health check became slow under load"

    def test_concurrent_workflow_operations(self, client):
        """Test concurrent workflow operations across bounded contexts."""
        def create_and_execute_workflow(index):
            # Create workflow
            workflow_data = {
                "name": f"Concurrent Workflow {index}",
                "description": f"Concurrent operation test {index}",
                "actions": [
                    {
                        "action_id": f"concurrent_action_{index}",
                        "service_name": "test_service",
                        "action_type": "concurrent_test",
                        "parameters": {"index": index}
                    }
                ],
                "required_services": ["test_service"],
                "tags": ["concurrent", "performance"]
            }

            response = client.post("/api/v1/workflows", json=workflow_data)
            if response.status_code != 201:
                return None

            workflow = response.json()

            # Execute workflow
            execution_data = {
                "workflow_id": workflow["workflow_id"],
                "parameters": {"test_param": f"value_{index}"}
            }

            response = client.post("/api/v1/workflows/execute", json=execution_data)
            return response.status_code

        # Run concurrent operations
        start_time = time.time()
        concurrent_count = 5

        with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
            futures = [executor.submit(create_and_execute_workflow, i) for i in range(concurrent_count)]
            results = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time

        # Verify all operations completed
        successful_results = [r for r in results if r in [200, 201, 202]]
        assert len(successful_results) == concurrent_count, f"Some concurrent operations failed: {results}"

        # Performance assertions
        assert total_time < 10.0, f"Concurrent operations too slow: {total_time}s"
        avg_time = total_time / concurrent_count
        assert avg_time < 2.0, f"Average operation time too slow: {avg_time}s"


class TestServiceRegistryPerformanceIntegration:
    """Test service registry performance under load."""

    def test_bulk_service_registration_performance(self, client):
        """Test registering multiple services and performance impact."""
        start_time = time.time()

        service_count = 20
        registered_services = []

        for i in range(service_count):
            service_data = {
                "service_name": f"perf-service-{i}",
                "service_url": f"http://perf-service-{i}:50{i:02d}",
                "capabilities": ["performance_test", f"capability_{i}"],
                "metadata": {"version": "1.0.0", "index": i}
            }

            response = client.post("/api/v1/services", json=service_data)
            assert response.status_code == 200
            registered_services.append(service_data["service_name"])

        registration_time = time.time() - start_time
        avg_registration_time = registration_time / service_count

        # Performance assertions
        assert avg_registration_time < 0.5, f"Average service registration time too slow: {avg_registration_time}s"
        assert registration_time < 5.0, f"Total registration time too slow: {registration_time}s"

        # Verify all services were registered
        response = client.get("/api/v1/services")
        assert response.status_code == 200
        services = response.json()["services"]
        registered_names = [s["service_name"] for s in services]
        for service_name in registered_services:
            assert service_name in registered_names

        # Verify health monitoring scales
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200
        health_data = response.json()
        health_check_time = time.time() - start_time
        assert health_check_time < 3.0, "Health monitoring became slow with many services"

    def test_service_discovery_performance(self, client):
        """Test service discovery performance with many registered services."""
        # First register services
        service_count = 15
        for i in range(service_count):
            service_data = {
                "service_name": f"discovery-service-{i}",
                "service_url": f"http://discovery-{i}:51{i:02d}",
                "capabilities": ["discovery_test"],
                "metadata": {"test": "discovery"}
            }
            response = client.post("/api/v1/services", json=service_data)
            assert response.status_code == 200

        # Test discovery performance
        start_time = time.time()

        # Multiple discovery calls
        for _ in range(10):
            response = client.get("/api/v1/services")
            assert response.status_code == 200
            services = response.json()["services"]
            assert len(services) >= service_count

        discovery_time = time.time() - start_time
        avg_discovery_time = discovery_time / 10

        # Performance assertions
        assert avg_discovery_time < 0.2, f"Average service discovery time too slow: {avg_discovery_time}s"
        assert discovery_time < 2.0, f"Total discovery time too slow: {discovery_time}s"


class TestHealthMonitoringPerformanceIntegration:
    """Test health monitoring performance under load."""

    def test_health_monitoring_scalability(self, client):
        """Test health monitoring performance with multiple components."""
        # Register multiple services first
        service_count = 10
        for i in range(service_count):
            service_data = {
                "service_name": f"health-service-{i}",
                "service_url": f"http://health-{i}:52{i:02d}",
                "capabilities": ["health_test"],
                "metadata": {"health_endpoint": "/health"}
            }
            response = client.post("/api/v1/services", json=service_data)
            assert response.status_code == 200

        # Create multiple workflows
        workflow_count = 5
        for i in range(workflow_count):
            workflow_data = {
                "name": f"Health Workflow {i}",
                "description": f"Health monitoring test workflow {i}",
                "actions": [],
                "required_services": [],
                "tags": ["health", "performance"]
            }
            response = client.post("/api/v1/workflows", json=workflow_data)
            assert response.status_code == 201

        # Test health monitoring performance
        start_time = time.time()

        # Multiple health checks
        health_check_count = 20
        for _ in range(health_check_count):
            response = client.get("/api/v1/health/system")
            assert response.status_code == 200

        health_check_time = time.time() - start_time
        avg_health_check_time = health_check_time / health_check_count

        # Performance assertions
        assert avg_health_check_time < 0.3, f"Average health check time too slow: {avg_health_check_time}s"
        assert health_check_time < 5.0, f"Total health check time too slow: {health_check_time}s"

        # Verify health data includes all components
        response = client.get("/api/v1/health/system")
        health_data = response.json()
        assert "services" in health_data


class TestEndToEndPerformanceIntegration:
    """Test end-to-end performance across all bounded contexts."""

    def test_full_system_performance_under_load(self, client):
        """Test full system performance with all bounded contexts active."""
        start_time = time.time()

        # 1. Register services
        service_count = 8
        service_names = []
        for i in range(service_count):
            service_data = {
                "service_name": f"full-service-{i}",
                "service_url": f"http://full-{i}:53{i:02d}",
                "capabilities": ["full_test", "integration"],
                "metadata": {"performance": "test"}
            }
            response = client.post("/api/v1/services", json=service_data)
            assert response.status_code == 200
            service_names.append(service_data["service_name"])

        service_registration_time = time.time() - start_time

        # 2. Create workflows
        workflow_count = 6
        workflow_ids = []
        for i in range(workflow_count):
            workflow_data = {
                "name": f"Full System Workflow {i}",
                "description": f"End-to-end performance test workflow {i}",
                "actions": [
                    {
                        "action_id": f"full_action_{i}",
                        "service_name": service_names[i % len(service_names)],
                        "action_type": "full_test",
                        "parameters": {"test_id": i}
                    }
                ],
                "required_services": [service_names[i % len(service_names)]],
                "tags": ["full", "performance", "integration"]
            }
            response = client.post("/api/v1/workflows", json=workflow_data)
            assert response.status_code == 201
            workflow = response.json()
            workflow_ids.append(workflow["workflow_id"])

        workflow_creation_time = time.time() - start_time - service_registration_time

        # 3. Execute workflows
        execution_start = time.time()
        execution_results = []
        for workflow_id in workflow_ids:
            execution_data = {
                "workflow_id": workflow_id,
                "parameters": {"execution_test": "performance"}
            }
            response = client.post("/api/v1/workflows/execute", json=execution_data)
            execution_results.append(response.status_code)

        execution_time = time.time() - execution_start

        # 4. Health monitoring checks
        health_start = time.time()
        for _ in range(5):
            response = client.get("/api/v1/health/system")
            assert response.status_code == 200

        health_check_time = time.time() - health_start

        # 5. Final state verification
        verification_start = time.time()

        # Check workflows
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        workflows = response.json()["workflows"]
        assert len(workflows) >= workflow_count

        # Check services
        response = client.get("/api/v1/services")
        assert response.status_code == 200
        services = response.json()["services"]
        assert len(services) >= service_count

        verification_time = time.time() - verification_start

        total_time = time.time() - start_time

        # Comprehensive performance assertions
        assert service_registration_time < 3.0, f"Service registration too slow: {service_registration_time}s"
        assert workflow_creation_time < 4.0, f"Workflow creation too slow: {workflow_creation_time}s"
        assert execution_time < 5.0, f"Workflow execution too slow: {execution_time}s"
        assert health_check_time < 2.0, f"Health monitoring too slow: {health_check_time}s"
        assert verification_time < 2.0, f"State verification too slow: {verification_time}s"
        assert total_time < 15.0, f"Total end-to-end time too slow: {total_time}s"

        # Verify all executions were accepted
        successful_executions = [r for r in execution_results if r in [200, 201, 202]]
        assert len(successful_executions) == workflow_count, f"Some executions failed: {execution_results}"

        print(f"Total end-to-end time: {total_time:.2f}s")
        print(f"Service registration time: {service_registration_time:.2f}s")
        print(f"Workflow creation time: {workflow_creation_time:.2f}s")
        print(f"Workflow execution time: {execution_time:.2f}s")
        print(f"Health check time: {health_check_time:.2f}s")
        print(f"Verification time: {verification_time:.2f}s")
class TestMemoryAndResourceUsage:
    """Test memory and resource usage under load."""

    def test_memory_usage_with_many_workflows(self, client):
        """Test memory usage when creating many workflows."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create many workflows
        workflow_count = 50
        for i in range(workflow_count):
            workflow_data = {
                "name": f"Memory Test Workflow {i}",
                "description": f"Testing memory usage {i}",
                "actions": [
                    {
                        "action_id": f"memory_action_{i}",
                        "service_name": "test_service",
                        "action_type": "memory_test",
                        "parameters": {"data": "x" * 1000}  # 1KB of data per action
                    }
                ],
                "required_services": ["test_service"],
                "tags": ["memory", "test"]
            }
            response = client.post("/api/v1/workflows", json=workflow_data)
            assert response.status_code == 201

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory assertions (reasonable increase for 50 workflows)
        assert memory_increase < 100, f"Memory usage too high: {memory_increase}MB increase"
        assert final_memory < 500, f"Total memory usage too high: {final_memory}MB"

        # Verify system still responds
        response = client.get("/api/v1/health/system")
        assert response.status_code == 200

        response = client.get("/api/v1/workflows?limit=10")
        assert response.status_code == 200
        workflows = response.json()["workflows"]
        assert len(workflows) >= 10
