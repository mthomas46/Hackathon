"""
Diagnostic tests for service connectivity issues.

These tests help identify and validate fixes for:
1. doc_store port configuration
2. MCP → doc_store connectivity
3. Gateway registration
"""

import pytest
import httpx
import asyncio
import subprocess
import json


@pytest.mark.diagnostic
@pytest.mark.asyncio
class TestDocStoreConnectivity:
    """Diagnostic tests for doc_store connectivity."""
    
    async def test_doc_store_is_running(self):
        """Verify doc_store container is running."""
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=doc_store', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )
        
        assert 'doc_store' in result.stdout, "doc_store container not running!"
    
    async def test_doc_store_health_check(self):
        """Test doc_store health endpoint."""
        # Try common ports
        ports_to_try = [5087, 5010, 8007]
        
        for port in ports_to_try:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"http://localhost:{port}/health")
                    if response.status_code == 200:
                        print(f"\n✅ doc_store responding on port {port}")
                        print(f"Response: {response.json()}")
                        return  # Success!
            except Exception as e:
                print(f"\n⚠️ Port {port} failed: {e}")
                continue
        
        pytest.fail("doc_store not responding on any common port!")
    
    async def test_doc_store_port_matches_mcp_config(self):
        """Verify MCP-base is configured with correct doc_store port."""
        # Read Dockerfile to see what URL is configured
        with open('docker/mcp-base/Dockerfile', 'r') as f:
            dockerfile_content = f.read()
        
        # Find DOC_STORE_URL configuration
        if 'DOC_STORE_URL' in dockerfile_content:
            # Extract the default URL
            for line in dockerfile_content.split('\n'):
                if 'DOC_STORE_URL' in line and 'doc_store' in line:
                    print(f"\n📋 Found in Dockerfile: {line}")
                    
                    # Check if it matches actual port
                    if ':8007' in line:
                        print("⚠️ Configured for port 8007")
                    elif ':5010' in line:
                        print("✅ Configured for port 5010")
                    elif ':5087' in line:
                        print("✅ Configured for port 5087")
        
        # Now check what port doc_store is actually using
        result = subprocess.run(
            ['docker', 'inspect', 'doc_store', '--format', '{{.Config.Env}}'],
            capture_output=True,
            text=True
        )
        
        print(f"\n📋 doc_store actual env: {result.stdout}")
        
        # This test documents the mismatch - we'll fix it next
        assert True, "Documentation test - see output above"


@pytest.mark.diagnostic
@pytest.mark.asyncio
class TestMCPDocStoreConnection:
    """Test MCP's ability to connect to doc_store."""
    
    async def test_mcp_can_reach_doc_store(self):
        """
        Test if a deployed MCP can actually reach doc_store.
        
        This simulates what the MCP container experiences.
        """
        # Find a running MCP
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=mcp-mcp-horus', '--format', '{{.Names}}', '--latest'],
            capture_output=True,
            text=True
        )
        
        mcp_container = result.stdout.strip().split('\n')[0] if result.stdout.strip() else None
        
        if not mcp_container:
            pytest.skip("No MCP container running")
        
        print(f"\n🔍 Testing from MCP container: {mcp_container}")
        
        # Try to reach doc_store from inside MCP container
        urls_to_test = [
            'http://doc_store:8007/health',
            'http://doc_store:5010/health',
            'http://doc_store:5087/health',
        ]
        
        for url in urls_to_test:
            result = subprocess.run(
                ['docker', 'exec', mcp_container, 'curl', '-s', '-m', '2', url],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                print(f"✅ {url} - REACHABLE")
                print(f"   Response: {result.stdout[:100]}")
                return  # Success!
            else:
                print(f"❌ {url} - FAILED")
        
        pytest.fail(f"MCP container {mcp_container} cannot reach doc_store on any port!")


@pytest.mark.diagnostic
@pytest.mark.asyncio
class TestGatewayRegistration:
    """Diagnostic tests for gateway registration."""
    
    async def test_gateway_register_endpoint_exists(self):
        """Verify gateway has /api/v1/gateway/register endpoint."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try POST to register endpoint (with dummy data)
            response = await client.post(
                "http://localhost:8001/api/v1/gateway/register",
                json={
                    "mcp_id": "test-diagnostic",
                    "host": "localhost",
                    "port": 9999,
                    "name": "Diagnostic Test MCP",
                    "tier": 0,
                    "health_check_url": "http://localhost:9999/health"
                }
            )
            
            print(f"\n📋 Register endpoint status: {response.status_code}")
            print(f"📋 Response: {response.text[:200]}")
            
            # Accept 200, 201, or even 400 (endpoint exists but validation failed)
            assert response.status_code in [200, 201, 400, 422], \
                f"Register endpoint returned unexpected status: {response.status_code}"
    
    async def test_gateway_instances_endpoint_exists(self):
        """Verify gateway has /api/v1/gateway/instances endpoint."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8001/api/v1/gateway/instances")
            
            print(f"\n📋 Instances endpoint status: {response.status_code}")
            print(f"📋 Response: {response.text[:200]}")
            
            assert response.status_code == 200, \
                f"Instances endpoint failed: {response.status_code}"
            
            # Check if it returns a list
            data = response.json()
            assert isinstance(data, list), "Expected list of instances"
            
            print(f"📊 Currently registered MCPs: {len(data)}")
            for instance in data:
                print(f"   - {instance.get('mcp_id', 'unknown')}")
    
    async def test_provisioner_attempts_registration(self):
        """Check if provisioner is actually calling gateway registration."""
        # Check provisioner logs for gateway registration attempts
        result = subprocess.run(
            ['docker', 'logs', 'mcp-provisioner', '--tail', '100'],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout + result.stderr
        
        # Look for gateway-related log messages
        gateway_mentions = [line for line in logs.split('\n') if 'gateway' in line.lower()]
        
        print(f"\n📋 Gateway-related log lines: {len(gateway_mentions)}")
        for line in gateway_mentions[-10:]:  # Last 10
            print(f"   {line[:150]}")
        
        # This is a documentation test - we want to see what's happening
        assert True, "Check output above for gateway registration attempts"


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s', '-m', 'diagnostic'])

