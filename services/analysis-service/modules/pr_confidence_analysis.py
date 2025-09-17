"""
PR Confidence Analysis Module for Analysis Service

This module provides comprehensive PR confidence analysis capabilities
moved from the orchestrator to the dedicated analysis service.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .models import AnalysisRequest, AnalysisResponse, FindingsResponse
from .shared_utils import get_analysis_service_client
from ..modules.analysis.pr_cross_reference_analyzer import pr_cross_reference_analyzer
from ..modules.analysis.pr_confidence_scorer import pr_confidence_scorer
from ..modules.analysis.pr_gap_detector import pr_gap_detector


@dataclass
class PRConfidenceAnalysisRequest:
    """Request model for PR confidence analysis."""
    pr_data: Dict[str, Any]
    jira_data: Optional[Dict[str, Any]] = None
    confluence_docs: Optional[List[Dict[str, Any]]] = None
    analysis_scope: str = "comprehensive"
    include_recommendations: bool = True
    confidence_threshold: float = 0.7


@dataclass
class PRConfidenceAnalysisResponse:
    """Response model for PR confidence analysis."""
    workflow_id: str
    analysis_timestamp: str
    confidence_score: float
    confidence_level: str
    approval_recommendation: str
    cross_reference_results: Dict[str, Any]
    detected_gaps: List[Dict[str, Any]]
    component_scores: Dict[str, float]
    recommendations: List[str]
    critical_concerns: List[str]
    strengths: List[str]
    improvement_areas: List[str]
    risk_assessment: str
    analysis_duration: float


class PRConfidenceAnalysisService:
    """Service for PR confidence analysis operations."""

    def __init__(self):
        self.service_client = get_analysis_service_client()

    async def analyze_pr_confidence(
        self,
        request: PRConfidenceAnalysisRequest
    ) -> PRConfidenceAnalysisResponse:
        """
        Perform comprehensive PR confidence analysis.

        Args:
            request: PR confidence analysis request

        Returns:
            Comprehensive analysis results
        """
        start_time = datetime.now()
        workflow_id = f"pr-analysis-{int(start_time.timestamp())}"

        try:
            # Step 1: Cross-reference analysis
            cross_ref_results = await self._perform_cross_reference_analysis(
                request.pr_data,
                request.jira_data,
                request.confluence_docs
            )

            # Step 2: Confidence scoring
            confidence_score = await self._calculate_confidence_score(
                request.pr_data,
                request.jira_data,
                request.confluence_docs,
                cross_ref_results
            )

            # Step 3: Gap detection
            detected_gaps = await self._detect_gaps(
                request.pr_data,
                request.jira_data,
                request.confluence_docs,
                cross_ref_results
            )

            analysis_duration = (datetime.now() - start_time).total_seconds()

            return PRConfidenceAnalysisResponse(
                workflow_id=workflow_id,
                analysis_timestamp=start_time.isoformat(),
                confidence_score=confidence_score.overall_score,
                confidence_level=confidence_score.confidence_level.value,
                approval_recommendation=confidence_score.approval_recommendation.value,
                cross_reference_results={
                    'overall_alignment_score': cross_ref_results.overall_alignment_score,
                    'requirement_alignment': cross_ref_results.requirement_alignment,
                    'documentation_consistency': cross_ref_results.documentation_consistency,
                    'identified_gaps': cross_ref_results.identified_gaps,
                    'consistency_issues': cross_ref_results.consistency_issues,
                    'risk_assessment': cross_ref_results.risk_assessment
                },
                detected_gaps=[
                    {
                        'gap_type': gap.gap_type.value,
                        'severity': gap.severity.value,
                        'description': gap.description,
                        'evidence': gap.evidence,
                        'recommendation': gap.recommendation,
                        'estimated_effort': gap.estimated_effort,
                        'blocking_approval': gap.blocking_approval
                    }
                    for gap in detected_gaps
                ],
                component_scores=confidence_score.component_scores,
                recommendations=confidence_score.improvement_areas + [
                    "Review all critical concerns before approval",
                    "Address all blocking gaps identified",
                    "Consider additional testing for security-related changes"
                ],
                critical_concerns=confidence_score.critical_concerns,
                strengths=confidence_score.strengths,
                improvement_areas=confidence_score.improvement_areas,
                risk_assessment=cross_ref_results.risk_assessment,
                analysis_duration=analysis_duration
            )

        except Exception as e:
            # Handle analysis errors gracefully
            analysis_duration = (datetime.now() - start_time).total_seconds()
            return PRConfidenceAnalysisResponse(
                workflow_id=workflow_id,
                analysis_timestamp=start_time.isoformat(),
                confidence_score=0.0,
                confidence_level="critical",
                approval_recommendation="reject",
                cross_reference_results={},
                detected_gaps=[],
                component_scores={},
                recommendations=["Analysis failed - manual review required"],
                critical_concerns=[f"Analysis error: {str(e)}"],
                strengths=[],
                improvement_areas=["Complete manual review due to analysis failure"],
                risk_assessment="critical",
                analysis_duration=analysis_duration
            )

    async def _perform_cross_reference_analysis(
        self,
        pr_data: Dict[str, Any],
        jira_data: Optional[Dict[str, Any]],
        confluence_docs: Optional[List[Dict[str, Any]]]
    ) -> Any:
        """Perform cross-reference analysis between PR and requirements."""
        # Use the cross-reference analyzer
        return pr_cross_reference_analyzer.perform_comprehensive_cross_reference(
            pr_data, jira_data or {}, confluence_docs or []
        )

    async def _calculate_confidence_score(
        self,
        pr_data: Dict[str, Any],
        jira_data: Optional[Dict[str, Any]],
        confluence_docs: Optional[List[Dict[str, Any]]],
        cross_ref_results: Any
    ) -> Any:
        """Calculate confidence score for PR approval."""
        # Use the confidence scorer
        return pr_confidence_scorer.calculate_confidence_score(
            pr_data,
            jira_data or {},
            confluence_docs or [],
            {
                'overall_alignment_score': cross_ref_results.overall_alignment_score,
                'requirements_alignment': cross_ref_results.requirement_alignment,
                'documentation_consistency': cross_ref_results.documentation_consistency,
                'identified_gaps': cross_ref_results.identified_gaps,
                'consistency_issues': cross_ref_results.consistency_issues
            }
        )

    async def _detect_gaps(
        self,
        pr_data: Dict[str, Any],
        jira_data: Optional[Dict[str, Any]],
        confluence_docs: Optional[List[Dict[str, Any]]],
        cross_ref_results: Any
    ) -> List[Any]:
        """Detect gaps in PR implementation."""
        # Use the gap detector
        return pr_gap_detector.detect_gaps(
            pr_data,
            jira_data or {},
            confluence_docs or [],
            {
                'overall_alignment_score': cross_ref_results.overall_alignment_score,
                'requirements_alignment': {'gaps': cross_ref_results.identified_gaps},
                'documentation_consistency': {'issues': cross_ref_results.consistency_issues}
            }
        )

    async def get_pr_analysis_history(self, pr_id: str) -> List[Dict[str, Any]]:
        """Get analysis history for a specific PR."""
        # This would query stored analysis results
        # For now, return empty list
        return []

    async def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics and metrics."""
        return {
            'total_analyses': 0,
            'average_confidence_score': 0.0,
            'common_gaps': [],
            'analysis_trends': {},
            'performance_metrics': {
                'average_analysis_time': 0.0,
                'success_rate': 0.0
            }
        }


# Create singleton instance
pr_confidence_analysis_service = PRConfidenceAnalysisService()
