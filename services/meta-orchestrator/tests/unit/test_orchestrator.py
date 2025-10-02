"""Unit tests for the MetaOrchestrator class"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from core.orchestrator import MetaOrchestrator
from models.service import ServiceStatus, ServiceInfo
from models.result import OperationResult
from config.settings import Settings


class TestMetaOrchestrator:
    """Test cases for MetaOrchestrator"""

    @pytest.mark.unit
    def test_initialization(self, mock_settings, mock_docker_manager):
        """Test orchestrator initialization"""
        orchestrator = MetaOrchestrator(mock_settings)
        orchestrator.docker_manager = mock_docker_manager

        assert orchestrator.settings == mock_settings
        assert orchestrator.services == {}
        assert orchestrator.compose_config is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_compose_config_success(self, mock_settings, sample_compose_config, mock_compose_file):
        """Test successful compose config loading"""
        mock_settings.workspace_path = str(mock_compose_file.parent)
        mock_settings.compose_file = mock_compose_file.name

        orchestrator = MetaOrchestrator(mock_settings)

        await orchestrator._load_compose_config()

        assert orchestrator.compose_config == sample_compose_config
        assert len(orchestrator.compose_config['services']) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_compose_config_file_not_found(self, mock_settings, tmp_path):
        """Test compose config loading when file doesn't exist"""
        mock_settings.workspace_path = str(tmp_path)
        mock_settings.compose_file = "nonexistent.yml"

        orchestrator = MetaOrchestrator(mock_settings)

        with pytest.raises(SystemExit):  # Should raise and exit
            await orchestrator._load_compose_config()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_discover_services(self, mock_orchestrator, mock_docker_manager):
        """Test service discovery"""
        # Setup mock containers
        mock_containers = [
            Mock(id="container1", name="hackathon-user-store-1", image="user-store:latest"),
            Mock(id="container2", name="hackathon-redis-1", image="redis:7-alpine")
        ]
        mock_docker_manager.list_containers.return_value = mock_containers

        await mock_orchestrator._discover_services()

        assert len(mock_orchestrator.services) == 2
        assert 'redis' in mock_orchestrator.services
        assert 'user-store' in mock_orchestrator.services

        # Check redis service
        redis_service = mock_orchestrator.services['redis']
        assert redis_service.status == ServiceStatus.STOPPED  # No running container
        assert redis_service.name == 'redis'
        assert '6379:6379' in redis_service.ports

        # Check user-store service
        user_store = mock_orchestrator.services['user-store']
        assert user_store.status == ServiceStatus.STOPPED
        assert user_store.name == 'user-store'
        assert '8106:5150' in user_store.ports
        assert user_store.environment['SERVICE_NAME'] == 'user-store'

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_service_success(self, mock_orchestrator, mock_docker_manager):
        """Test successful service start"""
        # Setup service
        service = ServiceInfo(
            name="user-store",
            status=ServiceStatus.STOPPED,
            config={},
            ports=["8106:5150"],
            environment={"SERVICE_NAME": "user-store"}
        )
        mock_orchestrator.services["user-store"] = service

        # Mock successful compose up
        mock_docker_manager.compose_up.return_value = OperationResult(
            success=True,
            message="Service user-store started successfully"
        )

        result = await mock_orchestrator.start_service("user-store")

        assert result.success is True
        assert result.service_name == "user-store"
        assert result.action == "start"
        assert service.status == ServiceStatus.RUNNING

        # Verify docker manager was called
        mock_docker_manager.compose_up.assert_called_once_with(["user-store"], profile="all")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_service_not_found(self, mock_orchestrator):
        """Test starting a non-existent service"""
        with pytest.raises(Exception) as exc_info:
            await mock_orchestrator.start_service("nonexistent-service")

        assert "not found" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stop_service_success(self, mock_orchestrator, mock_docker_manager):
        """Test successful service stop"""
        # Setup running service
        service = ServiceInfo(
            name="user-store",
            status=ServiceStatus.RUNNING,
            config={},
            container_id="container123"
        )
        mock_orchestrator.services["user-store"] = service

        # Mock successful compose down
        mock_docker_manager.compose_down.return_value = OperationResult(
            success=True,
            message="Service user-store stopped successfully"
        )

        result = await mock_orchestrator.stop_service("user-store")

        assert result.success is True
        assert result.service_name == "user-store"
        assert result.action == "stop"
        assert service.status == ServiceStatus.STOPPED
        assert service.container_id is None

        # Verify docker manager was called
        mock_docker_manager.compose_down.assert_called_once_with(["user-store"])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_restart_service(self, mock_orchestrator, mock_docker_manager):
        """Test service restart"""
        # Setup service
        service = ServiceInfo(name="user-store", status=ServiceStatus.RUNNING, config={})
        mock_orchestrator.services["user-store"] = service

        # Mock successful operations
        mock_docker_manager.compose_down.return_value = OperationResult(success=True, message="Stopped")
        mock_docker_manager.compose_up.return_value = OperationResult(success=True, message="Started")

        result = await mock_orchestrator.restart_service("user-store")

        assert result.success is True
        assert result.action == "restart"

        # Verify both operations were called
        mock_docker_manager.compose_down.assert_called_once_with(["user-store"])
        mock_docker_manager.compose_up.assert_called_once_with(["user-store"], profile="all")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_service_config(self, mock_orchestrator):
        """Test service configuration update"""
        # Setup service with initial config
        initial_config = {
            'environment': ['SERVICE_NAME=user-store', 'PORT=8080'],
            'ports': ['8080:8080']
        }
        service = ServiceInfo(
            name="user-store",
            status=ServiceStatus.STOPPED,
            config=initial_config.copy(),
            environment={'SERVICE_NAME': 'user-store', 'PORT': '8080'}
        )
        mock_orchestrator.services["user-store"] = service

        # Update configuration
        config_updates = {
            'environment': {'NEW_VAR': 'new_value', 'PORT': '9090'}
        }

        result = await mock_orchestrator.update_service_config("user-store", config_updates)

        assert result.success is True
        assert result.action == "update_config"

        # Verify configuration was updated
        assert service.config['environment']['NEW_VAR'] == 'new_value'
        assert service.config['environment']['PORT'] == '9090'

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_service_status_all(self, mock_orchestrator):
        """Test getting status for all services"""
        # Setup services
        service1 = ServiceInfo(name="redis", status=ServiceStatus.RUNNING, config={})
        service2 = ServiceInfo(name="user-store", status=ServiceStatus.STOPPED, config={})
        mock_orchestrator.services = {"redis": service1, "user-store": service2}

        services = await mock_orchestrator.get_service_status()

        assert len(services) == 2
        assert services[0].name == "redis"
        assert services[1].name == "user-store"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_service_status_specific(self, mock_orchestrator):
        """Test getting status for specific service"""
        service = ServiceInfo(name="redis", status=ServiceStatus.RUNNING, config={})
        mock_orchestrator.services = {"redis": service}

        services = await mock_orchestrator.get_service_status("redis")

        assert len(services) == 1
        assert services[0].name == "redis"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_service_logs(self, mock_orchestrator, mock_docker_manager):
        """Test getting service logs"""
        mock_docker_manager.get_container_logs.return_value = "Sample log output"

        logs = await mock_orchestrator.get_service_logs("user-store", 100)

        assert logs == "Sample log output"
        mock_docker_manager.get_container_logs.assert_called_once_with("user-store", 100)
