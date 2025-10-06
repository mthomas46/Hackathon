"""E2E tests for service health and connectivity."""

import pytest
import httpx


class TestServiceHealth:
    """Test all MCP services are healthy and accessible."""
    
    @pytest.mark.asyncio
    async def test_all_services_healthy(
        self, 
        http_client: httpx.AsyncClient,
        service_urls: dict
    ):
        """Test all services respond to health checks."""
        results = {}
        
        for service_name, url in service_urls.items():
            try:
                response = await http_client.get(f"{url}/health")
                results[service_name] = {
                    "status_code": response.status_code,
                    "healthy": response.status_code == 200,
                    "response": response.json() if response.status_code == 200 else None
                }
            except Exception as e:
                results[service_name] = {
                    "status_code": None,
                    "healthy": False,
                    "error": str(e)
                }
        
        # Print summary
        print("\n" + "="*60)
        print("SERVICE HEALTH SUMMARY")
        print("="*60)
        for service, result in results.items():
            status = "✅" if result["healthy"] else "❌"
            print(f"{status} {service}: {result.get('status_code', 'ERROR')}")
        print("="*60)
        
        # Assert all healthy
        unhealthy = [s for s, r in results.items() if not r["healthy"]]
        assert not unhealthy, f"Unhealthy services: {unhealthy}"
    
    @pytest.mark.asyncio
    async def test_provisioner_root(
        self,
        http_client: httpx.AsyncClient,
        service_urls: dict
    ):
        """Test MCP Provisioner root endpoint."""
        response = await http_client.get(service_urls["mcp_provisioner"])
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "mcp-provisioner"
    
    @pytest.mark.asyncio
    async def test_infrastructure_root(
        self,
        http_client: httpx.AsyncClient,
        service_urls: dict
    ):
        """Test MCP Infrastructure root endpoint."""
        response = await http_client.get(service_urls["mcp_infrastructure"])
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "mcp-infrastructure"
    
    @pytest.mark.asyncio
    async def test_gateway_root(
        self,
        http_client: httpx.AsyncClient,
        service_urls: dict
    ):
        """Test MCP Gateway root endpoint."""
        response = await http_client.get(service_urls["mcp_gateway"])
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "mcp-gateway"
    
    @pytest.mark.asyncio
    async def test_interpreter_root(
        self,
        http_client: httpx.AsyncClient,
        service_urls: dict
    ):
        """Test MCP Interpreter root endpoint."""
        response = await http_client.get(service_urls["mcp_interpreter"])
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "mcp-interpreter"
    
    @pytest.mark.asyncio
    async def test_orchestrator_root(
        self,
        http_client: httpx.AsyncClient,
        service_urls: dict
    ):
        """Test MCP Orchestrator root endpoint."""
        response = await http_client.get(service_urls["mcp_orchestrator"])
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "mcp-orchestrator"
    
    @pytest.mark.asyncio
    async def test_registry_root(
        self,
        http_client: httpx.AsyncClient,
        service_urls: dict
    ):
        """Test MCP Registry root endpoint."""
        response = await http_client.get(service_urls["mcp_registry"])
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "mcp-registry"
    
    @pytest.mark.asyncio
    async def test_training_coordinator_root(
        self,
        http_client: httpx.AsyncClient,
        service_urls: dict
    ):
        """Test Training Coordinator root endpoint."""
        response = await http_client.get(service_urls["training_coordinator"])
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "training-coordinator"

