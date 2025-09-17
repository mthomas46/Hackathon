"""Application Queries for Service Registry"""

from typing import Optional, List
from dataclasses import dataclass

from ...domain.service_registry import ServiceId


@dataclass
class GetServiceQuery:
    """Query to get a service by ID."""
    service_id: ServiceId


@dataclass
class ListServicesQuery:
    """Query to list services with optional filters."""
    category_filter: Optional[str] = None
    capability_filter: Optional[str] = None
    status_filter: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetServiceCategoriesQuery:
    """Query to get all service categories."""


@dataclass
class GetServiceCapabilitiesQuery:
    """Query to get service capabilities summary."""
