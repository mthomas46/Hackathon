"""Service discovery domain events for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel
from datetime import datetime


class ServiceRegisteredEvent(BaseModel):
    """Event fired when a service is registered."""
    service_id: str
    service_type: str
    endpoint: str
    registered_at: datetime
    capabilities: Optional[list] = None


class ServiceUnregisteredEvent(BaseModel):
    """Event fired when a service is unregistered."""
    service_id: str
    unregistered_at: datetime


class ServiceUpdatedEvent(BaseModel):
    """Event fired when a service is updated."""
    service_id: str
    updates: Dict[str, Any]
    updated_at: datetime


class ServiceDiscoveryPerformedEvent(BaseModel):
    """Event fired when a service discovery operation is performed."""
    query_criteria: Dict[str, Any]
    services_found: int
    discovery_duration_ms: int
    performed_at: datetime
