"""Tests for Doc Store caching functionality.

Tests Redis-based caching, cache invalidation, performance monitoring,
and fallback mechanisms for the doc store service.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import pytest

# Setup path for direct imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import modules directly
import importlib.util
spec = importlib.util.spec_from_file_location("caching", PROJECT_ROOT / "services" / "doc_store" / "modules" / "caching.py")
caching_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(caching_module)

DocStoreCache = caching_module.DocStoreCache
docstore_cache = caching_module.docstore_cache


class TestDocStoreCache:
    """Test DocStoreCache class functionality."""

    @pytest.fixture
    def cache(self):
        """Create a test cache instance."""
        return DocStoreCache()

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        return Mock()

    def test_cache_initialization(self, cache):
        """Test cache initialization."""
        assert cache.redis_client is None
        assert cache.local_cache == {}
        assert cache.stats.total_hits == 0
        assert cache.stats.total_misses == 0

    @pytest.mark.asyncio
    async def test_redis_connection_success(self, cache, mock_redis):
        """Test successful Redis connection."""
        # Temporarily set REDIS_AVAILABLE to True
        original_available = caching_module.REDIS_AVAILABLE
        caching_module.REDIS_AVAILABLE = True
        try:
            # Mock the Redis class in the caching module
            with patch.object(caching_module, 'aioredis') as mock_aioredis:
                mock_aioredis.from_url.return_value = mock_redis
                mock_redis.config_set = AsyncMock(return_value=None)

                result = await cache.initialize()
                assert result is True
                assert cache.redis_client is not None
        finally:
            caching_module.REDIS_AVAILABLE = original_available

    @patch('redis.asyncio.Redis')
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, mock_redis_class, cache):
        """Test Redis connection failure fallback."""
        with patch.object(caching_module, 'REDIS_AVAILABLE', True):
            mock_redis_class.from_url.side_effect = Exception("Connection failed")

            result = await cache.initialize()
            assert result is False
            assert cache.redis_client is None

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache, mock_redis):
        """Test cache hit scenario."""
        cache.redis_client = mock_redis
        # Generate the expected cache key
        expected_key = cache._generate_cache_key("test_operation", {"param": "value"})
        mock_redis.get = AsyncMock(return_value=b'{"test": "data"}')
        mock_redis.hincrby = AsyncMock(return_value=None)
        mock_redis.hset = AsyncMock(return_value=None)

        result = await cache.get("test_operation", {"param": "value"}, tags=["tag1"])

        assert result == {"test": "data"}
        assert cache.stats.total_hits == 1
        assert cache.stats.total_misses == 0
        mock_redis.get.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache, mock_redis):
        """Test cache miss scenario."""
        cache.redis_client = mock_redis
        mock_redis.get.return_value = None

        result = await cache.get("test_key", {"param": "value"}, tags=["tag1"])

        assert result is None
        assert cache.stats.total_hits == 0
        assert cache.stats.total_misses == 1

    @pytest.mark.asyncio
    async def test_get_redis_error_fallback(self, cache, mock_redis):
        """Test Redis error with local cache fallback."""
        cache.redis_client = mock_redis
        # Generate the cache key and set up local cache with proper CacheEntry
        cache_key = cache._generate_cache_key("local_key", {})
        from datetime import datetime, timedelta
        from services.shared.utilities import utc_now
        # Use a recent created_at time to ensure TTL check passes
        past_time = utc_now() - timedelta(seconds=10)  # 10 seconds ago
        cache.local_cache[cache_key] = caching_module.CacheEntry(
            key=cache_key,
            value={"local": "data"},
            ttl=3600,  # 1 hour
            created_at=past_time,
            hits=0,
            last_accessed=past_time
        )
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))

        result = await cache.get("local_key", {}, tags=["tag1"])

        assert result == {"local": "data"}

    @pytest.mark.asyncio
    async def test_set_cache_success(self, cache, mock_redis):
        """Test successful cache set operation."""
        with patch.object(caching_module, 'REDIS_AVAILABLE', True):
            cache.redis_client = mock_redis
            mock_redis.setex = AsyncMock(return_value=None)
            mock_redis.hset = AsyncMock(return_value=None)
            mock_redis.expire = AsyncMock(return_value=None)
            mock_redis.sadd = AsyncMock(return_value=None)

            result = await cache.set("test_operation", {"param": "value"}, {"test": "data"}, ttl=300, tags=["tag1"])

            assert result is True
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_cache_redis_failure(self, cache, mock_redis):
        """Test cache set with Redis failure."""
        with patch.object(caching_module, 'REDIS_AVAILABLE', True):
            cache.redis_client = mock_redis
            mock_redis.setex = AsyncMock(side_effect=Exception("Redis error"))

            result = await cache.set("test_key", {"param": "value"}, {"test": "data"}, ttl=300, tags=["tag1"])

            assert result is True  # Should succeed with local cache
            # Check that data is in local cache with proper key
            cache_key = cache._generate_cache_key("test_key", {"param": "value"})
            assert cache_key in cache.local_cache
            assert cache.local_cache[cache_key].value == {"test": "data"}

    @pytest.mark.asyncio
    async def test_invalidate_tags(self, cache, mock_redis):
        """Test tag-based cache invalidation."""
        cache.redis_client = mock_redis
        mock_redis.smembers.return_value = ["key1", "key3"]
        mock_redis.delete.return_value = None

        # Add some local cache entries
        cache.local_cache = {"key1": "data1", "key2": "data2", "key3": "data3"}

        result = await cache.invalidate(tags=["tag1"])

        # Should return number of invalidated keys
        assert result >= 0
        mock_redis.smembers.assert_called_with("docstore:cache:tag:tag1")

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, cache, mock_redis):
        """Test cache statistics retrieval."""
        cache.redis_client = mock_redis
        cache.stats.total_hits = 42
        cache.stats.total_misses = 8
        cache.local_cache = {"key1": "data1", "key2": "data2"}
        mock_redis.info = AsyncMock(return_value={"used_memory": 1000, "total_connections_received": 5, "connected_clients": 2})
        mock_redis.dbsize = AsyncMock(return_value=10)

        stats = await cache.get_stats()

        # Check if it's an error response
        if "error" in stats:
            print(f"Stats error: {stats['error']}")
            assert False, f"get_stats returned error: {stats['error']}"

        assert stats["total_hits"] == 42
        assert stats["total_misses"] == 8
        assert stats["hit_rate_percent"] == 84.0  # 42 / (42 + 8) * 100
        assert stats["local_cache_entries"] == 2
        assert "uptime_seconds" in stats
        assert "redis_stats" in stats

    @pytest.mark.asyncio
    async def test_cache_operations_workflow(self, cache, mock_redis):
        """Test complete cache operations workflow."""
        with patch.object(caching_module, 'REDIS_AVAILABLE', True):
            cache.redis_client = mock_redis
            mock_redis.get = AsyncMock(return_value=None)  # Cache miss
            mock_redis.setex = AsyncMock(return_value=None)
            mock_redis.hset = AsyncMock(return_value=None)
            mock_redis.expire = AsyncMock(return_value=None)

            # Test cache miss
            result = await cache.get("test_op", {"param": "value"})
            assert result is None
            assert cache.stats.total_misses == 1

            # Test cache set
            success = await cache.set("test_op", {"param": "value"}, {"data": "test"}, ttl=300)
            assert success is True


class TestDocStoreCacheIntegration:
    """Test cache integration with doc store operations."""

    @pytest.fixture
    def docstore_cache(self):
        """Create a real DocStoreCache instance for integration tests."""
        return caching_module.DocStoreCache()

    @pytest.mark.asyncio
    async def test_document_caching_workflow(self, docstore_cache, mock_redis):
        """Test complete caching workflow for document operations."""
        docstore_cache.redis_client = mock_redis
        mock_redis.get = AsyncMock(return_value=None)  # Initial miss
        mock_redis.setex = AsyncMock(return_value=None)
        mock_redis.hset = AsyncMock(return_value=None)
        mock_redis.expire = AsyncMock(return_value=None)
        mock_redis.hincrby = AsyncMock(return_value=None)

        # Simulate document retrieval with caching
        doc_data = {"id": "test-doc", "content": "test content"}

        # First call - cache miss
        await docstore_cache.set("documents", {"id": "test-doc"}, doc_data, ttl=300, tags=["documents"])

        # Mock cache hit for second call
        mock_redis.get = AsyncMock(return_value=b'{"id": "test-doc", "content": "test content"}')
        cached_result = await docstore_cache.get("documents", {"id": "test-doc"}, tags=["documents"])

        assert cached_result == doc_data

        # Check stats
        stats = await docstore_cache.get_stats()
        if "error" not in stats:
            assert stats["total_hits"] == 1

    @pytest.mark.asyncio
    async def test_search_caching(self, docstore_cache, mock_redis):
        """Test search result caching."""
        docstore_cache.redis_client = mock_redis
        mock_redis.get = AsyncMock(return_value=None)  # Initial miss
        mock_redis.setex = AsyncMock(return_value=None)
        mock_redis.hset = AsyncMock(return_value=None)
        mock_redis.expire = AsyncMock(return_value=None)

        search_params = {"q": "test query", "limit": 20}
        search_results = {"items": [{"id": "doc1"}, {"id": "doc2"}]}

        # Cache search results
        await docstore_cache.set("search", search_params, search_results, ttl=600, tags=["search"])

        # Mock cache hit
        mock_redis.get = AsyncMock(return_value=b'{"items": [{"id": "doc1"}, {"id": "doc2"}]}')
        mock_redis.hincrby = AsyncMock(return_value=None)

        # Retrieve from cache
        cached_results = await docstore_cache.get("search", search_params, tags=["search"])

        assert cached_results == search_results

    @pytest.mark.asyncio
    async def test_tag_invalidation_cascade(self, docstore_cache, mock_redis):
        """Test that tag invalidation properly cascades."""
        docstore_cache.redis_client = mock_redis
        mock_redis.smembers = AsyncMock(return_value=["docstore:cache:documents:id:1", "docstore:cache:search:user"])
        mock_redis.delete = AsyncMock(return_value=None)

        # Mock the tag invalidation
        result = await docstore_cache.invalidate(tags=["user:alice"])

        # Should attempt to delete keys
        assert mock_redis.smembers.called
        assert mock_redis.delete.called
