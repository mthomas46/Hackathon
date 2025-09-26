"""Simple tests to improve test coverage for discovery-agent."""

import pytest
from domain import Endpoint


class TestEndpointCoverage:
    """Basic tests for Endpoint entity to improve coverage."""

    def test_endpoint_basic_creation(self):
        """Test basic endpoint creation."""
        endpoint = Endpoint(
            path="/api/test",
            method="GET",
            summary="Test endpoint"
        )
        assert endpoint.path == "/api/test"
        assert endpoint.method == "GET"
        assert endpoint.summary == "Test endpoint"

    def test_endpoint_operation_id(self):
        """Test operation ID generation."""
        endpoint = Endpoint(
            path="/api/users/{id}",
            method="GET"
        )
        assert endpoint.operation_id == "GET_api_users__id_"

    def test_endpoint_with_parameters(self):
        """Test endpoint with parameters."""
        endpoint = Endpoint(
            path="/api/users",
            method="POST",
            parameters=[{"name": "user", "in": "body"}],
            responses={"200": {"description": "Success"}}
        )
        assert len(endpoint.parameters) == 1
        assert "200" in endpoint.responses

    def test_endpoint_with_tags(self):
        """Test endpoint with tags."""
        endpoint = Endpoint(
            path="/api/admin",
            method="DELETE",
            tags=["admin", "dangerous"]
        )
        assert "admin" in endpoint.tags
        assert "dangerous" in endpoint.tags
