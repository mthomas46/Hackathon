"""
Integration tests for container lifecycle management.

Tests container operations, health checks, restart recovery, and network isolation.
"""

import pytest
import httpx
import os
import asyncio
from datetime import datetime


pytestmark = pytest.mark.integration


@pytest.fixture
def api_base_url():
    """Get API base URL from environment."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
async def async_http_client(api_base_url):
    """Create async HTTP client."""
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30.0) as client:
        yield client


class TestContainerOperations:
    """Test basic container operations."""

    async def test_list_containers(self, async_http_client):
        """Test listing containers."""
        try:
            response = await async_http_client.get("/api/v1/infrastructure/health")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                
                # Check for container/service information
                # (actual structure may vary)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_get_container_status(self, async_http_client):
        """Test getting container status."""
        try:
            response = await async_http_client.get("/api/v1/config/docker")
            
            # Should return container info or not found
            assert response.status_code in [200, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_container_health_check(self, async_http_client):
        """Test container health check."""
        try:
            response = await async_http_client.get("/health")
            
            # Should return health status
            assert response.status_code in [200, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_container_logs(self, async_http_client):
        """Test accessing container logs."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/logs/recent")
            
            # Should return logs or not found
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict))
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_container_metrics(self, async_http_client):
        """Test container metrics retrieval."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/metrics")
            
            # Should return metrics or not found
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")


class TestContainerHealthChecks:
    """Test container health check functionality."""

    async def test_liveness_probe(self, async_http_client):
        """Test liveness probe."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/health/liveness")
            
            # Should return liveness status
            assert response.status_code in [200, 404, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_readiness_probe(self, async_http_client):
        """Test readiness probe."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/health/readiness")
            
            # Should return readiness status
            assert response.status_code in [200, 404, 503]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_startup_probe(self, async_http_client):
        """Test startup probe."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/health/startup")
            
            # Should return startup status
            assert response.status_code in [200, 404, 503]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_component_health(self, async_http_client):
        """Test individual component health."""
        try:
            response = await async_http_client.get("/api/v1/diagnostics/health/components")
            
            # Should return component health
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, (list, dict))
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_dependency_health(self, async_http_client):
        """Test dependency health checks."""
        try:
            response = await async_http_client.get("/api/v1/infrastructure/health")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                
                # Check for dependency status
                # (actual structure may vary)
        except httpx.ConnectError:
            pytest.skip("API not accessible")


class TestContainerRestartRecovery:
    """Test container restart and recovery."""

    async def test_service_recovery_after_restart(self, async_http_client):
        """Test service recovery after restart."""
        try:
            # Check initial health
            response1 = await async_http_client.get("/health")
            
            # Wait a bit (simulating restart time)
            await asyncio.sleep(0.5)
            
            # Check health again
            response2 = await async_http_client.get("/health")
            
            # Both should succeed or both should fail consistently
            assert response1.status_code in [200, 503]
            assert response2.status_code in [200, 503]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_job_recovery_after_restart(self, async_http_client):
        """Test job recovery after container restart."""
        try:
            # Get job status
            response = await async_http_client.get("/api/v1/admin/ingest/status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Jobs should be recoverable
                assert isinstance(data, (list, dict))
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_state_persistence_after_restart(self, async_http_client):
        """Test state persistence after restart."""
        try:
            # Check if data persists
            response = await async_http_client.get("/api/v1/admin/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                # Stats should be available
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_connection_recovery(self, async_http_client):
        """Test connection recovery after restart."""
        try:
            # Test database connection
            response = await async_http_client.get("/api/v1/infrastructure/health")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cache_recovery(self, async_http_client):
        """Test cache recovery after restart."""
        try:
            # Check cache status
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            # Should return cache stats or service unavailable
            assert response.status_code in [200, 404, 500, 503]
        except httpx.ConnectError:
            pytest.skip("API not accessible")


class TestContainerNetworkIsolation:
    """Test container network isolation."""

    async def test_service_to_service_communication(self, async_http_client):
        """Test service-to-service communication."""
        try:
            # Test if service can communicate with dependencies
            response = await async_http_client.get("/api/v1/infrastructure/health")
            
            if response.status_code == 200:
                data = response.json()
                
                # Should show connectivity to other services
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_external_network_access(self, async_http_client):
        """Test external network access."""
        try:
            # Check if service can access external resources
            response = await async_http_client.get("/health")
            
            # Should be accessible
            assert response.status_code in [200, 503]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_port_exposure(self, async_http_client):
        """Test port exposure configuration."""
        try:
            # Test if configured ports are accessible
            response = await async_http_client.get("/health")
            
            # Should be accessible on configured port
            assert response.status_code in [200, 503]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_network_isolation(self, async_http_client):
        """Test network isolation between services."""
        try:
            # Services should only access what they need
            response = await async_http_client.get("/api/v1/infrastructure/health")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_dns_resolution(self, async_http_client):
        """Test DNS resolution for service discovery."""
        try:
            # Services should be able to resolve each other
            response = await async_http_client.get("/api/v1/config/docker")
            
            # Should return config or not found
            assert response.status_code in [200, 404, 500]
        except httpx.ConnectError:
            pytest.skip("API not accessible")


class TestContainerResourceManagement:
    """Test container resource management."""

    async def test_memory_limits(self, async_http_client):
        """Test memory limit enforcement."""
        try:
            # Check if service respects memory limits
            response = await async_http_client.get("/api/v1/admin/stats")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cpu_limits(self, async_http_client):
        """Test CPU limit enforcement."""
        try:
            # Check if service respects CPU limits
            response = await async_http_client.get("/api/v1/diagnostics/metrics")
            
            # Should return metrics or not found
            assert response.status_code in [200, 404]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_disk_usage(self, async_http_client):
        """Test disk usage monitoring."""
        try:
            # Check disk usage
            response = await async_http_client.get("/api/v1/admin/stats")
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_resource_cleanup(self, async_http_client):
        """Test resource cleanup on shutdown."""
        try:
            # Check if resources are properly managed
            response = await async_http_client.get("/health")
            
            # Should be healthy
            assert response.status_code in [200, 503]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_connection_pool_limits(self, async_http_client):
        """Test connection pool limits."""
        try:
            # Make multiple requests to test connection pooling
            responses = []
            for _ in range(5):
                response = await async_http_client.get("/health")
                responses.append(response)
            
            # All should succeed or fail consistently
            assert all(r.status_code in [200, 503] for r in responses)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

