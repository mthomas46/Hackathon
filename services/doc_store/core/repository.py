"""Base repository for data access operations.

Provides common CRUD operations and utilities for all repositories.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic
from datetime import datetime
from .entities import BaseEntity

T = TypeVar('T', bound=BaseEntity)


class BaseRepository(Generic[T], ABC):
    """Base repository with common CRUD operations."""

    def __init__(self, table_name: str):
        self.table_name = table_name

    @abstractmethod
    def _row_to_entity(self, row: Dict[str, Any]) -> T:
        """Convert database row to entity."""
        pass

    @abstractmethod
    def _entity_to_row(self, entity: T) -> Dict[str, Any]:
        """Convert entity to database row."""
        pass

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        from ..db.queries import execute_query

        row = execute_query(
            f"SELECT * FROM {self.table_name} WHERE id = ?",
            (entity_id,),
            fetch_one=True
        )
        return self._row_to_entity(row) if row else None

    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with pagination."""
        from ..db.queries import execute_query

        rows = execute_query(
            f"SELECT * FROM {self.table_name} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
            fetch_all=True
        )
        return [self._row_to_entity(row) for row in rows]

    def save(self, entity: T) -> None:
        """Save entity to database."""
        from ..db.queries import execute_query

        row_data = self._entity_to_row(entity)
        columns = ', '.join(row_data.keys())
        placeholders = ', '.join(['?'] * len(row_data))
        values = tuple(row_data.values())

        execute_query(
            f"INSERT OR REPLACE INTO {self.table_name} ({columns}) VALUES ({placeholders})",
            values
        )

    def update(self, entity: T) -> None:
        """Update existing entity."""
        from ..db.queries import execute_query

        entity.update_timestamp()
        row_data = self._entity_to_row(entity)
        set_clause = ', '.join([f"{k} = ?" for k in row_data.keys() if k != 'id'])
        values = tuple([row_data[k] for k in row_data.keys() if k != 'id']) + (entity.id,)

        execute_query(
            f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?",
            values
        )

    def delete_by_id(self, entity_id: str) -> None:
        """Delete entity by ID."""
        from ..db.queries import execute_query

        execute_query(f"DELETE FROM {self.table_name} WHERE id = ?", (entity_id,))

    def exists(self, entity_id: str) -> bool:
        """Check if entity exists."""
        from ..db.queries import execute_query

        row = execute_query(
            f"SELECT 1 FROM {self.table_name} WHERE id = ? LIMIT 1",
            (entity_id,),
            fetch_one=True
        )
        return row is not None

    def count(self) -> int:
        """Count total entities."""
        from ..db.queries import execute_query

        row = execute_query(f"SELECT COUNT(*) as count FROM {self.table_name}", fetch_one=True)
        return row['count'] if row else 0
