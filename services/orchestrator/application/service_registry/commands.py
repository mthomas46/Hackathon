"""Application Commands for Service Registry"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ...domain.service_registry import ServiceId


@dataclass
class RegisterServiceCommand:
    """Command to register a new service."""
    service_id: ServiceId
    name: str
    description: str
    category: str
    base_url: Optional[str] = None
    openapi_url: Optional[str] = None
    capabilities: Optional[List[str]] = None
    endpoints: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.endpoints is None:
            self.endpoints = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UnregisterServiceCommand:
    """Command to unregister a service."""
    service_id: ServiceId


@dataclass
class UpdateServiceStatusCommand:
    """Command to update service status."""
    service_id: ServiceId
    status: str


@dataclass
class HeartbeatServiceCommand:
    """Command to send heartbeat for a service."""
    service_id: ServiceId
