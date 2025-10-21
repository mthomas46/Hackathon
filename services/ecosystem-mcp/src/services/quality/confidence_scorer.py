"""
Confidence Scorer

Calculates confidence scores for generated documentation.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from .completeness_checker import CompletenessResult
from .accuracy_validator import AccuracyResult

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceScore:
    """Overall confidence score for documentation."""
    overall_confidence: float  # 0-1
    completeness_confidence: float
    accuracy_confidence: float
    source_quality_confidence: float
    requires_review: bool
    confidence_breakdown: Dict[str, float]
    review_priority: str  # low, medium, high, critical
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'overall_confidence': self.overall_confidence,
            'completeness_confidence': self.completeness_confidence,
            'accuracy_confidence': self.accuracy_confidence,
            'source_quality_confidence': self.source_quality_confidence,
            'requires_review': self.requires_review,
            'confidence_breakdown': self.confidence_breakdown,
            'review_priority': self.review_priority
        }


class ConfidenceScorer:
    """
    Calculates confidence scores for documentation.
    
    Factors:
    - Completeness score
    - Accuracy score
    - Source code quality
    - Analysis depth
    - Cross-validation results
    """
    
    def __init__(self):
        # Confidence thresholds
        self.high_confidence_threshold = 0.85
        self.medium_confidence_threshold = 0.70
        self.review_threshold = 0.60
        
        # Weight factors
        self.weights = {
            'completeness': 0.35,
            'accuracy': 0.40,
            'source_quality': 0.15,
            'analysis_depth': 0.10
        }
        
        logger.info("ConfidenceScorer initialized")
    
    async def score(
        self,
        artifact: Dict,
        completeness_result: CompletenessResult,
        accuracy_result: AccuracyResult,
        source_quality: Optional[float] = None,
        analysis_report: Optional[Dict] = None
    ) -> ConfidenceScore:
        """
        Calculate confidence score for documentation.
        
        Args:
            artifact: Documentation artifact
            completeness_result: Completeness check result
            accuracy_result: Accuracy validation result
            source_quality: Optional source code quality score (0-1)
            analysis_report: Optional Phase 3 analysis report
        
        Returns:
            Confidence score with breakdown
        """
        title = artifact.get('title', 'Unknown')
        logger.info(f"📊 Calculating confidence: {title}")
        
        # Component confidences
        completeness_conf = completeness_result.overall_score
        accuracy_conf = accuracy_result.overall_score
        
        # Calculate source quality confidence
        source_quality_conf = await self._calculate_source_quality(
            source_quality,
            analysis_report
        )
        
        # Calculate analysis depth confidence
        analysis_depth_conf = await self._calculate_analysis_depth(
            artifact,
            analysis_report
        )
        
        # Calculate overall confidence (weighted average)
        overall = (
            completeness_conf * self.weights['completeness'] +
            accuracy_conf * self.weights['accuracy'] +
            source_quality_conf * self.weights['source_quality'] +
            analysis_depth_conf * self.weights['analysis_depth']
        )
        
        # Determine if review is required
        requires_review = overall < self.review_threshold
        
        # Determine review priority
        priority = self._determine_priority(
            overall,
            completeness_result,
            accuracy_result
        )
        
        # Build confidence breakdown
        breakdown = {
            'completeness': completeness_conf,
            'accuracy': accuracy_conf,
            'source_quality': source_quality_conf,
            'analysis_depth': analysis_depth_conf,
            'weighted_overall': overall
        }
        
        score = ConfidenceScore(
            overall_confidence=overall,
            completeness_confidence=completeness_conf,
            accuracy_confidence=accuracy_conf,
            source_quality_confidence=source_quality_conf,
            requires_review=requires_review,
            confidence_breakdown=breakdown,
            review_priority=priority
        )
        
        logger.info(f"   ✅ Overall confidence: {overall:.2f}")
        logger.info(f"   📋 Review required: {requires_review} (priority: {priority})")
        
        return score
    
    async def _calculate_source_quality(
        self,
        provided_quality: Optional[float],
        analysis_report: Optional[Dict]
    ) -> float:
        """
        Calculate source code quality confidence.
        
        Uses provided quality or derives from analysis report.
        """
        if provided_quality is not None:
            return provided_quality
        
        if analysis_report:
            # Use modularity score as proxy for code quality
            modularity = analysis_report.get('modularity_score', 0.7)
            
            # Check for other quality indicators
            has_tests = analysis_report.get('has_tests', False)
            has_docs = analysis_report.get('has_documentation', False)
            
            # Calculate quality score
            quality = modularity
            if has_tests:
                quality += 0.1
            if has_docs:
                quality += 0.1
            
            return min(1.0, quality)
        
        # Default to moderate quality
        return 0.7
    
    async def _calculate_analysis_depth(
        self,
        artifact: Dict,
        analysis_report: Optional[Dict]
    ) -> float:
        """
        Calculate confidence based on analysis depth.
        
        Higher depth = more context = higher confidence.
        """
        score = 0.5  # Base score
        
        # Check artifact metadata
        if 'word_count' in artifact:
            word_count = artifact['word_count']
            if word_count > 500:
                score += 0.1
            if word_count > 1000:
                score += 0.1
        
        # Check if backed by analysis
        if analysis_report:
            score += 0.1
            
            # Check analysis completeness
            if analysis_report.get('dependency_graph'):
                score += 0.05
            if analysis_report.get('technology_stack'):
                score += 0.05
            if analysis_report.get('architecture'):
                score += 0.05
            if analysis_report.get('service_map'):
                score += 0.05
        
        return min(1.0, score)
    
    def _determine_priority(
        self,
        overall_confidence: float,
        completeness_result: CompletenessResult,
        accuracy_result: AccuracyResult
    ) -> str:
        """
        Determine review priority.
        
        Returns: 'low', 'medium', 'high', or 'critical'
        """
        # Critical priority
        if overall_confidence < 0.4:
            return 'critical'
        
        if accuracy_result.overall_score < 0.5:
            return 'critical'
        
        if len(accuracy_result.factual_errors) > 3:
            return 'critical'
        
        # High priority
        if overall_confidence < self.review_threshold:
            return 'high'
        
        if completeness_result.placeholder_count > 5:
            return 'high'
        
        if len(completeness_result.missing_sections) > 2:
            return 'high'
        
        # Medium priority
        if overall_confidence < self.medium_confidence_threshold:
            return 'medium'
        
        if len(accuracy_result.code_example_issues) > 0:
            return 'medium'
        
        # Low priority
        return 'low'
    
    def calculate_aggregate_confidence(
        self,
        scores: List[ConfidenceScore]
    ) -> Dict[str, float]:
        """
        Calculate aggregate confidence for a set of documents.
        
        Args:
            scores: List of confidence scores
        
        Returns:
            Aggregate statistics
        """
        if not scores:
            return {
                'average_confidence': 0.0,
                'min_confidence': 0.0,
                'max_confidence': 0.0,
                'review_rate': 0.0
            }
        
        confidences = [s.overall_confidence for s in scores]
        
        return {
            'average_confidence': sum(confidences) / len(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'review_rate': sum(1 for s in scores if s.requires_review) / len(scores),
            'critical_count': sum(1 for s in scores if s.review_priority == 'critical'),
            'high_priority_count': sum(1 for s in scores if s.review_priority == 'high'),
            'medium_priority_count': sum(1 for s in scores if s.review_priority == 'medium')
        }


# Singleton instance
_confidence_scorer: Optional[ConfidenceScorer] = None


def get_confidence_scorer() -> ConfidenceScorer:
    """Get or create singleton confidence scorer."""
    global _confidence_scorer
    if _confidence_scorer is None:
        _confidence_scorer = ConfidenceScorer()
    return _confidence_scorer

