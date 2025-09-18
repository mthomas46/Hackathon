"""Workflow Completed Event"""

from typing import Dict, Any

from .base_event import DomainEvent


class WorkflowCompletedEvent(DomainEvent):
    """Event emitted when a workflow execution completes."""

    def __init__(self, execution_id: str, workflow_id: str, duration_ms: int):
        super().__init__(
            event_type="workflow.completed",
            aggregate_id=execution_id,
            event_data={
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "duration_ms": duration_ms
            }
        )
