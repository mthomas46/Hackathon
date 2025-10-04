"""Memory Item domain entity for DDD compliance."""

from typing import Any, Dict, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum


class MemoryType(Enum):
    """Memory item type enumeration."""
    CONVERSATION = "conversation"
    FACT = "fact"
    PREFERENCE = "preference"
    CONTEXT = "context"
    SESSION = "session"


@dataclass
class MemoryItem:
    """Domain entity representing a memory item."""

    id: str
    user_id: str
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def update_content(self, new_content: str) -> None:
        """Update memory content."""
        self.content = new_content
        self.updated_at = datetime.utcnow()
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

    def record_access(self) -> None:
        """Record memory access."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if memory item is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def age_seconds(self) -> float:
        """Get age of memory item in seconds."""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()
    
    @classmethod
    def generate_id(cls) -> str:
        """Generate a unique identifier for new entities."""
        from uuid import uuid4
        return str(uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation with JSON serialization for complex fields."""
        import json
        return {
            "id": self.id,
            "user_id": self.user_id,
            "memory_type": self.memory_type.value if isinstance(self.memory_type, MemoryType) else str(self.memory_type),
            "content": self.content,
            "metadata": json.dumps(self.metadata) if isinstance(self.metadata, dict) else self.metadata,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "expires_at": self.expires_at.isoformat() if isinstance(self.expires_at, datetime) and self.expires_at else None,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if isinstance(self.last_accessed, datetime) and self.last_accessed else None,
        }
