#!/usr/bin/env python3
"""
Dependency Adder Tool

Automatically adds missing service dependency declarations to Docker Compose files
to ensure proper startup ordering and service health.
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class DependencyAddition:
    """Represents a dependency addition operation."""
    file_path: str
    service_name: str
    operation: str
    description: str
    added_dependencies: List[str]
    dependency_format: str  # 'list' or 'dict'


class DependencyAdder:
    """
    Adds missing service dependency declarations to Docker Compose files.

    Ensures services have proper startup ordering and health dependencies.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Service dependency mapping
        self.service_dependencies = {
            # Core infrastructure services (usually don't depend on others)
            'redis': [],
            'postgres': [],
            'mongodb': [],
            'rabbitmq': [],

            # API and backend services
            'orchestrator': ['redis'],
            'analysis-service': ['redis', 'doc_store'],
            'llm-gateway': ['redis'],
            'summarizer-hub': ['redis'],
            'doc_store': ['redis'],
            'unified-api-dashboard': ['redis'],
            'bedrock-proxy': ['redis'],
            'source-agent': ['redis'],
            'memory-agent': ['redis'],
            'user-store': ['redis'],
            'external-service-store': ['redis'],
            'mock-data-generator': ['redis'],
            'secure-analyzer': ['redis'],
            'code-analyzer': ['redis'],
            'interpreter': ['redis'],
            'architecture-digitizer': ['redis'],
            'github-mcp': ['redis'],
            'notification-service': ['redis'],
            'log-collector': ['redis'],
            'discovery-agent': ['redis'],
            'project-planning-service': ['redis'],
            'ollama': ['redis'],
            'prompt_store': ['redis'],
            'cli': ['redis'],

            # Frontend services
            'frontend': ['unified-api-dashboard'],
            'simulation-dashboard': ['unified-api-dashboard'],
            'project-simulation': ['redis'],
            'data-services-dashboard': ['unified-api-dashboard'],

            # Specialized services that might need databases
            'user-store': ['redis', 'postgres'],
            'doc_store': ['redis', 'postgres'],
            'external-service-store': ['redis', 'postgres'],
            'prompt_store': ['redis', 'postgres'],
        }

    def add_missing_dependencies(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Add missing dependency declarations to Docker Compose files.

        Args:
            dry_run: If True, only show what would be changed

        Returns:
            Addition results
        """
        results = {
            'files_processed': 0,
            'dependencies_added': 0,
            'services_updated': 0,
            'errors': [],
            'additions': []
        }

        print(f"🔧 Dependency Addition ({'DRY RUN' if dry_run else 'APPLY CHANGES'})")
        print("=" * 70)

        # Find all docker-compose files
        compose_files = []
        for pattern in ["docker-compose*.yml", "docker-compose*.yaml"]:
            compose_files.extend(list(self.project_root.rglob(pattern)))

        # Also check service-specific docker-compose files
        for service_dir in self.project_root.glob("services/*"):
            if service_dir.is_dir():
                compose_files.extend(list(service_dir.glob("docker-compose*.yml")))
                compose_files.extend(list(service_dir.glob("docker-compose*.yaml")))

        # Remove duplicates and exclude template files with YAML errors
        compose_files = list(set(compose_files))
        compose_files = [f for f in compose_files if 'template' not in f.name.lower()]

        for compose_file in compose_files:
            results['files_processed'] += 1
            service_name = compose_file.parent.name

            try:
                additions = self._add_dependencies_to_file(compose_file, service_name, dry_run)
                results['additions'].extend(additions)
                results['dependencies_added'] += sum(len(add.added_dependencies) for add in additions)

                if additions:
                    results['services_updated'] += len(set(add.service_name for add in additions))
                    print(f"📄 {compose_file.relative_to(self.project_root)}: {len(additions)} services updated")

            except Exception as e:
                error_msg = f"Error processing {compose_file}: {e}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)

        print(f"\n📊 Dependency Addition Summary:")
        print(f"   Files processed: {results['files_processed']}")
        print(f"   Services updated: {results['services_updated']}")
        print(f"   Dependencies added: {results['dependencies_added']}")
        print(f"   Errors: {len(results['errors'])}")

        if results['additions']:
            print(f"\n✅ Dependencies Added:")
            service_updates = {}
            for addition in results['additions']:
                if addition.service_name not in service_updates:
                    service_updates[addition.service_name] = []
                service_updates[addition.service_name].extend(addition.added_dependencies)

            for service, deps in service_updates.items():
                unique_deps = list(set(deps))
                print(f"   • {service}: {', '.join(unique_deps)}")

        return results

    def _add_dependencies_to_file(self, compose_file: Path, service_name: str, dry_run: bool) -> List[DependencyAddition]:
        """Add missing dependencies to a single docker-compose file."""
        additions = []

        try:
            import yaml
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)

            if not config or 'services' not in config:
                return additions

            modified = False

            for svc_name, service_config in config['services'].items():
                # Check if this service needs dependencies
                if svc_name in self.service_dependencies:
                    required_deps = self.service_dependencies[svc_name]
                    if not required_deps:
                        continue  # This service doesn't need dependencies

                    # Check current dependencies
                    current_deps = self._get_current_dependencies(service_config)

                    # Find missing dependencies
                    missing_deps = [dep for dep in required_deps if dep not in current_deps]

                    if missing_deps:
                        # Add missing dependencies
                        if 'depends_on' not in service_config:
                            service_config['depends_on'] = []

                        if isinstance(service_config['depends_on'], list):
                            service_config['depends_on'].extend(missing_deps)
                            # Remove duplicates while preserving order
                            seen = set()
                            service_config['depends_on'] = [x for x in service_config['depends_on'] if not (x in seen or seen.add(x))]
                        elif isinstance(service_config['depends_on'], dict):
                            # Add to dict format
                            for dep in missing_deps:
                                if dep not in service_config['depends_on']:
                                    service_config['depends_on'][dep] = {'condition': 'service_started'}

                        additions.append(DependencyAddition(
                            file_path=str(compose_file),
                            service_name=svc_name,
                            operation="add_dependencies",
                            description=f"Added missing dependencies: {', '.join(missing_deps)}",
                            added_dependencies=missing_deps,
                            dependency_format='list' if isinstance(service_config['depends_on'], list) else 'dict'
                        ))

                        modified = True

            if modified and not dry_run:
                with open(compose_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        except Exception as e:
            print(f"Error adding dependencies to {compose_file}: {e}")

        return additions

    def _get_current_dependencies(self, service_config: Dict[str, Any]) -> Set[str]:
        """Get current dependencies from service configuration."""
        current_deps = set()

        if 'depends_on' in service_config:
            deps = service_config['depends_on']
            if isinstance(deps, list):
                current_deps.update(deps)
            elif isinstance(deps, dict):
                current_deps.update(deps.keys())

        return current_deps


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Dependency Adder Tool")
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Perform dry run (only show changes)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    adder = DependencyAdder()

    try:
        dry_run = args.dry_run
        results = adder.add_missing_dependencies(dry_run=dry_run)

        if dry_run:
            print("\n💡 This was a DRY RUN. No files were actually modified.")
            print("   Run without --dry-run to apply changes.")

        if args.verbose:
            print("\n📋 Detailed Results:")
            print(f"Files processed: {results['files_processed']}")
            print(f"Services updated: {results['services_updated']}")
            print(f"Dependencies added: {results['dependencies_added']}")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Addition failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
