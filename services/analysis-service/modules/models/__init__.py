"""Refactored Models - Domain-specific model definitions.

This package contains the refactored model definitions that were extracted from the
original monolithic models.py file (1191+ lines) to improve maintainability,
organization, and separation of concerns.
"""

from .analysis import (
    AnalysisRequest,
    ContentQualityRequest,
    ContentQualityResponse,
    FindingsResponse,
    NotifyOwnersRequest,
    PortfolioTrendAnalysisRequest,
    PortfolioTrendAnalysisResponse,
    ReportRequest,
    SemanticSimilarityRequest,
    SemanticSimilarityResponse,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse,
    ToneAnalysisRequest,
    ToneAnalysisResponse,
    TrendAnalysisRequest,
    TrendAnalysisResponse,
)
from .base import (
    BaseModel,
    ErrorDetail,
    ErrorResponse,
    SuccessResponse,
    ValidationErrorDetail,
)
from .distributed import (
    BatchTasksRequest,
    BatchTasksResponse,
    CancelTaskRequest,
    DistributedTaskRequest,
    DistributedTaskResponse,
    LoadBalancingConfigRequest,
    LoadBalancingConfigResponse,
    LoadBalancingStrategyRequest,
    LoadBalancingStrategyResponse,
    ProcessingStatsResponse,
    QueueStatusResponse,
    ScaleWorkersRequest,
    ScaleWorkersResponse,
    TaskStatusRequest,
    TaskStatusResponse,
    WorkersStatusResponse,
)
from .impact import (
    ChangeImpactAnalysisRequest,
    ChangeImpactAnalysisResponse,
    PortfolioChangeImpactRequest,
    PortfolioChangeImpactResponse,
)
from .maintenance import (
    MaintenanceForecastRequest,
    MaintenanceForecastResponse,
    PortfolioMaintenanceForecastRequest,
    PortfolioMaintenanceForecastResponse,
    PortfolioQualityDegradationRequest,
    PortfolioQualityDegradationResponse,
    QualityDegradationDetectionRequest,
    QualityDegradationDetectionResponse,
)
from .remediation import (
    AutomatedRemediationRequest,
    AutomatedRemediationResponse,
    RemediationPreviewRequest,
    RemediationPreviewResponse,
)
from .repository import (
    AnalysisFrameworksResponse,
    CrossRepositoryAnalysisRequest,
    CrossRepositoryAnalysisResponse,
    RepositoryConnectivityRequest,
    RepositoryConnectivityResponse,
    RepositoryConnectorConfigRequest,
    RepositoryConnectorConfigResponse,
    SupportedConnectorsResponse,
)
from .risk import (
    PortfolioRiskAssessmentRequest,
    PortfolioRiskAssessmentResponse,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
)
from .workflow import (
    WebhookConfigRequest,
    WebhookConfigResponse,
    WorkflowEventRequest,
    WorkflowEventResponse,
    WorkflowQueueStatusResponse,
    WorkflowStatusRequest,
    WorkflowStatusResponse,
)

__all__ = [
    # Base models
    "BaseModel",
    "SuccessResponse",
    "ErrorResponse",
    "ValidationErrorDetail",
    "ErrorDetail",
    # Analysis models
    "AnalysisRequest",
    "ReportRequest",
    "NotifyOwnersRequest",
    "FindingsResponse",
    "SemanticSimilarityRequest",
    "SemanticSimilarityResponse",
    "SentimentAnalysisRequest",
    "SentimentAnalysisResponse",
    "ToneAnalysisRequest",
    "ToneAnalysisResponse",
    "ContentQualityRequest",
    "ContentQualityResponse",
    "TrendAnalysisRequest",
    "TrendAnalysisResponse",
    "PortfolioTrendAnalysisRequest",
    "PortfolioTrendAnalysisResponse",
    # Risk models
    "RiskAssessmentRequest",
    "RiskAssessmentResponse",
    "PortfolioRiskAssessmentRequest",
    "PortfolioRiskAssessmentResponse",
    # Maintenance models
    "MaintenanceForecastRequest",
    "MaintenanceForecastResponse",
    "PortfolioMaintenanceForecastRequest",
    "PortfolioMaintenanceForecastResponse",
    "QualityDegradationDetectionRequest",
    "QualityDegradationDetectionResponse",
    "PortfolioQualityDegradationRequest",
    "PortfolioQualityDegradationResponse",
    # Impact models
    "ChangeImpactAnalysisRequest",
    "ChangeImpactAnalysisResponse",
    "PortfolioChangeImpactRequest",
    "PortfolioChangeImpactResponse",
    # Remediation models
    "AutomatedRemediationRequest",
    "AutomatedRemediationResponse",
    "RemediationPreviewRequest",
    "RemediationPreviewResponse",
    # Workflow models
    "WorkflowEventRequest",
    "WorkflowEventResponse",
    "WorkflowStatusRequest",
    "WorkflowStatusResponse",
    "WorkflowQueueStatusResponse",
    "WebhookConfigRequest",
    "WebhookConfigResponse",
    # Distributed models
    "DistributedTaskRequest",
    "DistributedTaskResponse",
    "BatchTasksRequest",
    "BatchTasksResponse",
    "TaskStatusRequest",
    "TaskStatusResponse",
    "CancelTaskRequest",
    "WorkersStatusResponse",
    "ProcessingStatsResponse",
    "ScaleWorkersRequest",
    "ScaleWorkersResponse",
    "LoadBalancingStrategyRequest",
    "LoadBalancingStrategyResponse",
    "QueueStatusResponse",
    "LoadBalancingConfigRequest",
    "LoadBalancingConfigResponse",
    # Repository models
    "CrossRepositoryAnalysisRequest",
    "CrossRepositoryAnalysisResponse",
    "RepositoryConnectivityRequest",
    "RepositoryConnectivityResponse",
    "RepositoryConnectorConfigRequest",
    "RepositoryConnectorConfigResponse",
    "SupportedConnectorsResponse",
    "AnalysisFrameworksResponse",
]
