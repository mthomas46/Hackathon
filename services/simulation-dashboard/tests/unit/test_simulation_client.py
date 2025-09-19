"""Unit tests for SimulationClient.

This module contains unit tests for the SimulationClient class,
testing HTTP client functionality and error handling.
"""

import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock
from services.clients.simulation_client import SimulationClient, SimulationClientError


class TestSimulationClient:
    """Test cases for SimulationClient."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        config = Mock()
        config.base_url = "http://test-simulation:5075"
        config.timeout = 30.0
        config.retry_attempts = 3
        return SimulationClient(config)

    @pytest.mark.asyncio
    async def test_create_simulation_success(self, client):
        """Test successful simulation creation."""
        mock_response = {
            "success": True,
            "simulation_id": "test_sim_001",
            "message": "Simulation created successfully"
        }

        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            mock_request.return_value.status_code = 201
            mock_request.return_value.headers = {'content-type': 'application/json'}
            mock_request.return_value.json.return_value = mock_response

            result = await client.create_simulation({"name": "Test Simulation"})

            assert result == mock_response
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_simulation_failure(self, client):
        """Test simulation creation failure."""
        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            mock_request.return_value.status_code = 400
            mock_request.return_value.headers = {'content-type': 'application/json'}
            mock_request.return_value.json.return_value = {"error": "Invalid request"}

            with pytest.raises(SimulationClientError):
                await client.create_simulation({"name": ""})

    @pytest.mark.asyncio
    async def test_get_simulation_success(self, client):
        """Test successful simulation retrieval."""
        simulation_id = "test_sim_001"
        mock_response = {
            "success": True,
            "simulation_id": simulation_id,
            "status": "running",
            "progress": 0.5
        }

        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            mock_request.return_value.status_code = 200
            mock_request.return_value.headers = {'content-type': 'application/json'}
            mock_request.return_value.json.return_value = mock_response

            result = await client.get_simulation(simulation_id)

            assert result == mock_response
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_simulations_with_pagination(self, client):
        """Test simulation listing with pagination."""
        mock_response = {
            "simulations": [
                {"id": "sim_001", "name": "Test Sim 1"},
                {"id": "sim_002", "name": "Test Sim 2"}
            ],
            "total_count": 25,
            "page": 1,
            "page_size": 20
        }

        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            mock_request.return_value.status_code = 200
            mock_request.return_value.headers = {'content-type': 'application/json'}
            mock_request.return_value.json.return_value = mock_response

            result = await client.list_simulations(page=1, page_size=20)

            assert result == mock_response
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_simulation_success(self, client):
        """Test successful simulation execution."""
        simulation_id = "test_sim_001"
        mock_response = {
            "success": True,
            "message": "Simulation execution started"
        }

        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            mock_request.return_value.status_code = 202
            mock_request.return_value.headers = {'content-type': 'application/json'}
            mock_request.return_value.json.return_value = mock_response

            result = await client.execute_simulation(simulation_id)

            assert result == mock_response
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_reports_success(self, client):
        """Test successful report generation."""
        simulation_id = "test_sim_001"
        report_types = ["executive_summary", "technical_report"]
        mock_response = {
            "success": True,
            "reports": {
                "executive_summary": {"generated_at": "2024-01-01T12:00:00Z"},
                "technical_report": {"generated_at": "2024-01-01T12:00:00Z"}
            }
        }

        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            mock_request.return_value.status_code = 200
            mock_request.return_value.headers = {'content-type': 'application/json'}
            mock_request.return_value.json.return_value = mock_response

            result = await client.generate_reports(simulation_id, report_types)

            assert result == mock_response
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_simulation_events_with_filters(self, client):
        """Test simulation events retrieval with filters."""
        simulation_id = "test_sim_001"
        mock_response = {
            "events": [
                {
                    "event_id": "evt_001",
                    "event_type": "SimulationStarted",
                    "timestamp": "2024-01-01T12:00:00Z"
                }
            ],
            "total_count": 1
        }

        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            mock_request.return_value.status_code = 200
            mock_request.return_value.headers = {'content-type': 'application/json'}
            mock_request.return_value.json.return_value = mock_response

            result = await client.get_simulation_events(
                simulation_id=simulation_id,
                event_types=["SimulationStarted"],
                limit=10
            )

            assert result == mock_response
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_endpoints(self, client):
        """Test health check endpoints."""
        mock_response = {
            "status": "healthy",
            "service": "project-simulation",
            "version": "1.0.0"
        }

        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            mock_request.return_value.status_code = 200
            mock_request.return_value.headers = {'content-type': 'application/json'}
            mock_request.return_value.json.return_value = mock_response

            # Test basic health check
            result = await client.get_health()
            assert result == mock_response

            # Test detailed health check
            result = await client.get_detailed_health()
            assert result == mock_response

            # Test system health check
            result = await client.get_system_health()
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_timeout_handling(self, client):
        """Test timeout error handling."""
        with patch.object(client.client, 'request', side_effect=httpx.TimeoutException("Request timeout")):
            with pytest.raises(SimulationClientError, match="Request timeout"):
                await client.get_simulation("test_sim_001")

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, client):
        """Test connection error handling."""
        with patch.object(client.client, 'request', side_effect=httpx.ConnectError("Connection failed")):
            with pytest.raises(SimulationClientError, match="Connection error"):
                await client.list_simulations()

    @pytest.mark.asyncio
    async def test_cache_functionality(self, client):
        """Test response caching functionality."""
        simulation_id = "test_sim_001"
        mock_response = {
            "success": True,
            "simulation_id": simulation_id,
            "status": "running"
        }

        with patch.object(client.client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = Mock()
            mock_request.return_value.status_code = 200
            mock_request.return_value.headers = {'content-type': 'application/json'}
            mock_request.return_value.json.return_value = mock_response

            # First call should make HTTP request
            result1 = await client.get_simulation(simulation_id)
            assert mock_request.call_count == 1

            # Second call should use cache
            result2 = await client.get_simulation(simulation_id)
            assert mock_request.call_count == 1  # Still 1, cache was used

            assert result1 == result2 == mock_response

    def test_cache_management(self, client):
        """Test cache management methods."""
        # Add some mock cache entries
        client._cache["test_key"] = {"data": "test"}
        client._cache_timestamps["test_key"] = 1234567890.0

        assert len(client._cache) == 1
        assert "test_key" in client._cache

        # Clear cache
        client.clear_cache()

        assert len(client._cache) == 0
        assert len(client._cache_timestamps) == 0

    def test_simulation_cache_clearing(self, client):
        """Test simulation-specific cache clearing."""
        # Add mock cache entries for different simulations
        client._cache["GET|/api/v1/simulations/sim_001|"] = {"data": "sim1"}
        client._cache["GET|/api/v1/simulations/sim_002|"] = {"data": "sim2"}
        client._cache["GET|/api/v1/simulations/sim_001/execute|"] = {"data": "execute"}
        client._cache_timestamps.update({
            "GET|/api/v1/simulations/sim_001|": 1234567890.0,
            "GET|/api/v1/simulations/sim_002|": 1234567890.0,
            "GET|/api/v1/simulations/sim_001/execute|": 1234567890.0
        })

        # Clear cache for sim_001
        client.clear_simulation_cache("sim_001")

        # sim_001 entries should be cleared, sim_002 should remain
        assert "GET|/api/v1/simulations/sim_001|" not in client._cache
        assert "GET|/api/v1/simulations/sim_001/execute|" not in client._cache
        assert "GET|/api/v1/simulations/sim_002|" in client._cache
