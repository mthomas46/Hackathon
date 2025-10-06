"""MCP Status DTO - Application Layer.

This DTO carries status information about an MCP instance.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class MCPStatusDTO:
    """
    Data Transfer Object for MCP instance status.
    
    This DTO is used to transfer MCP status information
    from the application layer to the presentation layer.
    """
    
    # Identity
    mcp_id: str
    client_id: str
    name: str
    
    # Status
    state: str  # e.g., "cold", "warming", "hot", "cooling", "error"
    container_id: Optional[str] = None
    ip_address: Optional[str] = None
    external_port: Optional[int] = None
    
    # Configuration
    tier: int = 0
    image_name: str = "client-mcp:latest"
    
    # Timestamps
    created_at: Optional[str] = None  # ISO 8601 format
    updated_at: Optional[str] = None
    last_accessed_at: Optional[str] = None
    
    # Additional info
    metadata: Dict[str, Any] = field(default_factory=dict)
    health_status: Optional[str] = None  # "healthy", "unhealthy", "unknown"
    
    @classmethod
    def from_entity(cls, instance) -> "MCPStatusDTO":
        """
        Create DTO from MCPInstance entity.
        
        Args:
            instance: MCPInstance domain entity
        
        Returns:
            MCPStatusDTO
        """
        return cls(
            mcp_id=instance.id,
            client_id=instance.client_id,
            name=instance.name,
            state=instance.state.value,
            container_id=instance.container_id,
            ip_address=instance.ip_address,
            external_port=instance.external_port,
            tier=instance.mcp_config.tier if hasattr(instance.mcp_config, 'tier') else 0,
            image_name=instance.mcp_config.image_name,
            created_at=instance.created_at.isoformat() if instance.created_at else None,
            updated_at=instance.updated_at.isoformat() if instance.updated_at else None,
            last_accessed_at=instance.last_accessed_at.isoformat() if instance.last_accessed_at else None,
            metadata=instance.metadata,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        return {
            "mcp_id": self.mcp_id,
            "client_id": self.client_id,
            "name": self.name,
            "state": self.state,
            "container_id": self.container_id,
            "ip_address": self.ip_address,
            "external_port": self.external_port,
            "tier": self.tier,
            "image_name": self.image_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_accessed_at": self.last_accessed_at,
            "metadata": self.metadata,
            "health_status": self.health_status,
        }

