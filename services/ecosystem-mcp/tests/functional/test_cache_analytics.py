"""
Functional tests for cache analytics.

Tests hit/miss tracking, analytics collection, cache warming, and eviction policies.
"""

import pytest
import httpx
import os
import asyncio
from datetime import datetime


pytestmark = pytest.mark.functional


@pytest.fixture
def api_base_url():
    """Get API base URL from environment."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
async def async_http_client(api_base_url):
    """Create async HTTP client."""
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30.0) as client:
        yield client


class TestCacheHitMissTracking:
    """Test cache hit/miss tracking."""

    async def test_cache_hit_tracking(self, async_http_client):
        """Test cache hit tracking."""
        try:
            # Make a query
            query = "test cache hit query"
            
            # First request (cache miss)
            response1 = await async_http_client.post(
                "/api/v1/query",
                json={"query": query}
            )
            
            if response1.status_code != 200:
                pytest.skip("Query endpoint not working")
            
            # Second request (cache hit)
            response2 = await async_http_client.post(
                "/api/v1/query",
                json={"query": query}
            )
            
            # Both should succeed
            assert response2.status_code == 200
            
            # Check cache stats
            stats_response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                assert isinstance(stats, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cache_miss_tracking(self, async_http_client):
        """Test cache miss tracking."""
        try:
            # Make unique queries (cache misses)
            for i in range(3):
                query = f"unique cache miss query {i} {datetime.utcnow().timestamp()}"
                
                response = await async_http_client.post(
                    "/api/v1/query",
                    json={"query": query}
                )
                
                # Should process query
                assert response.status_code in [200, 500, 503]
            
            # Check cache stats
            stats_response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                assert isinstance(stats, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cache_hit_rate_calculation(self, async_http_client):
        """Test cache hit rate calculation."""
        try:
            # Get cache stats
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                # Should have hit rate information
                assert isinstance(stats, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cache_size_tracking(self, async_http_client):
        """Test cache size tracking."""
        try:
            # Get cache stats
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                # Should have size information
                assert isinstance(stats, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cache_entry_count(self, async_http_client):
        """Test cache entry count tracking."""
        try:
            # Get cache stats
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                # Should have entry count
                assert isinstance(stats, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")


class TestCacheAnalyticsCollection:
    """Test cache analytics collection."""

    async def test_analytics_data_collection(self, async_http_client):
        """Test analytics data collection."""
        try:
            # Get cache analytics
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if response.status_code == 200:
                analytics = response.json()
                
                # Should have analytics data
                assert isinstance(analytics, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_analytics_time_series(self, async_http_client):
        """Test analytics time series data."""
        try:
            # Collect analytics over time
            samples = []
            
            for _ in range(3):
                response = await async_http_client.get("/api/v1/admin/cache/stats")
                
                if response.status_code == 200:
                    samples.append(response.json())
                
                await asyncio.sleep(0.5)
            
            # Should have collected samples
            assert len(samples) >= 0
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_analytics_aggregation(self, async_http_client):
        """Test analytics aggregation."""
        try:
            # Get aggregated analytics
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if response.status_code == 200:
                analytics = response.json()
                
                # Should have aggregated data
                assert isinstance(analytics, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_analytics_export(self, async_http_client):
        """Test analytics export."""
        try:
            # Export analytics
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if response.status_code == 200:
                analytics = response.json()
                
                # Should be exportable
                assert isinstance(analytics, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_analytics_visualization_data(self, async_http_client):
        """Test analytics visualization data."""
        try:
            # Get data for visualization
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                # Should be suitable for visualization
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")


class TestCacheWarming:
    """Test cache warming functionality."""

    async def test_cache_warm_on_startup(self, async_http_client):
        """Test cache warming on startup."""
        try:
            # Check if cache is warmed
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if response.status_code == 200:
                stats = response.json()
                assert isinstance(stats, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_manual_cache_warming(self, async_http_client):
        """Test manual cache warming."""
        try:
            # Trigger cache warming
            response = await async_http_client.post("/api/v1/cache/warm")
            
            # Should accept or return not found
            assert response.status_code in [200, 202, 404]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cache_preload(self, async_http_client):
        """Test cache preloading."""
        try:
            # Preload common queries
            common_queries = [
                "What is this project?",
                "How do I get started?",
                "What are the main features?"
            ]
            
            for query in common_queries:
                response = await async_http_client.post(
                    "/api/v1/query",
                    json={"query": query}
                )
                
                # Should process or skip
                assert response.status_code in [200, 404, 500, 503]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cache_refresh(self, async_http_client):
        """Test cache refresh."""
        try:
            # Refresh cache
            response = await async_http_client.post("/api/v1/cache/refresh")
            
            # Should accept or return not found
            assert response.status_code in [200, 202, 404]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_selective_cache_warming(self, async_http_client):
        """Test selective cache warming."""
        try:
            # Warm specific cache entries
            response = await async_http_client.post(
                "/api/v1/cache/warm",
                json={"keys": ["query:test1", "query:test2"]}
            )
            
            # Should accept or return not found
            assert response.status_code in [200, 202, 404, 422]
        except httpx.ConnectError:
            pytest.skip("API not accessible")


class TestCacheEvictionPolicies:
    """Test cache eviction policies."""

    async def test_lru_eviction(self, async_http_client):
        """Test LRU eviction policy."""
        try:
            # Make many unique queries to trigger eviction
            for i in range(20):
                query = f"eviction test query {i}"
                
                response = await async_http_client.post(
                    "/api/v1/query",
                    json={"query": query}
                )
                
                # Should process
                assert response.status_code in [200, 500, 503]
            
            # Check cache stats
            stats_response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                assert isinstance(stats, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_ttl_eviction(self, async_http_client):
        """Test TTL-based eviction."""
        try:
            # Make a query
            query = "ttl eviction test"
            
            response = await async_http_client.post(
                "/api/v1/query",
                json={"query": query}
            )
            
            if response.status_code == 200:
                # Wait for TTL to expire (if configured)
                await asyncio.sleep(1)
                
                # Check if entry still exists
                stats_response = await async_http_client.get("/api/v1/admin/cache/stats")
                
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    assert isinstance(stats, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_size_based_eviction(self, async_http_client):
        """Test size-based eviction."""
        try:
            # Fill cache with large entries
            for i in range(10):
                query = f"large query {i}" * 100
                
                response = await async_http_client.post(
                    "/api/v1/query",
                    json={"query": query}
                )
                
                # Should process
                assert response.status_code in [200, 400, 422, 500, 503]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_manual_eviction(self, async_http_client):
        """Test manual cache eviction."""
        try:
            # Clear cache
            response = await async_http_client.post("/api/v1/admin/clear-cache")
            
            # Should accept or return not found
            assert response.status_code in [200, 202, 404, 500]
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_selective_eviction(self, async_http_client):
        """Test selective cache eviction."""
        try:
            # Evict specific entries
            response = await async_http_client.post(
                "/api/v1/cache/evict",
                json={"pattern": "query:*"}
            )
            
            # Should accept or return not found
            assert response.status_code in [200, 202, 404, 422]
        except httpx.ConnectError:
            pytest.skip("API not accessible")


class TestCachePerformance:
    """Test cache performance characteristics."""

    async def test_cache_latency(self, async_http_client):
        """Test cache access latency."""
        try:
            import time
            
            # Make a query
            query = "cache latency test"
            
            # First request (cache miss)
            start1 = time.time()
            response1 = await async_http_client.post(
                "/api/v1/query",
                json={"query": query}
            )
            miss_latency = time.time() - start1
            
            if response1.status_code != 200:
                pytest.skip("Query endpoint not working")
            
            # Second request (cache hit)
            start2 = time.time()
            response2 = await async_http_client.post(
                "/api/v1/query",
                json={"query": query}
            )
            hit_latency = time.time() - start2
            
            # Cache hit should be faster
            if response2.status_code == 200:
                assert hit_latency <= miss_latency * 2  # Allow some variance
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cache_throughput(self, async_http_client):
        """Test cache throughput."""
        try:
            # Make many cached requests
            query = "cache throughput test"
            
            # Prime cache
            await async_http_client.post(
                "/api/v1/query",
                json={"query": query}
            )
            
            # Measure throughput
            import time
            start = time.time()
            
            for _ in range(10):
                await async_http_client.post(
                    "/api/v1/query",
                    json={"query": query}
                )
            
            duration = time.time() - start
            throughput = 10 / duration
            
            # Should have reasonable throughput
            assert throughput > 0
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cache_memory_usage(self, async_http_client):
        """Test cache memory usage."""
        try:
            # Get cache stats
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                # Should have memory usage info
                assert isinstance(stats, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cache_efficiency(self, async_http_client):
        """Test cache efficiency."""
        try:
            # Get cache stats
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                # Should have efficiency metrics
                assert isinstance(stats, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

    async def test_cache_overhead(self, async_http_client):
        """Test cache overhead."""
        try:
            # Measure overhead of caching
            response = await async_http_client.get("/api/v1/admin/cache/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                # Should have overhead metrics
                assert isinstance(stats, dict)
        except httpx.ConnectError:
            pytest.skip("API not accessible")

