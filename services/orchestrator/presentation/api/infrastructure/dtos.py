"""DTOs for Infrastructure API"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class DLQRetryRequest(BaseModel):
    """Request for DLQ retry operations."""
    event_ids: List[str] = Field(..., min_items=1)
    max_retries: Optional[int] = Field(3, ge=1, le=10)


class EventReplayRequest(BaseModel):
    """Request for event replay."""
    from_timestamp: Optional[str] = None
    to_timestamp: Optional[str] = None
    event_types: Optional[List[str]] = None
    service_filter: Optional[str] = None


class EventClearRequest(BaseModel):
    """Request for clearing events."""
    before_timestamp: str
    event_types: Optional[List[str]] = None


class DLQStatsResponse(BaseModel):
    """Response containing DLQ statistics."""
    total_events: int
    failed_events: int
    retryable_events: int
    oldest_event: Optional[str] = None
    newest_event: Optional[str] = None

    class Config:
        from_attributes = True


class SagaStatsResponse(BaseModel):
    """Response containing saga statistics."""
    total_sagas: int
    active_sagas: int
    completed_sagas: int
    failed_sagas: int
    avg_completion_time: Optional[float] = None

    class Config:
        from_attributes = True


class SagaDetailResponse(BaseModel):
    """Response containing detailed saga information."""
    saga_id: str
    status: str
    steps: List[Dict[str, Any]]
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class EventHistoryResponse(BaseModel):
    """Response containing event history."""
    events: List[Dict[str, Any]]
    total_count: int
    filtered_count: int

    class Config:
        from_attributes = True


class TracingStatsResponse(BaseModel):
    """Response containing tracing statistics."""
    total_traces: int
    active_traces: int
    avg_trace_duration: Optional[float] = None
    error_rate: float = 0.0

    class Config:
        from_attributes = True


class TraceDetailResponse(BaseModel):
    """Response containing detailed trace information."""
    trace_id: str
    service_name: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    status: str
    spans: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class PeerInfoResponse(BaseModel):
    """Response containing peer orchestrator information."""
    peer_id: str
    peer_url: str
    status: str
    last_contact: str
    capabilities: List[str]

    class Config:
        from_attributes = True
