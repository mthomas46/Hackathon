"""Orchestrator queries for CQRS pattern compliance."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GetWorkflowStatusQuery(BaseModel):
    """Query to get workflow status."""
    workflow_id: str


class ListWorkflowsQuery(BaseModel):
    """Query to list workflows with filters."""
    status: Optional[str] = None
    workflow_type: Optional[str] = None
    limit: int = 50
    offset: int = 0


class GetServiceRegistryQuery(BaseModel):
    """Query to get service registry information."""
    service_id: Optional[str] = None


class GetWorkflowMetricsQuery(BaseModel):
    """Query to get workflow performance metrics."""
    time_range: str = "24h"
    metric_types: List[str]
