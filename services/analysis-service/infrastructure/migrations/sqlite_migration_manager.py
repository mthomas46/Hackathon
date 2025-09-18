"""SQLite Migration Manager - SQLite-specific migration implementation."""

import sqlite3
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from .migration_manager import MigrationManager
from .migration import MigrationExecutionContext, MigrationResult, MigrationStatus


class SQLiteMigrationManager(MigrationManager):
    """SQLite-specific migration manager."""

    def __init__(
        self,
        database_path: str,
        migration_table: str = "schema_migrations",
        dry_run: bool = False
    ):
        """Initialize SQLite migration manager."""
        super().__init__(dry_run=dry_run)
        self.database_path = Path(database_path)
        self.migration_table = migration_table
        self._connection_pool: Dict[int, sqlite3.Connection] = {}

    def _get_connection(self, task_id: Optional[int] = None) -> sqlite3.Connection:
        """Get database connection for current task."""
        if task_id is None:
            task_id = asyncio.current_task().get_loop()._task_id if asyncio.current_task() else 0

        if task_id not in self._connection_pool:
            # Ensure database directory exists
            self.database_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(
                str(self.database_path),
                isolation_level=None,  # We'll manage transactions manually
                check_same_thread=False
            )
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")

            self._connection_pool[task_id] = conn

        return self._connection_pool[task_id]

    def _close_connection(self, task_id: Optional[int] = None) -> None:
        """Close database connection for current task."""
        if task_id is None:
            task_id = asyncio.current_task().get_loop()._task_id if asyncio.current_task() else 0

        if task_id in self._connection_pool:
            conn = self._connection_pool[task_id]
            conn.close()
            del self._connection_pool[task_id]

    async def initialize_migration_table(self) -> None:
        """Initialize the migration tracking table."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Create migration table if it doesn't exist
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.migration_table} (
                    migration_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    migration_type TEXT NOT NULL,
                    executed_at TIMESTAMP NOT NULL,
                    duration_seconds REAL NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    rollback_available BOOLEAN NOT NULL DEFAULT 0,
                    checksum TEXT,
                    metadata TEXT
                )
            """)

            # Create indexes for better performance
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_migrations_executed_at
                ON {self.migration_table} (executed_at)
            """)

            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_migrations_status
                ON {self.migration_table} (status)
            """)

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._close_connection()

    async def load_migration_state(self) -> None:
        """Load migration execution state from database."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Get all completed migrations
            cursor.execute(f"""
                SELECT migration_id FROM {self.migration_table}
                WHERE status = ?
                ORDER BY executed_at
            """, (MigrationStatus.COMPLETED.value,))

            executed_migration_ids = [row[0] for row in cursor.fetchall()]
            self.executed_migrations = set(executed_migration_ids)

        except Exception as e:
            print(f"Warning: Failed to load migration state: {e}")
        finally:
            self._close_connection()

    async def save_migration_result(self, result: MigrationResult) -> None:
        """Save migration execution result to database."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Insert or replace migration record
            cursor.execute(f"""
                INSERT OR REPLACE INTO {self.migration_table}
                (migration_id, name, version, migration_type, executed_at,
                 duration_seconds, status, error_message, rollback_available,
                 checksum, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.migration_id,
                self.migrations.get(result.migration_id, Migration()).name if result.migration_id in self.migrations else "Unknown",
                self.migrations.get(result.migration_id, Migration()).version if result.migration_id in self.migrations else "1.0.0",
                self.migrations.get(result.migration_id, Migration()).migration_type.value if result.migration_id in self.migrations else "schema",
                result.executed_at.isoformat(),
                result.duration_seconds,
                result.status.value,
                result.error_message,
                result.rollback_available,
                self._calculate_checksum(result.migration_id),
                str(result.metadata) if result.metadata else None
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._close_connection()

    def _calculate_checksum(self, migration_id: str) -> str:
        """Calculate checksum for migration."""
        import hashlib

        migration = self.migrations.get(migration_id)
        if migration:
            # Create a simple checksum based on migration content
            content = f"{migration.migration_id}{migration.name}{migration.version}"
            return hashlib.md5(content.encode()).hexdigest()

        return ""

    async def create_execution_context(self) -> MigrationExecutionContext:
        """Create execution context for migrations."""
        conn = self._get_connection()
        context = SQLiteMigrationExecutionContext(conn)
        return context

    async def execute_migration_with_tracking(
        self,
        migration_id: str
    ) -> MigrationResult:
        """Execute a migration with full tracking."""
        migration = self.get_migration(migration_id)
        if not migration:
            raise ValueError(f"Migration {migration_id} not found")

        context = await self.create_execution_context()
        start_time = asyncio.get_event_loop().time()

        try:
            # Execute migration
            result = await self.execute_migration(migration, context)

            # Save result to database
            await self.save_migration_result(result)

            return result

        except Exception as e:
            # Create failure result
            execution_time = asyncio.get_event_loop().time() - start_time
            failure_result = MigrationResult(
                migration_id=migration_id,
                status=MigrationStatus.FAILED,
                executed_at=datetime.utcnow(),
                duration_seconds=execution_time,
                error_message=str(e)
            )

            # Save failure result
            await self.save_migration_result(failure_result)

            raise e
        finally:
            self._close_connection()

    async def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration execution history."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT migration_id, name, version, migration_type, executed_at,
                       duration_seconds, status, error_message, rollback_available
                FROM {self.migration_table}
                ORDER BY executed_at DESC
            """)

            history = []
            for row in cursor.fetchall():
                history.append({
                    'migration_id': row[0],
                    'name': row[1],
                    'version': row[2],
                    'migration_type': row[3],
                    'executed_at': row[4],
                    'duration_seconds': row[5],
                    'status': row[6],
                    'error_message': row[7],
                    'rollback_available': row[8]
                })

            return history

        except Exception as e:
            print(f"Warning: Failed to get migration history: {e}")
            return []
        finally:
            self._close_connection()

    async def get_migration_status(self, migration_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific migration."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT migration_id, name, version, migration_type, executed_at,
                       duration_seconds, status, error_message, rollback_available
                FROM {self.migration_table}
                WHERE migration_id = ?
            """, (migration_id,))

            row = cursor.fetchone()
            if row:
                return {
                    'migration_id': row[0],
                    'name': row[1],
                    'version': row[2],
                    'migration_type': row[3],
                    'executed_at': row[4],
                    'duration_seconds': row[5],
                    'status': row[6],
                    'error_message': row[7],
                    'rollback_available': row[8]
                }

            return None

        except Exception as e:
            print(f"Warning: Failed to get migration status: {e}")
            return None
        finally:
            self._close_connection()

    async def rollback_migration_with_tracking(
        self,
        migration_id: str
    ) -> MigrationResult:
        """Rollback a migration with tracking."""
        migration = self.get_migration(migration_id)
        if not migration:
            raise ValueError(f"Migration {migration_id} not found")

        context = await self.create_execution_context()
        start_time = asyncio.get_event_loop().time()

        try:
            # Execute rollback
            result = await self.rollback_migration(migration, context)

            # Update database record
            await self.save_migration_result(result)

            return result

        except Exception as e:
            # Create failure result
            execution_time = asyncio.get_event_loop().time() - start_time
            failure_result = MigrationResult(
                migration_id=migration_id,
                status=MigrationStatus.FAILED,
                executed_at=datetime.utcnow(),
                duration_seconds=execution_time,
                error_message=f"Rollback failed: {str(e)}"
            )

            # Save failure result
            await self.save_migration_result(failure_result)

            raise e
        finally:
            self._close_connection()

    async def cleanup_old_migrations(self, days_to_keep: int = 365) -> int:
        """Clean up old migration records."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Delete old records but keep the most recent of each migration
            cursor.execute(f"""
                DELETE FROM {self.migration_table}
                WHERE migration_id IN (
                    SELECT migration_id
                    FROM {self.migration_table}
                    WHERE executed_at < datetime('now', '-{days_to_keep} days')
                    AND migration_id NOT IN (
                        SELECT migration_id
                        FROM {self.migration_table}
                        WHERE status = 'completed'
                        GROUP BY migration_id
                        HAVING executed_at = MAX(executed_at)
                    )
                )
            """)

            deleted_count = cursor.rowcount
            conn.commit()

            return deleted_count

        except Exception as e:
            conn.rollback()
            print(f"Warning: Failed to cleanup old migrations: {e}")
            return 0
        finally:
            self._close_connection()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        try:
            # Test database connection
            conn = self._get_connection()

            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()

            # Get migration table info
            cursor.execute(f"SELECT COUNT(*) FROM {self.migration_table}")
            migration_count = cursor.fetchone()[0]

            self._close_connection()

            return {
                'status': 'healthy',
                'database_path': str(self.database_path),
                'database_exists': self.database_path.exists(),
                'migration_table_exists': True,
                'total_migrations_recorded': migration_count,
                'registered_migrations': len(self.migrations),
                'executed_migrations': len(self.executed_migrations)
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_path': str(self.database_path)
            }


class SQLiteMigrationExecutionContext(MigrationExecutionContext):
    """SQLite-specific migration execution context."""

    def __init__(self, connection: sqlite3.Connection):
        """Initialize SQLite execution context."""
        super().__init__(connection=connection)
        self._transaction_active = False

    async def execute_sql(self, sql: str, params: Optional[Tuple] = None) -> Any:
        """Execute SQL statement with SQLite-specific handling."""
        self._executed_statements.append(sql)

        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            # Get affected rows for data migrations
            if sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                affected_rows = cursor.rowcount
                self.add_metadata('affected_rows', affected_rows)

            return cursor

        except Exception as e:
            raise e

    async def execute_many(self, sql: str, params_list: List[Tuple]) -> Any:
        """Execute SQL statement with multiple parameter sets."""
        self._executed_statements.append(f"{sql} [BATCH: {len(params_list)} records]")

        cursor = self.connection.cursor()
        try:
            cursor.executemany(sql, params_list)

            # Get affected rows
            affected_rows = cursor.rowcount
            self.add_metadata('affected_rows', affected_rows)

            return cursor

        except Exception as e:
            raise e

    def begin_transaction(self) -> None:
        """Begin transaction."""
        if not self._transaction_active:
            self.connection.execute("BEGIN")
            self._transaction_active = True

    def commit_transaction(self) -> None:
        """Commit transaction."""
        if self._transaction_active:
            self.connection.commit()
            self._transaction_active = False

    def rollback_transaction(self) -> None:
        """Rollback transaction."""
        if self._transaction_active:
            self.connection.rollback()
            self._transaction_active = False
