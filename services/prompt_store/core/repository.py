"""Base repository pattern for Prompt Store service.

Following domain-driven design principles with generic repository implementation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic
from ..core.entities import BaseEntity

T = TypeVar('T', bound=BaseEntity)


class BaseRepository(ABC, Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, table_name: str):
        self.table_name = table_name

    @abstractmethod
    def save(self, entity: T) -> T:
        """Save entity to database."""
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def get_all(self, limit: int = 50, offset: int = 0, **filters) -> Dict[str, Any]:
        """Get all entities with pagination and filtering."""
        pass

    @abstractmethod
    def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[T]:
        """Update entity."""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity."""
        pass

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        pass

    @abstractmethod
    def count(self, **filters) -> int:
        """Count entities matching filters."""
        pass

    def _row_to_entity(self, row: Dict[str, Any]) -> T:
        """Convert database row to entity (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement _row_to_entity")

    def _entity_to_row(self, entity: T) -> Dict[str, Any]:
        """Convert entity to database row (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement _entity_to_row")
