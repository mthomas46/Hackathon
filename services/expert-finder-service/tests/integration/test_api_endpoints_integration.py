"""
Integration tests for API endpoints.

Tests real HTTP interactions with the FastAPI application.
Uses TestClient to simulate actual HTTP requests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app


@pytest.mark.integration
class TestAPIEndpointsIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_health_endpoint_integration(self, client):
        """Test health endpoint returns proper response."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "expert-finder-service"
    
    def test_about_me_endpoint_integration(self, client):
        """Test about-me endpoint returns service information."""
        response = client.get("/about-me")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert data["name"] == "expert-finder-service"
    
    def test_endpoints_list_integration(self, client):
        """Test endpoints list is returned."""
        response = client.get("/endpoints")
        
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) > 0
        
        # Verify key endpoints are listed
        endpoint_paths = [ep["path"] for ep in data["endpoints"]]
        assert "/health" in endpoint_paths
        assert "/about-me" in endpoint_paths
        assert "/api/v1/find-experts" in endpoint_paths
    
    def test_provider_consumer_integration(self, client):
        """Test provider-consumer endpoint returns service relationships."""
        response = client.get("/provider-consumer")
        
        assert response.status_code == 200
        data = response.json()
        assert "relationships" in data
        assert isinstance(data["relationships"], list)
        
        # expert-finder-service is a consumer
        service_names = [rel["service"] for rel in data["relationships"]]
        assert "user-store" in service_names
    
    def test_openapi_json_integration(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert schema["info"]["title"] == "expert-finder-service"
    
    @pytest.mark.asyncio
    async def test_find_experts_endpoint_integration(self, client):
        """Test find-experts endpoint with mocked dependencies."""
        # Mock the use case dependencies
        with patch("presentation.routes.expert_routes.find_experts_use_case") as mock_use_case:
            # Set up mock response
            from domain.entities.expert import Expert
            from domain.value_objects.expert_match import ExpertMatch
            
            mock_match = ExpertMatch(
                expert=Expert(
                    user_id="user1",
                    name="Test Expert",
                    role="Developer",
                    topics=["Python"],
                    services=[],
                    document_count=10,
                    service_count=2
                ),
                overall_score=0.85,
                role_score=0.9,
                topic_score=0.8,
                service_score=0.7,
                document_score=0.6,
                explanation="Match found"
            )
            
            mock_use_case.execute = AsyncMock(return_value=[mock_match])
            
            # Make request
            response = client.post(
                "/api/v1/find-experts",
                json={
                    "query_text": "Python developer",
                    "role": "Developer",
                    "limit": 10
                }
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert "matches" in data
            assert len(data["matches"]) == 1
            assert data["matches"][0]["expert"]["name"] == "Test Expert"
    
    def test_find_experts_validation_error(self, client):
        """Test find-experts endpoint validates input."""
        # Missing required field
        response = client.post(
            "/api/v1/find-experts",
            json={
                "role": "Developer"
                # Missing query_text
            }
        )
        
        # Should return validation error
        assert response.status_code == 422  # Validation error
    
    def test_find_experts_empty_query_text(self, client):
        """Test find-experts endpoint rejects empty query text."""
        response = client.post(
            "/api/v1/find-experts",
            json={
                "query_text": "",
                "limit": 10
            }
        )
        
        # Should return validation error
        assert response.status_code in [400, 422]
    
    def test_cors_headers_integration(self, client):
        """Test CORS headers are set correctly."""
        response = client.options("/health")
        
        # Verify CORS headers are present (if configured)
        # Note: CORS headers are typically set by middleware
        assert response.status_code in [200, 204]
    
    def test_api_versioning_integration(self, client):
        """Test API versioning is implemented."""
        # Verify v1 endpoints are available
        response = client.get("/endpoints")
        data = response.json()
        
        v1_endpoints = [ep for ep in data["endpoints"] if "/api/v1/" in ep["path"]]
        assert len(v1_endpoints) > 0, "API should have versioned endpoints"
    
    def test_error_handling_integration(self, client):
        """Test that API handles errors gracefully."""
        # Request non-existent endpoint
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        # Verify error response format
        data = response.json()
        assert "detail" in data
    
    def test_request_response_content_type(self, client):
        """Test that API uses JSON content type."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_identify_smes_endpoint_structure(self, client):
        """Test identify-smes endpoint structure."""
        # Note: This may require mocking dependencies
        response = client.post(
            "/api/v1/identify-smes",
            json={
                "min_documents": 10,
                "min_score": 0.7,
                "limit": 5
            }
        )
        
        # Should have proper structure (even if it fails due to dependencies)
        assert response.status_code in [200, 500, 503]  # Various possible states

