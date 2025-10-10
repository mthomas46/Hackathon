"""
Unit tests for presentation layer routes.

Tests standard and expert routes using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from main import app


class TestStandardRoutes:
    """Tests for standard API routes."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "expert-finder-service"
        assert data["version"] == "1.0.0"
    
    def test_about_me_endpoint(self, client):
        """Test about-me endpoint."""
        response = client.get("/about-me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "expert-finder-service"
        assert "capabilities" in data
        assert "ecosystem_role" in data
        assert "architecture" in data
        assert "scoring_algorithm" in data
    
    def test_endpoints_list(self, client):
        """Test endpoints listing."""
        response = client.get("/endpoints")
        
        assert response.status_code == 200
        data = response.json()
        assert "standard_endpoints" in data
        assert "business_endpoints" in data
        assert len(data["standard_endpoints"]) >= 5
        assert len(data["business_endpoints"]) >= 2
    
    def test_provider_consumer(self, client):
        """Test provider-consumer endpoint."""
        response = client.get("/provider-consumer")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service_name"] == "expert-finder-service"
        assert "relationships" in data
        assert "dependency_summary" in data
        
        # Should have user-store as required dependency
        relationships = data["relationships"]
        user_store = next((r for r in relationships if r["service"] == "user-store"), None)
        assert user_store is not None
        assert user_store["criticality"] == "required"
    
    def test_openapi_json(self, client):
        """Test OpenAPI specification endpoint."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert data["openapi"] == "3.1.0"
        assert data["info"]["title"] == "Expert Finder Service"
        assert data["info"]["version"] == "1.0.0"
        assert "paths" in data
        assert "components" in data


class TestExpertRoutes:
    """Tests for expert finding routes."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_use_case(self):
        """Create a mock use case."""
        use_case = AsyncMock()
        use_case.execute = AsyncMock(return_value=[])
        return use_case
    
    @patch("presentation.routes.expert_routes.get_find_experts_use_case")
    def test_find_experts_endpoint_exists(self, mock_get_use_case, client, mock_use_case):
        """Test that find-experts endpoint exists."""
        mock_get_use_case.return_value = mock_use_case
        
        response = client.post(
            "/api/v1/find-experts",
            json={
                "query_text": "Python developer",
                "limit": 10
            }
        )
        
        # Should not be 404
        assert response.status_code != 404
    
    @patch("presentation.routes.expert_routes.get_find_experts_use_case")
    def test_find_experts_validates_request(self, mock_get_use_case, client, mock_use_case):
        """Test that find-experts validates request body."""
        mock_get_use_case.return_value = mock_use_case
        
        # Missing required field
        response = client.post(
            "/api/v1/find-experts",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch("presentation.routes.expert_routes.get_find_experts_use_case")
    def test_find_experts_validates_limit(self, mock_get_use_case, client, mock_use_case):
        """Test that find-experts validates limit parameter."""
        mock_get_use_case.return_value = mock_use_case
        
        # Limit too high
        response = client.post(
            "/api/v1/find-experts",
            json={
                "query_text": "test",
                "limit": 10000  # Exceeds MAX_RESULTS
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch("presentation.routes.expert_routes.get_find_experts_use_case")
    def test_find_experts_returns_structured_response(
        self, mock_get_use_case, client, mock_use_case
    ):
        """Test that find-experts returns properly structured response."""
        from domain.entities.expert import Expert
        from domain.value_objects.expert_match import ExpertMatch
        
        # Mock successful response
        mock_matches = [
            ExpertMatch(
                expert=Expert(
                    user_id="1",
                    name="Alice",
                    role="Backend Developer",
                    topics=["Python"],
                    document_count=10
                ),
                overall_score=0.85,
                role_score=0.9,
                topic_score=0.8,
                service_score=0.7,
                document_score=0.8
            )
        ]
        mock_use_case.execute.return_value = mock_matches
        mock_get_use_case.return_value = mock_use_case
        
        response = client.post(
            "/api/v1/find-experts",
            json={
                "query_text": "Python developer",
                "limit": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "total_matches" in data
        assert "matches" in data
        assert data["total_matches"] == 1
        assert len(data["matches"]) == 1
        
        match = data["matches"][0]
        assert match["user_id"] == "1"
        assert match["name"] == "Alice"
        assert match["overall_score"] == 0.85
    
    @patch("presentation.routes.expert_routes.get_find_experts_use_case")
    def test_identify_smes_endpoint_exists(self, mock_get_use_case, client, mock_use_case):
        """Test that identify-smes endpoint exists."""
        mock_get_use_case.return_value = mock_use_case
        
        response = client.post(
            "/api/v1/identify-smes",
            json={
                "query_text": "FastAPI expert",
                "limit": 5
            }
        )
        
        # Should not be 404
        assert response.status_code != 404
    
    @patch("presentation.routes.expert_routes.get_find_experts_use_case")
    def test_identify_smes_validates_min_documents(
        self, mock_get_use_case, client, mock_use_case
    ):
        """Test that identify-smes validates min_documents parameter."""
        mock_get_use_case.return_value = mock_use_case
        
        response = client.post(
            "/api/v1/identify-smes",
            json={
                "query_text": "test",
                "min_documents": -1  # Invalid
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch("presentation.routes.expert_routes.get_find_experts_use_case")
    def test_identify_smes_default_parameters(
        self, mock_get_use_case, client, mock_use_case
    ):
        """Test that identify-smes uses sensible defaults."""
        mock_use_case.execute.return_value = []
        mock_get_use_case.return_value = mock_use_case
        
        response = client.post(
            "/api/v1/identify-smes",
            json={
                "query_text": "Python expert"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert isinstance(data["matches"], list)

