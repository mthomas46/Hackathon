"""Workflow Failed Event"""

from typing import Dict, Any

from .base_event import DomainEvent


class WorkflowFailedEvent(DomainEvent):
    """Event emitted when a workflow execution fails."""

    def __init__(self, execution_id: str, workflow_id: str, error_message: str):
        super().__init__(
            event_type="workflow.failed",
            aggregate_id=execution_id,
            event_data={
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "error_message": error_message
            }
        )
