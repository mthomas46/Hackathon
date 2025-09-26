"""Database infrastructure for Doc Store service.

Handles database connections, migrations, and schema management.
"""

from .connection import get_db_connection, init_database
from .migrations import run_migrations

__all__ = [
    "get_db_connection",
    "init_database",
    "run_migrations",
]
