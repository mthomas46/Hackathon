"""Service Entity"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ..value_objects.service_id import ServiceId
from ..value_objects.service_endpoint import ServiceEndpoint
from ..value_objects.service_capability import ServiceCapability


class Service:
    """Entity representing a registered service in the ecosystem."""

    def __init__(
        self,
        service_id: ServiceId,
        name: str,
        description: str,
        category: str,
        base_url: Optional[str] = None,
        openapi_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._service_id = service_id
        self._name = name.strip()
        self._description = description.strip()
        self._category = category.strip()
        self._base_url = base_url.strip() if base_url else None
        self._openapi_url = openapi_url.strip() if openapi_url else None
        self._metadata = metadata or {}
        self._capabilities: List[ServiceCapability] = []
        self._endpoints: List[ServiceEndpoint] = []
        self._registered_at = datetime.utcnow()
        self._last_seen = datetime.utcnow()
        self._status = "unknown"

        self._validate()

    def _validate(self):
        """Validate service data."""
        if not self._name:
            raise ValueError("Service name cannot be empty")

        if not self._description:
            raise ValueError("Service description cannot be empty")

        if not self._category:
            raise ValueError("Service category cannot be empty")

    @property
    def service_id(self) -> ServiceId:
        """Get the service ID."""
        return self._service_id

    @property
    def name(self) -> str:
        """Get the service name."""
        return self._name

    @property
    def description(self) -> str:
        """Get the service description."""
        return self._description

    @property
    def category(self) -> str:
        """Get the service category."""
        return self._category

    @property
    def base_url(self) -> Optional[str]:
        """Get the service base URL."""
        return self._base_url

    @property
    def openapi_url(self) -> Optional[str]:
        """Get the service OpenAPI URL."""
        return self._openapi_url

    @property
    def capabilities(self) -> List[ServiceCapability]:
        """Get the service capabilities."""
        return self._capabilities.copy()

    @property
    def endpoints(self) -> List[ServiceEndpoint]:
        """Get the service endpoints."""
        return self._endpoints.copy()

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get the service metadata."""
        return self._metadata.copy()

    @property
    def registered_at(self) -> datetime:
        """Get the registration timestamp."""
        return self._registered_at

    @property
    def last_seen(self) -> datetime:
        """Get the last seen timestamp."""
        return self._last_seen

    @property
    def status(self) -> str:
        """Get the service status."""
        return self._status

    def add_capability(self, capability: ServiceCapability):
        """Add a capability to the service."""
        if capability not in self._capabilities:
            self._capabilities.append(capability)

    def remove_capability(self, capability: ServiceCapability):
        """Remove a capability from the service."""
        if capability in self._capabilities:
            self._capabilities.remove(capability)

    def add_endpoint(self, endpoint: ServiceEndpoint):
        """Add an endpoint to the service."""
        if endpoint not in self._endpoints:
            self._endpoints.append(endpoint)

    def update_status(self, status: str):
        """Update the service status."""
        valid_statuses = ["healthy", "unhealthy", "unknown", "maintenance"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        self._status = status
        self._last_seen = datetime.utcnow()

    def update_metadata(self, metadata: Dict[str, Any]):
        """Update the service metadata."""
        self._metadata.update(metadata)

    def has_capability(self, capability_name: str) -> bool:
        """Check if service has a specific capability."""
        return any(cap.name == capability_name for cap in self._capabilities)

    def get_endpoints_by_method(self, method: str) -> List[ServiceEndpoint]:
        """Get endpoints filtered by HTTP method."""
        return [ep for ep in self._endpoints if ep.method == method.upper()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "service_id": self._service_id.value,
            "name": self._name,
            "description": self._description,
            "category": self._category,
            "base_url": self._base_url,
            "openapi_url": self._openapi_url,
            "capabilities": [cap.name for cap in self._capabilities],
            "endpoints": [ep.full_path for ep in self._endpoints],
            "metadata": self._metadata,
            "registered_at": self._registered_at.isoformat(),
            "last_seen": self._last_seen.isoformat(),
            "status": self._status
        }
