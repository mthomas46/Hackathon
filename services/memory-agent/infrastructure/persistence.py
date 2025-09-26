"""Memory repository implementation."""

from typing import List, Optional
from ..domain.repositories.memory_repository import MemoryRepository as BaseMemoryRepository
from ..domain.entities.memory_item import MemoryItem


class MemoryRepository(BaseMemoryRepository):
    """Concrete implementation of memory repository."""

    def __init__(self):
        self._memories = []  # In-memory storage for now

    async def save(self, memory_item: MemoryItem) -> None:
        """Save a memory item."""
        self._memories.append(memory_item)

    async def find_by_id(self, memory_id: str) -> Optional[MemoryItem]:
        """Find memory by ID."""
        for memory in self._memories:
            if memory.id == memory_id:
                return memory
        return None

    async def find_memories(self, query) -> List[MemoryItem]:
        """Find memories based on query."""
        # Simple filtering implementation
        results = self._memories

        if hasattr(query, 'user_id') and query.user_id:
            results = [m for m in results if m.user_id == query.user_id]

        if hasattr(query, 'memory_type') and query.memory_type:
            results = [m for m in results if m.memory_type.value == query.memory_type]

        # Apply limit
        limit = getattr(query, 'limit', 50)
        return results[-limit:] if results else []

    async def find_all(self) -> List[MemoryItem]:
        """Find all memories."""
        return self._memories.copy()

    async def get_stats(self) -> dict:
        """Get memory statistics."""
        return {
            "total_items": len(self._memories),
            "max_items": 1000,  # Placeholder
            "usage_percent": (len(self._memories) / 1000) * 100,
            "ttl_seconds": 3600  # Placeholder
        }
