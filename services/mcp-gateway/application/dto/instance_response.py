"""Instance Response DTO."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class InstanceResponse:
    """
    DTO for MCP instance response.
    """
    
    id: str
    mcp_id: str
    name: str
    host: str
    port: int
    base_url: str
    status: str
    health_check_url: str
    last_health_check: Optional[str]
    consecutive_failures: int
    active_requests: int
    total_requests: int
    average_response_time_ms: float
    tier: int
    priority: int
    weight: int
    max_concurrent_requests: int
    registered_at: str
    last_seen_at: str
    version: int
    tags: List[str]
    metadata: Dict[str, Any]
    load_factor: float
    is_available: bool
    
    @classmethod
    def from_entity(cls, instance) -> "InstanceResponse":
        """Create response from MCPInstance entity."""
        instance_dict = instance.to_dict()
        return cls(**instance_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "mcp_id": self.mcp_id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "base_url": self.base_url,
            "status": self.status,
            "health_check_url": self.health_check_url,
            "last_health_check": self.last_health_check,
            "consecutive_failures": self.consecutive_failures,
            "active_requests": self.active_requests,
            "total_requests": self.total_requests,
            "average_response_time_ms": self.average_response_time_ms,
            "tier": self.tier,
            "priority": self.priority,
            "weight": self.weight,
            "max_concurrent_requests": self.max_concurrent_requests,
            "registered_at": self.registered_at,
            "last_seen_at": self.last_seen_at,
            "version": self.version,
            "tags": self.tags,
            "metadata": self.metadata,
            "load_factor": self.load_factor,
            "is_available": self.is_available,
        }

