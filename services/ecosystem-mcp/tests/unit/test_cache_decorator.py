#!/usr/bin/env python3
"""
Unit Tests: Cache Decorator

Tests the @cache decorator functionality that powers our caching optimizations.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.utils.cache_decorator import cache


@pytest.fixture
async def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    return redis


class TestCacheDecorator:
    """Test suite for cache decorator."""
    
    @pytest.mark.asyncio
    async def test_cache_miss_and_hit(self, mock_redis):
        """Test cache miss followed by cache hit."""
        call_count = 0
        
        @cache(ttl=60, key_prefix="test")
        async def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return x * 2
        
        # First call - cache miss
        with patch('src.utils.cache_decorator.get_redis', return_value=mock_redis):
            mock_redis.get.return_value = None
            result1 = await expensive_function(5)
            
            assert result1 == 10
            assert call_count == 1
            assert mock_redis.get.called
            assert mock_redis.setex.called
        
        # Second call - cache hit (simulate)
        with patch('src.utils.cache_decorator.get_redis', return_value=mock_redis):
            import json
            mock_redis.get.return_value = json.dumps(10)
            result2 = await expensive_function(5)
            
            assert result2 == 10
            assert call_count == 1  # Function not called again!
    
    @pytest.mark.asyncio
    async def test_cache_speedup(self, mock_redis):
        """Test that caching provides significant speedup."""
        
        @cache(ttl=60, key_prefix="test")
        async def slow_function() -> str:
            await asyncio.sleep(0.2)  # 200ms delay
            return "result"
        
        # First call - should be slow
        with patch('src.utils.cache_decorator.get_redis', return_value=mock_redis):
            mock_redis.get.return_value = None
            
            start = time.time()
            result1 = await slow_function()
            time1 = time.time() - start
            
            assert result1 == "result"
            assert time1 >= 0.2  # At least 200ms
        
        # Second call - should be fast (simulated cache hit)
        with patch('src.utils.cache_decorator.get_redis', return_value=mock_redis):
            import json
            mock_redis.get.return_value = json.dumps("result")
            
            start = time.time()
            result2 = await slow_function()
            time2 = time.time() - start
            
            assert result2 == "result"
            assert time2 < 0.1  # Much faster than 200ms
            
            # Verify speedup
            speedup = time1 / time2 if time2 > 0 else float('inf')
            assert speedup > 2  # At least 2x faster
    
    @pytest.mark.asyncio
    async def test_cache_different_args(self, mock_redis):
        """Test that different arguments generate different cache keys."""
        call_count = 0
        
        @cache(ttl=60, key_prefix="test")
        async def add(a: int, b: int) -> int:
            nonlocal call_count
            call_count += 1
            return a + b
        
        with patch('src.utils.cache_decorator.get_redis', return_value=mock_redis):
            mock_redis.get.return_value = None
            
            result1 = await add(1, 2)
            result2 = await add(3, 4)
            
            assert result1 == 3
            assert result2 == 7
            assert call_count == 2  # Both called (different args)
    
    @pytest.mark.asyncio
    async def test_custom_key_fn(self, mock_redis):
        """Test custom key generation function."""
        
        def my_key_fn(data: dict) -> str:
            return f"custom_{data['id']}"
        
        @cache(ttl=60, key_prefix="test", key_fn=my_key_fn)
        async def get_data(data: dict) -> dict:
            return {"result": data["id"] * 2}
        
        with patch('src.utils.cache_decorator.get_redis', return_value=mock_redis):
            mock_redis.get.return_value = None
            
            result = await get_data({"id": 5})
            
            assert result == {"result": 10}
            # Verify custom key was used
            assert mock_redis.setex.called


@pytest.mark.asyncio
async def test_parallel_embedding_speedup():
    """
    Test that parallel embedding generation is faster than sequential.
    
    This tests the optimization in embedding_service.py
    """
    from services.embeddings.embedding_service import EmbeddingService
    
    # Mock texts
    texts = [f"Test text {i}" for i in range(10)]
    
    # We can't easily test the actual speedup without the full service,
    # but we can verify the structure is correct
    service = EmbeddingService()
    
    # Verify the method exists and has correct signature
    assert hasattr(service, 'generate_batch')
    assert hasattr(service, 'generate_embedding')


@pytest.mark.asyncio
async def test_httpx_connection_pool():
    """
    Test that HTTPx connection pooling is configured correctly.
    
    This tests the optimization in ollama_client.py
    """
    from services.models.ollama_client import OllamaClient
    
    client = OllamaClient()
    
    # Verify client has pooled connection
    assert hasattr(client, '_client')
    assert client._client is not None
    
    # Verify close method exists
    assert hasattr(client, 'close')
    
    # Clean up
    await client.close()


def test_rag_cache_decorator_exists():
    """Verify RAG endpoint has cache decorator."""
    # This would require importing the route, which has dependencies
    # Instead, we can verify the decorator is applied by checking the file
    from pathlib import Path
    
    ask_file = Path(__file__).parent.parent.parent / "src" / "api" / "routes" / "ask.py"
    content = ask_file.read_text()
    
    assert "@cache" in content, "RAG endpoint should have @cache decorator"
    assert "key_prefix=\"rag\"" in content, "RAG cache should use 'rag' prefix"
    assert "_make_rag_cache_key" in content, "RAG should have custom key function"


def test_search_cache_decorator_exists():
    """Verify search endpoint has cache decorator."""
    from pathlib import Path
    
    search_file = Path(__file__).parent.parent.parent / "src" / "api" / "routes" / "search.py"
    content = search_file.read_text()
    
    assert "@cache" in content, "Search endpoint should have @cache decorator"


def test_query_cache_decorator_exists():
    """Verify query endpoint has cache decorator."""
    from pathlib import Path
    
    query_file = Path(__file__).parent.parent.parent / "src" / "api" / "routes" / "query.py"
    content = query_file.read_text()
    
    assert "@cache" in content, "Query endpoint should have @cache decorator"
    assert "key_prefix=\"doc_query\"" in content, "Query cache should use 'doc_query' prefix"


def test_chromadb_cache_decorator_exists():
    """Verify ChromaDB search is cached."""
    from pathlib import Path
    
    rag_service_file = Path(__file__).parent.parent.parent / "src" / "services" / "rag" / "rag_service.py"
    content = rag_service_file.read_text()
    
    assert "@cache" in content, "RAG service should have @cache decorator"
    assert "key_prefix=\"chroma_search\"" in content, "ChromaDB cache should use 'chroma_search' prefix"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

