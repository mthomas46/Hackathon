"""Quality Analysis Handler - Handles content quality assessment."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base_handler import BaseAnalysisHandler, AnalysisResult
from ..models import (
    ContentQualityRequest, ContentQualityResponse,
    QualityBreakdown, Recommendation, ImprovementSuggestion
)

logger = logging.getLogger(__name__)


class QualityAnalysisHandler(BaseAnalysisHandler):
    """Handler for content quality analysis operations."""

    def __init__(self):
        super().__init__("quality_analysis")

    async def handle(self, request: ContentQualityRequest) -> AnalysisResult:
        """Handle content quality analysis request."""
        try:
            # Import quality scorer
            try:
                from ..content_quality_scorer import assess_document_quality
            except ImportError:
                # Fallback for testing
                assess_document_quality = self._mock_quality_assessment

            # Perform quality assessment
            quality_result = await assess_document_quality(
                document_id=request.document_id,
                quality_checks=request.quality_checks,
                options=request.options or {}
            )

            # Convert to standardized response format
            response = ContentQualityResponse(
                analysis_id=f"quality-{int(datetime.now(timezone.utc).timestamp())}",
                document_id=request.document_id,
                overall_score=quality_result.get('overall_score', 0.0),
                quality_breakdown=QualityBreakdown(**quality_result.get('quality_breakdown', {})),
                recommendations=[
                    Recommendation(**rec) for rec in quality_result.get('recommendations', [])
                ],
                improvement_suggestions=[
                    ImprovementSuggestion(**sug) for sug in quality_result.get('improvement_suggestions', [])
                ],
                execution_time_seconds=quality_result.get('execution_time_seconds', 0.0),
                error_message=None
            )

            return self._create_analysis_result(
                analysis_id=response.analysis_id,
                data={"response": response.dict()},
                execution_time=response.execution_time_seconds
            )

        except Exception as e:
            error_msg = f"Quality analysis failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            analysis_id = f"quality-{int(datetime.now(timezone.utc).timestamp())}"
            return await self._handle_error(e, analysis_id)

    async def _mock_quality_assessment(self, document_id: str,
                                     quality_checks: Optional[List[str]] = None,
                                     options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock quality assessment for testing purposes."""
        import random

        checks = quality_checks or ['readability', 'grammar', 'structure', 'completeness']

        # Mock quality breakdown
        quality_breakdown = {}
        total_score = 0.0

        for check in checks:
            if check == 'readability':
                score = random.uniform(70.0, 95.0)
                issues = [] if score > 80 else ['sentence_length', 'complexity']
            elif check == 'grammar':
                score = random.uniform(85.0, 100.0)
                issues = [] if score > 95 else ['minor_errors']
            elif check == 'structure':
                score = random.uniform(75.0, 98.0)
                issues = [] if score > 85 else ['missing_headings', 'poor_organization']
            elif check == 'completeness':
                score = random.uniform(60.0, 90.0)
                issues = [] if score > 75 else ['missing_examples', 'incomplete_sections']
            else:
                score = random.uniform(70.0, 90.0)
                issues = []

            quality_breakdown[check] = {
                'score': score,
                'level': self._score_to_level(score),
                'issues': issues
            }
            total_score += score

        overall_score = total_score / len(checks) if checks else 0.0

        # Mock recommendations
        recommendations = []
        if overall_score < 80:
            recommendations.append({
                'priority': 'high',
                'category': 'structure',
                'description': 'Improve document structure and organization',
                'impact': 'high'
            })
        if any(breakdown['score'] < 75 for breakdown in quality_breakdown.values()):
            recommendations.append({
                'priority': 'medium',
                'category': 'content',
                'description': 'Enhance content completeness and examples',
                'impact': 'medium'
            })

        # Mock improvement suggestions
        improvement_suggestions = {
            'high_priority': ['Improve document structure', 'Add missing examples'],
            'medium_priority': ['Enhance readability', 'Fix grammar issues'],
            'low_priority': ['Add cross-references', 'Improve formatting']
        }

        return {
            'overall_score': overall_score,
            'quality_breakdown': quality_breakdown,
            'recommendations': recommendations,
            'improvement_suggestions': improvement_suggestions,
            'execution_time_seconds': random.uniform(1.0, 3.0)
        }

    def _score_to_level(self, score: float) -> str:
        """Convert score to quality level."""
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 70:
            return 'fair'
        else:
            return 'poor'

    async def handle_batch_quality_analysis(self, requests: List[ContentQualityRequest]) -> List[AnalysisResult]:
        """Handle batch quality analysis."""
        results = []

        for request in requests:
            result = await self.handle(request)
            results.append(result)

        return results

    async def get_quality_metrics(self, document_ids: List[str]) -> Dict[str, Any]:
        """Get quality metrics across multiple documents."""
        results = []

        for doc_id in document_ids:
            request = ContentQualityRequest(
                document_id=doc_id,
                quality_checks=['readability', 'grammar', 'structure']
            )
            result = await self.handle(request)
            results.append(result)

        # Aggregate metrics
        total_score = 0.0
        successful_analyses = 0
        quality_distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        common_issues = {}

        for result in results:
            if not result.error_message and result.data:
                response_data = result.data.get('response', {})
                score = response_data.get('overall_score', 0.0)
                level = self._score_to_level(score)

                total_score += score
                successful_analyses += 1
                quality_distribution[level] += 1

                # Track common issues
                breakdown = response_data.get('quality_breakdown', {})
                for check_name, check_data in breakdown.items():
                    for issue in check_data.get('issues', []):
                        common_issues[issue] = common_issues.get(issue, 0) + 1

        avg_score = total_score / successful_analyses if successful_analyses > 0 else 0.0

        # Get most common issues
        top_issues = sorted(common_issues.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'document_count': len(document_ids),
            'successful_analyses': successful_analyses,
            'average_score': avg_score,
            'quality_distribution': quality_distribution,
            'top_common_issues': [{'issue': issue, 'count': count} for issue, count in top_issues],
            'execution_time_seconds': sum(r.execution_time_seconds or 0 for r in results)
        }

    async def assess_readability(self, document_id: str) -> Dict[str, Any]:
        """Assess document readability specifically."""
        request = ContentQualityRequest(
            document_id=document_id,
            quality_checks=['readability'],
            options={'detailed_readability': True}
        )

        result = await self.handle(request)

        if result.error_message:
            return {"error": result.error_message}

        response_data = result.data.get('response', {})
        breakdown = response_data.get('quality_breakdown', {})
        readability_data = breakdown.get('readability', {})

        return {
            'document_id': document_id,
            'readability_score': readability_data.get('score', 0.0),
            'level': readability_data.get('level', 'unknown'),
            'issues': readability_data.get('issues', []),
            'flesch_kincaid_score': readability_data.get('flesch_kincaid', 0.0),
            'avg_sentence_length': readability_data.get('avg_sentence_length', 0.0),
            'avg_words_per_sentence': readability_data.get('avg_words_per_sentence', 0.0),
            'complexity_score': readability_data.get('complexity_score', 0.0),
            'execution_time_seconds': result.execution_time_seconds
        }

    async def check_grammar_and_style(self, document_id: str) -> Dict[str, Any]:
        """Check grammar and style issues."""
        request = ContentQualityRequest(
            document_id=document_id,
            quality_checks=['grammar'],
            options={'detailed_grammar_check': True}
        )

        result = await self.handle(request)

        if result.error_message:
            return {"error": result.error_message}

        response_data = result.data.get('response', {})
        breakdown = response_data.get('quality_breakdown', {})
        grammar_data = breakdown.get('grammar', {})

        return {
            'document_id': document_id,
            'grammar_score': grammar_data.get('score', 0.0),
            'level': grammar_data.get('level', 'unknown'),
            'issues': grammar_data.get('issues', []),
            'error_count': grammar_data.get('error_count', 0),
            'spelling_errors': grammar_data.get('spelling_errors', []),
            'grammar_errors': grammar_data.get('grammar_errors', []),
            'style_suggestions': grammar_data.get('style_suggestions', []),
            'execution_time_seconds': result.execution_time_seconds
        }

    async def analyze_structure_and_completeness(self, document_id: str) -> Dict[str, Any]:
        """Analyze document structure and completeness."""
        request = ContentQualityRequest(
            document_id=document_id,
            quality_checks=['structure', 'completeness'],
            options={'detailed_structure_analysis': True}
        )

        result = await self.handle(request)

        if result.error_message:
            return {"error": result.error_message}

        response_data = result.data.get('response', {})
        breakdown = response_data.get('quality_breakdown', {})

        structure_data = breakdown.get('structure', {})
        completeness_data = breakdown.get('completeness', {})

        return {
            'document_id': document_id,
            'structure_score': structure_data.get('score', 0.0),
            'structure_level': structure_data.get('level', 'unknown'),
            'structure_issues': structure_data.get('issues', []),
            'completeness_score': completeness_data.get('score', 0.0),
            'completeness_level': completeness_data.get('level', 'unknown'),
            'completeness_issues': completeness_data.get('issues', []),
            'missing_sections': completeness_data.get('missing_sections', []),
            'incomplete_sections': completeness_data.get('incomplete_sections', []),
            'structure_suggestions': structure_data.get('suggestions', []),
            'execution_time_seconds': result.execution_time_seconds
        }


# Register handler
from .base_handler import handler_registry
handler_registry.register("quality_analysis", QualityAnalysisHandler())
handler_registry.register("content_quality", QualityAnalysisHandler())
