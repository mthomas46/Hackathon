"""
Unit tests for Redis cache service.

Tests caching functionality for embeddings and normalization.
"""

import pytest
from src.services.cache_service import CacheService


class TestCacheService:
    """Test cache service functionality."""
    
    def test_initialization(self):
        """Test service initialization."""
        service = CacheService()
        assert service is not None
        assert service.ttl == 2592000  # 30 days
    
    @pytest.mark.asyncio
    async def test_connect(self, cache_service):
        """Test Redis connection."""
        assert cache_service.redis is not None
        assert cache_service.enabled is True
    
    def test_compute_hash(self, cache_service):
        """Test content hash computation."""
        text = "test content"
        hash1 = cache_service._compute_hash(text)
        hash2 = cache_service._compute_hash(text)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_make_key(self, cache_service):
        """Test cache key generation."""
        content_hash = "abc123"
        key = cache_service._make_key("embed", content_hash)
        
        assert key == "embed:abc123"
    
    @pytest.mark.asyncio
    async def test_embedding_cache_miss(self, cache_service):
        """Test cache miss for embedding."""
        text = "unique text for cache miss test"
        result = await cache_service.get_embedding(text)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_embedding_cache_hit(self, cache_service):
        """Test cache hit for embedding."""
        text = "test text for cache"
        embedding_data = {
            "embedding": [0.1, 0.2, 0.3],
            "dimensions": 768,
            "tokens": 5
        }
        
        # Set cache
        await cache_service.set_embedding(text, embedding_data)
        
        # Get from cache
        result = await cache_service.get_embedding(text)
        
        assert result is not None
        assert result["embedding"] == [0.1, 0.2, 0.3]
        assert result["dimensions"] == 768
    
    @pytest.mark.asyncio
    async def test_batch_cache_operations(self, cache_service, sample_texts):
        """Test batch cache operations."""
        # Cache some embeddings
        for i, text in enumerate(sample_texts[:3]):
            embedding_data = {
                "embedding": [float(i)] * 768,
                "dimensions": 768,
                "tokens": 5
            }
            await cache_service.set_embedding(text, embedding_data)
        
        # Batch lookup (mix of hits and misses)
        results, miss_indices = await cache_service.get_embeddings_batch(sample_texts)
        
        assert len(results) == len(sample_texts)
        assert len(miss_indices) == 2  # Last 2 should be misses
        
        # First 3 should be hits
        for i in range(3):
            assert results[i] is not None
            assert results[i]["embedding"][0] == float(i)
        
        # Last 2 should be misses
        assert results[3] is None
        assert results[4] is None
    
    @pytest.mark.asyncio
    async def test_batch_cache_set(self, cache_service, sample_texts):
        """Test batch cache setting."""
        embeddings = []
        for i in range(len(sample_texts)):
            embeddings.append({
                "embedding": [float(i)] * 768,
                "dimensions": 768,
                "tokens": 5
            })
        
        await cache_service.set_embeddings_batch(sample_texts, embeddings)
        
        # Verify all were cached
        for i, text in enumerate(sample_texts):
            result = await cache_service.get_embedding(text)
            assert result is not None
            assert result["embedding"][0] == float(i)
    
    @pytest.mark.asyncio
    async def test_normalization_cache(self, cache_service):
        """Test normalization caching."""
        content = "test content"
        file_ext = ".py"
        normalized_data = {
            "content": "# Test\nNormalized content",
            "metadata": {"language": "python"}
        }
        
        # Cache miss
        result = await cache_service.get_normalized(content, file_ext)
        assert result is None
        
        # Set cache
        await cache_service.set_normalized(content, file_ext, normalized_data)
        
        # Cache hit
        result = await cache_service.get_normalized(content, file_ext)
        assert result is not None
        assert result["content"] == "# Test\nNormalized content"
        assert result["metadata"]["language"] == "python"
    
    @pytest.mark.asyncio
    async def test_different_extensions_separate_cache(self, cache_service):
        """Test that different file extensions have separate cache entries."""
        content = "test content"
        normalized_py = {"content": "python version"}
        normalized_js = {"content": "javascript version"}
        
        await cache_service.set_normalized(content, ".py", normalized_py)
        await cache_service.set_normalized(content, ".js", normalized_js)
        
        result_py = await cache_service.get_normalized(content, ".py")
        result_js = await cache_service.get_normalized(content, ".js")
        
        assert result_py["content"] == "python version"
        assert result_js["content"] == "javascript version"
    
    @pytest.mark.asyncio
    async def test_get_stats(self, cache_service):
        """Test cache statistics."""
        stats = await cache_service.get_stats()
        
        assert "enabled" in stats
        assert "connected" in stats
        assert stats["enabled"] is True
        assert stats["connected"] is True

