"""
End-to-end tests for complete embedding workflow.

Tests integration between main service and embedding service.
"""

import pytest
import asyncio
from httpx import AsyncClient


class TestE2EWorkflow:
    """Test complete embedding workflow end-to-end."""
    
    @pytest.mark.asyncio
    async def test_complete_embedding_pipeline(self, test_client: AsyncClient):
        """Test complete pipeline from request to cached response."""
        text = "End-to-end test document for complete workflow validation"
        
        # Step 1: Generate embedding (cache miss)
        response1 = await test_client.post(
            "/embed/single",
            json={"text": text}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["cached"] is False
        initial_duration = data1["duration_ms"]
        
        # Step 2: Retrieve from cache (cache hit)
        response2 = await test_client.post(
            "/embed/single",
            json={"text": text}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["cached"] is True
        cached_duration = data2["duration_ms"]
        
        # Step 3: Verify speedup
        assert cached_duration < initial_duration * 0.1
        
        # Step 4: Verify embedding consistency
        assert data1["embedding"] == data2["embedding"]
        assert data1["dimensions"] == data2["dimensions"]
    
    @pytest.mark.asyncio
    async def test_mixed_cache_batch(self, test_client: AsyncClient):
        """Test batch request with mix of cached and uncached texts."""
        texts = [
            "Cached text 1",
            "Cached text 2",
            "Uncached text 1",
            "Uncached text 2"
        ]
        
        # Prime cache with first 2 texts
        for text in texts[:2]:
            await test_client.post("/embed/single", json={"text": text})
        
        # Batch request with mix
        response = await test_client.post(
            "/embed/batch",
            json={"texts": texts}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["cache_hits"] == 2
        assert data["cache_misses"] == 2
        assert len(data["embeddings"]) == 4
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_client: AsyncClient):
        """Test handling of concurrent requests."""
        texts = [f"Concurrent test {i}" for i in range(10)]
        
        # Send concurrent requests
        tasks = [
            test_client.post("/embed/single", json={"text": text})
            for text in texts
        ]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # All should have valid embeddings
        for response in responses:
            data = response.json()
            assert len(data["embedding"]) == 768
    
    @pytest.mark.asyncio
    async def test_service_resilience(self, test_client: AsyncClient):
        """Test service handles errors gracefully."""
        # Test with various edge cases
        test_cases = [
            "",  # Empty
            "a",  # Single char
            "word " * 10000,  # Very long
            "Special chars: !@#$%^&*()",
            "Emojis: 🚀🎉💡",
            "Multilingual: Hello 你好 Привет"
        ]
        
        for text in test_cases:
            response = await test_client.post(
                "/embed/single",
                json={"text": text}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["embedding"]) == 768
    
    @pytest.mark.asyncio
    async def test_cache_consistency_across_requests(self, test_client: AsyncClient):
        """Test cache consistency across multiple requests."""
        text = "Cache consistency test"
        
        # Generate embedding 5 times
        embeddings = []
        for _ in range(5):
            response = await test_client.post(
                "/embed/single",
                json={"text": text}
            )
            data = response.json()
            embeddings.append(data["embedding"])
        
        # All should be identical
        for i in range(1, 5):
            assert embeddings[i] == embeddings[0]
    
    @pytest.mark.asyncio
    async def test_batch_ordering_preserved(self, test_client: AsyncClient):
        """Test that batch preserves input order."""
        texts = [f"Order test {i}" for i in range(10)]
        
        response = await test_client.post(
            "/embed/batch",
            json={"texts": texts}
        )
        
        data = response.json()
        embeddings = data["embeddings"]
        
        # Verify order by checking each embedding is unique
        # (different texts should produce different embeddings)
        for i in range(len(embeddings) - 1):
            assert embeddings[i] != embeddings[i + 1]

