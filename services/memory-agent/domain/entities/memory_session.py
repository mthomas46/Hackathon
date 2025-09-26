"""Memory Session domain entity for DDD compliance."""

from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from .memory_item import MemoryItem


@dataclass
class MemorySession:
    """Domain entity representing a memory session."""

    id: str
    user_id: str
    session_type: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    memory_items: List[MemoryItem] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_memory_item(self, item: MemoryItem) -> None:
        """Add a memory item to the session."""
        self.memory_items.append(item)
        self.last_activity = datetime.utcnow()

    def get_recent_items(self, limit: int = 10) -> List[MemoryItem]:
        """Get recent memory items."""
        return sorted(
            self.memory_items,
            key=lambda x: x.last_accessed or x.created_at,
            reverse=True
        )[:limit]

    def close_session(self) -> None:
        """Close the memory session."""
        self.is_active = False
        self.last_activity = datetime.utcnow()

    @property
    def item_count(self) -> int:
        """Get total number of memory items."""
        return len(self.memory_items)

    @property
    def session_age_seconds(self) -> float:
        """Get session age in seconds."""
        return (datetime.utcnow() - self.created_at).total_seconds()
