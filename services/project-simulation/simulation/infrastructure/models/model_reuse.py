"""Model Reuse Strategy - Centralized Pydantic Model Reuse from Ecosystem Services.

This module implements a comprehensive strategy for reusing existing Pydantic models
from the LLM Documentation Ecosystem, following DRY principles and maximizing code reuse.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Type
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

# Import shared models and utilities
try:
    from shared.models.base import BaseResponse, BaseRequest, PaginationParams
    from shared.models.health import HealthStatus, HealthCheck
    from shared.models.monitoring import MetricData, PerformanceMetrics
    from shared.models.responses import StandardResponse, ErrorResponse
except ImportError:
    # Fallback definitions if shared models not available
    class BaseResponse(BaseModel):
        success: bool = Field(default=True, description="Operation success status")
        message: Optional[str] = Field(default=None, description="Response message")
        timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

    class BaseRequest(BaseModel):
        pass

    class PaginationParams(BaseModel):
        page: int = Field(default=1, ge=1, description="Page number")
        page_size: int = Field(default=50, ge=1, le=1000, description="Items per page")
        sort_by: Optional[str] = Field(default=None, description="Sort field")
        sort_order: str = Field(default="asc", regex="^(asc|desc)$", description="Sort order")

    class HealthStatus(str, Enum):
        HEALTHY = "healthy"
        DEGRADED = "degraded"
        UNHEALTHY = "unhealthy"

    class HealthCheck(BaseModel):
        status: HealthStatus = Field(description="Health status")
        timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
        checks: Dict[str, Any] = Field(default_factory=dict, description="Individual health checks")

    class MetricData(BaseModel):
        name: str = Field(description="Metric name")
        value: Union[int, float] = Field(description="Metric value")
        timestamp: datetime = Field(default_factory=datetime.now, description="Metric timestamp")
        tags: Dict[str, str] = Field(default_factory=dict, description="Metric tags")

    class PerformanceMetrics(BaseModel):
        response_time_ms: float = Field(description="Response time in milliseconds")
        throughput: float = Field(description="Requests per second")
        error_rate: float = Field(description="Error rate percentage")
        memory_usage_mb: float = Field(description="Memory usage in MB")

    class StandardResponse(BaseResponse):
        data: Optional[Any] = Field(default=None, description="Response data")

    class ErrorResponse(BaseResponse):
        success: bool = Field(default=False, description="Always false for errors")
        error_code: str = Field(description="Error code")
        details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")


# Ecosystem Service Model Imports (with fallbacks)
try:
    # Doc Store models
    from services.doc_store.models import Document, DocumentMetadata
except ImportError:
    class Document(BaseModel):
        id: str = Field(description="Document ID")
        title: str = Field(description="Document title")
        content: str = Field(description="Document content")
        metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")

    class DocumentMetadata(BaseModel):
        author: Optional[str] = Field(default=None, description="Document author")
        created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
        updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
        tags: List[str] = Field(default_factory=list, description="Document tags")

try:
    # Analysis Service models
    from services.analysis_service.models import AnalysisResult, QualityMetrics
except ImportError:
    class AnalysisResult(BaseModel):
        document_id: str = Field(description="Analyzed document ID")
        score: float = Field(description="Analysis score")
        insights: List[str] = Field(default_factory=list, description="Analysis insights")
        recommendations: List[str] = Field(default_factory=list, description="Recommendations")

    class QualityMetrics(BaseModel):
        readability_score: float = Field(description="Readability score")
        coherence_score: float = Field(description="Coherence score")
        relevance_score: float = Field(description="Relevance score")

try:
    # LLM Gateway models
    from services.llm_gateway.models import GenerationRequest, GenerationResponse
except ImportError:
    class GenerationRequest(BaseModel):
        prompt: str = Field(description="Generation prompt")
        model: str = Field(default="gpt-4", description="Model to use")
        temperature: float = Field(default=0.7, ge=0, le=2, description="Generation temperature")
        max_tokens: int = Field(default=1000, ge=1, description="Maximum tokens")

    class GenerationResponse(BaseModel):
        content: str = Field(description="Generated content")
        model: str = Field(description="Model used")
        tokens_used: int = Field(description="Tokens consumed")
        finish_reason: str = Field(description="Generation finish reason")

try:
    # Orchestrator models
    from services.orchestrator.models import WorkflowDefinition, WorkflowExecution
except ImportError:
    class WorkflowDefinition(BaseModel):
        id: str = Field(description="Workflow definition ID")
        name: str = Field(description="Workflow name")
        steps: List[Dict[str, Any]] = Field(description="Workflow steps")
        triggers: List[str] = Field(default_factory=list, description="Workflow triggers")

    class WorkflowExecution(BaseModel):
        workflow_id: str = Field(description="Workflow definition ID")
        execution_id: str = Field(description="Execution ID")
        status: str = Field(description="Execution status")
        results: Dict[str, Any] = Field(default_factory=dict, description="Execution results")


# Simulation-Specific Models (extending ecosystem models)

class SimulationBaseRequest(BaseRequest):
    """Base request model for simulation operations."""
    simulation_id: Optional[str] = Field(default=None, description="Simulation ID for context")
    correlation_id: Optional[str] = Field(default=None, description="Request correlation ID")
    user_id: Optional[str] = Field(default=None, description="Requesting user ID")

    @validator('correlation_id', always=True)
    def generate_correlation_id(cls, v):
        return v or f"sim-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(datetime.now()) % 10000:04d}"


class SimulationBaseResponse(StandardResponse):
    """Base response model for simulation operations."""
    simulation_id: Optional[str] = Field(default=None, description="Simulation ID")
    request_id: Optional[str] = Field(default=None, description="Request ID for correlation")
    processing_time_ms: Optional[float] = Field(default=None, description="Processing time")


class SimulationHealthCheck(HealthCheck):
    """Enhanced health check for simulation service."""
    service_status: Dict[str, HealthStatus] = Field(default_factory=dict, description="Individual service health")
    ecosystem_connectivity: Dict[str, bool] = Field(default_factory=dict, description="Ecosystem service connectivity")
    active_simulations: int = Field(default=0, description="Number of active simulations")
    queue_depth: int = Field(default=0, description="Queued simulation requests")


class SimulationMetrics(PerformanceMetrics):
    """Enhanced performance metrics for simulation service."""
    active_simulations: int = Field(default=0, description="Currently active simulations")
    completed_simulations: int = Field(default=0, description="Total completed simulations")
    average_simulation_duration: float = Field(default=0.0, description="Average simulation duration in seconds")
    simulation_success_rate: float = Field(default=0.0, description="Simulation success rate percentage")
    ecosystem_service_calls: int = Field(default=0, description="Total ecosystem service calls")
    average_service_response_time: float = Field(default=0.0, description="Average ecosystem service response time")


class ProjectDocument(Document):
    """Project document model extending ecosystem Document."""
    project_id: str = Field(description="Associated project ID")
    simulation_id: str = Field(description="Associated simulation ID")
    document_type: str = Field(description="Type of project document")
    phase: Optional[str] = Field(default=None, description="Project phase this document belongs to")
    quality_score: Optional[float] = Field(default=None, description="Document quality score")
    generation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Document generation metadata")

    @validator('quality_score')
    def validate_quality_score(cls, v):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError('Quality score must be between 0.0 and 1.0')
        return v


class SimulationAnalysisResult(AnalysisResult):
    """Simulation-specific analysis result extending ecosystem AnalysisResult."""
    simulation_context: Dict[str, Any] = Field(default_factory=dict, description="Simulation context")
    project_phase: Optional[str] = Field(default=None, description="Project phase context")
    team_impact: Dict[str, Any] = Field(default_factory=dict, description="Team impact analysis")
    timeline_impact: Dict[str, Any] = Field(default_factory=dict, description="Timeline impact analysis")


class SimulationGenerationRequest(GenerationRequest):
    """Simulation-specific generation request extending ecosystem GenerationRequest."""
    simulation_context: Dict[str, Any] = Field(default_factory=dict, description="Simulation context")
    project_type: Optional[str] = Field(default=None, description="Project type context")
    complexity_level: Optional[str] = Field(default=None, description="Complexity level context")
    team_composition: Optional[Dict[str, Any]] = Field(default=None, description="Team composition context")
    timeline_phase: Optional[str] = Field(default=None, description="Timeline phase context")


class SimulationWorkflowDefinition(WorkflowDefinition):
    """Simulation workflow definition extending ecosystem WorkflowDefinition."""
    simulation_type: str = Field(description="Type of simulation workflow")
    project_template: Optional[str] = Field(default=None, description="Project template to use")
    required_services: List[str] = Field(default_factory=list, description="Required ecosystem services")
    estimated_duration: Optional[int] = Field(default=None, description="Estimated duration in seconds")


class SimulationWorkflowExecution(WorkflowExecution):
    """Simulation workflow execution extending ecosystem WorkflowExecution."""
    simulation_id: str = Field(description="Associated simulation ID")
    project_id: str = Field(description="Associated project ID")
    phase_progress: Dict[str, float] = Field(default_factory=dict, description="Progress by phase")
    service_interactions: Dict[str, int] = Field(default_factory=dict, description="Service interaction counts")
    generated_documents: List[str] = Field(default_factory=list, description="Generated document IDs")


# Specialized Simulation Models

class SimulationConfiguration(BaseModel):
    """Simulation configuration model."""
    simulation_id: str = Field(description="Unique simulation identifier")
    project_config: Dict[str, Any] = Field(description="Project configuration")
    team_config: Dict[str, Any] = Field(description="Team configuration")
    timeline_config: Dict[str, Any] = Field(description="Timeline configuration")
    ecosystem_services: List[str] = Field(description="Enabled ecosystem services")
    quality_thresholds: Dict[str, float] = Field(default_factory=dict, description="Quality thresholds")
    performance_targets: Dict[str, Any] = Field(default_factory=dict, description="Performance targets")

    @validator('ecosystem_services')
    def validate_services(cls, v):
        valid_services = {
            'doc_store', 'prompt_store', 'analysis_service', 'llm_gateway',
            'mock_data_generator', 'orchestrator', 'log_collector', 'notification_service'
        }
        invalid_services = set(v) - valid_services
        if invalid_services:
            raise ValueError(f"Invalid ecosystem services: {invalid_services}")
        return v


class SimulationProgress(BaseModel):
    """Simulation progress tracking model."""
    simulation_id: str = Field(description="Simulation ID")
    status: str = Field(description="Current simulation status")
    progress_percentage: float = Field(ge=0, le=100, description="Overall progress percentage")
    current_phase: Optional[str] = Field(default=None, description="Current active phase")
    completed_phases: List[str] = Field(default_factory=list, description="Completed phases")
    pending_phases: List[str] = Field(default_factory=list, description="Pending phases")
    phase_progress: Dict[str, float] = Field(default_factory=dict, description="Progress by phase")
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last progress update")


class SimulationResults(BaseModel):
    """Simulation results model."""
    simulation_id: str = Field(description="Simulation ID")
    project_id: str = Field(description="Project ID")
    status: str = Field(description="Final simulation status")
    completed_at: datetime = Field(default_factory=datetime.now, description="Completion timestamp")
    duration_seconds: float = Field(description="Total simulation duration")
    generated_documents: List[str] = Field(default_factory=list, description="Generated document IDs")
    service_interactions: Dict[str, int] = Field(default_factory=dict, description="Service interaction counts")
    quality_metrics: Dict[str, Any] = Field(default_factory=dict, description="Overall quality metrics")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    insights: List[str] = Field(default_factory=list, description="Simulation insights")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")


class EcosystemServiceStatus(BaseModel):
    """Ecosystem service status model."""
    service_name: str = Field(description="Service name")
    status: HealthStatus = Field(description="Service health status")
    response_time_ms: Optional[float] = Field(default=None, description="Response time")
    last_checked: datetime = Field(default_factory=datetime.now, description="Last health check")
    error_message: Optional[str] = Field(default=None, description="Error message if unhealthy")
    version: Optional[str] = Field(default=None, description="Service version")
    endpoints: Dict[str, HealthStatus] = Field(default_factory=dict, description="Endpoint-specific status")


# Model Registry for Dynamic Loading
MODEL_REGISTRY = {
    # Base Models
    'BaseRequest': SimulationBaseRequest,
    'BaseResponse': SimulationBaseResponse,
    'StandardResponse': SimulationBaseResponse,
    'ErrorResponse': ErrorResponse,
    'PaginationParams': PaginationParams,

    # Health & Monitoring Models
    'HealthCheck': SimulationHealthCheck,
    'HealthStatus': HealthStatus,
    'MetricData': MetricData,
    'PerformanceMetrics': SimulationMetrics,

    # Document Models
    'Document': ProjectDocument,
    'DocumentMetadata': DocumentMetadata,

    # Analysis Models
    'AnalysisResult': SimulationAnalysisResult,
    'QualityMetrics': QualityMetrics,

    # AI Generation Models
    'GenerationRequest': SimulationGenerationRequest,
    'GenerationResponse': GenerationResponse,

    # Workflow Models
    'WorkflowDefinition': SimulationWorkflowDefinition,
    'WorkflowExecution': SimulationWorkflowExecution,

    # Simulation-Specific Models
    'SimulationConfiguration': SimulationConfiguration,
    'SimulationProgress': SimulationProgress,
    'SimulationResults': SimulationResults,
    'EcosystemServiceStatus': EcosystemServiceStatus,
}


def get_model(model_name: str) -> Type[BaseModel]:
    """Get a model class by name from the registry."""
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Model '{model_name}' not found in registry")
    return MODEL_REGISTRY[model_name]


def create_model_instance(model_name: str, **kwargs) -> BaseModel:
    """Create a model instance with the given parameters."""
    model_class = get_model(model_name)
    return model_class(**kwargs)


def validate_model_data(model_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate data against a model and return validated data."""
    model_class = get_model(model_name)
    instance = model_class(**data)
    return instance.dict()


def get_available_models() -> List[str]:
    """Get list of all available model names."""
    return list(MODEL_REGISTRY.keys())


def get_model_schema(model_name: str) -> Dict[str, Any]:
    """Get the JSON schema for a model."""
    model_class = get_model(model_name)
    return model_class.schema()


# Ecosystem Integration Helpers

def create_ecosystem_request(service_name: str, operation: str, **kwargs) -> Dict[str, Any]:
    """Create a standardized request for ecosystem service integration."""
    return {
        "service": service_name,
        "operation": operation,
        "timestamp": datetime.now(),
        "correlation_id": f"eco-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(datetime.now()) % 10000:04d}",
        "parameters": kwargs
    }


def create_simulation_response(success: bool, data: Any = None, message: str = None,
                              simulation_id: str = None) -> SimulationBaseResponse:
    """Create a standardized simulation response."""
    return SimulationBaseResponse(
        success=success,
        data=data,
        message=message,
        simulation_id=simulation_id
    )


# Export all models
__all__ = [
    # Base Models
    'BaseRequest', 'BaseResponse', 'StandardResponse', 'ErrorResponse', 'PaginationParams',

    # Health & Monitoring
    'HealthCheck', 'HealthStatus', 'MetricData', 'PerformanceMetrics', 'SimulationHealthCheck', 'SimulationMetrics',

    # Document Models
    'Document', 'DocumentMetadata', 'ProjectDocument',

    # Analysis Models
    'AnalysisResult', 'QualityMetrics', 'SimulationAnalysisResult',

    # AI Generation Models
    'GenerationRequest', 'GenerationResponse', 'SimulationGenerationRequest',

    # Workflow Models
    'WorkflowDefinition', 'WorkflowExecution', 'SimulationWorkflowDefinition', 'SimulationWorkflowExecution',

    # Simulation Models
    'SimulationBaseRequest', 'SimulationBaseResponse', 'SimulationConfiguration',
    'SimulationProgress', 'SimulationResults', 'EcosystemServiceStatus',

    # Utility Functions
    'get_model', 'create_model_instance', 'validate_model_data',
    'get_available_models', 'get_model_schema',
    'create_ecosystem_request', 'create_simulation_response',

    # Registry
    'MODEL_REGISTRY'
]
