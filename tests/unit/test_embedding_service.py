"""
Unit tests for Embedding Service.

Tests all major features:
- Model selection and routing
- Backend switching (FastEmbed vs Ollama)
- Dimension consistency
- Error handling and fallbacks
- Health checks and smart retry
- Batch processing
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

# Mock dependencies before importing
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "services" / "ecosystem-mcp" / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client."""
    client = AsyncMock()
    client.embed = AsyncMock(return_value=[0.1] * 768)  # 768-dim embedding
    client.is_available = AsyncMock(return_value=True)
    client.circuit_breaker = Mock()
    client.circuit_breaker.reset = AsyncMock()
    return client


@pytest.fixture
def mock_embedding_client():
    """Mock FastEmbed client."""
    client = AsyncMock()
    client.generate_embedding = AsyncMock(return_value={
        "embedding": [0.2] * 768,  # 768-dim embedding
        "tokens": 100,
        "model": "BAAI/bge-base-en-v1.5",
        "duration_ms": 50
    })
    client.generate_batch = AsyncMock(return_value=[
        {
            "embedding": [0.2] * 768,
            "tokens": 100,
            "model": "BAAI/bge-base-en-v1.5",
            "duration_ms": 50
        }
    ])
    client.circuit_breaker = Mock()
    client.circuit_breaker.reset = AsyncMock()
    return client


class TestEmbeddingServiceInit:
    """Test embedding service initialization."""
    
    @patch('services.ecosystem.mcp.src.services.embeddings.embedding_service.get_ollama_client')
    def test_init_with_ollama_backend(self, mock_get_ollama):
        """Test initialization with Ollama backend."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        service = EmbeddingService(backend="ollama")
        
        assert service.backend == "ollama"
        assert service.ollama_client is not None
        assert service.embedding_client is None
    
    @patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client')
    @patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_embedding_client')
    def test_init_with_fastembed_backend(self, mock_get_embedding, mock_get_ollama):
        """Test initialization with FastEmbed backend."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        mock_get_embedding.return_value = Mock()
        
        service = EmbeddingService(backend="service")
        
        assert service.backend == "service"
        assert service.ollama_client is not None  # Still initialized as fallback
        assert service.embedding_client is not None


class TestEmbeddingGeneration:
    """Test embedding generation."""
    
    @pytest.mark.asyncio
    async def test_generate_with_fastembed(self, mock_embedding_client, mock_ollama_client):
        """Test embedding generation with FastEmbed."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_embedding_client',
                   return_value=mock_embedding_client), \
             patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client):
            
            service = EmbeddingService(backend="service")
            result = await service.generate_embedding("test text")
            
            assert result["model"] == "BAAI/bge-base-en-v1.5"
            assert result["dimensions"] == 768
            assert result["backend"] == "fastembed"
            assert len(result["embedding"]) == 768
            assert isinstance(result["duration"], float)
    
    @pytest.mark.asyncio
    async def test_generate_with_ollama(self, mock_ollama_client):
        """Test embedding generation with Ollama."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client):
            
            service = EmbeddingService(backend="ollama")
            result = await service.generate_embedding("test text")
            
            assert result["model"] == "nomic-embed-text"
            assert result["dimensions"] == 768
            assert result["backend"] == "ollama"
            assert len(result["embedding"]) == 768
            assert isinstance(result["duration"], float)
    
    @pytest.mark.asyncio
    async def test_fastembed_fallback_to_ollama(self, mock_embedding_client, mock_ollama_client):
        """Test fallback from FastEmbed to Ollama on error."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        # Make FastEmbed fail
        mock_embedding_client.generate_embedding.side_effect = Exception("FastEmbed failed")
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_embedding_client',
                   return_value=mock_embedding_client), \
             patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client):
            
            service = EmbeddingService(backend="service")
            result = await service.generate_embedding("test text")
            
            # Should fall back to Ollama
            assert result["model"] == "nomic-embed-text"
            assert result["backend"] == "ollama"
            assert len(result["embedding"]) == 768


class TestDimensionConsistency:
    """Test embedding dimension consistency."""
    
    @pytest.mark.asyncio
    async def test_fastembed_dimensions(self, mock_embedding_client, mock_ollama_client):
        """Test FastEmbed returns 768 dimensions."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_embedding_client',
                   return_value=mock_embedding_client), \
             patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client):
            
            service = EmbeddingService(backend="service")
            result = await service.generate_embedding("test")
            
            assert result["dimensions"] == 768
            assert len(result["embedding"]) == 768
    
    @pytest.mark.asyncio
    async def test_ollama_dimensions(self, mock_ollama_client):
        """Test Ollama returns 768 dimensions."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client):
            
            service = EmbeddingService(backend="ollama")
            result = await service.generate_embedding("test")
            
            assert result["dimensions"] == 768
            assert len(result["embedding"]) == 768
    
    @pytest.mark.asyncio
    async def test_consistent_dimensions_across_backends(self, mock_embedding_client, mock_ollama_client):
        """Test both backends return same dimensions."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_embedding_client',
                   return_value=mock_embedding_client), \
             patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client):
            
            # Test FastEmbed
            service1 = EmbeddingService(backend="service")
            result1 = await service1.generate_embedding("test")
            
            # Test Ollama
            service2 = EmbeddingService(backend="ollama")
            result2 = await service2.generate_embedding("test")
            
            # Both should be 768
            assert result1["dimensions"] == result2["dimensions"] == 768


class TestBatchProcessing:
    """Test batch embedding generation."""
    
    @pytest.mark.asyncio
    async def test_batch_with_fastembed(self, mock_embedding_client, mock_ollama_client):
        """Test batch processing with FastEmbed."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        texts = ["text1", "text2", "text3"]
        mock_embedding_client.generate_batch.return_value = [
            {"embedding": [0.1] * 768, "tokens": 10, "model": "BAAI/bge-base-en-v1.5", "duration_ms": 50}
            for _ in texts
        ]
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_embedding_client',
                   return_value=mock_embedding_client), \
             patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client):
            
            service = EmbeddingService(backend="service")
            results = await service.generate_batch(texts)
            
            assert len(results) == 3
            for result in results:
                assert result["dimensions"] == 768
                assert result["model"] == "BAAI/bge-base-en-v1.5"


class TestHealthChecks:
    """Test health check functionality."""
    
    @pytest.mark.asyncio
    async def test_fastembed_health_check_success(self, mock_embedding_client, mock_ollama_client):
        """Test successful FastEmbed health check."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_embedding_client',
                   return_value=mock_embedding_client), \
             patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client), \
             patch('httpx.AsyncClient') as mock_http:
            
            # Mock successful health check
            mock_response = Mock()
            mock_response.status_code = 200
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            service = EmbeddingService(backend="service")
            is_healthy = await service._check_fastembed_health()
            
            assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_ollama_health_check_success(self, mock_ollama_client):
        """Test successful Ollama health check."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        mock_ollama_client.is_available.return_value = True
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client):
            
            service = EmbeddingService(backend="ollama")
            is_healthy = await service._check_ollama_health()
            
            assert is_healthy is True


class TestModelMetadata:
    """Test model metadata tracking."""
    
    @pytest.mark.asyncio
    async def test_metadata_includes_model_info(self, mock_ollama_client):
        """Test that result includes complete model metadata."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client):
            
            service = EmbeddingService(backend="ollama")
            result = await service.generate_embedding("test")
            
            # Check all required metadata fields
            assert "model" in result
            assert "dimensions" in result
            assert "backend" in result
            assert "tokens" in result
            assert "cost" in result
            assert "duration" in result
            
            # Validate values
            assert result["model"] == "nomic-embed-text"
            assert result["dimensions"] == 768
            assert result["backend"] == "ollama"


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_handles_empty_text(self, mock_ollama_client):
        """Test handling of empty text input."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client):
            
            service = EmbeddingService(backend="ollama")
            result = await service.generate_embedding("")
            
            # Should still return valid result
            assert result["dimensions"] == 768
            assert len(result["embedding"]) == 768
    
    @pytest.mark.asyncio
    async def test_handles_very_long_text(self, mock_ollama_client):
        """Test handling of very long text (should truncate)."""
        from services.ecosystem_mcp.src.services.embeddings.embedding_service import EmbeddingService
        
        with patch('services.ecosystem_mcp.src.services.embeddings.embedding_service.get_ollama_client',
                   return_value=mock_ollama_client):
            
            service = EmbeddingService(backend="ollama")
            long_text = "x" * 10000  # 10k chars
            result = await service.generate_embedding(long_text)
            
            # Should still return valid result (after truncation)
            assert result["dimensions"] == 768
            assert len(result["embedding"]) == 768


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

