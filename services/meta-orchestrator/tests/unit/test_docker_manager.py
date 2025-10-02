"""Unit tests for the DockerManager class"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import subprocess

from docker.manager import DockerManager
from models.container import ContainerInfo
from models.result import OperationResult
from config.settings import DockerSettings


class TestDockerManager:
    """Test cases for DockerManager"""

    @pytest.fixture
    def docker_settings(self):
        """Docker settings for testing"""
        return DockerSettings(
            host="unix:///var/run/docker.sock",
            tls_verify=False,
            timeout=60
        )

    @pytest.fixture
    def docker_manager(self, docker_settings):
        """Docker manager instance"""
        manager = DockerManager(docker_settings)
        return manager

    @pytest.mark.unit
    def test_initialization(self, docker_manager, docker_settings):
        """Test Docker manager initialization"""
        assert docker_manager.settings == docker_settings
        assert docker_manager.workspace_path is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_containers_success(self, docker_manager):
        """Test successful container listing"""
        mock_output = """container1\thackathon-user-store-1\tuser-store:latest\tUp 2 hours\t0.0.0.0:8106->5150/tcp
container2\thackathon-redis-1\tredis:7-alpine\tUp 2 hours\t0.0.0.0:6379->6379/tcp"""

        with patch.object(docker_manager, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=['docker', 'ps', '--format', 'json', '-a'],
                returncode=0,
                stdout=mock_output,
                stderr=""
            )

            containers = await docker_manager.list_containers(all=True)

            assert len(containers) == 2
            assert containers[0].id == "container1"
            assert containers[0].name == "hackathon-user-store-1"
            assert containers[0].image == "user-store:latest"
            assert containers[1].name == "hackathon-redis-1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_containers_empty(self, docker_manager):
        """Test container listing when no containers exist"""
        with patch.object(docker_manager, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=['docker', 'ps', '--format', 'json', '-a'],
                returncode=0,
                stdout="",
                stderr=""
            )

            containers = await docker_manager.list_containers()

            assert len(containers) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compose_up_success(self, docker_manager):
        """Test successful docker-compose up"""
        with patch.object(docker_manager, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=['docker', 'compose', 'up', '-d', 'user-store'],
                returncode=0,
                stdout="user-store is up-to-date",
                stderr=""
            )

            result = await docker_manager.compose_up(["user-store"], profile="all")

            assert result.success is True
            assert "up-to-date" in result.message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compose_up_failure(self, docker_manager):
        """Test docker-compose up failure"""
        with patch.object(docker_manager, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=['docker', 'compose', 'up', '-d', 'user-store'],
                returncode=1,
                stdout="",
                stderr="ERROR: Service 'user-store' failed to build"
            )

            result = await docker_manager.compose_up(["user-store"])

            assert result.success is False
            assert "failed to build" in result.message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compose_down_success(self, docker_manager):
        """Test successful docker-compose down"""
        with patch.object(docker_manager, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=['docker', 'compose', 'down', 'user-store'],
                returncode=0,
                stdout="user-store stopped and removed",
                stderr=""
            )

            result = await docker_manager.compose_down(["user-store"])

            assert result.success is True
            assert "stopped and removed" in result.message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_compose_restart_success(self, docker_manager):
        """Test successful docker-compose restart"""
        with patch.object(docker_manager, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=['docker', 'compose', 'restart', 'user-store'],
                returncode=0,
                stdout="user-store restarted",
                stderr=""
            )

            result = await docker_manager.compose_restart(["user-store"])

            assert result.success is True
            assert "restarted" in result.message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_container_logs_success(self, docker_manager):
        """Test successful log retrieval"""
        mock_logs = "2023-10-01 10:00:00 INFO Starting user-store service\n2023-10-01 10:00:01 INFO Service ready"

        with patch.object(docker_manager, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=['docker', 'logs', '--tail', '100', 'user-store'],
                returncode=0,
                stdout=mock_logs,
                stderr=""
            )

            logs = await docker_manager.get_container_logs("user-store", 100)

            assert logs == mock_logs

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_container_logs_failure(self, docker_manager):
        """Test log retrieval failure"""
        with patch.object(docker_manager, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=['docker', 'logs', '--tail', '100', 'user-store'],
                returncode=1,
                stdout="",
                stderr="Error: No such container: user-store"
            )

            logs = await docker_manager.get_container_logs("user-store", 100)

            assert "Error retrieving logs" in logs
            assert "No such container" in logs

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_service_status_running(self, docker_manager):
        """Test getting status of running service"""
        mock_output = "container1\thackathon-user-store-1\tuser-store:latest\tUp 5 minutes\t0.0.0.0:8106->5150/tcp"

        with patch.object(docker_manager, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=['docker', 'ps', '--format', 'json'],
                returncode=0,
                stdout=mock_output,
                stderr=""
            )

            status = await docker_manager.get_service_status("user-store")

            assert status == "Up 5 minutes"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_service_status_not_found(self, docker_manager):
        """Test getting status of non-existent service"""
        with patch.object(docker_manager, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=['docker', 'ps', '--format', 'json'],
                returncode=0,
                stdout="",
                stderr=""
            )

            status = await docker_manager.get_service_status("nonexistent")

            assert status is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_command_success(self, docker_manager):
        """Test successful command execution"""
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Hello World", b"")
            mock_exec.return_value = mock_process

            result = await docker_manager._run_command(['echo', 'Hello World'])

            assert result.returncode == 0
            assert result.stdout == "Hello World"
            assert result.stderr == ""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_command_failure(self, docker_manager):
        """Test command execution failure"""
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"Command failed")
            mock_exec.return_value = mock_process

            result = await docker_manager._run_command(['invalid-command'])

            assert result.returncode == 1
            assert result.stdout == ""
            assert result.stderr == "Command failed"
