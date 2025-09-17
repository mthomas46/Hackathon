"""Workflow Models - Workflow-triggered analysis request and response models."""

from typing import Optional, List, Dict, Any
from pydantic import Field

from .base import BaseModel


class WorkflowEventRequest(BaseModel):
    """Request for workflow event processing."""
    event_type: str = Field(..., description="Type of workflow event")
    event_data: Dict[str, Any] = Field(..., description="Event data payload")
    trigger_conditions: Optional[Dict[str, Any]] = Field(None, description="Trigger conditions")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class WorkflowEventResponse(BaseModel):
    """Response for workflow event processing."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    event_type: str = Field(..., description="Type of event processed")
    triggered_analyses: List[str] = Field(default_factory=list, description="Triggered analysis IDs")
    notifications_sent: int = Field(..., description="Number of notifications sent")
    workflow_status: str = Field(..., description="Workflow processing status")
    execution_time_seconds: float = Field(..., description="Time taken to process event")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")


class WorkflowStatusRequest(BaseModel):
    """Request for workflow status."""
    workflow_id: str = Field(..., description="Workflow ID to check")
    include_history: Optional[bool] = Field(False, description="Include workflow history")


class WorkflowStatusResponse(BaseModel):
    """Response for workflow status."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    workflow_id: str = Field(..., description="Workflow ID")
    status: str = Field(..., description="Workflow status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Workflow progress")
    current_step: str = Field(..., description="Current workflow step")
    steps_completed: List[str] = Field(default_factory=list, description="Completed steps")
    steps_remaining: List[str] = Field(default_factory=list, description="Remaining steps")
    estimated_completion_time_seconds: float = Field(..., description="Estimated completion time")
    error_message: Optional[str] = Field(None, description="Error message if workflow failed")


class WorkflowQueueStatusResponse(BaseModel):
    """Response for workflow queue status."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    queue_length: int = Field(..., description="Current queue length")
    processing_rate_per_minute: float = Field(..., description="Processing rate")
    average_wait_time_seconds: float = Field(..., description="Average wait time")
    priority_distribution: Dict[str, int] = Field(default_factory=dict, description="Priority distribution")
    oldest_item_age_seconds: float = Field(..., description="Age of oldest item")
    error_message: Optional[str] = Field(None, description="Error message if queue check failed")


class WebhookConfigRequest(BaseModel):
    """Request for webhook configuration."""
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to trigger webhook")
    secret: Optional[str] = Field(None, description="Webhook secret")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class WebhookConfigResponse(BaseModel):
    """Response for webhook configuration."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    webhook_id: str = Field(..., description="Webhook ID")
    url: str = Field(..., description="Configured webhook URL")
    events: List[str] = Field(..., description="Configured events")
    secret_configured: bool = Field(..., description="Whether secret is configured")
    status: str = Field(..., description="Configuration status")
    error_message: Optional[str] = Field(None, description="Error message if configuration failed")
