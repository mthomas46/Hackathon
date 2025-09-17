"""Tests for sentiment analysis functionality in Analysis Service.

Tests the sentiment analyzer module and its integration with the analysis service.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from services.analysis_service.modules.sentiment_analyzer import (
    SentimentAnalyzer,
    analyze_document_sentiment,
    SENTIMENT_ANALYSIS_AVAILABLE
)


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        {
            "id": "doc1",
            "title": "Getting Started Guide",
            "content": "Welcome to our amazing platform! This comprehensive guide will help you get started quickly and easily. We're excited to have you here and can't wait to see what you'll build.",
            "metadata": {
                "author": "John Doe",
                "type": "documentation",
                "tags": ["tutorial", "beginner"]
            }
        },
        {
            "id": "doc2",
            "title": "Troubleshooting Common Issues",
            "content": "If you're experiencing problems with the system, don't worry! Here are some common issues and their solutions. First, check your configuration files for any errors.",
            "metadata": {
                "author": "Jane Smith",
                "type": "support",
                "tags": ["troubleshooting", "errors"]
            }
        },
        {
            "id": "doc3",
            "title": "API Reference Documentation",
            "content": "The API provides endpoints for user management, data processing, and system integration. Each endpoint requires proper authentication and follows RESTful conventions.",
            "metadata": {
                "author": "Bob Wilson",
                "type": "reference",
                "tags": ["api", "reference"]
            }
        }
    ]


@pytest.fixture
def mock_textblob():
    """Mock TextBlob for testing."""
    mock_blob = Mock()
    mock_blob.sentiment.polarity = 0.8
    mock_blob.sentiment.subjectivity = 0.6
    return mock_blob


@pytest.fixture
def mock_sentiment_pipeline():
    """Mock transformer sentiment pipeline."""
    mock_pipeline = Mock()
    mock_pipeline.return_value = [
        {'label': 'LABEL_2', 'score': 0.9},  # Positive
        {'label': 'LABEL_0', 'score': 0.05},  # Negative
        {'label': 'LABEL_1', 'score': 0.05}   # Neutral
    ]
    return mock_pipeline


class TestSentimentAnalyzer:
    """Test the SentimentAnalyzer class."""

    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful initialization of the sentiment analyzer."""
        analyzer = SentimentAnalyzer()

        with patch('services.analysis_service.modules.sentiment_analyzer.pipeline') as mock_pipeline, \
             patch('services.analysis_service.modules.sentiment_analyzer.nltk') as mock_nltk:

            mock_pipeline.return_value = Mock()
            mock_nltk.download.return_value = True

            success = analyzer._initialize_models()
            assert success is True
            assert analyzer.initialized is True

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure when dependencies are not available."""
        original_available = SENTIMENT_ANALYSIS_AVAILABLE

        with patch('services.analysis_service.modules.sentiment_analyzer.SENTIMENT_ANALYSIS_AVAILABLE', False):
            analyzer = SentimentAnalyzer()
            success = analyzer._initialize_models()
            assert success is False
            assert analyzer.initialized is False

    @pytest.mark.asyncio
    async def test_analyze_sentiment_textblob_positive(self, mock_textblob):
        """Test TextBlob sentiment analysis with positive text."""
        analyzer = SentimentAnalyzer()

        with patch('services.analysis_service.modules.sentiment_analyzer.TextBlob', return_value=mock_textblob):
            result = analyzer._analyze_sentiment_textblob("This is amazing!")

            assert result['sentiment'] == 'positive'
            assert result['polarity'] == 0.8
            assert result['subjectivity'] == 0.6
            assert result['confidence'] > 0
            assert result['method'] == 'textblob'

    @pytest.mark.asyncio
    async def test_analyze_sentiment_textblob_negative(self):
        """Test TextBlob sentiment analysis with negative text."""
        analyzer = SentimentAnalyzer()

        mock_blob = Mock()
        mock_blob.sentiment.polarity = -0.6
        mock_blob.sentiment.subjectivity = 0.8

        with patch('services.analysis_service.modules.sentiment_analyzer.TextBlob', return_value=mock_blob):
            result = analyzer._analyze_sentiment_textblob("This is terrible!")

            assert result['sentiment'] == 'negative'
            assert result['polarity'] == -0.6
            assert result['subjectivity'] == 0.8

    @pytest.mark.asyncio
    async def test_analyze_sentiment_transformer_success(self, mock_sentiment_pipeline):
        """Test transformer-based sentiment analysis."""
        analyzer = SentimentAnalyzer()
        analyzer.sentiment_pipeline = mock_sentiment_pipeline

        result = analyzer._analyze_sentiment_transformer("This is great!")

        assert result['sentiment'] == 'positive'
        assert result['confidence'] == 0.9
        assert result['method'] == 'transformer'
        assert 'all_scores' in result

    @pytest.mark.asyncio
    async def test_analyze_sentiment_transformer_fallback(self, mock_textblob):
        """Test transformer fallback to TextBlob."""
        analyzer = SentimentAnalyzer()
        analyzer.sentiment_pipeline = None  # Force fallback

        with patch('services.analysis_service.modules.sentiment_analyzer.TextBlob', return_value=mock_textblob):
            result = analyzer._analyze_sentiment_transformer("Test text")

            assert result['method'] == 'textblob'
            assert result['polarity'] == 0.8

    @pytest.mark.asyncio
    async def test_calculate_readability_metrics_simple(self):
        """Test readability metrics calculation with simple text."""
        analyzer = SentimentAnalyzer()

        text = "This is a simple sentence. It has basic words and structure."
        result = analyzer._calculate_readability_metrics(text)

        assert 'sentence_count' in result
        assert 'word_count' in result
        assert 'character_count' in result
        assert 'readability_score' in result
        assert 'clarity_score' in result
        assert result['word_count'] > 0
        assert result['sentence_count'] > 0

    @pytest.mark.asyncio
    async def test_assess_clarity_good_text(self):
        """Test clarity assessment with clear, well-written text."""
        analyzer = SentimentAnalyzer()

        sentences = ["This is a clear and concise sentence.", "It uses simple language.", "The structure is easy to follow."]
        content_words = ["clear", "concise", "sentence", "simple", "language", "structure", "easy", "follow"]

        clarity = analyzer._assess_clarity("Test text", sentences, content_words)
        assert 0.0 <= clarity <= 1.0
        assert clarity > 0.5  # Should be reasonably high for clear text

    @pytest.mark.asyncio
    async def test_interpret_readability_levels(self):
        """Test readability level interpretation."""
        analyzer = SentimentAnalyzer()

        assert analyzer._interpret_readability(4) == "very_easy"
        assert analyzer._interpret_readability(8) == "easy"
        assert analyzer._interpret_readability(12) == "standard"
        assert analyzer._interpret_readability(16) == "difficult"
        assert analyzer._interpret_readability(20) == "very_difficult"

    @pytest.mark.asyncio
    async def test_analyze_tone_patterns_positive(self):
        """Test tone analysis with positive content."""
        analyzer = SentimentAnalyzer()

        text = "This is amazing! We're so excited and happy to help you succeed."
        result = analyzer._analyze_tone_patterns(text)

        assert result['primary_tone'] in ['encouraging', 'positive', 'neutral']
        assert 'positive' in result['tone_scores']
        assert result['tone_scores']['positive'] > 0
        assert result['tone_indicators']['positive_words'] > 0

    @pytest.mark.asyncio
    async def test_analyze_tone_patterns_technical(self):
        """Test tone analysis with technical content."""
        analyzer = SentimentAnalyzer()

        text = "The implementation requires configuration of the database schema and integration with the authentication framework."
        result = analyzer._analyze_tone_patterns(text)

        assert 'technical' in result['tone_scores']
        assert result['tone_indicators']['technical_terms'] > 0

    @pytest.mark.asyncio
    async def test_calculate_overall_quality_score(self):
        """Test overall quality score calculation."""
        analyzer = SentimentAnalyzer()

        sentiment = {'sentiment': 'positive', 'polarity': 0.8, 'confidence': 0.9}
        readability = {'readability_score': 8.5, 'clarity_score': 0.8}

        score = analyzer._calculate_overall_quality_score(sentiment, readability)
        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Should be high for good sentiment and readability

    @pytest.mark.asyncio
    async def test_generate_recommendations_positive(self):
        """Test recommendation generation for positive analysis."""
        analyzer = SentimentAnalyzer()

        sentiment = {'sentiment': 'positive'}
        readability = {'flesch_kincaid_grade': 8.0, 'clarity_score': 0.9}
        tone = {'primary_tone': 'encouraging'}

        recommendations = analyzer._generate_recommendations(sentiment, readability, tone)
        assert isinstance(recommendations, list)
        # Should not have major recommendations for good content
        assert len(recommendations) >= 0

    @pytest.mark.asyncio
    async def test_generate_recommendations_improvement_needed(self):
        """Test recommendation generation for content needing improvement."""
        analyzer = SentimentAnalyzer()

        sentiment = {'sentiment': 'negative'}
        readability = {'flesch_kincaid_grade': 18.0, 'clarity_score': 0.3}
        tone = {'primary_tone': 'technical'}

        recommendations = analyzer._generate_recommendations(sentiment, readability, tone)
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Should contain improvement suggestions
        recommendation_text = ' '.join(recommendations).lower()
        assert any(word in recommendation_text for word in ['simplify', 'revise', 'improve', 'language'])

    @pytest.mark.asyncio
    async def test_analyze_sentiment_and_clarity_full(self, sample_documents, mock_textblob):
        """Test full sentiment and clarity analysis."""
        analyzer = SentimentAnalyzer()

        with patch.object(analyzer, '_initialize_models', return_value=True), \
             patch('services.analysis_service.modules.sentiment_analyzer.TextBlob', return_value=mock_textblob):

            result = await analyzer.analyze_sentiment_and_clarity(
                document=sample_documents[0],
                use_transformer=False,
                include_tone_analysis=True
            )

            assert 'document_id' in result
            assert 'sentiment_analysis' in result
            assert 'readability_metrics' in result
            assert 'tone_analysis' in result
            assert 'quality_score' in result
            assert 'recommendations' in result
            assert 'processing_time' in result

    @pytest.mark.asyncio
    async def test_analyze_sentiment_and_clarity_empty_content(self):
        """Test analysis with empty document content."""
        analyzer = SentimentAnalyzer()

        with patch.object(analyzer, '_initialize_models', return_value=True):
            result = await analyzer.analyze_sentiment_and_clarity(
                document={"id": "empty", "title": "", "content": ""},
                use_transformer=False,
                include_tone_analysis=False
            )

            assert result['document_id'] == 'empty'
            assert 'No text content' in result['sentiment_analysis'].get('message', '')

    @pytest.mark.asyncio
    async def test_analyze_sentiment_and_clarity_error_handling(self, sample_documents):
        """Test error handling in sentiment analysis."""
        analyzer = SentimentAnalyzer()

        with patch.object(analyzer, '_initialize_models', side_effect=Exception("Init failed")):
            result = await analyzer.analyze_sentiment_and_clarity(
                document=sample_documents[0]
            )

            assert 'error' in result
            assert 'not available' in result['message'].lower()


@pytest.mark.asyncio
class TestSentimentAnalysisIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_analyze_document_sentiment_function(self, sample_documents):
        """Test the convenience function for sentiment analysis."""
        with patch('services.analysis_service.modules.sentiment_analyzer.sentiment_analyzer') as mock_analyzer:
            mock_analyzer.analyze_sentiment_and_clarity.return_value = {
                'document_id': 'doc1',
                'sentiment_analysis': {'sentiment': 'positive', 'confidence': 0.8},
                'readability_metrics': {'readability_score': 8.5},
                'tone_analysis': {'primary_tone': 'encouraging'},
                'quality_score': 0.85,
                'recommendations': ['Good job!'],
                'processing_time': 1.2
            }

            result = await analyze_document_sentiment(
                document=sample_documents[0],
                use_transformer=False,
                include_tone_analysis=True
            )

            assert result['document_id'] == 'doc1'
            assert result['sentiment_analysis']['sentiment'] == 'positive'
            assert result['quality_score'] == 0.85
            mock_analyzer.analyze_sentiment_and_clarity.assert_called_once()


class TestSentimentAnalysisHandlers:
    """Test the analysis handlers integration."""

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        client = Mock()
        client.doc_store_url.return_value = "http://docstore:5000"
        client.get_json = Mock()
        return client

    @pytest.mark.asyncio
    async def test_handle_sentiment_analysis_success(self, mock_service_client, sample_documents):
        """Test successful sentiment analysis handling."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import SentimentAnalysisRequest

        # Mock successful analysis
        with patch('services.analysis_service.modules.analysis_handlers.get_analysis_service_client', return_value=mock_service_client), \
             patch('services.analysis_service.modules.analysis_handlers.analyze_document_sentiment') as mock_analyze:

            mock_service_client.get_json.return_value = sample_documents[0]
            mock_analyze.return_value = {
                'document_id': 'doc1',
                'sentiment_analysis': {'sentiment': 'positive', 'confidence': 0.8, 'polarity': 0.6},
                'readability_metrics': {'readability_score': 8.5, 'clarity_score': 0.7},
                'tone_analysis': {'primary_tone': 'encouraging'},
                'quality_score': 0.82,
                'recommendations': ['Excellent tone and clarity'],
                'processing_time': 1.5
            }

            request = SentimentAnalysisRequest(
                document_id="doc1",
                use_transformer=True,
                include_tone_analysis=True
            )

            result = await AnalysisHandlers.handle_sentiment_analysis(request)

            assert result.document_id == 'doc1'
            assert result.sentiment_analysis['sentiment'] == 'positive'
            assert result.quality_score == 0.82
            assert len(result.recommendations) > 0
            assert result.processing_time == 1.5

    @pytest.mark.asyncio
    async def test_handle_sentiment_analysis_document_not_found(self, mock_service_client):
        """Test handling when document is not found."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import SentimentAnalysisRequest

        with patch('services.analysis_service.modules.analysis_handlers.get_analysis_service_client', return_value=mock_service_client):
            mock_service_client.get_json.return_value = None

            request = SentimentAnalysisRequest(document_id="nonexistent")

            result = await AnalysisHandlers.handle_sentiment_analysis(request)

            assert result.document_id == 'nonexistent'
            assert 'Document not found' in result.sentiment_analysis.get('error', '')
            assert result.quality_score == 0.0

    @pytest.mark.asyncio
    async def test_handle_tone_analysis_full_scope(self, mock_service_client, sample_documents):
        """Test tone analysis with full scope."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import ToneAnalysisRequest

        with patch('services.analysis_service.modules.analysis_handlers.get_analysis_service_client', return_value=mock_service_client), \
             patch('services.analysis_service.modules.analysis_handlers.analyze_document_sentiment') as mock_analyze:

            mock_service_client.get_json.return_value = sample_documents[0]
            mock_analyze.return_value = {
                'document_id': 'doc1',
                'sentiment_analysis': {'sentiment': 'positive', 'confidence': 0.8},
                'readability_metrics': {'readability_score': 8.5, 'clarity_score': 0.7},
                'tone_analysis': {
                    'primary_tone': 'encouraging',
                    'tone_scores': {'positive': 2.1, 'professional': 0.5},
                    'tone_indicators': {'positive_words': 3, 'professional_phrases': 1}
                },
                'processing_time': 1.2
            }

            request = ToneAnalysisRequest(
                document_id="doc1",
                analysis_scope="full"
            )

            result = await AnalysisHandlers.handle_tone_analysis(request)

            assert result.document_id == 'doc1'
            assert result.primary_tone == 'encouraging'
            assert 'positive' in result.tone_scores
            assert result.sentiment_summary['sentiment'] == 'positive'
            assert result.clarity_assessment['readability_score'] == 8.5

    @pytest.mark.asyncio
    async def test_handle_tone_analysis_sentiment_only_scope(self, mock_service_client, sample_documents):
        """Test tone analysis with sentiment-only scope."""
        from services.analysis_service.modules.analysis_handlers import AnalysisHandlers
        from services.analysis_service.modules.models import ToneAnalysisRequest

        with patch('services.analysis_service.modules.analysis_handlers.get_analysis_service_client', return_value=mock_service_client), \
             patch('services.analysis_service.modules.analysis_handlers.analyze_document_sentiment') as mock_analyze:

            mock_service_client.get_json.return_value = sample_documents[0]
            mock_analyze.return_value = {
                'document_id': 'doc1',
                'sentiment_analysis': {'sentiment': 'positive', 'confidence': 0.8},
                'processing_time': 1.2
            }

            request = ToneAnalysisRequest(
                document_id="doc1",
                analysis_scope="sentiment_only"
            )

            result = await AnalysisHandlers.handle_tone_analysis(request)

            assert result.document_id == 'doc1'
            assert result.primary_tone == 'unknown'
            assert result.sentiment_summary['sentiment'] == 'positive'
            assert result.tone_scores == {}
            assert result.clarity_assessment == {}


if __name__ == "__main__":
    pytest.main([__file__])
