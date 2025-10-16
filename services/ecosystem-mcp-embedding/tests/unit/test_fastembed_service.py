"""
Unit tests for FastEmbed service.

Tests ONNX-optimized embedding generation.
"""

import pytest
import numpy as np
from src.services.fastembed_service import FastEmbedService


class TestFastEmbedService:
    """Test FastEmbed service functionality."""
    
    def test_initialization(self):
        """Test service initialization."""
        service = FastEmbedService()
        assert service is not None
        assert service.model_name == "BAAI/bge-base-en-v1.5"
        assert service.max_text_length == 8000
    
    def test_model_loading(self, fastembed_service):
        """Test model loading."""
        assert fastembed_service.model is not None
        assert fastembed_service.dimensions == 768
    
    @pytest.mark.asyncio
    async def test_generate_single_embedding(self, fastembed_service, sample_text):
        """Test single embedding generation."""
        result = await fastembed_service.generate_embedding(sample_text)
        
        assert "embedding" in result
        assert "dimensions" in result
        assert "tokens" in result
        assert "model" in result
        assert "duration_ms" in result
        
        assert len(result["embedding"]) == 768
        assert result["dimensions"] == 768
        assert result["tokens"] > 0
        assert result["model"] == "BAAI/bge-base-en-v1.5"
        assert result["duration_ms"] > 0
        
        # Verify embedding is normalized
        embedding = np.array(result["embedding"])
        norm = np.linalg.norm(embedding)
        assert 0.9 < norm < 1.1  # Should be approximately 1
    
    @pytest.mark.asyncio
    async def test_generate_batch_embeddings(self, fastembed_service, sample_texts):
        """Test batch embedding generation."""
        results = await fastembed_service.generate_batch(sample_texts)
        
        assert len(results) == len(sample_texts)
        
        for result in results:
            assert "embedding" in result
            assert len(result["embedding"]) == 768
            assert result["dimensions"] == 768
    
    @pytest.mark.asyncio
    async def test_text_truncation(self, fastembed_service):
        """Test handling of very long text."""
        long_text = "word " * 10000  # Much longer than max_text_length
        result = await fastembed_service.generate_embedding(long_text)
        
        assert result is not None
        assert len(result["embedding"]) == 768
    
    @pytest.mark.asyncio
    async def test_empty_text(self, fastembed_service):
        """Test handling of empty text."""
        result = await fastembed_service.generate_embedding("")
        
        assert result is not None
        assert len(result["embedding"]) == 768
    
    @pytest.mark.asyncio
    async def test_batch_performance(self, fastembed_service, sample_texts):
        """Test that batch processing is faster than sequential."""
        import time
        
        # Sequential
        start = time.time()
        for text in sample_texts:
            await fastembed_service.generate_embedding(text)
        sequential_time = time.time() - start
        
        # Batch
        start = time.time()
        await fastembed_service.generate_batch(sample_texts)
        batch_time = time.time() - start
        
        # Batch should be significantly faster
        assert batch_time < sequential_time * 0.5
    
    @pytest.mark.asyncio
    async def test_consistency(self, fastembed_service, sample_text):
        """Test that same text produces same embedding."""
        result1 = await fastembed_service.generate_embedding(sample_text)
        result2 = await fastembed_service.generate_embedding(sample_text)
        
        embedding1 = np.array(result1["embedding"])
        embedding2 = np.array(result2["embedding"])
        
        # Should be identical
        np.testing.assert_array_almost_equal(embedding1, embedding2, decimal=5)
    
    def test_get_info(self, fastembed_service):
        """Test get_info method."""
        info = fastembed_service.get_info()
        
        assert "model" in info
        assert "dimensions" in info
        assert "max_text_length" in info
        assert "backend" in info
        assert "loaded" in info
        
        assert info["model"] == "BAAI/bge-base-en-v1.5"
        assert info["dimensions"] == 768
        assert info["backend"] == "ONNX Runtime"
        assert info["loaded"] is True

