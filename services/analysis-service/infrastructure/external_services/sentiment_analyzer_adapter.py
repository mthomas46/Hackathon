"""Sentiment analyzer adapter for external sentiment analysis services."""

import asyncio
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import time
from enum import Enum

from ...domain.exceptions import SentimentAnalysisException
from ..config import ExternalServiceConfig


class SentimentLabel(Enum):
    """Sentiment labels."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SentimentAnalysisResult:
    """Result of sentiment analysis."""

    def __init__(self,
                 document_id: str,
                 sentiment: SentimentLabel,
                 confidence: float,
                 scores: Optional[Dict[str, float]] = None,
                 aspects: Optional[Dict[str, Any]] = None,
                 processing_time: float = 0.0):
        """Initialize sentiment analysis result."""
        self.document_id = document_id
        self.sentiment = sentiment
        self.confidence = confidence
        self.scores = scores or {}
        self.aspects = aspects or {}
        self.processing_time = processing_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'document_id': self.document_id,
            'sentiment': self.sentiment.value,
            'confidence': self.confidence,
            'scores': self.scores,
            'aspects': self.aspects,
            'processing_time': self.processing_time
        }


class SentimentAnalyzerAdapter(ABC):
    """Abstract adapter for sentiment analysis services."""

    def __init__(self, config: ExternalServiceConfig):
        """Initialize adapter with configuration."""
        self.config = config
        self._retry_config = config.get_retry_config()

    @abstractmethod
    async def analyze_sentiment(self, document_text: str, document_id: str) -> SentimentAnalysisResult:
        """Analyze sentiment of document."""
        pass

    @abstractmethod
    async def analyze_tone(self, document_text: str, document_id: str) -> Dict[str, Any]:
        """Analyze tone and writing style of document."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is available."""
        pass


class LocalSentimentAnalyzerAdapter(SentimentAnalyzerAdapter):
    """Local implementation using basic text processing."""

    def __init__(self, config: ExternalServiceConfig):
        """Initialize local sentiment analyzer."""
        super().__init__(config)
        self.confidence_threshold = config.get_sentiment_config().get('confidence_threshold', 0.6)

    async def analyze_sentiment(self, document_text: str, document_id: str) -> SentimentAnalysisResult:
        """Analyze sentiment using basic text processing."""
        start_time = time.time()

        try:
            # Simple sentiment analysis based on keyword matching
            positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like', 'best'}
            negative_words = {'bad', 'terrible', 'awful', 'hate', 'worst', 'poor', 'disappointing', 'fail'}

            words = document_text.lower().split()
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            neutral_count = len(words) - positive_count - negative_count

            # Calculate sentiment scores
            total_words = len(words)
            if total_words == 0:
                sentiment = SentimentLabel.NEUTRAL
                confidence = 0.0
            else:
                positive_score = positive_count / total_words
                negative_score = negative_count / total_words
                neutral_score = neutral_count / total_words

                if positive_score > negative_score and positive_score > 0.1:
                    sentiment = SentimentLabel.POSITIVE
                    confidence = positive_score
                elif negative_score > positive_score and negative_score > 0.1:
                    sentiment = SentimentLabel.NEGATIVE
                    confidence = negative_score
                else:
                    sentiment = SentimentLabel.NEUTRAL
                    confidence = neutral_score

            scores = {
                'positive': positive_score,
                'negative': negative_score,
                'neutral': neutral_score
            }

            processing_time = time.time() - start_time

            return SentimentAnalysisResult(
                document_id=document_id,
                sentiment=sentiment,
                confidence=min(confidence, 1.0),  # Cap at 1.0
                scores=scores,
                processing_time=processing_time
            )

        except Exception as e:
            raise SentimentAnalysisException("LocalSentimentAnalyzer", str(e))

    async def analyze_tone(self, document_text: str, document_id: str) -> Dict[str, Any]:
        """Analyze tone using basic text processing."""
        # Simple tone analysis
        text_lower = document_text.lower()

        # Check for formal vs informal language
        formal_indicators = ['therefore', 'however', 'consequently', 'moreover', 'furthermore', 'accordingly']
        informal_indicators = ['like', 'kinda', 'sorta', 'totally', 'awesome', 'cool']

        formal_count = sum(1 for word in formal_indicators if word in text_lower)
        informal_count = sum(1 for word in informal_indicators if word in text_lower)

        if formal_count > informal_count:
            tone = "formal"
            confidence = min(formal_count / len(text_lower.split()) * 10, 1.0)
        elif informal_count > formal_count:
            tone = "informal"
            confidence = min(informal_count / len(text_lower.split()) * 10, 1.0)
        else:
            tone = "neutral"
            confidence = 0.5

        return {
            'document_id': document_id,
            'tone': tone,
            'confidence': confidence,
            'formal_indicators': formal_count,
            'informal_indicators': informal_count,
            'readability_score': self._calculate_readability(text_lower)
        }

    def is_available(self) -> bool:
        """Check if local analyzer is available."""
        return True

    def _calculate_readability(self, text: str) -> float:
        """Calculate basic readability score."""
        sentences = text.split('.')
        words = text.split()
        avg_words_per_sentence = len(words) / len(sentences) if sentences else 0

        # Simple readability score (lower is easier to read)
        if avg_words_per_sentence < 10:
            return 0.9  # Easy
        elif avg_words_per_sentence < 20:
            return 0.7  # Medium
        else:
            return 0.4  # Hard


class TransformersSentimentAnalyzerAdapter(SentimentAnalyzerAdapter):
    """Hugging Face Transformers-based sentiment analyzer."""

    def __init__(self, config: ExternalServiceConfig):
        """Initialize transformers sentiment analyzer."""
        super().__init__(config)
        self.model_name = config.get_sentiment_config().get('model', 'cardiffnlp/twitter-roberta-base-sentiment-latest')
        self.confidence_threshold = config.get_sentiment_config().get('confidence_threshold', 0.6)
        self._model = None  # Lazy loading

    async def analyze_sentiment(self, document_text: str, document_id: str) -> SentimentAnalysisResult:
        """Analyze sentiment using transformers model."""
        start_time = time.time()

        try:
            # Lazy load the model
            if self._model is None:
                await self._load_model()

            # Truncate text if too long (model has token limits)
            truncated_text = document_text[:512] if len(document_text) > 512 else document_text

            # Mock sentiment analysis (in real implementation, this would use the transformers model)
            sentiment_result = await self._analyze_with_model(truncated_text)

            processing_time = time.time() - start_time

            return SentimentAnalysisResult(
                document_id=document_id,
                sentiment=SentimentLabel(sentiment_result['label'].lower()),
                confidence=sentiment_result['confidence'],
                scores=sentiment_result['scores'],
                processing_time=processing_time
            )

        except Exception as e:
            raise SentimentAnalysisException("TransformersSentimentAnalyzer", str(e))

    async def analyze_tone(self, document_text: str, document_id: str) -> Dict[str, Any]:
        """Analyze tone using transformers model."""
        try:
            # Mock tone analysis
            return {
                'document_id': document_id,
                'tone': 'professional',  # Mock result
                'confidence': 0.85,
                'style_features': {
                    'formality': 0.8,
                    'objectivity': 0.7,
                    'technical_level': 0.6
                }
            }
        except Exception as e:
            raise SentimentAnalysisException("TransformersSentimentAnalyzer", str(e))

    def is_available(self) -> bool:
        """Check if transformers service is available."""
        try:
            import transformers
            return True
        except ImportError:
            return False

    async def _load_model(self) -> None:
        """Load the transformers model."""
        try:
            # In a real implementation, this would load the actual model
            # For now, we'll just set a flag
            self._model = "loaded"
        except Exception as e:
            raise SentimentAnalysisException("TransformersSentimentAnalyzer", f"Failed to load model: {e}")

    async def _analyze_with_model(self, text: str) -> Dict[str, Any]:
        """Analyze text with the loaded model."""
        # Mock implementation - in real code, this would use the actual model
        return {
            'label': 'POSITIVE',  # Mock positive sentiment
            'confidence': 0.89,
            'scores': {
                'POSITIVE': 0.89,
                'NEGATIVE': 0.08,
                'NEUTRAL': 0.03
            }
        }
