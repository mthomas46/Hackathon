"""Data Transfer Objects for service discovery operations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class ServiceDto(BaseModel):
    """DTO for service data."""
    id: str
    service_type: str
    endpoint: str
    capabilities: List[str]
    registered_at: datetime
    status: str


class ServiceRegistryDto(BaseModel):
    """DTO for service registry data."""
    total_services: int
    active_services: int
    service_types: List[str]
    last_updated: datetime


class DiscoveryResultDto(BaseModel):
    """DTO for discovery operation results."""
    services_found: int
    search_criteria: Dict[str, Any]
    results: List[ServiceDto]
