"""Discovery agent queries for CQRS pattern compliance."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GetServiceByIdQuery(BaseModel):
    """Query to get service by ID."""
    service_id: str


class ListServicesQuery(BaseModel):
    """Query to list services with filters."""
    service_type: Optional[str] = None
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0


class GetServiceHealthQuery(BaseModel):
    """Query to get service health information."""
    service_id: str


class GetDiscoveryStatsQuery(BaseModel):
    """Query to get discovery statistics."""
    time_range: str = "24h"
