"""
TDD Tests for Embedding Service

Tests cover:
- Service initialization and model loading
- Single embedding generation
- Batch embedding generation
- Document embedding with storage
- Semantic search via service
- Error handling and edge cases
"""

import pytest
import asyncio
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock


class TestEmbeddingServiceInitialization:
    """Test embedding service initialization."""
    
    def test_service_creation(self):
        """Test service can be created."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        service = EmbeddingService()
        assert service is not None
        assert service.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    
    def test_singleton_pattern(self):
        """Test get_embedding_service returns singleton."""
        from services.doc_store.domain.embeddings.service import get_embedding_service
        
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        
        assert service1 is service2  # Same instance
    
    def test_lazy_model_loading(self):
        """Test model is not loaded until first use."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        service = EmbeddingService()
        assert service._generator is None  # Not loaded yet
    
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    def test_model_loading_on_first_use(self, mock_generator_class):
        """Test model loads on first embedding generation."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        service = EmbeddingService()
        generator = service._get_generator()
        
        assert generator is mock_generator
        mock_generator_class.assert_called_once_with(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    def test_model_caching(self, mock_generator_class):
        """Test model is cached after first load."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        service = EmbeddingService()
        gen1 = service._get_generator()
        gen2 = service._get_generator()
        
        assert gen1 is gen2
        mock_generator_class.assert_called_once()  # Only called once


class TestSingleEmbeddingGeneration:
    """Test single text embedding generation."""
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_generate_embedding_basic(self, mock_generator_class):
        """Test basic embedding generation."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        # Setup mock
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.embedding = [0.1, 0.2, 0.3, 0.4]
        mock_generator.generate_embedding.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        
        service = EmbeddingService()
        embedding = await service.generate_embedding("test text")
        
        assert embedding == [0.1, 0.2, 0.3, 0.4]
        mock_generator.generate_embedding.assert_called_once_with("test text")
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_generate_embedding_empty_text(self, mock_generator_class):
        """Test embedding generation with empty text."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.embedding = [0.0] * 384  # Zero vector
        mock_generator.generate_embedding.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        
        service = EmbeddingService()
        embedding = await service.generate_embedding("")
        
        assert len(embedding) == 384
        mock_generator.generate_embedding.assert_called_once_with("")
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_generate_embedding_long_text(self, mock_generator_class):
        """Test embedding generation with very long text."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.embedding = [0.5] * 384
        mock_generator.generate_embedding.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        
        long_text = "word " * 10000  # Very long text
        service = EmbeddingService()
        embedding = await service.generate_embedding(long_text)
        
        assert len(embedding) == 384
        mock_generator.generate_embedding.assert_called_once()


class TestBatchEmbeddingGeneration:
    """Test batch embedding generation."""
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_batch_generation_basic(self, mock_generator_class):
        """Test basic batch embedding generation."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_results = [
            Mock(embedding=[0.1, 0.2]),
            Mock(embedding=[0.3, 0.4]),
            Mock(embedding=[0.5, 0.6]),
        ]
        mock_generator.batch_generate_embeddings.return_value = mock_results
        mock_generator_class.return_value = mock_generator
        
        service = EmbeddingService()
        texts = ["text1", "text2", "text3"]
        embeddings = await service.generate_embeddings_batch(texts)
        
        assert len(embeddings) == 3
        assert embeddings[0] == [0.1, 0.2]
        assert embeddings[1] == [0.3, 0.4]
        assert embeddings[2] == [0.5, 0.6]
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_batch_generation_empty_list(self, mock_generator_class):
        """Test batch generation with empty list."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_generator.batch_generate_embeddings.return_value = []
        mock_generator_class.return_value = mock_generator
        
        service = EmbeddingService()
        embeddings = await service.generate_embeddings_batch([])
        
        assert embeddings == []
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_batch_generation_custom_batch_size(self, mock_generator_class):
        """Test batch generation with custom batch size."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_results = [Mock(embedding=[0.1]) for _ in range(100)]
        mock_generator.batch_generate_embeddings.return_value = mock_results
        mock_generator_class.return_value = mock_generator
        
        service = EmbeddingService()
        texts = [f"text{i}" for i in range(100)]
        embeddings = await service.generate_embeddings_batch(texts, batch_size=64)
        
        assert len(embeddings) == 100
        mock_generator.batch_generate_embeddings.assert_called_once()
        call_args = mock_generator.batch_generate_embeddings.call_args
        assert call_args[0][1] == 64  # batch_size argument


class TestDocumentEmbedding:
    """Test document embedding with storage."""
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.insert_document_vector')
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_embed_document_basic(self, mock_generator_class, mock_insert):
        """Test basic document embedding."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        # Setup mocks
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.embedding = [0.1, 0.2, 0.3]
        mock_generator.generate_embedding.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        mock_insert.return_value = "vec-123"
        
        service = EmbeddingService()
        result = await service.embed_document(
            document_id="doc-456",
            content="test content"
        )
        
        assert result["vector_id"] == "vec-123"
        assert result["document_id"] == "doc-456"
        assert result["embedding_dimension"] == 3
        mock_insert.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.insert_document_vector')
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_embed_document_with_metadata(self, mock_generator_class, mock_insert):
        """Test document embedding with metadata."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.embedding = [0.1, 0.2]
        mock_generator.generate_embedding.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        mock_insert.return_value = "vec-123"
        
        service = EmbeddingService()
        metadata = {"source": "wiki", "tier": 1}
        result = await service.embed_document(
            document_id="doc-456",
            content="test content",
            metadata=metadata
        )
        
        # Verify metadata was passed to insert
        call_args = mock_insert.call_args
        assert call_args[1]["metadata"] == metadata


class TestBatchDocumentEmbedding:
    """Test batch document embedding."""
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.insert_document_vector')
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_embed_documents_batch_basic(self, mock_generator_class, mock_insert):
        """Test basic batch document embedding."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_results = [
            Mock(embedding=[0.1, 0.2]),
            Mock(embedding=[0.3, 0.4]),
        ]
        mock_generator.batch_generate_embeddings.return_value = mock_results
        mock_generator_class.return_value = mock_generator
        mock_insert.side_effect = ["vec-1", "vec-2"]
        
        service = EmbeddingService()
        documents = [
            {"id": "doc-1", "content": "content 1"},
            {"id": "doc-2", "content": "content 2"},
        ]
        results = await service.embed_documents_batch(documents)
        
        assert len(results) == 2
        assert all(r["success"] for r in results)
        assert results[0]["document_id"] == "doc-1"
        assert results[1]["document_id"] == "doc-2"
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.insert_document_vector')
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_embed_documents_batch_partial_failure(self, mock_generator_class, mock_insert):
        """Test batch embedding with partial failures."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_results = [
            Mock(embedding=[0.1, 0.2]),
            Mock(embedding=[0.3, 0.4]),
        ]
        mock_generator.batch_generate_embeddings.return_value = mock_results
        mock_generator_class.return_value = mock_generator
        
        # First succeeds, second fails
        mock_insert.side_effect = ["vec-1", Exception("DB error")]
        
        service = EmbeddingService()
        documents = [
            {"id": "doc-1", "content": "content 1"},
            {"id": "doc-2", "content": "content 2"},
        ]
        results = await service.embed_documents_batch(documents)
        
        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert "error" in results[1]


class TestSemanticSearchViaService:
    """Test semantic search through service."""
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.semantic_search_documents')
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_semantic_search_basic(self, mock_generator_class, mock_search):
        """Test basic semantic search."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.embedding = [0.1, 0.2, 0.3]
        mock_generator.generate_embedding.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        
        mock_search.return_value = [
            {"id": "doc-1", "semantic_similarity": 0.9},
            {"id": "doc-2", "semantic_similarity": 0.7},
        ]
        
        service = EmbeddingService()
        results = await service.semantic_search("test query", limit=10)
        
        assert len(results) == 2
        assert results[0]["semantic_similarity"] == 0.9
        mock_search.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.semantic_search_documents')
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_semantic_search_with_threshold(self, mock_generator_class, mock_search):
        """Test semantic search with similarity threshold."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.embedding = [0.1, 0.2]
        mock_generator.generate_embedding.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        mock_search.return_value = []
        
        service = EmbeddingService()
        await service.semantic_search("query", min_similarity=0.8)
        
        call_args = mock_search.call_args
        assert call_args[1]["min_similarity"] == 0.8


class TestModelInfo:
    """Test model information retrieval."""
    
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    def test_get_model_info(self, mock_generator_class):
        """Test retrieving model information."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_model_info = Mock()
        mock_model_info.name = "test-model"
        mock_model_info.dimensions = 384
        mock_model_info.max_sequence_length = 512
        mock_model_info.model_size_mb = 90.5
        mock_model_info.language = "en"
        mock_generator.get_model_info.return_value = mock_model_info
        mock_generator_class.return_value = mock_generator
        
        service = EmbeddingService()
        info = service.get_model_info()
        
        assert info["name"] == "test-model"
        assert info["dimensions"] == 384
        assert info["max_sequence_length"] == 512
        assert info["model_size_mb"] == 90.5
        assert info["language"] == "en"


class TestErrorHandling:
    """Test error handling in embedding service."""
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_import_error_handling(self, mock_generator_class):
        """Test handling of import errors."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator_class.side_effect = ImportError("sentence-transformers not found")
        
        service = EmbeddingService()
        with pytest.raises(RuntimeError) as exc_info:
            service._get_generator()
        
        assert "sentence-transformers" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('services.doc_store.domain.embeddings.service.LocalEmbeddingGenerator')
    async def test_generation_error_propagation(self, mock_generator_class):
        """Test that generation errors are propagated."""
        from services.doc_store.domain.embeddings.service import EmbeddingService
        
        mock_generator = Mock()
        mock_generator.generate_embedding.side_effect = Exception("Model error")
        mock_generator_class.return_value = mock_generator
        
        service = EmbeddingService()
        with pytest.raises(Exception) as exc_info:
            await service.generate_embedding("test")
        
        assert "Model error" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

