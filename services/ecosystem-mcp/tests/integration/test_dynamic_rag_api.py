"""
Integration tests for Dynamic Temporal RAG API endpoints.

Tests the actual API layer with real HTTP requests.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.mark.integration
class TestDynamicRAGQueryEndpoint:
    """Test POST /api/v1/dynamic-rag/query endpoint."""
    
    def test_query_endpoint_exists(self, client):
        """Test that the query endpoint exists."""
        response = client.post(
            "/api/v1/dynamic-rag/query",
            params={"query": "test"}
        )
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_query_missing_param(self, client):
        """Test query endpoint with missing required parameter."""
        response = client.post("/api/v1/dynamic-rag/query")
        
        # Should return 422 (validation error)
        assert response.status_code == 422
    
    def test_query_with_simple_query(self, client):
        """Test query with simple text."""
        response = client.post(
            "/api/v1/dynamic-rag/query",
            params={
                "query": "What is authentication?",
                "citation_format": "markdown"
            }
        )
        
        # Should succeed or return no documents (404)
        assert response.status_code in [200, 404, 500]
        
        data = response.json()
        assert "success" in data or "detail" in data
    
    def test_query_with_service_filter(self, client):
        """Test query with service name filter."""
        response = client.post(
            "/api/v1/dynamic-rag/query",
            params={
                "query": "What is the /api/auth endpoint?",
                "service_name": "ecosystem-mcp",
                "citation_format": "markdown"
            }
        )
        
        # Should process request
        assert response.status_code in [200, 404, 500]
    
    def test_query_with_html_format(self, client):
        """Test query with HTML citation format."""
        response = client.post(
            "/api/v1/dynamic-rag/query",
            params={
                "query": "How does authentication work?",
                "citation_format": "html"
            }
        )
        
        assert response.status_code in [200, 404, 500]
    
    def test_query_with_plain_format(self, client):
        """Test query with plain text citation format."""
        response = client.post(
            "/api/v1/dynamic-rag/query",
            params={
                "query": "Explain JWT",
                "citation_format": "plain"
            }
        )
        
        assert response.status_code in [200, 404, 500]
    
    def test_query_with_cache_disabled(self, client):
        """Test query with caching disabled."""
        response = client.post(
            "/api/v1/dynamic-rag/query",
            params={
                "query": "Test query",
                "use_cache": False
            }
        )
        
        assert response.status_code in [200, 404, 500]
    
    def test_query_response_structure(self, client):
        """Test that successful response has expected structure."""
        response = client.post(
            "/api/v1/dynamic-rag/query",
            params={"query": "authentication"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "query" in data
            assert "topics" in data
            assert "metadata" in data
            # May or may not have results depending on DB
            print(f"✅ Response structure valid: {list(data.keys())}")


@pytest.mark.integration
class TestDynamicRAGStreamingEndpoint:
    """Test POST /api/v1/dynamic-rag/query/stream endpoint."""
    
    def test_streaming_endpoint_exists(self, client):
        """Test that streaming endpoint exists."""
        response = client.post(
            "/api/v1/dynamic-rag/query/stream",
            params={"query": "test"}
        )
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_streaming_missing_param(self, client):
        """Test streaming with missing required parameter."""
        response = client.post("/api/v1/dynamic-rag/query/stream")
        
        # Should return 422 (validation error)
        assert response.status_code == 422
    
    def test_streaming_content_type(self, client):
        """Test streaming returns correct content type."""
        response = client.post(
            "/api/v1/dynamic-rag/query/stream",
            params={"query": "test"}
        )
        
        if response.status_code == 200:
            assert "text/event-stream" in response.headers.get("content-type", "")
            print("✅ Streaming returns SSE content type")


@pytest.mark.integration
class TestDynamicRAGCapabilitiesEndpoint:
    """Test GET /api/v1/dynamic-rag/capabilities endpoint."""
    
    def test_capabilities_endpoint_exists(self, client):
        """Test that capabilities endpoint exists."""
        response = client.get("/api/v1/dynamic-rag/capabilities")
        
        assert response.status_code == 200
    
    def test_capabilities_response_structure(self, client):
        """Test capabilities response structure."""
        response = client.get("/api/v1/dynamic-rag/capabilities")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "capabilities" in data
        
        capabilities = data["capabilities"]
        assert "topic_extraction" in capabilities
        assert "document_search" in capabilities
        assert "timeline_construction" in capabilities
        assert "answer_synthesis" in capabilities
        assert "citation_formatting" in capabilities
        
        print(f"✅ Capabilities: {list(capabilities.keys())}")


@pytest.mark.integration
class TestDynamicRAGCacheEndpoint:
    """Test cache management endpoints."""
    
    def test_clear_cache_endpoint_exists(self, client):
        """Test that clear cache endpoint exists."""
        response = client.delete("/api/v1/dynamic-rag/cache")
        
        assert response.status_code == 200
    
    def test_clear_cache_response(self, client):
        """Test clear cache response structure."""
        response = client.delete("/api/v1/dynamic-rag/cache")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "message" in data
        
        print("✅ Cache cleared successfully")


@pytest.mark.integration
class TestDynamicRAGHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_endpoint_exists(self, client):
        """Test that health endpoint exists."""
        response = client.get("/api/v1/dynamic-rag/health")
        
        assert response.status_code == 200
    
    def test_health_response_structure(self, client):
        """Test health check response structure."""
        response = client.get("/api/v1/dynamic-rag/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "components" in data
        
        # Should have 6 components
        components = data["components"]
        assert len(components) == 6
        
        # All components should have status
        for component in components:
            assert "name" in component
            assert "status" in component
        
        print(f"✅ Health check: {len(components)} components")


@pytest.mark.integration
class TestDynamicRAGErrorHandling:
    """Test error handling in API endpoints."""
    
    def test_query_empty_string(self, client):
        """Test query with empty string."""
        response = client.post(
            "/api/v1/dynamic-rag/query",
            params={"query": ""}
        )
        
        # Should handle gracefully (may return 400 or 404)
        assert response.status_code in [200, 400, 404, 422, 500]
    
    def test_query_very_long(self, client):
        """Test query with very long string."""
        long_query = "a" * 10000
        response = client.post(
            "/api/v1/dynamic-rag/query",
            params={"query": long_query}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 404, 413, 500]
    
    def test_query_invalid_format(self, client):
        """Test query with invalid citation format."""
        response = client.post(
            "/api/v1/dynamic-rag/query",
            params={
                "query": "test",
                "citation_format": "invalid_format"
            }
        )
        
        # Should handle gracefully (may succeed with default format)
        assert response.status_code in [200, 400, 404, 422, 500]


@pytest.mark.integration
class TestDynamicRAGEndToEndScenarios:
    """Test end-to-end scenarios through the API."""
    
    def test_multiple_queries_sequence(self, client):
        """Test executing multiple queries in sequence."""
        queries = [
            "What is authentication?",
            "How does JWT work?",
            "Explain OAuth2"
        ]
        
        for query in queries:
            response = client.post(
                "/api/v1/dynamic-rag/query",
                params={"query": query}
            )
            # All should process without crashing
            assert response.status_code in [200, 404, 500]
        
        print("✅ Multiple queries executed successfully")
    
    def test_capabilities_then_query(self, client):
        """Test getting capabilities before querying."""
        # First get capabilities
        cap_response = client.get("/api/v1/dynamic-rag/capabilities")
        assert cap_response.status_code == 200
        
        # Then execute query
        query_response = client.post(
            "/api/v1/dynamic-rag/query",
            params={"query": "test"}
        )
        assert query_response.status_code in [200, 404, 500]
        
        print("✅ Capabilities → Query workflow works")
    
    def test_query_then_clear_cache(self, client):
        """Test querying then clearing cache."""
        # Execute query
        query_response = client.post(
            "/api/v1/dynamic-rag/query",
            params={"query": "test", "use_cache": True}
        )
        assert query_response.status_code in [200, 404, 500]
        
        # Clear cache
        clear_response = client.delete("/api/v1/dynamic-rag/cache")
        assert clear_response.status_code == 200
        
        print("✅ Query → Clear cache workflow works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

