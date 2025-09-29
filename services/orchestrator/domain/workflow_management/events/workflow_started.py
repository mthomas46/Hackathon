"""Workflow Started Event"""

from typing import Dict, Any

from .base_event import DomainEvent


class WorkflowStartedEvent(DomainEvent):
    """Event emitted when a workflow execution starts."""

    def __init__(self, execution_id: str, workflow_id: str, correlation_id: str = None):
        super().__init__(
            event_type="workflow.started",
            aggregate_id=execution_id,
            event_data={
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "correlation_id": correlation_id
            }
        )
