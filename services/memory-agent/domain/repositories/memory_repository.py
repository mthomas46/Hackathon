"""Memory repository interface for DDD compliance."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.memory_item import MemoryItem, MemoryType
from ..entities.memory_session import MemorySession


class MemoryRepository(ABC):
    """Abstract repository for memory operations."""

    @abstractmethod
    async def save_memory_item(self, item: MemoryItem) -> None:
        """Save a memory item."""
        pass

    @abstractmethod
    async def find_memory_item_by_id(self, item_id: str) -> Optional[MemoryItem]:
        """Find memory item by ID."""
        pass

    @abstractmethod
    async def find_memory_items_by_user(self, user_id: str, limit: int = 50) -> List[MemoryItem]:
        """Find memory items by user."""
        pass

    @abstractmethod
    async def find_memory_items_by_type(self, user_id: str, memory_type: MemoryType, limit: int = 50) -> List[MemoryItem]:
        """Find memory items by type."""
        pass

    @abstractmethod
    async def delete_memory_item(self, item_id: str) -> bool:
        """Delete a memory item."""
        pass

    @abstractmethod
    async def cleanup_expired_items(self) -> int:
        """Clean up expired memory items."""
        pass
