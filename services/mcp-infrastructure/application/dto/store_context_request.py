"""Store Context Request DTO."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class StoreContextRequest:
    """
    DTO for storing MCP context.
    
    Contains all information needed to create or update
    context in the infrastructure service.
    """
    
    # Required fields
    mcp_id: str
    context_type: str  # Will be converted to MCPContextType enum
    data: Dict[str, Any]
    
    # Optional fields
    metadata: Dict[str, Any] = field(default_factory=dict)
    ttl: Optional[int] = None  # Use default if not provided
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the request after initialization."""
        if not self.mcp_id:
            raise ValueError("mcp_id is required")
        
        if not self.context_type:
            raise ValueError("context_type is required")
        
        if not isinstance(self.data, dict):
            raise TypeError("data must be a dictionary")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mcp_id": self.mcp_id,
            "context_type": self.context_type,
            "data": self.data,
            "metadata": self.metadata,
            "ttl": self.ttl,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoreContextRequest":
        """Create from dictionary."""
        return cls(
            mcp_id=data["mcp_id"],
            context_type=data["context_type"],
            data=data["data"],
            metadata=data.get("metadata", {}),
            ttl=data.get("ttl"),
            tags=data.get("tags", []),
        )

