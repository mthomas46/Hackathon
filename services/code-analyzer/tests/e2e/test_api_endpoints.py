"""
End-to-end tests for FastAPI endpoints.

These tests verify that all API endpoints are working correctly,
including the standard endpoints and core analysis functionality.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

# Create test client
client = TestClient(app)


# ============================================================================
# Standard Endpoints Tests
# ============================================================================

class TestStandardEndpoints:
    """Test standard endpoints required by all services."""
    
    def test_health_endpoint_returns_200(self):
        """Test that /health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
        
    def test_health_endpoint_returns_correct_data(self):
        """Test that /health returns correct health information."""
        response = client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "code-analyzer"
        assert "version" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert data["checks"]["domain_layer"] == "ok"
        
    def test_about_me_endpoint_returns_200(self):
        """Test that /about-me endpoint returns 200 OK."""
        response = client.get("/about-me")
        assert response.status_code == 200
        
    def test_about_me_returns_service_info(self):
        """Test that /about-me returns comprehensive service information."""
        response = client.get("/about-me")
        data = response.json()
        
        assert data["service"] == "code-analyzer"
        assert "version" in data
        assert "description" in data
        assert "capabilities" in data
        assert "python" in data["features"]["languages"]
        assert data["architecture"]["pattern"] == "DDD (Domain-Driven Design)"
        
    def test_endpoints_list_returns_200(self):
        """Test that /endpoints returns 200 OK."""
        response = client.get("/endpoints")
        assert response.status_code == 200
        
    def test_endpoints_lists_all_endpoints(self):
        """Test that /endpoints lists all available endpoints."""
        response = client.get("/endpoints")
        data = response.json()
        
        assert data["service"] == "code-analyzer"
        assert "endpoints" in data
        assert len(data["endpoints"]) >= 4  # At least 4 standard endpoints
        
        # Check that standard endpoints are listed
        endpoint_paths = [e["path"] for e in data["endpoints"]]
        assert "/health" in endpoint_paths
        assert "/about-me" in endpoint_paths
        assert "/endpoints" in endpoint_paths
        assert "/provider-consumer" in endpoint_paths
        
    def test_provider_consumer_returns_200(self):
        """Test that /provider-consumer returns 200 OK."""
        response = client.get("/provider-consumer")
        assert response.status_code == 200
        
    def test_provider_consumer_shows_relationships(self):
        """Test that /provider-consumer shows service relationships."""
        response = client.get("/provider-consumer")
        data = response.json()
        
        assert data["service"] == "code-analyzer"
        assert "relationships" in data
        assert "providers" in data["relationships"]
        assert "consumers" in data["relationships"]
        assert data["self_contained"] is True


# ============================================================================
# Analysis Endpoint Tests
# ============================================================================

class TestAnalyzeEndpoint:
    """Test the /analyze endpoint for code analysis."""
    
    def test_analyze_simple_python_code(self):
        """Test analyzing a simple Python function."""
        response = client.post(
            "/analyze",
            json={
                "code": "def hello():\n    return 'Hello, World!'",
                "language": "python"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "analysis_id" in data
        assert data["status"] == "completed"
        assert data["language"] == "python"
        assert "results" in data
        
    def test_analyze_with_options(self):
        """Test analyzing code with custom options."""
        response = client.post(
            "/analyze",
            json={
                "code": "def calculate(x):\n    if x > 10:\n        return x * 2\n    return x",
                "language": "python",
                "options": {
                    "include_complexity": True,
                    "include_security": False,
                    "include_style": False
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "completed"
        assert "results" in data
        assert "complexity" in data["results"]
        
    def test_analyze_invalid_language(self):
        """Test that unsupported language returns 400."""
        response = client.post(
            "/analyze",
            json={
                "code": "console.log('test');",
                "language": "javascript"
            }
        )
        
        assert response.status_code == 400
        assert "Unsupported language" in response.json()["detail"]
        
    def test_analyze_malformed_code(self):
        """Test analyzing malformed code returns failed status."""
        response = client.post(
            "/analyze",
            json={
                "code": "def broken(:",
                "language": "python"
            }
        )
        
        assert response.status_code == 200  # Request succeeds
        data = response.json()
        
        assert data["status"] == "failed"
        assert "error" in data
        
    def test_analyze_returns_structures(self):
        """Test that analysis returns code structures."""
        response = client.post(
            "/analyze",
            json={
                "code": "def func1():\n    pass\n\ndef func2():\n    pass",
                "language": "python"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "structures" in data["results"]
        assert len(data["results"]["structures"]) >= 2
        
    def test_analyze_returns_complexity_metrics(self):
        """Test that analysis returns complexity metrics."""
        response = client.post(
            "/analyze",
            json={
                "code": "def complex(x):\n    if x > 5:\n        if x < 10:\n            return x\n    return 0",
                "language": "python"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "complexity" in data["results"]
        assert data["results"]["complexity"] is not None
        assert "cyclomatic" in data["results"]["complexity"]


# ============================================================================
# Documentation Endpoints Tests
# ============================================================================

class TestDocumentationEndpoints:
    """Test documentation endpoints."""
    
    def test_openapi_docs_available(self):
        """Test that OpenAPI docs are available at /docs."""
        response = client.get("/docs")
        assert response.status_code == 200
        
    def test_redoc_docs_available(self):
        """Test that ReDoc docs are available at /redoc."""
        response = client.get("/redoc")
        assert response.status_code == 200
        
    def test_openapi_json_available(self):
        """Test that OpenAPI JSON schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "info" in data
        assert data["info"]["title"] == "Code Analyzer Service"

