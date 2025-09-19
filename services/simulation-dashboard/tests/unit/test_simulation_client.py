"""Unit tests for simulation service client."""

import pytest
import asyncio
import json
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from aiohttp import ClientError, ClientTimeout

from services.clients.simulation_client import (
    SimulationClient, SimulationClientError, SimulationClientTimeoutError
)


class TestSimulationClient:
    """Test cases for SimulationClient."""

    @pytest.fixture
    def config(self):
        """Create a mock configuration for testing."""
        config = MagicMock()
        config.simulation_service.host = "localhost"
        config.simulation_service.port = 5075
        config.simulation_service.timeout = 30.0
        config.simulation_service.retry_attempts = 3
        config.simulation_service.base_url = "http://localhost:5075"
        return config

    @pytest.fixture
    def client(self, config):
        """Create a SimulationClient instance for testing."""
        return SimulationClient(config.simulation_service)

    def test_client_initialization(self, config):
        """Test client initialization."""
        client = SimulationClient(config.simulation_service)

        assert client.base_url == "http://localhost:5075"
        assert client.timeout == 30.0
        assert client.retry_attempts == 3
        assert client.session is None  # Not created until first use

    @pytest.mark.asyncio
    async def test_successful_health_check(self, client):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "status": "healthy",
            "version": "1.0.0",
            "uptime": "2h 30m"
        })

        with patch('aiohttp.ClientSession.get', return_value=mock_response) as mock_get:
            result = await client.get_health()

            assert result["status"] == "healthy"
            assert result["version"] == "1.0.0"
            mock_get.assert_called_once_with(
                "http://localhost:5075/health",
                timeout=30.0
            )

    @pytest.mark.asyncio
    async def test_health_check_http_error(self, client):
        """Test health check with HTTP error."""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")

        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            with pytest.raises(SimulationClientError) as exc_info:
                await client.get_health()

            assert "HTTP 500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_health_check_connection_error(self, client):
        """Test health check with connection error."""
        with patch('aiohttp.ClientSession.get', side_effect=ClientError("Connection failed")):
            with pytest.raises(SimulationClientError) as exc_info:
                await client.get_health()

            assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, client):
        """Test health check with timeout."""
        with patch('aiohttp.ClientSession.get', side_effect=asyncio.TimeoutError()):
            with pytest.raises(SimulationClientTimeoutError):
                await client.get_health()

    @pytest.mark.asyncio
    async def test_list_simulations(self, client):
        """Test listing simulations."""
        mock_simulations = [
            {
                "id": "sim_001",
                "name": "Test Simulation",
                "status": "completed",
                "created_at": "2024-01-15T10:00:00Z"
            }
        ]

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_simulations)

        with patch('aiohttp.ClientSession.get', return_value=mock_response) as mock_get:
            result = await client.list_simulations()

            assert len(result) == 1
            assert result[0]["id"] == "sim_001"
            mock_get.assert_called_once_with(
                "http://localhost:5075/api/v1/simulations",
                timeout=30.0
            )

    @pytest.mark.asyncio
    async def test_create_simulation(self, client):
        """Test creating a simulation."""
        simulation_data = {
            "name": "New Simulation",
            "type": "software_development",
            "complexity": "medium"
        }

        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={
            "id": "sim_002",
            "name": "New Simulation",
            "status": "created",
            "created_at": "2024-01-16T10:00:00Z"
        })

        with patch('aiohttp.ClientSession.post', return_value=mock_response) as mock_post:
            result = await client.create_simulation(simulation_data)

            assert result["id"] == "sim_002"
            assert result["status"] == "created"

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://localhost:5075/api/v1/simulations"
            assert call_args[1]["json"] == simulation_data

    @pytest.mark.asyncio
    async def test_get_simulation_details(self, client):
        """Test getting simulation details."""
        simulation_id = "sim_001"
        mock_details = {
            "id": simulation_id,
            "name": "Test Simulation",
            "status": "running",
            "progress": 65.5
        }

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_details)

        with patch('aiohttp.ClientSession.get', return_value=mock_response) as mock_get:
            result = await client.get_simulation_details(simulation_id)

            assert result["id"] == simulation_id
            assert result["status"] == "running"
            mock_get.assert_called_once_with(
                f"http://localhost:5075/api/v1/simulations/{simulation_id}",
                timeout=30.0
            )

    @pytest.mark.asyncio
    async def test_execute_simulation(self, client):
        """Test executing a simulation."""
        simulation_id = "sim_001"

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "status": "executing",
            "message": "Simulation started successfully"
        })

        with patch('aiohttp.ClientSession.post', return_value=mock_response) as mock_post:
            result = await client.execute_simulation(simulation_id)

            assert result["status"] == "executing"
            mock_post.assert_called_once_with(
                f"http://localhost:5075/api/v1/simulations/{simulation_id}/execute",
                timeout=30.0
            )

    @pytest.mark.asyncio
    async def test_get_simulation_reports(self, client):
        """Test getting simulation reports."""
        simulation_id = "sim_001"
        mock_reports = [
            {
                "id": "report_001",
                "type": "executive_summary",
                "generated_at": "2024-01-16T12:00:00Z",
                "status": "completed"
            }
        ]

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_reports)

        with patch('aiohttp.ClientSession.get', return_value=mock_response) as mock_get:
            result = await client.get_simulation_reports(simulation_id)

            assert len(result) == 1
            assert result[0]["type"] == "executive_summary"
            mock_get.assert_called_once_with(
                f"http://localhost:5075/api/v1/simulations/{simulation_id}/reports",
                timeout=30.0
            )

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, client):
        """Test retry mechanism on failures."""
        # Mock a sequence of failures followed by success
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "healthy"})

        with patch('aiohttp.ClientSession.get') as mock_get:
            # First two calls fail, third succeeds
            mock_get.side_effect = [
                ClientError("Connection failed"),
                ClientError("Connection failed"),
                mock_response
            ]

            result = await client.get_health()

            assert result["status"] == "healthy"
            assert mock_get.call_count == 3  # Should retry twice before succeeding

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, client):
        """Test behavior when max retries are exceeded."""
        with patch('aiohttp.ClientSession.get', side_effect=ClientError("Connection failed")):
            with pytest.raises(SimulationClientError):
                await client.get_health()

    @pytest.mark.asyncio
    async def test_session_reuse(self, client):
        """Test that HTTP sessions are reused."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "healthy"})

        with patch('aiohttp.ClientSession.get', return_value=mock_response) as mock_get:
            # Make multiple requests
            await client.get_health()
            await client.get_health()

            # Should reuse the same session
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, client):
        """Test handling of invalid JSON responses."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))

        with patch('aiohttp.ClientSession.get', return_value=mock_response):
            with pytest.raises(SimulationClientError) as exc_info:
                await client.get_health()

            assert "Invalid JSON" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_context_manager_usage(self, client):
        """Test that client can be used as context manager."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "healthy"})

        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session

            async with client:
                result = await client.get_health()

            assert result["status"] == "healthy"
            # Session should be closed when exiting context
            mock_session.close.assert_called_once()

    def test_client_string_representation(self, client):
        """Test client string representation."""
        assert str(client) == "SimulationClient(base_url=http://localhost:5075)"
        assert repr(client) == "SimulationClient(base_url=http://localhost:5075, timeout=30.0)"


class TestSimulationClientError:
    """Test cases for SimulationClientError."""

    def test_error_initialization(self):
        """Test error initialization."""
        error = SimulationClientError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"

    def test_error_with_cause(self):
        """Test error with underlying cause."""
        cause = ValueError("Original error")
        error = SimulationClientError("Wrapper error", cause)

        assert str(error) == "Wrapper error"
        assert error.cause == cause


class TestSimulationClientTimeoutError:
    """Test cases for SimulationClientTimeoutError."""

    def test_timeout_error(self):
        """Test timeout error."""
        error = SimulationClientTimeoutError("Request timed out")
        assert str(error) == "Request timed out"
        assert isinstance(error, SimulationClientError)


if __name__ == "__main__":
    pytest.main([__file__])