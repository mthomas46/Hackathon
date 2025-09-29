"""API endpoint tests for mock-data-generator service."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the FastAPI app
from ..main import app

# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint(self):
        """Test basic health check."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data

    def test_health_endpoint_content(self):
        """Test health endpoint returns proper content."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "mock-data-generator"
        assert "timestamp" in data
        assert "version" in data


class TestGenerationEndpoint:
    """Test mock data generation endpoints."""

    @patch('httpx.AsyncClient')
    def test_generate_confluence_page(self, mock_client):
        """Test generating a Confluence page."""
        # Mock LLM Gateway response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "This is a mock Confluence page content about API documentation."
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        request_data = {
            "data_type": "confluence_page",
            "count": 1,
            "parameters": {
                "title": "API Documentation",
                "space": "DEV"
            }
        }

        response = client.post("/api/v1/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["count"] == 1
        assert data["data_type"] == "confluence_page"
        assert "title" in data["data"][0]
        assert "content" in data["data"][0]

    @patch('httpx.AsyncClient')
    def test_generate_github_repo(self, mock_client):
        """Test generating a GitHub repository."""
        # Mock LLM Gateway response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "This is a mock GitHub repository README."
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        request_data = {
            "data_type": "github_repo",
            "count": 1,
            "parameters": {
                "name": "test-repo",
                "owner": "testuser"
            }
        }

        response = client.post("/api/v1/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data_type"] == "github_repo"

    def test_generate_invalid_data_type(self):
        """Test generating with invalid data type."""
        request_data = {
            "data_type": "invalid_type",
            "count": 1
        }

        response = client.post("/api/v1/generate", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_generate_count_too_high(self):
        """Test generating with count exceeding limit."""
        request_data = {
            "data_type": "confluence_page",
            "count": 150  # Over limit of 100
        }

        response = client.post("/api/v1/generate", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_generate_zero_count(self):
        """Test generating with zero count."""
        request_data = {
            "data_type": "confluence_page",
            "count": 0
        }

        response = client.post("/api/v1/generate", json=request_data)

        assert response.status_code == 422  # Validation error


class TestBulkGenerationEndpoint:
    """Test bulk collection generation endpoints."""

    @patch('httpx.AsyncClient')
    def test_bulk_generation(self, mock_client):
        """Test bulk collection generation."""
        # Mock LLM Gateway response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "Mock bulk collection content."
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        request_data = {
            "name": "test_collection",
            "data_types": ["confluence_page", "github_repo"],
            "total_items": 3
        }

        response = client.post("/api/v1/bulk/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "collection_id" in data
        assert data["name"] == "test_collection"
        assert data["total_items"] == 3
        assert "status" in data

    def test_bulk_generation_invalid_data_types(self):
        """Test bulk generation with invalid data types."""
        request_data = {
            "name": "test_collection",
            "data_types": ["invalid_type"],
            "total_items": 5
        }

        response = client.post("/api/v1/bulk/generate", json=request_data)

        assert response.status_code == 400


class TestEcosystemScenarioEndpoint:
    """Test ecosystem scenario generation endpoints."""

    @patch('httpx.AsyncClient')
    def test_ecosystem_scenario_generation(self, mock_client):
        """Test ecosystem scenario generation."""
        # Mock LLM Gateway response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "Mock ecosystem scenario content."
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        request_data = {
            "scenario_type": "development_environment",
            "scale": "small",
            "include_services": ["llm-gateway", "doc-store"]
        }

        response = client.post("/api/v1/scenario/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "scenario_id" in data
        assert data["scenario_type"] == "development_environment"
        assert data["scale"] == "small"
        assert "total_items" in data

    def test_ecosystem_scenario_invalid_scale(self):
        """Test ecosystem scenario with invalid scale."""
        request_data = {
            "scenario_type": "development_environment",
            "scale": "invalid_scale"
        }

        response = client.post("/api/v1/scenario/generate", json=request_data)

        assert response.status_code == 400


class TestConfigurationEndpoint:
    """Test configuration management endpoints."""

    def test_get_configuration(self):
        """Test getting current configuration."""
        response = client.get("/api/v1/config")

        assert response.status_code == 200
        data = response.json()

        assert "llm_gateway_url" in data
        assert "doc_store_url" in data
        assert "supported_data_types" in data

    def test_update_configuration(self):
        """Test updating configuration."""
        config_data = {
            "llm_gateway_url": "http://test-gateway:5055",
            "doc_store_url": "http://test-store:5010"
        }

        response = client.put("/api/v1/config", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestStatisticsEndpoint:
    """Test statistics and metrics endpoints."""

    def test_get_statistics(self):
        """Test getting generation statistics."""
        response = client.get("/api/v1/stats")

        assert response.status_code == 200
        data = response.json()

        assert "total_generations" in data
        assert "data_types_generated" in data
        assert "average_generation_time" in data

    def test_get_statistics_by_type(self):
        """Test getting statistics filtered by data type."""
        response = client.get("/api/v1/stats?data_type=confluence_page")

        assert response.status_code == 200
        data = response.json()

        # Should contain statistics specific to confluence_page
        assert isinstance(data, dict)


class TestErrorHandling:
    """Test error handling across endpoints."""

    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/v1/generate",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        request_data = {}  # Missing data_type

        response = client.post("/api/v1/generate", json=request_data)

        assert response.status_code == 422  # Validation error

    @patch('httpx.AsyncClient')
    def test_llm_gateway_unavailable(self, mock_client):
        """Test handling when LLM Gateway is unavailable."""
        # Mock connection error
        mock_client.return_value.__aenter__.side_effect = Exception("Connection failed")

        request_data = {
            "data_type": "confluence_page",
            "count": 1
        }

        response = client.post("/api/v1/generate", json=request_data)

        assert response.status_code == 503  # Service unavailable

    @patch('httpx.AsyncClient')
    def test_llm_gateway_timeout(self, mock_client):
        """Test handling of LLM Gateway timeout."""
        # Mock timeout
        from httpx import TimeoutException
        mock_client.return_value.__aenter__.side_effect = TimeoutException("Request timeout")

        request_data = {
            "data_type": "confluence_page",
            "count": 1
        }

        response = client.post("/api/v1/generate", json=request_data)

        assert response.status_code == 504  # Gateway timeout
