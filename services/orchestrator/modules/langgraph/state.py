"""Workflow state management for LangGraph integration.

This module defines the state structures and management for LangGraph workflows
integrated with the orchestrator service.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from services.shared.utilities import utc_now, generate_id


class WorkflowMetadata(BaseModel):
    """Metadata for workflow execution."""
    workflow_id: str = Field(default_factory=generate_id)
    workflow_type: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    user_id: Optional[str] = None
    correlation_id: str = Field(default_factory=generate_id)
    tags: List[str] = Field(default_factory=list)


class ServiceExecution(BaseModel):
    """Execution details for a service call."""
    service_name: str
    service_endpoint: str
    method: str = "POST"
    request_data: Dict[str, Any] = Field(default_factory=dict)
    response_data: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None
    execution_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)


class WorkflowState(BaseModel):
    """Complete state for LangGraph workflow execution."""
    metadata: WorkflowMetadata

    # Input/Output data
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)

    # Execution tracking
    current_step: str = "initialized"
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)
    service_executions: List[ServiceExecution] = Field(default_factory=list)

    # Error handling
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3

    # Service health and registry
    service_health: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    available_services: List[str] = Field(default_factory=list)

    # Context and memory
    workflow_context: Dict[str, Any] = Field(default_factory=dict)
    shared_memory: Dict[str, Any] = Field(default_factory=dict)

    # Logging and monitoring
    log_entries: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    def add_service_execution(self, execution: ServiceExecution):
        """Add a service execution to the history."""
        self.service_executions.append(execution)
        self.execution_history.append({
            "type": "service_execution",
            "service": execution.service_name,
            "success": execution.success,
            "timestamp": execution.timestamp,
            "execution_time": execution.execution_time
        })

    def add_error(self, error: Dict[str, Any]):
        """Add an error to the workflow state."""
        error_entry = {
            "timestamp": utc_now(),
            "step": self.current_step,
            **error
        }
        self.errors.append(error_entry)
        self.log_entries.append({
            "level": "ERROR",
            "message": error.get("message", "Unknown error"),
            "data": error_entry,
            "timestamp": utc_now()
        })

    def add_log_entry(self, level: str, message: str, data: Optional[Dict] = None):
        """Add a log entry to the workflow."""
        self.log_entries.append({
            "level": level,
            "message": message,
            "data": data or {},
            "timestamp": utc_now()
        })

    def update_metrics(self, metrics: Dict[str, Any]):
        """Update workflow metrics."""
        self.metrics.update(metrics)
        self.metadata.updated_at = utc_now()

    def is_healthy(self) -> bool:
        """Check if the workflow is in a healthy state."""
        return len(self.errors) == 0 or self.retry_count < self.max_retries

    def can_retry(self) -> bool:
        """Check if the workflow can be retried."""
        return self.retry_count < self.max_retries

    def increment_retry(self):
        """Increment the retry count."""
        self.retry_count += 1
        self.add_log_entry(
            "INFO",
            f"Retry attempt {self.retry_count}/{self.max_retries}",
            {"retry_count": self.retry_count}
        )


def create_workflow_state(
    workflow_type: str,
    input_data: Dict[str, Any],
    user_id: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> WorkflowState:
    """Create a new workflow state instance."""

    metadata = WorkflowMetadata(
        workflow_type=workflow_type,
        user_id=user_id,
        tags=tags or []
    )

    return WorkflowState(
        metadata=metadata,
        input_data=input_data,
        current_step="created"
    )
