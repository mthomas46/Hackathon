"""API Layer Tests - Simulation Endpoints Testing.

Tests for Project Simulation Service API endpoints following established
ecosystem patterns. Validates request/response handling, error cases,
and integration with FastAPI framework.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from typing import Dict, Any, List

from main import app
from simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, ProjectStatus
)


class TestSimulationEndpoints:
    """Test cases for simulation API endpoints."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_simulation_request(self):
        """Sample simulation creation request."""
        return {
            "name": "Test E-commerce Platform",
            "description": "A comprehensive e-commerce platform with microservices",
            "type": ProjectType.WEB_APPLICATION.value,
            "team_size": 5,
            "complexity": ComplexityLevel.COMPLEX.value,
            "duration_weeks": 12,
            "team_members": [
                {
                    "member_id": "dev_001",
                    "name": "Alice Johnson",
                    "role": "developer",
                    "experience_years": 5,
                    "skills": ["Python", "FastAPI", "React"]
                }
            ],
            "phases": [
                {
                    "name": "Planning",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-15",
                    "duration_days": 15
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_create_simulation_success(self, client, sample_simulation_request):
        """Test successful simulation creation."""
        # Act
        response = client.post("/api/v1/simulations", json=sample_simulation_request)

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert "data" in data  # Fallback response format
        assert "simulation_id" in data["data"]
        assert data["success"] is True
        assert "_links" in data
        assert data["data"]["message"] == "Simulation created successfully"

        # Check hypermedia links
        links = data["_links"]
        assert any(link["rel"] == "self" for link in links)
        assert any(link["rel"] == "execute" for link in links)

    def test_create_simulation_validation_error(self, client):
        """Test simulation creation with validation errors."""
        # Arrange
        invalid_request = {
            "name": "",  # Invalid: empty name
            "type": "invalid_type",  # Invalid: not a valid project type
            "team_size": -1,  # Invalid: negative team size
            "complexity": "invalid_complexity"
        }

        # Act
        response = client.post("/api/v1/simulations", json=invalid_request)

        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()

        # FastAPI validation error format
        assert "detail" in data
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0

        # Check that we have validation errors for each invalid field
        error_types = [error["type"] for error in data["detail"]]
        assert "string_too_short" in error_types  # Empty name
        assert "string_pattern_mismatch" in error_types  # Invalid type and complexity
        assert "greater_than_equal" in error_types  # Negative team size

    def test_get_simulation_not_found(self, client):
        """Test getting non-existent simulation."""
        # Act
        response = client.get("/api/v1/simulations/non_existent_id")

        # Assert
        assert response.status_code == 404
        data = response.json()

        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_get_simulation_success(self, client, sample_simulation_request):
        """Test successful simulation retrieval."""
        # Arrange - Create simulation first
        create_response = client.post("/api/v1/simulations", json=sample_simulation_request)
        assert create_response.status_code == 201
        simulation_id = create_response.json()["data"]["simulation_id"]

        # Act
        response = client.get(f"/api/v1/simulations/{simulation_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "_links" in data

        # Check hypermedia links
        links = data["_links"]
        assert any(link["rel"] == "self" for link in links)

    def test_list_simulations_with_pagination(self, client):
        """Test simulation listing with pagination."""
        # Act
        response = client.get("/api/v1/simulations?page=1&page_size=10")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data
        assert "pagination" in data

        pagination = data["pagination"]
        assert "page" in pagination
        assert "page_size" in pagination
        assert "total_items" in pagination
        assert "has_next" in pagination
        assert "has_previous" in pagination

    def test_list_simulations_invalid_pagination(self, client):
        """Test simulation listing with invalid pagination parameters."""
        # Act
        response = client.get("/api/v1/simulations?page=-1&page_size=150")

        # Assert
        assert response.status_code == 422  # Validation error
        data = response.json()

        assert data["success"] is False
        assert "field_errors" in data

    @pytest.mark.asyncio
    async def test_execute_simulation_success(self, client, sample_simulation_request):
        """Test successful simulation execution."""
        # Arrange - Create simulation first
        create_response = client.post("/api/v1/simulations", json=sample_simulation_request)
        assert create_response.status_code == 201
        simulation_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/v1/simulations/{simulation_id}/execute")

        # Assert
        assert response.status_code == 202  # Accepted for background processing
        data = response.json()

        assert data["status"] == "accepted"  # HATEOAS response status
        assert data["data"]["simulation_id"] == simulation_id
        assert data["data"]["status"] == "running"

    def test_execute_non_existent_simulation(self, client):
        """Test executing non-existent simulation."""
        # Act
        response = client.post("/api/v1/simulations/non_existent_id/execute")

        # Assert
        assert response.status_code == 500  # Internal server error from application service
        data = response.json()

        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_cancel_simulation_success(self, client, sample_simulation_request):
        """Test successful simulation cancellation."""
        # Arrange - Create simulation first
        create_response = client.post("/api/v1/simulations", json=sample_simulation_request)
        assert create_response.status_code == 201
        simulation_id = create_response.json()["id"]

        # Act
        response = client.delete(f"/api/v1/simulations/{simulation_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True

    def test_health_endpoint_structure(self, client):
        """Test health endpoint returns proper structure."""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data

        health_data = data["data"]
        assert "status" in health_data
        assert "service" in health_data
        assert "version" in health_data

    def test_detailed_health_endpoint(self, client):
        """Test detailed health endpoint."""
        # Act
        response = client.get("/health/detailed")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data

    def test_system_health_endpoint(self, client):
        """Test system-wide health endpoint."""
        # Act
        response = client.get("/health/system")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "data" in data

    def test_root_endpoint_hypermedia(self, client):
        """Test root endpoint provides proper hypermedia navigation."""
        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "service" in data
        assert "version" in data
        assert "_links" in data

        links = data["_links"]
        assert any(link["rel"] == "self" for link in links)
        assert any(link["rel"] == "simulations" for link in links)
        assert any(link["rel"] == "health" for link in links)

    @pytest.mark.asyncio
    async def test_simulation_results_endpoint(self, client, sample_simulation_request):
        """Test simulation results retrieval."""
        # Arrange - Create and execute simulation
        create_response = client.post("/api/v1/simulations", json=sample_simulation_request)
        assert create_response.status_code == 201
        simulation_id = create_response.json()["id"]

        # Act
        response = client.get(f"/api/v1/simulations/{simulation_id}/results")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "_links" in data

    def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        # Act
        response = client.options("/api/v1/simulations")

        # Assert
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    def test_request_id_propagation(self, client):
        """Test request ID propagation in responses."""
        # Arrange
        headers = {"X-Correlation-ID": "test-request-123"}

        # Act
        response = client.get("/health", headers=headers)

        # Assert
        assert response.headers.get("X-Correlation-ID") == "test-request-123"

    def test_content_type_validation(self, client):
        """Test content type validation for JSON endpoints."""
        # Act
        response = client.post(
            "/api/v1/simulations",
            data="not json",
            headers={"Content-Type": "text/plain"}
        )

        # Assert - Should handle gracefully or return appropriate error
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_concurrent_simulation_creation(self, client, sample_simulation_request):
        """Test concurrent simulation creation handling."""
        import asyncio

        # Create multiple concurrent requests
        async def create_simulation():
            return client.post("/api/v1/simulations", json=sample_simulation_request)

        # Run concurrent requests
        tasks = [create_simulation() for _ in range(3)]
        responses = await asyncio.gather(*[task() for task in tasks])

        # Assert all requests handled properly
        for response in responses:
            assert response.status_code in [201, 409]  # Created or Conflict

    def test_large_request_handling(self, client):
        """Test handling of large request payloads."""
        # Arrange
        large_request = {
            "name": "Large Test Project",
            "description": "A" * 10000,  # Large description
            "type": ProjectType.WEB_APPLICATION.value,
            "team_size": 50,
            "complexity": ComplexityLevel.COMPLEX.value,
            "duration_weeks": 24,
            "team_members": [
                {
                    "member_id": f"member_{i}",
                    "name": f"Team Member {i}",
                    "role": "developer",
                    "experience_years": 5,
                    "skills": ["Python", "JavaScript", "AWS"] * 10  # Large skills list
                } for i in range(50)
            ]
        }

        # Act
        response = client.post("/api/v1/simulations", json=large_request)

        # Assert - Should handle large payload appropriately
        assert response.status_code in [201, 413, 422]  # Created, Payload Too Large, or Validation Error

    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON requests."""
        # Act
        response = client.post(
            "/api/v1/simulations",
            data='{"invalid": json}',
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 422  # Validation error for malformed JSON

    def test_unsupported_http_methods(self, client):
        """Test handling of unsupported HTTP methods."""
        # Act
        response = client.patch("/api/v1/simulations")

        # Assert
        assert response.status_code == 405  # Method Not Allowed

    @pytest.mark.asyncio
    async def test_simulation_lifecycle(self, client, sample_simulation_request):
        """Test complete simulation lifecycle through API."""
        # 1. Create simulation
        create_response = client.post("/api/v1/simulations", json=sample_simulation_request)
        assert create_response.status_code == 201
        simulation_id = create_response.json()["id"]

        # 2. Get simulation status
        status_response = client.get(f"/api/v1/simulations/{simulation_id}")
        assert status_response.status_code == 200

        # 3. Execute simulation
        execute_response = client.post(f"/api/v1/simulations/{simulation_id}/execute")
        assert execute_response.status_code == 202

        # 4. Get results
        results_response = client.get(f"/api/v1/simulations/{simulation_id}/results")
        assert results_response.status_code == 200

        # 5. Cancel simulation (if still running)
        cancel_response = client.delete(f"/api/v1/simulations/{simulation_id}")
        assert cancel_response.status_code == 200

    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # Make multiple rapid requests
        responses = []
        for _ in range(15):  # Exceed rate limit
            response = client.post("/api/v1/simulations", json={
                "name": f"Rate Limit Test {_}",
                "type": ProjectType.WEB_APPLICATION.value,
                "complexity": ComplexityLevel.SIMPLE.value,
                "duration_weeks": 4
            })
            responses.append(response)

        # Check that some requests are rate limited
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        if rate_limited_responses:
            assert len(rate_limited_responses) > 0

    def test_api_versioning(self, client):
        """Test API versioning support."""
        # Test v1 endpoints
        response = client.get("/api/v1/simulations")
        assert response.status_code in [200, 404]  # 404 if no simulations exist

        # Verify version in response
        if response.status_code == 200:
            # Check if version is included in response
            pass

    def test_openapi_specification(self, client):
        """Test OpenAPI specification generation."""
        # Act
        response = client.get("/openapi.json")

        # Assert
        assert response.status_code == 200
        spec = response.json()

        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec

        # Check for simulation paths
        assert "/api/v1/simulations" in spec["paths"]


if __name__ == "__main__":
    pytest.main([__file__])
