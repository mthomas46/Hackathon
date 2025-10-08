"""
Diagnostic Tests: Service Endpoint Discovery

This test suite systematically probes all service endpoints to:
1. Discover correct API paths
2. Identify missing endpoints
3. Validate request/response formats
4. Expose root causes of 404 errors
"""

import pytest
import httpx
import asyncio
from typing import Dict, List


class TestServiceEndpointDiscovery:
    """Discover actual working endpoints for each service."""
    
    @pytest.fixture
    def services(self):
        """Service configurations."""
        return {
            'mcp-provisioner': {
                'base_url': 'http://localhost:5400',
                'expected_endpoints': [
                    '/mcps',  # Likely provision endpoint
                    '/api/v1/provision',
                    '/api/v1/mcps',
                ]
            },
            'kafka-ingestion-service': {
                'base_url': 'http://localhost:5700',
                'expected_endpoints': [
                    '/events',  # Likely ingest endpoint
                    '/api/v1/ingest',
                    '/api/v1/events',
                    '/ingest',
                ]
            },
            'mcp-gateway': {
                'base_url': 'http://localhost:8001',
                'expected_endpoints': [
                    '/api/v1/query',
                    '/query',
                    '/api/query',
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_discover_provisioner_endpoints(self, services):
        """Test 1: Discover mcp-provisioner's actual provision endpoint."""
        service = services['mcp-provisioner']
        base_url = service['base_url']
        
        print(f"\n🔍 Testing {base_url}...")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            results = {}
            
            # Test each potential endpoint
            for endpoint in service['expected_endpoints']:
                url = f"{base_url}{endpoint}"
                
                # Try OPTIONS to see if endpoint exists
                try:
                    response = await client.options(url)
                    results[endpoint] = {
                        'exists': response.status_code != 404,
                        'status': response.status_code,
                        'methods': response.headers.get('Allow', 'unknown')
                    }
                except Exception as e:
                    results[endpoint] = {'exists': False, 'error': str(e)}
                
                # Try POST with minimal payload
                try:
                    response = await client.post(
                        url,
                        json={
                            'client_id': 'test',
                            'tier': 1,
                            'memory_limit': 1024,
                            'cpu_shares': 1024
                        }
                    )
                    results[endpoint]['post_status'] = response.status_code
                    results[endpoint]['post_response'] = response.text[:200]
                except Exception as e:
                    results[endpoint]['post_error'] = str(e)
            
            # Print results
            print("\n📊 Provisioner Endpoint Results:")
            for endpoint, result in results.items():
                print(f"  {endpoint}:")
                print(f"    Exists: {result.get('exists', False)}")
                print(f"    POST Status: {result.get('post_status', 'N/A')}")
                if 'post_response' in result:
                    print(f"    Response: {result['post_response']}")
            
            # Find working endpoint
            working_endpoints = [
                ep for ep, res in results.items()
                if res.get('post_status') not in [404, None]
            ]
            
            assert len(working_endpoints) > 0, \
                f"No working provision endpoint found! Tried: {list(results.keys())}"
            
            print(f"\n✅ Working endpoint(s): {working_endpoints}")
            return working_endpoints[0]
    
    @pytest.mark.asyncio
    async def test_discover_ingestion_endpoints(self, services):
        """Test 2: Discover kafka-ingestion-service's actual ingest endpoint."""
        service = services['kafka-ingestion-service']
        base_url = service['base_url']
        
        print(f"\n🔍 Testing {base_url}...")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            results = {}
            
            for endpoint in service['expected_endpoints']:
                url = f"{base_url}{endpoint}"
                
                # Try POST with document payload
                try:
                    response = await client.post(
                        url,
                        json={
                            'document_id': 'test-doc',
                            'title': 'Test',
                            'content': 'Test content',
                            'event_type': 'DOCUMENT_CREATED',
                            'source_metadata': {'source': 'test'},
                            'tags': ['test']
                        }
                    )
                    results[endpoint] = {
                        'status': response.status_code,
                        'response': response.text[:200]
                    }
                except Exception as e:
                    results[endpoint] = {'error': str(e)}
            
            # Print results
            print("\n📊 Ingestion Endpoint Results:")
            for endpoint, result in results.items():
                print(f"  {endpoint}:")
                print(f"    Status: {result.get('status', 'ERROR')}")
                if 'response' in result:
                    print(f"    Response: {result['response']}")
            
            # Find working endpoint
            working_endpoints = [
                ep for ep, res in results.items()
                if res.get('status') not in [404, None]
            ]
            
            assert len(working_endpoints) > 0, \
                f"No working ingest endpoint found! Tried: {list(results.keys())}"
            
            print(f"\n✅ Working endpoint(s): {working_endpoints}")
            return working_endpoints[0]
    
    @pytest.mark.asyncio
    async def test_discover_gateway_endpoints(self, services):
        """Test 3: Discover mcp-gateway's actual query endpoint."""
        service = services['mcp-gateway']
        base_url = service['base_url']
        
        print(f"\n🔍 Testing {base_url}...")
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            results = {}
            
            for endpoint in service['expected_endpoints']:
                url = f"{base_url}{endpoint}"
                
                # Try POST with query payload
                try:
                    response = await client.post(
                        url,
                        json={
                            'mcp_id': 'test-mcp',
                            'query': 'test query',
                            'context': {}
                        }
                    )
                    results[endpoint] = {
                        'status': response.status_code,
                        'response': response.text[:200]
                    }
                except Exception as e:
                    results[endpoint] = {'error': str(e)}
            
            # Print results
            print("\n📊 Gateway Endpoint Results:")
            for endpoint, result in results.items():
                print(f"  {endpoint}:")
                print(f"    Status: {result.get('status', 'ERROR')}")
                if 'response' in result:
                    print(f"    Response: {result['response']}")
            
            # Find working endpoint
            working_endpoints = [
                ep for ep, res in results.items()
                if res.get('status') not in [404, None]
            ]
            
            print(f"\n✅ Working endpoint(s): {working_endpoints if working_endpoints else 'NONE - This is expected if no MCP exists'}")
            return working_endpoints[0] if working_endpoints else None


class TestServiceHealthDetailed:
    """Detailed health checks to expose unhealthy services."""
    
    @pytest.mark.asyncio
    async def test_provisioner_health_detailed(self):
        """Test 4: Detailed health check for mcp-provisioner."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try multiple health endpoints
            health_endpoints = [
                'http://localhost:5400/health',
                'http://localhost:5400/api/health',
                'http://localhost:5400/api/v1/health',
            ]
            
            print("\n🏥 MCP Provisioner Health:")
            for url in health_endpoints:
                try:
                    response = await client.get(url)
                    print(f"  {url}: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"    Status: {data.get('status')}")
                        print(f"    Dependencies: {data.get('dependencies', {})}")
                except Exception as e:
                    print(f"  {url}: ERROR - {e}")
    
    @pytest.mark.asyncio
    async def test_ingestion_health_detailed(self):
        """Test 5: Detailed health check for kafka-ingestion-service."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            health_endpoints = [
                'http://localhost:5700/health',
                'http://localhost:5700/api/health',
                'http://localhost:5700/api/v1/health',
            ]
            
            print("\n🏥 Kafka Ingestion Service Health:")
            for url in health_endpoints:
                try:
                    response = await client.get(url)
                    print(f"  {url}: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"    Status: {data.get('status')}")
                except Exception as e:
                    print(f"  {url}: ERROR - {e}")


class TestDockerInspection:
    """Test Docker container states to identify unhealthy services."""
    
    def test_check_unhealthy_containers(self):
        """Test 6: Check why containers are unhealthy."""
        import subprocess
        
        print("\n🐳 Docker Container Health:")
        
        # Get unhealthy containers
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'health=unhealthy', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )
        
        unhealthy = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        if unhealthy:
            print(f"  Unhealthy containers: {unhealthy}")
            
            # Get logs for each unhealthy container
            for container in unhealthy:
                if container:
                    print(f"\n  📜 Last 20 lines of logs for {container}:")
                    log_result = subprocess.run(
                        ['docker', 'logs', '--tail', '20', container],
                        capture_output=True,
                        text=True
                    )
                    print(f"    {log_result.stdout}")
                    if log_result.stderr:
                        print(f"    STDERR: {log_result.stderr}")
        else:
            print("  ✅ No unhealthy containers!")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, '-v', '-s'])

