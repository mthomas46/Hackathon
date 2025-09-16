"""Analytics domain entities for performance tracking and insights."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from ...core.entities import BaseEntity


@dataclass
class PromptPerformanceMetrics(BaseEntity):
    """Performance metrics for prompt execution."""
    prompt_id: str
    version: int
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time_ms: float = 0.0
    median_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    total_tokens_used: int = 0
    average_tokens_per_request: float = 0.0
    cost_estimate_usd: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests) if self.total_requests > 0 else 0,
            "average_response_time_ms": self.average_response_time_ms,
            "median_response_time_ms": self.median_response_time_ms,
            "p95_response_time_ms": self.p95_response_time_ms,
            "p99_response_time_ms": self.p99_response_time_ms,
            "total_tokens_used": self.total_tokens_used,
            "average_tokens_per_request": self.average_tokens_per_request,
            "cost_estimate_usd": self.cost_estimate_usd,
            "last_updated": self.last_updated.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class UserSatisfactionScore(BaseEntity):
    """User satisfaction scores for prompts."""
    prompt_id: str
    user_id: str
    session_id: str
    rating: float  # 1.0 to 5.0 scale
    feedback_text: Optional[str] = None
    context_tags: List[str] = field(default_factory=list)
    response_quality_score: Optional[float] = None  # AI-assessed quality
    use_case_category: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "rating": self.rating,
            "feedback_text": self.feedback_text,
            "context_tags": self.context_tags,
            "response_quality_score": self.response_quality_score,
            "use_case_category": self.use_case_category,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class PromptOptimizationSuggestion(BaseEntity):
    """AI-generated suggestions for prompt improvement."""
    prompt_id: str
    current_version: int
    suggestion_type: str  # "clarity", "specificity", "structure", "bias", etc.
    confidence_score: float  # 0.0 to 1.0
    suggestion_text: str
    proposed_changes: Dict[str, Any]
    expected_impact: str  # "high", "medium", "low"
    llm_service_used: str
    implemented: bool = False
    implemented_at: Optional[datetime] = None
    implementation_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "current_version": self.current_version,
            "suggestion_type": self.suggestion_type,
            "confidence_score": self.confidence_score,
            "suggestion_text": self.suggestion_text,
            "proposed_changes": self.proposed_changes,
            "expected_impact": self.expected_impact,
            "llm_service_used": self.llm_service_used,
            "implemented": self.implemented,
            "implemented_at": self.implemented_at.isoformat() if self.implemented_at else None,
            "implementation_result": self.implementation_result,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class PromptEvolutionMetrics(BaseEntity):
    """Track how prompts evolve and improve over time."""
    prompt_id: str
    from_version: int
    to_version: int
    change_type: str  # "manual_edit", "refinement", "optimization", "ab_test_winner"
    performance_delta: Dict[str, float]  # Before/after metrics comparison
    quality_improvement_score: float  # 0.0 to 1.0
    user_satisfaction_change: Optional[float] = None
    token_efficiency_change: Optional[float] = None
    cost_savings_usd: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "change_type": self.change_type,
            "performance_delta": self.performance_delta,
            "quality_improvement_score": self.quality_improvement_score,
            "user_satisfaction_change": self.user_satisfaction_change,
            "token_efficiency_change": self.token_efficiency_change,
            "cost_savings_usd": self.cost_savings_usd,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class CostOptimizationMetrics(BaseEntity):
    """Track and optimize LLM API costs."""
    prompt_id: str
    version: int
    total_cost_usd: float
    cost_per_request_usd: float
    token_efficiency_score: float  # tokens per dollar
    optimization_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    cost_trend: str = "stable"  # "increasing", "decreasing", "stable"
    projected_monthly_savings: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "total_cost_usd": self.total_cost_usd,
            "cost_per_request_usd": self.cost_per_request_usd,
            "token_efficiency_score": self.token_efficiency_score,
            "optimization_opportunities": self.optimization_opportunities,
            "cost_trend": self.cost_trend,
            "projected_monthly_savings": self.projected_monthly_savings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class BiasDetectionResult(BaseEntity):
    """Results from bias detection analysis."""
    prompt_id: str
    version: int
    bias_type: str  # "gender", "racial", "cultural", "political", etc.
    severity_score: float  # 0.0 to 1.0
    detected_phrases: List[str]
    suggested_alternatives: List[str]
    confidence_score: float
    analysis_method: str  # "pattern_matching", "llm_analysis", "statistical"
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "bias_type": self.bias_type,
            "severity_score": self.severity_score,
            "detected_phrases": self.detected_phrases,
            "suggested_alternatives": self.suggested_alternatives,
            "confidence_score": self.confidence_score,
            "analysis_method": self.analysis_method,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class PromptTestingResult(BaseEntity):
    """Results from automated prompt testing."""
    prompt_id: str
    version: int
    test_suite_id: str
    test_case_id: str
    test_name: str
    passed: bool
    execution_time_ms: float
    output_quality_score: float
    expected_output_similarity: float  # How close to expected result
    error_message: Optional[str] = None
    test_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "test_suite_id": self.test_suite_id,
            "test_case_id": self.test_case_id,
            "test_name": self.test_name,
            "passed": self.passed,
            "execution_time_ms": self.execution_time_ms,
            "output_quality_score": self.output_quality_score,
            "expected_output_similarity": self.expected_output_similarity,
            "error_message": self.error_message,
            "test_metadata": self.test_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
