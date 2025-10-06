"""MCP Context Entity - Domain Layer.

Represents operational context for an MCP instance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

from services.mcp_infrastructure.domain.value_objects.mcp_context_type import MCPContextType


@dataclass
class MCPContext:
    """
    MCP Context entity - represents operational context for an MCP instance.
    
    This is the core aggregate root for MCP context management,
    storing operational state, metadata, and temporal information.
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mcp_id: str = ""  # MCP instance this context belongs to
    
    # Context type and data
    context_type: MCPContextType = MCPContextType.INSTANCE
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Temporal information
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # TTL and tags
    ttl: int = 3600  # Time-to-live in seconds (default 1 hour)
    tags: List[str] = field(default_factory=list)
    
    # Versioning
    version: int = 1
    
    def __post_init__(self):
        """Validate the context after initialization."""
        if not self.mcp_id:
            raise ValueError("MCPContext must have an mcp_id")
        
        if not isinstance(self.context_type, MCPContextType):
            raise TypeError("context_type must be an instance of MCPContextType")
        
        # Set expires_at based on TTL if not set
        if self.expires_at is None and self.ttl > 0:
            from datetime import timedelta
            self.expires_at = self.created_at + timedelta(seconds=self.ttl)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """
        Update the context data.
        
        Args:
            data: New data to merge with existing data
        """
        self.data.update(data)
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the context.
        
        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the context.
        
        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def refresh_ttl(self, ttl: Optional[int] = None) -> None:
        """
        Refresh the TTL and update expires_at.
        
        Args:
            ttl: New TTL in seconds (optional, uses existing if not provided)
        """
        if ttl is not None:
            self.ttl = ttl
        
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(seconds=self.ttl)
        self.updated_at = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if the context has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the MCPContext to a dictionary.
        
        Returns:
            Dictionary representation of the context
        """
        return {
            "id": self.id,
            "mcp_id": self.mcp_id,
            "context_type": self.context_type.value,
            "data": self.data,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "ttl": self.ttl,
            "tags": self.tags,
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPContext":
        """
        Create an MCPContext from a dictionary.
        
        Args:
            data: Dictionary containing context data
        
        Returns:
            MCPContext instance
        """
        return cls(
            id=data["id"],
            mcp_id=data["mcp_id"],
            context_type=MCPContextType(data["context_type"]),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            ttl=data.get("ttl", 3600),
            tags=data.get("tags", []),
            version=data.get("version", 1),
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, MCPContext):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"MCPContext(id={self.id}, mcp_id={self.mcp_id}, "
            f"type={self.context_type}, version={self.version})"
        )

