"""Service domain entity."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

from ..value_objects.service_id import ServiceId
from ..value_objects.service_status import ServiceStatus


@dataclass
class Service:
    """Domain entity representing a service in the ecosystem."""

    id: ServiceId
    name: str
    status: ServiceStatus
    endpoint: str
    metadata: Optional[Dict[str, Any]] = None
    registered_at: datetime = None
    last_health_check: Optional[datetime] = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.registered_at is None:
            self.registered_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def validate(self) -> None:
        """Validate the service according to domain rules."""
        if not self.name or not self.name.strip():
            raise ValueError("Service name cannot be empty")

        if not self.endpoint or not self.endpoint.strip():
            raise ValueError("Service endpoint cannot be empty")

    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status.is_healthy()

    def update_health_status(self, healthy: bool) -> None:
        """Update service health status."""
        if healthy:
            if self.status == ServiceStatus.UNKNOWN:
                self.status = ServiceStatus.REGISTERED
            elif self.status == ServiceStatus.DEGRADED:
                self.status = ServiceStatus.ACTIVE
        else:
            if self.status == ServiceStatus.ACTIVE:
                self.status = ServiceStatus.DEGRADED
            elif self.status in [ServiceStatus.REGISTERED, ServiceStatus.UNKNOWN]:
                self.status = ServiceStatus.FAILED

        self.last_health_check = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': str(self.id),
            'name': self.name,
            'status': str(self.status),
            'endpoint': self.endpoint,
            'metadata': self.metadata,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
        }
