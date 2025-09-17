"""Migration State Manager - Tracks migration execution state."""

import json
import hashlib
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path

from .migration import Migration, MigrationResult, MigrationStatus


class MigrationStateManager:
    """Manages migration execution state and history."""

    def __init__(self, state_file: Optional[str] = None):
        """Initialize state manager."""
        self.state_file = Path(state_file) if state_file else Path("migration_state.json")
        self.executed_migrations: Set[str] = set()
        self.migration_history: List[Dict[str, Any]] = []
        self.checksums: Dict[str, str] = {}

        # Load existing state
        self._load_state()

    def mark_executed(self, migration: Migration, result: MigrationResult) -> None:
        """Mark migration as executed."""
        self.executed_migrations.add(migration.migration_id)

        # Add to history
        history_entry = {
            'migration_id': migration.migration_id,
            'name': migration.name,
            'version': migration.version,
            'executed_at': result.executed_at.isoformat(),
            'duration_seconds': result.duration_seconds,
            'status': result.status.value,
            'checksum': self._calculate_checksum(migration),
            'metadata': result.metadata or {}
        }

        self.migration_history.append(history_entry)
        self.checksums[migration.migration_id] = history_entry['checksum']

        # Save state
        self._save_state()

    def mark_failed(self, migration: Migration, error: str) -> None:
        """Mark migration as failed."""
        # Add failure to history
        history_entry = {
            'migration_id': migration.migration_id,
            'name': migration.name,
            'version': migration.version,
            'executed_at': datetime.utcnow().isoformat(),
            'duration_seconds': 0.0,
            'status': MigrationStatus.FAILED.value,
            'error': error,
            'checksum': self._calculate_checksum(migration),
            'metadata': {}
        }

        self.migration_history.append(history_entry)

        # Save state
        self._save_state()

    def is_executed(self, migration_id: str) -> bool:
        """Check if migration has been executed."""
        return migration_id in self.executed_migrations

    def get_execution_history(self, migration_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get execution history."""
        if migration_id:
            return [entry for entry in self.migration_history if entry['migration_id'] == migration_id]

        return self.migration_history.copy()

    def get_last_execution(self, migration_id: str) -> Optional[Dict[str, Any]]:
        """Get last execution of migration."""
        history = self.get_execution_history(migration_id)
        return history[-1] if history else None

    def has_changed(self, migration: Migration) -> bool:
        """Check if migration has changed since last execution."""
        if migration.migration_id not in self.checksums:
            return True

        current_checksum = self._calculate_checksum(migration)
        return current_checksum != self.checksums[migration.migration_id]

    def get_pending_migrations(self, migrations: List[Migration]) -> List[Migration]:
        """Get migrations that haven't been executed."""
        return [
            migration for migration in migrations
            if not self.is_executed(migration.migration_id)
        ]

    def get_executed_migrations(self, migrations: List[Migration]) -> List[Migration]:
        """Get migrations that have been executed."""
        return [
            migration for migration in migrations
            if self.is_executed(migration.migration_id)
        ]

    def get_changed_migrations(self, migrations: List[Migration]) -> List[Migration]:
        """Get migrations that have changed since execution."""
        return [
            migration for migration in migrations
            if self.has_changed(migration)
        ]

    def _calculate_checksum(self, migration: Migration) -> str:
        """Calculate checksum for migration."""
        # Create a string representation of the migration
        migration_str = f"{migration.migration_id}{migration.name}{migration.version}"

        # Add migration-specific content
        if hasattr(migration, 'up_sql'):
            migration_str += migration.up_sql
        if hasattr(migration, 'down_sql') and migration.down_sql:
            migration_str += migration.down_sql

        # Calculate checksum
        return hashlib.md5(migration_str.encode()).hexdigest()

    def _load_state(self) -> None:
        """Load state from file."""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            # Load executed migrations
            self.executed_migrations = set(state_data.get('executed_migrations', []))

            # Load history
            self.migration_history = state_data.get('migration_history', [])

            # Load checksums
            self.checksums = state_data.get('checksums', {})

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load migration state: {e}")
            # Initialize empty state
            self.executed_migrations = set()
            self.migration_history = []
            self.checksums = {}

    def _save_state(self) -> None:
        """Save state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            state_data = {
                'executed_migrations': list(self.executed_migrations),
                'migration_history': self.migration_history,
                'checksums': self.checksums,
                'last_updated': datetime.utcnow().isoformat()
            }

            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)

        except IOError as e:
            print(f"Warning: Failed to save migration state: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get migration statistics."""
        stats = {
            'total_executed': len(self.executed_migrations),
            'total_history_entries': len(self.migration_history),
            'last_execution': None,
            'execution_counts_by_status': {},
            'average_execution_time': 0.0,
            'total_execution_time': 0.0
        }

        if self.migration_history:
            # Get last execution
            sorted_history = sorted(self.migration_history, key=lambda x: x['executed_at'], reverse=True)
            stats['last_execution'] = sorted_history[0]

            # Count by status
            status_counts = {}
            total_time = 0.0
            valid_entries = 0

            for entry in self.migration_history:
                status = entry.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1

                if entry.get('duration_seconds', 0) > 0:
                    total_time += entry['duration_seconds']
                    valid_entries += 1

            stats['execution_counts_by_status'] = status_counts
            stats['total_execution_time'] = total_time

            if valid_entries > 0:
                stats['average_execution_time'] = total_time / valid_entries

        return stats

    def reset_state(self) -> None:
        """Reset migration state."""
        self.executed_migrations.clear()
        self.migration_history.clear()
        self.checksums.clear()
        self._save_state()

    def cleanup_old_history(self, days_to_keep: int = 365) -> int:
        """Clean up old migration history entries."""
        if not self.migration_history:
            return 0

        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)

        original_count = len(self.migration_history)

        # Keep at least one entry per migration
        migrations_seen = set()
        filtered_history = []

        for entry in reversed(self.migration_history):
            migration_id = entry['migration_id']

            if migration_id not in migrations_seen:
                # Keep the most recent entry for each migration
                filtered_history.append(entry)
                migrations_seen.add(migration_id)
            elif entry['executed_at'] >= cutoff_date.isoformat():
                # Keep recent entries
                filtered_history.append(entry)

        # Reverse back to chronological order
        self.migration_history = list(reversed(filtered_history))

        # Save updated state
        self._save_state()

        return original_count - len(self.migration_history)

    def validate_state_integrity(self) -> Dict[str, Any]:
        """Validate state integrity."""
        issues = []

        # Check for missing checksums
        for migration_id in self.executed_migrations:
            if migration_id not in self.checksums:
                issues.append(f"Missing checksum for executed migration: {migration_id}")

        # Check for orphaned checksums
        for migration_id in self.checksums:
            if migration_id not in self.executed_migrations:
                issues.append(f"Orphaned checksum for non-executed migration: {migration_id}")

        # Check history consistency
        history_migration_ids = set()
        for entry in self.migration_history:
            migration_id = entry.get('migration_id')
            if migration_id:
                history_migration_ids.add(migration_id)

        missing_from_history = self.executed_migrations - history_migration_ids
        if missing_from_history:
            issues.append(f"Migrations executed but missing from history: {missing_from_history}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'total_migrations': len(self.executed_migrations),
            'total_history_entries': len(self.migration_history)
        }


class MigrationStateValidator:
    """Validates migration state consistency."""

    def __init__(self, state_manager: MigrationStateManager):
        """Initialize state validator."""
        self.state_manager = state_manager

    def validate_against_migrations(self, migrations: List[Migration]) -> Dict[str, Any]:
        """Validate state against available migrations."""
        issues = []

        available_migration_ids = {m.migration_id for m in migrations}

        # Check for executed migrations that no longer exist
        for executed_id in self.state_manager.executed_migrations:
            if executed_id not in available_migration_ids:
                issues.append(f"Executed migration no longer exists: {executed_id}")

        # Check for checksum mismatches
        for migration in migrations:
            if self.state_manager.has_changed(migration):
                issues.append(f"Migration has changed since execution: {migration.migration_id}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'available_migrations': len(available_migration_ids),
            'executed_migrations': len(self.state_manager.executed_migrations)
        }

    def detect_drift(self, migrations: List[Migration]) -> Dict[str, Any]:
        """Detect state drift between migrations and execution state."""
        drift_info = {
            'has_drift': False,
            'missing_executions': [],
            'unexpected_executions': [],
            'checksum_mismatches': [],
            'total_migrations': len(migrations)
        }

        available_migration_ids = {m.migration_id for m in migrations}

        # Find missing executions
        for migration in migrations:
            if not self.state_manager.is_executed(migration.migration_id):
                drift_info['missing_executions'].append(migration.migration_id)

        # Find unexpected executions
        for executed_id in self.state_manager.executed_migrations:
            if executed_id not in available_migration_ids:
                drift_info['unexpected_executions'].append(executed_id)

        # Find checksum mismatches
        for migration in migrations:
            if self.state_manager.is_executed(migration.migration_id):
                if self.state_manager.has_changed(migration):
                    drift_info['checksum_mismatches'].append(migration.migration_id)

        drift_info['has_drift'] = any([
            drift_info['missing_executions'],
            drift_info['unexpected_executions'],
            drift_info['checksum_mismatches']
        ])

        return drift_info

    def suggest_resolution(self, drift_info: Dict[str, Any]) -> List[str]:
        """Suggest resolution steps for detected drift."""
        suggestions = []

        if drift_info['missing_executions']:
            suggestions.append(
                f"Execute missing migrations: {drift_info['missing_executions']}"
            )

        if drift_info['unexpected_executions']:
            suggestions.append(
                f"Review unexpected executions (possibly removed migrations): {drift_info['unexpected_executions']}"
            )

        if drift_info['checksum_mismatches']:
            suggestions.append(
                f"Review changed migrations: {drift_info['checksum_mismatches']} "
                "(consider rollback and re-execution if changes are significant)"
            )

        if not suggestions:
            suggestions.append("No drift detected - state is consistent")

        return suggestions


class MigrationStateExporter:
    """Exports migration state for backup or transfer."""

    def __init__(self, state_manager: MigrationStateManager):
        """Initialize state exporter."""
        self.state_manager = state_manager

    def export_to_file(self, file_path: str, format_type: str = "json") -> None:
        """Export state to file."""
        if format_type == "json":
            self._export_json(file_path)
        elif format_type == "yaml":
            self._export_yaml(file_path)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def _export_json(self, file_path: str) -> None:
        """Export state as JSON."""
        export_data = {
            'metadata': {
                'exported_at': datetime.utcnow().isoformat(),
                'format_version': '1.0',
                'total_migrations': len(self.state_manager.executed_migrations)
            },
            'executed_migrations': list(self.state_manager.executed_migrations),
            'migration_history': self.state_manager.migration_history,
            'checksums': self.state_manager.checksums,
            'statistics': self.state_manager.get_statistics()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def _export_yaml(self, file_path: str) -> None:
        """Export state as YAML."""
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for YAML export")

        export_data = {
            'metadata': {
                'exported_at': datetime.utcnow().isoformat(),
                'format_version': '1.0',
                'total_migrations': len(self.state_manager.executed_migrations)
            },
            'executed_migrations': list(self.state_manager.executed_migrations),
            'migration_history': self.state_manager.migration_history,
            'checksums': self.state_manager.checksums,
            'statistics': self.state_manager.get_statistics()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(export_data, f, default_flow_style=False, indent=2)

    def import_from_file(self, file_path: str) -> None:
        """Import state from file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                try:
                    import yaml
                    import_data = yaml.safe_load(f)
                except ImportError:
                    raise ImportError("PyYAML is required for YAML import")
            else:
                import_data = json.load(f)

        # Validate import data
        if 'executed_migrations' not in import_data:
            raise ValueError("Invalid import file: missing executed_migrations")

        # Import state
        self.state_manager.executed_migrations = set(import_data['executed_migrations'])
        self.state_manager.migration_history = import_data.get('migration_history', [])
        self.state_manager.checksums = import_data.get('checksums', {})

        # Save imported state
        self.state_manager._save_state()
