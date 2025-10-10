"""Domain Entities for Service Discovery.

This module defines the core domain entities for the service discovery system.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import uuid


# Simple BaseEntity implementation (removed dependency on shared infrastructure)
@dataclass
class BaseEntity:
    """Base class for all domain entities."""
    
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Endpoint:
    """Represents a discovered API endpoint."""

    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    responses: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    service_id: Optional[str] = None
    # BaseEntity fields
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def operation_id(self) -> str:
        """Generate a unique operation ID."""
        # Replace URL special characters with underscores for operation ID
        safe_path = self.path.replace('/', '_').replace('{', '_').replace('}', '_').replace('-', '_')
        return f"{self.method.upper()}{safe_path}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert endpoint to dictionary representation."""
        return {
            "id": self.id,
            "path": self.path,
            "method": self.method,
            "summary": self.summary,
            "description": self.description,
            "parameters": self.parameters,
            "responses": self.responses,
            "tags": self.tags,
            "service_id": self.service_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Endpoint':
        """Create endpoint from dictionary."""
        # Handle datetime parsing
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")

        return cls(
            id=data.get("id"),
            path=data["path"],
            method=data["method"],
            summary=data.get("summary"),
            description=data.get("description"),
            parameters=data.get("parameters", []),
            responses=data.get("responses", {}),
            tags=data.get("tags", []),
            service_id=data.get("service_id"),
            created_at=datetime.fromisoformat(created_at) if created_at else None,
            updated_at=datetime.fromisoformat(updated_at) if updated_at else None,
        )


@dataclass
class Service:
    """Represents a discovered service with its endpoints."""

    name: str
    base_url: str
    openapi_url: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    endpoints: List[Endpoint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "discovered"  # discovered, active, inactive, error
    # BaseEntity fields
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def endpoint_count(self) -> int:
        """Get the number of endpoints."""
        return len(self.endpoints)

    @property
    def health_url(self) -> str:
        """Get the health check URL."""
        return f"{self.base_url.rstrip('/')}/health"

    def add_endpoint(self, endpoint: Endpoint) -> None:
        """Add an endpoint to this service."""
        endpoint.service_id = self.id
        self.endpoints.append(endpoint)
        self.updated_at = datetime.now(timezone.utc)

    def remove_endpoint(self, endpoint_id: str) -> bool:
        """Remove an endpoint from this service."""
        for i, endpoint in enumerate(self.endpoints):
            if endpoint.id == endpoint_id:
                self.endpoints.pop(i)
                self.updated_at = datetime.now(timezone.utc)
                return True
        return False

    def find_endpoint(self, path: str, method: str) -> Optional[Endpoint]:
        """Find an endpoint by path and method."""
        for endpoint in self.endpoints:
            if endpoint.path == path and endpoint.method.upper() == method.upper():
                return endpoint
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert service to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "openapi_url": self.openapi_url,
            "version": self.version,
            "description": self.description,
            "endpoints": [endpoint.to_dict() for endpoint in self.endpoints],
            "endpoint_count": self.endpoint_count,
            "metadata": self.metadata,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Service':
        """Create service from dictionary."""
        # Handle datetime parsing
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")

        # Handle endpoints
        endpoints_data = data.get("endpoints", [])
        endpoints = [Endpoint.from_dict(endpoint_data) for endpoint_data in endpoints_data]

        return cls(
            id=data.get("id"),
            name=data["name"],
            base_url=data["base_url"],
            openapi_url=data.get("openapi_url"),
            version=data.get("version"),
            description=data.get("description"),
            endpoints=endpoints,
            metadata=data.get("metadata", {}),
            status=data.get("status", "discovered"),
            created_at=datetime.fromisoformat(created_at) if created_at else None,
            updated_at=datetime.fromisoformat(updated_at) if updated_at else None,
        )


@dataclass
class DiscoveryResult:
    """Result of a service discovery operation."""

    service: Service
    success: bool
    error_message: Optional[str] = None
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    discovery_duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_successful(self) -> bool:
        """Check if discovery was successful."""
        return self.success

    @property
    def endpoint_count(self) -> int:
        """Get the number of discovered endpoints."""
        return len(self.service.endpoints) if self.success else 0

    def summary(self) -> str:
        """Get a human-readable summary of the discovery result."""
        if self.success:
            return (
                f"Successfully discovered service '{self.service.name}' "
                f"with {self.endpoint_count} endpoints"
                + (f" in {self.discovery_duration_ms:.2f}ms" if self.discovery_duration_ms else "")
            )
        else:
            return f"Failed to discover service: {self.error_message or 'Unknown error'}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "service": self.service.to_dict(),
            "success": self.success,
            "is_successful": self.is_successful,
            "error_message": self.error_message,
            "endpoint_count": self.endpoint_count,
            "discovery_duration_ms": self.discovery_duration_ms,
            "metadata": self.metadata,
            "discovered_at": self.discovered_at.isoformat(),
            "summary": self.summary(),
        }
