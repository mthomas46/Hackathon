"""Shared test configuration and fixtures"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from pathlib import Path

from config.settings import Settings, DockerSettings, ServiceSettings, SecuritySettings
from tests.fixtures.docker_compose_fixture import sample_compose_config, mock_compose_file


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings(tmp_path):
    """Mock settings for testing"""
    settings = Settings()
    settings.workspace_path = str(tmp_path)
    settings.compose_file = "docker-compose.test.yml"
    settings.docker = DockerSettings(
        host="unix:///var/run/docker.sock",
        tls_verify=False
    )
    settings.service = ServiceSettings(
        name="test-orchestrator",
        debug=True
    )
    settings.security = SecuritySettings(
        enable_auth=False
    )
    return settings


@pytest.fixture
def mock_docker_manager():
    """Mock Docker manager for testing"""
    manager = Mock()
    manager.list_containers = AsyncMock(return_value=[])
    manager.compose_up = AsyncMock(return_value=Mock(success=True, message="Service started"))
    manager.compose_down = AsyncMock(return_value=Mock(success=True, message="Service stopped"))
    manager.compose_restart = AsyncMock(return_value=Mock(success=True, message="Service restarted"))
    manager.get_container_logs = AsyncMock(return_value="Mock logs")
    return manager


@pytest.fixture
def mock_orchestrator(mock_settings, mock_docker_manager, sample_compose_config):
    """Mock orchestrator with pre-configured services"""
    from core.orchestrator import MetaOrchestrator

    # Mock the compose config
    orchestrator = MetaOrchestrator.__new__(MetaOrchestrator)
    orchestrator.settings = mock_settings
    orchestrator.docker_manager = mock_docker_manager
    orchestrator.compose_config = sample_compose_config
    orchestrator.services = {}

    return orchestrator
