"""Tests for semantic similarity analysis functionality.

Tests the semantic analyzer module and its integration with the analysis service.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from services.analysis_service.modules.semantic_analyzer import (
    SemanticSimilarityAnalyzer,
    analyze_semantic_similarity,
    SEMANTIC_ANALYSIS_AVAILABLE
)
from services.shared.models import Document


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        Document(
            id="doc1",
            title="Getting Started Guide",
            content="This guide will help you get started with our API. First, you need to create an account and obtain your API key.",
            source_type="confluence",
            metadata={"author": "John Doe", "last_updated": "2024-01-15"}
        ),
        Document(
            id="doc2",
            title="API Onboarding",
            content="Welcome to our API! To begin using our services, you'll need to sign up for an account and get your authentication credentials.",
            source_type="confluence",
            metadata={"author": "Jane Smith", "last_updated": "2024-01-16"}
        ),
        Document(
            id="doc3",
            title="User Authentication",
            content="Learn how to authenticate users in your application using OAuth 2.0 and JWT tokens.",
            source_type="github",
            metadata={"author": "Bob Wilson", "last_updated": "2024-01-17"}
        ),
        Document(
            id="doc4",
            title="Database Setup",
            content="This document explains how to configure and optimize your database settings for better performance.",
            source_type="confluence",
            metadata={"author": "Alice Brown", "last_updated": "2024-01-18"}
        )
    ]


@pytest.fixture
def mock_sentence_transformer():
    """Mock sentence transformer for testing."""
    mock_model = Mock()
    mock_model.encode.return_value = Mock()
    mock_model.encode.return_value.cpu.return_value.numpy.return_value = [
        [0.1, 0.2, 0.3],  # Embedding for doc1
        [0.15, 0.25, 0.35],  # Embedding for doc2 (similar to doc1)
        [0.8, 0.9, 0.1],  # Embedding for doc3 (different)
        [0.85, 0.95, 0.15]  # Embedding for doc4 (similar to doc3)
    ]
    mock_model.get_sentence_embedding_dimension.return_value = 3
    return mock_model


@pytest.fixture
def mock_cos_sim():
    """Mock cosine similarity function."""
    def cos_sim_func(embeddings1, embeddings2):
        # Return a similarity matrix
        import numpy as np
        # Simulate: doc1-doc2: 0.95 (high similarity), doc3-doc4: 0.92 (high similarity)
        return np.array([
            [1.0, 0.95, 0.3, 0.25],  # doc1 similarities
            [0.95, 1.0, 0.28, 0.22],  # doc2 similarities
            [0.3, 0.28, 1.0, 0.92],   # doc3 similarities
            [0.25, 0.22, 0.92, 1.0]   # doc4 similarities
        ])
    return cos_sim_func


class TestSemanticSimilarityAnalyzer:
    """Test the SemanticSimilarityAnalyzer class."""

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization of the analyzer."""
        analyzer = SemanticSimilarityAnalyzer()

        # Mock the dependencies
        with patch('services.analysis_service.modules.semantic_analyzer.SentenceTransformer') as mock_st, \
             patch('services.analysis_service.modules.semantic_analyzer.faiss') as mock_faiss:

            mock_model = Mock()
            mock_st.return_value = mock_model
            mock_model.get_sentence_embedding_dimension.return_value = 384

            # Test initialization
            success = analyzer._initialize_model()
            assert success is True
            assert analyzer.initialized is True
            assert analyzer.model == mock_model

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure when dependencies are not available."""
        # Temporarily set the availability flag to False
        original_available = SEMANTIC_ANALYSIS_AVAILABLE

        with patch('services.analysis_service.modules.semantic_analyzer.SEMANTIC_ANALYSIS_AVAILABLE', False):
            analyzer = SemanticSimilarityAnalyzer()
            success = analyzer._initialize_model()
            assert success is False
            assert analyzer.initialized is False

    @pytest.mark.asyncio
    async def test_extract_text_for_analysis_content_only(self, sample_documents):
        """Test text extraction with content scope."""
        analyzer = SemanticSimilarityAnalyzer()
        doc = sample_documents[0]

        text = analyzer._extract_text_for_analysis(doc, "content")
        assert "getting started" in text.lower()
        assert "api key" in text.lower()

    @pytest.mark.asyncio
    async def test_extract_text_for_analysis_titles_only(self, sample_documents):
        """Test text extraction with titles scope."""
        analyzer = SemanticSimilarityAnalyzer()
        doc = sample_documents[0]

        text = analyzer._extract_text_for_analysis(doc, "titles")
        assert "Getting Started Guide" in text
        assert "API key" not in text.lower()  # Content should not be included

    @pytest.mark.asyncio
    async def test_extract_text_for_analysis_combined(self, sample_documents):
        """Test text extraction with combined scope."""
        analyzer = SemanticSimilarityAnalyzer()
        doc = sample_documents[0]

        text = analyzer._extract_text_for_analysis(doc, "combined")
        assert "Getting Started Guide" in text
        assert "getting started" in text.lower()
        assert "api key" in text.lower()

    @pytest.mark.asyncio
    async def test_chunk_text_small_content(self):
        """Test text chunking with small content."""
        analyzer = SemanticSimilarityAnalyzer()
        text = "This is a short text."

        chunks = analyzer._chunk_text(text, chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    @pytest.mark.asyncio
    async def test_chunk_text_large_content(self):
        """Test text chunking with large content."""
        analyzer = SemanticSimilarityAnalyzer()
        text = "This is a very long text that should be split into multiple chunks. " * 50

        chunks = analyzer._chunk_text(text, chunk_size=50)
        assert len(chunks) > 1
        assert all(len(chunk) <= 50 for chunk in chunks)

    @pytest.mark.asyncio
    async def test_calculate_similarities_with_threshold(self, mock_cos_sim):
        """Test similarity calculation with threshold filtering."""
        analyzer = SemanticSimilarityAnalyzer()
        analyzer.document_ids = ["doc1", "doc2", "doc3", "doc4"]

        # Mock embeddings
        import numpy as np
        embeddings = np.array([
            [0.1, 0.2, 0.3],
            [0.15, 0.25, 0.35],
            [0.8, 0.9, 0.1],
            [0.85, 0.95, 0.15]
        ])

        with patch('services.analysis_service.modules.semantic_analyzer.cos_sim', mock_cos_sim):
            similarities = analyzer._calculate_similarities(embeddings, threshold=0.9)

        # Should find high similarity pairs (0.95 and 0.92)
        assert len(similarities) == 2
        assert similarities[0]['similarity_score'] >= 0.9
        assert similarities[1]['similarity_score'] >= 0.9

    @pytest.mark.asyncio
    async def test_analyze_similarity_insufficient_documents(self, sample_documents):
        """Test analysis with insufficient documents."""
        analyzer = SemanticSimilarityAnalyzer()

        result = await analyzer.analyze_similarity(
            documents=[sample_documents[0]],  # Only one document
            similarity_threshold=0.8,
            analysis_scope="content"
        )

        assert result['total_documents'] == 1
        assert len(result['similarity_pairs']) == 0
        assert "At least 2 documents" in result.get('message', '')

    @pytest.mark.asyncio
    async def test_analyze_similarity_full_flow(self, sample_documents, mock_sentence_transformer, mock_cos_sim):
        """Test the complete analysis flow."""
        analyzer = SemanticSimilarityAnalyzer()

        with patch('services.analysis_service.modules.semantic_analyzer.SentenceTransformer', return_value=mock_sentence_transformer), \
             patch('services.analysis_service.modules.semantic_analyzer.faiss'), \
             patch('services.analysis_service.modules.semantic_analyzer.cos_sim', mock_cos_sim):

            result = await analyzer.analyze_similarity(
                documents=sample_documents,
                similarity_threshold=0.8,
                analysis_scope="content"
            )

            assert result['total_documents'] == 4
            assert len(result['similarity_pairs']) > 0
            assert 'analysis_summary' in result
            assert 'processing_time' in result
            assert result['model_used'] == 'all-MiniLM-L6-v2'

    @pytest.mark.asyncio
    async def test_analyze_similarity_error_handling(self, sample_documents):
        """Test error handling during analysis."""
        analyzer = SemanticSimilarityAnalyzer()

        # Mock initialization failure
        with patch.object(analyzer, '_initialize_model', return_value=False):
            result = await analyzer.analyze_similarity(
                documents=sample_documents,
                similarity_threshold=0.8,
                analysis_scope="content"
            )

            assert 'error' in result
            assert 'not available' in result.get('message', '').lower()


@pytest.mark.asyncio
class TestSemanticSimilarityIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_analyze_semantic_similarity_function(self, sample_documents):
        """Test the convenience function."""
        with patch('services.analysis_service.modules.semantic_analyzer.semantic_analyzer') as mock_analyzer:
            mock_analyzer.analyze_similarity.return_value = {
                'total_documents': 4,
                'similarity_pairs': [],
                'analysis_summary': {},
                'processing_time': 1.5,
                'model_used': 'test-model'
            }

            result = await analyze_semantic_similarity(
                documents=sample_documents,
                similarity_threshold=0.8,
                analysis_scope="content"
            )

            assert result['total_documents'] == 4
            assert result['processing_time'] == 1.5
            mock_analyzer.analyze_similarity.assert_called_once()


class TestSemanticSimilarityAnalysisHandlers:
    """Test the analysis handlers integration."""

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        client = Mock()
        client.doc_store_url.return_value = "http://docstore:5000"
        client.get_json = Mock()
        return client

    @pytest.mark.asyncio
    async def test_handle_semantic_similarity_analysis_success(self, mock_service_client):
        """Test successful semantic similarity analysis handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import SemanticSimilarityRequest

        # Mock document data
        mock_doc_data = {
            "id": "doc1",
            "title": "Test Document",
            "content": "This is test content for similarity analysis.",
            "source_type": "confluence",
            "metadata": {"author": "Test Author"}
        }

        with patch('services.analysis_service.modules.analysis_handlers.get_analysis_service_client', return_value=mock_service_client), \
             patch('services.analysis_service.modules.analysis_handlers.analyze_semantic_similarity') as mock_analyze:

            # Setup mocks
            mock_service_client.get_json.return_value = mock_doc_data
            mock_analyze.return_value = {
                'total_documents': 2,
                'similarity_pairs': [
                    {
                        'document_id_1': 'doc1',
                        'document_id_2': 'doc2',
                        'similarity_score': 0.95,
                        'confidence': 0.97,
                        'similar_sections': ['content'],
                        'rationale': 'High semantic similarity detected'
                    }
                ],
                'analysis_summary': {
                    'high_similarity_pairs': 1,
                    'average_similarity': 0.95
                },
                'processing_time': 1.2,
                'model_used': 'all-MiniLM-L6-v2'
            }

            # Create request
            request = SemanticSimilarityRequest(
                document_ids=["doc1", "doc2"],
                similarity_threshold=0.8,
                analysis_scope="content"
            )

            # Execute handler
            result = await AnalysisHandlers.handle_semantic_similarity_analysis(request)

            # Verify results
            assert result.total_documents == 2
            assert len(result.similarity_pairs) == 1
            assert result.similarity_pairs[0].similarity_score == 0.95
            assert result.processing_time == 1.2
            assert result.model_used == 'all-MiniLM-L6-v2'

    @pytest.mark.asyncio
    async def test_handle_semantic_similarity_analysis_insufficient_docs(self, mock_service_client):
        """Test handling with insufficient documents."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import SemanticSimilarityRequest

        with patch('services.analysis_service.modules.analysis_handlers.get_analysis_service_client', return_value=mock_service_client):
            mock_service_client.get_json.return_value = {"id": "doc1", "content": "test"}

            request = SemanticSimilarityRequest(
                document_ids=["doc1"],  # Only one document
                similarity_threshold=0.8,
                analysis_scope="content"
            )

            result = await AnalysisHandlers.handle_semantic_similarity_analysis(request)

            assert result.total_documents == 1
            assert len(result.similarity_pairs) == 0
            assert result.processing_time == 0.0
            assert result.model_used == "none"

    @pytest.mark.asyncio
    async def test_handle_semantic_similarity_analysis_error_recovery(self, mock_service_client):
        """Test error recovery in analysis handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import SemanticSimilarityRequest

        with patch('services.analysis_service.modules.analysis_handlers.get_analysis_service_client', return_value=mock_service_client), \
             patch('services.analysis_service.modules.analysis_handlers.analyze_semantic_similarity') as mock_analyze:

            # Setup mock to raise exception
            mock_service_client.get_json.return_value = {"id": "doc1", "content": "test"}
            mock_analyze.side_effect = Exception("Analysis failed")

            request = SemanticSimilarityRequest(
                document_ids=["doc1", "doc2"],
                similarity_threshold=0.8,
                analysis_scope="content"
            )

            result = await AnalysisHandlers.handle_semantic_similarity_analysis(request)

            assert result.total_documents == 2
            assert len(result.similarity_pairs) == 0
            assert result.processing_time == 0.0
            assert result.model_used == "error"
            assert "Analysis failed" in result.analysis_summary.get("error", "")


if __name__ == "__main__":
    pytest.main([__file__])
