"""Request and response models for Orchestrator service.

Contains all Pydantic models used for API requests and responses.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class WorkflowRunRequest(BaseModel):
    """Request model for running workflows."""
    workflow_id: str
    parameters: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class DemoE2ERequest(BaseModel):
    """Request model for E2E demo."""
    scenario: str = "basic_ingestion"
    parameters: Optional[Dict[str, Any]] = None


class ServiceRegistrationRequest(BaseModel):
    """Request model for service registration."""
    service_name: str
    service_url: str
    capabilities: List[str] = []
    metadata: Optional[Dict[str, Any]] = None


class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    source_url: str
    source_type: str = "github"
    parameters: Optional[Dict[str, Any]] = None


class DLQRetryRequest(BaseModel):
    """Request model for DLQ retry operations."""
    event_ids: List[str]
    max_retries: Optional[int] = 3


class EventReplayRequest(BaseModel):
    """Request model for event replay."""
    from_timestamp: Optional[str] = None
    to_timestamp: Optional[str] = None
    event_types: Optional[List[str]] = None
    service_filter: Optional[str] = None


class EventClearRequest(BaseModel):
    """Request model for clearing events."""
    before_timestamp: str
    event_types: Optional[List[str]] = None


class PollOpenAPIRequest(BaseModel):
    """Request model for polling OpenAPI specs."""
    service_urls: List[str]
    force_refresh: bool = False


class WorkflowHistoryRequest(BaseModel):
    """Request model for workflow history."""
    workflow_id: Optional[str] = None
    limit: int = 50
    status_filter: Optional[str] = None


class JobRecalcQualityRequest(BaseModel):
    """Request model for quality recalculation jobs."""
    target_services: List[str] = []
    force_recalc: bool = False


class NotifyConsolidationRequest(BaseModel):
    """Request model for consolidation notifications."""
    consolidation_id: str
    notification_channels: List[str] = ["email"]
    recipients: Optional[List[str]] = None


class DocStoreSaveRequest(BaseModel):
    """Request model for docstore save operations."""
    documents: List[Dict[str, Any]]
    collection: str = "default"
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str
    services: Dict[str, Dict[str, Any]]
    timestamp: str


class ServiceInfo(BaseModel):
    """Service information model."""
    name: str
    description: str
    category: str
    capabilities: List[str]
    endpoints: List[str]
    status: str = "unknown"
    version: Optional[str] = None


class WorkflowTemplate(BaseModel):
    """Workflow template model."""
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    required_services: List[str]
    estimated_duration: Optional[int] = None


class RegistryEntry(BaseModel):
    """Service registry entry model."""
    service_name: str
    service_url: str
    capabilities: List[str]
    status: str
    last_seen: str
    metadata: Dict[str, Any]


class DLQStats(BaseModel):
    """DLQ statistics model."""
    total_events: int
    failed_events: int
    retryable_events: int
    oldest_event: Optional[str] = None
    newest_event: Optional[str] = None


class SagaStats(BaseModel):
    """Saga statistics model."""
    total_sagas: int
    active_sagas: int
    completed_sagas: int
    failed_sagas: int
    avg_completion_time: Optional[float] = None


class SagaDetail(BaseModel):
    """Detailed saga information."""
    saga_id: str
    status: str
    steps: List[Dict[str, Any]]
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class EventHistory(BaseModel):
    """Event history model."""
    events: List[Dict[str, Any]]
    total_count: int
    filtered_count: int


class TracingStats(BaseModel):
    """Tracing statistics model."""
    total_traces: int
    active_traces: int
    avg_trace_duration: Optional[float] = None
    error_rate: float = 0.0


class TraceDetail(BaseModel):
    """Detailed trace information."""
    trace_id: str
    service_name: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    status: str
    spans: List[Dict[str, Any]]


class PeerInfo(BaseModel):
    """Peer orchestrator information."""
    peer_id: str
    peer_url: str
    status: str
    last_contact: str
    capabilities: List[str]


class WorkflowHistoryEntry(BaseModel):
    """Workflow execution history entry."""
    workflow_id: str
    execution_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    steps_executed: int
    error_message: Optional[str] = None


class QualityRecalcResult(BaseModel):
    """Quality recalculation result."""
    service_name: str
    documents_processed: int
    quality_improvements: int
    errors: List[str]


class ConsolidationNotification(BaseModel):
    """Consolidation notification details."""
    consolidation_id: str
    status: str
    recipients_notified: int
    channels_used: List[str]
    sent_at: str
