"""
Integration tests for mcp-provisioner → gateway registration.

TDD RED Phase: These tests will fail initially.
"""

import pytest
import httpx
import asyncio
import subprocess


@pytest.mark.integration
@pytest.mark.asyncio
class TestProvisionerGatewayIntegration:
    """Integration tests for automatic gateway registration."""
    
    async def test_mcp_auto_registers_with_gateway(self):
        """
        Test that when an MCP is provisioned, it automatically registers with the gateway.
        
        TDD RED: This will fail initially because gateway registration isn't implemented.
        TDD GREEN: Should pass after implementing gateway_client integration.
        """
        # Arrange
        client_id = f"tdd-test-{int(asyncio.get_event_loop().time())}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Act: Provision MCP
            provision_response = await client.post(
                "http://localhost:5400/api/v1/mcps",
                json={
                    "client_id": client_id,
                    "tier": 2,
                    "memory_limit": "1024M",
                    "cpu_shares": 1024,
                    "image_name": "mcp-base:latest"
                }
            )
            
            # Assert: Provisioning succeeded
            assert provision_response.status_code == 201, f"Provisioning failed: {provision_response.text}"
            
            provision_data = provision_response.json()
            mcp_id = provision_data["data"]["mcp_id"]
            container_id = provision_data["data"].get("container_id")
            
            assert mcp_id is not None, "MCP ID not returned"
            assert container_id is not None, "Container ID not returned (deployment failed)"
            
            # Wait for gateway registration to complete
            await asyncio.sleep(3)
            
            # Assert: MCP registered with gateway
            gateway_response = await client.get(
                f"http://localhost:8001/api/v1/gateway/instances?mcp_id={mcp_id}"
            )
            
            assert gateway_response.status_code == 200, f"Gateway query failed: {gateway_response.text}"
            
            instances = gateway_response.json()
            assert len(instances) > 0, f"MCP {mcp_id} not registered with gateway!"
            assert instances[0]["mcp_id"] == mcp_id, "Wrong MCP ID in gateway"
            
            # Cleanup
            try:
                subprocess.run(['docker', 'stop', container_id], timeout=5)
                subprocess.run(['docker', 'rm', container_id], timeout=5)
            except:
                pass
    
    async def test_gateway_knows_mcp_port(self):
        """
        Test that gateway has correct port information for the MCP.
        
        TDD RED: Will fail if port isn't extracted and passed to gateway.
        """
        client_id = f"tdd-port-test-{int(asyncio.get_event_loop().time())}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Provision MCP
            provision_response = await client.post(
                "http://localhost:5400/api/v1/mcps",
                json={
                    "client_id": client_id,
                    "tier": 2,
                    "memory_limit": "1024M",
                    "cpu_shares": 1024,
                    "image_name": "mcp-base:latest"
                }
            )
            
            assert provision_response.status_code == 201
            mcp_id = provision_response.json()["data"]["mcp_id"]
            container_id = provision_response.json()["data"]["container_id"]
            
            await asyncio.sleep(3)
            
            # Check gateway has port info
            gateway_response = await client.get(
                f"http://localhost:8001/api/v1/gateway/instances?mcp_id={mcp_id}"
            )
            
            assert gateway_response.status_code == 200
            instances = gateway_response.json()
            assert len(instances) > 0
            
            instance = instances[0]
            assert instance["port"] > 0, "Gateway doesn't have MCP port!"
            assert instance["host"] in ["localhost", "host.docker.internal"], "Wrong host"
            
            # Cleanup
            try:
                subprocess.run(['docker', 'stop', container_id], timeout=5)
                subprocess.run(['docker', 'rm', container_id], timeout=5)
            except:
                pass
    
    async def test_gateway_health_check_url_set(self):
        """
        Test that gateway has correct health check URL.
        
        TDD RED: Will fail if health_check_url not set properly.
        """
        client_id = f"tdd-health-test-{int(asyncio.get_event_loop().time())}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Provision MCP
            provision_response = await client.post(
                "http://localhost:5400/api/v1/mcps",
                json={
                    "client_id": client_id,
                    "tier": 2,
                    "memory_limit": "1024M",
                    "cpu_shares": 1024,
                    "image_name": "mcp-base:latest"
                }
            )
            
            assert provision_response.status_code == 201
            mcp_id = provision_response.json()["data"]["mcp_id"]
            container_id = provision_response.json()["data"]["container_id"]
            
            await asyncio.sleep(3)
            
            # Check gateway has health_check_url
            gateway_response = await client.get(
                f"http://localhost:8001/api/v1/gateway/instances?mcp_id={mcp_id}"
            )
            
            assert gateway_response.status_code == 200
            instances = gateway_response.json()
            assert len(instances) > 0
            
            instance = instances[0]
            assert instance["health_check_url"], "No health_check_url!"
            assert "/health" in instance["health_check_url"], "Wrong health check URL"
            
            # Cleanup
            try:
                subprocess.run(['docker', 'stop', container_id], timeout=5)
                subprocess.run(['docker', 'rm', container_id], timeout=5)
            except:
                pass


@pytest.mark.integration
@pytest.mark.asyncio
class TestGatewayRouting:
    """Integration tests for gateway routing to registered MCPs."""
    
    async def test_gateway_routes_to_newly_provisioned_mcp(self):
        """
        Test that gateway can route queries to a newly provisioned MCP.
        
        TDD RED: Will fail until full integration is complete.
        TDD GREEN: Should pass once provisioner registers with gateway.
        """
        client_id = f"tdd-route-test-{int(asyncio.get_event_loop().time())}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Provision MCP
            provision_response = await client.post(
                "http://localhost:5400/api/v1/mcps",
                json={
                    "client_id": client_id,
                    "tier": 2,
                    "memory_limit": "1024M",
                    "cpu_shares": 1024,
                    "image_name": "mcp-base:latest"
                }
            )
            
            assert provision_response.status_code == 201
            mcp_id = provision_response.json()["data"]["mcp_id"]
            container_id = provision_response.json()["data"]["container_id"]
            
            # 2. Wait for registration and health check
            await asyncio.sleep(5)
            
            # 3. Query via gateway
            route_response = await client.post(
                "http://localhost:8001/api/v1/gateway/route",
                json={
                    "mcp_id": mcp_id,
                    "method": "POST",
                    "path": "/api/query",
                    "body": {"query": "Test query via gateway"},
                    "tier": 2,
                    "timeout_seconds": 30
                }
            )
            
            # Assert: Gateway successfully routed
            assert route_response.status_code == 200, f"Gateway routing failed: {route_response.text}"
            
            route_data = route_response.json()
            assert route_data.get("success") is True, f"Routing not successful: {route_data}"
            assert route_data.get("body") is not None, "No response body from MCP"
            
            # Cleanup
            try:
                subprocess.run(['docker', 'stop', container_id], timeout=5)
                subprocess.run(['docker', 'rm', container_id], timeout=5)
            except:
                pass


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s', '-m', 'integration'])

