"""Base repository for Doc Store infrastructure.

Provides common repository patterns and utilities.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
from ..adapters.database_adapter import DatabaseAdapter

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Base repository with common database operations."""

    def __init__(self, db_adapter: DatabaseAdapter):
        """Initialize repository with database adapter.

        Args:
            db_adapter: Database adapter instance
        """
        self.db_adapter = db_adapter

    @abstractmethod
    def table_name(self) -> str:
        """Return the table name for this repository."""
        pass

    def health_check(self) -> Dict[str, Any]:
        """Check repository health by testing database connectivity.

        Returns:
            Health status dictionary
        """
        return self.db_adapter.health_check()

    def table_exists(self) -> bool:
        """Check if the repository's table exists.

        Returns:
            True if table exists, False otherwise
        """
        return self.db_adapter.table_exists(self.table_name())

    def get_table_info(self) -> List[Dict[str, Any]]:
        """Get table structure information.

        Returns:
            List of column information
        """
        return self.db_adapter.get_table_info(self.table_name())
