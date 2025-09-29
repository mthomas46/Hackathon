"""Tests for Provider Manager"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from services.summarizer-hub.modules.provider_manager import ProviderManager


class TestProviderManager:
    """Test cases for ProviderManager."""

    @pytest.fixture
    def provider_manager(self):
        """Create ProviderManager instance."""
        return ProviderManager()

    def test_init(self, provider_manager):
        """Test provider manager initialization."""
        assert provider_manager.providers == {}
        assert provider_manager._cache == {}
        assert provider_manager._cache_ttl == 300  # 5 minutes

    @pytest.mark.asyncio
    async def test_register_provider(self, provider_manager):
        """Test provider registration."""
        mock_provider = Mock()
        mock_provider.name = "test_provider"

        await provider_manager.register_provider(mock_provider)

        assert "test_provider" in provider_manager.providers
        assert provider_manager.providers["test_provider"] == mock_provider

    @pytest.mark.asyncio
    async def test_get_provider_success(self, provider_manager):
        """Test successful provider retrieval."""
        mock_provider = Mock()
        mock_provider.name = "test_provider"
        provider_manager.providers["test_provider"] = mock_provider

        result = await provider_manager.get_provider("test_provider")

        assert result == mock_provider

    @pytest.mark.asyncio
    async def test_get_provider_not_found(self, provider_manager):
        """Test provider retrieval when provider doesn't exist."""
        with pytest.raises(ValueError, match="Provider 'nonexistent' not found"):
            await provider_manager.get_provider("nonexistent")

    @pytest.mark.asyncio
    async def test_list_providers(self, provider_manager):
        """Test listing all providers."""
        mock_provider1 = Mock()
        mock_provider1.name = "provider1"
        mock_provider2 = Mock()
        mock_provider2.name = "provider2"

        provider_manager.providers = {
            "provider1": mock_provider1,
            "provider2": mock_provider2
        }

        result = await provider_manager.list_providers()

        assert len(result) == 2
        assert "provider1" in result
        assert "provider2" in result

    @pytest.mark.asyncio
    async def test_test_provider_connection_success(self, provider_manager):
        """Test successful provider connection testing."""
        mock_provider = Mock()
        mock_provider.name = "test_provider"
        mock_provider.test_connection = AsyncMock(return_value=True)
        provider_manager.providers["test_provider"] = mock_provider

        result = await provider_manager.test_provider_connection("test_provider")

        assert result == True
        mock_provider.test_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_provider_connection_failure(self, provider_manager):
        """Test provider connection testing failure."""
        mock_provider = Mock()
        mock_provider.name = "test_provider"
        mock_provider.test_connection = AsyncMock(return_value=False)
        provider_manager.providers["test_provider"] = mock_provider

        result = await provider_manager.test_provider_connection("test_provider")

        assert result == False
        mock_provider.test_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_provider_health(self, provider_manager):
        """Test getting provider health status."""
        mock_provider = Mock()
        mock_provider.name = "test_provider"
        mock_provider.get_health_status = AsyncMock(return_value={"status": "healthy"})
        provider_manager.providers["test_provider"] = mock_provider

        result = await provider_manager.get_provider_health("test_provider")

        assert result == {"status": "healthy"}
        mock_provider.get_health_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarize_with_provider_success(self, provider_manager):
        """Test successful summarization with provider."""
        mock_provider = Mock()
        mock_provider.name = "test_provider"
        mock_provider.summarize = AsyncMock(return_value="Test summary")
        provider_manager.providers["test_provider"] = mock_provider

        result = await provider_manager.summarize_with_provider(
            "test_provider", "Test content", {"max_length": 100}
        )

        assert result == "Test summary"
        mock_provider.summarize.assert_called_once_with("Test content", {"max_length": 100})

    @pytest.mark.asyncio
    async def test_summarize_with_provider_error(self, provider_manager):
        """Test summarization with provider error."""
        mock_provider = Mock()
        mock_provider.name = "test_provider"
        mock_provider.summarize = AsyncMock(side_effect=Exception("Summarization failed"))
        provider_manager.providers["test_provider"] = mock_provider

        with pytest.raises(Exception, match="Summarization failed"):
            await provider_manager.summarize_with_provider(
                "test_provider", "Test content", {}
            )

    def test_is_cache_fresh_no_cache(self, provider_manager):
        """Test cache freshness when no cache exists."""
        assert not provider_manager._is_cache_fresh("test_key")

    def test_is_cache_fresh_expired(self, provider_manager):
        """Test cache freshness when cache is expired."""
        import time
        expired_time = time.time() - 400  # 400 seconds ago (past TTL)
        provider_manager._cache["test_key_timestamp"] = expired_time

        assert not provider_manager._is_cache_fresh("test_key")

    def test_is_cache_fresh_valid(self, provider_manager):
        """Test cache freshness when cache is still valid."""
        import time
        recent_time = time.time() - 100  # 100 seconds ago (within TTL)
        provider_manager._cache["test_key_timestamp"] = recent_time

        assert provider_manager._is_cache_fresh("test_key")

    def test_clear_cache(self, provider_manager):
        """Test cache clearing."""
        provider_manager._cache = {"key1": "value1", "key1_timestamp": 1234567890}
        provider_manager.providers = {"provider1": Mock()}

        provider_manager.clear_cache()

        assert provider_manager._cache == {}
        assert provider_manager.providers == {}  # Should also clear providers

    @pytest.mark.asyncio
    async def test_get_provider_stats(self, provider_manager):
        """Test getting provider statistics."""
        mock_provider1 = Mock()
        mock_provider1.name = "provider1"
        mock_provider1.get_stats = AsyncMock(return_value={"requests": 10})

        mock_provider2 = Mock()
        mock_provider2.name = "provider2"
        mock_provider2.get_stats = AsyncMock(return_value={"requests": 5})

        provider_manager.providers = {
            "provider1": mock_provider1,
            "provider2": mock_provider2
        }

        result = await provider_manager.get_provider_stats()

        assert len(result) == 2
        assert result["provider1"]["requests"] == 10
        assert result["provider2"]["requests"] == 5
