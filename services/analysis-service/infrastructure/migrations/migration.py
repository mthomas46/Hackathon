"""Database Migration - Core migration abstractions and interfaces."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field


class MigrationStatus(Enum):
    """Migration execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class MigrationType(Enum):
    """Types of database migrations."""
    SCHEMA = "schema"
    DATA = "data"
    INDEX = "index"
    CONSTRAINT = "constraint"
    VIEW = "view"
    FUNCTION = "function"
    TRIGGER = "trigger"


@dataclass
class MigrationResult:
    """Result of a migration execution."""
    migration_id: str
    status: MigrationStatus
    executed_at: datetime
    duration_seconds: float
    error_message: Optional[str] = None
    rollback_available: bool = False
    affected_rows: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize result."""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'migration_id': self.migration_id,
            'status': self.status.value,
            'executed_at': self.executed_at.isoformat(),
            'duration_seconds': self.duration_seconds,
            'error_message': self.error_message,
            'rollback_available': self.rollback_available,
            'affected_rows': self.affected_rows,
            'metadata': self.metadata
        }


@dataclass
class MigrationDependency:
    """Migration dependency definition."""
    migration_id: str
    description: str
    required: bool = True


class Migration(ABC):
    """Abstract base class for database migrations."""

    def __init__(
        self,
        migration_id: str,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        migration_type: MigrationType = MigrationType.SCHEMA,
        dependencies: Optional[List[MigrationDependency]] = None
    ):
        """Initialize migration."""
        self.migration_id = migration_id
        self.name = name
        self.description = description or f"Migration: {name}"
        self.version = version
        self.migration_type = migration_type
        self.dependencies = dependencies or []
        self.created_at = datetime.utcnow()

        # Execution tracking
        self._execution_result: Optional[MigrationResult] = None

    @abstractmethod
    async def up(self, context: 'MigrationExecutionContext') -> None:
        """Execute the migration (upgrade)."""
        pass

    @abstractmethod
    async def down(self, context: 'MigrationExecutionContext') -> None:
        """Rollback the migration (downgrade)."""
        pass

    @abstractmethod
    def is_reversible(self) -> bool:
        """Check if migration can be rolled back."""
        pass

    def get_dependencies(self) -> List[MigrationDependency]:
        """Get migration dependencies."""
        return self.dependencies.copy()

    def has_dependency(self, migration_id: str) -> bool:
        """Check if migration has a specific dependency."""
        return any(dep.migration_id == migration_id for dep in self.dependencies)

    def get_required_dependencies(self) -> List[str]:
        """Get list of required dependency IDs."""
        return [dep.migration_id for dep in self.dependencies if dep.required]

    def set_execution_result(self, result: MigrationResult) -> None:
        """Set execution result."""
        self._execution_result = result

    def get_execution_result(self) -> Optional[MigrationResult]:
        """Get execution result."""
        return self._execution_result

    def get_metadata(self) -> Dict[str, Any]:
        """Get migration metadata."""
        return {
            'id': self.migration_id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'type': self.migration_type.value,
            'dependencies': [dep.migration_id for dep in self.dependencies],
            'created_at': self.created_at.isoformat(),
            'reversible': self.is_reversible()
        }


class SchemaMigration(Migration):
    """Schema migration for table structure changes."""

    def __init__(
        self,
        migration_id: str,
        name: str,
        up_sql: str,
        down_sql: Optional[str] = None,
        **kwargs
    ):
        """Initialize schema migration."""
        super().__init__(
            migration_id,
            name,
            migration_type=MigrationType.SCHEMA,
            **kwargs
        )
        self.up_sql = up_sql
        self.down_sql = down_sql

    async def up(self, context: 'MigrationExecutionContext') -> None:
        """Execute schema migration."""
        await context.execute_sql(self.up_sql)

    async def down(self, context: 'MigrationExecutionContext') -> None:
        """Rollback schema migration."""
        if self.down_sql:
            await context.execute_sql(self.down_sql)
        else:
            raise NotImplementedError(f"Migration {self.migration_id} is not reversible")

    def is_reversible(self) -> bool:
        """Check if migration is reversible."""
        return self.down_sql is not None


class DataMigration(Migration):
    """Data migration for data transformations."""

    def __init__(
        self,
        migration_id: str,
        name: str,
        **kwargs
    ):
        """Initialize data migration."""
        super().__init__(
            migration_id,
            name,
            migration_type=MigrationType.DATA,
            **kwargs
        )

    async def up(self, context: 'MigrationExecutionContext') -> None:
        """Execute data migration."""
        # Default implementation - subclasses should override
        pass

    async def down(self, context: 'MigrationExecutionContext') -> None:
        """Rollback data migration."""
        # Default implementation - subclasses should override
        raise NotImplementedError(f"Data migration {self.migration_id} rollback not implemented")

    def is_reversible(self) -> bool:
        """Data migrations are generally not reversible."""
        return False


class IndexMigration(Migration):
    """Index migration for performance optimizations."""

    def __init__(
        self,
        migration_id: str,
        name: str,
        create_sql: str,
        drop_sql: str,
        **kwargs
    ):
        """Initialize index migration."""
        super().__init__(
            migration_id,
            name,
            migration_type=MigrationType.INDEX,
            **kwargs
        )
        self.create_sql = create_sql
        self.drop_sql = drop_sql

    async def up(self, context: 'MigrationExecutionContext') -> None:
        """Create index."""
        await context.execute_sql(self.create_sql)

    async def down(self, context: 'MigrationExecutionContext') -> None:
        """Drop index."""
        await context.execute_sql(self.drop_sql)

    def is_reversible(self) -> bool:
        """Index migrations are reversible."""
        return True


class MigrationExecutionContext:
    """Context for migration execution."""

    def __init__(self, connection=None, transaction_manager=None):
        """Initialize execution context."""
        self.connection = connection
        self.transaction_manager = transaction_manager
        self._executed_statements: List[str] = []
        self._execution_metadata: Dict[str, Any] = {}

    async def execute_sql(self, sql: str, params: Optional[tuple] = None) -> Any:
        """Execute SQL statement."""
        self._executed_statements.append(sql)

        if self.connection:
            cursor = self.connection.cursor()
            try:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)

                # Commit if not in transaction
                if not self.transaction_manager:
                    self.connection.commit()

                return cursor
            except Exception as e:
                if not self.transaction_manager:
                    self.connection.rollback()
                raise e

        # For testing - just track the statement
        return None

    async def execute_many(self, sql: str, params_list: List[tuple]) -> Any:
        """Execute SQL statement with multiple parameter sets."""
        self._executed_statements.append(f"{sql} [BATCH: {len(params_list)} records]")

        if self.connection:
            cursor = self.connection.cursor()
            try:
                cursor.executemany(sql, params_list)

                # Commit if not in transaction
                if not self.transaction_manager:
                    self.connection.commit()

                return cursor
            except Exception as e:
                if not self.transaction_manager:
                    self.connection.rollback()
                raise e

        return None

    def add_metadata(self, key: str, value: Any) -> None:
        """Add execution metadata."""
        self._execution_metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get execution metadata."""
        return self._execution_metadata.get(key, default)

    def get_executed_statements(self) -> List[str]:
        """Get list of executed SQL statements."""
        return self._executed_statements.copy()

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        return {
            'executed_statements_count': len(self._executed_statements),
            'executed_statements': self._executed_statements,
            'metadata': self._execution_metadata
        }


class MigrationFactory:
    """Factory for creating migration instances."""

    @staticmethod
    def create_migration(
        migration_class: Type[Migration],
        migration_id: str,
        **kwargs
    ) -> Migration:
        """Create migration instance."""
        return migration_class(migration_id, **kwargs)

    @staticmethod
    def create_schema_migration(
        migration_id: str,
        name: str,
        up_sql: str,
        down_sql: Optional[str] = None,
        **kwargs
    ) -> SchemaMigration:
        """Create schema migration."""
        return SchemaMigration(migration_id, name, up_sql, down_sql, **kwargs)

    @staticmethod
    def create_data_migration(
        migration_id: str,
        name: str,
        **kwargs
    ) -> DataMigration:
        """Create data migration."""
        return DataMigration(migration_id, name, **kwargs)

    @staticmethod
    def create_index_migration(
        migration_id: str,
        name: str,
        create_sql: str,
        drop_sql: str,
        **kwargs
    ) -> IndexMigration:
        """Create index migration."""
        return IndexMigration(migration_id, name, create_sql, drop_sql, **kwargs)
