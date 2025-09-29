"""Migration Validator - Validates migrations before execution."""

import re
import sqlparse
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .migration import Migration, MigrationType


@dataclass
class ValidationResult:
    """Result of migration validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

    def __init__(self):
        """Initialize validation result."""
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.suggestions = []

    def add_error(self, message: str) -> None:
        """Add validation error."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add validation warning."""
        self.warnings.append(message)

    def add_suggestion(self, message: str) -> None:
        """Add validation suggestion."""
        self.suggestions.append(message)


class MigrationValidator:
    """Validates migrations before execution."""

    def __init__(self, strict_mode: bool = False):
        """Initialize migration validator."""
        self.strict_mode = strict_mode
        self._sql_keywords = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
            'ALTER', 'TRUNCATE', 'BEGIN', 'COMMIT', 'ROLLBACK'
        }

    async def validate_migration(self, migration: Migration) -> ValidationResult:
        """Validate a single migration."""
        result = ValidationResult()

        # Basic validation
        await self._validate_basic_properties(migration, result)

        # Type-specific validation
        if migration.migration_type == MigrationType.SCHEMA:
            await self._validate_schema_migration(migration, result)
        elif migration.migration_type == MigrationType.DATA:
            await self._validate_data_migration(migration, result)
        elif migration.migration_type == MigrationType.INDEX:
            await self._validate_index_migration(migration, result)

        # Dependency validation
        await self._validate_dependencies(migration, result)

        # Security validation
        await self._validate_security(migration, result)

        return result

    async def validate_migration_batch(
        self,
        migrations: List[Migration]
    ) -> Dict[str, ValidationResult]:
        """Validate a batch of migrations."""
        results = {}

        for migration in migrations:
            result = await self.validate_migration(migration)
            results[migration.migration_id] = result

        return results

    async def _validate_basic_properties(self, migration: Migration, result: ValidationResult) -> None:
        """Validate basic migration properties."""
        # Check migration ID format
        if not migration.migration_id:
            result.add_error("Migration ID cannot be empty")
        elif not re.match(r'^[a-zA-Z0-9_-]+$', migration.migration_id):
            result.add_error("Migration ID must contain only alphanumeric characters, hyphens, and underscores")
        elif len(migration.migration_id) > 100:
            result.add_error("Migration ID is too long (max 100 characters)")

        # Check name
        if not migration.name:
            result.add_error("Migration name cannot be empty")
        elif len(migration.name) > 200:
            result.add_warning("Migration name is very long")

        # Check version format
        if not migration.version:
            result.add_error("Migration version cannot be empty")
        elif not re.match(r'^\d+\.\d+\.\d+.*$', migration.version):
            result.add_warning(f"Version '{migration.version}' does not follow semantic versioning")

        # Check description
        if not migration.description:
            result.add_warning("Migration description is empty")

    async def _validate_schema_migration(self, migration: Migration, result: ValidationResult) -> None:
        """Validate schema migration."""
        # This would need access to the actual migration implementation
        # For now, we'll do basic checks

        # Check if migration has up/down methods
        if not hasattr(migration, 'up'):
            result.add_error("Schema migration must have 'up' method")
        if not hasattr(migration, 'down') and migration.is_reversible():
            result.add_error("Reversible migration must have 'down' method")

        # For schema migrations with SQL, we could validate SQL syntax
        # This would require database-specific validation

    async def _validate_data_migration(self, migration: Migration, result: ValidationResult) -> None:
        """Validate data migration."""
        # Data migrations are generally more dangerous
        if not migration.is_reversible():
            result.add_warning("Data migration is not reversible - data may be lost")

        # Check if migration has proper error handling
        # This would require inspecting the migration code

    async def _validate_index_migration(self, migration: Migration, result: ValidationResult) -> None:
        """Validate index migration."""
        # Index migrations should generally be reversible
        if not migration.is_reversible():
            result.add_warning("Index migration is not reversible")

    async def _validate_dependencies(self, migration: Migration, result: ValidationResult) -> None:
        """Validate migration dependencies."""
        dependencies = migration.get_required_dependencies()

        # Check for self-dependency
        if migration.migration_id in dependencies:
            result.add_error("Migration cannot depend on itself")

        # Check for reasonable number of dependencies
        if len(dependencies) > 10:
            result.add_warning(f"Migration has many dependencies ({len(dependencies)})")

        # Check for duplicate dependencies
        if len(dependencies) != len(set(dependencies)):
            result.add_error("Migration has duplicate dependencies")

    async def _validate_security(self, migration: Migration, result: ValidationResult) -> None:
        """Validate migration security."""
        # This would analyze the migration content for potential security issues

        # For schema migrations with SQL
        if hasattr(migration, 'up_sql') and migration.up_sql:
            await self._validate_sql_security(migration.up_sql, result)

        if hasattr(migration, 'down_sql') and migration.down_sql:
            await self._validate_sql_security(migration.down_sql, result)

    async def _validate_sql_security(self, sql: str, result: ValidationResult) -> None:
        """Validate SQL for security issues."""
        sql_upper = sql.upper()

        # Check for dangerous operations
        dangerous_patterns = [
            (r'\bDROP\s+DATABASE\b', "Contains DROP DATABASE statement"),
            (r'\bTRUNCATE\s+TABLE\b', "Contains TRUNCATE TABLE statement"),
            (r'\bDELETE\s+FROM\b.*\bWHERE\b.*1\s*=\s*1', "Contains DELETE without WHERE clause"),
            (r'\bUPDATE\b.*\bSET\b.*\bWHERE\b.*1\s*=\s*1', "Contains UPDATE without WHERE clause"),
        ]

        for pattern, message in dangerous_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                if self.strict_mode:
                    result.add_error(f"Security issue: {message}")
                else:
                    result.add_warning(f"Security concern: {message}")

        # Check for SQL injection patterns
        injection_patterns = [
            (r'\'\s*\+.*\+.*\'', "Potential string concatenation"),
            (r'\%s|\%d|\%f', "Uses old-style string formatting"),
        ]

        for pattern, message in injection_patterns:
            if re.search(pattern, sql):
                result.add_warning(f"Potential SQL injection: {message}")

    async def validate_migration_plan(
        self,
        migrations: List[Migration],
        execution_order: List[str]
    ) -> ValidationResult:
        """Validate a migration execution plan."""
        result = ValidationResult()

        # Check if all migrations are included in the plan
        plan_migration_ids = set(execution_order)
        all_migration_ids = set(m.migration_id for m in migrations)

        missing_from_plan = all_migration_ids - plan_migration_ids
        extra_in_plan = plan_migration_ids - all_migration_ids

        if missing_from_plan:
            result.add_error(f"Migrations missing from execution plan: {missing_from_plan}")

        if extra_in_plan:
            result.add_error(f"Extra migrations in execution plan: {extra_in_plan}")

        # Validate execution order respects dependencies
        executed_migrations = set()
        for migration_id in execution_order:
            migration = next((m for m in migrations if m.migration_id == migration_id), None)
            if migration:
                # Check if all dependencies are satisfied
                for dep in migration.get_required_dependencies():
                    if dep not in executed_migrations:
                        result.add_error(
                            f"Migration {migration_id} depends on {dep} which is not executed yet"
                        )

                executed_migrations.add(migration_id)

        # Check for circular dependencies
        await self._detect_circular_dependencies(migrations, result)

        return result

    async def _detect_circular_dependencies(
        self,
        migrations: List[Migration],
        result: ValidationResult
    ) -> None:
        """Detect circular dependencies in migration set."""
        # Create dependency graph
        graph = {}
        for migration in migrations:
            graph[migration.migration_id] = migration.get_required_dependencies()

        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for dep in graph.get(node, []):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for migration in migrations:
            if migration.migration_id not in visited:
                if has_cycle(migration.migration_id):
                    result.add_error(f"Circular dependency detected involving {migration.migration_id}")
                    break

    async def suggest_optimizations(self, migrations: List[Migration]) -> List[str]:
        """Suggest optimizations for migrations."""
        suggestions = []

        # Check for multiple schema changes that could be combined
        schema_migrations = [m for m in migrations if m.migration_type == MigrationType.SCHEMA]
        if len(schema_migrations) > 5:
            suggestions.append("Consider combining multiple schema migrations into fewer, larger migrations")

        # Check for data migrations that could be batched
        data_migrations = [m for m in migrations if m.migration_type == MigrationType.DATA]
        if len(data_migrations) > 3:
            suggestions.append("Consider batching data migrations to reduce execution time")

        # Check for migrations without rollback
        non_reversible = [m for m in migrations if not m.is_reversible()]
        if len(non_reversible) > len(migrations) * 0.5:
            suggestions.append("Many migrations are not reversible - consider adding rollback logic")

        return suggestions


class SQLValidator:
    """Validates SQL syntax and structure."""

    def __init__(self, database_type: str = "sqlite"):
        """Initialize SQL validator."""
        self.database_type = database_type

    def validate_sql(self, sql: str) -> ValidationResult:
        """Validate SQL syntax."""
        result = ValidationResult()

        try:
            # Parse SQL
            parsed = sqlparse.parse(sql)
            if not parsed:
                result.add_error("SQL parsing failed")
                return result

            # Basic validation
            self._validate_sql_structure(parsed, result)

        except Exception as e:
            result.add_error(f"SQL validation error: {str(e)}")

        return result

    def _validate_sql_structure(self, parsed_sql, result: ValidationResult) -> None:
        """Validate SQL structure."""
        # This would contain database-specific SQL validation logic
        # For now, just basic checks

        sql_string = str(parsed_sql).upper()

        # Check for basic SQL structure
        if not any(keyword in sql_string for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']):
            result.add_warning("SQL does not contain recognized SQL keywords")

        # Check for semicolons
        if ';' not in str(parsed_sql):
            result.add_warning("SQL statement does not end with semicolon")


class MigrationConflictDetector:
    """Detects conflicts between migrations."""

    def detect_conflicts(self, migrations: List[Migration]) -> List[str]:
        """Detect potential conflicts between migrations."""
        conflicts = []

        # Check for migrations that modify the same tables
        table_modifications = {}

        for migration in migrations:
            # This would require parsing the SQL to extract table names
            # For now, just check migration names for patterns
            if hasattr(migration, 'up_sql'):
                tables = self._extract_table_names(migration.up_sql)
                for table in tables:
                    if table not in table_modifications:
                        table_modifications[table] = []
                    table_modifications[table].append(migration.migration_id)

        # Report potential conflicts
        for table, migration_ids in table_modifications.items():
            if len(migration_ids) > 1:
                conflicts.append(
                    f"Multiple migrations modify table '{table}': {migration_ids}"
                )

        return conflicts

    def _extract_table_names(self, sql: str) -> List[str]:
        """Extract table names from SQL (simplified)."""
        # This is a very simplified implementation
        # In a real system, you'd use proper SQL parsing
        tables = []
        sql_upper = sql.upper()

        # Look for common patterns
        patterns = [
            r'FROM\s+(\w+)',
            r'INTO\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'ALTER\s+TABLE\s+(\w+)',
            r'CREATE\s+TABLE\s+(\w+)',
            r'DROP\s+TABLE\s+(\w+)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, sql_upper)
            tables.extend(matches)

        return list(set(tables))  # Remove duplicates
