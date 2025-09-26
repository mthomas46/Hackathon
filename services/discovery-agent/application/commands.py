"""Discovery agent commands for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class RegisterServiceCommand(BaseModel):
    """Command to register a new service."""
    service_id: str
    service_type: str
    endpoint: str
    capabilities: Optional[list] = None


class UnregisterServiceCommand(BaseModel):
    """Command to unregister a service."""
    service_id: str


class UpdateServiceCommand(BaseModel):
    """Command to update service information."""
    service_id: str
    updates: Dict[str, Any]


class DiscoverServicesCommand(BaseModel):
    """Command to discover available services."""
    service_type: Optional[str] = None
    capabilities: Optional[list] = None
