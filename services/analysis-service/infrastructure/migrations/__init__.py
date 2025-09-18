"""Database Migrations - Schema versioning and data migration infrastructure."""

from .migration import Migration, MigrationResult, MigrationStatus
from .migration_manager import MigrationManager, MigrationExecutionContext
from .sqlite_migration_manager import SQLiteMigrationManager
from .postgres_migration_manager import PostgreSQLMigrationManager
from .migration_discovery import MigrationDiscovery
from .migration_validator import MigrationValidator, ValidationResult
from .migration_rollback import MigrationRollbackManager
from .migration_state import MigrationStateManager
from .migration_templates import MigrationTemplateGenerator

__all__ = [
    'Migration',
    'MigrationResult',
    'MigrationStatus',
    'MigrationManager',
    'MigrationExecutionContext',
    'SQLiteMigrationManager',
    'PostgreSQLMigrationManager',
    'MigrationDiscovery',
    'MigrationValidator',
    'ValidationResult',
    'MigrationRollbackManager',
    'MigrationStateManager',
    'MigrationTemplateGenerator'
]
