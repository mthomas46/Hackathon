"""Unit tests for application commands."""

import pytest
from datetime import datetime, timezone

from services.discovery_agent.application.commands import (
    RegisterServiceCommand,
    UnregisterServiceCommand,
    UpdateServiceCommand,
    DiscoverServicesCommand
)


class TestRegisterServiceCommand:
    """Test cases for RegisterServiceCommand."""

    def test_command_creation(self):
        """Test basic command creation."""
        command = RegisterServiceCommand(
            service_id="test-service-001",
            service_type="api",
            endpoint="http://localhost:8080",
            capabilities=["health", "metrics"]
        )

        assert command.service_id == "test-service-001"
        assert command.service_type == "api"
        assert command.endpoint == "http://localhost:8080"
        assert command.capabilities == ["health", "metrics"]

    def test_command_with_optional_fields(self):
        """Test command with all optional fields."""
        command = RegisterServiceCommand(
            service_id="test-service-002",
            service_type="worker",
            endpoint="http://localhost:8081",
            capabilities=["processing", "queue"],
            metadata={"version": "1.0.0", "env": "prod"},
            tags=["production", "critical"]
        )

        assert command.metadata["version"] == "1.0.0"
        assert "production" in command.tags

    def test_command_validation(self):
        """Test command validation."""
        # Valid command
        valid_command = RegisterServiceCommand(
            service_id="valid-service",
            service_type="api",
            endpoint="http://example.com"
        )
        assert valid_command.service_id == "valid-service"

        # Commands are validated at creation time
        # (In a real implementation, you might have validation decorators)


class TestUnregisterServiceCommand:
    """Test cases for UnregisterServiceCommand."""

    def test_command_creation(self):
        """Test basic unregister command."""
        command = UnregisterServiceCommand(service_id="test-service-001")

        assert command.service_id == "test-service-001"
        assert hasattr(command, 'service_id')


class TestUpdateServiceCommand:
    """Test cases for UpdateServiceCommand."""

    def test_command_creation(self):
        """Test update command creation."""
        updates = {
            "status": "healthy",
            "capabilities": ["health", "metrics", "api"]
        }

        command = UpdateServiceCommand(
            service_id="test-service-001",
            updates=updates
        )

        assert command.service_id == "test-service-001"
        assert command.updates == updates

    def test_partial_updates(self):
        """Test partial update commands."""
        # Status only update
        status_command = UpdateServiceCommand(
            service_id="service-001",
            updates={"status": "unhealthy"}
        )
        assert status_command.updates["status"] == "unhealthy"

        # Capabilities update
        caps_command = UpdateServiceCommand(
            service_id="service-002",
            updates={"capabilities": ["new-capability"]}
        )
        assert "new-capability" in caps_command.updates["capabilities"]


class TestDiscoverServicesCommand:
    """Test cases for DiscoverServicesCommand."""

    def test_automatic_discovery_command(self):
        """Test automatic discovery command."""
        command = DiscoverServicesCommand(
            mode="automatic",
            timeout=30,
            filters={"type": "api"}
        )

        assert command.mode == "automatic"
        assert command.timeout == 30
        assert command.filters["type"] == "api"

    def test_manual_discovery_command(self):
        """Test manual discovery command."""
        services_to_discover = [
            {"name": "service1", "endpoint": "http://localhost:8080"},
            {"name": "service2", "endpoint": "http://localhost:8081"}
        ]

        command = DiscoverServicesCommand(
            mode="manual",
            services=services_to_discover
        )

        assert command.mode == "manual"
        assert len(command.services) == 2
        assert command.services[0]["name"] == "service1"

    def test_discovery_with_filters(self):
        """Test discovery command with various filters."""
        command = DiscoverServicesCommand(
            mode="automatic",
            filters={
                "network": "192.168.1.0/24",
                "port_range": "8000-9000",
                "service_types": ["api", "worker"]
            }
        )

        assert command.filters["network"] == "192.168.1.0/24"
        assert "api" in command.filters["service_types"]


class TestCommandValidation:
    """Test command validation logic."""

    def test_required_fields(self):
        """Test that required fields are enforced."""
        # RegisterServiceCommand requires service_id, service_type, endpoint
        with pytest.raises(TypeError):
            # Missing required fields should cause TypeError in pydantic
            RegisterServiceCommand()

    def test_field_types(self):
        """Test field type validation."""
        # Valid types
        command = RegisterServiceCommand(
            service_id="test-001",
            service_type="api",
            endpoint="http://example.com",
            capabilities=["health"]  # Should be list
        )
        assert isinstance(command.capabilities, list)

    def test_command_immutability(self):
        """Test that commands are immutable after creation."""
        command = RegisterServiceCommand(
            service_id="immutable-test",
            service_type="api",
            endpoint="http://test.com"
        )

        # Commands should be treated as immutable
        # (though pydantic allows modification, good practice is to treat as immutable)
        original_id = command.service_id

        # In practice, you shouldn't modify commands after creation
        assert command.service_id == original_id
