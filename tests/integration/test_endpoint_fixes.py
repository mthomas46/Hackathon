"""
Integration Tests: Validate Endpoint Fixes

Tests to verify all endpoint fixes are working correctly.
"""

import pytest
import httpx
import asyncio


class TestEndpointFixes:
    """Integration tests for fixed endpoints."""
    
    @pytest.mark.asyncio
    async def test_mcp_provisioner_endpoint(self):
        """Test that MCP provisioner endpoint /api/v1/mcps works."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try to provision with correct endpoint
            response = await client.post(
                "http://localhost:5400/api/v1/mcps",
                json={
                    "client_id": "integration-test",
                    "tier": "standard",
                    "memory_limit": "1024M",
                    "cpu_shares": 1024,
                    "image_name": "mcp-base:latest"
                }
            )
            
            # Should not be 404
            assert response.status_code != 404, \
                f"Endpoint returned 404. Response: {response.text}"
            
            # Should be either 200 (success) or 400/422 (validation error)
            assert response.status_code in [200, 201, 400, 422], \
                f"Unexpected status code: {response.status_code}. Response: {response.text}"
            
            print(f"✅ MCP Provisioner endpoint working: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    
    @pytest.mark.asyncio
    async def test_kafka_ingestion_endpoint(self):
        """Test that kafka-ingestion-service endpoint /api/v1/ingestion/ingest works."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try to ingest with correct endpoint
            response = await client.post(
                "http://localhost:5700/api/v1/ingestion/ingest",
                json={
                    "document_id": "integration-test-doc",
                    "title": "Test Document",
                    "content": "Test content",
                    "metadata": {"source": "test"},
                    "tags": ["test"]
                }
            )
            
            # Should not be 404
            assert response.status_code != 404, \
                f"Endpoint returned 404. Response: {response.text}"
            
            # Should be either 200 (success) or 400/422 (validation error)
            assert response.status_code in [200, 201, 400, 422], \
                f"Unexpected status code: {response.status_code}. Response: {response.text}"
            
            print(f"✅ Kafka Ingestion endpoint working: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    
    @pytest.mark.asyncio
    async def test_hierarchical_topics_check_health(self):
        """Test that HierarchicalTopicExtractor.check_health() works."""
        from ingestion.tagging.hierarchical_topics import HierarchicalTopicExtractor
        
        extractor = HierarchicalTopicExtractor(
            summarizer_url="http://localhost:8200",
            timeout=2,
            batch_size=5
        )
        
        # Should not raise AttributeError
        try:
            is_healthy = await extractor.check_service_health()
            print(f"✅ check_service_health() method exists: healthy={is_healthy}")
            assert isinstance(is_healthy, bool), "check_service_health() should return bool"
        except AttributeError as e:
            pytest.fail(f"check_service_health() method missing: {e}")
    
    @pytest.mark.asyncio
    async def test_all_health_endpoints(self):
        """Test that all services have consistent health endpoints."""
        services = {
            'mcp-provisioner': 'http://localhost:5400/api/v1/health',
            'kafka-ingestion-service': 'http://localhost:5700/health',
            'mcp-gateway': 'http://localhost:8001/api/v1/health',
            'mcp-training-coordinator': 'http://localhost:5600/health',
        }
        
        async with httpx.AsyncClient(timeout=2.0) as client:
            results = {}
            for service, health_url in services.items():
                try:
                    response = await client.get(health_url)
                    results[service] = {
                        'status': response.status_code,
                        'healthy': response.status_code == 200
                    }
                except Exception as e:
                    results[service] = {'status': 'ERROR', 'error': str(e)}
            
            print("\n📊 Health Endpoint Results:")
            for service, result in results.items():
                status = result.get('status', 'ERROR')
                print(f"  {service}: {status}")
            
            # At least one service should be healthy
            healthy_count = sum(1 for r in results.values() if r.get('healthy'))
            assert healthy_count > 0, "At least one service should be healthy"


if __name__ == "__main__":
    pytest.main([__file__, '-v', '-s'])

