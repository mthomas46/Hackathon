"""Action Executed Event"""

from typing import Dict, Any

from .base_event import DomainEvent


class ActionExecutedEvent(DomainEvent):
    """Event emitted when a workflow action is executed."""

    def __init__(self, execution_id: str, action_id: str, status: str, execution_time_ms: int):
        super().__init__(
            event_type="action.executed",
            aggregate_id=execution_id,
            event_data={
                "execution_id": execution_id,
                "action_id": action_id,
                "status": status,
                "execution_time_ms": execution_time_ms
            }
        )
