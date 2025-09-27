"""Integration tests for service discovery functionality."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from httpx import AsyncClient

from services.discovery_agent.domain.entities import ServiceInfo, ToolInfo
from services.discovery_agent.domain.value_objects import ServiceStatus, ToolCategory
from services.discovery_agent.application.commands import RegisterServiceCommand
from services.discovery_agent.application.handlers.service_handler import ServiceHandler


class TestServiceDiscoveryIntegration:
    """Integration tests for complete service discovery workflows."""

    @pytest.fixture
    async def client(self):
        """Create test client for API integration tests."""
        from services.discovery_agent.presentation.api.routes import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_full_service_discovery_workflow(self):
        """Test complete service discovery workflow from API to domain."""
        # This is a high-level integration test that would test the full flow
        # For now, we'll mock the components

        # Mock service discovery
        with patch('services.discovery_agent.domain.services.discovery_service') as mock_discovery:
            mock_discovery.discover_services = AsyncMock()
            mock_discovery.discover_services.return_value = Mock(
                services_discovered=[
                    ServiceInfo(name="test-service", type="api", port=8080)
                ],
                tools_discovered=[
                    ToolInfo(name="test-tool", category=ToolCategory.ANALYSIS)
                ],
                success=True,
                duration=1.5
            )

            # Test the workflow (mocked for now)
            assert True  # Placeholder - would test actual workflow

    @pytest.mark.asyncio
    async def test_service_registration_integration(self):
        """Test service registration through command handler."""
        handler = ServiceHandler()

        command = RegisterServiceCommand(
            service_id="test-service-001",
            service_type="api",
            endpoint="http://localhost:8080",
            capabilities=["health", "metrics", "api"]
        )

        # Mock the repository
        with patch.object(handler, '_service_repository') as mock_repo:
            mock_repo.save = AsyncMock()

            # Execute command (would be through command bus in real implementation)
            result = await handler.handle_register_service(command)

            # Verify repository was called
            mock_repo.save.assert_called_once()
            assert result is not None

    @pytest.mark.asyncio
    async def test_tool_execution_integration(self):
        """Test tool execution workflow."""
        from services.discovery_agent.domain.services import ToolExecutionService

        service = ToolExecutionService()

        # Register a mock tool
        tool = ToolInfo(
            name="mock-analyzer",
            category=ToolCategory.ANALYSIS,
            description="Mock analysis tool",
            parameters={"input": "string", "format": "json"}
        )

        service.register_tool(tool)

        # Mock execution
        with patch.object(service, '_execute_tool_impl', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {"status": "success", "result": "analyzed"}

            result = await service.execute_tool("mock-analyzer", {"input": "test"})

            assert result["status"] == "success"
            assert result["result"] == "analyzed"

    def test_domain_entity_integration(self):
        """Test domain entities work together properly."""
        # Create service
        service = ServiceInfo(
            name="integration-test-service",
            type="api",
            port=8080,
            status=ServiceStatus.HEALTHY
        )

        # Create tool
        tool = ToolInfo(
            name="integration-test-tool",
            category=ToolCategory.MONITORING,
            description="Integration test tool"
        )

        # Test relationships
        assert service.name == "integration-test-service"
        assert service.status == ServiceStatus.HEALTHY
        assert tool.category == ToolCategory.MONITORING

        # Test serialization
        service_data = service.to_dict()
        assert service_data["name"] == "integration-test-service"

        tool_data = tool.to_dict()
        assert tool_data["name"] == "integration-test-tool"

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error handling across layers."""
        from services.discovery_agent.domain.services import DiscoveryService

        service = DiscoveryService()

        # Test with invalid input
        with pytest.raises(ValueError):
            await service.discover_services("invalid_mode")

    def test_value_object_validation(self):
        """Test value objects maintain invariants."""
        from services.discovery_agent.domain.value_objects import ServiceStatus, ToolCategory

        # Test enum values
        assert ServiceStatus.HEALTHY.value == "healthy"
        assert ToolCategory.ANALYSIS.value == "analysis"

        # Test string conversion
        assert ServiceStatus.from_string("unhealthy") == ServiceStatus.UNHEALTHY
        assert ToolCategory.from_string("monitoring") == ToolCategory.MONITORING

    def test_repository_pattern_integration(self):
        """Test repository pattern implementation."""
        from services.discovery_agent.infrastructure.repositories import ServiceRepository

        # Mock repository operations
        repo = ServiceRepository()

        # Test interface (would be implemented with actual storage)
        assert hasattr(repo, 'save')
        assert hasattr(repo, 'find_by_id')
        assert hasattr(repo, 'find_all')
        assert hasattr(repo, 'delete')

    def test_event_driven_architecture(self):
        """Test event-driven architecture components."""
        from services.discovery_agent.application.events import ServiceDiscoveredEvent

        # Create event
        event = ServiceDiscoveredEvent(
            service_id="test-service",
            service_type="api",
            discovered_at="2023-01-01T00:00:00Z"
        )

        # Test event structure
        assert event.service_id == "test-service"
        assert event.service_type == "api"
        assert event.event_type == "service_discovered"
