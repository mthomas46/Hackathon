#!/usr/bin/env python3
"""
Network Consolidation Tool

Consolidates and standardizes Docker network configurations by
merging similar networks and adding missing default networks.
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
class NetworkConsolidation:
    """Represents a network consolidation operation."""
    file_path: str
    service_name: str
    operation: str
    description: str
    original_config: Any
    consolidated_config: Any
    can_auto_fix: bool = True


class NetworkConsolidator:
    """
    Consolidates Docker network configurations across the ecosystem.

    Merges similar networks, standardizes naming, and adds missing defaults.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Network name mappings for consolidation
        self.network_mappings = {
            # Standardize hackathon networks
            'hackathon': 'hackathon_default',
            'hackathon-network': 'hackathon_default',
            'default': 'hackathon_default',

            # Consolidate monitoring networks
            'monitoring': 'hackathon_monitoring',

            # Consolidate simulation networks
            'simulation-network': 'hackathon_simulation',
            'project-simulation-dev': 'hackathon_simulation',

            # Consolidate external service networks
            'github_net': 'hackathon_external',
            'jira_net': 'hackathon_external',
            'confluence_net': 'hackathon_external',
            'consistency_net': 'hackathon_external',

            # Consolidate documentation networks
            'doc-consistency': 'hackathon_backend',
            'doc-ecosystem-prod': 'hackathon_backend',

            # Consolidate API networks
            'api-dashboard': 'hackathon_frontend',

            # Consolidate security networks
            'security': 'hackathon_backend'
        }

    def consolidate_networks(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Consolidate network configurations across all Docker Compose files.

        Args:
            dry_run: If True, only show what would be changed

        Returns:
            Consolidation results
        """
        results = {
            'files_processed': 0,
            'consolidations_applied': 0,
            'networks_consolidated': 0,
            'defaults_added': 0,
            'errors': [],
            'consolidations': []
        }

        print(f"🔧 Network Consolidation ({'DRY RUN' if dry_run else 'APPLY CHANGES'})")
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
                consolidations = self._consolidate_compose_file(compose_file, service_name, dry_run)
                results['consolidations'].extend(consolidations)
                results['consolidations_applied'] += len(consolidations)

                # Count specific types
                for consolidation in consolidations:
                    if consolidation.operation == 'add_default_network':
                        results['defaults_added'] += 1
                    elif consolidation.operation == 'consolidate_network':
                        results['networks_consolidated'] += 1

                if consolidations:
                    print(f"📄 {compose_file.relative_to(self.project_root)}: {len(consolidations)} consolidations")

            except Exception as e:
                error_msg = f"Error processing {compose_file}: {e}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)

        print(f"\n📊 Consolidation Summary:")
        print(f"   Files processed: {results['files_processed']}")
        print(f"   Consolidations applied: {results['consolidations_applied']}")
        print(f"   Networks consolidated: {results['networks_consolidated']}")
        print(f"   Default networks added: {results['defaults_added']}")
        print(f"   Errors: {len(results['errors'])}")

        if results['consolidations']:
            print(f"\n✅ Applied Consolidations:")
            operation_counts = {}
            for cons in results['consolidations']:
                operation_counts[cons.operation] = operation_counts.get(cons.operation, 0) + 1

            for operation, count in operation_counts.items():
                print(f"   • {operation}: {count}")

        return results

    def _consolidate_compose_file(self, compose_file: Path, service_name: str, dry_run: bool) -> List[NetworkConsolidation]:
        """Consolidate network configurations in a single docker-compose file."""
        consolidations = []

        try:
            import yaml
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)

            if not config or 'services' not in config:
                return consolidations

            modified = False

            # Consolidate network names in networks section
            if 'networks' in config:
                original_networks = config['networks'].copy()
                consolidated_networks, net_consolidations = self._consolidate_network_definitions(
                    config['networks'], compose_file
                )

                if consolidated_networks != original_networks:
                    config['networks'] = consolidated_networks
                    modified = True
                    consolidations.extend(net_consolidations)

            # Update service network references
            for svc_name, service_config in config['services'].items():
                if 'networks' in service_config:
                    original_svc_networks = service_config['networks']
                    consolidated_svc_networks, svc_consolidations = self._consolidate_service_networks(
                        svc_name, service_config['networks'], compose_file
                    )

                    if consolidated_svc_networks != original_svc_networks:
                        service_config['networks'] = consolidated_svc_networks
                        modified = True
                        consolidations.extend(svc_consolidations)

            # Add default network if missing and services exist
            if 'services' in config and config['services']:
                has_default_network = self._has_default_network(config)
                if not has_default_network:
                    if 'networks' not in config:
                        config['networks'] = {}

                    config['networks']['hackathon_default'] = {'driver': 'bridge'}

                    # Add default network to services that don't have explicit networks
                    for svc_name, service_config in config['services'].items():
                        if 'networks' not in service_config:
                            service_config['networks'] = ['hackathon_default']

                    consolidations.append(NetworkConsolidation(
                        file_path=str(compose_file),
                        service_name=service_name,
                        operation="add_default_network",
                        description="Added missing default network for service communication",
                        original_config=None,
                        consolidated_config={'hackathon_default': {'driver': 'bridge'}}
                    ))
                    modified = True

            if modified and not dry_run:
                with open(compose_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        except Exception as e:
            print(f"Error consolidating {compose_file}: {e}")

        return consolidations

    def _consolidate_network_definitions(self, networks: Dict[str, Any], compose_file: Path) -> Tuple[Dict[str, Any], List[NetworkConsolidation]]:
        """Consolidate network definitions in the networks section."""
        consolidations = []
        consolidated = {}

        for network_name, network_config in networks.items():
            # Check if this network should be consolidated
            if network_name in self.network_mappings:
                new_name = self.network_mappings[network_name]

                if new_name != network_name:
                    consolidations.append(NetworkConsolidation(
                        file_path=str(compose_file),
                        service_name="networks",
                        operation="consolidate_network",
                        description=f"Consolidated network '{network_name}' to '{new_name}'",
                        original_config={network_name: network_config},
                        consolidated_config={new_name: network_config}
                    ))

                    # Use the new name
                    network_name = new_name

            consolidated[network_name] = network_config

        return consolidated, consolidations

    def _consolidate_service_networks(self, service_name: str, networks: Any, compose_file: Path) -> Tuple[Any, List[NetworkConsolidation]]:
        """Consolidate network references in service configurations."""
        consolidations = []

        if isinstance(networks, list):
            consolidated_list = []
            for network in networks:
                if isinstance(network, str) and network in self.network_mappings:
                    new_network = self.network_mappings[network]
                    if new_network != network:
                        consolidations.append(NetworkConsolidation(
                            file_path=str(compose_file),
                            service_name=service_name,
                            operation="consolidate_network_ref",
                            description=f"Updated service network reference from '{network}' to '{new_network}'",
                            original_config=network,
                            consolidated_config=new_network
                        ))
                        consolidated_list.append(new_network)
                    else:
                        consolidated_list.append(network)
                else:
                    consolidated_list.append(network)

            return consolidated_list, consolidations

        elif isinstance(networks, dict):
            consolidated_dict = {}
            for network_name, network_config in networks.items():
                if network_name in self.network_mappings:
                    new_name = self.network_mappings[network_name]
                    if new_name != network_name:
                        consolidations.append(NetworkConsolidation(
                            file_path=str(compose_file),
                            service_name=service_name,
                            operation="consolidate_network_ref",
                            description=f"Updated service network reference from '{network_name}' to '{new_name}'",
                            original_config={network_name: network_config},
                            consolidated_config={new_name: network_config}
                        ))
                        consolidated_dict[new_name] = network_config
                    else:
                        consolidated_dict[network_name] = network_config
                else:
                    consolidated_dict[network_name] = network_config

            return consolidated_dict, consolidations

        return networks, consolidations

    def _has_default_network(self, config: Dict[str, Any]) -> bool:
        """Check if the configuration has a default network."""
        if 'networks' in config:
            # Check for any network that could serve as default
            for network_name in config['networks'].keys():
                if 'default' in network_name.lower() or 'hackathon' in network_name.lower():
                    return True

        # Check if services have network configurations
        if 'services' in config:
            for service_config in config['services'].values():
                if 'networks' in service_config:
                    return True

        return False


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Network Consolidation Tool")
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Perform dry run (only show changes)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    consolidator = NetworkConsolidator()

    try:
        dry_run = args.dry_run
        results = consolidator.consolidate_networks(dry_run=dry_run)

        if dry_run:
            print("\n💡 This was a DRY RUN. No files were actually modified.")
            print("   Run without --dry-run to apply changes.")

        if args.verbose:
            print("\n📋 Detailed Results:")
            print(f"Files processed: {results['files_processed']}")
            print(f"Consolidations: {results['consolidations_applied']}")
            print(f"Networks consolidated: {results['networks_consolidated']}")
            print(f"Defaults added: {results['defaults_added']}")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Consolidation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
