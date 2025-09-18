"""Application Commands for Workflow Management"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from ...domain.workflow_management import WorkflowId, ExecutionId


@dataclass
class CreateWorkflowCommand:
    """Command to create a new workflow."""
    name: str
    description: str
    created_by: str
    parameters: list[Dict[str, Any]]
    actions: list[Dict[str, Any]]
    tags: list[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class UpdateWorkflowCommand:
    """Command to update an existing workflow."""
    workflow_id: WorkflowId
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[list[Dict[str, Any]]] = None
    actions: Optional[list[Dict[str, Any]]] = None
    tags: Optional[list[str]] = None


@dataclass
class DeleteWorkflowCommand:
    """Command to delete a workflow."""
    workflow_id: WorkflowId


@dataclass
class ActivateWorkflowCommand:
    """Command to activate a workflow."""
    workflow_id: WorkflowId


@dataclass
class ExecuteWorkflowCommand:
    """Command to execute a workflow."""
    workflow_id: WorkflowId
    parameters: Dict[str, Any]
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None


@dataclass
class CancelWorkflowExecutionCommand:
    """Command to cancel a workflow execution."""
    execution_id: ExecutionId


@dataclass
class RetryWorkflowExecutionCommand:
    """Command to retry a failed workflow execution."""
    execution_id: ExecutionId
