"""Base Repository Class"""

from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')
ID = TypeVar('ID')


class BaseRepository(Generic[T, ID], ABC):
    """Base class for all repository implementations."""

    @abstractmethod
    def save(self, entity: T) -> bool:
        """Save an entity."""
        pass

    @abstractmethod
    def find_by_id(self, entity_id: ID) -> Optional[T]:
        """Find an entity by ID."""
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        """Find all entities."""
        pass

    @abstractmethod
    def delete(self, entity_id: ID) -> bool:
        """Delete an entity by ID."""
        pass

    @abstractmethod
    def exists(self, entity_id: ID) -> bool:
        """Check if an entity exists."""
        pass
