"""Workflow Created Event"""

from typing import Dict, Any

from .base_event import DomainEvent


class WorkflowCreatedEvent(DomainEvent):
    """Event emitted when a workflow is created."""

    def __init__(self, workflow_id: str, name: str, created_by: str):
        super().__init__(
            event_type="workflow.created",
            aggregate_id=workflow_id,
            event_data={
                "workflow_id": workflow_id,
                "name": name,
                "created_by": created_by
            }
        )
