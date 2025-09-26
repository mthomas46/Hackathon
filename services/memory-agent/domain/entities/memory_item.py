"""Memory Item domain entity for DDD compliance."""

from typing import Any, Dict, Optional
from datetime import datetime
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
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
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
        return (datetime.utcnow() - self.created_at).total_seconds()
