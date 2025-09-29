"""
Domain entities for service discovery.
Following DDD principles with clean, focused entities.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class ServiceEndpoint:
    """Represents a service endpoint."""
    path: str
    method: str
    description: Optional[str] = None
    parameters: Optional[List[str]] = None
    response_type: Optional[str] = None
    is_active: bool = True


@dataclass
class ServiceRegistration:
    """Represents a service registration in the discovery system."""
    service_name: str
    base_url: str
    endpoints: List[ServiceEndpoint] = field(default_factory=list)
    version: Optional[str] = None
    health_check_url: Optional[str] = None
    registered_at: datetime = field(default_factory=datetime.now)
    last_health_check: Optional[datetime] = None
    is_active: bool = True
    metadata: Optional[dict] = None


@dataclass
class HealthStatus:
    """Represents the health status of a service."""
    is_healthy: bool
    version: Optional[str] = None
    uptime_seconds: Optional[int] = None
    endpoints: List[dict] = field(default_factory=list)
    last_checked: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None


@dataclass
class EndpointValidation:
    """Represents the validation result of an endpoint."""
    endpoint: ServiceEndpoint
    is_accessible: bool
    response_time_ms: Optional[int] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    validated_at: datetime = field(default_factory=datetime.now)


@dataclass
class DiscoveryResult:
    """Represents the result of a service discovery operation."""
    service_name: str
    base_url: Optional[str] = None
    status: str = "not_found"  # found, not_found, error
    registration: Optional[ServiceRegistration] = None
    health_status: Optional[HealthStatus] = None
    discovered_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
