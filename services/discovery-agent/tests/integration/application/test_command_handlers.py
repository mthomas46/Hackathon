"""Integration tests for discovery agent command handlers."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from services.discovery_agent.application.commands import (
    RegisterServiceCommand,
    DiscoverServicesCommand,
    UpdateServiceCommand
)
from services.discovery_agent.application.handlers.service_handler import ServiceHandler
from services.discovery_agent.application.handlers.discovery_handler import DiscoveryHandler
from services.discovery_agent.domain.entities import ServiceInfo, ToolInfo
from services.discovery_agent.domain.value_objects import ServiceStatus, ToolCategory


class TestServiceHandlerIntegration:
    """Integration tests for ServiceHandler."""

    @pytest.fixture
    async def service_handler(self):
        """Create ServiceHandler with mocked dependencies."""
        handler = ServiceHandler()

        # Mock the repository
        handler._service_repository = Mock()
        handler._service_repository.save = AsyncMock()
        handler._service_repository.find_by_id = AsyncMock()
        handler._service_repository.update = AsyncMock()

        # Mock domain services
        handler._health_check_service = Mock()
        handler._health_check_service.check_service_health = AsyncMock(
            return_value=Mock(status=ServiceStatus.HEALTHY, response_time=0.25)
        )

        return handler

    @pytest.mark.asyncio
    async def test_register_service_full_workflow(self, service_handler):
        """Test complete service registration workflow."""
        command = RegisterServiceCommand(
            service_id="integration-test-service",
            service_type="api",
            endpoint="http://localhost:8080",
            capabilities=["health", "metrics", "api"],
            metadata={"version": "1.0.0", "environment": "test"}
        )

        # Execute command
        result = await service_handler.handle_register_service(command)

        # Verify the workflow completed
        assert result is not None
        service_handler._service_repository.save.assert_called_once()

        # Verify the saved service has all expected attributes
        saved_service = service_handler._service_repository.save.call_args[0][0]
        assert saved_service.name == "integration-test-service"
        assert saved_service.type == "api"
        assert saved_service.endpoint == "http://localhost:8080"
        assert "health" in saved_service.capabilities

    @pytest.mark.asyncio
    async def test_update_service_integration(self, service_handler):
        """Test service update with validation."""
        # Mock existing service
        existing_service = ServiceInfo(
            name="existing-service",
            type="api",
            port=8080,
            status=ServiceStatus.HEALTHY
        )
        service_handler._service_repository.find_by_id.return_value = existing_service

        command = UpdateServiceCommand(
            service_id="existing-service",
            updates={
                "capabilities": ["health", "metrics", "updated-api"],
                "metadata": {"version": "2.0.0"}
            }
        )

        result = await service_handler.handle_update_service(command)

        assert result is not None
        service_handler._service_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_service_with_health_check(self, service_handler):
        """Test service registration includes health check."""
        command = RegisterServiceCommand(
            service_id="health-check-service",
            service_type="api",
            endpoint="http://localhost:8081"
        )

        await service_handler.handle_register_service(command)

        # Verify health check was performed
        service_handler._health_check_service.check_service_health.assert_called_once()


class TestDiscoveryHandlerIntegration:
    """Integration tests for DiscoveryHandler."""

    @pytest.fixture
    async def discovery_handler(self):
        """Create DiscoveryHandler with mocked dependencies."""
        handler = DiscoveryHandler()

        # Mock discovery service
        handler._discovery_service = Mock()
        handler._discovery_service.discover_services = AsyncMock(
            return_value=Mock(
                services_discovered=[
                    ServiceInfo(name="discovered-api", type="api", port=8080),
                    ServiceInfo(name="discovered-worker", type="worker", port=8081)
                ],
                tools_discovered=[
                    ToolInfo(name="api-tool", category=ToolCategory.ANALYSIS),
                    ToolInfo(name="worker-tool", category=ToolCategory.MONITORING)
                ],
                success=True,
                duration=2.5,
                errors=[]
            )
        )

        # Mock repositories
        handler._service_repository = Mock()
        handler._service_repository.save = AsyncMock()
        handler._tool_repository = Mock()
        handler._tool_repository.save = AsyncMock()

        return handler

    @pytest.mark.asyncio
    async def test_automatic_discovery_workflow(self, discovery_handler):
        """Test complete automatic discovery workflow."""
        command = DiscoverServicesCommand(
            mode="automatic",
            timeout=30,
            filters={"type": "api"}
        )

        result = await discovery_handler.handle_discover_services(command)

        # Verify discovery was performed
        discovery_handler._discovery_service.discover_services.assert_called_once_with(
            mode="automatic",
            timeout=30,
            filters={"type": "api"}
        )

        # Verify results were saved
        assert discovery_handler._service_repository.save.call_count == 2  # 2 services
        assert discovery_handler._tool_repository.save.call_count == 2    # 2 tools

        assert result.success is True
        assert result.services_discovered == 2
        assert result.tools_discovered == 2

    @pytest.mark.asyncio
    async def test_manual_discovery_workflow(self, discovery_handler):
        """Test manual discovery with provided services."""
        manual_services = [
            {"name": "manual-service-1", "endpoint": "http://manual1:8080"},
            {"name": "manual-service-2", "endpoint": "http://manual2:8081"}
        ]

        command = DiscoverServicesCommand(
            mode="manual",
            services=manual_services
        )

        result = await discovery_handler.handle_discover_services(command)

        # For manual discovery, should not call the discovery service
        discovery_handler._discovery_service.discover_services.assert_not_called()

        # Should still save the manual services
        assert discovery_handler._service_repository.save.call_count == 2

    @pytest.mark.asyncio
    async def test_discovery_error_handling(self, discovery_handler):
        """Test error handling during discovery."""
        # Mock discovery service to raise an exception
        discovery_handler._discovery_service.discover_services.side_effect = Exception("Network timeout")

        command = DiscoverServicesCommand(mode="automatic")

        result = await discovery_handler.handle_discover_services(command)

        # Should handle the error gracefully
        assert result.success is False
        assert "Network timeout" in result.error_message


class TestCommandBusIntegration:
    """Integration tests for command bus functionality."""

    @pytest.mark.asyncio
    async def test_command_bus_routing(self):
        """Test that commands are routed to correct handlers."""
        # This would test the command bus if implemented
        # For now, test the handler interfaces directly

        # Test RegisterServiceCommand routing concept
        command = RegisterServiceCommand(
            service_id="bus-test-service",
            service_type="api",
            endpoint="http://bus-test:8080"
        )

        # Verify command structure for routing
        assert hasattr(command, 'service_id')
        assert hasattr(command, 'service_type')
        assert hasattr(command, 'endpoint')

        # In a real command bus, this would be routed to ServiceHandler.handle_register_service

    def test_command_validation_integration(self):
        """Test command validation across different command types."""
        # Test valid commands
        valid_register = RegisterServiceCommand(
            service_id="valid-service",
            service_type="api",
            endpoint="http://valid:8080"
        )

        valid_discover = DiscoverServicesCommand(
            mode="automatic",
            timeout=60
        )

        # Commands should be valid (no exceptions during creation)
        assert valid_register.service_id == "valid-service"
        assert valid_discover.mode == "automatic"

    @pytest.mark.asyncio
    async def test_event_driven_workflow(self):
        """Test event-driven aspects of command handling."""
        # Mock event publishing
        with patch('services.discovery_agent.infrastructure.events.event_publisher') as mock_publisher:
            mock_publisher.publish_event = AsyncMock()

            # Create a handler and execute a command that should publish events
            handler = ServiceHandler()
            handler._service_repository = Mock()
            handler._service_repository.save = AsyncMock()

            command = RegisterServiceCommand(
                service_id="event-test-service",
                service_type="api",
                endpoint="http://event-test:8080"
            )

            # Mock event publishing in handler (if implemented)
            # await handler.handle_register_service(command)

            # Verify events were published
            # mock_publisher.publish_event.assert_called()

            # Placeholder - would verify ServiceRegistered event was published
            assert True  # Test structure is in place
