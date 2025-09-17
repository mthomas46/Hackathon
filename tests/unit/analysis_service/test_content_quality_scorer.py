"""Tests for content quality scoring functionality in Analysis Service.

Tests the content quality scorer module and its integration with the analysis service.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any

from services.analysis_service.modules.content_quality_scorer import (
    ContentQualityScorer,
    assess_document_quality,
    CONTENT_QUALITY_AVAILABLE
)


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        {
            "id": "doc1",
            "title": "Getting Started Guide",
            "content": "Welcome to our comprehensive platform! This guide will walk you through the essential steps to get started. First, you need to create an account and verify your email. Then, you can explore the dashboard and begin using our powerful features. We recommend starting with the basic tutorial to understand the core concepts before diving into advanced functionality.",
            "metadata": {
                "author": "John Doe",
                "type": "documentation",
                "tags": ["tutorial", "beginner", "getting-started"]
            }
        },
        {
            "id": "doc2",
            "title": "API Reference",
            "content": "The API provides comprehensive endpoints for data management. GET /users - Retrieve user information. POST /users - Create new user. PUT /users/{id} - Update user details. DELETE /users/{id} - Remove user. All endpoints require authentication via Bearer token in the Authorization header.",
            "metadata": {
                "author": "Jane Smith",
                "type": "reference",
                "tags": ["api", "reference", "technical"]
            }
        },
        {
            "id": "doc3",
            "title": "Troubleshooting Network Issues",
            "content": "Having trouble connecting? Don't worry! Here are the most common network problems and how to fix them. Problem 1: Connection timeout. Solution: Check your firewall settings and ensure port 443 is open. Problem 2: DNS resolution failed. Solution: Verify your DNS settings or try using Google's DNS (8.8.8.8).",
            "metadata": {
                "author": "Bob Wilson",
                "type": "support",
                "tags": ["troubleshooting", "network", "support"]
            }
        }
    ]


class TestContentQualityScorer:
    """Test the ContentQualityScorer class."""

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization of the quality scorer."""
        scorer = ContentQualityScorer()
        success = scorer._initialize_scorer()
        assert success is True
        assert scorer.initialized is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure when dependencies are not available."""
        original_available = CONTENT_QUALITY_AVAILABLE

        with patch('services.analysis_service.modules.content_quality_scorer.CONTENT_QUALITY_AVAILABLE', False):
            scorer = ContentQualityScorer()
            success = scorer._initialize_scorer()
            assert success is False
            assert scorer.initialized is False

    @pytest.mark.asyncio
    async def test_extract_text_content_full(self, sample_documents):
        """Test extracting text content from complete document."""
        scorer = ContentQualityScorer()

        text = scorer._extract_text_content(sample_documents[0])
        assert "Getting Started Guide" in text
        assert "Welcome to our comprehensive platform" in text
        assert "John Doe" in text  # Should include metadata

    @pytest.mark.asyncio
    async def test_extract_text_content_minimal(self):
        """Test extracting text content from minimal document."""
        scorer = ContentQualityScorer()

        doc = {"id": "test", "title": "Test Title"}
        text = scorer._extract_text_content(doc)
        assert text == "Test Title"

    @pytest.mark.asyncio
    async def test_tokenize_content_with_nltk(self, sample_documents):
        """Test content tokenization with NLTK."""
        scorer = ContentQualityScorer()

        text = "This is a test sentence. It has multiple parts!"
        sentences, words = scorer._tokenize_content(text)

        assert len(sentences) >= 1
        assert len(words) >= 5
        assert "test" in [w.lower() for w in words]

    @pytest.mark.asyncio
    async def test_calculate_readability_metrics_simple(self):
        """Test readability metrics calculation with simple text."""
        scorer = ContentQualityScorer()

        text = "This is a simple test document. It contains basic sentences for analysis."
        result = scorer._calculate_readability_metrics(text)

        assert 'sentence_count' in result
        assert 'word_count' in result
        assert 'readability_score' in result
        assert 'flesch_kincaid_grade' in result
        assert result['word_count'] > 0
        assert result['sentence_count'] > 0
        assert 0 <= result['readability_score'] <= 1

    @pytest.mark.asyncio
    async def test_calculate_readability_metrics_complex(self):
        """Test readability metrics with more complex text."""
        scorer = ContentQualityScorer()

        text = "The implementation utilizes sophisticated algorithms for data processing and analysis. Consequently, the system architecture incorporates multiple layers of abstraction to facilitate scalability and maintainability. Furthermore, the integration with external services requires careful consideration of security protocols and authentication mechanisms."
        result = scorer._calculate_readability_metrics(text)

        assert result['flesch_kincaid_grade'] > 12  # Should be fairly difficult
        assert result['readability_level'] in ['difficult', 'very_difficult']

    @pytest.mark.asyncio
    async def test_count_syllables(self):
        """Test syllable counting functionality."""
        scorer = ContentQualityScorer()

        assert scorer._count_syllables("test") == 1
        assert scorer._count_syllables("testing") == 2
        assert scorer._count_syllables("implementation") == 5
        assert scorer._count_syllables("Hello world!") == 3

    @pytest.mark.asyncio
    async def test_interpret_readability_levels(self):
        """Test readability level interpretation."""
        scorer = ContentQualityScorer()

        assert scorer._interpret_readability_level(4) == "very_easy"
        assert scorer._interpret_readability_level(8) == "easy"
        assert scorer._interpret_readability_level(12) == "standard"
        assert scorer._interpret_readability_level(16) == "difficult"
        assert scorer._interpret_readability_level(20) == "very_difficult"

    @pytest.mark.asyncio
    async def test_assess_content_structure_good(self, sample_documents):
        """Test content structure assessment with well-structured content."""
        scorer = ContentQualityScorer()

        text = "# Introduction\n\nThis guide explains the basics.\n\n## Getting Started\n\nFollow these steps:\n- Step 1\n- Step 2\n\n## Next Steps\n\nFor more information..."
        sentences = [s.strip() for s in text.split('.') if s.strip()]

        result = scorer._assess_content_structure(text, sentences)

        assert 'structure_score' in result
        assert 'heading_count' in result
        assert 'list_count' in result
        assert result['heading_count'] >= 2
        assert result['structure_score'] > 0.5

    @pytest.mark.asyncio
    async def test_assess_content_structure_poor(self):
        """Test content structure assessment with poorly structured content."""
        scorer = ContentQualityScorer()

        text = "This is just a bunch of text without any structure or headings. It goes on and on without clear organization or formatting."
        sentences = [s.strip() for s in text.split('.') if s.strip()]

        result = scorer._assess_content_structure(text, sentences)

        assert result['heading_count'] == 0
        assert result['structure_score'] < 0.3

    @pytest.mark.asyncio
    async def test_assess_content_completeness_good(self, sample_documents):
        """Test completeness assessment with comprehensive content."""
        scorer = ContentQualityScorer()

        # Content that includes multiple documentation elements
        text = "Welcome to our guide! This tutorial will help you get started. Here are the requirements: Python 3.8+. Here's how to install: pip install our-package. For examples, see the code below. For troubleshooting, check the FAQ."
        doc = sample_documents[0]

        result = scorer._assess_content_completeness(text, doc)

        assert 'completeness_score' in result
        assert 'found_elements' in result
        assert 'introduction' in result['found_elements']
        assert 'requirements' in result['found_elements']
        assert result['completeness_score'] > 0.5

    @pytest.mark.asyncio
    async def test_assess_content_completeness_poor(self):
        """Test completeness assessment with incomplete content."""
        scorer = ContentQualityScorer()

        text = "This is just a short note."  # Very minimal content
        doc = {"id": "test"}

        result = scorer._assess_content_completeness(text, doc)

        assert result['word_count'] < 10
        assert result['completeness_score'] < 0.3

    @pytest.mark.asyncio
    async def test_assess_technical_accuracy_good(self):
        """Test technical accuracy assessment with clean content."""
        scorer = ContentQualityScorer()

        text = "This document is well-written and properly formatted. It follows standard conventions and uses appropriate terminology."
        doc = {"id": "test"}

        result = scorer._assess_technical_accuracy(text, doc)

        assert 'accuracy_score' in result
        assert 'issue_count' in result
        assert result['accuracy_score'] > 0.8  # Should be high for clean content

    @pytest.mark.asyncio
    async def test_assess_technical_accuracy_with_issues(self):
        """Test technical accuracy assessment with problematic content."""
        scorer = ContentQualityScorer()

        text = "This document has some isses. It contains grammer errors and uses caps lock too much. THE CONTENT IS SHOUTING!"
        doc = {"id": "test"}

        result = scorer._assess_technical_accuracy(text, doc)

        assert result['issue_count'] > 0
        assert result['caps_ratio'] > 0.1
        assert result['accuracy_score'] < 0.8  # Should be lower due to issues

    @pytest.mark.asyncio
    async def test_calculate_overall_quality_score(self):
        """Test overall quality score calculation."""
        scorer = ContentQualityScorer()

        readability_score = 0.8
        structure_score = 0.7
        completeness_score = 0.9
        accuracy_score = 0.85

        result = scorer._calculate_overall_quality_score(
            readability_score, structure_score, completeness_score, accuracy_score
        )

        assert 'overall_score' in result
        assert 'grade' in result
        assert 'component_scores' in result
        assert result['overall_score'] > 0.8  # Should be high for good components
        assert result['grade'] in ['A', 'B', 'C', 'D', 'F']

    @pytest.mark.asyncio
    async def test_generate_recommendations_comprehensive(self):
        """Test recommendation generation for various scenarios."""
        scorer = ContentQualityScorer()

        # Test with readability issues
        readability_data = {'flesch_kincaid_grade': 16, 'readability_score': 0.4}
        structure_data = {'structure_score': 0.8}
        completeness_data = {'found_elements': ['introduction', 'examples']}
        accuracy_data = {'issue_count': 2}

        recommendations = scorer._generate_quality_recommendations(
            readability_data, structure_data, completeness_data, accuracy_data
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Should include readability improvement suggestions
        recommendation_text = ' '.join(recommendations).lower()
        assert any(word in recommendation_text for word in ['readability', 'simplify', 'sentences', 'review', 'correct'])

    @pytest.mark.asyncio
    async def test_assess_content_quality_full(self, sample_documents):
        """Test full content quality assessment pipeline."""
        scorer = ContentQualityScorer()

        result = await scorer.assess_content_quality(sample_documents[0])

        assert 'document_id' in result
        assert 'quality_assessment' in result
        assert 'detailed_metrics' in result
        assert 'recommendations' in result
        assert 'processing_time' in result

        quality = result['quality_assessment']
        assert 'overall_score' in quality
        assert 'grade' in quality
        assert 'component_scores' in quality

        metrics = result['detailed_metrics']
        assert 'readability' in metrics
        assert 'structure' in metrics
        assert 'completeness' in metrics
        assert 'accuracy' in metrics

    @pytest.mark.asyncio
    async def test_assess_content_quality_empty_content(self):
        """Test quality assessment with empty document content."""
        scorer = ContentQualityScorer()

        doc = {"id": "empty", "title": "", "content": ""}
        result = await scorer.assess_content_quality(doc)

        assert result['document_id'] == 'empty'
        assert 'No content found' in result['quality_assessment']['description']
        assert result['quality_assessment']['overall_score'] == 0.0

    @pytest.mark.asyncio
    async def test_assess_content_quality_error_handling(self, sample_documents):
        """Test error handling in quality assessment."""
        scorer = ContentQualityScorer()

        with patch.object(scorer, '_initialize_scorer', side_effect=Exception("Init failed")):
            result = await scorer.assess_content_quality(sample_documents[0])

            assert 'error' in result
            assert 'not available' in result['message'].lower()


@pytest.mark.asyncio
class TestContentQualityIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_assess_document_quality_function(self, sample_documents):
        """Test the convenience function for quality assessment."""
        with patch('services.analysis_service.modules.content_quality_scorer.content_quality_scorer') as mock_scorer:
            mock_scorer.assess_content_quality.return_value = {
                'document_id': 'doc1',
                'quality_assessment': {
                    'overall_score': 0.85,
                    'grade': 'B',
                    'description': 'Very Good',
                    'component_scores': {'readability': 0.8, 'structure': 0.9}
                },
                'detailed_metrics': {},
                'recommendations': ['Good job!'],
                'processing_time': 1.2
            }

            result = await assess_document_quality(sample_documents[0])

            assert result['document_id'] == 'doc1'
            assert result['quality_assessment']['grade'] == 'B'
            mock_scorer.assess_content_quality.assert_called_once()


class TestQualityAssessmentHandlers:
    """Test the analysis handlers integration."""

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        client = Mock()
        client.doc_store_url.return_value = "http://docstore:5000"
        client.get_json = Mock()
        return client

    @pytest.mark.asyncio
    async def test_handle_content_quality_assessment_success(self, mock_service_client, sample_documents):
        """Test successful content quality assessment handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import ContentQualityRequest

        with patch('services.analysis_service.modules.analysis_handlers.get_analysis_service_client', return_value=mock_service_client), \
             patch('services.analysis_service.modules.analysis_handlers.assess_document_quality') as mock_assess:

            mock_service_client.get_json.return_value = sample_documents[0]
            mock_assess.return_value = {
                'document_id': 'doc1',
                'quality_assessment': {
                    'overall_score': 0.85,
                    'grade': 'B',
                    'description': 'Very Good',
                    'component_scores': {'readability': 0.8, 'structure': 0.9},
                    'component_weights': {'readability': 0.25, 'structure': 0.2}
                },
                'detailed_metrics': {
                    'readability': {'readability_score': 0.8},
                    'structure': {'structure_score': 0.9}
                },
                'recommendations': ['Excellent structure', 'Good readability'],
                'processing_time': 1.5,
                'analysis_timestamp': 1234567890.0
            }

            request = ContentQualityRequest(
                document_id="doc1",
                include_detailed_metrics=True
            )

            result = await AnalysisHandlers.handle_content_quality_assessment(request)

            assert result.document_id == 'doc1'
            assert result.quality_assessment['grade'] == 'B'
            assert result.quality_assessment['overall_score'] == 0.85
            assert result.detailed_metrics is not None
            assert len(result.recommendations) == 2
            assert result.processing_time == 1.5

    @pytest.mark.asyncio
    async def test_handle_content_quality_assessment_no_detailed_metrics(self, mock_service_client, sample_documents):
        """Test quality assessment without detailed metrics."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import ContentQualityRequest

        with patch('services.analysis_service.modules.analysis_handlers.get_analysis_service_client', return_value=mock_service_client), \
             patch('services.analysis_service.modules.analysis_handlers.assess_document_quality') as mock_assess:

            mock_service_client.get_json.return_value = sample_documents[0]
            mock_assess.return_value = {
                'document_id': 'doc1',
                'quality_assessment': {'overall_score': 0.75, 'grade': 'C'},
                'detailed_metrics': {'readability': {}, 'structure': {}},
                'recommendations': ['Consider improving structure'],
                'processing_time': 1.2
            }

            request = ContentQualityRequest(
                document_id="doc1",
                include_detailed_metrics=False
            )

            result = await AnalysisHandlers.handle_content_quality_assessment(request)

            assert result.document_id == 'doc1'
            assert result.detailed_metrics is None  # Should be None when not requested
            assert result.quality_assessment['grade'] == 'C'

    @pytest.mark.asyncio
    async def test_handle_content_quality_assessment_document_not_found(self, mock_service_client):
        """Test handling when document is not found."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import ContentQualityRequest

        with patch('services.analysis_service.modules.analysis_handlers.get_analysis_service_client', return_value=mock_service_client):
            mock_service_client.get_json.return_value = None

            request = ContentQualityRequest(document_id="nonexistent")

            result = await AnalysisHandlers.handle_content_quality_assessment(request)

            assert result.document_id == 'nonexistent'
            assert result.quality_assessment['grade'] == 'F'
            assert 'Document not found' in result.quality_assessment['description']
            assert result.quality_assessment['overall_score'] == 0.0


if __name__ == "__main__":
    pytest.main([__file__])
