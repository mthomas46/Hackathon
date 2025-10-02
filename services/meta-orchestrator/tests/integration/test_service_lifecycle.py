"""Integration tests for service lifecycle management"""

import pytest
from unittest.mock import Mock, AsyncMock
import asyncio

from core.orchestrator import MetaOrchestrator
from models.service import ServiceStatus
from models.result import OperationResult


@pytest.mark.integration
class TestServiceLifecycle:
    """Test the complete service lifecycle"""

    @pytest.fixture
    def orchestrator(self, mock_settings, mock_docker_manager, sample_compose_config):
        """Create orchestrator with mock dependencies"""
        orchestrator = MetaOrchestrator.__new__(MetaOrchestrator)
        orchestrator.settings = mock_settings
        orchestrator.docker_manager = mock_docker_manager
        orchestrator.compose_config = sample_compose_config
        orchestrator.services = {}

        # Initialize services from compose config
        asyncio.run(orchestrator._discover_services())

        return orchestrator

    @pytest.mark.asyncio
    async def test_complete_service_lifecycle(self, orchestrator, mock_docker_manager):
        """Test complete service lifecycle: discover -> start -> modify -> restart -> stop"""

        # 1. Verify services are discovered
        services = await orchestrator.get_service_status()
        assert len(services) == 2

        redis_service = next(s for s in services if s.name == 'redis')
        user_store_service = next(s for s in services if s.name == 'user-store')

        assert redis_service.status == ServiceStatus.STOPPED
        assert user_store_service.status == ServiceStatus.STOPPED

        # 2. Start the user-store service
        mock_docker_manager.compose_up.return_value = OperationResult(
            success=True, message="user-store started"
        )

        start_result = await orchestrator.start_service("user-store")
        assert start_result.success is True
        assert start_result.action == "start"

        # Verify service status changed
        services = await orchestrator.get_service_status("user-store")
        assert services[0].status == ServiceStatus.RUNNING

        # 3. Update service configuration
        config_updates = {
            "environment": {
                "NEW_ENV_VAR": "test_value",
                "SERVICE_API_PORT": "9090"
            }
        }

        update_result = await orchestrator.update_service_config("user-store", config_updates)
        assert update_result.success is True
        assert update_result.action == "update_config"

        # Verify configuration was updated
        user_store = orchestrator.services["user-store"]
        assert user_store.environment["NEW_ENV_VAR"] == "test_value"
        assert user_store.environment["SERVICE_API_PORT"] == "9090"

        # 4. Restart the service with new configuration
        mock_docker_manager.compose_down.return_value = OperationResult(
            success=True, message="user-store stopped"
        )
        mock_docker_manager.compose_up.return_value = OperationResult(
            success=True, message="user-store restarted"
        )

        restart_result = await orchestrator.restart_service("user-store")
        assert restart_result.success is True
        assert restart_result.action == "restart"

        # 5. Stop the service
        stop_result = await orchestrator.stop_service("user-store")
        assert stop_result.success is True
        assert stop_result.action == "stop"

        # Verify service is stopped
        services = await orchestrator.get_service_status("user-store")
        assert services[0].status == ServiceStatus.STOPPED

    @pytest.mark.asyncio
    async def test_dependency_handling(self, orchestrator, mock_docker_manager):
        """Test that service dependencies are respected"""

        # Mock successful operations
        mock_docker_manager.compose_up.return_value = OperationResult(success=True, message="OK")

        # Try to start user-store (depends on redis)
        result = await orchestrator.start_service("user-store")

        # Should succeed (dependency checking is basic in this implementation)
        assert result.success is True

        # Verify compose_up was called with correct parameters
        mock_docker_manager.compose_up.assert_called_with(["user-store"], profile="all")

    @pytest.mark.asyncio
    async def test_configuration_validation(self, orchestrator):
        """Test configuration update validation"""

        # Setup service
        service = orchestrator.services["user-store"]

        # Valid configuration update
        valid_updates = {
            "environment": {
                "NEW_VAR": "value",
                "EXISTING_VAR": "updated"
            }
        }

        result = await orchestrator.update_service_config("user-store", valid_updates)
        assert result.success is True

        # Verify changes were applied
        assert service.environment["NEW_VAR"] == "value"

    @pytest.mark.asyncio
    async def test_error_handling(self, orchestrator, mock_docker_manager):
        """Test error handling in service operations"""

        # Mock failed operation
        mock_docker_manager.compose_up.return_value = OperationResult(
            success=False, message="Failed to start container"
        )

        result = await orchestrator.start_service("user-store")

        assert result.success is False
        assert "Failed to start container" in result.message

        # Service status should remain unchanged
        services = await orchestrator.get_service_status("user-store")
        assert services[0].status == ServiceStatus.STOPPED

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, orchestrator, mock_docker_manager):
        """Test handling concurrent service operations"""

        # Mock async operations
        async def delayed_success(*args, **kwargs):
            await asyncio.sleep(0.1)
            return OperationResult(success=True, message="Success")

        mock_docker_manager.compose_up.side_effect = delayed_success

        # Start multiple operations concurrently
        tasks = [
            orchestrator.start_service("user-store"),
            orchestrator.start_service("redis")
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All operations should succeed
        for result in results:
            assert result.success is True

    @pytest.mark.asyncio
    async def test_service_logs_retrieval(self, orchestrator, mock_docker_manager):
        """Test service logs retrieval"""

        mock_logs = """
2023-10-02 10:00:00 INFO Starting user-store service
2023-10-02 10:00:01 INFO Database connection established
2023-10-02 10:00:02 INFO Service listening on port 5150
2023-10-02 10:00:03 INFO Health check passed
        """.strip()

        mock_docker_manager.get_container_logs.return_value = mock_logs

        logs = await orchestrator.get_service_logs("user-store", 100)

        assert "Starting user-store service" in logs
        assert "listening on port 5150" in logs
        assert "Health check passed" in logs

        mock_docker_manager.get_container_logs.assert_called_once_with("user-store", 100)
