"""Tests for automated categorization functionality in Summarizer Hub.

Tests the categorizer module and its integration with the summarizer hub service.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from services.summarizer_hub.modules.categorizer import (
    DocumentCategorizer,
    categorize_document,
    categorize_documents_batch,
    CATEGORIZATION_AVAILABLE
)


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        {
            "id": "doc1",
            "title": "REST API Authentication Guide",
            "content": "This guide explains how to authenticate with our REST API using OAuth 2.0. You need to obtain an access token first, then include it in your request headers.",
            "metadata": {
                "author": "John Doe",
                "type": "documentation",
                "tags": ["api", "authentication"]
            }
        },
        {
            "id": "doc2",
            "title": "Getting Started Tutorial",
            "content": "Welcome to our platform! This tutorial will walk you through the basic setup and configuration steps to get your first application running.",
            "metadata": {
                "author": "Jane Smith",
                "type": "tutorial",
                "difficulty": "beginner"
            }
        },
        {
            "id": "doc3",
            "title": "Database Performance Optimization",
            "content": "Learn advanced techniques for optimizing database performance including indexing strategies, query optimization, and caching mechanisms.",
            "metadata": {
                "author": "Bob Wilson",
                "type": "technical",
                "tags": ["database", "performance"]
            }
        },
        {
            "id": "doc4",
            "title": "Troubleshooting Connection Issues",
            "content": "Common connection problems and their solutions. Check firewall settings, network connectivity, and configuration files.",
            "metadata": {
                "author": "Alice Brown",
                "type": "support",
                "tags": ["troubleshooting", "network"]
            }
        }
    ]


@pytest.fixture
def mock_zero_shot_pipeline():
    """Mock zero-shot classification pipeline."""
    mock_pipeline = Mock()
    mock_pipeline.return_value = {
        'labels': ['api_documentation', 'user_guide', 'technical_specification'],
        'scores': [0.85, 0.12, 0.03]
    }
    return mock_pipeline


@pytest.fixture
def mock_tokenizer():
    """Mock tokenizer for transformers."""
    return Mock()


@pytest.fixture
def mock_model():
    """Mock model for transformers."""
    return Mock()


class TestDocumentCategorizer:
    """Test the DocumentCategorizer class."""

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization of the categorizer."""
        categorizer = DocumentCategorizer()

        with patch('services.summarizer_hub.modules.categorizer.pipeline') as mock_pipeline, \
             patch('services.summarizer_hub.modules.categorizer.Pipeline') as mock_ml_pipeline:

            mock_pipeline.return_value = Mock()
            mock_ml_pipeline.return_value = Mock()

            success = categorizer._initialize_models()
            assert success is True
            assert categorizer.initialized is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure when dependencies are not available."""
        original_available = CATEGORIZATION_AVAILABLE

        with patch('services.summarizer_hub.modules.categorizer.CATEGORIZATION_AVAILABLE', False):
            categorizer = DocumentCategorizer()
            success = categorizer._initialize_models()
            assert success is False
            assert categorizer.initialized is False

    @pytest.mark.asyncio
    async def test_get_document_text_full_content(self, sample_documents):
        """Test extracting text from document with all fields."""
        categorizer = DocumentCategorizer()
        doc = sample_documents[0]

        text = categorizer._get_document_text(doc)
        assert "REST API Authentication Guide" in text
        assert "OAuth 2.0" in text
        assert "access token" in text

    @pytest.mark.asyncio
    async def test_get_document_text_minimal_content(self):
        """Test extracting text from minimal document."""
        categorizer = DocumentCategorizer()
        doc = {"id": "test", "title": "Test Title"}

        text = categorizer._get_document_text(doc)
        assert text == "Test Title"

    @pytest.mark.asyncio
    async def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        categorizer = DocumentCategorizer()
        text = "This is a test document about API authentication and security."

        keywords = categorizer._extract_keywords(text, max_keywords=5)
        assert "test" in keywords or "document" in keywords
        assert "api" in keywords or "authentication" in keywords
        assert len(keywords) <= 5

    @pytest.mark.asyncio
    async def test_rule_based_categorization_api_doc(self, sample_documents):
        """Test rule-based categorization for API documentation."""
        categorizer = DocumentCategorizer()
        doc = sample_documents[0]  # API Authentication Guide

        result = categorizer._rule_based_categorization(
            categorizer._get_document_text(doc)
        )

        assert result['category'] in ['api_documentation', 'security']
        assert result['confidence'] > 0.0
        assert result['method'] == 'rule_based'

    @pytest.mark.asyncio
    async def test_rule_based_categorization_tutorial(self, sample_documents):
        """Test rule-based categorization for tutorial content."""
        categorizer = DocumentCategorizer()
        doc = sample_documents[1]  # Getting Started Tutorial

        result = categorizer._rule_based_categorization(
            categorizer._get_document_text(doc)
        )

        assert result['category'] in ['user_guide', 'general']
        assert result['confidence'] > 0.0

    @pytest.mark.asyncio
    async def test_generate_tags_with_category(self, sample_documents):
        """Test tag generation with category context."""
        categorizer = DocumentCategorizer()
        doc = sample_documents[0]  # API Authentication Guide
        text = categorizer._get_document_text(doc)

        tags = categorizer._generate_tags(text, "api_documentation", max_tags=3)
        assert isinstance(tags, list)
        assert len(tags) <= 3
        # Should include API-related tags
        tag_text = ' '.join(tags).lower()
        assert any(keyword in tag_text for keyword in ['api', 'authentication', 'security'])

    @pytest.mark.asyncio
    async def test_categorize_document_zero_shot(self, sample_documents, mock_zero_shot_pipeline):
        """Test document categorization with zero-shot approach."""
        categorizer = DocumentCategorizer()

        with patch.object(categorizer, '_initialize_models', return_value=True), \
             patch.object(categorizer, '_categorize_with_zero_shot') as mock_categorize, \
             patch.object(categorizer, '_generate_tags', return_value=['api', 'authentication']):

            mock_categorize.return_value = {
                'category': 'api_documentation',
                'confidence': 0.85,
                'all_scores': {'api_documentation': 0.85}
            }

            result = await categorizer.categorize_document(
                document=sample_documents[0],
                candidate_categories=['api_documentation', 'user_guide'],
                use_zero_shot=True
            )

            assert result['document_id'] == 'doc1'
            assert result['category'] == 'api_documentation'
            assert result['confidence'] == 0.85
            assert result['tags'] == ['api', 'authentication']
            assert result['method'] == 'zero_shot'

    @pytest.mark.asyncio
    async def test_categorize_document_traditional_fallback(self, sample_documents):
        """Test document categorization with traditional ML fallback."""
        categorizer = DocumentCategorizer()

        with patch.object(categorizer, '_initialize_models', return_value=True), \
             patch.object(categorizer, '_categorize_with_zero_shot', side_effect=Exception("Zero-shot failed")), \
             patch.object(categorizer, '_rule_based_categorization') as mock_rule_based, \
             patch.object(categorizer, '_generate_tags', return_value=['guide', 'tutorial']):

            mock_rule_based.return_value = {
                'category': 'user_guide',
                'confidence': 0.7,
                'method': 'rule_based'
            }

            result = await categorizer.categorize_document(
                document=sample_documents[1],  # Tutorial document
                use_zero_shot=False
            )

            assert result['category'] == 'user_guide'
            assert result['confidence'] == 0.7
            assert result['method'] == 'rule_based'

    @pytest.mark.asyncio
    async def test_categorize_document_empty_content(self):
        """Test categorization with empty document content."""
        categorizer = DocumentCategorizer()
        doc = {"id": "empty", "title": ""}

        with patch.object(categorizer, '_initialize_models', return_value=True):
            result = await categorizer.categorize_document(doc)

            assert result['category'] == 'empty'
            assert result['confidence'] == 0.0
            assert result['message'] == 'No text content found in document'

    @pytest.mark.asyncio
    async def test_categorize_documents_batch_success(self, sample_documents):
        """Test batch document categorization."""
        categorizer = DocumentCategorizer()

        mock_results = [
            {
                'document_id': 'doc1',
                'category': 'api_documentation',
                'confidence': 0.85,
                'tags': ['api', 'authentication'],
                'method': 'zero_shot'
            },
            {
                'document_id': 'doc2',
                'category': 'user_guide',
                'confidence': 0.75,
                'tags': ['tutorial', 'guide'],
                'method': 'zero_shot'
            }
        ]

        with patch.object(categorizer, 'categorize_document') as mock_categorize:
            mock_categorize.side_effect = mock_results

            result = await categorizer.categorize_documents_batch(
                documents=sample_documents[:2]
            )

            assert result['total_documents'] == 2
            assert result['successful_categorizations'] == 2
            assert len(result['results']) == 2
            assert 'summary' in result
            assert 'processing_time' in result

    @pytest.mark.asyncio
    async def test_categorize_documents_batch_empty(self):
        """Test batch categorization with empty document list."""
        categorizer = DocumentCategorizer()

        result = await categorizer.categorize_documents_batch([])

        assert result['total_documents'] == 0
        assert result['successful_categorizations'] == 0
        assert len(result['results']) == 0
        assert 'No documents provided' in result['message']


@pytest.mark.asyncio
class TestCategorizationIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_categorize_document_function(self, sample_documents):
        """Test the convenience function for single document categorization."""
        with patch('services.summarizer_hub.modules.categorizer.document_categorizer') as mock_categorizer:
            mock_categorizer.categorize_document.return_value = {
                'document_id': 'doc1',
                'category': 'api_documentation',
                'confidence': 0.85,
                'tags': ['api', 'authentication'],
                'method': 'zero_shot'
            }

            result = await categorize_document(
                document=sample_documents[0],
                candidate_categories=['api_documentation', 'user_guide']
            )

            assert result['document_id'] == 'doc1'
            assert result['category'] == 'api_documentation'
            mock_categorizer.categorize_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_categorize_documents_batch_function(self, sample_documents):
        """Test the convenience function for batch categorization."""
        with patch('services.summarizer_hub.modules.categorizer.document_categorizer') as mock_categorizer:
            mock_categorizer.categorize_documents_batch.return_value = {
                'total_documents': 2,
                'successful_categorizations': 2,
                'results': [],
                'summary': {},
                'processing_time': 1.5
            }

            result = await categorize_documents_batch(
                documents=sample_documents[:2]
            )

            assert result['total_documents'] == 2
            assert result['processing_time'] == 1.5
            mock_categorizer.categorize_documents_batch.assert_called_once()


class TestZeroShotClassification:
    """Test zero-shot classification functionality."""

    @pytest.mark.asyncio
    async def test_zero_shot_categorization_success(self, mock_zero_shot_pipeline):
        """Test successful zero-shot categorization."""
        categorizer = DocumentCategorizer()
        categorizer.zero_shot_classifier = mock_zero_shot_pipeline

        text = "This is an API documentation about authentication."
        categories = ['api_documentation', 'user_guide', 'technical_specification']

        result = categorizer._categorize_with_zero_shot(text, categories)

        assert result['category'] == 'api_documentation'
        assert result['confidence'] == 0.85
        assert 'all_scores' in result
        mock_zero_shot_pipeline.assert_called_once()

    @pytest.mark.asyncio
    async def test_zero_shot_categorization_failure(self, mock_zero_shot_pipeline):
        """Test zero-shot categorization failure handling."""
        categorizer = DocumentCategorizer()
        categorizer.zero_shot_classifier = mock_zero_shot_pipeline

        mock_zero_shot_pipeline.side_effect = Exception("Model error")

        text = "This is test content."
        categories = ['api_documentation', 'user_guide']

        result = categorizer._categorize_with_zero_shot(text, categories)

        assert result['category'] == 'uncategorized'
        assert result['confidence'] == 0.0
        assert 'error' in result


class TestRuleBasedCategorization:
    """Test rule-based categorization functionality."""

    def test_api_documentation_detection(self):
        """Test detection of API documentation patterns."""
        categorizer = DocumentCategorizer()

        text = "Learn how to use our REST API endpoints for authentication and data retrieval."
        result = categorizer._rule_based_categorization(text)

        assert result['category'] == 'api_documentation'
        assert result['confidence'] > 0.0

    def test_user_guide_detection(self):
        """Test detection of user guide patterns."""
        categorizer = DocumentCategorizer()

        text = "This guide will help you get started with our platform and configure your first project."
        result = categorizer._rule_based_categorization(text)

        assert result['category'] == 'user_guide'
        assert result['confidence'] > 0.0

    def test_troubleshooting_detection(self):
        """Test detection of troubleshooting patterns."""
        categorizer = DocumentCategorizer()

        text = "If you're experiencing connection issues, try these troubleshooting steps."
        result = categorizer._rule_based_categorization(text)

        assert result['category'] == 'troubleshooting'
        assert result['confidence'] > 0.0

    def test_general_fallback(self):
        """Test fallback to general category."""
        categorizer = DocumentCategorizer()

        text = "This is a general document about various topics without specific patterns."
        result = categorizer._rule_based_categorization(text)

        assert result['category'] == 'general'
        assert result['confidence'] >= 0.0


if __name__ == "__main__":
    pytest.main([__file__])
