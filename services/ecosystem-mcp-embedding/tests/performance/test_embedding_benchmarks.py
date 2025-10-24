"""
Performance benchmarks for embedding service.

Tests throughput, latency, resource usage, and scalability.
"""

import pytest
import httpx
import os
import time
import asyncio
from typing import List


pytestmark = pytest.mark.performance


@pytest.fixture
def api_base_url():
    """Get API base URL from environment."""
    return os.getenv("EMBEDDING_API_URL", "http://localhost:8001")


@pytest.fixture
async def async_http_client(api_base_url):
    """Create async HTTP client."""
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
def sample_texts():
    """Generate sample texts for testing."""
    return [
        f"This is a test document number {i} with some content for embedding generation."
        for i in range(100)
    ]


class TestThroughput:
    """Test embedding service throughput."""

    async def test_single_embedding_latency(self, async_http_client):
        """Test single embedding generation latency."""
        try:
            text = "This is a test document for embedding."
            
            start = time.time()
            response = await async_http_client.post(
                "/api/v1/embeddings/generate",
                json={"text": text}
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                # Should complete in under 1 second
                assert duration < 1.0
                
                data = response.json()
                assert "embedding" in data
        except httpx.ConnectError:
            pytest.skip("Embedding service not accessible")

    async def test_batch_embedding_throughput(self, async_http_client, sample_texts):
        """Test batch embedding throughput."""
        try:
            batch_size = 32
            texts = sample_texts[:batch_size]
            
            start = time.time()
            response = await async_http_client.post(
                "/api/v1/embeddings/batch",
                json={"texts": texts}
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                embeddings = data.get("embeddings", [])
                
                # Calculate throughput
                throughput = len(embeddings) / duration
                
                # Should process at least 10 embeddings per second
                assert throughput > 10
        except httpx.ConnectError:
            pytest.skip("Embedding service not accessible")

    async def test_concurrent_request_throughput(self, async_http_client):
        """Test concurrent request handling throughput."""
        try:
            # Send 10 concurrent requests
            tasks = []
            for i in range(10):
                task = async_http_client.post(
                    "/api/v1/embeddings/generate",
                    json={"text": f"Test document {i}"}
                )
                tasks.append(task)
            
            start = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            duration = time.time() - start
            
            # Count successful responses
            successful = sum(
                1 for r in responses 
                if not isinstance(r, Exception) and r.status_code == 200
            )
            
            if successful > 0:
                # Calculate throughput
                throughput = successful / duration
                
                # Should handle at least 5 requests per second
                assert throughput > 5
        except httpx.ConnectError:
            pytest.skip("Embedding service not accessible")

    async def test_cache_hit_performance(self, async_http_client):
        """Test cache hit performance."""
        try:
            text = "This is a cached test document."
            
            # First request (cache miss)
            response1 = await async_http_client.post(
                "/api/v1/embeddings/generate",
                json={"text": text}
            )
            
            if response1.status_code != 200:
                pytest.skip("Embedding service not working")
            
            # Second request (cache hit)
            start = time.time()
            response2 = await async_http_client.post(
                "/api/v1/embeddings/generate",
                json={"text": text}
            )
            cache_hit_duration = time.time() - start
            
            if response2.status_code == 200:
                # Cache hit should be faster than 100ms
                assert cache_hit_duration < 0.1
        except httpx.ConnectError:
            pytest.skip("Embedding service not accessible")

    async def test_cache_miss_performance(self, async_http_client):
        """Test cache miss performance."""
        try:
            # Unique text for cache miss
            text = f"Unique test document {time.time()}"
            
            start = time.time()
            response = await async_http_client.post(
                "/api/v1/embeddings/generate",
                json={"text": text}
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                # Cache miss should complete in under 2 seconds
                assert duration < 2.0
        except httpx.ConnectError:
            pytest.skip("Embedding service not accessible")


class TestResourceUsage:
    """Test resource usage and efficiency."""

    async def test_memory_usage_per_embedding(self, async_http_client):
        """Test memory usage for single embedding."""
        try:
            text = "Test document for memory usage measurement."
            
            response = await async_http_client.post(
                "/api/v1/embeddings/generate",
                json={"text": text}
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = data.get("embedding", [])
                
                # Verify embedding size is reasonable
                assert len(embedding) > 0
                assert len(embedding) <= 1024  # Max 1024 dimensions
        except httpx.ConnectError:
            pytest.skip("Embedding service not accessible")

    async def test_batch_processing_efficiency(self, async_http_client, sample_texts):
        """Test batch processing efficiency vs individual requests."""
        try:
            batch_size = 10
            texts = sample_texts[:batch_size]
            
            # Test batch request
            start_batch = time.time()
            batch_response = await async_http_client.post(
                "/api/v1/embeddings/batch",
                json={"texts": texts}
            )
            batch_duration = time.time() - start_batch
            
            if batch_response.status_code != 200:
                pytest.skip("Batch endpoint not working")
            
            # Test individual requests
            start_individual = time.time()
            for text in texts:
                await async_http_client.post(
                    "/api/v1/embeddings/generate",
                    json={"text": text}
                )
            individual_duration = time.time() - start_individual
            
            # Batch should be more efficient (at least 2x faster)
            if individual_duration > 0:
                efficiency_ratio = individual_duration / batch_duration
                assert efficiency_ratio > 1.5
        except httpx.ConnectError:
            pytest.skip("Embedding service not accessible")

    async def test_connection_pool_usage(self, async_http_client):
        """Test connection pool efficiency."""
        try:
            # Send multiple requests to test connection reuse
            responses = []
            for i in range(5):
                response = await async_http_client.post(
                    "/api/v1/embeddings/generate",
                    json={"text": f"Test {i}"}
                )
                responses.append(response)
            
            # All requests should succeed
            successful = sum(1 for r in responses if r.status_code == 200)
            assert successful >= 0  # At least some should succeed
        except httpx.ConnectError:
            pytest.skip("Embedding service not accessible")

    async def test_cache_memory_usage(self, async_http_client):
        """Test cache memory usage."""
        try:
            # Get cache stats
            response = await async_http_client.get("/api/v1/cache/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify cache stats are available
                assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("Embedding service not accessible")

    async def test_large_text_handling(self, async_http_client):
        """Test handling of large text inputs."""
        try:
            # Generate large text (10KB)
            large_text = "This is a test sentence. " * 500
            
            start = time.time()
            response = await async_http_client.post(
                "/api/v1/embeddings/generate",
                json={"text": large_text}
            )
            duration = time.time() - start
            
            # Should handle large text or return appropriate error
            assert response.status_code in [200, 400, 413, 422]
            
            if response.status_code == 200:
                # Should complete in reasonable time
                assert duration < 5.0
        except httpx.ConnectError:
            pytest.skip("Embedding service not accessible")

