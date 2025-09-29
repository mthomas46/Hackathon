"""DTOs for Workflow Management API"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, List
from datetime import datetime


class CreateWorkflowRequest(BaseModel):
    """Request to create a new workflow."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    workflow_type: str = Field(..., min_length=1, max_length=100)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Workflow name cannot be empty')
        return v.strip()

    @field_validator('workflow_type')
    @classmethod
    def validate_workflow_type(cls, v):
        if not v.strip():
            raise ValueError('Workflow type cannot be empty')
        return v.strip()


class ExecuteWorkflowRequest(BaseModel):
    """Request to execute a workflow."""

    workflow_id: str = Field(..., min_length=1, max_length=255)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = Field(None, max_length=255)
    correlation_id: Optional[str] = Field(None, max_length=255)
    priority: int = Field(5, ge=1, le=10)  # Priority 1-10

    @field_validator('workflow_id')
    @classmethod
    def validate_workflow_id(cls, v):
        if not v.strip():
            raise ValueError('Workflow ID cannot be empty')
        return v.strip()

    @field_validator('correlation_id')
    @classmethod
    def validate_correlation_id(cls, v):
        if v and len(v) > 255:
            raise ValueError('Correlation ID too long (max 255 characters)')
        return v


class GetWorkflowRequest(BaseModel):
    """Request to get a workflow."""

    workflow_id: str = Field(..., min_length=1, max_length=255)

    @field_validator('workflow_id')
    @classmethod
    def validate_workflow_id(cls, v):
        if not v.strip():
            raise ValueError('Workflow ID cannot be empty')
        return v.strip()


class ListWorkflowsRequest(BaseModel):
    """Request to list workflows."""

    workflow_type: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = Field(None)
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class WorkflowResponse(BaseModel):
    """Response containing workflow information."""

    workflow_id: str
    name: str
    description: Optional[str]
    workflow_type: str
    status: str
    parameters: Dict[str, Any]
    actions: List[Dict[str, Any]]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowExecutionResponse(BaseModel):
    """Response containing workflow execution information."""

    execution_id: str
    workflow_id: str
    status: str
    parameters: Dict[str, Any]
    results: Dict[str, Any]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """Response containing list of workflows."""

    workflows: List[WorkflowResponse]
    total: int
    limit: int
    offset: int


class ExecutionListResponse(BaseModel):
    """Response containing list of executions."""

    executions: List[WorkflowExecutionResponse]
    total: int
    limit: int
    offset: int


class WorkflowHistoryRequest(BaseModel):
    """Request for workflow history."""
    workflow_id: Optional[str] = Field(None, max_length=255)
    limit: int = Field(50, ge=1, le=1000)
    status_filter: Optional[str] = Field(None, max_length=50)


class WorkflowHistoryEntryResponse(BaseModel):
    """Response containing workflow execution history entry."""
    workflow_id: str
    execution_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    steps_executed: int
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class WorkflowHistoryResponse(BaseModel):
    """Response containing workflow execution history."""
    entries: List[WorkflowHistoryEntryResponse]
    total: int
    limit: int

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
