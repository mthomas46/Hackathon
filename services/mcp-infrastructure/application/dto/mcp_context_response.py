"""MCP Context Response DTO."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class MCPContextResponse:
    """
    DTO for MCP context responses.
    
    Used to transfer context data from application layer
    to presentation layer.
    """
    
    # Identity
    id: str
    mcp_id: str
    
    # Context data
    context_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Temporal information
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None
    
    # Additional info
    ttl: int = 3600
    tags: List[str] = field(default_factory=list)
    version: int = 1
    is_expired: bool = False
    
    @classmethod
    def from_entity(cls, context) -> "MCPContextResponse":
        """
        Create response from MCPContext entity.
        
        Args:
            context: MCPContext domain entity
        
        Returns:
            MCPContextResponse
        """
        return cls(
            id=context.id,
            mcp_id=context.mcp_id,
            context_type=context.context_type.value,
            data=context.data,
            metadata=context.metadata,
            created_at=context.created_at.isoformat() if context.created_at else None,
            updated_at=context.updated_at.isoformat() if context.updated_at else None,
            expires_at=context.expires_at.isoformat() if context.expires_at else None,
            ttl=context.ttl,
            tags=context.tags,
            version=context.version,
            is_expired=context.is_expired(),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "mcp_id": self.mcp_id,
            "context_type": self.context_type,
            "data": self.data,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "ttl": self.ttl,
            "tags": self.tags,
            "version": self.version,
            "is_expired": self.is_expired,
        }

