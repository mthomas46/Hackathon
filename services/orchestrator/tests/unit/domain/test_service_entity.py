"""Unit tests for Service entity in orchestrator domain."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from services.orchestrator.domain.service_registry.entities.service import Service
from services.orchestrator.domain.service_registry.value_objects.service_id import ServiceId
from services.orchestrator.domain.service_registry.value_objects.service_capability import ServiceCapability
from services.orchestrator.domain.service_registry.value_objects.service_endpoint import ServiceEndpoint


class TestServiceEntity:
    """Test Service entity functionality."""

    def test_service_creation_valid(self):
        """Test creating a service with valid data."""
        service_id = ServiceId("test-service-123")
        service = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing"
        )

        assert service.service_id == service_id
        assert service.name == "Test Service"
        assert service.description == "A test service"
        assert service.category == "testing"
        assert service.status == "unknown"
        assert len(service.capabilities) == 0
        assert len(service.endpoints) == 0
        assert service.metadata == {}

    def test_service_creation_with_optional_fields(self):
        """Test creating a service with optional fields."""
        service_id = ServiceId("test-service-456")
        metadata = {"version": "1.0.0", "owner": "team-a"}

        service = Service(
            service_id=service_id,
            name="Advanced Service",
            description="An advanced test service",
            category="advanced",
            base_url="https://api.example.com",
            openapi_url="https://api.example.com/openapi.json",
            metadata=metadata
        )

        assert service.base_url == "https://api.example.com"
        assert service.openapi_url == "https://api.example.com/openapi.json"
        assert service.metadata == metadata

    def test_service_creation_invalid_name(self):
        """Test creating a service with invalid name."""
        service_id = ServiceId("test-service")

        with pytest.raises(ValueError, match="Service name cannot be empty"):
            Service(
                service_id=service_id,
                name="",  # Invalid empty name
                description="A test service",
                category="testing"
            )

    def test_service_creation_invalid_description(self):
        """Test creating a service with invalid description."""
        service_id = ServiceId("test-service")

        with pytest.raises(ValueError, match="Service description cannot be empty"):
            Service(
                service_id=service_id,
                name="Test Service",
                description="",  # Invalid empty description
                category="testing"
            )

    def test_service_creation_invalid_category(self):
        """Test creating a service with invalid category."""
        service_id = ServiceId("test-service")

        with pytest.raises(ValueError, match="Service category cannot be empty"):
            Service(
                service_id=service_id,
                name="Test Service",
                description="A test service",
                category=""  # Invalid empty category
            )

    def test_service_strip_whitespace(self):
        """Test that service strips whitespace from string fields."""
        service_id = ServiceId("test-service")

        service = Service(
            service_id=service_id,
            name="  Test Service  ",
            description="  A test service  ",
            category="  testing  ",
            base_url="  https://api.example.com  ",
            openapi_url="  https://api.example.com/openapi.json  "
        )

        assert service.name == "Test Service"
        assert service.description == "A test service"
        assert service.category == "testing"
        assert service.base_url == "https://api.example.com"
        assert service.openapi_url == "https://api.example.com/openapi.json"

    def test_service_add_capability(self):
        """Test adding capabilities to a service."""
        service_id = ServiceId("test-service")
        service = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing"
        )

        capability = ServiceCapability(
            name="document_processing",
            description="Can process documents"
        )

        service.add_capability(capability)

        assert len(service.capabilities) == 1
        assert service.capabilities[0] == capability

    def test_service_add_endpoint(self):
        """Test adding endpoints to a service."""
        service_id = ServiceId("test-service")
        service = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing"
        )

        endpoint = ServiceEndpoint(
            path="/api/v1/process",
            method="POST",
            description="Process endpoint"
        )

        service.add_endpoint(endpoint)

        assert len(service.endpoints) == 1
        assert service.endpoints[0] == endpoint

    def test_service_update_status(self):
        """Test updating service status."""
        service_id = ServiceId("test-service")
        service = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing"
        )

        assert service.status == "unknown"

        service.update_status("healthy")
        assert service.status == "healthy"

        service.update_status("unhealthy")
        assert service.status == "unhealthy"

    def test_service_last_seen_update(self):
        """Test that last_seen is updated when status changes."""
        service_id = ServiceId("test-service")
        service = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing"
        )

        initial_last_seen = service.last_seen

        # Simulate some time passing
        import time
        time.sleep(0.001)

        service.update_status("healthy")

        # last_seen should be updated
        assert service.last_seen > initial_last_seen

    def test_service_to_dict(self):
        """Test serializing service to dictionary."""
        service_id = ServiceId("test-service-123")
        registered_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        last_seen = datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc)

        service = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing",
            base_url="https://api.example.com",
            metadata={"version": "1.0.0"}
        )

        # Manually set timestamps for testing
        service._registered_at = registered_at
        service._last_seen = last_seen

        data = service.to_dict()

        assert data["service_id"] == "test-service-123"
        assert data["name"] == "Test Service"
        assert data["description"] == "A test service"
        assert data["category"] == "testing"
        assert data["base_url"] == "https://api.example.com"
        assert data["status"] == "unknown"
        assert data["metadata"] == {"version": "1.0.0"}
        assert data["capabilities"] == []
        assert data["endpoints"] == []
        assert data["registered_at"] == registered_at.isoformat()
        assert data["last_seen"] == last_seen.isoformat()

    def test_service_from_dict(self):
        """Test deserializing service from dictionary."""
        data = {
            "service_id": "test-service-456",
            "name": "Restored Service",
            "description": "A restored test service",
            "category": "restored",
            "base_url": "https://restored.example.com",
            "status": "healthy",
            "metadata": {"version": "2.0.0"},
            "capabilities": [],
            "endpoints": [],
            "registered_at": "2024-01-01T12:00:00+00:00",
            "last_seen": "2024-01-01T12:30:00+00:00"
        }

        service = Service.from_dict(data)

        assert service.service_id.value == "test-service-456"
        assert service.name == "Restored Service"
        assert service.description == "A restored test service"
        assert service.category == "restored"
        assert service.base_url == "https://restored.example.com"
        assert service.status == "healthy"
        assert service.metadata == {"version": "2.0.0"}

    def test_service_equality(self):
        """Test service equality based on service_id."""
        service_id1 = ServiceId("same-id")
        service_id2 = ServiceId("same-id")
        service_id3 = ServiceId("different-id")

        service1 = Service(
            service_id=service_id1,
            name="Service 1",
            description="Description 1",
            category="cat1"
        )

        service2 = Service(
            service_id=service_id2,
            name="Service 2",  # Different name
            description="Description 2",  # Different description
            category="cat2"  # Different category
        )

        service3 = Service(
            service_id=service_id3,
            name="Service 1",  # Same name as service1
            description="Description 1",  # Same description as service1
            category="cat1"  # Same category as service1
        )

        # Services with same ID should be equal
        assert service1 == service2

        # Services with different IDs should not be equal
        assert service1 != service3
        assert service2 != service3

    def test_service_string_representation(self):
        """Test service string representation."""
        service_id = ServiceId("test-service")
        service = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing"
        )

        str_repr = str(service)
        assert "test-service" in str_repr
        assert "Test Service" in str_repr
        assert "testing" in str_repr
