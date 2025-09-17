"""Migration Manager - Orchestrates migration execution and state management."""

import asyncio
import hashlib
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from pathlib import Path

from .migration import (
    Migration, MigrationResult, MigrationStatus,
    MigrationExecutionContext, MigrationDependency
)


class MigrationManager:
    """Manages database migration execution and state."""

    def __init__(
        self,
        migration_state_manager=None,
        migration_validator=None,
        dry_run: bool = False
    ):
        """Initialize migration manager."""
        self.migration_state_manager = migration_state_manager
        self.migration_validator = migration_validator
        self.dry_run = dry_run

        # Migration registry
        self.migrations: Dict[str, Migration] = {}
        self.executed_migrations: Set[str] = set()

        # Execution statistics
        self.execution_stats = {
            'total_migrations': 0,
            'successful_migrations': 0,
            'failed_migrations': 0,
            'total_execution_time': 0.0
        }

    def register_migration(self, migration: Migration) -> None:
        """Register a migration."""
        if migration.migration_id in self.migrations:
            raise ValueError(f"Migration {migration.migration_id} already registered")

        self.migrations[migration.migration_id] = migration
        self.execution_stats['total_migrations'] += 1

    def register_migrations(self, migrations: List[Migration]) -> None:
        """Register multiple migrations."""
        for migration in migrations:
            self.register_migration(migration)

    def unregister_migration(self, migration_id: str) -> bool:
        """Unregister a migration."""
        if migration_id in self.migrations:
            del self.migrations[migration_id]
            self.execution_stats['total_migrations'] -= 1
            return True
        return False

    def get_migration(self, migration_id: str) -> Optional[Migration]:
        """Get a registered migration."""
        return self.migrations.get(migration_id)

    def get_registered_migrations(self) -> List[Migration]:
        """Get all registered migrations."""
        return list(self.migrations.values())

    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that haven't been executed yet."""
        return [
            migration for migration in self.migrations.values()
            if migration.migration_id not in self.executed_migrations
        ]

    def get_executed_migrations(self) -> List[Migration]:
        """Get migrations that have been executed."""
        return [
            migration for migration in self.migrations.values()
            if migration.migration_id in self.executed_migrations
        ]

    async def execute_migration(
        self,
        migration: Migration,
        context: MigrationExecutionContext
    ) -> MigrationResult:
        """Execute a single migration."""
        start_time = asyncio.get_event_loop().time()

        try:
            # Validate migration before execution
            if self.migration_validator:
                validation_result = await self.migration_validator.validate_migration(migration)
                if not validation_result.is_valid:
                    raise ValueError(f"Migration validation failed: {validation_result.errors}")

            # Execute migration
            if not self.dry_run:
                await migration.up(context)

            # Mark as executed
            self.executed_migrations.add(migration.migration_id)

            # Record success
            execution_time = asyncio.get_event_loop().time() - start_time
            result = MigrationResult(
                migration_id=migration.migration_id,
                status=MigrationStatus.COMPLETED,
                executed_at=datetime.utcnow(),
                duration_seconds=execution_time,
                rollback_available=migration.is_reversible(),
                metadata=context.get_execution_summary()
            )

            migration.set_execution_result(result)
            self.execution_stats['successful_migrations'] += 1
            self.execution_stats['total_execution_time'] += execution_time

            return result

        except Exception as e:
            # Record failure
            execution_time = asyncio.get_event_loop().time() - start_time
            result = MigrationResult(
                migration_id=migration.migration_id,
                status=MigrationStatus.FAILED,
                executed_at=datetime.utcnow(),
                duration_seconds=execution_time,
                error_message=str(e),
                metadata=context.get_execution_summary()
            )

            migration.set_execution_result(result)
            self.execution_stats['failed_migrations'] += 1
            self.execution_stats['total_execution_time'] += execution_time

            raise e

    async def execute_pending_migrations(
        self,
        context_factory: callable,
        batch_size: int = 10
    ) -> List[MigrationResult]:
        """Execute all pending migrations in dependency order."""
        results = []

        while True:
            # Get pending migrations that can be executed
            executable_migrations = await self._get_executable_migrations()

            if not executable_migrations:
                break

            # Limit batch size
            batch = executable_migrations[:batch_size]

            # Execute batch
            batch_results = await self._execute_batch(batch, context_factory)
            results.extend(batch_results)

            # Check for completion
            if len(batch) < batch_size:
                break

        return results

    async def _get_executable_migrations(self) -> List[Migration]:
        """Get migrations that can be executed (dependencies satisfied)."""
        executable = []

        for migration in self.get_pending_migrations():
            # Check if all required dependencies are satisfied
            dependencies_satisfied = True

            for dependency in migration.get_required_dependencies():
                if dependency not in self.executed_migrations:
                    dependencies_satisfied = False
                    break

            if dependencies_satisfied:
                executable.append(migration)

        # Sort by dependency order (simplified topological sort)
        return self._sort_by_dependencies(executable)

    async def _execute_batch(
        self,
        migrations: List[Migration],
        context_factory: callable
    ) -> List[MigrationResult]:
        """Execute a batch of migrations."""
        results = []

        for migration in migrations:
            context = context_factory()
            try:
                result = await self.execute_migration(migration, context)
                results.append(result)
            except Exception as e:
                # Create failure result
                result = MigrationResult(
                    migration_id=migration.migration_id,
                    status=MigrationStatus.FAILED,
                    executed_at=datetime.utcnow(),
                    duration_seconds=0.0,
                    error_message=str(e)
                )
                results.append(result)

        return results

    def _sort_by_dependencies(self, migrations: List[Migration]) -> List[Migration]:
        """Sort migrations by dependency order."""
        # Simple dependency sort - in production you'd want a proper topological sort
        sorted_migrations = []
        remaining = migrations.copy()

        while remaining:
            # Find migrations with no dependencies in remaining list
            no_deps = []
            for migration in remaining:
                deps = migration.get_required_dependencies()
                if not any(dep in [m.migration_id for m in remaining] for dep in deps):
                    no_deps.append(migration)

            if not no_deps:
                # Circular dependency or missing dependency
                sorted_migrations.extend(remaining)
                break

            # Sort by migration ID for consistent ordering
            no_deps.sort(key=lambda m: m.migration_id)
            sorted_migrations.extend(no_deps)

            # Remove from remaining
            for migration in no_deps:
                remaining.remove(migration)

        return sorted_migrations

    async def rollback_migration(
        self,
        migration: Migration,
        context: MigrationExecutionContext
    ) -> MigrationResult:
        """Rollback a migration."""
        start_time = asyncio.get_event_loop().time()

        try:
            if not migration.is_reversible():
                raise ValueError(f"Migration {migration.migration_id} is not reversible")

            # Execute rollback
            if not self.dry_run:
                await migration.down(context)

            # Remove from executed set
            self.executed_migrations.discard(migration.migration_id)

            # Record rollback
            execution_time = asyncio.get_event_loop().time() - start_time
            result = MigrationResult(
                migration_id=migration.migration_id,
                status=MigrationStatus.ROLLED_BACK,
                executed_at=datetime.utcnow(),
                duration_seconds=execution_time,
                metadata=context.get_execution_summary()
            )

            migration.set_execution_result(result)
            return result

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            result = MigrationResult(
                migration_id=migration.migration_id,
                status=MigrationStatus.FAILED,
                executed_at=datetime.utcnow(),
                duration_seconds=execution_time,
                error_message=f"Rollback failed: {str(e)}"
            )

            migration.set_execution_result(result)
            raise e

    async def validate_migration_plan(
        self,
        target_migrations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Validate migration execution plan."""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'migration_plan': []
        }

        # Get target migrations
        if target_migrations:
            migrations_to_check = [
                self.migrations[mid] for mid in target_migrations
                if mid in self.migrations
            ]
        else:
            migrations_to_check = self.get_pending_migrations()

        # Check for missing dependencies
        all_migration_ids = set(self.migrations.keys())
        for migration in migrations_to_check:
            for dep in migration.get_required_dependencies():
                if dep not in all_migration_ids:
                    validation_result['errors'].append(
                        f"Migration {migration.migration_id} requires missing dependency: {dep}"
                    )
                    validation_result['valid'] = False

        # Check for circular dependencies (simplified)
        for migration in migrations_to_check:
            for dep in migration.get_required_dependencies():
                if dep in [m.migration_id for m in migrations_to_check]:
                    dep_migration = self.migrations[dep]
                    if migration.migration_id in dep_migration.get_required_dependencies():
                        validation_result['errors'].append(
                            f"Circular dependency detected between {migration.migration_id} and {dep}"
                        )
                        validation_result['valid'] = False

        # Build execution plan
        executable_order = []
        if validation_result['valid']:
            try:
                executable_order = self._sort_by_dependencies(migrations_to_check)
                validation_result['migration_plan'] = [m.migration_id for m in executable_order]
            except Exception as e:
                validation_result['errors'].append(f"Failed to build execution plan: {str(e)}")
                validation_result['valid'] = False

        return validation_result

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        stats = self.execution_stats.copy()
        stats['executed_migrations'] = list(self.executed_migrations)
        stats['pending_migrations'] = len(self.get_pending_migrations())
        stats['registered_migrations'] = len(self.migrations)

        if stats['total_execution_time'] > 0:
            stats['average_execution_time'] = stats['total_execution_time'] / max(1, stats['successful_migrations'])
        else:
            stats['average_execution_time'] = 0.0

        return stats

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self.execution_stats = {
            'total_migrations': len(self.migrations),
            'successful_migrations': 0,
            'failed_migrations': 0,
            'total_execution_time': 0.0
        }

    def clear_execution_state(self) -> None:
        """Clear execution state (for testing)."""
        self.executed_migrations.clear()
        self.reset_stats()
