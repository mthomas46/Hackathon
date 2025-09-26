"""Tests for CLI utility modules (cache, API, error handling, metrics).

Tests the DRY utility modules that provide common functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from aiohttp import ClientError, ClientTimeout
import time

from services.cli.modules.utils.cache_utils import CacheManager
from services.cli.modules.utils.api_utils import APIClient
from services.cli.modules.utils.error_utils import handle_cli_error
from services.cli.modules.utils.metrics_utils import log_cli_operation, log_cli_command


class TestCacheManager:
    """Test CacheManager functionality."""

    @pytest.fixture
    def cache_manager(self):
        """CacheManager instance for testing."""
        return CacheManager()

    def test_initialization(self, cache_manager):
        """Test CacheManager initialization."""
        assert cache_manager.cache == {}
        assert hasattr(cache_manager, 'get')
        assert hasattr(cache_manager, 'set')
        assert hasattr(cache_manager, 'delete')
        assert hasattr(cache_manager, 'clear')

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_manager):
        """Test basic set and get operations."""
        await cache_manager.set("test_key", "test_value", 300)
        result = await cache_manager.get("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_manager):
        """Test getting nonexistent key."""
        result = await cache_manager.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache_manager):
        """Test TTL expiration."""
        # Set with very short TTL
        await cache_manager.set("short_key", "value", 0.1)

        # Should exist immediately
        result = await cache_manager.get("short_key")
        assert result == "value"

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Should be expired
        result = await cache_manager.get("short_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, cache_manager):
        """Test key deletion."""
        await cache_manager.set("delete_key", "value", 300)
        result = await cache_manager.get("delete_key")
        assert result == "value"

        await cache_manager.delete("delete_key")
        result = await cache_manager.get("delete_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_cache(self, cache_manager):
        """Test cache clearing."""
        await cache_manager.set("key1", "value1", 300)
        await cache_manager.set("key2", "value2", 300)

        # Verify both exist
        assert await cache_manager.get("key1") == "value1"
        assert await cache_manager.get("key2") == "value2"

        # Clear cache
        await cache_manager.clear()

        # Verify both are gone
        assert await cache_manager.get("key1") is None
        assert await cache_manager.get("key2") is None


class TestAPIClient:
    """Test APIClient functionality."""

    @pytest.fixture
    def api_client(self, mock_clients, mock_console):
        """APIClient instance for testing."""
        return APIClient(mock_clients, mock_console, timeout=5)

    def test_initialization(self, api_client, mock_clients, mock_console):
        """Test APIClient initialization."""
        assert api_client.timeout == 5
        assert api_client.clients == mock_clients
        assert api_client.console == mock_console

    @pytest.mark.asyncio
    async def test_get_json_success(self, api_client):
        """Test successful JSON GET request."""
        mock_response_data = {"status": "success", "data": "test"}

        api_client.clients.get_json = AsyncMock(return_value=mock_response_data)

        result = await api_client.get_json("http://test.com/api")

        assert result == mock_response_data
        api_client.clients.get_json.assert_called_once_with("http://test.com/api")

    @pytest.mark.asyncio
    async def test_get_json_with_retry(self, api_client):
        """Test GET request with timeout handling."""
        mock_response_data = {"status": "success"}

        api_client.clients.get_json = AsyncMock(return_value=mock_response_data)

        result = await api_client.get_json("http://test.com/api")

        assert result == mock_response_data
        api_client.clients.get_json.assert_called_once_with("http://test.com/api")

    @pytest.mark.asyncio
    async def test_get_json_max_retries_exceeded(self, api_client):
        """Test GET request error handling."""
        from aiohttp.client_exceptions import ClientError

        api_client.clients.get_json = AsyncMock(side_effect=ClientError("Connection failed"))

        result = await api_client.get_json("http://test.com/api")

        assert result is None  # APIClient returns None on errors
        api_client.clients.get_json.assert_called_once_with("http://test.com/api")

    @pytest.mark.asyncio
    async def test_post_json_success(self, api_client):
        """Test successful JSON POST request."""
        request_data = {"action": "test"}
        response_data = {"result": "success"}

        api_client.clients.post_json = AsyncMock(return_value=response_data)

        result = await api_client.post_json("http://test.com/api", request_data)

        assert result == response_data
        api_client.clients.post_json.assert_called_once_with("http://test.com/api", request_data)

    @pytest.mark.asyncio
    async def test_context_manager(self, api_client):
        """Test APIClient as context manager."""
        # Test that context manager methods exist and can be called
        result = await api_client.__aenter__()
        assert result == api_client

        await api_client.__aexit__(None, None, None)


class TestErrorHandling:
    """Test error handling utilities."""

    def test_handle_cli_error(self):
        """Test CLI error handling."""
        with patch('services.cli.modules.utils.error_utils.fire_and_forget') as mock_fire:
            result = handle_cli_error("test_operation", ValueError("test error"), context="test")

            mock_fire.assert_called_once()
            assert result['success'] is False
            assert result['error'] == 'unknown_error'
            assert 'test error' in result['message']


class TestMetricsUtils:
    """Test metrics utilities."""

    def test_log_cli_operation(self):
        """Test CLI operation logging."""
        with patch('services.cli.modules.utils.metrics_utils.fire_and_forget') as mock_fire:
            log_cli_operation("test_operation", param1="value1", param2="value2")

            mock_fire.assert_called_once()
            call_args = mock_fire.call_args
            assert call_args[0][1] == "CLI operation: test_operation"
            assert call_args[0][2] == "cli"  # service
            context = call_args[0][3]  # context dict
            assert context["operation"] == "test_operation"
            assert context["param1"] == "value1"
            assert context["param2"] == "value2"

    def test_log_cli_command(self):
        """Test CLI command logging."""
        with patch('services.cli.modules.utils.metrics_utils.fire_and_forget') as mock_fire:
            log_cli_command("test_command", {"arg1": "value1", "arg2": "value2"})

            mock_fire.assert_called_once()
            call_args = mock_fire.call_args
            assert call_args[0][1] == "CLI command: test_command"
            assert call_args[0][2] == "cli"  # service
            context = call_args[0][3]  # context dict
            assert context["command"] == "test_command"
            assert context["args"]["arg1"] == "value1"
            assert context["args"]["arg2"] == "value2"


class TestDRYIntegration:
    """Test integration of DRY utilities."""

    @pytest.fixture
    def integrated_setup(self, mock_clients, mock_console):
        """Set up integrated test with all utilities."""
        cache = CacheManager()
        api_client = APIClient(mock_clients, mock_console, timeout=1)
        return {
            'cache': cache,
            'api': api_client
        }

    @pytest.mark.asyncio
    async def test_cache_api_integration(self, integrated_setup):
        """Test cache and API integration."""
        cache = integrated_setup['cache']
        api = integrated_setup['api']

        # Cache a mock API response
        mock_response = {"data": "cached_response"}
        await cache.set("api_response", mock_response, 300)

        # Verify cache retrieval
        cached = await cache.get("api_response")
        assert cached == mock_response

    @pytest.mark.asyncio
    async def test_error_handling_with_cache(self, integrated_setup):
        """Test error handling combined with caching."""
        cache = integrated_setup['cache']

        # Test error handling when cache is empty
        result = await cache.get("nonexistent_key")
        assert result is None

        # Test successful cache operation after error
        await cache.set("recovery_key", "recovered_value", 300)
        result = await cache.get("recovery_key")
        assert result == "recovered_value"
