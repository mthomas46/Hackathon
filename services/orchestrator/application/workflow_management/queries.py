"""Application Queries for Workflow Management"""

from typing import Optional, List
from dataclasses import dataclass

from ...domain.workflow_management import WorkflowId, ExecutionId


@dataclass
class GetWorkflowQuery:
    """Query to get a workflow by ID."""
    workflow_id: WorkflowId


@dataclass
class ListWorkflowsQuery:
    """Query to list workflows with optional filters."""
    name_filter: Optional[str] = None
    tag_filter: Optional[str] = None
    status_filter: Optional[str] = None
    created_by_filter: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetWorkflowExecutionQuery:
    """Query to get a workflow execution by ID."""
    execution_id: ExecutionId


@dataclass
class ListWorkflowExecutionsQuery:
    """Query to list workflow executions with optional filters."""
    workflow_id_filter: Optional[WorkflowId] = None
    status_filter: Optional[str] = None
    correlation_id_filter: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetWorkflowStatsQuery:
    """Query to get workflow statistics."""
    workflow_id: Optional[WorkflowId] = None
    time_range_days: Optional[int] = None
