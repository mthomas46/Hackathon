"""Unit tests for domain entities."""

import pytest
from datetime import datetime, timezone

import sys
from pathlib import Path

# Add project root to path - navigate up from test file location
# tests/unit/test_domain_entities.py -> discovery-agent -> services -> project root
current_dir = Path(__file__).parent  # tests/unit
tests_dir = current_dir.parent       # tests
service_dir = tests_dir.parent       # discovery-agent
services_dir = service_dir.parent    # services
project_root = services_dir.parent   # project root

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(services_dir))

from services.discovery_agent.domain.entities import Service, Endpoint, DiscoveryResult


class TestEndpoint:
    """Test Endpoint entity."""

    def test_endpoint_creation(self):
        """Test creating an endpoint."""
        endpoint = Endpoint(
            path="/api/users",
            method="GET",
            summary="Get users",
            description="Retrieve a list of users"
        )

        assert endpoint.path == "/api/users"
        assert endpoint.method == "GET"
        assert endpoint.summary == "Get users"
        assert endpoint.description == "Retrieve a list of users"
        assert endpoint.operation_id == "GET_/api/users"
        assert endpoint.tags == []

    def test_endpoint_with_parameters(self):
        """Test endpoint with parameters."""
        endpoint = Endpoint(
            path="/api/users/{user_id}",
            method="GET",
            parameters=[
                {
                    "name": "user_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ]
        )

        assert endpoint.path == "/api/users/{user_id}"
        assert len(endpoint.parameters) == 1
        assert endpoint.parameters[0]["name"] == "user_id"

    def test_endpoint_to_dict(self):
        """Test endpoint serialization."""
        endpoint = Endpoint(
            id="test-id",
            path="/api/test",
            method="POST",
            summary="Test endpoint"
        )

        data = endpoint.to_dict()
        assert data["id"] == "test-id"
        assert data["path"] == "/api/test"
        assert data["method"] == "POST"
        assert data["summary"] == "Test endpoint"

    def test_endpoint_from_dict(self):
        """Test endpoint deserialization."""
        data = {
            "id": "test-id",
            "path": "/api/test",
            "method": "POST",
            "summary": "Test endpoint",
            "parameters": [],
            "responses": {},
            "tags": ["test"]
        }

        endpoint = Endpoint.from_dict(data)
        assert endpoint.id == "test-id"
        assert endpoint.path == "/api/test"
        assert endpoint.method == "POST"
        assert endpoint.summary == "Test endpoint"
        assert endpoint.tags == ["test"]


class TestService:
    """Test Service entity."""

    def test_service_creation(self):
        """Test creating a service."""
        service = Service(
            name="test-service",
            base_url="https://api.example.com"
        )

        assert service.name == "test-service"
        assert service.base_url == "https://api.example.com"
        assert service.status == "discovered"
        assert service.endpoints == []
        assert service.endpoint_count == 0
        assert service.health_url == "https://api.example.com/health"

    def test_service_with_endpoints(self):
        """Test service with endpoints."""
        service = Service(
            name="api-service",
            base_url="https://api.example.com"
        )

        endpoint1 = Endpoint(path="/users", method="GET")
        endpoint2 = Endpoint(path="/users", method="POST")

        service.add_endpoint(endpoint1)
        service.add_endpoint(endpoint2)

        assert service.endpoint_count == 2
        assert len(service.endpoints) == 2
        assert endpoint1.service_id == service.id
        assert endpoint2.service_id == service.id

    def test_service_remove_endpoint(self):
        """Test removing endpoints from service."""
        service = Service(
            name="api-service",
            base_url="https://api.example.com"
        )

        endpoint = Endpoint(path="/users", method="GET")
        service.add_endpoint(endpoint)

        assert service.endpoint_count == 1

        # Remove endpoint
        removed = service.remove_endpoint(endpoint.id)
        assert removed is True
        assert service.endpoint_count == 0

        # Try to remove non-existent endpoint
        removed = service.remove_endpoint("non-existent")
        assert removed is False

    def test_service_to_dict(self):
        """Test service serialization."""
        service = Service(
            id="service-id",
            name="test-service",
            base_url="https://api.example.com",
            version="1.0.0",
            description="Test API"
        )

        data = service.to_dict()
        assert data["id"] == "service-id"
        assert data["name"] == "test-service"
        assert data["base_url"] == "https://api.example.com"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Test API"
        assert data["endpoint_count"] == 0


class TestDiscoveryResult:
    """Test DiscoveryResult."""

    def test_successful_discovery_result(self):
        """Test successful discovery result."""
        service = Service(
            name="test-service",
            base_url="https://api.example.com"
        )

        endpoint = Endpoint(path="/users", method="GET")
        service.add_endpoint(endpoint)

        result = DiscoveryResult(service=service, success=True)

        assert result.success is True
        assert result.endpoint_count == 1
        assert result.error_message is None

    def test_failed_discovery_result(self):
        """Test failed discovery result."""
        service = Service(
            name="failed-service",
            base_url="https://api.example.com",
            status="error"
        )

        result = DiscoveryResult(
            service=service,
            success=False,
            error_message="Connection timeout"
        )

        assert result.success is False
        assert result.endpoint_count == 0
        assert result.error_message == "Connection timeout"

    def test_discovery_result_to_dict(self):
        """Test discovery result serialization."""
        service = Service(
            name="test-service",
            base_url="https://api.example.com"
        )

        result = DiscoveryResult(
            service=service,
            success=True
        )

        data = result.to_dict()
        assert data["success"] is True
        assert data["endpoint_count"] == 0
        assert "service" in data
        assert "discovered_at" in data
