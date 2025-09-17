"""Request and response models for Analysis Service.

Contains all Pydantic models used for API requests and responses.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_validator

try:
    from services.shared.models import Finding
except ImportError:
    # Fallback for testing or when shared services are not available
    class Finding:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


class AnalysisRequest(BaseModel):
    """Input for analysis operations."""
    targets: List[str]  # Document IDs or API IDs
    analysis_type: str = "consistency"  # consistency, reporting, combined
    options: Optional[Dict[str, Any]] = None

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
    kind: str  # summary, life_of_ticket, pr_confidence, trends
    format: str = "json"
    payload: Optional[Dict[str, Any]] = None

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
    findings: List[Dict[str, Any]]
    channels: List[str] = ["email"]
    priority: str = "medium"

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
    findings: List[Finding]
    count: int
    severity_counts: Dict[str, int]
    type_counts: Dict[str, int]


class ArchitectureAnalysisRequest(BaseModel):
    """Input for architecture analysis operations."""
    components: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    analysis_type: str = "consistency"  # consistency, completeness, best_practices
    options: Optional[Dict[str, Any]] = None

    @field_validator('components')
    @classmethod
    def validate_components(cls, v):
        if not v:
            raise ValueError('Components cannot be empty')
        for comp in v:
            if not comp.get('id'):
                raise ValueError('Each component must have an id')
            if not comp.get('type'):
                raise ValueError('Each component must have a type')
        return v

    @field_validator('analysis_type')
    @classmethod
    def validate_analysis_type(cls, v):
        supported = ['consistency', 'completeness', 'best_practices', 'combined']
        if v not in supported:
            raise ValueError(f'Unsupported analysis type: {v}. Must be one of {supported}')
        return v


class SemanticSimilarityRequest(BaseModel):
    """Input for semantic similarity analysis operations."""
    document_ids: List[str]
    similarity_threshold: float = 0.8
    analysis_scope: str = "content"  # content, titles, metadata
    options: Optional[Dict[str, Any]] = None

    @field_validator('document_ids')
    @classmethod
    def validate_document_ids(cls, v):
        if not v:
            raise ValueError('Document IDs cannot be empty')
        if len(v) > 100:
            raise ValueError('Too many documents (max 100)')
        for doc_id in v:
            if len(doc_id) > 500:
                raise ValueError('Document ID too long (max 500 characters)')
        return v

    @field_validator('similarity_threshold')
    @classmethod
    def validate_similarity_threshold(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Similarity threshold must be between 0.0 and 1.0')
        return v

    @field_validator('analysis_scope')
    @classmethod
    def validate_analysis_scope(cls, v):
        supported = ['content', 'titles', 'metadata', 'combined']
        if v not in supported:
            raise ValueError(f'Unsupported analysis scope: {v}. Must be one of {supported}')
        return v


class SimilarityPair(BaseModel):
    """Represents a pair of similar documents."""
    document_id_1: str
    document_id_2: str
    similarity_score: float
    confidence: float
    similar_sections: List[str]
    rationale: str


class SemanticSimilarityResponse(BaseModel):
    """Response model for semantic similarity analysis."""
    total_documents: int
    similarity_pairs: List[SimilarityPair]
    analysis_summary: Dict[str, Any]
    processing_time: float
    model_used: str


class SentimentAnalysisRequest(BaseModel):
    """Input for sentiment analysis operations."""
    document_id: str
    use_transformer: bool = True
    include_tone_analysis: bool = True

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Document ID cannot be empty')
        if len(v) > 500:
            raise ValueError('Document ID too long (max 500 characters)')
        return v.strip()


class SentimentAnalysisResponse(BaseModel):
    """Response model for sentiment analysis."""
    document_id: str
    sentiment_analysis: Dict[str, Any]
    readability_metrics: Dict[str, Any]
    tone_analysis: Dict[str, Any]
    quality_score: float
    processing_time: float
    recommendations: List[str]


class ToneAnalysisRequest(BaseModel):
    """Input for tone analysis operations."""
    document_id: str
    analysis_scope: str = "full"  # full, sentiment_only, readability_only

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Document ID cannot be empty')
        if len(v) > 500:
            raise ValueError('Document ID too long (max 500 characters)')
        return v.strip()

    @field_validator('analysis_scope')
    @classmethod
    def validate_analysis_scope(cls, v):
        supported = ['full', 'sentiment_only', 'readability_only', 'tone_only']
        if v not in supported:
            raise ValueError(f'Unsupported analysis scope: {v}. Must be one of {supported}')
        return v


class ToneAnalysisResponse(BaseModel):
    """Response model for tone analysis."""
    document_id: str
    primary_tone: str
    tone_scores: Dict[str, float]
    tone_indicators: Dict[str, int]
    sentiment_summary: Dict[str, Any]
    clarity_assessment: Dict[str, Any]
    processing_time: float


class ContentQualityRequest(BaseModel):
    """Input for content quality assessment."""
    document_id: str
    include_detailed_metrics: bool = True

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Document ID cannot be empty')
        if len(v) > 500:
            raise ValueError('Document ID too long (max 500 characters)')
        return v.strip()


class ContentQualityResponse(BaseModel):
    """Response model for content quality assessment."""
    document_id: str
    quality_assessment: Dict[str, Any]
    detailed_metrics: Optional[Dict[str, Any]] = None
    recommendations: List[str]
    processing_time: float
    analysis_timestamp: float


class TrendAnalysisRequest(BaseModel):
    """Input for trend analysis operations."""
    document_id: str
    analysis_results: List[Dict[str, Any]]
    prediction_days: int = 30
    include_predictions: bool = True

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Document ID cannot be empty')
        if len(v) > 500:
            raise ValueError('Document ID too long (max 500 characters)')
        return v.strip()

    @field_validator('analysis_results')
    @classmethod
    def validate_analysis_results(cls, v):
        if not v:
            raise ValueError('Analysis results cannot be empty')
        if len(v) > 1000:
            raise ValueError('Too many analysis results (max 1000)')
        return v

    @field_validator('prediction_days')
    @classmethod
    def validate_prediction_days(cls, v):
        if v < 1 or v > 365:
            raise ValueError('Prediction days must be between 1 and 365')
        return v


class PortfolioTrendAnalysisRequest(BaseModel):
    """Input for portfolio trend analysis operations."""
    analysis_results: List[Dict[str, Any]]
    group_by: str = "document_id"
    prediction_days: int = 30

    @field_validator('analysis_results')
    @classmethod
    def validate_analysis_results(cls, v):
        if not v:
            raise ValueError('Analysis results cannot be empty')
        if len(v) > 10000:
            raise ValueError('Too many analysis results (max 10000)')
        return v

    @field_validator('group_by')
    @classmethod
    def validate_group_by(cls, v):
        supported = ['document_id', 'source_type', 'analysis_type']
        if v not in supported:
            raise ValueError(f'Unsupported group_by field: {v}. Must be one of {supported}')
        return v


class TrendAnalysisResponse(BaseModel):
    """Response model for trend analysis."""
    document_id: str
    trend_direction: str
    confidence: float
    patterns: Dict[str, Any]
    predictions: Dict[str, Any]
    risk_areas: List[Dict[str, Any]]
    insights: List[str]
    analysis_period_days: int
    data_points: int
    volatility: float
    processing_time: float
    analysis_timestamp: float


class PortfolioTrendAnalysisResponse(BaseModel):
    """Response model for portfolio trend analysis."""
    portfolio_summary: Dict[str, Any]
    document_trends: List[Dict[str, Any]]
    processing_time: float
    analysis_timestamp: float


class RiskAssessmentRequest(BaseModel):
    """Input for risk assessment operations."""
    document_id: str
    document_data: Dict[str, Any]
    analysis_history: Optional[List[Dict[str, Any]]] = None

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Document ID cannot be empty')
        if len(v) > 500:
            raise ValueError('Document ID too long (max 500 characters)')
        return v.strip()

    @field_validator('document_data')
    @classmethod
    def validate_document_data(cls, v):
        if not v:
            raise ValueError('Document data cannot be empty')
        required_keys = ['content']  # At minimum, content is required
        if not any(key in v for key in required_keys):
            raise ValueError('Document data must contain at least content or metadata')
        return v


class PortfolioRiskAssessmentRequest(BaseModel):
    """Input for portfolio risk assessment operations."""
    documents: List[Dict[str, Any]]
    group_by: str = "document_type"

    @field_validator('documents')
    @classmethod
    def validate_documents(cls, v):
        if not v:
            raise ValueError('Documents list cannot be empty')
        if len(v) > 1000:
            raise ValueError('Too many documents (max 1000)')
        return v

    @field_validator('group_by')
    @classmethod
    def validate_group_by(cls, v):
        supported = ['document_type', 'source_type', 'owner', 'department']
        if v not in supported:
            raise ValueError(f'Unsupported group_by field: {v}. Must be one of {supported}')
        return v


class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessment."""
    document_id: str
    overall_risk: Dict[str, Any]
    risk_factors: Dict[str, Any]
    risk_drivers: List[Dict[str, Any]]
    recommendations: List[str]
    assessment_timestamp: float
    processing_time: float


class PortfolioRiskAssessmentResponse(BaseModel):
    """Response model for portfolio risk assessment."""
    portfolio_summary: Dict[str, Any]
    document_assessments: List[Dict[str, Any]]
    high_risk_documents: List[str]
    processing_time: float
    assessment_timestamp: float


class MaintenanceForecastRequest(BaseModel):
    """Input for maintenance forecasting operations."""
    document_id: str
    document_data: Dict[str, Any]
    analysis_history: Optional[List[Dict[str, Any]]] = None

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Document ID cannot be empty')
        if len(v) > 500:
            raise ValueError('Document ID too long (max 500 characters)')
        return v.strip()

    @field_validator('document_data')
    @classmethod
    def validate_document_data(cls, v):
        if not v:
            raise ValueError('Document data cannot be empty')
        required_keys = ['content']  # At minimum, content is required
        if not any(key in v for key in required_keys):
            raise ValueError('Document data must contain at least content or metadata')
        return v


class PortfolioMaintenanceForecastRequest(BaseModel):
    """Input for portfolio maintenance forecasting operations."""
    documents: List[Dict[str, Any]]
    group_by: str = "document_type"

    @field_validator('documents')
    @classmethod
    def validate_documents(cls, v):
        if not v:
            raise ValueError('Documents list cannot be empty')
        if len(v) > 1000:
            raise ValueError('Too many documents (max 1000)')
        return v

    @field_validator('group_by')
    @classmethod
    def validate_group_by(cls, v):
        supported = ['document_type', 'source_type', 'owner', 'department', 'priority_level']
        if v not in supported:
            raise ValueError(f'Unsupported group_by field: {v}. Must be one of {supported}')
        return v


class MaintenanceForecastResponse(BaseModel):
    """Response model for maintenance forecasting."""
    document_id: str
    forecast_data: Dict[str, Any]
    recommendations: List[str]
    processing_time: float
    forecast_timestamp: float


class PortfolioMaintenanceForecastResponse(BaseModel):
    """Response model for portfolio maintenance forecasting."""
    portfolio_summary: Dict[str, Any]
    maintenance_schedule: List[Dict[str, Any]]
    document_forecasts: List[Dict[str, Any]]
    processing_time: float
    forecast_timestamp: float


class QualityDegradationDetectionRequest(BaseModel):
    """Input for quality degradation detection operations."""
    document_id: str
    analysis_history: List[Dict[str, Any]]
    baseline_period_days: int = 90
    alert_threshold: float = 0.1

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Document ID cannot be empty')
        if len(v) > 500:
            raise ValueError('Document ID too long (max 500 characters)')
        return v.strip()

    @field_validator('analysis_history')
    @classmethod
    def validate_analysis_history(cls, v):
        if not v:
            raise ValueError('Analysis history cannot be empty')
        if len(v) > 1000:
            raise ValueError('Analysis history too large (max 1000 entries)')
        return v

    @field_validator('baseline_period_days')
    @classmethod
    def validate_baseline_period_days(cls, v):
        if v < 7 or v > 730:
            raise ValueError('Baseline period must be between 7 and 730 days')
        return v

    @field_validator('alert_threshold')
    @classmethod
    def validate_alert_threshold(cls, v):
        if v < 0.01 or v > 0.5:
            raise ValueError('Alert threshold must be between 0.01 and 0.5')
        return v


class PortfolioQualityDegradationRequest(BaseModel):
    """Input for portfolio quality degradation monitoring operations."""
    documents: List[Dict[str, Any]]
    baseline_period_days: int = 90
    alert_threshold: float = 0.1

    @field_validator('documents')
    @classmethod
    def validate_documents(cls, v):
        if not v:
            raise ValueError('Documents list cannot be empty')
        if len(v) > 1000:
            raise ValueError('Too many documents (max 1000)')
        return v

    @field_validator('baseline_period_days')
    @classmethod
    def validate_baseline_period_days(cls, v):
        if v < 7 or v > 730:
            raise ValueError('Baseline period must be between 7 and 730 days')
        return v

    @field_validator('alert_threshold')
    @classmethod
    def validate_alert_threshold(cls, v):
        if v < 0.01 or v > 0.5:
            raise ValueError('Alert threshold must be between 0.01 and 0.5')
        return v


class QualityDegradationDetectionResponse(BaseModel):
    """Response model for quality degradation detection."""
    document_id: str
    degradation_detected: bool
    severity_assessment: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    volatility_analysis: Dict[str, Any]
    degradation_events: List[Dict[str, Any]]
    finding_trend: Dict[str, Any]
    analysis_period_days: int
    data_points: int
    baseline_period_days: int
    alert_threshold: float
    alerts: List[Dict[str, Any]]
    processing_time: float
    detection_timestamp: float


class PortfolioQualityDegradationResponse(BaseModel):
    """Response model for portfolio quality degradation monitoring."""
    portfolio_summary: Dict[str, Any]
    degradation_results: List[Dict[str, Any]]
    alerts_summary: List[Dict[str, Any]]
    processing_time: float
    monitoring_timestamp: float


class ChangeImpactAnalysisRequest(BaseModel):
    """Input for change impact analysis operations."""
    document_id: str
    document_data: Dict[str, Any]
    change_description: Dict[str, Any]
    related_documents: Optional[List[Dict[str, Any]]] = None

    @field_validator('document_id')
    @classmethod
    def validate_document_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Document ID cannot be empty')
        if len(v) > 500:
            raise ValueError('Document ID too long (max 500 characters)')
        return v.strip()

    @field_validator('document_data')
    @classmethod
    def validate_document_data(cls, v):
        if not v:
            raise ValueError('Document data cannot be empty')
        required_keys = ['content']  # At minimum, content is required
        if not any(key in v for key in required_keys):
            raise ValueError('Document data must contain at least content or metadata')
        return v

    @field_validator('change_description')
    @classmethod
    def validate_change_description(cls, v):
        if not v:
            raise ValueError('Change description cannot be empty')
        required_keys = ['change_type']  # At minimum, change type is required
        if not any(key in v for key in required_keys):
            raise ValueError('Change description must contain at least change_type')
        return v


class PortfolioChangeImpactRequest(BaseModel):
    """Input for portfolio change impact analysis operations."""
    changes: List[Dict[str, Any]]
    document_portfolio: List[Dict[str, Any]]

    @field_validator('changes')
    @classmethod
    def validate_changes(cls, v):
        if not v:
            raise ValueError('Changes list cannot be empty')
        if len(v) > 100:
            raise ValueError('Too many changes (max 100)')
        return v

    @field_validator('document_portfolio')
    @classmethod
    def validate_document_portfolio(cls, v):
        if not v:
            raise ValueError('Document portfolio cannot be empty')
        if len(v) > 1000:
            raise ValueError('Portfolio too large (max 1000 documents)')
        return v


class ChangeImpactAnalysisResponse(BaseModel):
    """Response model for change impact analysis."""
    document_id: str
    change_description: Dict[str, Any]
    document_features: Dict[str, Any]
    impact_analysis: Dict[str, Any]
    related_documents_analysis: Dict[str, Any]
    recommendations: List[str]
    processing_time: float
    analysis_timestamp: float


class PortfolioChangeImpactResponse(BaseModel):
    """Response model for portfolio change impact analysis."""
    portfolio_summary: Dict[str, Any]
    change_impacts: List[Dict[str, Any]]
    processing_time: float
    analysis_timestamp: float


class AutomatedRemediationRequest(BaseModel):
    """Request model for automated remediation."""
    content: str
    issues: Optional[List[Dict[str, Any]]] = None
    doc_type: str = "general"
    metadata: Optional[Dict[str, Any]] = None
    confidence_level: str = "medium"
    preview_only: bool = False

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()

    @field_validator('doc_type')
    @classmethod
    def validate_doc_type(cls, v):
        valid_types = ['general', 'api_reference', 'user_guide', 'tutorial',
                      'architecture', 'troubleshooting', 'security', 'technical_spec']
        if v not in valid_types:
            raise ValueError(f'Document type must be one of: {valid_types}')
        return v

    @field_validator('confidence_level')
    @classmethod
    def validate_confidence_level(cls, v):
        valid_levels = ['high', 'medium', 'low', 'suggestion_only']
        if v not in valid_levels:
            raise ValueError(f'Confidence level must be one of: {valid_levels}')
        return v


class RemediationPreviewRequest(BaseModel):
    """Request model for remediation preview."""
    content: str
    issues: Optional[List[Dict[str, Any]]] = None
    doc_type: str = "general"
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()

    @field_validator('doc_type')
    @classmethod
    def validate_doc_type(cls, v):
        valid_types = ['general', 'api_reference', 'user_guide', 'tutorial',
                      'architecture', 'troubleshooting', 'security', 'technical_spec']
        if v not in valid_types:
            raise ValueError(f'Document type must be one of: {valid_types}')
        return v


class AutomatedRemediationResponse(BaseModel):
    """Response model for automated remediation."""
    original_content: str
    remediated_content: str
    backup: Optional[Dict[str, Any]]
    report: Dict[str, Any]
    changes_applied: int
    safety_status: str
    processing_time: float
    remediation_timestamp: float


class RemediationPreviewResponse(BaseModel):
    """Response model for remediation preview."""
    preview_available: bool
    proposed_fixes: List[str]
    fix_count: int
    estimated_processing_time: float
    preview_timestamp: float


class WorkflowEventRequest(BaseModel):
    """Request model for workflow event processing."""
    event_type: str
    action: str
    repository: Optional[str] = None
    branch: Optional[str] = None
    base_branch: Optional[str] = None
    commit_sha: Optional[str] = None
    pr_number: Optional[int] = None
    author: Optional[str] = None
    files_changed: Optional[List[str]] = None
    files_added: Optional[List[str]] = None
    files_modified: Optional[List[str]] = None
    files_deleted: Optional[List[str]] = None
    lines_changed: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    labels: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        valid_types = ['pull_request', 'push', 'release', 'issue',
                      'deployment', 'documentation_update', 'merge', 'tag']
        if v not in valid_types:
            raise ValueError(f'Event type must be one of: {valid_types}')
        return v

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        valid_actions = ['opened', 'closed', 'merged', 'synchronize',
                        'push', 'published', 'updated', 'deleted',
                        'started', 'completed', 'failed', 'created', 'edited']
        if v not in valid_actions:
            raise ValueError(f'Action must be one of: {valid_actions}')
        return v


class WorkflowEventResponse(BaseModel):
    """Response model for workflow event processing."""
    workflow_id: str
    status: str
    priority: str
    analysis_types: List[str]
    estimated_processing_time: float
    processing_time: float
    event_type: str
    event_action: str


class WorkflowStatusRequest(BaseModel):
    """Request model for workflow status check."""
    workflow_id: str

    @field_validator('workflow_id')
    @classmethod
    def validate_workflow_id(cls, v):
        if not v or not v.startswith('wf_'):
            raise ValueError('Invalid workflow ID format')
        return v


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    workflow_id: str
    status: str
    priority: str
    created_at: float
    processed_at: Optional[float]
    completed_at: Optional[float]
    analysis_plan: Optional[Dict[str, Any]]
    results: Optional[Dict[str, Any]]
    error: Optional[str]


class WorkflowQueueStatusResponse(BaseModel):
    """Response model for workflow queue status."""
    queues: Dict[str, int]
    total_queued: int
    active_workflows: int
    recent_events: List[Dict[str, Any]]


class WebhookConfigRequest(BaseModel):
    """Request model for webhook configuration."""
    secret: str
    enabled_events: Optional[List[str]] = None

    @field_validator('secret')
    @classmethod
    def validate_secret(cls, v):
        if len(v) < 16:
            raise ValueError('Webhook secret must be at least 16 characters')
        return v

    @field_validator('enabled_events')
    @classmethod
    def validate_enabled_events(cls, v):
        if v:
            valid_events = ['pull_request', 'push', 'release', 'issue',
                          'deployment', 'documentation_update']
            invalid_events = [event for event in v if event not in valid_events]
            if invalid_events:
                raise ValueError(f'Invalid events: {invalid_events}')
        return v


class WebhookConfigResponse(BaseModel):
    """Response model for webhook configuration."""
    configured: bool
    enabled_events: List[str]
    webhook_url: Optional[str]


class CrossRepositoryAnalysisRequest(BaseModel):
    """Request model for cross-repository analysis."""
    repositories: List[Dict[str, Any]]
    analysis_types: Optional[List[str]] = None
    include_connectivity_analysis: bool = True
    max_repositories: int = 50

    @field_validator('repositories')
    @classmethod
    def validate_repositories(cls, v):
        if not v:
            raise ValueError('Repositories list cannot be empty')
        if len(v) > 50:
            raise ValueError('Too many repositories (max 50)')
        for i, repo in enumerate(v):
            if 'repository_id' not in repo:
                raise ValueError(f'Repository {i} missing repository_id field')
        return v

    @field_validator('analysis_types')
    @classmethod
    def validate_analysis_types(cls, v):
        if v:
            valid_types = ['consistency_analysis', 'coverage_analysis', 'quality_analysis',
                          'redundancy_analysis', 'dependency_analysis']
            invalid_types = [analysis_type for analysis_type in v if analysis_type not in valid_types]
            if invalid_types:
                raise ValueError(f'Invalid analysis types: {invalid_types}')
        return v


class RepositoryConnectivityRequest(BaseModel):
    """Request model for repository connectivity analysis."""
    repositories: List[Dict[str, Any]]

    @field_validator('repositories')
    @classmethod
    def validate_repositories(cls, v):
        if not v:
            raise ValueError('Repositories list cannot be empty')
        if len(v) > 20:
            raise ValueError('Too many repositories for connectivity analysis (max 20)')
        for i, repo in enumerate(v):
            if 'repository_id' not in repo:
                raise ValueError(f'Repository {i} missing repository_id field')
        return v


class RepositoryConnectorConfigRequest(BaseModel):
    """Request model for repository connector configuration."""
    connector_type: str
    config: Dict[str, Any]

    @field_validator('connector_type')
    @classmethod
    def validate_connector_type(cls, v):
        valid_types = ['github', 'gitlab', 'bitbucket', 'azure_devops', 'filesystem']
        if v not in valid_types:
            raise ValueError(f'Connector type must be one of: {valid_types}')
        return v

    @field_validator('config')
    @classmethod
    def validate_config(cls, v):
        required_fields = ['base_url']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Config missing required field: {field}')
        return v


class CrossRepositoryAnalysisResponse(BaseModel):
    """Response model for cross-repository analysis."""
    repository_count: int
    repositories_analyzed: List[Dict[str, Any]]
    analysis_types: List[str]
    consistency_analysis: Dict[str, Any]
    coverage_analysis: Dict[str, Any]
    quality_analysis: Dict[str, Any]
    redundancy_analysis: Dict[str, Any]
    dependency_analysis: Dict[str, Any]
    overall_score: float
    recommendations: List[Dict[str, Any]]
    processing_time: float
    analysis_timestamp: float


class RepositoryConnectivityResponse(BaseModel):
    """Response model for repository connectivity analysis."""
    repository_count: int
    cross_references: List[Dict[str, Any]]
    shared_dependencies: List[Dict[str, Any]]
    integration_points: List[Dict[str, Any]]
    connectivity_score: float
    processing_time: float


class RepositoryConnectorConfigResponse(BaseModel):
    """Response model for repository connector configuration."""
    connector_type: str
    configured: bool
    supported_features: List[str]
    rate_limits: Dict[str, Any]


class SupportedConnectorsResponse(BaseModel):
    """Response model for supported repository connectors."""
    connectors: Dict[str, Dict[str, Any]]
    total_supported: int


class AnalysisFrameworksResponse(BaseModel):
    """Response model for analysis frameworks."""
    frameworks: Dict[str, Dict[str, Any]]
    total_frameworks: int


class DistributedTaskRequest(BaseModel):
    """Request model for submitting a distributed task."""
    task_type: str
    data: Dict[str, Any]
    priority: Optional[str] = "normal"
    dependencies: Optional[List[str]] = None

    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v):
        valid_types = ['semantic_similarity', 'sentiment_analysis', 'content_quality',
                      'trend_analysis', 'risk_assessment', 'cross_repository',
                      'batch_analysis', 'data_processing']
        if v not in valid_types:
            raise ValueError(f'Task type must be one of: {valid_types}')
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v:
            valid_priorities = ['low', 'normal', 'high', 'critical']
            if v not in valid_priorities:
                raise ValueError(f'Priority must be one of: {valid_priorities}')
        return v


class BatchTasksRequest(BaseModel):
    """Request model for submitting multiple distributed tasks."""
    tasks: List[Dict[str, Any]]

    @field_validator('tasks')
    @classmethod
    def validate_tasks(cls, v):
        if not v:
            raise ValueError('Tasks list cannot be empty')
        if len(v) > 100:
            raise ValueError('Too many tasks (max 100)')
        for i, task in enumerate(v):
            if 'task_type' not in task:
                raise ValueError(f'Task {i} missing task_type field')
            if 'data' not in task:
                raise ValueError(f'Task {i} missing data field')
        return v


class TaskStatusRequest(BaseModel):
    """Request model for getting task status."""
    task_id: str

    @field_validator('task_id')
    @classmethod
    def validate_task_id(cls, v):
        if not v:
            raise ValueError('Task ID cannot be empty')
        return v


class CancelTaskRequest(BaseModel):
    """Request model for cancelling a task."""
    task_id: str

    @field_validator('task_id')
    @classmethod
    def validate_task_id(cls, v):
        if not v:
            raise ValueError('Task ID cannot be empty')
        return v


class ScaleWorkersRequest(BaseModel):
    """Request model for scaling workers."""
    target_count: int

    @field_validator('target_count')
    @classmethod
    def validate_target_count(cls, v):
        if v < 1:
            raise ValueError('Target count must be at least 1')
        if v > 100:
            raise ValueError('Target count cannot exceed 100')
        return v


class DistributedTaskResponse(BaseModel):
    """Response model for distributed task submission."""
    task_id: str
    task_type: str
    status: str
    priority: str
    submitted_at: str
    estimated_completion: Optional[str] = None


class BatchTasksResponse(BaseModel):
    """Response model for batch task submission."""
    task_ids: List[str]
    total_tasks: int
    submitted_at: str


class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    task_type: str
    status: str
    priority: str
    progress: float
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    assigned_worker: Optional[str] = None
    error_message: Optional[str] = None
    estimated_completion: Optional[str] = None
    retry_count: int = 0


class WorkersStatusResponse(BaseModel):
    """Response model for workers status."""
    workers: Dict[str, Dict[str, Any]]
    total_workers: int
    available_workers: int
    busy_workers: int


class ProcessingStatsResponse(BaseModel):
    """Response model for processing statistics."""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    active_workers: int
    avg_processing_time: float
    throughput_per_minute: float
    completion_rate: float


class ScaleWorkersResponse(BaseModel):
    """Response model for scaling workers."""
    previous_count: int
    new_count: int
    scaled_at: str


class LoadBalancingStrategyRequest(BaseModel):
    """Request model for setting load balancing strategy."""
    strategy: str

    @field_validator('strategy')
    @classmethod
    def validate_strategy(cls, v):
        valid_strategies = ['round_robin', 'least_loaded', 'weighted_random', 'performance_based', 'adaptive']
        if v not in valid_strategies:
            raise ValueError(f'Strategy must be one of: {valid_strategies}')
        return v


class LoadBalancingStrategyResponse(BaseModel):
    """Response model for load balancing strategy."""
    current_strategy: str
    available_strategies: List[str]
    changed_at: str


class QueueStatusResponse(BaseModel):
    """Response model for queue status."""
    queue_length: int
    priority_distribution: Dict[str, int]
    oldest_task_age: Optional[float]
    queue_efficiency: float
    processing_rate: float


class LoadBalancingConfigRequest(BaseModel):
    """Request model for load balancing configuration."""
    strategy: Optional[str] = None
    worker_count: Optional[int] = None
    max_queue_size: Optional[int] = None
    enable_auto_scaling: Optional[bool] = None

    @field_validator('strategy')
    @classmethod
    def validate_strategy(cls, v):
        if v:
            valid_strategies = ['round_robin', 'least_loaded', 'weighted_random', 'performance_based', 'adaptive']
            if v not in valid_strategies:
                raise ValueError(f'Strategy must be one of: {valid_strategies}')
        return v

    @field_validator('worker_count')
    @classmethod
    def validate_worker_count(cls, v):
        if v and (v < 1 or v > 100):
            raise ValueError('Worker count must be between 1 and 100')
        return v

    @field_validator('max_queue_size')
    @classmethod
    def validate_max_queue_size(cls, v):
        if v and (v < 10 or v > 10000):
            raise ValueError('Max queue size must be between 10 and 10000')
        return v


class LoadBalancingConfigResponse(BaseModel):
    """Response model for load balancing configuration."""
    strategy: str
    worker_count: int
    max_queue_size: Optional[int]
    enable_auto_scaling: bool
    configured_at: str
