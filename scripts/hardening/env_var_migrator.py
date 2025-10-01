#!/usr/bin/env python3
"""
Environment Variable Migration Script

Automatically migrates environment variable names from old patterns to new standardized ones.
Handles the migration across all configuration files, docker-compose files, and documentation.
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class EnvVarMigration:
    """Represents a single environment variable migration."""
    old_name: str
    new_name: str
    category: str
    reason: str
    files_affected: List[str] = None


class EnvironmentVariableMigrator:
    """
    Migrates environment variable names across the entire codebase.

    Handles systematic renaming of environment variables to follow
    standardized naming conventions.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Define migrations to perform
        self.migrations = self._define_migrations()

    def _define_migrations(self) -> List[EnvVarMigration]:
        """Define the environment variable migrations to perform."""
        return [
            # Feature flags: ENABLE_* → FEATURE_*
            EnvVarMigration(
                old_name="FEATURE_FILE_LOGGING",
                new_name="FEATURE_FILE_LOGGING",
                category="feature_flag",
                reason="Standardize feature flag naming convention"
            ),
            EnvVarMigration(
                old_name="FEATURE_CORRELATION_ID",
                new_name="FEATURE_CORRELATION_ID",
                category="feature_flag",
                reason="Standardize feature flag naming convention"
            ),
            EnvVarMigration(
                old_name="FEATURE_METRICS",
                new_name="FEATURE_METRICS",
                category="feature_flag",
                reason="Standardize feature flag naming convention"
            ),
            EnvVarMigration(
                old_name="FEATURE_HEALTH_CHECKS",
                new_name="FEATURE_HEALTH_CHECKS",
                category="feature_flag",
                reason="Standardize feature flag naming convention"
            ),
            EnvVarMigration(
                old_name="FEATURE_PROFILING",
                new_name="FEATURE_PROFILING",
                category="feature_flag",
                reason="Standardize feature flag naming convention"
            ),
            EnvVarMigration(
                old_name="FEATURE_ADVANCED_ANALYTICS",
                new_name="FEATURE_ADVANCED_ANALYTICS",
                category="feature_flag",
                reason="Standardize feature flag naming convention"
            ),
            EnvVarMigration(
                old_name="FEATURE_REAL_TIME_UPDATES",
                new_name="FEATURE_REAL_TIME_UPDATES",
                category="feature_flag",
                reason="Standardize feature flag naming convention"
            ),
            EnvVarMigration(
                old_name="FEATURE_EXTENDED_LOGGING",
                new_name="FEATURE_EXTENDED_LOGGING",
                category="feature_flag",
                reason="Standardize feature flag naming convention"
            ),
            EnvVarMigration(
                old_name="FEATURE_DETAILED_METRICS",
                new_name="FEATURE_DETAILED_METRICS",
                category="feature_flag",
                reason="Standardize feature flag naming convention"
            ),

            # All other migrations were already completed successfully
        ]

    def analyze_migration_impact(self) -> Dict[str, Any]:
        """
        Analyze the impact of planned migrations.

        Returns:
            Analysis of files and variables that would be affected
        """
        impact = {
            'total_migrations': len(self.migrations),
            'files_affected': set(),
            'variables_found': {},
            'categories_affected': set()
        }

        # File patterns to search
        search_patterns = [
            "*.yml", "*.yaml", "*.py", "*.md", "*.sh", "*.json"
        ]

        # Directories to exclude (cache, dependencies, etc.)
        exclude_dirs = {
            '.git', '__pycache__', '.pytest_cache', '.mypy_cache', 'node_modules',
            '.venv', 'venv', 'env', 'ENV', '.env',
            'build', 'dist', '.next', '.nuxt',
            # Python virtual environments and cache
            'lib', 'site-packages', 'dist-packages',
            '.ci_test', 'test_env', 'demo_venv', 'venv_audit', 'venv_hardening', 'venv_validation'
        }

        for migration in self.migrations:
            impact['categories_affected'].add(migration.category)
            impact['variables_found'][migration.old_name] = []

            # Search for the old variable name
            for pattern in search_patterns:
                for file_path in self.project_root.rglob(pattern):
                    if file_path.is_file():
                        # Skip excluded directories
                        if any(part in exclude_dirs for part in file_path.parts):
                            continue

                        # Only include relevant project files
                        if not (file_path.name.endswith(('.yml', '.yaml', '.py', '.md', '.sh', '.json')) or
                               'services/' in str(file_path) or
                               'config/' in str(file_path) or
                               'scripts/' in str(file_path) or
                               'docs/' in str(file_path)):
                            continue

                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if migration.old_name in content:
                                    impact['files_affected'].add(str(file_path))
                                    impact['variables_found'][migration.old_name].append(str(file_path))
                        except Exception:
                            continue

        impact['files_affected'] = sorted(list(impact['files_affected']))
        return impact

    def perform_migrations(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Perform the environment variable migrations.

        Args:
            dry_run: If True, only show what would be changed

        Returns:
            Migration results
        """
        results = {
            'migrations_performed': 0,
            'files_modified': 0,
            'errors': [],
            'dry_run': dry_run
        }

        print(f"🔄 Environment Variable Migration ({'DRY RUN' if dry_run else 'APPLY CHANGES'})")
        print("=" * 70)

        for migration in self.migrations:
            print(f"\n📝 Migrating: {migration.old_name} → {migration.new_name}")
            print(f"   Reason: {migration.reason}")

            files_modified = 0

            # Find and update files
            exclude_dirs = {
                '.git', '__pycache__', '.pytest_cache', '.mypy_cache', 'node_modules',
                '.venv', 'venv', 'env', 'ENV', '.env',
                'build', 'dist', '.next', '.nuxt',
                'lib', 'site-packages', 'dist-packages',
                '.ci_test', 'test_env', 'demo_venv', 'venv_audit', 'venv_hardening', 'venv_validation'
            }

            for pattern in ["*.yml", "*.yaml", "*.py", "*.md", "*.sh", "*.json"]:
                for file_path in self.project_root.rglob(pattern):
                    if file_path.is_file():
                        # Skip excluded directories
                        if any(part in exclude_dirs for part in file_path.parts):
                            continue

                        # Only include relevant project files
                        if not (file_path.name.endswith(('.yml', '.yaml', '.py', '.md', '.sh', '.json')) or
                               'services/' in str(file_path) or
                               'config/' in str(file_path) or
                               'scripts/' in str(file_path) or
                               'docs/' in str(file_path)):
                            continue

                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()

                            if migration.old_name in content:
                                print(f"   📄 Updating {file_path.relative_to(self.project_root)}")

                                # Perform the replacement
                                new_content = content.replace(migration.old_name, migration.new_name)

                                if not dry_run:
                                    with open(file_path, 'w', encoding='utf-8') as f:
                                        f.write(new_content)

                                files_modified += 1
                                results['migrations_performed'] += 1

                        except Exception as e:
                            error_msg = f"Error processing {file_path}: {e}"
                            print(f"   ❌ {error_msg}")
                            results['errors'].append(error_msg)

            if files_modified > 0:
                results['files_modified'] += 1
                print(f"   ✅ Modified {files_modified} files")
            else:
                print(f"   ℹ️  No files contained {migration.old_name}")

        print(f"\n📊 Migration Summary:")
        print(f"   Migrations performed: {results['migrations_performed']}")
        print(f"   Files modified: {results['files_modified']}")
        print(f"   Errors: {len(results['errors'])}")

        if results['errors']:
            print(f"\n❌ Errors encountered:")
            for error in results['errors'][:5]:
                print(f"   • {error}")
            if len(results['errors']) > 5:
                print(f"   ... and {len(results['errors']) - 5} more")

        return results

    def validate_migrations(self) -> Dict[str, Any]:
        """
        Validate that migrations were applied correctly.

        Returns:
            Validation results
        """
        validation = {
            'migrations_validated': 0,
            'issues_found': [],
            'recommendations': []
        }

        print("🔍 Validating Environment Variable Migrations")
        print("=" * 50)

        for migration in self.migrations:
            old_name_found = False
            new_name_found = False

            # Check if old name still exists
            for pattern in ["*.yml", "*.yaml", "*.py", "*.md", "*.sh", "*.json"]:
                for file_path in self.project_root.rglob(pattern):
                    if file_path.is_file():
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if migration.old_name in content:
                                    old_name_found = True
                                    validation['issues_found'].append({
                                        'type': 'old_name_persists',
                                        'migration': f"{migration.old_name} → {migration.new_name}",
                                        'file': str(file_path),
                                        'issue': f"Old variable name still exists in {file_path}"
                                    })
                                if migration.new_name in content:
                                    new_name_found = True
                        except Exception:
                            continue

            if not old_name_found and new_name_found:
                validation['migrations_validated'] += 1
                print(f"✅ {migration.old_name} → {migration.new_name}")
            elif old_name_found:
                print(f"❌ {migration.old_name} → {migration.new_name} (old name still exists)")
            else:
                print(f"ℹ️  {migration.old_name} → {migration.new_name} (not found in codebase)")

        print(f"\n📊 Validation Summary:")
        print(f"   Migrations validated: {validation['migrations_validated']}")
        print(f"   Issues found: {len(validation['issues_found'])}")

        if validation['issues_found']:
            validation['recommendations'].append("Review and fix migration issues")
            validation['recommendations'].append("Update any hardcoded references to old variable names")

        return validation


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Environment Variable Migration Tool")
    parser.add_argument('--action', '-a', choices=['analyze', 'migrate', 'validate'],
                       default='analyze', help='Action to perform')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Perform dry run (only show changes)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    migrator = EnvironmentVariableMigrator()

    try:
        if args.action == 'analyze':
            print("🔍 Analyzing Migration Impact")
            impact = migrator.analyze_migration_impact()

            print(f"📊 Migration Impact Analysis:")
            print(f"   Total migrations planned: {impact['total_migrations']}")
            print(f"   Files that would be affected: {len(impact['files_affected'])}")
            print(f"   Categories affected: {', '.join(sorted(impact['categories_affected']))}")

            if impact['files_affected']:
                print(f"\n📁 Sample affected files:")
                for file in impact['files_affected'][:10]:
                    print(f"   • {file}")
                if len(impact['files_affected']) > 10:
                    print(f"   ... and {len(impact['files_affected']) - 10} more")

        elif args.action == 'migrate':
            dry_run = args.dry_run
            results = migrator.perform_migrations(dry_run=dry_run)

            if dry_run:
                print("\n💡 This was a DRY RUN. No files were actually modified.")
                print("   Run with --action migrate (without --dry-run) to apply changes.")

        elif args.action == 'validate':
            validation = migrator.validate_migrations()

            if validation['issues_found']:
                print("\n❌ Migration Issues Found:")
                for issue in validation['issues_found'][:5]:
                    print(f"   • {issue['migration']}: {issue['issue']}")

                if len(validation['issues_found']) > 5:
                    print(f"   ... and {len(validation['issues_found']) - 5} more issues")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
