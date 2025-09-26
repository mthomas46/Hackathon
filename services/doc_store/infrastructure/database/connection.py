"""Database connection management for Doc Store.

Provides database connection pooling and lifecycle management.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator, Any
from ..config.settings import get_database_config


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection with automatic cleanup.

    Yields:
        SQLite database connection

    Raises:
        sqlite3.Error: If connection fails
    """
    config = get_database_config()
    conn = None

    try:
        conn = sqlite3.connect(
            config["path"],
            timeout=config["timeout"]
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")

        yield conn

    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def init_database() -> None:
    """Initialize database schema and tables.

    Creates all necessary tables and indexes for the Doc Store service.
    This function should be called during service startup.
    """
    with get_db_connection() as conn:
        # Create documents table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT,  -- JSON string
                tags TEXT,      -- JSON string
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)

        # Create cache table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at REAL NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)

        # Create indexes for performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_updated ON documents(updated_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")

        conn.commit()


def check_database_connection() -> bool:
    """Check if database connection is working.

    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as health_check")
            result = cursor.fetchone()
            return result[0] == 1
    except Exception:
        return False


def get_database_stats() -> dict[str, Any]:
    """Get database statistics and health information.

    Returns:
        Dictionary with database statistics
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get table counts
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cache")
            cache_count = cursor.fetchone()[0]

            # Get database file size (approximate)
            config = get_database_config()
            import os
            db_size = os.path.getsize(config["path"]) if os.path.exists(config["path"]) else 0

            return {
                "documents_count": doc_count,
                "cache_entries_count": cache_count,
                "database_size_bytes": db_size,
                "connection_healthy": True
            }

    except Exception as e:
        return {
            "error": str(e),
            "connection_healthy": False
        }
