"""
Integration tests for Phase 2 features (live service).

Tests against running service at http://localhost:8000.
Run with: pytest tests/integration/test_phase2_live.py -v
"""

import pytest
import time
import httpx

# Base URL for tests
BASE_URL = "http://localhost:8000"


# @pytest.mark.skip(reason="Requires running server at localhost:8000 - end-to-end test")
class TestHealthCheck:
    """Test enhanced health check."""
    
    def test_health_returns_detailed_status(self):
        """Test health endpoint returns component details."""
        response = httpx.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "components" in data
        
        # Check components
        components = data["components"]
        for name in ["database", "redis", "chromadb", "ollama"]:
            assert name in components
            assert "status" in components[name]
            assert "response_time_ms" in components[name]
    
    def test_health_includes_request_id(self):
        """Test health response includes request ID."""
        response = httpx.get(f"{BASE_URL}/health")
        
        assert "x-request-id" in response.headers


# @pytest.mark.skip(reason="Requires running server at localhost:8000 - end-to-end test")
class TestErrorHandling:
    """Test standardized error responses."""
    
    def test_validation_error_standardized(self):
        """Test validation errors are standardized."""
        response = httpx.post(
            f"{BASE_URL}/api/v1/search",
            json={"query": "", "limit": 10}
        )
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["success"] is False
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "request_id" in data
        assert "details" in data
    
    def test_404_error_standardized(self):
        """Test 404 errors return proper response."""
        response = httpx.get(f"{BASE_URL}/api/v1/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        
        # FastAPI default 404 format
        assert "detail" in data
        assert data["detail"] == "Not Found"


# @pytest.mark.skip(reason="Requires running server at localhost:8000 - end-to-end test")
class TestMiddleware:
    """Test middleware functionality."""
    
    def test_request_id_generated(self):
        """Test request ID is auto-generated."""
        response = httpx.get(f"{BASE_URL}/health")
        
        assert "x-request-id" in response.headers
    
    def test_request_id_propagated(self):
        """Test custom request ID is propagated."""
        custom_id = "test-123"
        response = httpx.get(
            f"{BASE_URL}/health",
            headers={"X-Request-ID": custom_id}
        )
        
        assert response.headers["x-request-id"] == custom_id
    
    def test_timeout_doesnt_hang(self):
        """Test requests complete within reasonable time."""
        start = time.time()
        response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 5.0  # Health should be fast


# @pytest.mark.skip(reason="Requires running server at localhost:8000 - end-to-end test")
class TestAPIDocumentation:
    """Test API documentation."""
    
    def test_openapi_json_available(self):
        """Test OpenAPI JSON is available."""
        response = httpx.get(f"{BASE_URL}/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    def test_docs_available(self):
        """Test Swagger UI is available."""
        response = httpx.get(f"{BASE_URL}/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_redoc_available(self):
        """Test ReDoc is available."""
        response = httpx.get(f"{BASE_URL}/redoc")
        
        assert response.status_code == 200


# @pytest.mark.skip(reason="Requires running server at localhost:8000 - end-to-end test")
class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_returns_info(self):
        """Test root returns service info."""
        response = httpx.get(f"{BASE_URL}/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "docs" in data


# @pytest.mark.skip(reason="Requires running server at localhost:8000 - end-to-end test")
class TestRateLimiting:
    """Test rate limiting (careful - may affect other tests)."""
    
    @pytest.mark.slow
    def test_rate_limiting_eventually_triggers(self):
        """Test that rate limiting eventually triggers."""
        # Make many rapid requests
        status_codes = []
        
        for _ in range(30):
            try:
                response = httpx.post(
                    f"{BASE_URL}/api/v1/search",
                    json={"query": "test", "limit": 1},
                    timeout=5.0
                )
                status_codes.append(response.status_code)
            except:
                pass
        
        # Should have some non-200 responses (rate limit or other errors)
        has_errors = any(code != 200 for code in status_codes)
        assert has_errors


# Mark all tests to require live service
pytestmark = pytest.mark.integration

