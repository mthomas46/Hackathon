"""Orchestrator domain events for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel
from datetime import datetime


class WorkflowStartedEvent(BaseModel):
    """Event fired when a workflow starts."""
    workflow_id: str
    workflow_type: str
    started_at: datetime
    parameters: Optional[Dict[str, Any]] = None


class WorkflowCompletedEvent(BaseModel):
    """Event fired when a workflow completes."""
    workflow_id: str
    execution_id: str
    completed_at: datetime
    final_status: str
    results: Optional[Dict[str, Any]] = None


class WorkflowFailedEvent(BaseModel):
    """Event fired when a workflow fails."""
    workflow_id: str
    execution_id: str
    failed_at: datetime
    error_message: str
    error_code: Optional[str] = None


class ServiceRegisteredEvent(BaseModel):
    """Event fired when a service is registered."""
    service_id: str
    service_type: str
    registered_at: datetime


class ServiceUnregisteredEvent(BaseModel):
    """Event fired when a service is unregistered."""
    service_id: str
    unregistered_at: datetime
