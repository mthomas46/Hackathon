"""Data Transfer Objects for workflow operations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class WorkflowDto(BaseModel):
    """DTO for workflow data."""
    id: str
    workflow_type: str
    status: str
    created_at: datetime
    parameters: Optional[Dict[str, Any]] = None


class WorkflowExecutionDto(BaseModel):
    """DTO for workflow execution data."""
    workflow_id: str
    execution_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None


class ServiceRegistryDto(BaseModel):
    """DTO for service registry data."""
    service_id: str
    service_type: str
    endpoint: str
    capabilities: List[str]
