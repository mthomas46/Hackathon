"""Base service pattern for Prompt Store service.

Following domain-driven design principles with generic service implementation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic
from ..core.entities import BaseEntity
from ..core.repository import BaseRepository

T = TypeVar('T', bound=BaseEntity)


class BaseService(ABC, Generic[T]):
    """Base service with common business logic operations."""

    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository

    def create_entity(self, data: Dict[str, Any], entity_id: Optional[str] = None) -> T:
        """Create a new entity with validation."""
        # This will be implemented by subclasses
        raise NotImplementedError("Subclasses must implement create_entity")

    def get_entity(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        return self.repository.get_by_id(entity_id)

    def list_entities(self, limit: int = 50, offset: int = 0, **filters) -> Dict[str, Any]:
        """List entities with pagination."""
        result = self.repository.get_all(limit=limit, offset=offset, **filters)
        entities = result.get("items", [])

        return {
            "items": [entity.to_dict() for entity in entities],
            "total": result.get("total", 0),
            "has_more": result.get("has_more", False),
            "limit": limit,
            "offset": offset
        }

    def update_entity(self, entity_id: str, updates: Dict[str, Any]) -> Optional[T]:
        """Update entity."""
        return self.repository.update(entity_id, updates)

    def delete_entity(self, entity_id: str) -> bool:
        """Delete entity."""
        return self.repository.delete(entity_id)

    def entity_exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        return self.repository.exists(entity_id)

    def count_entities(self, **filters) -> int:
        """Count entities."""
        return self.repository.count(**filters)
