"""Orchestrator commands for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class StartWorkflowCommand(BaseModel):
    """Command to start a new workflow."""
    workflow_id: str
    workflow_type: str
    parameters: Optional[Dict[str, Any]] = None


class StopWorkflowCommand(BaseModel):
    """Command to stop a running workflow."""
    workflow_id: str
    reason: Optional[str] = None


class ProcessEventCommand(BaseModel):
    """Command to process a workflow event."""
    event_type: str
    event_data: Dict[str, Any]


class UpdateServiceRegistryCommand(BaseModel):
    """Command to update service registry."""
    service_id: str
    service_data: Dict[str, Any]
