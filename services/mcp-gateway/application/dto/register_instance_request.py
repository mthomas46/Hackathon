"""Register Instance Request DTO."""

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class RegisterInstanceRequest:
    """
    DTO for registering an MCP instance with the Gateway.
    """
    
    # Required fields
    mcp_id: str  # MCP identifier
    host: str  # Hostname/IP
    port: int  # Port number
    
    # Optional fields
    name: str = ""
    tier: int = 0
    priority: int = 100
    weight: int = 100
    max_concurrent_requests: int = 100
    health_check_url: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the request."""
        if not self.mcp_id:
            raise ValueError("mcp_id is required")
        if not self.host:
            raise ValueError("host is required")
        if self.port <= 0:
            raise ValueError("port must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mcp_id": self.mcp_id,
            "host": self.host,
            "port": self.port,
            "name": self.name,
            "tier": self.tier,
            "priority": self.priority,
            "weight": self.weight,
            "max_concurrent_requests": self.max_concurrent_requests,
            "health_check_url": self.health_check_url,
            "tags": self.tags,
            "metadata": self.metadata,
        }

