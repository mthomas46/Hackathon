"""Analysis-specific HTTP models for FastAPI endpoints."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseResponse, SuccessResponse, ErrorResponse
from .common import FilterCriteria


class AnalysisType(str, Enum):
    """Analysis type enumeration."""
    CONSISTENCY = "consistency"
    QUALITY = "quality"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    SENTIMENT = "sentiment"
    TONE = "tone"
    TREND = "trend"
    RISK = "risk"
    MAINTENANCE = "maintenance"
    DEGRADATION = "degradation"
    CHANGE_IMPACT = "change_impact"
    REMEDIATION = "remediation"


class SeverityLevel(str, Enum):
    """Severity level enumeration."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AnalysisRequest(BaseModel):
    """Base analysis request model."""

    targets: List[str] = Field(..., description="Document or content targets to analyze")
    analysis_type: AnalysisType = Field(..., description="Type of analysis to perform")
    detectors: Optional[List[str]] = Field(None, description="Specific detectors to use")
    options: Optional[Dict[str, Any]] = Field(None, description="Analysis-specific options")

    @validator('targets')
    def validate_targets(cls, v):
        """Validate analysis targets."""
        if not v:
            raise ValueError("At least one target must be specified")
        if len(v) > 100:
            raise ValueError("Maximum 100 targets allowed")
        return v


class AnalysisResponse(BaseResponse):
    """Base analysis response model."""

    analysis_id: str = Field(..., description="Unique analysis identifier")
    analysis_type: AnalysisType = Field(..., description="Type of analysis performed")
    targets: List[str] = Field(..., description="Targets that were analyzed")
    status: str = Field(..., description="Analysis status")
    results: Dict[str, Any] = Field(..., description="Analysis results")
    findings: Optional[List[Dict[str, Any]]] = Field(None, description="Analysis findings")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Analysis metadata")


class SemanticSimilarityRequest(AnalysisRequest):
    """Semantic similarity analysis request."""

    analysis_type: AnalysisType = AnalysisType.SEMANTIC_SIMILARITY
    threshold: float = Field(0.8, ge=0.0, le=1.0, description="Similarity threshold")
    embedding_model: Optional[str] = Field("sentence-transformers/all-MiniLM-L6-v2", description="Embedding model")
    similarity_metric: Optional[str] = Field("cosine", description="Similarity metric")
    options: Optional[Dict[str, Any]] = Field({
        "normalize_embeddings": True,
        "batch_size": 32
    }, description="Embedding options")

    @validator('similarity_metric')
    def validate_similarity_metric(cls, v):
        """Validate similarity metric."""
        valid_metrics = ['cosine', 'euclidean', 'manhattan', 'dot_product']
        if v not in valid_metrics:
            raise ValueError(f"Invalid similarity metric: {v}. Must be one of {valid_metrics}")
        return v


class SemanticSimilarityResponse(AnalysisResponse):
    """Semantic similarity analysis response."""

    analysis_type: AnalysisType = AnalysisType.SEMANTIC_SIMILARITY
    similarities: List[Dict[str, Any]] = Field(..., description="Similarity results")
    clusters: Optional[List[Dict[str, Any]]] = Field(None, description="Similarity clusters")


class SentimentAnalysisRequest(AnalysisRequest):
    """Sentiment analysis request."""

    analysis_type: AnalysisType = AnalysisType.SENTIMENT
    model: Optional[str] = Field("cardiffnlp/twitter-roberta-base-sentiment-latest", description="Sentiment model")
    language: Optional[str] = Field("en", description="Content language")
    options: Optional[Dict[str, Any]] = Field({
        "return_all_scores": True,
        "truncation": True
    }, description="Sentiment analysis options")


class SentimentAnalysisResponse(AnalysisResponse):
    """Sentiment analysis response."""

    analysis_type: AnalysisType = AnalysisType.SENTIMENT
    sentiments: List[Dict[str, Any]] = Field(..., description="Sentiment results")
    overall_sentiment: Optional[Dict[str, Any]] = Field(None, description="Overall sentiment summary")


class ToneAnalysisRequest(AnalysisRequest):
    """Tone analysis request."""

    analysis_type: AnalysisType = AnalysisType.TONE
    aspects: Optional[List[str]] = Field([
        "formality", "confidence", "urgency", "clarity", "technical_level"
    ], description="Tone aspects to analyze")
    options: Optional[Dict[str, Any]] = Field(None, description="Tone analysis options")


class ToneAnalysisResponse(AnalysisResponse):
    """Tone analysis response."""

    analysis_type: AnalysisType = AnalysisType.TONE
    tone_scores: Dict[str, float] = Field(..., description="Tone scores by aspect")
    recommendations: Optional[List[str]] = Field(None, description="Tone improvement recommendations")


class ContentQualityRequest(AnalysisRequest):
    """Content quality analysis request."""

    analysis_type: AnalysisType = AnalysisType.QUALITY
    metrics: Optional[List[str]] = Field([
        "readability", "completeness", "accuracy", "consistency", "structure"
    ], description="Quality metrics to evaluate")
    thresholds: Optional[Dict[str, float]] = Field({
        "readability_min": 60.0,
        "completeness_min": 0.7,
        "accuracy_min": 0.8
    }, description="Quality thresholds")
    options: Optional[Dict[str, Any]] = Field(None, description="Quality analysis options")


class ContentQualityResponse(AnalysisResponse):
    """Content quality analysis response."""

    analysis_type: AnalysisType = AnalysisType.QUALITY
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    metrics: Dict[str, Any] = Field(..., description="Detailed quality metrics")
    recommendations: List[str] = Field(..., description="Quality improvement recommendations")


class TrendAnalysisRequest(AnalysisRequest):
    """Trend analysis request."""

    analysis_type: AnalysisType = AnalysisType.TREND
    time_range: Optional[str] = Field("30d", description="Time range for trend analysis")
    granularity: Optional[str] = Field("daily", description="Analysis granularity")
    metrics: Optional[List[str]] = Field([
        "quality_score", "finding_count", "severity_distribution"
    ], description="Metrics to analyze")
    forecast_periods: Optional[int] = Field(7, description="Number of periods to forecast")
    options: Optional[Dict[str, Any]] = Field(None, description="Trend analysis options")

    @validator('time_range')
    def validate_time_range(cls, v):
        """Validate time range format."""
        import re
        if not re.match(r'^\d+[dhwmy]$', v):
            raise ValueError("Time range must be in format: <number><unit> (e.g., 30d, 1w, 6m)")
        return v

    @validator('granularity')
    def validate_granularity(cls, v):
        """Validate granularity."""
        valid_granularities = ['hourly', 'daily', 'weekly', 'monthly']
        if v not in valid_granularities:
            raise ValueError(f"Invalid granularity: {v}. Must be one of {valid_granularities}")
        return v


class TrendAnalysisResponse(AnalysisResponse):
    """Trend analysis response."""

    analysis_type: AnalysisType = AnalysisType.TREND
    trends: Dict[str, List[Dict[str, Any]]] = Field(..., description="Trend data by metric")
    forecasts: Optional[Dict[str, List[Dict[str, Any]]]] = Field(None, description="Forecast data")
    insights: List[str] = Field(..., description="Key insights from trend analysis")


class RiskAssessmentRequest(AnalysisRequest):
    """Risk assessment request."""

    analysis_type: AnalysisType = AnalysisType.RISK
    risk_factors: Optional[List[str]] = Field([
        "quality_degradation", "stale_content", "missing_coverage", "inconsistency"
    ], description="Risk factors to assess")
    severity_thresholds: Optional[Dict[str, float]] = Field({
        "critical": 0.8,
        "high": 0.6,
        "medium": 0.4
    }, description="Risk severity thresholds")
    options: Optional[Dict[str, Any]] = Field(None, description="Risk assessment options")


class RiskAssessmentResponse(AnalysisResponse):
    """Risk assessment response."""

    analysis_type: AnalysisType = AnalysisType.RISK
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Overall risk score")
    risk_factors: Dict[str, Any] = Field(..., description="Detailed risk factor assessments")
    mitigation_actions: List[str] = Field(..., description="Recommended mitigation actions")


class MaintenanceForecastRequest(AnalysisRequest):
    """Maintenance forecast request."""

    analysis_type: AnalysisType = AnalysisType.MAINTENANCE
    forecast_horizon: Optional[int] = Field(90, description="Forecast horizon in days")
    factors: Optional[List[str]] = Field([
        "content_age", "update_frequency", "quality_trends", "usage_patterns"
    ], description="Forecast factors")
    confidence_level: Optional[float] = Field(0.95, description="Forecast confidence level")
    options: Optional[Dict[str, Any]] = Field(None, description="Forecast options")

    @validator('forecast_horizon')
    def validate_forecast_horizon(cls, v):
        """Validate forecast horizon."""
        if v < 1 or v > 365:
            raise ValueError("Forecast horizon must be between 1 and 365 days")
        return v

    @validator('confidence_level')
    def validate_confidence_level(cls, v):
        """Validate confidence level."""
        if v < 0.5 or v > 0.99:
            raise ValueError("Confidence level must be between 0.5 and 0.99")
        return v


class MaintenanceForecastResponse(AnalysisResponse):
    """Maintenance forecast response."""

    analysis_type: AnalysisType = AnalysisType.MAINTENANCE
    forecasts: List[Dict[str, Any]] = Field(..., description="Maintenance forecasts")
    schedule: Dict[str, Any] = Field(..., description="Recommended maintenance schedule")
    resource_requirements: Optional[Dict[str, Any]] = Field(None, description="Resource requirements")


class QualityDegradationRequest(AnalysisRequest):
    """Quality degradation detection request."""

    analysis_type: AnalysisType = AnalysisType.DEGRADATION
    baseline_period: Optional[str] = Field("30d", description="Baseline period for comparison")
    degradation_metrics: Optional[List[str]] = Field([
        "quality_score", "readability", "completeness", "consistency"
    ], description="Metrics to monitor for degradation")
    sensitivity: Optional[float] = Field(0.1, description="Degradation detection sensitivity")
    options: Optional[Dict[str, Any]] = Field(None, description="Degradation detection options")


class QualityDegradationResponse(AnalysisResponse):
    """Quality degradation detection response."""

    analysis_type: AnalysisType = AnalysisType.DEGRADATION
    degradation_score: float = Field(..., ge=0.0, le=1.0, description="Overall degradation score")
    degraded_metrics: Dict[str, Any] = Field(..., description="Degraded metrics details")
    alerts: List[str] = Field(..., description="Quality degradation alerts")


class ChangeImpactRequest(AnalysisRequest):
    """Change impact analysis request."""

    analysis_type: AnalysisType = AnalysisType.CHANGE_IMPACT
    change_description: str = Field(..., description="Description of the change")
    impact_scope: Optional[str] = Field("related", description="Scope of impact analysis")
    stakeholders: Optional[List[str]] = Field(None, description="Affected stakeholders")
    options: Optional[Dict[str, Any]] = Field(None, description="Impact analysis options")

    @validator('impact_scope')
    def validate_impact_scope(cls, v):
        """Validate impact scope."""
        valid_scopes = ['direct', 'related', 'full']
        if v not in valid_scopes:
            raise ValueError(f"Invalid impact scope: {v}. Must be one of {valid_scopes}")
        return v


class ChangeImpactResponse(AnalysisResponse):
    """Change impact analysis response."""

    analysis_type: AnalysisType = AnalysisType.CHANGE_IMPACT
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Overall impact score")
    affected_entities: List[Dict[str, Any]] = Field(..., description="Affected entities")
    risk_assessment: Dict[str, Any] = Field(..., description="Impact risk assessment")
    recommendations: List[str] = Field(..., description="Impact mitigation recommendations")


class FindingFilter(BaseModel):
    """Filter for findings."""

    severity: Optional[SeverityLevel] = Field(None, description="Filter by severity")
    finding_type: Optional[str] = Field(None, description="Filter by finding type")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")


class FindingsResponse(BaseResponse):
    """Findings list response."""

    findings: List[Dict[str, Any]] = Field(..., description="List of findings")
    total_count: int = Field(..., description="Total number of findings")
    filter_applied: Optional[Dict[str, Any]] = Field(None, description="Applied filters")
