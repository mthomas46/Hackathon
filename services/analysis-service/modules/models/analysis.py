"""Analysis Models - Core analysis request and response models."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field, field_validator
from datetime import datetime, timezone

from .base import BaseModel


class AnalysisRequest(BaseModel):
    """Input for analysis operations."""
    targets: List[str] = Field(..., description="Document IDs or API IDs to analyze")
    analysis_type: str = Field("consistency", description="Type of analysis to perform")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional analysis options")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request tracing")

    @field_validator('targets')
    @classmethod
    def validate_targets(cls, v):
        if not v:
            raise ValueError('Targets cannot be empty')
        if len(v) > 1000:
            raise ValueError('Too many targets (max 1000)')
        for target in v:
            if len(target) > 500:
                raise ValueError('Target too long (max 500 characters)')
        return v

    @field_validator('analysis_type')
    @classmethod
    def validate_analysis_type(cls, v):
        if v not in ["consistency", "reporting", "combined"]:
            raise ValueError('Analysis type must be one of: consistency, reporting, combined')
        return v


class ReportRequest(BaseModel):
    """Input for report generation."""
    kind: str = Field(..., description="Report type (summary, life_of_ticket, pr_confidence, trends)")
    format: str = Field("json", description="Output format")
    payload: Optional[Dict[str, Any]] = Field(None, description="Report-specific parameters")

    @field_validator('kind')
    @classmethod
    def validate_kind(cls, v):
        if not v:
            raise ValueError('Kind cannot be empty')
        if len(v) > 100:
            raise ValueError('Kind too long (max 100 characters)')
        return v

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        if v not in ["json", "pdf", "html", "text"]:
            raise ValueError('Format must be one of: json, pdf, html, text')
        return v


class NotifyOwnersRequest(BaseModel):
    """Input for notification operations."""
    findings: List[Dict[str, Any]] = Field(..., description="Findings to notify owners about")
    channels: List[str] = Field(["email"], description="Notification channels to use")
    priority: str = Field("medium", description="Notification priority level")

    @field_validator('findings')
    @classmethod
    def validate_findings(cls, v):
        if not v:
            raise ValueError('Findings cannot be empty')
        if len(v) > 1000:
            raise ValueError('Too many findings (max 1000)')
        return v

    @field_validator('channels')
    @classmethod
    def validate_channels(cls, v):
        if not v:
            raise ValueError('Channels cannot be empty')
        if len(v) > 10:
            raise ValueError('Too many channels (max 10)')
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v not in ["low", "medium", "high", "urgent"]:
            raise ValueError('Priority must be one of: low, medium, high, urgent')
        return v


class FindingsResponse(BaseModel):
    """Response model for findings."""
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="List of findings")
    count: int = Field(0, description="Total number of findings")
    severity_counts: Dict[str, int] = Field(default_factory=dict, description="Findings by severity")
    type_counts: Dict[str, int] = Field(default_factory=dict, description="Findings by type")
    analysis_id: Optional[str] = Field(None, description="Analysis ID that generated these findings")
    execution_time_seconds: Optional[float] = Field(None, description="Time taken to generate findings")


class SemanticSimilarityRequest(BaseModel):
    """Request for semantic similarity analysis."""
    targets: List[str] = Field(..., description="Documents to compare for similarity")
    threshold: float = Field(0.8, ge=0.0, le=1.0, description="Similarity threshold")
    embedding_model: str = Field("sentence-transformers/all-MiniLM-L6-v2",
                                 description="Embedding model to use")
    similarity_metric: str = Field("cosine", description="Similarity metric to use")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")

    @field_validator('targets')
    @classmethod
    def validate_targets(cls, v):
        if len(v) < 2:
            raise ValueError('At least 2 targets required for similarity analysis')
        if len(v) > 100:
            raise ValueError('Too many targets (max 100)')
        return v


class SimilarityPair(BaseModel):
    """Model for document similarity pair."""
    source: str = Field(..., description="Source document ID")
    target: str = Field(..., description="Target document ID")
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in similarity score")


class SimilarityMatrix(BaseModel):
    """Model for similarity matrix."""
    matrix: List[List[float]] = Field(..., description="Similarity matrix")
    targets: List[str] = Field(..., description="Target document IDs in matrix order")


class SemanticSimilarityResponse(BaseModel):
    """Response for semantic similarity analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    analysis_type: str = Field("semantic_similarity", description="Type of analysis performed")
    targets: List[str] = Field(..., description="Documents that were analyzed")
    status: str = Field("completed", description="Analysis status")
    similarity_matrix: List[List[float]] = Field(default_factory=list,
                                                 description="Similarity matrix")
    similar_pairs: List[SimilarityPair] = Field(default_factory=list,
                                                description="Highly similar document pairs")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Analysis summary")
    execution_time_seconds: float = Field(..., description="Time taken to complete analysis")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")


class SentimentAnalysisRequest(BaseModel):
    """Request for sentiment analysis."""
    document_id: str = Field(..., description="Document ID to analyze")
    analysis_options: Optional[Dict[str, Any]] = Field(None, description="Analysis options")
    include_detailed_scores: bool = Field(True, description="Include detailed sentiment scores")
    language: str = Field("en", description="Document language")


class SentimentScores(BaseModel):
    """Model for sentiment scores."""
    positive: float = Field(..., ge=0.0, le=1.0, description="Positive sentiment score")
    negative: float = Field(..., ge=0.0, le=1.0, description="Negative sentiment score")
    neutral: float = Field(..., ge=0.0, le=1.0, description="Neutral sentiment score")


class DetailedAnalysis(BaseModel):
    """Model for detailed sentiment analysis."""
    sentence_sentiments: List[Dict[str, Any]] = Field(default_factory=list,
                                                      description="Sentiment per sentence")
    overall_tone: str = Field(..., description="Overall document tone")
    readability_score: float = Field(..., description="Document readability score")


class SentimentAnalysisResponse(BaseModel):
    """Response for sentiment analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_id: str = Field(..., description="Document that was analyzed")
    sentiment: str = Field(..., description="Overall sentiment")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in sentiment analysis")
    scores: SentimentScores = Field(..., description="Detailed sentiment scores")
    detailed_analysis: DetailedAnalysis = Field(..., description="Detailed analysis results")
    execution_time_seconds: float = Field(..., description="Time taken to complete analysis")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")


class ToneAnalysisRequest(BaseModel):
    """Request for tone analysis."""
    document_id: str = Field(..., description="Document ID to analyze")
    analysis_options: Optional[Dict[str, Any]] = Field(None, description="Analysis options")
    include_detailed_scores: bool = Field(True, description="Include detailed tone scores")
    language: str = Field("en", description="Document language")


class ToneAnalysisResponse(BaseModel):
    """Response for tone analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_id: str = Field(..., description="Document that was analyzed")
    overall_tone: str = Field(..., description="Overall document tone")
    tone_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in tone analysis")
    tone_distribution: Dict[str, float] = Field(default_factory=dict, description="Tone distribution")
    key_phrases: List[str] = Field(default_factory=list, description="Key phrases affecting tone")
    writing_style: Dict[str, Any] = Field(default_factory=dict, description="Writing style analysis")
    readability_score: float = Field(..., description="Document readability score")
    execution_time_seconds: float = Field(..., description="Time taken to complete analysis")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")


class ContentQualityRequest(BaseModel):
    """Request for content quality analysis."""
    document_id: str = Field(..., description="Document ID to analyze")
    quality_checks: List[str] = Field(..., description="Quality checks to perform")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")

    @field_validator('quality_checks')
    @classmethod
    def validate_quality_checks(cls, v):
        if not v:
            raise ValueError('Quality checks cannot be empty')
        valid_checks = ['readability', 'grammar', 'structure', 'completeness', 'consistency']
        invalid_checks = [check for check in v if check not in valid_checks]
        if invalid_checks:
            raise ValueError(f'Invalid quality checks: {invalid_checks}. Valid: {valid_checks}')
        return v


class QualityBreakdown(BaseModel):
    """Model for quality analysis breakdown."""
    readability: Dict[str, Any] = Field(default_factory=dict, description="Readability analysis")
    grammar: Dict[str, Any] = Field(default_factory=dict, description="Grammar analysis")
    structure: Dict[str, Any] = Field(default_factory=dict, description="Structure analysis")
    completeness: Dict[str, Any] = Field(default_factory=dict, description="Completeness analysis")


class Recommendation(BaseModel):
    """Model for quality recommendations."""
    priority: str = Field(..., description="Recommendation priority")
    category: str = Field(..., description="Recommendation category")
    description: str = Field(..., description="Recommendation description")
    impact: str = Field(..., description="Expected impact")


class ImprovementSuggestion(BaseModel):
    """Model for improvement suggestions."""
    high_priority: List[str] = Field(default_factory=list, description="High priority suggestions")
    medium_priority: List[str] = Field(default_factory=list, description="Medium priority suggestions")
    low_priority: List[str] = Field(default_factory=list, description="Low priority suggestions")


class ContentQualityResponse(BaseModel):
    """Response for content quality analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_id: str = Field(..., description="Document that was analyzed")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall quality score")
    quality_breakdown: QualityBreakdown = Field(..., description="Detailed quality breakdown")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Quality recommendations")
    improvement_suggestions: ImprovementSuggestion = Field(..., description="Improvement suggestions")
    execution_time_seconds: float = Field(..., description="Time taken to complete analysis")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")


class TrendAnalysisRequest(BaseModel):
    """Request for trend analysis."""
    document_id: str = Field(..., description="Document ID to analyze")
    time_range_days: int = Field(90, ge=1, le=365, description="Analysis time range in days")
    trend_metrics: List[str] = Field(..., description="Metrics to analyze for trends")
    forecast_days: int = Field(30, ge=1, le=180, description="Days to forecast")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class TrendData(BaseModel):
    """Model for trend data."""
    historical_data: List[Dict[str, Any]] = Field(default_factory=list, description="Historical data points")
    current_value: float = Field(..., description="Current metric value")
    trend_direction: str = Field(..., description="Trend direction")
    trend_slope: float = Field(..., description="Trend slope")
    volatility: float = Field(..., description="Data volatility")
    forecast: Dict[str, Any] = Field(default_factory=dict, description="Forecast data")


class ForecastData(BaseModel):
    """Model for forecast data."""
    forecasted_value: float = Field(..., description="Forecasted value")
    confidence_interval: Dict[str, float] = Field(..., description="Confidence interval")


class TrendAnalysisResponse(BaseModel):
    """Response for trend analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_id: str = Field(..., description="Document that was analyzed")
    time_range_days: int = Field(..., description="Analysis time range")
    trend_data: Dict[str, TrendData] = Field(default_factory=dict, description="Trend analysis data")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from analysis")
    recommendations: List[str] = Field(default_factory=list, description="Trend-based recommendations")
    forecast_accuracy: float = Field(..., ge=0.0, le=1.0, description="Forecast accuracy score")
    execution_time_seconds: float = Field(..., description="Time taken to complete analysis")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")


class PortfolioTrendAnalysisRequest(BaseModel):
    """Request for portfolio trend analysis."""
    document_ids: List[str] = Field(..., description="Document IDs to analyze")
    time_range_days: int = Field(90, ge=1, le=365, description="Analysis time range in days")
    trend_metrics: List[str] = Field(..., description="Metrics to analyze for trends")
    forecast_days: int = Field(30, ge=1, le=180, description="Days to forecast")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class PortfolioTrendAnalysisResponse(BaseModel):
    """Response for portfolio trend analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_ids: List[str] = Field(..., description="Documents that were analyzed")
    time_range_days: int = Field(..., description="Analysis time range")
    portfolio_trend_data: Dict[str, Any] = Field(default_factory=dict, description="Portfolio trend data")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from analysis")
    recommendations: List[str] = Field(default_factory=list, description="Trend-based recommendations")
    forecast_accuracy: float = Field(..., ge=0.0, le=1.0, description="Forecast accuracy score")
    execution_time_seconds: float = Field(..., description="Time taken to complete analysis")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
