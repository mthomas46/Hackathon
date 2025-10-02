#!/usr/bin/env python3
"""
Volume Simplification Tool

Automatically simplifies Docker volume configurations by removing duplicates,
standardizing paths, and reducing complexity.
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
class VolumeSimplification:
    """Represents a volume simplification operation."""
    file_path: str
    service_name: str
    operation: str
    description: str
    original_config: Any
    simplified_config: Any
    can_auto_fix: bool = True


class VolumeSimplifier:
    """
    Simplifies Docker volume configurations across the ecosystem.

    Removes duplicates, standardizes paths, and reduces complexity
    while maintaining functionality.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent

    def simplify_volumes(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Simplify volume configurations across all Docker Compose files.

        Args:
            dry_run: If True, only show what would be changed

        Returns:
            Simplification results
        """
        results = {
            'files_processed': 0,
            'simplifications_applied': 0,
            'errors': [],
            'simplifications': []
        }

        print(f"🔧 Volume Simplification ({'DRY RUN' if dry_run else 'APPLY CHANGES'})")
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
                simplifications = self._simplify_compose_file(compose_file, service_name, dry_run)
                results['simplifications'].extend(simplifications)
                results['simplifications_applied'] += len(simplifications)

                if simplifications:
                    print(f"📄 {compose_file.relative_to(self.project_root)}: {len(simplifications)} simplifications")

            except Exception as e:
                error_msg = f"Error processing {compose_file}: {e}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)

        print(f"\n📊 Simplification Summary:")
        print(f"   Files processed: {results['files_processed']}")
        print(f"   Simplifications applied: {results['simplifications_applied']}")
        print(f"   Errors: {len(results['errors'])}")

        if results['simplifications']:
            print(f"\n✅ Applied Simplifications:")
            operation_counts = {}
            for simp in results['simplifications']:
                operation_counts[simp.operation] = operation_counts.get(simp.operation, 0) + 1

            for operation, count in operation_counts.items():
                print(f"   • {operation}: {count}")

        return results

    def _simplify_compose_file(self, compose_file: Path, service_name: str, dry_run: bool) -> List[VolumeSimplification]:
        """Simplify volume configurations in a single docker-compose file."""
        simplifications = []

        try:
            import yaml
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)

            if not config or 'services' not in config:
                return simplifications

            modified = False

            for svc_name, service_config in config['services'].items():
                if 'volumes' in service_config:
                    original_volumes = service_config['volumes']
                    simplified_volumes, svc_simplifications = self._simplify_service_volumes(
                        svc_name, original_volumes, compose_file
                    )

                    if simplified_volumes != original_volumes:
                        service_config['volumes'] = simplified_volumes
                        modified = True
                        simplifications.extend(svc_simplifications)

            if modified and not dry_run:
                with open(compose_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        except Exception as e:
            print(f"Error simplifying {compose_file}: {e}")

        return simplifications

    def _simplify_service_volumes(self, service_name: str, volumes: List[Any], compose_file: Path) -> Tuple[List[Any], List[VolumeSimplification]]:
        """Simplify volume configurations for a specific service."""
        simplifications = []

        if not isinstance(volumes, list):
            return volumes, simplifications

        # Remove duplicate volumes
        seen_volumes = set()
        deduplicated = []

        for volume in volumes:
            volume_str = str(volume) if not isinstance(volume, str) else volume

            if volume_str not in seen_volumes:
                seen_volumes.add(volume_str)
                deduplicated.append(volume)
            else:
                simplifications.append(VolumeSimplification(
                    file_path=str(compose_file),
                    service_name=service_name,
                    operation="remove_duplicate",
                    description=f"Removed duplicate volume mount: {volume_str}",
                    original_config=volumes,
                    simplified_config=deduplicated
                ))

        # Simplify complex relative paths
        simplified = []
        for volume in deduplicated:
            if isinstance(volume, str):
                original_volume = volume

                # Replace ../../:/app:ro with ./:/app:ro (simpler relative path)
                if volume == '../../:/app:ro':
                    volume = './:/app:ro'
                    simplifications.append(VolumeSimplification(
                        file_path=str(compose_file),
                        service_name=service_name,
                        operation="simplify_relative_path",
                        description="Simplified complex relative path mount",
                        original_config=original_volume,
                        simplified_config=volume
                    ))

                # Simplify service-specific mounts
                if './:/app/services/' in volume and ':rw' in volume:
                    # Replace with named volume
                    volume = f"{service_name}_code:/app:rw"
                    simplifications.append(VolumeSimplification(
                        file_path=str(compose_file),
                        service_name=service_name,
                        operation="use_named_volume",
                        description="Replaced bind mount with named volume for service code",
                        original_config=original_volume,
                        simplified_config=volume
                    ))

            simplified.append(volume)

        return simplified, simplifications


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Volume Simplification Tool")
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Perform dry run (only show changes)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    simplifier = VolumeSimplifier()

    try:
        dry_run = args.dry_run
        results = simplifier.simplify_volumes(dry_run=dry_run)

        if dry_run:
            print("\n💡 This was a DRY RUN. No files were actually modified.")
            print("   Run without --dry-run to apply changes.")

        if args.verbose:
            print("\n📋 Detailed Results:")
            print(f"Files processed: {results['files_processed']}")
            print(f"Simplifications: {results['simplifications_applied']}")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Simplification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
