"""PR Confidence Report Value Object"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from .confidence_level import ConfidenceLevel
from .approval_recommendation import ApprovalRecommendation


class PRConfidenceReport:
    """Value object representing a comprehensive PR confidence analysis report."""

    def __init__(
        self,
        workflow_id: str,
        pr_id: str,
        confidence_score: float,
        confidence_level: ConfidenceLevel,
        approval_recommendation: ApprovalRecommendation,
        component_scores: Dict[str, float],
        cross_reference_results: Dict[str, Any],
        detected_gaps: List[Dict[str, Any]],
        risk_assessment: str,
        recommendations: List[str],
        critical_concerns: List[str],
        strengths: List[str],
        improvement_areas: List[str],
        analysis_duration: float,
        jira_ticket: Optional[str] = None,
        ai_provider: str = "local_llm",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._report_id = str(uuid4())
        self._workflow_id = workflow_id.strip()
        self._pr_id = pr_id.strip()
        self._jira_ticket = jira_ticket.strip() if jira_ticket else None
        self._analysis_timestamp = datetime.utcnow()
        self._confidence_score = max(0.0, min(1.0, confidence_score))
        self._confidence_level = confidence_level
        self._approval_recommendation = approval_recommendation
        self._component_scores = component_scores.copy()
        self._cross_reference_results = cross_reference_results.copy()
        self._detected_gaps = detected_gaps.copy()
        self._risk_assessment = risk_assessment.strip()
        self._recommendations = recommendations.copy()
        self._critical_concerns = critical_concerns.copy()
        self._strengths = strengths.copy()
        self._improvement_areas = improvement_areas.copy()
        self._analysis_duration = max(0.0, analysis_duration)
        self._ai_provider = ai_provider.strip()
        self._metadata = metadata or {}

        self._validate()

    def _validate(self):
        """Validate PR confidence report data."""
        if not self._workflow_id:
            raise ValueError("Workflow ID cannot be empty")

        if not self._pr_id:
            raise ValueError("PR ID cannot be empty")

        if not self._component_scores:
            raise ValueError("Component scores cannot be empty")

        if not self._recommendations:
            raise ValueError("Recommendations cannot be empty")

    @property
    def report_id(self) -> str:
        """Get the unique report ID."""
        return self._report_id

    @property
    def workflow_id(self) -> str:
        """Get the workflow ID."""
        return self._workflow_id

    @property
    def pr_id(self) -> str:
        """Get the PR ID."""
        return self._pr_id

    @property
    def jira_ticket(self) -> Optional[str]:
        """Get the Jira ticket."""
        return self._jira_ticket

    @property
    def analysis_timestamp(self) -> datetime:
        """Get the analysis timestamp."""
        return self._analysis_timestamp

    @property
    def confidence_score(self) -> float:
        """Get the overall confidence score (0.0 to 1.0)."""
        return self._confidence_score

    @property
    def confidence_percentage(self) -> float:
        """Get the confidence score as a percentage."""
        return self._confidence_score * 100

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get the confidence level."""
        return self._confidence_level

    @property
    def approval_recommendation(self) -> ApprovalRecommendation:
        """Get the approval recommendation."""
        return self._approval_recommendation

    @property
    def component_scores(self) -> Dict[str, float]:
        """Get the component scores."""
        return self._component_scores.copy()

    @property
    def cross_reference_results(self) -> Dict[str, Any]:
        """Get the cross-reference analysis results."""
        return self._cross_reference_results.copy()

    @property
    def detected_gaps(self) -> List[Dict[str, Any]]:
        """Get the detected gaps."""
        return self._detected_gaps.copy()

    @property
    def risk_assessment(self) -> str:
        """Get the risk assessment."""
        return self._risk_assessment

    @property
    def recommendations(self) -> List[str]:
        """Get the recommendations."""
        return self._recommendations.copy()

    @property
    def critical_concerns(self) -> List[str]:
        """Get the critical concerns."""
        return self._critical_concerns.copy()

    @property
    def strengths(self) -> List[str]:
        """Get the strengths."""
        return self._strengths.copy()

    @property
    def improvement_areas(self) -> List[str]:
        """Get the improvement areas."""
        return self._improvement_areas.copy()

    @property
    def analysis_duration(self) -> float:
        """Get the analysis duration in seconds."""
        return self._analysis_duration

    @property
    def ai_provider(self) -> str:
        """Get the AI provider used."""
        return self._ai_provider

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the metadata."""
        return self._metadata.copy()

    @property
    def gap_count(self) -> int:
        """Get the total number of detected gaps."""
        return len(self._detected_gaps)

    @property
    def blocking_gaps(self) -> List[Dict[str, Any]]:
        """Get gaps that block approval."""
        return [gap for gap in self._detected_gaps if gap.get('blocking_approval', False)]

    @property
    def has_critical_concerns(self) -> bool:
        """Check if there are critical concerns."""
        return len(self._critical_concerns) > 0

    @property
    def is_ready_for_approval(self) -> bool:
        """Check if the PR is ready for approval based on analysis."""
        return (
            self._approval_recommendation == ApprovalRecommendation.APPROVE and
            len(self.blocking_gaps) == 0 and
            not self.has_critical_concerns
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "report_id": self._report_id,
            "workflow_id": self._workflow_id,
            "pr_id": self._pr_id,
            "jira_ticket": self._jira_ticket,
            "analysis_timestamp": self._analysis_timestamp.isoformat(),
            "confidence_score": self._confidence_score,
            "confidence_percentage": self.confidence_percentage,
            "confidence_level": self._confidence_level.value,
            "approval_recommendation": self._approval_recommendation.value,
            "component_scores": self._component_scores,
            "cross_reference_results": self._cross_reference_results,
            "detected_gaps": self._detected_gaps,
            "risk_assessment": self._risk_assessment,
            "recommendations": self._recommendations,
            "critical_concerns": self._critical_concerns,
            "strengths": self._strengths,
            "improvement_areas": self._improvement_areas,
            "analysis_duration": self._analysis_duration,
            "ai_provider": self._ai_provider,
            "metadata": self._metadata,
            "gap_count": self.gap_count,
            "blocking_gaps_count": len(self.blocking_gaps),
            "is_ready_for_approval": self.is_ready_for_approval
        }

    def __repr__(self) -> str:
        return f"PRConfidenceReport(report_id='{self._report_id}', pr_id='{self._pr_id}', confidence={self.confidence_percentage:.1f}%, level={self._confidence_level})"
