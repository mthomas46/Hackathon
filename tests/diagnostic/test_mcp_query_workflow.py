"""
Diagnostic Tests: MCP Query Workflow

Systematically test the MCP query workflow to expose 404 root cause.
"""

import pytest
import httpx
import asyncio
import subprocess


class TestMCPQueryDiagnostics:
    """Systematic diagnosis of MCP query 404 issue."""
    
    def test_find_deployed_mcp_containers(self):
        """Test 1: Verify MCP containers are actually running."""
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=mcp-mcp-', '--format', '{{.Names}}\t{{.Status}}\t{{.Ports}}'],
            capture_output=True,
            text=True
        )
        
        containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        print(f"\n🐳 Found {len(containers)} MCP containers:")
        for container in containers:
            if container:
                print(f"  {container}")
        
        assert len(containers) > 0, "No MCP containers running!"
        
        return containers
    
    def test_get_mcp_port_mapping(self):
        """Test 2: Get port mapping for deployed MCP."""
        # Get latest MCP container
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=mcp-mcp-horus', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )
        
        container_name = result.stdout.strip().split('\n')[0] if result.stdout.strip() else None
        assert container_name, "No MCP container found!"
        
        print(f"\n🔍 Testing container: {container_name}")
        
        # Get port mapping
        port_result = subprocess.run(
            ['docker', 'port', container_name],
            capture_output=True,
            text=True
        )
        
        print(f"Port mappings:\n{port_result.stdout}")
        
        # Extract port
        for line in port_result.stdout.split('\n'):
            if '8080' in line or '3000' in line:
                port = line.split(':')[-1].strip()
                print(f"\n✅ Found MCP port: {port}")
                return container_name, port
        
        pytest.fail("No port mapping found for MCP container!")
    
    @pytest.mark.asyncio
    async def test_query_mcp_directly(self):
        """Test 3: Query MCP container directly (bypass gateway)."""
        # Get MCP info
        container_name, port = self.test_get_mcp_port_mapping()
        
        url = f"http://localhost:{port}/api/query"
        
        print(f"\n📡 Querying MCP directly: {url}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    url,
                    json={"query": "What is the Horus Heresy?"}
                )
                
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
                assert response.status_code == 200, \
                    f"MCP direct query failed: {response.status_code}"
                
                data = response.json()
                assert 'answer' in data or 'response' in data, \
                    f"MCP response missing answer field: {data}"
                
                print("\n✅ MCP responds to direct queries!")
                return True
                
            except Exception as e:
                pytest.fail(f"Failed to query MCP directly: {e}")
    
    @pytest.mark.asyncio
    async def test_gateway_knows_about_mcp(self):
        """Test 4: Check if gateway knows about deployed MCPs."""
        gateway_url = "http://localhost:8001"
        
        print(f"\n🌐 Checking gateway at {gateway_url}")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try to list MCPs
            endpoints_to_try = [
                '/api/v1/mcps',
                '/api/v1/registry',
                '/mcps',
                '/registry'
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    response = await client.get(f"{gateway_url}{endpoint}")
                    print(f"  {endpoint}: {response.status_code}")
                    if response.status_code == 200:
                        print(f"    Data: {response.text[:200]}")
                except Exception as e:
                    print(f"  {endpoint}: ERROR - {str(e)[:100]}")
    
    @pytest.mark.asyncio
    async def test_gateway_query_endpoint(self):
        """Test 5: Test gateway query endpoint with known MCP ID."""
        gateway_url = "http://localhost:8001"
        
        # Get MCP ID from container name
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=mcp-mcp-horus', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )
        
        container_name = result.stdout.strip().split('\n')[0] if result.stdout.strip() else None
        if not container_name:
            pytest.skip("No MCP container found")
        
        # Extract MCP ID from container name (format: mcp-mcp-<client>-<id>)
        mcp_id = container_name.replace('mcp-', '', 1)  # Remove first 'mcp-' prefix
        
        print(f"\n🔍 Testing gateway query for MCP: {mcp_id}")
        
        query_endpoints = [
            '/api/v1/query',
            '/api/query',
            '/query',
            f'/api/v1/mcps/{mcp_id}/query'
        ]
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for endpoint in query_endpoints:
                url = f"{gateway_url}{endpoint}"
                print(f"\n  Testing: {endpoint}")
                
                try:
                    response = await client.post(
                        url,
                        json={
                            "mcp_id": mcp_id,
                            "query": "What is the Horus Heresy?"
                        }
                    )
                    
                    print(f"    Status: {response.status_code}")
                    print(f"    Response: {response.text[:200]}")
                    
                    if response.status_code == 200:
                        print(f"\n✅ Found working endpoint: {endpoint}")
                        return endpoint
                        
                except Exception as e:
                    print(f"    ERROR: {str(e)[:100]}")
        
        pytest.fail("No working gateway query endpoint found!")
    
    @pytest.mark.asyncio
    async def test_mcp_registration_in_registry(self):
        """Test 6: Check if MCP is registered in mcp-registry."""
        registry_url = "http://localhost:8102"
        
        print(f"\n📋 Checking mcp-registry at {registry_url}")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try to list registered MCPs
            endpoints = [
                '/api/v1/registry',
                '/api/v1/mcps',
                '/registry',
                '/mcps'
            ]
            
            for endpoint in endpoints:
                try:
                    response = await client.get(f"{registry_url}{endpoint}")
                    print(f"  {endpoint}: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"    Registered MCPs: {len(data) if isinstance(data, list) else 'N/A'}")
                        print(f"    Data: {str(data)[:300]}")
                except Exception as e:
                    print(f"  {endpoint}: ERROR - {str(e)[:100]}")


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s'])

