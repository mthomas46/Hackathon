"""Database connection management for Doc Store service.

Provides connection pooling and secure database access.
"""
import os
import sqlite3
from typing import Optional, Any
from contextlib import contextmanager


def _validate_db_path(db_path: str) -> str:
    """Validate database path to prevent directory traversal attacks."""
    if any(char in db_path for char in ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']):
        return "services/doc_store/db.sqlite3"
    return db_path


def _validate_connection_pool_size(size_str: str) -> int:
    """Safely validate connection pool size."""
    try:
        size = int(size_str)
        if size < 1 or size > 20:
            return 5
        return size
    except (ValueError, TypeError):
        return 5


_DB_PATH = _validate_db_path(os.environ.get("DOCSTORE_DB", "services/doc_store/db.sqlite3"))
_CONNECTION_POOL_SIZE = _validate_connection_pool_size(os.environ.get("DOCSTORE_CONNECTION_POOL_SIZE", "5"))
_connection_pool = []


def get_doc_store_db_path() -> str:
    """Get the database path for doc_store service."""
    return _DB_PATH


def get_doc_store_connection() -> sqlite3.Connection:
    """Get database connection from pool with performance optimizations."""
    global _connection_pool

    # Try to get existing connection
    if _connection_pool:
        conn = _connection_pool.pop()
        try:
            # Test if connection is still valid
            conn.execute("SELECT 1").fetchone()
            return conn
        except sqlite3.Error:
            # Connection is dead, create new one
            pass

    # Create new connection with optimizations
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
    conn.execute("PRAGMA synchronous=NORMAL")  # Balance between performance and safety
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
    conn.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects

    return conn


def return_doc_store_connection(conn: sqlite3.Connection) -> None:
    """Return connection to pool."""
    global _connection_pool

    if len(_connection_pool) < _CONNECTION_POOL_SIZE:
        try:
            # Test connection before returning to pool
            conn.execute("SELECT 1").fetchone()
            _connection_pool.append(conn)
        except sqlite3.Error:
            # Connection is dead, don't return to pool
            conn.close()
    else:
        conn.close()


@contextmanager
def doc_store_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = get_doc_store_connection()
        yield conn
    finally:
        if conn:
            return_doc_store_connection(conn)
