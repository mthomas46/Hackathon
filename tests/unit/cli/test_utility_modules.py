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
    def api_client(self):
        """APIClient instance for testing."""
        return APIClient(timeout=5.0, max_retries=2)

    def test_initialization(self, api_client):
        """Test APIClient initialization."""
        assert api_client.timeout == 5.0
        assert api_client.max_retries == 2
        assert api_client.session is None

    @pytest.mark.asyncio
    async def test_get_json_success(self, api_client):
        """Test successful JSON GET request."""
        mock_response_data = {"status": "success", "data": "test"}

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_get.return_value = mock_response

            result = await api_client.get_json("http://test.com/api")

            assert result == mock_response_data
            mock_get.assert_called_once_with("http://test.com/api", timeout=5.0)

    @pytest.mark.asyncio
    async def test_get_json_with_retry(self, api_client):
        """Test GET request with retry on failure."""
        mock_response_data = {"status": "success"}

        with patch('aiohttp.ClientSession.get') as mock_get:
            # First call fails, second succeeds
            mock_response_fail = AsyncMock()
            mock_response_fail.json = AsyncMock(side_effect=ClientError("Connection failed"))
            mock_response_fail.status = 500
            mock_response_fail.__aenter__ = AsyncMock(return_value=mock_response_fail)
            mock_response_fail.__aexit__ = AsyncMock(return_value=None)

            mock_response_success = AsyncMock()
            mock_response_success.json = AsyncMock(return_value=mock_response_data)
            mock_response_success.status = 200
            mock_response_success.__aenter__ = AsyncMock(return_value=mock_response_success)
            mock_response_success.__aexit__ = AsyncMock(return_value=None)

            mock_get.side_effect = [mock_response_fail, mock_response_success]

            result = await api_client.get_json("http://test.com/api")

            assert result == mock_response_data
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_get_json_max_retries_exceeded(self, api_client):
        """Test GET request when max retries exceeded."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(side_effect=ClientError("Persistent failure"))
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_get.return_value = mock_response

            with pytest.raises(ClientError, match="Persistent failure"):
                await api_client.get_json("http://test.com/api")

            assert mock_get.call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_post_json_success(self, api_client):
        """Test successful JSON POST request."""
        request_data = {"action": "test"}
        response_data = {"result": "success"}

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=response_data)
            mock_response.status = 200
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_post.return_value = mock_response

            result = await api_client.post_json("http://test.com/api", request_data)

            assert result == response_data
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "http://test.com/api"
            assert call_args[1]['json'] == request_data

    @pytest.mark.asyncio
    async def test_context_manager(self, api_client):
        """Test APIClient as context manager."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            async with api_client:
                # Should create session on enter
                mock_session_class.assert_called_once()

            # Should close session on exit
            mock_session.close.assert_called_once()


class TestErrorHandling:
    """Test error handling utilities."""

    def test_handle_cli_error(self):
        """Test CLI error handling."""
        with patch('services.cli.modules.utils.error_utils.fire_and_forget') as mock_fire:
            with patch('services.cli.modules.utils.error_utils.create_error_response') as mock_create_error:
                mock_create_error.return_value = {"error": "test error"}

                result = handle_cli_error("test_operation", ValueError("test error"), context="test")

                mock_fire.assert_called_once()
                mock_create_error.assert_called_once_with(
                    "Failed to test_operation",
                    error_code="INTERNAL_ERROR"
                )
                assert result == {"error": "test error"}


class TestMetricsUtils:
    """Test metrics utilities."""

    def test_log_cli_operation(self):
        """Test CLI operation logging."""
        with patch('services.cli.modules.utils.metrics_utils.fire_and_forget') as mock_fire:
            log_cli_operation("test_operation", param1="value1", param2="value2")

            mock_fire.assert_called_once()
            call_args = mock_fire.call_args
            assert call_args[0][1] == "CLI test_operation"
            assert "param1" in call_args[0][2]
            assert "param2" in call_args[0][2]

    def test_log_cli_command(self):
        """Test CLI command logging."""
        with patch('services.cli.modules.utils.metrics_utils.fire_and_forget') as mock_fire:
            log_cli_command("test_command", "arg1", "arg2")

            mock_fire.assert_called_once()
            call_args = mock_fire.call_args
            assert "test_command" in call_args[0][1]
            assert "arg1" in call_args[0][2]
            assert "arg2" in call_args[0][2]


class TestDRYIntegration:
    """Test integration of DRY utilities."""

    @pytest.fixture
    def integrated_setup(self):
        """Set up integrated test with all utilities."""
        cache = CacheManager()
        api_client = APIClient(timeout=1.0, max_retries=1)
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
