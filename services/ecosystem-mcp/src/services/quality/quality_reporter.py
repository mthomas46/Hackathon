"""
Quality Reporter

Generates quality metrics and reports for documentation.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from .completeness_checker import CompletenessResult
from .accuracy_validator import AccuracyResult
from .confidence_scorer import ConfidenceScore

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """
    Comprehensive quality report for documentation set.
    """
    run_id: str
    generated_at: datetime
    
    # Summary metrics
    total_artifacts: int
    average_completeness: float
    average_accuracy: float
    average_confidence: float
    
    # Detailed breakdowns
    completeness_breakdown: Dict[str, float]
    accuracy_breakdown: Dict[str, float]
    confidence_breakdown: Dict[str, float]
    
    # Issue summary
    total_issues: int
    critical_issues: int
    issues_by_type: Dict[str, int]
    
    # Review requirements
    artifacts_requiring_review: int
    review_priority_breakdown: Dict[str, int]
    
    # Recommendations
    top_recommendations: List[str]
    
    # Trends (if historical data available)
    quality_trend: Optional[str] = None  # improving, declining, stable
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'run_id': self.run_id,
            'generated_at': self.generated_at.isoformat(),
            'total_artifacts': self.total_artifacts,
            'average_completeness': self.average_completeness,
            'average_accuracy': self.average_accuracy,
            'average_confidence': self.average_confidence,
            'completeness_breakdown': self.completeness_breakdown,
            'accuracy_breakdown': self.accuracy_breakdown,
            'confidence_breakdown': self.confidence_breakdown,
            'total_issues': self.total_issues,
            'critical_issues': self.critical_issues,
            'issues_by_type': self.issues_by_type,
            'artifacts_requiring_review': self.artifacts_requiring_review,
            'review_priority_breakdown': self.review_priority_breakdown,
            'top_recommendations': self.top_recommendations,
            'quality_trend': self.quality_trend
        }


class QualityReporter:
    """
    Generates quality reports and metrics.
    
    Aggregates results from:
    - Completeness checks
    - Accuracy validation
    - Confidence scoring
    """
    
    def __init__(self):
        logger.info("QualityReporter initialized")
    
    async def generate_report(
        self,
        run_id: str,
        completeness_results: List[CompletenessResult],
        accuracy_results: List[AccuracyResult],
        confidence_scores: List[ConfidenceScore],
        artifact_titles: Optional[List[str]] = None
    ) -> QualityReport:
        """
        Generate comprehensive quality report.
        
        Args:
            run_id: Documentation run ID
            completeness_results: List of completeness results
            accuracy_results: List of accuracy results
            confidence_scores: List of confidence scores
            artifact_titles: Optional list of artifact titles
        
        Returns:
            Quality report
        """
        logger.info(f"📊 Generating quality report for run {run_id}")
        
        total = len(completeness_results)
        
        # Calculate averages
        avg_completeness = (
            sum(r.overall_score for r in completeness_results) / total
            if total > 0 else 0.0
        )
        
        avg_accuracy = (
            sum(r.overall_score for r in accuracy_results) / total
            if total > 0 else 0.0
        )
        
        avg_confidence = (
            sum(s.overall_confidence for s in confidence_scores) / total
            if total > 0 else 0.0
        )
        
        # Generate breakdowns
        completeness_breakdown = self._analyze_completeness(completeness_results)
        accuracy_breakdown = self._analyze_accuracy(accuracy_results)
        confidence_breakdown = self._analyze_confidence(confidence_scores)
        
        # Count issues
        total_issues, critical_issues, issues_by_type = self._count_issues(
            completeness_results,
            accuracy_results
        )
        
        # Count review requirements
        requiring_review = sum(1 for s in confidence_scores if s.requires_review)
        
        priority_breakdown = {
            'critical': sum(1 for s in confidence_scores if s.review_priority == 'critical'),
            'high': sum(1 for s in confidence_scores if s.review_priority == 'high'),
            'medium': sum(1 for s in confidence_scores if s.review_priority == 'medium'),
            'low': sum(1 for s in confidence_scores if s.review_priority == 'low')
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            completeness_results,
            accuracy_results,
            confidence_scores
        )
        
        report = QualityReport(
            run_id=run_id,
            generated_at=datetime.now(),
            total_artifacts=total,
            average_completeness=avg_completeness,
            average_accuracy=avg_accuracy,
            average_confidence=avg_confidence,
            completeness_breakdown=completeness_breakdown,
            accuracy_breakdown=accuracy_breakdown,
            confidence_breakdown=confidence_breakdown,
            total_issues=total_issues,
            critical_issues=critical_issues,
            issues_by_type=issues_by_type,
            artifacts_requiring_review=requiring_review,
            review_priority_breakdown=priority_breakdown,
            top_recommendations=recommendations[:10]
        )
        
        logger.info(f"   ✅ Report generated: {total} artifacts analyzed")
        logger.info(f"   📊 Avg Completeness: {avg_completeness:.2f}")
        logger.info(f"   📊 Avg Accuracy: {avg_accuracy:.2f}")
        logger.info(f"   📊 Avg Confidence: {avg_confidence:.2f}")
        logger.info(f"   ⚠️  Requiring review: {requiring_review}/{total}")
        
        return report
    
    def _analyze_completeness(
        self,
        results: List[CompletenessResult]
    ) -> Dict[str, float]:
        """Analyze completeness results."""
        if not results:
            return {}
        
        total = len(results)
        
        return {
            'with_missing_sections': sum(
                1 for r in results if r.missing_sections
            ) / total,
            'with_placeholders': sum(
                1 for r in results if r.placeholder_count > 0
            ) / total,
            'with_broken_links': sum(
                1 for r in results if r.broken_links
            ) / total,
            'with_formatting_issues': sum(
                1 for r in results if r.formatting_issues
            ) / total,
            'with_code_examples': sum(
                1 for r in results if r.has_code_examples
            ) / total
        }
    
    def _analyze_accuracy(
        self,
        results: List[AccuracyResult]
    ) -> Dict[str, float]:
        """Analyze accuracy results."""
        if not results:
            return {}
        
        total = len(results)
        
        return {
            'with_code_issues': sum(
                1 for r in results if r.code_example_issues
            ) / total,
            'with_api_issues': sum(
                1 for r in results if r.api_mismatches
            ) / total,
            'with_type_errors': sum(
                1 for r in results if r.type_errors
            ) / total,
            'with_factual_errors': sum(
                1 for r in results if r.factual_errors
            ) / total,
            'validation_rate': sum(
                r.validated_examples / max(r.total_examples, 1)
                for r in results
            ) / total if total > 0 else 0.0
        }
    
    def _analyze_confidence(
        self,
        scores: List[ConfidenceScore]
    ) -> Dict[str, float]:
        """Analyze confidence scores."""
        if not scores:
            return {}
        
        total = len(scores)
        
        return {
            'high_confidence': sum(
                1 for s in scores if s.overall_confidence >= 0.85
            ) / total,
            'medium_confidence': sum(
                1 for s in scores 
                if 0.70 <= s.overall_confidence < 0.85
            ) / total,
            'low_confidence': sum(
                1 for s in scores if s.overall_confidence < 0.70
            ) / total,
            'requires_review_rate': sum(
                1 for s in scores if s.requires_review
            ) / total
        }
    
    def _count_issues(
        self,
        completeness_results: List[CompletenessResult],
        accuracy_results: List[AccuracyResult]
    ) -> tuple[int, int, Dict[str, int]]:
        """
        Count issues across all results.
        
        Returns:
            Tuple of (total_issues, critical_issues, issues_by_type)
        """
        issues_by_type = {
            'missing_sections': 0,
            'placeholders': 0,
            'broken_links': 0,
            'formatting': 0,
            'code_syntax': 0,
            'api_mismatches': 0,
            'type_errors': 0,
            'factual_errors': 0
        }
        
        # Count completeness issues
        for result in completeness_results:
            issues_by_type['missing_sections'] += len(result.missing_sections)
            issues_by_type['placeholders'] += result.placeholder_count
            issues_by_type['broken_links'] += len(result.broken_links)
            issues_by_type['formatting'] += len(result.formatting_issues)
        
        # Count accuracy issues
        for result in accuracy_results:
            issues_by_type['code_syntax'] += len(result.code_example_issues)
            issues_by_type['api_mismatches'] += len(result.api_mismatches)
            issues_by_type['type_errors'] += len(result.type_errors)
            issues_by_type['factual_errors'] += len(result.factual_errors)
        
        total_issues = sum(issues_by_type.values())
        
        # Critical issues are factual errors and code syntax errors
        critical_issues = (
            issues_by_type['factual_errors'] +
            issues_by_type['code_syntax']
        )
        
        return total_issues, critical_issues, issues_by_type
    
    def _generate_recommendations(
        self,
        completeness_results: List[CompletenessResult],
        accuracy_results: List[AccuracyResult],
        confidence_scores: List[ConfidenceScore]
    ) -> List[str]:
        """Generate prioritized recommendations."""
        recommendations = []
        
        # Aggregate issues
        all_completeness_recs = []
        for result in completeness_results:
            all_completeness_recs.extend(result.recommendations)
        
        # Count recommendation frequency
        rec_counts: Dict[str, int] = {}
        for rec in all_completeness_recs:
            rec_counts[rec] = rec_counts.get(rec, 0) + 1
        
        # Sort by frequency
        sorted_recs = sorted(
            rec_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Add top recommendations
        for rec, count in sorted_recs[:5]:
            recommendations.append(f"{rec} ({count} artifacts)")
        
        # Add accuracy-based recommendations
        total_code_issues = sum(
            len(r.code_example_issues) for r in accuracy_results
        )
        if total_code_issues > 0:
            recommendations.append(
                f"Fix {total_code_issues} code example syntax errors"
            )
        
        total_api_issues = sum(
            len(r.api_mismatches) for r in accuracy_results
        )
        if total_api_issues > 0:
            recommendations.append(
                f"Resolve {total_api_issues} API documentation mismatches"
            )
        
        # Add confidence-based recommendations
        low_conf_count = sum(
            1 for s in confidence_scores if s.overall_confidence < 0.6
        )
        if low_conf_count > 0:
            recommendations.append(
                f"Review {low_conf_count} low-confidence documents"
            )
        
        return recommendations
    
    async def generate_summary_text(self, report: QualityReport) -> str:
        """
        Generate human-readable summary text.
        
        Args:
            report: Quality report
        
        Returns:
            Formatted summary text
        """
        summary = f"""
# Quality Report Summary

**Run ID:** {report.run_id}
**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
**Total Artifacts:** {report.total_artifacts}

## Overall Scores

- **Completeness:** {report.average_completeness:.1%}
- **Accuracy:** {report.average_accuracy:.1%}
- **Confidence:** {report.average_confidence:.1%}

## Issues Summary

- **Total Issues:** {report.total_issues}
- **Critical Issues:** {report.critical_issues}
- **Artifacts Requiring Review:** {report.artifacts_requiring_review}

## Issues by Type

"""
        for issue_type, count in sorted(
            report.issues_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if count > 0:
                summary += f"- {issue_type.replace('_', ' ').title()}: {count}\n"
        
        summary += f"\n## Review Priority\n\n"
        for priority, count in report.review_priority_breakdown.items():
            if count > 0:
                summary += f"- {priority.title()}: {count}\n"
        
        summary += f"\n## Top Recommendations\n\n"
        for i, rec in enumerate(report.top_recommendations, 1):
            summary += f"{i}. {rec}\n"
        
        return summary


# Singleton instance
_quality_reporter: Optional[QualityReporter] = None


def get_quality_reporter() -> QualityReporter:
    """Get or create singleton quality reporter."""
    global _quality_reporter
    if _quality_reporter is None:
        _quality_reporter = QualityReporter()
    return _quality_reporter

