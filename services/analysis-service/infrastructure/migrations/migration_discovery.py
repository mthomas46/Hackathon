"""Migration Discovery - Automatic migration discovery and loading."""

import importlib
import inspect
import pkgutil
from typing import Any, Dict, List, Optional, Type
from pathlib import Path
from datetime import datetime

from .migration import Migration, MigrationType, MigrationDependency


class MigrationDiscovery:
    """Discovers and loads migrations from filesystem and modules."""

    def __init__(self, migration_directories: Optional[List[str]] = None):
        """Initialize migration discovery."""
        self.migration_directories = migration_directories or ["migrations"]
        self.discovered_migrations: Dict[str, Migration] = {}

    def discover_migrations(self) -> List[Migration]:
        """Discover all migrations from configured sources."""
        migrations = []

        # Discover from filesystem
        for directory in self.migration_directories:
            dir_migrations = self._discover_from_directory(directory)
            migrations.extend(dir_migrations)

        # Discover from Python modules
        module_migrations = self._discover_from_modules()
        migrations.extend(module_migrations)

        # Remove duplicates (keep latest version)
        unique_migrations = self._deduplicate_migrations(migrations)

        self.discovered_migrations = {m.migration_id: m for m in unique_migrations}
        return unique_migrations

    def _discover_from_directory(self, directory: str) -> List[Migration]:
        """Discover migrations from directory."""
        migrations = []
        dir_path = Path(directory)

        if not dir_path.exists():
            return migrations

        # Look for Python files
        for py_file in dir_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                file_migrations = self._load_migrations_from_file(py_file)
                migrations.extend(file_migrations)
            except Exception as e:
                print(f"Warning: Failed to load migrations from {py_file}: {e}")

        # Look for SQL files
        for sql_file in dir_path.glob("*.sql"):
            try:
                sql_migration = self._load_migration_from_sql_file(sql_file)
                if sql_migration:
                    migrations.append(sql_migration)
            except Exception as e:
                print(f"Warning: Failed to load migration from {sql_file}: {e}")

        return migrations

    def _discover_from_modules(self) -> List[Migration]:
        """Discover migrations from Python modules."""
        migrations = []

        # Try to import migration modules
        migration_modules = [
            "migrations",
            "database.migrations",
            "infrastructure.migrations"
        ]

        for module_name in migration_modules:
            try:
                module = importlib.import_module(module_name)
                module_migrations = self._load_migrations_from_module(module)
                migrations.extend(module_migrations)
            except ImportError:
                continue
            except Exception as e:
                print(f"Warning: Failed to load migrations from module {module_name}: {e}")

        return migrations

    def _load_migrations_from_file(self, file_path: Path) -> List[Migration]:
        """Load migrations from Python file."""
        migrations = []

        # Import the module
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find migration classes
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, Migration) and
                    obj != Migration):
                    try:
                        # Try to instantiate with default parameters
                        migration = self._instantiate_migration(obj, name)
                        if migration:
                            migrations.append(migration)
                    except Exception as e:
                        print(f"Warning: Failed to instantiate migration {name}: {e}")

        return migrations

    def _load_migration_from_sql_file(self, file_path: Path) -> Optional[Migration]:
        """Load migration from SQL file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse SQL file (simple format: -- UP and -- DOWN sections)
            up_sql, down_sql = self._parse_sql_migration(content)

            if up_sql:
                migration_id = file_path.stem
                migration_name = migration_id.replace("_", " ").title()

                from .migration import SchemaMigration
                return SchemaMigration(
                    migration_id=migration_id,
                    name=migration_name,
                    up_sql=up_sql,
                    down_sql=down_sql
                )

        except Exception as e:
            print(f"Warning: Failed to parse SQL migration {file_path}: {e}")

        return None

    def _parse_sql_migration(self, content: str) -> tuple:
        """Parse SQL migration file content."""
        lines = content.split('\n')
        up_lines = []
        down_lines = []
        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith('-- UP'):
                current_section = 'up'
                continue
            elif line.startswith('-- DOWN'):
                current_section = 'down'
                continue
            elif line.startswith('--'):
                continue  # Skip comments

            if current_section == 'up':
                up_lines.append(line)
            elif current_section == 'down':
                down_lines.append(line)

        up_sql = '\n'.join(up_lines).strip()
        down_sql = '\n'.join(down_lines).strip() if down_lines else None

        return up_sql, down_sql

    def _load_migrations_from_module(self, module) -> List[Migration]:
        """Load migrations from Python module."""
        migrations = []

        # Find migration classes in module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and
                issubclass(obj, Migration) and
                obj != Migration):
                try:
                    migration = self._instantiate_migration(obj, name)
                    if migration:
                        migrations.append(migration)
                except Exception as e:
                    print(f"Warning: Failed to instantiate migration {name}: {e}")

        return migrations

    def _instantiate_migration(self, migration_class: Type[Migration], name: str) -> Optional[Migration]:
        """Instantiate migration class."""
        try:
            # Try to create with default migration ID
            migration_id = getattr(migration_class, 'migration_id', name.lower())

            # Get constructor parameters
            sig = inspect.signature(migration_class.__init__)
            params = {}

            # Set required parameters with defaults
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                if param_name == 'migration_id':
                    params[param_name] = migration_id
                elif param_name == 'name':
                    params[param_name] = getattr(migration_class, 'name', name)
                elif param.default != inspect.Parameter.empty:
                    params[param_name] = param.default
                else:
                    # Try to get from class attributes
                    if hasattr(migration_class, param_name):
                        params[param_name] = getattr(migration_class, param_name)

            return migration_class(**params)

        except Exception as e:
            print(f"Warning: Failed to instantiate {migration_class.__name__}: {e}")
            return None

    def _deduplicate_migrations(self, migrations: List[Migration]) -> List[Migration]:
        """Remove duplicate migrations, keeping the latest version."""
        migration_map: Dict[str, Migration] = {}

        for migration in migrations:
            migration_id = migration.migration_id

            if migration_id not in migration_map:
                migration_map[migration_id] = migration
            else:
                # Compare versions and keep the newer one
                existing = migration_map[migration_id]

                if self._compare_versions(migration.version, existing.version) > 0:
                    migration_map[migration_id] = migration

        return list(migration_map.values())

    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings."""
        # Simple version comparison (semantic versioning)
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]

            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))

            for i in range(max_len):
                if v1_parts[i] > v2_parts[i]:
                    return 1
                elif v1_parts[i] < v2_parts[i]:
                    return -1

            return 0

        except (ValueError, AttributeError):
            # If version comparison fails, compare by timestamp
            return 0

    def get_discovered_migrations(self) -> Dict[str, Migration]:
        """Get all discovered migrations."""
        return self.discovered_migrations.copy()

    def get_migration_by_id(self, migration_id: str) -> Optional[Migration]:
        """Get migration by ID."""
        return self.discovered_migrations.get(migration_id)

    def filter_migrations_by_type(self, migration_type: MigrationType) -> List[Migration]:
        """Filter migrations by type."""
        return [
            m for m in self.discovered_migrations.values()
            if m.migration_type == migration_type
        ]

    def filter_migrations_by_version(self, min_version: str, max_version: Optional[str] = None) -> List[Migration]:
        """Filter migrations by version range."""
        filtered = []

        for migration in self.discovered_migrations.values():
            try:
                if self._compare_versions(migration.version, min_version) >= 0:
                    if max_version is None or self._compare_versions(migration.version, max_version) <= 0:
                        filtered.append(migration)
            except (ValueError, AttributeError):
                continue

        return filtered

    def validate_discovered_migrations(self) -> Dict[str, Any]:
        """Validate discovered migrations."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'summary': {
                'total_migrations': len(self.discovered_migrations),
                'by_type': {},
                'by_version': {}
            }
        }

        # Count by type
        for migration in self.discovered_migrations.values():
            migration_type = migration.migration_type.value
            if migration_type not in validation_result['summary']['by_type']:
                validation_result['summary']['by_type'][migration_type] = 0
            validation_result['summary']['by_type'][migration_type] += 1

        # Count by version
        for migration in self.discovered_migrations.values():
            version = migration.version
            if version not in validation_result['summary']['by_version']:
                validation_result['summary']['by_version'][version] = 0
            validation_result['summary']['by_version'][version] += 1

        # Check for missing dependencies
        for migration in self.discovered_migrations.values():
            for dep in migration.get_required_dependencies():
                if dep not in self.discovered_migrations:
                    validation_result['errors'].append(
                        f"Migration {migration.migration_id} requires missing dependency: {dep}"
                    )
                    validation_result['valid'] = False

        # Check for circular dependencies (simplified)
        for migration in self.discovered_migrations.values():
            for dep in migration.get_required_dependencies():
                if dep in self.discovered_migrations:
                    dep_migration = self.discovered_migrations[dep]
                    if migration.migration_id in dep_migration.get_required_dependencies():
                        validation_result['errors'].append(
                            f"Circular dependency detected between {migration.migration_id} and {dep}"
                        )
                        validation_result['valid'] = False

        return validation_result
