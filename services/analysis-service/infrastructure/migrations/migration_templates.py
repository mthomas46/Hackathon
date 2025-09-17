"""Migration Templates - Generates migration templates and boilerplate code."""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class MigrationTemplateGenerator:
    """Generates migration templates and boilerplate code."""

    def __init__(self, template_directory: Optional[str] = None):
        """Initialize template generator."""
        if template_directory:
            self.template_dir = Path(template_directory)
        else:
            self.template_dir = Path(__file__).parent / "templates"

        self.template_dir.mkdir(parents=True, exist_ok=True)

    def generate_schema_migration(
        self,
        migration_id: str,
        name: str,
        table_name: Optional[str] = None,
        operation: str = "create_table",
        output_dir: str = "migrations"
    ) -> str:
        """Generate a schema migration template."""
        template_vars = {
            'migration_id': migration_id,
            'name': name,
            'table_name': table_name or migration_id.split('_')[-1],
            'operation': operation,
            'timestamp': datetime.utcnow().strftime('%Y%m%d_%H%M%S'),
            'class_name': self._to_class_name(migration_id)
        }

        template = self._get_schema_template(operation)
        migration_code = template.format(**template_vars)

        # Write to file
        output_path = Path(output_dir) / f"{migration_id}.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_code)

        return str(output_path)

    def generate_data_migration(
        self,
        migration_id: str,
        name: str,
        description: str = "",
        output_dir: str = "migrations"
    ) -> str:
        """Generate a data migration template."""
        template_vars = {
            'migration_id': migration_id,
            'name': name,
            'description': description,
            'timestamp': datetime.utcnow().strftime('%Y%m%d_%H%M%S'),
            'class_name': self._to_class_name(migration_id)
        }

        template = self._get_data_template()
        migration_code = template.format(**template_vars)

        # Write to file
        output_path = Path(output_dir) / f"{migration_id}.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_code)

        return str(output_path)

    def generate_index_migration(
        self,
        migration_id: str,
        name: str,
        table_name: str,
        columns: list,
        index_name: Optional[str] = None,
        output_dir: str = "migrations"
    ) -> str:
        """Generate an index migration template."""
        if not index_name:
            index_name = f"idx_{table_name}_{'_'.join(columns)}"

        template_vars = {
            'migration_id': migration_id,
            'name': name,
            'table_name': table_name,
            'columns': ', '.join(f"'{col}'" for col in columns),
            'index_name': index_name,
            'timestamp': datetime.utcnow().strftime('%Y%m%d_%H%M%S'),
            'class_name': self._to_class_name(migration_id)
        }

        template = self._get_index_template()
        migration_code = template.format(**template_vars)

        # Write to file
        output_path = Path(output_dir) / f"{migration_id}.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_code)

        return str(output_path)

    def generate_sql_migration(
        self,
        migration_id: str,
        name: str,
        up_sql: str,
        down_sql: Optional[str] = None,
        output_dir: str = "migrations"
    ) -> str:
        """Generate a SQL migration file."""
        template_vars = {
            'migration_id': migration_id,
            'name': name,
            'up_sql': up_sql,
            'down_sql': down_sql or "-- No rollback SQL provided",
            'timestamp': datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        }

        template = self._get_sql_template()
        migration_sql = template.format(**template_vars)

        # Write to file
        output_path = Path(output_dir) / f"{migration_id}.sql"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_sql)

        return str(output_path)

    def _get_schema_template(self, operation: str) -> str:
        """Get schema migration template."""
        templates = {
            'create_table': '''"""Migration: {name}"""

from infrastructure.migrations.migration import SchemaMigration


class {class_name}(SchemaMigration):
    """{name}"""

    def __init__(self):
        """Initialize migration."""
        up_sql = """
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        down_sql = """
        DROP TABLE {table_name};
        """

        super().__init__(
            migration_id="{migration_id}",
            name="{name}",
            up_sql=up_sql.strip(),
            down_sql=down_sql.strip()
        )
''',
            'add_column': '''"""Migration: {name}"""

from infrastructure.migrations.migration import SchemaMigration


class {class_name}(SchemaMigration):
    """{name}"""

    def __init__(self):
        """Initialize migration."""
        up_sql = """
        ALTER TABLE {table_name} ADD COLUMN new_column VARCHAR(255);
        """

        down_sql = """
        ALTER TABLE {table_name} DROP COLUMN new_column;
        """

        super().__init__(
            migration_id="{migration_id}",
            name="{name}",
            up_sql=up_sql.strip(),
            down_sql=down_sql.strip()
        )
''',
            'drop_table': '''"""Migration: {name}"""

from infrastructure.migrations.migration import SchemaMigration


class {class_name}(SchemaMigration):
    """{name}"""

    def __init__(self):
        """Initialize migration."""
        up_sql = """
        DROP TABLE {table_name};
        """

        # Note: This migration is not reversible
        super().__init__(
            migration_id="{migration_id}",
            name="{name}",
            up_sql=up_sql.strip(),
            down_sql=None
        )
'''
        }

        return templates.get(operation, templates['create_table'])

    def _get_data_template(self) -> str:
        """Get data migration template."""
        return '''"""Migration: {name}"""

import asyncio
from infrastructure.migrations.migration import DataMigration, MigrationExecutionContext


class {class_name}(DataMigration):
    """{name} - {description}"""

    def __init__(self):
        """Initialize migration."""
        super().__init__(
            migration_id="{migration_id}",
            name="{name}",
            description="{description}"
        )

    async def up(self, context: MigrationExecutionContext) -> None:
        """Execute data migration."""
        # TODO: Implement data migration logic
        # Example:
        # await context.execute_sql("""
        #     UPDATE users SET status = 'active' WHERE status IS NULL;
        # """)

        print(f"Executing data migration: {self.name}")

    async def down(self, context: MigrationExecutionContext) -> None:
        """Rollback data migration."""
        # TODO: Implement rollback logic
        # Note: Data migrations are often not reversible
        print(f"Rolling back data migration: {self.name}")
        raise NotImplementedError("Data migration rollback not implemented")
'''

    def _get_index_template(self) -> str:
        """Get index migration template."""
        return '''"""Migration: {name}"""

from infrastructure.migrations.migration import IndexMigration


class {class_name}(IndexMigration):
    """{name}"""

    def __init__(self):
        """Initialize migration."""
        create_sql = """
        CREATE INDEX {index_name} ON {table_name} ({columns});
        """

        drop_sql = """
        DROP INDEX {index_name};
        """

        super().__init__(
            migration_id="{migration_id}",
            name="{name}",
            create_sql=create_sql.strip(),
            drop_sql=drop_sql.strip()
        )
'''

    def _get_sql_template(self) -> str:
        """Get SQL migration template."""
        return '''-- Migration: {name}
-- ID: {migration_id}
-- Generated: {timestamp}

-- UP
{up_sql}

-- DOWN
{down_sql}
'''

    def _to_class_name(self, migration_id: str) -> str:
        """Convert migration ID to class name."""
        parts = migration_id.split('_')
        return ''.join(word.capitalize() for word in parts)

    def list_available_templates(self) -> Dict[str, str]:
        """List available migration templates."""
        return {
            'schema:create_table': 'Create a new database table',
            'schema:add_column': 'Add a column to an existing table',
            'schema:drop_table': 'Drop an existing table',
            'data:migration': 'Transform existing data',
            'index:create': 'Create a database index',
            'sql:migration': 'Raw SQL migration'
        }

    def generate_migration_from_template(
        self,
        template_type: str,
        migration_id: str,
        name: str,
        **kwargs
    ) -> str:
        """Generate migration from template type."""
        if template_type.startswith('schema:'):
            operation = template_type.split(':', 1)[1]
            return self.generate_schema_migration(
                migration_id, name, operation=operation, **kwargs
            )
        elif template_type == 'data:migration':
            return self.generate_data_migration(migration_id, name, **kwargs)
        elif template_type == 'index:create':
            return self.generate_index_migration(migration_id, name, **kwargs)
        elif template_type == 'sql:migration':
            return self.generate_sql_migration(migration_id, name, **kwargs)
        else:
            raise ValueError(f"Unknown template type: {template_type}")


class MigrationCommandGenerator:
    """Generates command-line migration commands."""

    @staticmethod
    def generate_create_command(
        migration_type: str,
        name: str,
        output_dir: str = "migrations"
    ) -> str:
        """Generate migration creation command."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        migration_id = f"{timestamp}_{name.lower().replace(' ', '_')}"

        return f"""# Create a new {migration_type} migration
python -m infrastructure.migrations.cli create \\
    --type {migration_type} \\
    --name "{name}" \\
    --id {migration_id} \\
    --output {output_dir}

# Or using the migration manager directly
from infrastructure.migrations.migration_templates import MigrationTemplateGenerator

generator = MigrationTemplateGenerator()
file_path = generator.generate_migration_from_template(
    "{migration_type}:migration",
    "{migration_id}",
    "{name}"
)
print(f"Migration created: {{file_path}}")
"""

    @staticmethod
    def generate_execute_command(
        migration_ids: Optional[list] = None,
        dry_run: bool = False
    ) -> str:
        """Generate migration execution command."""
        args = []
        if migration_ids:
            args.extend([f"--migration {mid}" for mid in migration_ids])
        if dry_run:
            args.append("--dry-run")

        return f"""# Execute migrations
python -m infrastructure.migrations.cli execute {" ".join(args)}

# Or using the migration manager directly
from infrastructure.migrations.sqlite_migration_manager import SQLiteMigrationManager

manager = SQLiteMigrationManager("database.db")
await manager.initialize_migration_table()

# Load and execute migrations
from infrastructure.migrations.migration_discovery import MigrationDiscovery
discovery = MigrationDiscovery()
migrations = discovery.discover_migrations()
manager.register_migrations(migrations)

results = await manager.execute_pending_migrations()
for result in results:
    print(f"Executed: {{result.migration_id}} - {{result.status}}")
"""

    @staticmethod
    def generate_status_command() -> str:
        """Generate migration status command."""
        return """# Check migration status
python -m infrastructure.migrations.cli status

# Or using the migration manager directly
from infrastructure.migrations.sqlite_migration_manager import SQLiteMigrationManager

manager = SQLiteMigrationManager("database.db")
await manager.initialize_migration_table()
await manager.load_migration_state()

status = manager.get_execution_stats()
print(f"Total migrations: {status['total_migrations']}")
print(f"Executed: {status['executed_migrations']}")
print(f"Pending: {status['pending_migrations']}")
"""

    @staticmethod
    def generate_rollback_command(migration_id: Optional[str] = None) -> str:
        """Generate migration rollback command."""
        args = f"--migration {migration_id}" if migration_id else ""

        return f"""# Rollback migration
python -m infrastructure.migrations.cli rollback {args}

# Or using the migration manager directly
from infrastructure.migrations.sqlite_migration_manager import SQLiteMigrationManager

manager = SQLiteMigrationManager("database.db")
migration = manager.get_migration("{migration_id or 'target_migration'}")
result = await manager.rollback_migration_with_tracking(migration)
print(f"Rollback result: {result.status}")
"""
