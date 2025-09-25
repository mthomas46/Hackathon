"""
ServiceDTO - Data Transfer Object

DTO for transferring service data between layers.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class ServiceDTO:
    """Data Transfer Object for service information.

    Used to transfer service data between application
    and presentation layers without exposing domain entities.
    """

    name: str
    path: str
    type: str
    status: str
    discovered_at: Optional[datetime] = None
    last_audited_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_domain(cls, service_info) -> 'ServiceDTO':
        """Create DTO from domain ServiceInfo entity."""
        return cls(
            name=service_info.name,
            path=str(service_info.path),
            type=service_info.type,
            status=service_info.status,
            discovered_at=service_info.discovered_at,
            last_audited_at=service_info.last_audited_at,
            metadata=service_info.metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "name": self.name,
            "path": self.path,
            "type": self.type,
            "status": self.status,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
            "last_audited_at": self.last_audited_at.isoformat() if self.last_audited_at else None,
            "metadata": self.metadata or {},
        }
