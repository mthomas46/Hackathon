"""Database adapter for Doc Store infrastructure.

Provides a clean interface to database operations, abstracting
the underlying database implementation details.
"""

import sqlite3
from typing import Any, Dict, List, Optional
from contextlib import contextmanager


class DatabaseAdapter:
    """Adapter for database operations in Doc Store."""

    def __init__(self, db_path: str = "db.sqlite3"):
        """Initialize database adapter.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup.

        Yields:
            SQLite connection object

        Raises:
            sqlite3.Error: If database connection fails
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result rows as dictionaries

        Raises:
            sqlite3.Error: If query execution fails
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows

        Raises:
            sqlite3.Error: If query execution fails
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        result = self.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return len(result) > 0

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get information about table columns.

        Args:
            table_name: Name of the table

        Returns:
            List of column information dictionaries
        """
        return self.execute_query(f"PRAGMA table_info({table_name})")

    def health_check(self) -> Dict[str, Any]:
        """Perform database health check.

        Returns:
            Health status dictionary
        """
        try:
            # Simple query to test connectivity
            result = self.execute_query("SELECT 1 as test")
            return {
                "status": "healthy",
                "database_type": "sqlite",
                "connection_test": result[0]["test"] == 1
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_type": "sqlite"
            }
