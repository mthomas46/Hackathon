"""Memory service domain service for DDD compliance."""

from typing import List, Optional
from ..entities.memory_item import MemoryItem, MemoryType
from ..entities.memory_session import MemorySession
from ..repositories.memory_repository import MemoryRepository


class MemoryService:
    """Domain service for memory operations."""

    def __init__(self, repository: MemoryRepository):
        self._repository = repository

    async def store_memory(self, user_id: str, memory_type: str, content: str, **kwargs) -> MemoryItem:
        """Store a new memory item."""
        memory_item = MemoryItem(
            id=f"{user_id}_{memory_type}_{int(__import__('time').time() * 1000000)}",
            user_id=user_id,
            memory_type=MemoryType[memory_type.upper()],
            content=content,
            **kwargs
        )
        await self._repository.save_memory_item(memory_item)
        return memory_item

    async def retrieve_memories(self, user_id: str, memory_type: Optional[str] = None, limit: int = 50) -> List[MemoryItem]:
        """Retrieve memories for a user."""
        if memory_type:
            return await self._repository.find_memory_items_by_type(
                user_id, MemoryType[memory_type.upper()], limit
            )
        return await self._repository.find_memory_items_by_user(user_id, limit)

    async def update_memory(self, item_id: str, new_content: str) -> Optional[MemoryItem]:
        """Update memory content."""
        item = await self._repository.find_memory_item_by_id(item_id)
        if item:
            item.update_content(new_content)
            await self._repository.save_memory_item(item)
        return item

    async def get_memory_statistics(self, user_id: str) -> dict:
        """Get memory statistics for a user."""
        items = await self._repository.find_memory_items_by_user(user_id, limit=1000)
        return {
            "total_memories": len(items),
            "memories_by_type": {
                memory_type.value: len([i for i in items if i.memory_type == memory_type])
                for memory_type in MemoryType
            },
            "oldest_memory": min((i.created_at for i in items), default=None),
            "newest_memory": max((i.created_at for i in items), default=None)
        }
