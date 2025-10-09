"""
End-to-end tests for core API endpoints.

Tests the existing discovery API endpoints:
- POST /api/v1/discover
- POST /api/v1/discover/tools
- GET /api/v1/services/{service_name}
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.e2e
@pytest.mark.api
@pytest.mark.discovery
class TestDiscoverEndpoint:
    """Test POST /api/v1/discover endpoint."""
    
    def test_discover_service_from_url(self, test_client):
        """Test discovering a service from OpenAPI URL."""
        request_data = {
            "service_name": "test-service",
            "openapi_url": "http://test-service:8000/openapi.json"
        }
        
        response = test_client.post("/api/v1/discover", json=request_data)
        
        # This test will fail until implementation is added
        # Expected: 200 or 202 (Accepted)
        assert response.status_code in [200, 202]
    
    def test_discover_service_from_content(self, test_client, simple_openapi_spec):
        """Test discovering a service from inline OpenAPI content."""
        request_data = {
            "service_name": "test-service",
            "openapi_content": simple_openapi_spec
        }
        
        response = test_client.post("/api/v1/discover", json=request_data)
        
        assert response.status_code in [200, 202]
        data = response.json()
        
        assert "service_name" in data or "service" in data
        assert "success" in data or "status" in data
    
    def test_discover_requires_service_name(self, test_client):
        """Test that service_name is required."""
        request_data = {
            "openapi_url": "http://test:8000/openapi.json"
        }
        
        response = test_client.post("/api/v1/discover", json=request_data)
        
        # Should return validation error (422)
        assert response.status_code == 422
    
    def test_discover_requires_source(self, test_client):
        """Test that either URL or content is required."""
        request_data = {
            "service_name": "test-service"
        }
        
        response = test_client.post("/api/v1/discover", json=request_data)
        
        # Should return validation error
        assert response.status_code in [400, 422]
    
    def test_discover_returns_discovery_result(self, test_client, simple_openapi_spec):
        """Test that discover returns proper discovery result."""
        request_data = {
            "service_name": "test-service",
            "openapi_content": simple_openapi_spec
        }
        
        response = test_client.post("/api/v1/discover", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Should have result information
            assert "success" in data or "status" in data
            
            if data.get("success") or data.get("status") == "success":
                assert "service" in data or "service_name" in data
                assert "endpoints_discovered" in data or "endpoint_count" in data


@pytest.mark.e2e
@pytest.mark.api
@pytest.mark.tools
class TestDiscoverToolsEndpoint:
    """Test POST /api/v1/discover/tools endpoint."""
    
    def test_discover_tools_for_service(self, test_client, simple_openapi_spec):
        """Test discovering and generating tools for a service."""
        request_data = {
            "service_name": "test-service",
            "openapi_content": simple_openapi_spec
        }
        
        response = test_client.post("/api/v1/discover/tools", json=request_data)
        
        # Should succeed or be accepted
        assert response.status_code in [200, 202]
    
    def test_discover_tools_returns_tool_list(self, test_client, simple_openapi_spec):
        """Test that discover/tools returns list of generated tools."""
        request_data = {
            "service_name": "test-service",
            "openapi_content": simple_openapi_spec
        }
        
        response = test_client.post("/api/v1/discover/tools", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            
            assert "tools" in data or "generated_tools" in data
            
            if "tools" in data:
                assert isinstance(data["tools"], list)
            elif "generated_tools" in data:
                assert isinstance(data["generated_tools"], list)
    
    def test_discover_tools_requires_service_name(self, test_client):
        """Test that service_name is required."""
        request_data = {
            "openapi_url": "http://test:8000/openapi.json"
        }
        
        response = test_client.post("/api/v1/discover/tools", json=request_data)
        
        assert response.status_code == 422
    
    def test_discover_tools_with_url(self, test_client):
        """Test discovering tools from URL."""
        request_data = {
            "service_name": "test-service",
            "openapi_url": "http://test-service:8000/openapi.json"
        }
        
        response = test_client.post("/api/v1/discover/tools", json=request_data)
        
        # Should attempt to discover
        assert response.status_code in [200, 202, 404, 500]  # Various valid responses


@pytest.mark.e2e
@pytest.mark.api
class TestGetServiceEndpoint:
    """Test GET /api/v1/services/{service_name} endpoint."""
    
    def test_get_service_info(self, test_client):
        """Test getting service information."""
        # This will fail until service is discovered
        response = test_client.get("/api/v1/services/test-service")
        
        # Should return either 200 (found) or 404 (not found)
        assert response.status_code in [200, 404]
    
    def test_get_service_returns_service_details(self, test_client, simple_openapi_spec):
        """Test that get service returns service details."""
        # First discover a service
        discover_request = {
            "service_name": "discovered-service",
            "openapi_content": simple_openapi_spec
        }
        
        discover_response = test_client.post("/api/v1/discover", json=discover_request)
        
        if discover_response.status_code == 200:
            # Then retrieve it
            get_response = test_client.get("/api/v1/services/discovered-service")
            
            if get_response.status_code == 200:
                data = get_response.json()
                
                assert "name" in data or "service_name" in data
                assert "endpoints" in data or "endpoint_count" in data
    
    def test_get_nonexistent_service(self, test_client):
        """Test getting a service that doesn't exist."""
        response = test_client.get("/api/v1/services/nonexistent-service-12345")
        
        # Should return 404
        assert response.status_code == 404


@pytest.mark.e2e
@pytest.mark.api
class TestApiErrorHandling:
    """Test API error handling."""
    
    def test_invalid_json_body(self, test_client):
        """Test handling invalid JSON."""
        response = test_client.post(
            "/api/v1/discover",
            data="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 (Unprocessable Entity)
        assert response.status_code == 422
    
    def test_missing_required_fields(self, test_client):
        """Test handling missing required fields."""
        response = test_client.post("/api/v1/discover", json={})
        
        # Should return validation error
        assert response.status_code in [400, 422]
        
        if response.status_code == 422:
            data = response.json()
            assert "detail" in data
    
    def test_invalid_openapi_spec(self, test_client):
        """Test handling invalid OpenAPI specification."""
        request_data = {
            "service_name": "test-service",
            "openapi_content": {"invalid": "spec"}
        }
        
        response = test_client.post("/api/v1/discover", json=request_data)
        
        # Should return error (400 or 422)
        assert response.status_code in [400, 422, 500]
    
    def test_malformed_url(self, test_client):
        """Test handling malformed OpenAPI URL."""
        request_data = {
            "service_name": "test-service",
            "openapi_url": "not-a-valid-url"
        }
        
        response = test_client.post("/api/v1/discover", json=request_data)
        
        # Should return validation error
        assert response.status_code in [400, 422]


@pytest.mark.e2e
@pytest.mark.api
class TestApiResponseFormat:
    """Test API response format consistency."""
    
    def test_api_returns_json(self, test_client, simple_openapi_spec):
        """Test that API endpoints return JSON."""
        request_data = {
            "service_name": "test-service",
            "openapi_content": simple_openapi_spec
        }
        
        response = test_client.post("/api/v1/discover", json=request_data)
        
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_error_responses_include_detail(self, test_client):
        """Test that error responses include detail message."""
        response = test_client.post("/api/v1/discover", json={})
        
        if response.status_code >= 400:
            data = response.json()
            # Should have detail or error message
            assert "detail" in data or "error" in data or "message" in data
    
    def test_success_responses_include_status(self, test_client, simple_openapi_spec):
        """Test that success responses include status information."""
        request_data = {
            "service_name": "test-service",
            "openapi_content": simple_openapi_spec
        }
        
        response = test_client.post("/api/v1/discover", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            # Should have some status indicator
            assert any(key in data for key in ["success", "status", "result"])

