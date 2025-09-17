#!/usr/bin/env python3
"""
Domain Layer Tests for Service Registry

Tests the core domain logic for service discovery and registration.
"""

import pytest
from datetime import datetime

from services.orchestrator.domain.service_registry.value_objects import (
    ServiceId, ServiceEndpoint, ServiceCapability
)
from services.orchestrator.domain.service_registry.entities import Service
from services.orchestrator.domain.service_registry.services import (
    ServiceDiscoveryService, ServiceRegistrationService
)


class TestServiceId:
    """Test ServiceId value object."""

    def test_create_valid_service_id(self):
        """Test creating a valid service ID."""
        service_id = ServiceId("orchestrator")
        assert service_id.value == "orchestrator"
        assert str(service_id) == "orchestrator"

    def test_create_empty_service_id_raises_error(self):
        """Test that empty service ID raises error."""
        with pytest.raises(ValueError):
            ServiceId("")

    def test_service_id_equality(self):
        """Test service ID equality."""
        id1 = ServiceId("test")
        id2 = ServiceId("test")
        id3 = ServiceId("other")

        assert id1 == id2
        assert id1 != id3


class TestServiceEndpoint:
    """Test ServiceEndpoint value object."""

    def test_create_valid_endpoint(self):
        """Test creating a valid service endpoint."""
        endpoint = ServiceEndpoint("GET", "/health", "Health check endpoint")
        assert endpoint.method == "GET"
        assert endpoint.path == "/health"
        assert endpoint.description == "Health check endpoint"
        assert endpoint.full_path == "GET /health"

    def test_invalid_method_raises_error(self):
        """Test that invalid HTTP method raises error."""
        with pytest.raises(ValueError):
            ServiceEndpoint("INVALID", "/test")

    def test_path_without_leading_slash_raises_error(self):
        """Test that path without leading slash raises error."""
        with pytest.raises(ValueError):
            ServiceEndpoint("GET", "health")

    def test_empty_path_raises_error(self):
        """Test that empty path raises error."""
        with pytest.raises(ValueError):
            ServiceEndpoint("GET", "")


class TestServiceCapability:
    """Test ServiceCapability value object."""

    def test_create_valid_capability(self):
        """Test creating a valid service capability."""
        capability = ServiceCapability("query_processing", "Natural language query processing")
        assert capability.name == "query_processing"
        assert capability.description == "Natural language query processing"

    def test_empty_capability_name_raises_error(self):
        """Test that empty capability name raises error."""
        with pytest.raises(ValueError):
            ServiceCapability("", "Description")

    def test_capability_with_spaces_raises_error(self):
        """Test that capability name with spaces raises error."""
        with pytest.raises(ValueError):
            ServiceCapability("query processing", "Description")


class TestService:
    """Test Service entity."""

    def test_create_valid_service(self):
        """Test creating a valid service."""
        service_id = ServiceId("orchestrator")
        service = Service(
            service_id=service_id,
            name="Orchestrator",
            description="Central control plane",
            category="orchestration"
        )

        assert service.service_id == service_id
        assert service.name == "Orchestrator"
        assert service.category == "orchestration"
        assert service.status == "unknown"
        assert len(service.capabilities) == 0
        assert len(service.endpoints) == 0

    def test_add_capability(self):
        """Test adding capability to service."""
        service = self._create_test_service()
        capability = ServiceCapability("health_monitoring")

        service.add_capability(capability)

        assert len(service.capabilities) == 1
        assert service.capabilities[0] == capability
        assert service.has_capability("health_monitoring")

    def test_add_duplicate_capability_ignored(self):
        """Test that adding duplicate capability is ignored."""
        service = self._create_test_service()
        capability = ServiceCapability("health_monitoring")

        service.add_capability(capability)
        service.add_capability(capability)  # Duplicate

        assert len(service.capabilities) == 1

    def test_add_endpoint(self):
        """Test adding endpoint to service."""
        service = self._create_test_service()
        endpoint = ServiceEndpoint("GET", "/health")

        service.add_endpoint(endpoint)

        assert len(service.endpoints) == 1
        assert service.endpoints[0] == endpoint

    def test_update_status(self):
        """Test updating service status."""
        service = self._create_test_service()

        service.update_status("healthy")

        assert service.status == "healthy"
        assert service.last_seen > service.registered_at

    def test_invalid_status_raises_error(self):
        """Test that invalid status raises error."""
        service = self._create_test_service()

        with pytest.raises(ValueError):
            service.update_status("invalid_status")

    def test_to_dict(self):
        """Test converting service to dictionary."""
        service = self._create_test_service()
        capability = ServiceCapability("health_monitoring")
        endpoint = ServiceEndpoint("GET", "/health")
        service.add_capability(capability)
        service.add_endpoint(endpoint)

        data = service.to_dict()

        assert data["service_id"] == "test_service"
        assert data["name"] == "Test Service"
        assert data["capabilities"] == ["health_monitoring"]
        assert data["endpoints"] == ["GET /health"]
        assert "registered_at" in data
        assert "last_seen" in data

    def _create_test_service(self) -> Service:
        """Helper method to create a test service."""
        service_id = ServiceId("test_service")
        return Service(
            service_id=service_id,
            name="Test Service",
            description="Test service description",
            category="test"
        )


class TestServiceDiscoveryService:
    """Test ServiceDiscoveryService domain service."""

    def setup_method(self):
        """Setup test fixtures."""
        self.service_definitions = {
            "orchestrator": {
                "name": "Orchestrator",
                "description": "Central control plane",
                "category": "orchestration",
                "capabilities": ["coordination", "health_monitoring"],
                "endpoints": ["GET /health - Health check"]
            }
        }
        self.discovery_service = ServiceDiscoveryService(self.service_definitions)

    def test_get_all_services(self):
        """Test getting all services."""
        services = self.discovery_service.get_all_services()

        assert len(services) == 1
        service = services[0]
        assert service.name == "Orchestrator"
        assert service.category == "orchestration"
        assert service.has_capability("coordination")
        assert service.has_capability("health_monitoring")

    def test_get_service_by_id(self):
        """Test getting service by ID."""
        service_id = ServiceId("orchestrator")
        service = self.discovery_service.get_service_by_id(service_id)

        assert service is not None
        assert service.service_id == service_id
        assert service.name == "Orchestrator"

    def test_get_nonexistent_service(self):
        """Test getting non-existent service."""
        service_id = ServiceId("nonexistent")
        service = self.discovery_service.get_service_by_id(service_id)

        assert service is None

    def test_find_services_by_category(self):
        """Test finding services by category."""
        services = self.discovery_service.find_services_by_category("orchestration")

        assert len(services) == 1
        assert services[0].category == "orchestration"

    def test_find_services_by_capability(self):
        """Test finding services by capability."""
        services = self.discovery_service.find_services_by_capability("health_monitoring")

        assert len(services) == 1
        assert services[0].has_capability("health_monitoring")

    def test_get_service_categories(self):
        """Test getting service categories."""
        categories = self.discovery_service.get_service_categories()

        assert "orchestration" in categories

    def test_get_service_capabilities_summary(self):
        """Test getting capabilities summary."""
        summary = self.discovery_service.get_service_capabilities_summary()

        assert "Orchestrator" in summary
        assert "coordination" in summary["Orchestrator"]
        assert "health_monitoring" in summary["Orchestrator"]


class TestServiceRegistrationService:
    """Test ServiceRegistrationService domain service."""

    def setup_method(self):
        """Setup test fixtures."""
        self.registration_service = ServiceRegistrationService()

    def test_register_new_service(self):
        """Test registering a new service."""
        service_id = ServiceId("test_service")
        service = self.registration_service.register_service(
            service_id=service_id,
            name="Test Service",
            description="Test service",
            category="test",
            base_url="http://localhost:8000",
            capabilities=["test_capability"],
            endpoints=["GET /test - Test endpoint"]
        )

        assert service.service_id == service_id
        assert service.name == "Test Service"
        assert service.status == "healthy"
        assert service.has_capability("test_capability")

    def test_register_duplicate_service_updates_existing(self):
        """Test that registering duplicate service updates existing."""
        service_id = ServiceId("test_service")

        # Register first time
        service1 = self.registration_service.register_service(
            service_id=service_id,
            name="Test Service",
            description="Test service",
            category="test"
        )

        # Register again with different data
        service2 = self.registration_service.register_service(
            service_id=service_id,
            name="Updated Service",
            description="Updated description",
            category="test"
        )

        # Should be the same object with updated metadata
        assert service1 is service2
        assert service1.name == "Test Service"  # Name doesn't change
        assert service2.status == "healthy"  # Status gets updated

    def test_unregister_service(self):
        """Test unregistering a service."""
        service_id = ServiceId("test_service")

        # Register service
        self.registration_service.register_service(
            service_id=service_id,
            name="Test Service",
            description="Test service",
            category="test"
        )

        # Unregister service
        success = self.registration_service.unregister_service(service_id)
        assert success is True

        # Verify service is gone
        service = self.registration_service.get_registered_service(service_id)
        assert service is None

    def test_unregister_nonexistent_service(self):
        """Test unregistering non-existent service."""
        service_id = ServiceId("nonexistent")
        success = self.registration_service.unregister_service(service_id)

        assert success is False

    def test_update_service_status(self):
        """Test updating service status."""
        service_id = ServiceId("test_service")

        # Register service
        self.registration_service.register_service(
            service_id=service_id,
            name="Test Service",
            description="Test service",
            category="test"
        )

        # Update status
        success = self.registration_service.update_service_status(service_id, "maintenance")
        assert success is True

        # Verify status update
        service = self.registration_service.get_registered_service(service_id)
        assert service.status == "maintenance"

    def test_get_all_registered_services(self):
        """Test getting all registered services."""
        # Register multiple services
        service_id1 = ServiceId("service1")
        service_id2 = ServiceId("service2")

        self.registration_service.register_service(
            service_id=service_id1,
            name="Service 1",
            description="Test service 1",
            category="test"
        )

        self.registration_service.register_service(
            service_id=service_id2,
            name="Service 2",
            description="Test service 2",
            category="test"
        )

        services = self.registration_service.get_all_registered_services()
        assert len(services) == 2

        service_names = [s.name for s in services]
        assert "Service 1" in service_names
        assert "Service 2" in service_names

    def test_heartbeat_service(self):
        """Test service heartbeat functionality."""
        service_id = ServiceId("test_service")

        # Register service
        self.registration_service.register_service(
            service_id=service_id,
            name="Test Service",
            description="Test service",
            category="test"
        )

        initial_last_seen = self.registration_service.get_registered_service(service_id).last_seen

        # Send heartbeat
        success = self.registration_service.heartbeat_service(service_id)
        assert success is True

        # Verify last_seen was updated
        updated_last_seen = self.registration_service.get_registered_service(service_id).last_seen
        assert updated_last_seen >= initial_last_seen
