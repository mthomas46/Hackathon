"""
Integration tests for API endpoints.

Tests the full API with FastEmbed and Redis integration.
"""

import pytest
from httpx import AsyncClient


class TestEmbeddingEndpoints:
    """Test embedding API endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, test_client: AsyncClient):
        """Test health check endpoint."""
        response = await test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "model" in data
        assert "redis_connected" in data
        assert "cache_enabled" in data
        
        assert data["status"] in ["healthy", "unhealthy"]
        assert data["model"] == "BAAI/bge-base-en-v1.5"
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, test_client: AsyncClient):
        """Test root endpoint."""
        response = await test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "model" in data
        assert "dimensions" in data
        assert "endpoints" in data
    
    @pytest.mark.asyncio
    async def test_single_embedding(self, test_client: AsyncClient, sample_text):
        """Test single embedding generation."""
        response = await test_client.post(
            "/embed/single",
            json={"text": sample_text}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "embedding" in data
        assert "dimensions" in data
        assert "tokens" in data
        assert "model" in data
        assert "cached" in data
        assert "duration_ms" in data
        
        assert len(data["embedding"]) == 768
        assert data["dimensions"] == 768
        assert data["model"] == "BAAI/bge-base-en-v1.5"
        assert isinstance(data["cached"], bool)
        assert data["duration_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_single_embedding_caching(self, test_client: AsyncClient):
        """Test that single embedding is cached on second request."""
        text = {"text": "test text for caching"}
        
        # First request (cache miss)
        response1 = await test_client.post("/embed/single", json=text)
        data1 = response1.json()
        assert data1["cached"] is False
        
        # Second request (cache hit)
        response2 = await test_client.post("/embed/single", json=text)
        data2 = response2.json()
        assert data2["cached"] is True
        
        # Should be much faster
        assert data2["duration_ms"] < data1["duration_ms"]
        
        # Embeddings should be identical
        assert data1["embedding"] == data2["embedding"]
    
    @pytest.mark.asyncio
    async def test_batch_embedding(self, test_client: AsyncClient, sample_texts):
        """Test batch embedding generation."""
        response = await test_client.post(
            "/embed/batch",
            json={"texts": sample_texts}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "embeddings" in data
        assert "dimensions" in data
        assert "tokens" in data
        assert "model" in data
        assert "cache_hits" in data
        assert "cache_misses" in data
        assert "duration_ms" in data
        
        assert len(data["embeddings"]) == len(sample_texts)
        assert data["dimensions"] == 768
        assert data["cache_hits"] >= 0
        assert data["cache_misses"] >= 0
        assert data["cache_hits"] + data["cache_misses"] == len(sample_texts)
    
    @pytest.mark.asyncio
    async def test_batch_caching(self, test_client: AsyncClient, sample_texts):
        """Test batch caching behavior."""
        payload = {"texts": sample_texts}
        
        # First request (all misses)
        response1 = await test_client.post("/embed/batch", json=payload)
        data1 = response1.json()
        assert data1["cache_misses"] == len(sample_texts)
        assert data1["cache_hits"] == 0
        
        # Second request (all hits)
        response2 = await test_client.post("/embed/batch", json=payload)
        data2 = response2.json()
        assert data2["cache_hits"] == len(sample_texts)
        assert data2["cache_misses"] == 0
        
        # Should be much faster
        assert data2["duration_ms"] < data1["duration_ms"] * 0.1
    
    @pytest.mark.asyncio
    async def test_embed_info_endpoint(self, test_client: AsyncClient):
        """Test /embed/info endpoint."""
        response = await test_client.get("/embed/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "model" in data
        assert "cache" in data
        
        assert data["model"]["model"] == "BAAI/bge-base-en-v1.5"
        assert data["model"]["dimensions"] == 768
        assert data["model"]["backend"] == "ONNX Runtime"
    
    @pytest.mark.asyncio
    async def test_empty_text(self, test_client: AsyncClient):
        """Test handling of empty text."""
        response = await test_client.post(
            "/embed/single",
            json={"text": ""}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["embedding"]) == 768
    
    @pytest.mark.asyncio
    async def test_very_long_text(self, test_client: AsyncClient):
        """Test handling of very long text."""
        long_text = "word " * 10000  # Much longer than max_text_length
        
        response = await test_client.post(
            "/embed/single",
            json={"text": long_text}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["embedding"]) == 768
    
    @pytest.mark.asyncio
    async def test_batch_empty_list(self, test_client: AsyncClient):
        """Test batch embedding with empty list."""
        response = await test_client.post(
            "/embed/batch",
            json={"texts": []}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["embeddings"]) == 0
        assert data["cache_hits"] == 0
        assert data["cache_misses"] == 0
    
    @pytest.mark.asyncio
    async def test_invalid_request(self, test_client: AsyncClient):
        """Test invalid request handling."""
        response = await test_client.post(
            "/embed/single",
            json={"invalid_field": "value"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_openapi_docs(self, test_client: AsyncClient):
        """Test that OpenAPI docs are available."""
        response = await test_client.get("/docs")
        assert response.status_code == 200
        
        response = await test_client.get("/redoc")
        assert response.status_code == 200
        
        response = await test_client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_single_embedding_speed(self, test_client: AsyncClient):
        """Test single embedding is fast."""
        response = await test_client.post(
            "/embed/single",
            json={"text": "Quick performance test"}
        )
        
        data = response.json()
        # Should complete in under 50ms
        assert data["duration_ms"] < 50
    
    @pytest.mark.asyncio
    async def test_batch_faster_than_sequential(self, test_client: AsyncClient, sample_texts):
        """Test that batch is faster than sequential requests."""
        import time
        
        # Sequential
        start = time.time()
        for text in sample_texts:
            await test_client.post("/embed/single", json={"text": text})
        sequential_time = time.time() - start
        
        # Batch
        start = time.time()
        await test_client.post("/embed/batch", json={"texts": sample_texts})
        batch_time = time.time() - start
        
        # Batch should be significantly faster
        assert batch_time < sequential_time * 0.3
    
    @pytest.mark.asyncio
    async def test_cached_speed(self, test_client: AsyncClient):
        """Test cached embeddings are very fast."""
        text = {"text": "cache speed test"}
        
        # Prime cache
        await test_client.post("/embed/single", json=text)
        
        # Cached request
        response = await test_client.post("/embed/single", json=text)
        data = response.json()
        
        # Should be under 2ms
        assert data["duration_ms"] < 2
        assert data["cached"] is True

