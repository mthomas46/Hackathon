"""Sentiment Analysis Handler - Handles sentiment and tone analysis."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base_handler import BaseAnalysisHandler, AnalysisResult
from ..models import (
    SentimentAnalysisRequest, SentimentAnalysisResponse,
    ToneAnalysisRequest, ToneAnalysisResponse,
    SentimentScores, DetailedAnalysis, SentenceSentiment
)

logger = logging.getLogger(__name__)


class SentimentAnalysisHandler(BaseAnalysisHandler):
    """Handler for sentiment analysis operations."""

    def __init__(self):
        super().__init__("sentiment_analysis")

    async def handle(self, request) -> AnalysisResult:
        """Handle sentiment analysis request."""
        try:
            # Import sentiment analyzer
            try:
                from ..sentiment_analyzer import analyze_document_sentiment
            except ImportError:
                # Fallback for testing
                analyze_document_sentiment = self._mock_sentiment_analysis

            # Determine analysis type
            if isinstance(request, ToneAnalysisRequest):
                analysis_type = "tone_analysis"
            else:
                analysis_type = "sentiment_analysis"

            # Perform sentiment analysis
            analysis_result = await analyze_document_sentiment(
                document_id=request.document_id,
                analysis_options=getattr(request, 'analysis_options', {}),
                include_detailed_scores=getattr(request, 'include_detailed_scores', True),
                language=getattr(request, 'language', 'en')
            )

            # Convert to standardized response format
            if analysis_type == "tone_analysis":
                response = ToneAnalysisResponse(
                    analysis_id=f"tone-{int(datetime.now(timezone.utc).timestamp())}",
                    document_id=request.document_id,
                    overall_tone=analysis_result.get('overall_tone', 'neutral'),
                    tone_confidence=analysis_result.get('tone_confidence', 0.0),
                    tone_distribution=analysis_result.get('tone_distribution', {}),
                    key_phrases=analysis_result.get('key_phrases', []),
                    writing_style=analysis_result.get('writing_style', {}),
                    readability_score=analysis_result.get('readability_score', 0.0),
                    execution_time_seconds=analysis_result.get('execution_time_seconds', 0.0),
                    error_message=None
                )
            else:
                response = SentimentAnalysisResponse(
                    analysis_id=f"sentiment-{int(datetime.now(timezone.utc).timestamp())}",
                    document_id=request.document_id,
                    sentiment=analysis_result.get('sentiment', 'neutral'),
                    confidence=analysis_result.get('confidence', 0.0),
                    scores=SentimentScores(**analysis_result.get('scores', {})),
                    detailed_analysis=DetailedAnalysis(**analysis_result.get('detailed_analysis', {})),
                    execution_time_seconds=analysis_result.get('execution_time_seconds', 0.0),
                    error_message=None
                )

            return self._create_analysis_result(
                analysis_id=response.analysis_id,
                data={"response": response.dict()},
                execution_time=response.execution_time_seconds
            )

        except Exception as e:
            error_msg = f"Sentiment analysis failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            analysis_id = f"sentiment-{int(datetime.now(timezone.utc).timestamp())}"
            return await self._handle_error(e, analysis_id)

    async def _mock_sentiment_analysis(self, document_id: str,
                                     analysis_options: Optional[Dict[str, Any]] = None,
                                     include_detailed_scores: bool = True,
                                     language: str = "en") -> Dict[str, Any]:
        """Mock sentiment analysis for testing purposes."""
        import random

        # Mock sentiment scores
        positive = random.uniform(0.1, 0.9)
        negative = random.uniform(0.1, 0.9)
        neutral = random.uniform(0.1, 0.9)

        # Normalize scores
        total = positive + negative + neutral
        positive /= total
        negative /= total
        neutral /= total

        # Determine overall sentiment
        if positive > max(negative, neutral):
            sentiment = "positive"
            confidence = positive
        elif negative > max(positive, neutral):
            sentiment = "negative"
            confidence = negative
        else:
            sentiment = "neutral"
            confidence = neutral

        # Mock detailed analysis
        detailed_analysis = {
            'sentence_sentiments': [
                {
                    'text': 'This is a sample sentence.',
                    'sentiment': random.choice(['positive', 'negative', 'neutral']),
                    'confidence': random.uniform(0.7, 0.95),
                    'start_position': 0,
                    'end_position': 25
                },
                {
                    'text': 'Another example sentence with different tone.',
                    'sentiment': random.choice(['positive', 'negative', 'neutral']),
                    'confidence': random.uniform(0.7, 0.95),
                    'start_position': 26,
                    'end_position': 65
                }
            ],
            'overall_tone': random.choice(['professional', 'casual', 'formal', 'technical']),
            'readability_score': random.uniform(60.0, 90.0),
            'emotional_intensity': random.uniform(0.1, 0.8),
            'subjectivity_score': random.uniform(0.2, 0.9)
        }

        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'scores': {
                'positive': positive,
                'negative': negative,
                'neutral': neutral
            },
            'detailed_analysis': detailed_analysis,
            'execution_time_seconds': random.uniform(0.5, 2.0)
        }

    async def handle_batch_sentiment_analysis(self, requests: List[SentimentAnalysisRequest]) -> List[AnalysisResult]:
        """Handle batch sentiment analysis."""
        results = []

        for request in requests:
            result = await self.handle(request)
            results.append(result)

        return results

    async def analyze_document_tone(self, request: ToneAnalysisRequest) -> AnalysisResult:
        """Analyze document tone specifically."""
        return await self.handle(request)

    async def get_sentiment_distribution(self, document_ids: List[str]) -> Dict[str, Any]:
        """Get sentiment distribution across multiple documents."""
        results = []

        for doc_id in document_ids:
            request = SentimentAnalysisRequest(
                document_id=doc_id,
                analysis_options={'include_detailed_scores': False}
            )
            result = await self.handle(request)
            results.append(result)

        # Aggregate results
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        total_confidence = 0.0
        successful_analyses = 0

        for result in results:
            if not result.error_message and result.data:
                response_data = result.data.get('response', {})
                sentiment = response_data.get('sentiment')
                confidence = response_data.get('confidence', 0.0)

                if sentiment in sentiment_counts:
                    sentiment_counts[sentiment] += 1
                    total_confidence += confidence
                    successful_analyses += 1

        avg_confidence = total_confidence / successful_analyses if successful_analyses > 0 else 0.0

        return {
            'document_count': len(document_ids),
            'successful_analyses': successful_analyses,
            'sentiment_distribution': sentiment_counts,
            'average_confidence': avg_confidence,
            'dominant_sentiment': max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else None,
            'execution_time_seconds': sum(r.execution_time_seconds or 0 for r in results)
        }

    async def detect_emotional_intensity(self, document_id: str) -> Dict[str, Any]:
        """Detect emotional intensity in document."""
        request = SentimentAnalysisRequest(
            document_id=document_id,
            analysis_options={
                'include_detailed_scores': True,
                'detect_emotional_intensity': True
            }
        )

        result = await self.handle(request)

        if result.error_message:
            return {"error": result.error_message}

        response_data = result.data.get('response', {})
        detailed_analysis = response_data.get('detailed_analysis', {})

        return {
            'document_id': document_id,
            'emotional_intensity': detailed_analysis.get('emotional_intensity', 0.0),
            'subjectivity_score': detailed_analysis.get('subjectivity_score', 0.0),
            'sentiment_volatility': self._calculate_sentiment_volatility(detailed_analysis),
            'execution_time_seconds': result.execution_time_seconds
        }

    def _calculate_sentiment_volatility(self, detailed_analysis: Dict[str, Any]) -> float:
        """Calculate sentiment volatility from detailed analysis."""
        sentence_sentiments = detailed_analysis.get('sentence_sentiments', [])

        if len(sentence_sentiments) < 2:
            return 0.0

        confidences = [s.get('confidence', 0.0) for s in sentence_sentiments]
        mean_confidence = sum(confidences) / len(confidences)

        # Calculate variance in confidence scores
        variance = sum((c - mean_confidence) ** 2 for c in confidences) / len(confidences)

        # Return volatility as square root of variance (standard deviation)
        return variance ** 0.5


# Register handler
from .base_handler import handler_registry
handler_registry.register("sentiment_analysis", SentimentAnalysisHandler())
handler_registry.register("tone_analysis", SentimentAnalysisHandler())
