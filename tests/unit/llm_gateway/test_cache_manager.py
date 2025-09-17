"""Unit tests for LLM Gateway Cache Manager.

Tests the intelligent caching functionality for LLM responses including
TTL-based expiration, pattern-based cache clearing, and cache analytics.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

# Adjust path for local imports
import sys
from pathlib import Path

# Add the LLM Gateway service directory to Python path
llm_gateway_path = Path(__file__).parent.parent.parent.parent / "services" / "llm-gateway"
sys.path.insert(0, str(llm_gateway_path))

from modules.cache_manager import CacheManager, CacheEntry

# Test markers for parallel execution
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.cache
]


class TestCacheManager:
    """Test suite for CacheManager class."""

    @pytest.fixture
    def cache_manager(self):
        """Create a CacheManager instance for testing."""
        return CacheManager()

    @pytest.fixture
    def mock_request(self):
        """Create a mock LLM request for testing."""
        return {
            "prompt": "Test prompt for caching",
            "provider": "ollama",
            "model": "llama3",
            "context": {"test": "context"},
            "user_id": "test_user",
            "temperature": 0.7,
            "max_tokens": 1024
        }

    def test_cache_manager_initialization(self, cache_manager):
        """Test that CacheManager initializes correctly."""
        assert isinstance(cache_manager, CacheManager)
        assert hasattr(cache_manager, 'cache')
        assert hasattr(cache_manager, 'max_size')
        assert hasattr(cache_manager, 'default_ttl')
        assert isinstance(cache_manager.cache, dict)

    def test_generate_cache_key(self, cache_manager, mock_request):
        """Test cache key generation."""
        key = cache_manager.generate_cache_key(mock_request)

        # Should generate a consistent SHA256 hash
        assert isinstance(key, str)
        assert len(key) == 64  # SHA256 hex length

        # Same request should generate same key
        key2 = cache_manager.generate_cache_key(mock_request)
        assert key == key2

        # Different request should generate different key
        different_request = mock_request.copy()
        different_request["prompt"] = "Different prompt"
        key3 = cache_manager.generate_cache_key(different_request)
        assert key != key3

    @pytest.mark.asyncio
    async def test_cache_response(self, cache_manager, mock_request):
        """Test caching a response."""
        cache_key = cache_manager.generate_cache_key(mock_request)
        response = "Test cached response"
        ttl = 3600

        await cache_manager.cache_response(cache_key, response, ttl)

        # Should be in cache
        assert cache_key in cache_manager.cache
        entry = cache_manager.cache[cache_key]

        assert isinstance(entry, CacheEntry)
        assert entry.response == response
        assert entry.ttl == ttl
        assert entry.access_count == 0
        assert not entry.is_expired()

    @pytest.mark.asyncio
    async def test_get_cached_response(self, cache_manager, mock_request):
        """Test retrieving a cached response."""
        cache_key = cache_manager.generate_cache_key(mock_request)
        response = "Test cached response"

        # Cache the response first
        await cache_manager.cache_response(cache_key, response)

        # Retrieve from cache
        cached_response = await cache_manager.get_cached_response(cache_key)

        assert cached_response == response

        # Entry should have been accessed
        entry = cache_manager.cache[cache_key]
        assert entry.access_count == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_cache_entry(self, cache_manager):
        """Test retrieving a non-existent cache entry."""
        cached_response = await cache_manager.get_cached_response("nonexistent_key")

        assert cached_response is None

    @pytest.mark.asyncio
    async def test_expired_cache_entry(self, cache_manager, mock_request):
        """Test handling of expired cache entries."""
        cache_key = cache_manager.generate_cache_key(mock_request)
        response = "Test cached response"

        # Cache with very short TTL
        await cache_manager.cache_response(cache_key, response, ttl=1)

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Try to retrieve expired entry
        cached_response = await cache_manager.get_cached_response(cache_key)

        # Should return None and remove expired entry
        assert cached_response is None
        assert cache_key not in cache_manager.cache

    @pytest.mark.asyncio
    async def test_clear_cache_by_pattern(self, cache_manager):
        """Test clearing cache entries by pattern."""
        # Cache multiple entries with similar keys
        entries = [
            ("user123_prompt1", "response1"),
            ("user123_prompt2", "response2"),
            ("user456_prompt1", "response3"),
            ("admin_prompt1", "response4")
        ]

        for key, response in entries:
            await cache_manager.cache_response(key, response)

        # Clear entries matching user123 pattern
        cleared_count = await cache_manager.clear_cache("user123")

        assert cleared_count == 2
        assert "user123_prompt1" not in cache_manager.cache
        assert "user123_prompt2" not in cache_manager.cache
        assert "user456_prompt1" in cache_manager.cache  # Should not be cleared
        assert "admin_prompt1" in cache_manager.cache    # Should not be cleared

    @pytest.mark.asyncio
    async def test_clear_all_cache(self, cache_manager):
        """Test clearing all cache entries."""
        # Cache multiple entries
        entries = [
            ("key1", "response1"),
            ("key2", "response2"),
            ("key3", "response3")
        ]

        for key, response in entries:
            await cache_manager.cache_response(key, response)

        # Clear all
        cleared_count = await cache_manager.clear_all()

        assert cleared_count == 3
        assert len(cache_manager.cache) == 0

    @pytest.mark.asyncio
    async def test_clear_expired_entries(self, cache_manager):
        """Test clearing only expired entries."""
        # Cache entries with different TTLs
        await cache_manager.cache_response("short_ttl", "response1", ttl=1)
        await cache_manager.cache_response("long_ttl", "response2", ttl=3600)

        # Wait for short TTL to expire
        await asyncio.sleep(1.1)

        # Clear expired entries
        cleared_count = await cache_manager.clear_expired()

        assert cleared_count == 1
        assert "short_ttl" not in cache_manager.cache
        assert "long_ttl" in cache_manager.cache

    def test_cache_entry_structure(self, cache_manager):
        """Test CacheEntry structure and methods."""
        entry = CacheEntry("test_key", "test_response", ttl=3600)

        assert entry.key == "test_key"
        assert entry.response == "test_response"
        assert entry.ttl == 3600
        assert entry.access_count == 0
        assert not entry.is_expired()

    def test_cache_entry_expiration(self, cache_manager):
        """Test CacheEntry expiration logic."""
        # Create entry with very short TTL
        entry = CacheEntry("test_key", "test_response", ttl=0.1)

        # Should not be expired immediately
        assert not entry.is_expired()

        # Wait for expiration
        time.sleep(0.2)

        # Should be expired now
        assert entry.is_expired()

    def test_cache_entry_access_tracking(self, cache_manager):
        """Test CacheEntry access tracking."""
        entry = CacheEntry("test_key", "test_response")

        assert entry.access_count == 0

        # Access the entry
        entry.access()

        assert entry.access_count == 1
        assert entry.last_accessed > entry.created_at

    def test_remaining_ttl_calculation(self, cache_manager):
        """Test remaining TTL calculation."""
        entry = CacheEntry("test_key", "test_response", ttl=10)

        # Should have remaining TTL initially
        remaining = entry.get_remaining_ttl()
        assert remaining > 0
        assert remaining <= 10

        # After expiration, should be 0
        time.sleep(11)
        remaining = entry.get_remaining_ttl()
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_eviction_on_cache_full(self, cache_manager):
        """Test cache eviction when cache is full."""
        # Set very small cache size for testing
        cache_manager.max_size = 2

        # Fill cache to capacity
        await cache_manager.cache_response("key1", "response1")
        await cache_manager.cache_response("key2", "response2")

        # Add one more (should trigger eviction)
        await cache_manager.cache_response("key3", "response3")

        # Cache should still have max_size entries
        assert len(cache_manager.cache) <= cache_manager.max_size

    def test_get_cache_stats_empty_cache(self, cache_manager):
        """Test cache statistics for empty cache."""
        stats = cache_manager.get_cache_stats()

        assert isinstance(stats, dict)
        assert stats["total_entries"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["oldest_entry_age"] == 0
        assert stats["newest_entry_age"] == 0
        assert stats["average_access_count"] == 0.0

    @pytest.mark.asyncio
    async def test_get_cache_stats_with_entries(self, cache_manager):
        """Test cache statistics with entries."""
        # Add some entries
        await cache_manager.cache_response("key1", "short response", ttl=3600)
        await cache_manager.cache_response("key2", "this is a longer response for testing", ttl=1800)

        stats = cache_manager.get_cache_stats()

        assert stats["total_entries"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["oldest_entry_age"] >= 0
        assert stats["newest_entry_age"] >= 0
        assert stats["average_access_count"] >= 0

    @pytest.mark.asyncio
    async def test_health_status_check(self, cache_manager):
        """Test cache health status checking."""
        # Add a test entry
        await cache_manager.cache_response("test_key", "test_response")

        health = await cache_manager.get_health_status()

        assert isinstance(health, dict)
        assert "status" in health
        assert "stats" in health
        assert "expired_entries_cleared" in health
        assert "last_cleanup" in health

    @pytest.mark.asyncio
    async def test_preload_cache(self, cache_manager):
        """Test cache preloading functionality."""
        preload_requests = [
            {"prompt": "What is Python?", "provider": "ollama"},
            {"prompt": "Explain machine learning", "provider": "ollama"}
        ]

        preloaded_count = await cache_manager.preload_cache(preload_requests)

        # Should have preloaded the specified entries
        assert preloaded_count == len(preload_requests)

        # Check that entries were added to cache
        for request in preload_requests:
            cache_key = cache_manager.generate_cache_key(request)
            assert cache_key in cache_manager.cache

    @pytest.mark.asyncio
    async def test_cache_key_consistency(self, cache_manager):
        """Test that cache keys are generated consistently."""
        request1 = {"prompt": "test", "provider": "ollama", "temperature": 0.7}
        request2 = {"prompt": "test", "provider": "ollama", "temperature": 0.7}

        key1 = cache_manager.generate_cache_key(request1)
        key2 = cache_manager.generate_cache_key(request2)

        assert key1 == key2

        # Different parameters should generate different keys
        request3 = {"prompt": "test", "provider": "openai", "temperature": 0.7}
        key3 = cache_manager.generate_cache_key(request3)

        assert key1 != key3

    @pytest.mark.asyncio
    async def test_cache_with_different_ttl(self, cache_manager):
        """Test caching with different TTL values."""
        # Cache with different TTLs
        await cache_manager.cache_response("short", "response1", ttl=1)
        await cache_manager.cache_response("medium", "response2", ttl=60)
        await cache_manager.cache_response("long", "response3", ttl=3600)

        # All should be present initially
        assert "short" in cache_manager.cache
        assert "medium" in cache_manager.cache
        assert "long" in cache_manager.cache

        # Wait for short TTL to expire
        await asyncio.sleep(1.1)

        # Clear expired entries
        await cache_manager.clear_expired()

        # Short TTL entry should be gone, others should remain
        assert "short" not in cache_manager.cache
        assert "medium" in cache_manager.cache
        assert "long" in cache_manager.cache
