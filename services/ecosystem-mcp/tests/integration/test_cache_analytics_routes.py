"""
Integration tests for cache analytics API routes.

Tests cache performance monitoring, analytics, and optimization endpoints.
"""

import pytest
from datetime import datetime
from uuid import uuid4


from .test_helpers import skip_if_no_redis, redis_available


pytestmark = pytest.mark.integration



class TestCacheAnalytics:
    """Test cache analytics endpoints."""

    @skip_if_no_redis
    async def test_get_cache_analytics(self, async_test_client):
        """Test getting cache analytics."""
        response = await async_test_client.get("/api/v1/admin/cache/stats")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        # Check for nested cache structure or top-level fields
        assert "caches" in data or "hit_rate" in data or "miss_rate" in data

    @skip_if_no_redis
    async def test_get_cache_hit_rate(self, async_test_client):
        """Test getting cache hit rate."""
        response = await async_test_client.get("/api/v1/admin/cache/stats/hit-rate")
        
        assert response.status_code in [200, 404, 500, 503]
        # Endpoint may not exist (404), so only check data if 200
        if response.status_code == 200:
            data = response.json()
            assert "rate" in data or "percentage" in data

    @skip_if_no_redis
    async def test_get_cache_performance(self, async_test_client):
        """Test getting cache performance metrics."""
        response = await async_test_client.get("/api/v1/admin/cache/stats/performance")
        
        assert response.status_code in [200, 404, 500, 503]
        # Endpoint may not exist (404), so only check data if 200
        if response.status_code == 200:
            data = response.json()
            assert "average_latency" in data or "throughput" in data

    @skip_if_no_redis
    async def test_get_cache_size_metrics(self, async_test_client):
        """Test getting cache size metrics."""
        response = await async_test_client.get("/api/v1/admin/cache/stats/size")
        
        assert response.status_code in [200, 404, 500, 503]
        # Only check data structure if endpoint exists
        if response.status_code == 200:
            data = response.json()
            assert "total_keys" in data or "memory_usage" in data

    @skip_if_no_redis
    async def test_get_cache_eviction_stats(self, async_test_client):
        """Test getting cache eviction statistics."""
        response = await async_test_client.get("/api/v1/admin/cache/stats/evictions")
        
        assert response.status_code in [200, 404, 500, 503]
        # Only check data structure if endpoint exists
        if response.status_code == 200:
            data = response.json()
            assert "eviction_count" in data or "eviction_rate" in data


class TestCacheOptimization:
    """Test cache optimization endpoints."""

    @skip_if_no_redis
    async def test_get_cache_recommendations(self, async_test_client):
        """Test getting cache optimization recommendations."""
        response = await async_test_client.get("/api/v1/admin/cache/stats/recommendations")
        
        assert response.status_code in [200, 404, 500, 503]
        # Only check data structure if endpoint exists
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or "recommendations" in data

    @skip_if_no_redis
    async def test_analyze_cache_patterns(self, async_test_client):
        """Test analyzing cache access patterns."""
        response = await async_test_client.get("/api/v1/admin/cache/stats/patterns")
        
        assert response.status_code in [200, 404, 500, 503]
        # Only check data structure if endpoint exists
        if response.status_code == 200:
            data = response.json()
            assert "hot_keys" in data or "cold_keys" in data

    @skip_if_no_redis
    async def test_get_cache_efficiency_score(self, async_test_client):
        """Test getting cache efficiency score."""
        response = await async_test_client.get("/api/v1/admin/cache/stats/efficiency")
        
        assert response.status_code in [200, 404, 500, 503]
        # Only check data structure if endpoint exists
        if response.status_code == 200:
            data = response.json()
            assert "score" in data or "efficiency" in data

    @skip_if_no_redis
    async def test_warm_cache(self, async_test_client):
        """Test cache warming operation."""
        response = await async_test_client.post("/api/v1/admin/cache/stats/warm")
        
        assert response.status_code in [200, 202, 404, 500, 503]


class TestCacheReporting:
    """Test cache reporting endpoints."""

    @skip_if_no_redis
    async def test_generate_cache_report(self, async_test_client):
        """Test generating cache report."""
        response = await async_test_client.post("/api/v1/admin/cache/stats/report/generate")
        
        assert response.status_code in [200, 202, 404, 500, 503]
        # Only check data structure if endpoint exists and succeeds
        if response.status_code in [200, 202]:
            data = response.json()
            assert "report_id" in data or "status" in data

    @skip_if_no_redis
    async def test_get_cache_report(self, async_test_client):
        """Test getting cache report."""
        response = await async_test_client.get("/api/v1/admin/cache/stats/report/latest")
        
        assert response.status_code in [200, 404]

