#!/usr/bin/env python3
"""
Tests for Intelligent Caching Module

Tests the advanced caching system with intelligent invalidation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from services.shared.caching.intelligent_caching import (
    CacheEntry,
    CacheConfig,
    IntelligentCache,
    CacheStrategy,
    CacheMetrics,
    DistributedCache
)


class TestCacheEntry:
    """Test cache entry functionality."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            ttl_seconds=300
        )

        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.ttl_seconds == 300
        assert entry.created_at is not None
        assert entry.access_count == 0

    def test_cache_entry_expiration(self):
        """Test cache entry expiration."""
        # Create entry that expires immediately
        entry = CacheEntry(
            key="test",
            value="value",
            ttl_seconds=0
        )

        assert entry.is_expired() is True

        # Create entry that doesn't expire
        entry = CacheEntry(
            key="test",
            value="value",
            ttl_seconds=3600
        )

        assert entry.is_expired() is False

    def test_cache_entry_access_tracking(self):
        """Test cache entry access tracking."""
        entry = CacheEntry(key="test", value="value")

        assert entry.access_count == 0
        assert entry.last_accessed is None

        # Access the entry
        _ = entry.value
        assert entry.access_count == 1
        assert entry.last_accessed is not None

        # Access again
        _ = entry.value
        assert entry.access_count == 2


class TestCacheConfig:
    """Test cache configuration."""

    def test_cache_config_creation(self):
        """Test creating cache configuration."""
        config = CacheConfig(
            max_size=1000,
            default_ttl=300,
            cleanup_interval=60
        )

        assert config.max_size == 1000
        assert config.default_ttl == 300
        assert config.cleanup_interval == 60

    def test_cache_config_defaults(self):
        """Test cache configuration defaults."""
        config = CacheConfig()

        assert config.max_size == 1000
        assert config.default_ttl == 300
        assert config.cleanup_interval == 60
        assert config.enable_metrics is True


class TestIntelligentCache:
    """Test intelligent cache functionality."""

    def test_cache_initialization(self):
        """Test cache initialization."""
        cache = IntelligentCache()

        assert len(cache.entries) == 0
        assert cache.config.max_size == 1000
        assert cache.metrics is not None

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = IntelligentCache()

        # Set a value
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Set with custom TTL
        cache.set("key2", "value2", ttl_seconds=60)
        assert cache.get("key2") == "value2"

    def test_cache_get_nonexistent(self):
        """Test getting non-existent cache entry."""
        cache = IntelligentCache()

        assert cache.get("nonexistent") is None

    def test_cache_delete(self):
        """Test cache entry deletion."""
        cache = IntelligentCache()

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.delete("key1")
        assert cache.get("key1") is None

    def test_cache_contains(self):
        """Test cache key existence check."""
        cache = IntelligentCache()

        assert cache.contains("key1") is False

        cache.set("key1", "value1")
        assert cache.contains("key1") is True

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = IntelligentCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache.entries) == 2

        cache.clear()
        assert len(cache.entries) == 0

    def test_cache_size_limit(self):
        """Test cache size limit enforcement."""
        config = CacheConfig(max_size=2)
        cache = IntelligentCache(config)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache.entries) == 2

        # Adding third item should trigger eviction
        cache.set("key3", "value3")
        assert len(cache.entries) == 2  # Should evict one entry

    def test_cache_expiration(self):
        """Test cache entry expiration."""
        cache = IntelligentCache()

        # Set entry with very short TTL
        cache.set("short_ttl", "value", ttl_seconds=0)
        assert cache.get("short_ttl") is None  # Should be expired immediately

    def test_cache_metrics(self):
        """Test cache metrics collection."""
        cache = IntelligentCache()

        # Initial metrics
        assert cache.metrics.hits == 0
        assert cache.metrics.misses == 0

        # Cache miss
        cache.get("nonexistent")
        assert cache.metrics.misses == 1

        # Cache hit
        cache.set("key1", "value1")
        cache.get("key1")
        assert cache.metrics.hits == 1

        # Cache set
        assert cache.metrics.sets == 1


class TestCacheStrategy:
    """Test cache replacement strategies."""

    def test_lru_strategy(self):
        """Test LRU (Least Recently Used) strategy."""
        strategy = CacheStrategy.LRU

        # Test with small cache
        config = CacheConfig(max_size=2)
        cache = IntelligentCache(config, strategy=strategy)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Access key1 to make it most recently used
        cache.get("key1")

        # Add third item, should evict key2 (least recently used)
        cache.set("key3", "value3")

        assert cache.contains("key1") is True
        assert cache.contains("key2") is False
        assert cache.contains("key3") is True

    def test_lfu_strategy(self):
        """Test LFU (Least Frequently Used) strategy."""
        strategy = CacheStrategy.LFU

        config = CacheConfig(max_size=2)
        cache = IntelligentCache(config, strategy=strategy)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Access key1 multiple times to increase frequency
        cache.get("key1")
        cache.get("key1")

        # Access key2 once
        cache.get("key2")

        # Add third item, should evict key2 (least frequently used)
        cache.set("key3", "value3")

        assert cache.contains("key1") is True
        assert cache.contains("key2") is False
        assert cache.contains("key3") is True


class TestDistributedCache:
    """Test distributed cache functionality."""

    @pytest.mark.asyncio
    async def test_distributed_cache_initialization(self):
        """Test distributed cache initialization."""
        with patch('redis.asyncio.Redis') as mock_redis:
            cache = DistributedCache(redis_url="redis://localhost:6379")

            assert cache.redis_url == "redis://localhost:6379"
            assert cache.redis_client is not None

    @pytest.mark.asyncio
    async def test_distributed_cache_set_get(self):
        """Test distributed cache set and get operations."""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.set.return_value = True
            mock_client.get.return_value = b"test_value"

            cache = DistributedCache()
            await cache.set("key1", "test_value")
            result = await cache.get("key1")

            assert result == "test_value"
            mock_client.set.assert_called_once()
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_distributed_cache_delete(self):
        """Test distributed cache delete operation."""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.delete.return_value = 1

            cache = DistributedCache()
            result = await cache.delete("key1")

            assert result is True
            mock_client.delete.assert_called_once_with("key1")

    @pytest.mark.asyncio
    async def test_distributed_cache_connection_failure(self):
        """Test distributed cache behavior on connection failure."""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.get.side_effect = Exception("Connection failed")

            cache = DistributedCache()

            # Should return None on connection failure
            result = await cache.get("key1")
            assert result is None


class TestCacheMetrics:
    """Test cache metrics functionality."""

    def test_cache_metrics_initialization(self):
        """Test cache metrics initialization."""
        metrics = CacheMetrics()

        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.sets == 0
        assert metrics.deletes == 0
        assert metrics.evictions == 0

    def test_cache_metrics_operations(self):
        """Test cache metrics operation tracking."""
        metrics = CacheMetrics()

        metrics.record_hit()
        metrics.record_hit()
        assert metrics.hits == 2

        metrics.record_miss()
        assert metrics.misses == 1

        metrics.record_set()
        assert metrics.sets == 1

        metrics.record_delete()
        assert metrics.deletes == 1

        metrics.record_eviction()
        assert metrics.evictions == 1

    def test_cache_metrics_hit_rate(self):
        """Test cache hit rate calculation."""
        metrics = CacheMetrics()

        # No operations yet
        assert metrics.hit_rate == 0.0

        # Record some hits and misses
        metrics.record_hit()
        metrics.record_hit()
        metrics.record_miss()

        assert metrics.hit_rate == 2.0 / 3.0  # 2 hits out of 3 accesses

    def test_cache_metrics_summary(self):
        """Test cache metrics summary generation."""
        metrics = CacheMetrics()

        metrics.record_hit()
        metrics.record_miss()
        metrics.record_set()

        summary = metrics.get_summary()
        assert summary["hits"] == 1
        assert summary["misses"] == 1
        assert summary["sets"] == 1
        assert summary["hit_rate"] == 0.5
        assert "total_operations" in summary


if __name__ == "__main__":
    pytest.main([__file__])
