"""Database migrations for Doc Store.

Handles database schema migrations and version management.
"""

import logging
from typing import List, Dict, Any
from .connection import get_db_connection

logger = logging.getLogger(__name__)


def get_current_schema_version() -> int:
    """Get the current database schema version.

    Returns:
        Current schema version number
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at REAL DEFAULT (strftime('%s', 'now')),
                    description TEXT
                )
            """)

            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0

    except Exception as e:
        logger.error(f"Failed to get schema version: {e}")
        return 0


def record_migration(version: int, description: str) -> None:
    """Record a completed migration.

    Args:
        version: Migration version number
        description: Description of the migration
    """
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                (version, description)
            )
            conn.commit()
            logger.info(f"Recorded migration v{version}: {description}")
    except Exception as e:
        logger.error(f"Failed to record migration v{version}: {e}")


def run_migrations() -> None:
    """Run all pending database migrations.

    Executes migrations in order, skipping those already applied.
    """
    current_version = get_current_schema_version()
    logger.info(f"Current schema version: {current_version}")

    migrations = [
        (1, "Initial schema setup", _migration_v1_initial_schema),
        (2, "Add document versioning", _migration_v2_add_versioning),
        (3, "Add full-text search indexes", _migration_v3_add_search_indexes),
        (4, "Add document metadata indexes", _migration_v4_add_metadata_indexes),
    ]

    for version, description, migration_func in migrations:
        if version > current_version:
            logger.info(f"Applying migration v{version}: {description}")
            try:
                migration_func()
                record_migration(version, description)
                logger.info(f"Successfully applied migration v{version}")
            except Exception as e:
                logger.error(f"Failed to apply migration v{version}: {e}")
                raise


def _migration_v1_initial_schema() -> None:
    """Migration v1: Initial schema setup."""
    with get_db_connection() as conn:
        # Documents table
        conn.execute("""
            CREATE TABLE documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT,
                tags TEXT,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)

        # Cache table
        conn.execute("""
            CREATE TABLE cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at REAL NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)

        # Schema version table
        conn.execute("""
            CREATE TABLE schema_version (
                version INTEGER PRIMARY KEY,
                applied_at REAL DEFAULT (strftime('%s', 'now')),
                description TEXT
            )
        """)

        conn.commit()


def _migration_v2_add_versioning() -> None:
    """Migration v2: Add document versioning support."""
    with get_db_connection() as conn:
        # Document versions table
        conn.execute("""
            CREATE TABLE document_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                tags TEXT,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # Add version column to documents table
        conn.execute("ALTER TABLE documents ADD COLUMN version INTEGER DEFAULT 1")

        # Create indexes
        conn.execute("CREATE INDEX idx_document_versions_doc_id ON document_versions(document_id)")
        conn.execute("CREATE INDEX idx_document_versions_version ON document_versions(version)")

        conn.commit()


def _migration_v3_add_search_indexes() -> None:
    """Migration v3: Add full-text search capabilities."""
    with get_db_connection() as conn:
        # Create FTS5 virtual table for full-text search
        conn.execute("""
            CREATE VIRTUAL TABLE documents_fts USING fts5(
                content, metadata, tags,
                content=documents, content_rowid=id
            )
        """)

        # Populate the FTS table
        conn.execute("""
            INSERT INTO documents_fts(rowid, content, metadata, tags)
            SELECT id, content, metadata, tags FROM documents
        """)

        # Create triggers to keep FTS table in sync
        conn.execute("""
            CREATE TRIGGER documents_fts_insert AFTER INSERT ON documents
            BEGIN
                INSERT INTO documents_fts(rowid, content, metadata, tags)
                VALUES (new.id, new.content, new.metadata, new.tags);
            END
        """)

        conn.execute("""
            CREATE TRIGGER documents_fts_delete AFTER DELETE ON documents
            BEGIN
                DELETE FROM documents_fts WHERE rowid = old.id;
            END
        """)

        conn.execute("""
            CREATE TRIGGER documents_fts_update AFTER UPDATE ON documents
            BEGIN
                UPDATE documents_fts SET
                    content = new.content,
                    metadata = new.metadata,
                    tags = new.tags
                WHERE rowid = new.id;
            END
        """)

        conn.commit()


def _migration_v4_add_metadata_indexes() -> None:
    """Migration v4: Add metadata indexing for better query performance."""
    with get_db_connection() as conn:
        # Create GIN-style indexes for JSON metadata (using JSON functions)
        conn.execute("CREATE INDEX idx_documents_metadata ON documents(json_extract(metadata, '$.category'))")
        conn.execute("CREATE INDEX idx_documents_tags ON documents(tags)")

        # Add performance indexes
        conn.execute("CREATE INDEX idx_documents_composite ON documents(created_at, updated_at)")
        conn.execute("CREATE INDEX idx_cache_composite ON cache(expires_at, created_at)")

        conn.commit()


def rollback_migration(version: int) -> None:
    """Rollback a specific migration version.

    Args:
        version: Migration version to rollback

    Warning:
        This is a destructive operation that may result in data loss.
    """
    logger.warning(f"Rolling back migration v{version} - this may result in data loss!")

    rollback_funcs = {
        1: _rollback_v1_initial_schema,
        2: _rollback_v2_add_versioning,
        3: _rollback_v3_add_search_indexes,
        4: _rollback_v4_add_metadata_indexes,
    }

    if version in rollback_funcs:
        try:
            rollback_funcs[version]()
            # Remove the migration record
            with get_db_connection() as conn:
                conn.execute("DELETE FROM schema_version WHERE version = ?", (version,))
                conn.commit()
            logger.info(f"Successfully rolled back migration v{version}")
        except Exception as e:
            logger.error(f"Failed to rollback migration v{version}: {e}")
            raise
    else:
        raise ValueError(f"No rollback function available for migration v{version}")


def _rollback_v1_initial_schema() -> None:
    """Rollback migration v1."""
    with get_db_connection() as conn:
        conn.execute("DROP TABLE IF EXISTS cache")
        conn.execute("DROP TABLE IF EXISTS documents")
        conn.execute("DROP TABLE IF EXISTS schema_version")
        conn.commit()


def _rollback_v2_add_versioning() -> None:
    """Rollback migration v2."""
    with get_db_connection() as conn:
        conn.execute("DROP TABLE IF EXISTS document_versions")
        conn.execute("ALTER TABLE documents DROP COLUMN version")
        conn.commit()


def _rollback_v3_add_search_indexes() -> None:
    """Rollback migration v3."""
    with get_db_connection() as conn:
        conn.execute("DROP TRIGGER IF EXISTS documents_fts_insert")
        conn.execute("DROP TRIGGER IF EXISTS documents_fts_delete")
        conn.execute("DROP TRIGGER IF EXISTS documents_fts_update")
        conn.execute("DROP TABLE IF EXISTS documents_fts")
        conn.commit()


def _rollback_v4_add_metadata_indexes() -> None:
    """Rollback migration v4."""
    with get_db_connection() as conn:
        # SQLite doesn't support DROP INDEX IF EXISTS, so we need to check first
        indexes_to_drop = [
            'idx_documents_metadata',
            'idx_documents_tags',
            'idx_documents_composite',
            'idx_cache_composite'
        ]

        for index_name in indexes_to_drop:
            try:
                conn.execute(f"DROP INDEX {index_name}")
            except:
                pass  # Index might not exist

        conn.commit()
