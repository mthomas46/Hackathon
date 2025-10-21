"""
Unit tests for ConfidenceScorer.
"""

import pytest
from src.services.quality.confidence_scorer import (
    ConfidenceScorer,
    get_confidence_scorer
)
from src.services.quality.completeness_checker import CompletenessResult
from src.services.quality.accuracy_validator import AccuracyResult


@pytest.mark.asyncio
class TestConfidenceScorer:
    """Test ConfidenceScorer functionality."""
    
    async def test_initialization(self):
        """Test scorer initialization."""
        scorer = ConfidenceScorer()
        assert scorer is not None
        assert scorer.high_confidence_threshold == 0.85
        assert scorer.medium_confidence_threshold == 0.70
        assert scorer.review_threshold == 0.60
    
    async def test_singleton(self):
        """Test singleton pattern."""
        scorer1 = get_confidence_scorer()
        scorer2 = get_confidence_scorer()
        assert scorer1 is scorer2
    
    async def test_high_confidence_score(self):
        """Test high confidence scoring."""
        scorer = ConfidenceScorer()
        
        # Perfect completeness
        completeness = CompletenessResult(
            overall_score=1.0,
            missing_sections=[],
            incomplete_sections=[],
            placeholder_count=0,
            broken_links=[],
            formatting_issues=[],
            recommendations=[],
            section_word_counts={'section': 100},
            has_code_examples=True
        )
        
        # Perfect accuracy
        accuracy = AccuracyResult(
            overall_score=1.0,
            code_example_issues=[],
            api_mismatches=[],
            type_errors=[],
            factual_errors=[],
            warnings=[],
            validated_examples=5,
            total_examples=5
        )
        
        artifact = {'title': 'Test', 'word_count': 1000}
        
        result = await scorer.score(
            artifact,
            completeness,
            accuracy,
            source_quality=0.9
        )
        
        assert result.overall_confidence >= 0.90
        assert result.requires_review is False
        assert result.review_priority == 'low'
    
    async def test_low_confidence_score(self):
        """Test low confidence scoring."""
        scorer = ConfidenceScorer()
        
        # Poor completeness
        completeness = CompletenessResult(
            overall_score=0.4,
            missing_sections=['overview', 'usage', 'examples'],
            incomplete_sections=['intro'],
            placeholder_count=5,
            broken_links=['link1', 'link2'],
            formatting_issues=['issue1'],
            recommendations=['fix1', 'fix2'],
            section_word_counts={'intro': 10},
            has_code_examples=False
        )
        
        # Poor accuracy
        accuracy = AccuracyResult(
            overall_score=0.5,
            code_example_issues=['syntax error 1', 'syntax error 2'],
            api_mismatches=['endpoint1'],
            type_errors=['type1'],
            factual_errors=['error1', 'error2'],
            warnings=['warn1'],
            validated_examples=1,
            total_examples=5
        )
        
        artifact = {'title': 'Test', 'word_count': 100}
        
        result = await scorer.score(
            artifact,
            completeness,
            accuracy,
            source_quality=0.5
        )
        
        assert result.overall_confidence < 0.60
        assert result.requires_review is True
        assert result.review_priority in ['critical', 'high']
    
    async def test_weighted_scoring(self):
        """Test weighted scoring algorithm."""
        scorer = ConfidenceScorer()
        
        # Test that weights are applied correctly
        completeness = CompletenessResult(
            overall_score=0.8,
            missing_sections=[],
            incomplete_sections=[],
            placeholder_count=0,
            broken_links=[],
            formatting_issues=[],
            recommendations=[],
            section_word_counts={},
            has_code_examples=True
        )
        
        accuracy = AccuracyResult(
            overall_score=0.6,  # Lower accuracy
            code_example_issues=[],
            api_mismatches=[],
            type_errors=[],
            factual_errors=[],
            warnings=[],
            validated_examples=3,
            total_examples=3
        )
        
        artifact = {'title': 'Test'}
        
        result = await scorer.score(artifact, completeness, accuracy)
        
        # Overall should be weighted average
        expected = (0.8 * 0.35) + (0.6 * 0.40) + (0.7 * 0.15) + (0.5 * 0.10)
        assert abs(result.overall_confidence - expected) < 0.05
    
    async def test_critical_priority(self):
        """Test critical priority determination."""
        scorer = ConfidenceScorer()
        
        completeness = CompletenessResult(
            overall_score=0.3,  # Very low
            missing_sections=[],
            incomplete_sections=[],
            placeholder_count=0,
            broken_links=[],
            formatting_issues=[],
            recommendations=[],
            section_word_counts={},
            has_code_examples=False
        )
        
        accuracy = AccuracyResult(
            overall_score=0.4,
            code_example_issues=[],
            api_mismatches=[],
            type_errors=[],
            factual_errors=['error1', 'error2', 'error3', 'error4'],
            warnings=[],
            validated_examples=0,
            total_examples=2
        )
        
        artifact = {'title': 'Test'}
        
        result = await scorer.score(artifact, completeness, accuracy)
        
        assert result.review_priority == 'critical'
    
    async def test_high_priority(self):
        """Test high priority determination."""
        scorer = ConfidenceScorer()
        
        completeness = CompletenessResult(
            overall_score=0.55,  # Just below review threshold
            missing_sections=['section1', 'section2', 'section3'],
            incomplete_sections=[],
            placeholder_count=6,
            broken_links=[],
            formatting_issues=[],
            recommendations=[],
            section_word_counts={},
            has_code_examples=False
        )
        
        accuracy = AccuracyResult(
            overall_score=0.7,
            code_example_issues=[],
            api_mismatches=[],
            type_errors=[],
            factual_errors=[],
            warnings=[],
            validated_examples=2,
            total_examples=2
        )
        
        artifact = {'title': 'Test'}
        
        result = await scorer.score(artifact, completeness, accuracy)
        
        assert result.review_priority == 'high'
    
    async def test_medium_priority(self):
        """Test medium priority determination."""
        scorer = ConfidenceScorer()
        
        completeness = CompletenessResult(
            overall_score=0.75,  # Medium
            missing_sections=[],
            incomplete_sections=[],
            placeholder_count=0,
            broken_links=[],
            formatting_issues=[],
            recommendations=[],
            section_word_counts={},
            has_code_examples=True
        )
        
        accuracy = AccuracyResult(
            overall_score=0.65,
            code_example_issues=['issue1'],
            api_mismatches=[],
            type_errors=[],
            factual_errors=[],
            warnings=[],
            validated_examples=2,
            total_examples=3
        )
        
        artifact = {'title': 'Test'}
        
        result = await scorer.score(artifact, completeness, accuracy)
        
        assert result.review_priority == 'medium'
    
    async def test_source_quality_integration(self):
        """Test source quality factor."""
        scorer = ConfidenceScorer()
        
        completeness = CompletenessResult(
            overall_score=0.8,
            missing_sections=[],
            incomplete_sections=[],
            placeholder_count=0,
            broken_links=[],
            formatting_issues=[],
            recommendations=[],
            section_word_counts={},
            has_code_examples=True
        )
        
        accuracy = AccuracyResult(
            overall_score=0.8,
            code_example_issues=[],
            api_mismatches=[],
            type_errors=[],
            factual_errors=[],
            warnings=[],
            validated_examples=2,
            total_examples=2
        )
        
        artifact = {'title': 'Test'}
        
        # High source quality
        result_high = await scorer.score(
            artifact, completeness, accuracy, source_quality=0.9
        )
        
        # Low source quality
        result_low = await scorer.score(
            artifact, completeness, accuracy, source_quality=0.5
        )
        
        assert result_high.overall_confidence > result_low.overall_confidence
        assert result_high.source_quality_confidence == 0.9
        assert result_low.source_quality_confidence == 0.5
    
    async def test_analysis_depth_impact(self):
        """Test analysis depth calculation."""
        scorer = ConfidenceScorer()
        
        completeness = CompletenessResult(
            overall_score=0.8,
            missing_sections=[],
            incomplete_sections=[],
            placeholder_count=0,
            broken_links=[],
            formatting_issues=[],
            recommendations=[],
            section_word_counts={},
            has_code_examples=True
        )
        
        accuracy = AccuracyResult(
            overall_score=0.8,
            code_example_issues=[],
            api_mismatches=[],
            type_errors=[],
            factual_errors=[],
            warnings=[],
            validated_examples=2,
            total_examples=2
        )
        
        # With analysis report
        analysis_report = {
            'dependency_graph': True,
            'technology_stack': True,
            'architecture': True,
            'service_map': True
        }
        
        artifact_with_analysis = {'title': 'Test', 'word_count': 1500}
        result_with = await scorer.score(
            artifact_with_analysis,
            completeness,
            accuracy,
            analysis_report=analysis_report
        )
        
        # Without analysis report
        artifact_without_analysis = {'title': 'Test', 'word_count': 300}
        result_without = await scorer.score(
            artifact_without_analysis,
            completeness,
            accuracy
        )
        
        # With analysis should have higher confidence
        assert result_with.overall_confidence >= result_without.overall_confidence
    
    async def test_aggregate_confidence(self):
        """Test aggregate confidence calculation."""
        scorer = ConfidenceScorer()
        
        from src.services.quality.confidence_scorer import ConfidenceScore
        
        scores = [
            ConfidenceScore(
                overall_confidence=0.9,
                completeness_confidence=0.9,
                accuracy_confidence=0.9,
                source_quality_confidence=0.9,
                requires_review=False,
                confidence_breakdown={},
                review_priority='low'
            ),
            ConfidenceScore(
                overall_confidence=0.5,
                completeness_confidence=0.5,
                accuracy_confidence=0.5,
                source_quality_confidence=0.5,
                requires_review=True,
                confidence_breakdown={},
                review_priority='high'
            ),
            ConfidenceScore(
                overall_confidence=0.7,
                completeness_confidence=0.7,
                accuracy_confidence=0.7,
                source_quality_confidence=0.7,
                requires_review=False,
                confidence_breakdown={},
                review_priority='medium'
            )
        ]
        
        aggregate = scorer.calculate_aggregate_confidence(scores)
        
        assert aggregate['average_confidence'] == pytest.approx(0.7, abs=0.01)
        assert aggregate['min_confidence'] == 0.5
        assert aggregate['max_confidence'] == 0.9
        assert aggregate['review_rate'] == pytest.approx(1/3, abs=0.01)
        assert aggregate['high_priority_count'] == 1
    
    async def test_to_dict(self):
        """Test result serialization."""
        scorer = ConfidenceScorer()
        
        completeness = CompletenessResult(
            overall_score=0.8,
            missing_sections=[],
            incomplete_sections=[],
            placeholder_count=0,
            broken_links=[],
            formatting_issues=[],
            recommendations=[],
            section_word_counts={},
            has_code_examples=True
        )
        
        accuracy = AccuracyResult(
            overall_score=0.8,
            code_example_issues=[],
            api_mismatches=[],
            type_errors=[],
            factual_errors=[],
            warnings=[],
            validated_examples=2,
            total_examples=2
        )
        
        artifact = {'title': 'Test'}
        
        result = await scorer.score(artifact, completeness, accuracy)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'overall_confidence' in result_dict
        assert 'requires_review' in result_dict
        assert 'review_priority' in result_dict
        assert 'confidence_breakdown' in result_dict

