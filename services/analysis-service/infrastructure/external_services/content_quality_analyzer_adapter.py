"""Content quality analyzer adapter."""

from typing import Dict, Any, List
import time
from abc import ABC, abstractmethod

from ...domain.exceptions import ExternalServiceException


class ContentQualityAnalysisResult:
    """Result of content quality analysis."""

    def __init__(self,
                 document_id: str,
                 readability_score: float,
                 complexity_score: float,
                 completeness_score: float,
                 overall_quality_score: float,
                 issues: List[str],
                 suggestions: List[str],
                 metrics: Dict[str, Any],
                 processing_time: float = 0.0):
        """Initialize content quality analysis result."""
        self.document_id = document_id
        self.readability_score = readability_score
        self.complexity_score = complexity_score
        self.completeness_score = completeness_score
        self.overall_quality_score = overall_quality_score
        self.issues = issues
        self.suggestions = suggestions
        self.metrics = metrics
        self.processing_time = processing_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'document_id': self.document_id,
            'readability_score': self.readability_score,
            'complexity_score': self.complexity_score,
            'completeness_score': self.completeness_score,
            'overall_quality_score': self.overall_quality_score,
            'issues': self.issues,
            'suggestions': self.suggestions,
            'metrics': self.metrics,
            'processing_time': self.processing_time
        }


class ContentQualityAnalyzerAdapter(ABC):
    """Abstract adapter for content quality analysis."""

    @abstractmethod
    async def analyze_quality(self, document_text: str, document_id: str) -> ContentQualityAnalysisResult:
        """Analyze content quality."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is available."""
        pass


class LocalContentQualityAnalyzerAdapter(ContentQualityAnalyzerAdapter):
    """Local implementation of content quality analysis."""

    def __init__(self):
        """Initialize local content quality analyzer."""
        pass

    async def analyze_quality(self, document_text: str, document_id: str) -> ContentQualityAnalysisResult:
        """Analyze content quality using local algorithms."""
        start_time = time.time()

        # Analyze readability
        readability_score = self._calculate_readability(document_text)

        # Analyze complexity
        complexity_score = self._calculate_complexity(document_text)

        # Analyze completeness
        completeness_score = self._calculate_completeness(document_text)

        # Calculate overall quality
        overall_quality_score = (readability_score + (1 - complexity_score) + completeness_score) / 3

        # Identify issues
        issues = []
        suggestions = []

        if readability_score < 0.6:
            issues.append("Low readability score")
            suggestions.append("Use shorter sentences and simpler words")

        if complexity_score > 0.7:
            issues.append("High complexity")
            suggestions.append("Break down complex concepts")

        if completeness_score < 0.5:
            issues.append("Incomplete content")
            suggestions.append("Add missing sections or examples")

        # Additional metrics
        metrics = {
            'word_count': len(document_text.split()),
            'sentence_count': len(document_text.split('.')),
            'paragraph_count': len(document_text.split('\n\n')),
            'avg_words_per_sentence': len(document_text.split()) / max(1, len(document_text.split('.')))
        }

        processing_time = time.time() - start_time

        return ContentQualityAnalysisResult(
            document_id=document_id,
            readability_score=readability_score,
            complexity_score=complexity_score,
            completeness_score=completeness_score,
            overall_quality_score=overall_quality_score,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics,
            processing_time=processing_time
        )

    def is_available(self) -> bool:
        """Check if local analyzer is available."""
        return True

    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score."""
        sentences = text.split('.')
        words = text.split()
        avg_words_per_sentence = len(words) / len(sentences) if sentences else 0

        # Simple readability formula (Flesch Reading Ease approximation)
        if avg_words_per_sentence < 10:
            return 0.9  # Very easy
        elif avg_words_per_sentence < 15:
            return 0.7  # Easy
        elif avg_words_per_sentence < 20:
            return 0.5  # Standard
        else:
            return 0.3  # Difficult

    def _calculate_complexity(self, text: str) -> float:
        """Calculate complexity score."""
        words = text.split()

        # Count complex words (long words, technical terms)
        complex_words = [w for w in words if len(w) > 6]
        complexity_ratio = len(complex_words) / len(words) if words else 0

        # Count technical indicators
        technical_indicators = ['api', 'function', 'class', 'method', 'algorithm', 'implementation']
        technical_count = sum(1 for word in words if word.lower() in technical_indicators)

        technical_ratio = technical_count / len(words) if words else 0

        return min(1.0, (complexity_ratio + technical_ratio) / 2)

    def _calculate_completeness(self, text: str) -> float:
        """Calculate completeness score."""
        text_lower = text.lower()

        # Check for common documentation elements
        completeness_indicators = [
            'introduction', 'overview', 'purpose', 'usage', 'example',
            'installation', 'configuration', 'api', 'reference', 'faq'
        ]

        found_indicators = sum(1 for indicator in completeness_indicators if indicator in text_lower)
        completeness_ratio = found_indicators / len(completeness_indicators)

        # Check for structured content (headings, lists)
        has_structure = '#' in text or '*' in text or '-' in text or '1.' in text

        structure_bonus = 0.2 if has_structure else 0.0

        return min(1.0, completeness_ratio + structure_bonus)
