"""In-Memory Repository Implementations"""

from typing import List, Optional, Dict
from threading import Lock

from .interfaces import WorkflowRepositoryInterface, WorkflowExecutionRepositoryInterface
from ...domain.workflow_management import Workflow, WorkflowExecution, WorkflowId, ExecutionId


class InMemoryWorkflowRepository(WorkflowRepositoryInterface):
    """In-memory implementation of workflow repository."""

    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._lock = Lock()

    def save_workflow(self, workflow: Workflow) -> bool:
        """Save a workflow."""
        with self._lock:
            self._workflows[workflow.workflow_id.value] = workflow
            return True

    def get_workflow(self, workflow_id: WorkflowId) -> Optional[Workflow]:
        """Get a workflow by ID."""
        with self._lock:
            return self._workflows.get(workflow_id.value)

    def list_workflows(
        self,
        name_filter: Optional[str] = None,
        tag_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        created_by_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Workflow]:
        """List workflows with optional filters."""
        with self._lock:
            workflows = list(self._workflows.values())

            # Apply filters
            if name_filter:
                workflows = [w for w in workflows if name_filter.lower() in w.name.lower()]

            if tag_filter:
                workflows = [w for w in workflows if tag_filter in w.tags]

            if status_filter:
                workflows = [w for w in workflows if w.status.value == status_filter]

            if created_by_filter:
                workflows = [w for w in workflows if w.created_by == created_by_filter]

            # Apply pagination
            start = offset
            end = offset + limit
            return workflows[start:end]

    def delete_workflow(self, workflow_id: WorkflowId) -> bool:
        """Delete a workflow."""
        with self._lock:
            if workflow_id.value in self._workflows:
                del self._workflows[workflow_id.value]
                return True
            return False

    def update_workflow(self, workflow: Workflow) -> bool:
        """Update a workflow."""
        with self._lock:
            self._workflows[workflow.workflow_id.value] = workflow
            return True


class InMemoryWorkflowExecutionRepository(WorkflowExecutionRepositoryInterface):
    """In-memory implementation of workflow execution repository."""

    def __init__(self):
        self._executions: Dict[str, WorkflowExecution] = {}
        self._lock = Lock()

    def save_execution(self, execution: WorkflowExecution) -> bool:
        """Save a workflow execution."""
        with self._lock:
            self._executions[execution.execution_id.value] = execution
            return True

    def get_execution(self, execution_id: ExecutionId) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        with self._lock:
            return self._executions.get(execution_id.value)

    def list_executions(
        self,
        workflow_id: Optional[WorkflowId] = None,
        status_filter: Optional[str] = None,
        started_after: Optional[str] = None,
        started_before: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """List workflow executions with optional filters."""
        with self._lock:
            executions = list(self._executions.values())

            # Apply filters
            if workflow_id:
                executions = [e for e in executions if e.workflow_id == workflow_id]

            if status_filter:
                executions = [e for e in executions if e.status.value == status_filter]

            if started_after:
                try:
                    after_dt = datetime.fromisoformat(started_after.replace('Z', '+00:00'))
                    executions = [e for e in executions if e.started_at and e.started_at >= after_dt]
                except ValueError:
                    pass  # Invalid date format, skip filter

            if started_before:
                try:
                    before_dt = datetime.fromisoformat(started_before.replace('Z', '+00:00'))
                    executions = [e for e in executions if e.started_at and e.started_at <= before_dt]
                except ValueError:
                    pass  # Invalid date format, skip filter

            # Sort by started_at descending
            executions.sort(key=lambda e: e.started_at or datetime.min, reverse=True)

            # Apply pagination
            start = offset
            end = offset + limit
            return executions[start:end]

    def update_execution(self, execution: WorkflowExecution) -> bool:
        """Update a workflow execution."""
        with self._lock:
            self._executions[execution.execution_id.value] = execution
            return True

    def delete_execution(self, execution_id: ExecutionId) -> bool:
        """Delete a workflow execution."""
        with self._lock:
            if execution_id.value in self._executions:
                del self._executions[execution_id.value]
                return True
            return False
