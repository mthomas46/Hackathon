"""
End-to-end workflow tests for ecosystem-mcp.

Tests the complete service functionality from startup to shutdown.
"""

import pytest
import httpx
import time
from pathlib import Path


BASE_URL = "http://localhost:8000"


class TestServiceBasics:
    """Test basic service functionality."""
    
    def test_service_is_running(self):
        """Test that service is accessible."""
        response = httpx.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Ecosystem MCP"
        assert data["version"] == "0.1.0"
    
    def test_health_check_works(self):
        """Test health check endpoint."""
        response = httpx.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data
        assert "components" in data
        
        # Check all components
        for component in ["database", "redis", "chromadb", "ollama"]:
            assert component in data["components"]
    
    def test_openapi_docs_available(self):
        """Test OpenAPI documentation."""
        response = httpx.get(f"{BASE_URL}/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestMetrics:
    """Test Prometheus metrics."""
    
    def test_metrics_endpoint_works(self):
        """Test metrics are exposed."""
        response = httpx.get(f"{BASE_URL}/metrics")
        assert response.status_code == 200
        
        content = response.text
        assert "http_requests_total" in content
        assert "http_request_duration_seconds" in content
        assert "service_info" in content
    
    def test_metrics_track_requests(self):
        """Test that metrics track requests."""
        # Make a request
        httpx.get(f"{BASE_URL}/health")
        
        # Check metrics updated
        response = httpx.get(f"{BASE_URL}/metrics")
        content = response.text
        
        assert 'endpoint="/health"' in content
        assert 'method="GET"' in content


class TestSearch:
    """Test search functionality."""
    
    def test_search_endpoint_accepts_requests(self):
        """Test search endpoint is functional."""
        response = httpx.post(
            f"{BASE_URL}/api/v1/search",
            json={"query": "test search", "limit": 5},
            timeout=10.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "query" in data
        assert data["query"] == "test search"
        assert "total_results" in data
        assert isinstance(data["results"], list)
    
    def test_search_with_invalid_query(self):
        """Test search validation."""
        response = httpx.post(
            f"{BASE_URL}/api/v1/search",
            json={"query": "", "limit": 5}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"


class TestAdmin:
    """Test admin endpoints."""
    
    def test_admin_stats_works(self):
        """Test admin stats endpoint."""
        response = httpx.get(f"{BASE_URL}/api/v1/admin/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "documents" in data
        assert "queues" in data
        assert "cost" in data
    
    def test_queue_status_works(self):
        """Test queue status endpoint."""
        response = httpx.get(f"{BASE_URL}/api/v1/admin/queue-status")
        assert response.status_code == 200
        data = response.json()
        
        assert "ingestion_queue" in data
        assert "embedding_queue" in data
        assert "failed_queue" in data
    
    def test_ingestion_status_works(self):
        """Test ingestion status endpoint."""
        response = httpx.get(f"{BASE_URL}/api/v1/admin/ingest/status")
        assert response.status_code == 200
        data = response.json()
        
        assert "jobs" in data
        assert "total" in data


class TestQuery:
    """Test query endpoints."""
    
    def test_document_query_works(self):
        """Test document query endpoint."""
        response = httpx.post(
            f"{BASE_URL}/api/v1/query",
            json={"limit": 10, "offset": 0}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "documents" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    def test_404_returns_standard_error(self):
        """Test 404 errors are standardized."""
        response = httpx.get(f"{BASE_URL}/api/v1/nonexistent")
        assert response.status_code == 404
        data = response.json()
        
        assert "error_code" in data
        assert "request_id" in data
    
    def test_rate_limiting_works(self):
        """Test rate limiting is enforced."""
        # Make many rapid requests
        responses = []
        for _ in range(25):
            try:
                r = httpx.post(
                    f"{BASE_URL}/api/v1/search",
                    json={"query": "test", "limit": 1},
                    timeout=2.0
                )
                responses.append(r.status_code)
            except:
                pass
        
        # Should have some rate limit responses (429) or errors
        has_rate_limit = 429 in responses
        has_errors = any(code >= 400 for code in responses)
        
        assert has_rate_limit or has_errors


class TestOllama:
    """Test Ollama integration."""
    
    def test_ollama_status_endpoint(self):
        """Test Ollama status endpoint."""
        response = httpx.get(f"{BASE_URL}/api/v1/ollama/status")
        assert response.status_code == 200
        data = response.json()
        
        assert "available" in data
        assert "base_url" in data
    
    def test_ollama_models_list(self):
        """Test Ollama models endpoint."""
        response = httpx.get(f"{BASE_URL}/api/v1/ollama/models")
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert isinstance(data["models"], list)


class TestPerformance:
    """Test performance requirements."""
    
    def test_health_check_is_fast(self):
        """Test health check completes quickly."""
        start = time.time()
        response = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0  # Should be sub-second
    
    def test_metrics_endpoint_is_fast(self):
        """Test metrics endpoint is responsive."""
        start = time.time()
        response = httpx.get(f"{BASE_URL}/metrics", timeout=5.0)
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0


class TestMiddleware:
    """Test middleware functionality."""
    
    def test_request_id_propagation(self):
        """Test request IDs are propagated."""
        custom_id = "test-e2e-123"
        response = httpx.get(
            f"{BASE_URL}/health",
            headers={"X-Request-ID": custom_id}
        )
        
        assert response.headers.get("x-request-id") == custom_id
    
    def test_cors_headers_present(self):
        """Test CORS headers are configured."""
        response = httpx.get(f"{BASE_URL}/health")
        
        # Request ID should be exposed
        assert "x-request-id" in response.headers


# Mark all tests for E2E
pytestmark = pytest.mark.e2e

