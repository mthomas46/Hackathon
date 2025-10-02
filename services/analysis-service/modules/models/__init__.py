"""Refactored Models - Domain-specific model definitions.

This package contains the refactored model definitions that were extracted from the
original monolithic models.py file (1191+ lines) to improve maintainability,
organization, and separation of concerns.
"""

from .base import (
    BaseModel, SuccessResponse, ErrorResponse,
    ValidationErrorDetail, ErrorDetail
)
from .analysis import (
    AnalysisRequest, ReportRequest, DocumentDumpRequest, NotifyOwnersRequest, FindingsResponse,
    SemanticSimilarityRequest, SemanticSimilarityResponse, SimilarityPair, SimilarityMatrix,
    SentimentAnalysisRequest, SentimentAnalysisResponse,
    ToneAnalysisRequest, ToneAnalysisResponse,
    ContentQualityRequest, ContentQualityResponse,
    QualityBreakdown, Recommendation, ImprovementSuggestion,
    TrendAnalysisRequest, TrendAnalysisResponse,
    PortfolioTrendAnalysisRequest, PortfolioTrendAnalysisResponse,
    SentimentScores, DetailedAnalysis, TrendData, ForecastData,
    ArchitectureAnalysisRequest, ArchitectureAnalysisResponse
)
from .risk import (
    RiskAssessmentRequest, RiskAssessmentResponse,
    PortfolioRiskAssessmentRequest, PortfolioRiskAssessmentResponse
)
from .maintenance import (
    MaintenanceForecastRequest, MaintenanceForecastResponse,
    PortfolioMaintenanceForecastRequest, PortfolioMaintenanceForecastResponse,
    QualityDegradationDetectionRequest, QualityDegradationDetectionResponse,
    PortfolioQualityDegradationRequest, PortfolioQualityDegradationResponse
)
from .impact import (
    ChangeImpactAnalysisRequest, ChangeImpactAnalysisResponse,
    PortfolioChangeImpactRequest, PortfolioChangeImpactResponse
)
from .remediation import (
    AutomatedRemediationRequest, AutomatedRemediationResponse,
    RemediationPreviewRequest, RemediationPreviewResponse
)
from .workflow import (
    WorkflowEventRequest, WorkflowEventResponse,
    WorkflowStatusRequest, WorkflowStatusResponse,
    WorkflowQueueStatusResponse, WebhookConfigRequest, WebhookConfigResponse
)
from .distributed import (
    DistributedTaskRequest, DistributedTaskResponse,
    BatchTasksRequest, BatchTasksResponse,
    TaskStatusRequest, TaskStatusResponse,
    CancelTaskRequest, WorkersStatusResponse,
    ProcessingStatsResponse, ScaleWorkersRequest,
    ScaleWorkersResponse, LoadBalancingStrategyRequest,
    LoadBalancingStrategyResponse, QueueStatusResponse,
    LoadBalancingConfigRequest, LoadBalancingConfigResponse
)
from .repository import (
    CrossRepositoryAnalysisRequest, CrossRepositoryAnalysisResponse,
    RepositoryConnectivityRequest, RepositoryConnectivityResponse,
    RepositoryConnectorConfigRequest, RepositoryConnectorConfigResponse,
    SupportedConnectorsResponse, AnalysisFrameworksResponse
)

__all__ = [
    # Base models
    'BaseModel', 'SuccessResponse', 'ErrorResponse',
    'ValidationErrorDetail', 'ErrorDetail',

    # Analysis models
    'AnalysisRequest', 'ReportRequest', 'DocumentDumpRequest', 'NotifyOwnersRequest', 'FindingsResponse',
    'SemanticSimilarityRequest', 'SemanticSimilarityResponse', 'SimilarityPair', 'SimilarityMatrix',
    'SentimentAnalysisRequest', 'SentimentAnalysisResponse',
    'ToneAnalysisRequest', 'ToneAnalysisResponse',
    'ContentQualityRequest', 'ContentQualityResponse',
    'QualityBreakdown', 'Recommendation', 'ImprovementSuggestion',
    'TrendAnalysisRequest', 'TrendAnalysisResponse',
    'PortfolioTrendAnalysisRequest', 'PortfolioTrendAnalysisResponse',
    'SentimentScores', 'DetailedAnalysis', 'TrendData', 'ForecastData',
    'ArchitectureAnalysisRequest', 'ArchitectureAnalysisResponse',

    # Risk models
    'RiskAssessmentRequest', 'RiskAssessmentResponse',
    'PortfolioRiskAssessmentRequest', 'PortfolioRiskAssessmentResponse',

    # Maintenance models
    'MaintenanceForecastRequest', 'MaintenanceForecastResponse',
    'PortfolioMaintenanceForecastRequest', 'PortfolioMaintenanceForecastResponse',
    'QualityDegradationDetectionRequest', 'QualityDegradationDetectionResponse',
    'PortfolioQualityDegradationRequest', 'PortfolioQualityDegradationResponse',

    # Impact models
    'ChangeImpactAnalysisRequest', 'ChangeImpactAnalysisResponse',
    'PortfolioChangeImpactRequest', 'PortfolioChangeImpactResponse',

    # Remediation models
    'AutomatedRemediationRequest', 'AutomatedRemediationResponse',
    'RemediationPreviewRequest', 'RemediationPreviewResponse',

    # Workflow models
    'WorkflowEventRequest', 'WorkflowEventResponse',
    'WorkflowStatusRequest', 'WorkflowStatusResponse',
    'WorkflowQueueStatusResponse', 'WebhookConfigRequest', 'WebhookConfigResponse',

    # Distributed models
    'DistributedTaskRequest', 'DistributedTaskResponse',
    'BatchTasksRequest', 'BatchTasksResponse',
    'TaskStatusRequest', 'TaskStatusResponse',
    'CancelTaskRequest', 'WorkersStatusResponse',
    'ProcessingStatsResponse', 'ScaleWorkersRequest',
    'ScaleWorkersResponse', 'LoadBalancingStrategyRequest',
    'LoadBalancingStrategyResponse', 'QueueStatusResponse',
    'LoadBalancingConfigRequest', 'LoadBalancingConfigResponse',

    # Repository models
    'CrossRepositoryAnalysisRequest', 'CrossRepositoryAnalysisResponse',
    'RepositoryConnectivityRequest', 'RepositoryConnectivityResponse',
    'RepositoryConnectorConfigRequest', 'RepositoryConnectorConfigResponse',
    'SupportedConnectorsResponse', 'AnalysisFrameworksResponse'
]
