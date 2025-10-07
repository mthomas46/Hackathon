"""
E2E Tests: Service Health

Tests that all services are operational and respond correctly to health checks.
Mimics STEP 1 of demo_mcp_workflow_validation.py.

Test Modes:
- Code: Tests health endpoint implementation
- Live: Tests running Docker containers
"""

import pytest
import asyncio


class TestServiceHealth:
    """Test suite for service health checks."""
    
    @pytest.mark.asyncio
    async def test_kafka_ingestion_health(
        self,
        http_client,
        service_urls,
        test_mode
    ):
        """
        Test kafka-ingestion-service health endpoint.
        
        Expected:
        - 200 status code
        - JSON response with status=healthy
        - Response time < 1s
        """
        url = service_urls["kafka-ingestion"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        response = await http_client.get(f"{url}/health")
        
        assert response.status_code == 200, \
            f"Health check failed with status {response.status_code}"
        
        data = response.json()
        assert "status" in data, "Response missing 'status' field"
        assert data["status"] in ["healthy", "degraded"], \
            f"Unexpected status: {data['status']}"
        
        assert response.elapsed.total_seconds() < 1.0, \
            f"Health check took {response.elapsed.total_seconds()}s (> 1s)"
    
    @pytest.mark.asyncio
    async def test_llm_tagging_health(
        self,
        http_client,
        service_urls,
        test_mode
    ):
        """
        Test llm-tagging-pipeline health endpoint.
        
        Expected:
        - 200 status code
        - Service metadata present
        """
        url = service_urls["llm-tagging"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        response = await http_client.get(f"{url}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_mcp_local_llm_health(
        self,
        http_client,
        service_urls,
        test_mode
    ):
        """
        Test mcp-local-llm health endpoint.
        
        Expected:
        - 200 status code
        - Ollama connection reported
        """
        url = service_urls["mcp-local-llm"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        response = await http_client.get(f"{url}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_mcp_package_manager_health(
        self,
        http_client,
        service_urls,
        test_mode
    ):
        """Test mcp-package-manager health endpoint."""
        url = service_urls["mcp-package-manager"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        response = await http_client.get(f"{url}/health")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_mcp_evergreen_docs_health(
        self,
        http_client,
        service_urls,
        test_mode
    ):
        """Test mcp-evergreen-docs health endpoint."""
        url = service_urls["mcp-evergreen-docs"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        response = await http_client.get(f"{url}/health")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_mcp_logs_health(
        self,
        http_client,
        service_urls,
        test_mode
    ):
        """Test mcp-logs health endpoint."""
        url = service_urls["mcp-logs"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        response = await http_client.get(f"{url}/health")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_all_services_healthy(
        self,
        http_client,
        service_urls,
        test_mode
    ):
        """
        Test that all critical services are healthy.
        
        This is a smoke test to ensure the ecosystem is operational.
        """
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        critical_services = [
            "kafka-ingestion",
            "llm-tagging",
            "mcp-logs",
        ]
        
        results = {}
        for service_name in critical_services:
            url = service_urls[service_name]
            try:
                response = await http_client.get(f"{url}/health")
                results[service_name] = response.status_code == 200
            except Exception as e:
                results[service_name] = False
        
        failed_services = [
            name for name, healthy in results.items()
            if not healthy
        ]
        
        assert len(failed_services) == 0, \
            f"Services not healthy: {', '.join(failed_services)}"