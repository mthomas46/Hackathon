"""Sentiment Analyzer - Advanced sentiment detection and tone analysis."""

import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib

from services.shared.core.di.services import ILoggerService
from services.shared.core.logging.logger import get_logger
from services.shared.core.performance.cache_manager import get_cache_manager
from services.shared.core.performance.profiler import profile_async_operation


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""

    text: str
    sentiment: str  # "positive", "negative", "neutral"
    confidence: float
    polarity: float  # -1.0 to 1.0
    subjectivity: float  # 0.0 to 1.0
    analyzer: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "text": self.text,
            "sentiment": self.sentiment,
            "confidence": self.confidence,
            "polarity": self.polarity,
            "subjectivity": self.subjectivity,
            "analyzer": self.analyzer,
            "metadata": self.metadata
        }


class SentimentDetector:
    """Detects sentiment in text using rule-based analysis."""

    def __init__(self,
                 logger: Optional[ILoggerService] = None,
                 cache: Optional[Any] = None):
        """Initialize sentiment detector."""
        self._logger = logger or get_logger()
        self._cache = cache or get_cache_manager()

    async def detect_sentiment(self, text: str) -> SentimentResult:
        """Detect sentiment in text using rule-based analysis."""
        # Check cache first
        cache_key = f"sentiment:{hashlib.md5(text.encode()).hexdigest()}"
        cached_result = await self._cache.get(cache_key)

        if cached_result:
            await self._logger.debug("Using cached sentiment analysis", text_length=len(text))
            return SentimentResult(**cached_result)

        async with profile_async_operation("detect_sentiment"):
            result = self._analyze_rule_based(text)

            # Cache the result
            await self._cache.set(cache_key, result.to_dict(), ttl=1800)

            await self._logger.debug(
                f"Detected sentiment: {result.sentiment}",
                confidence=result.confidence
            )

            return result

    def _analyze_rule_based(self, text: str) -> SentimentResult:
        """Rule-based sentiment analysis."""
        text_lower = text.lower()

        # Define positive and negative word lists
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'best', 'awesome', 'brilliant', 'perfect',
            'happy', 'pleased', 'satisfied', 'delighted', 'thrilled'
        }

        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate',
            'dislike', 'poor', 'disappointing', 'frustrating', 'annoying',
            'sad', 'angry', 'upset', 'displeased', 'unhappy', 'dissatisfied'
        }

        # Count positive and negative words
        words = re.findall(r'\b\w+\b', text_lower)
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        # Calculate polarity and sentiment
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            polarity = 0.0
            sentiment = "neutral"
            confidence = 0.5
        else:
            polarity = (positive_count - negative_count) / total_sentiment_words
            if polarity > 0.1:
                sentiment = "positive"
                confidence = min(1.0, polarity)
            elif polarity < -0.1:
                sentiment = "negative"
                confidence = min(1.0, abs(polarity))
            else:
                sentiment = "neutral"
                confidence = 1.0 - abs(polarity)

        return SentimentResult(
            text=text,
            sentiment=sentiment,
            confidence=float(confidence),
            polarity=float(polarity),
            subjectivity=float(total_sentiment_words / len(words)) if words else 0.0,
            analyzer="rule_based",
            metadata={
                "positive_words": positive_count,
                "negative_words": negative_count,
                "total_words": len(words)
            }
        )

    async def detect_batch_sentiment(self, texts: List[str]) -> List[SentimentResult]:
        """Detect sentiment for multiple texts."""
        tasks = [self.detect_sentiment(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                await self._logger.error(f"Failed to analyze sentiment for text {i}", error=str(result))
                valid_results.append(SentimentResult(
                    text=texts[i],
                    sentiment="neutral",
                    confidence=0.0,
                    polarity=0.0,
                    subjectivity=0.0,
                    analyzer="error_fallback"
                ))
            else:
                valid_results.append(result)

        return valid_results


class SentimentAnalyzer:
    """Main sentiment analysis service."""

    def __init__(self,
                 sentiment_detector: Optional[SentimentDetector] = None,
                 logger: Optional[ILoggerService] = None):
        """Initialize sentiment analyzer."""
        self._sentiment_detector = sentiment_detector or SentimentDetector()
        self._logger = logger or get_logger()

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Perform sentiment analysis on text."""
        async with profile_async_operation("analyze_sentiment"):
            start_time = datetime.now(timezone.utc)

            try:
                sentiment_result = await self._sentiment_detector.detect_sentiment(text)
                execution_time = datetime.now(timezone.utc) - start_time

                result = {
                    "analysis_id": f"sentiment-{start_time.timestamp()}",
                    "status": "completed",
                    "text": text,
                    "sentiment": sentiment_result.sentiment,
                    "confidence": sentiment_result.confidence,
                    "polarity": sentiment_result.polarity,
                    "subjectivity": sentiment_result.subjectivity,
                    "analyzer": sentiment_result.analyzer,
                    "execution_time_seconds": execution_time.total_seconds(),
                    "created_at": start_time.isoformat()
                }

                await self._logger.info(
                    "Completed sentiment analysis",
                    sentiment=sentiment_result.sentiment,
                    confidence=sentiment_result.confidence
                )

                return result

            except Exception as e:
                execution_time = datetime.now(timezone.utc) - start_time
                error_msg = f"Sentiment analysis failed: {str(e)}"

                await self._logger.error(error_msg, error=str(e))

                return {
                    "error": error_msg,
                    "analysis_id": f"error-{start_time.timestamp()}",
                    "execution_time_seconds": execution_time.total_seconds(),
                    "status": "failed"
                }

    async def analyze_batch_sentiment(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze sentiment for multiple texts."""
        async with profile_async_operation("analyze_batch_sentiment"):
            start_time = datetime.now(timezone.utc)

            try:
                sentiment_results = await self._sentiment_detector.detect_batch_sentiment(texts)
                execution_time = datetime.now(timezone.utc) - start_time

                results = []
                for i, sentiment in enumerate(sentiment_results):
                    results.append({
                        "index": i,
                        "text": texts[i],
                        "sentiment": sentiment.sentiment,
                        "confidence": sentiment.confidence,
                        "polarity": sentiment.polarity,
                        "subjectivity": sentiment.subjectivity
                    })

                result = {
                    "analysis_id": f"batch-sentiment-{start_time.timestamp()}",
                    "status": "completed",
                    "total_texts": len(texts),
                    "results": results,
                    "execution_time_seconds": execution_time.total_seconds(),
                    "created_at": start_time.isoformat(),
                    "summary": {
                        "sentiment_distribution": self._calculate_sentiment_distribution(sentiment_results),
                        "average_confidence": sum(s.confidence for s in sentiment_results) / len(sentiment_results)
                    }
                }

                await self._logger.info(
                    "Completed batch sentiment analysis",
                    num_texts=len(texts),
                    execution_time_seconds=result["execution_time_seconds"]
                )

                return result

            except Exception as e:
                execution_time = datetime.now(timezone.utc) - start_time
                error_msg = f"Batch sentiment analysis failed: {str(e)}"

                await self._logger.error(error_msg, error=str(e))

                return {
                    "error": error_msg,
                    "analysis_id": f"error-{start_time.timestamp()}",
                    "execution_time_seconds": execution_time.total_seconds(),
                    "status": "failed"
                }

    def _calculate_sentiment_distribution(self, results: List[SentimentResult]) -> Dict[str, int]:
        """Calculate distribution of sentiment labels."""
        distribution = {"positive": 0, "negative": 0, "neutral": 0}
        for result in results:
            distribution[result.sentiment] += 1
        return distribution


# Global sentiment analyzer instance
_sentiment_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get global sentiment analyzer instance."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer


# Convenience functions
async def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Convenience function for sentiment analysis."""
    return await get_sentiment_analyzer().analyze_sentiment(text)


async def analyze_batch_sentiment(texts: List[str]) -> Dict[str, Any]:
    """Convenience function for batch sentiment analysis."""
    return await get_sentiment_analyzer().analyze_batch_sentiment(texts)