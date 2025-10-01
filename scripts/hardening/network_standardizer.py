#!/usr/bin/env python3
"""
Network Configuration Standardization System

Analyzes and standardizes Docker network configurations across all services
to ensure consistency and proper isolation.
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class NetworkIssueType(Enum):
    """Types of network configuration issues."""
    MISSING_NETWORKS_SECTION = "missing_networks_section"
    INCONSISTENT_NETWORK_NAMES = "inconsistent_network_names"
    MISSING_DEFAULT_NETWORK = "missing_default_network"
    REDUNDANT_NETWORK_CONNECTIONS = "redundant_network_connections"
    INCONSISTENT_DRIVER_CONFIG = "inconsistent_driver_config"
    SECURITY_CONCERNS = "security_concerns"


@dataclass
class NetworkIssue:
    """Represents a network configuration issue."""
    file_path: str
    service_name: str
    issue_type: NetworkIssueType
    severity: str  # 'error', 'warning', 'info'
    description: str
    current_config: Any
    recommended_config: Any
    can_auto_fix: bool = False


@dataclass
class NetworkAnalysis:
    """Analysis results for network configurations."""
    total_services: int = 0
    total_networks: int = 0
    issues_found: int = 0
    issues_by_type: Dict[NetworkIssueType, int] = field(default_factory=dict)
    network_patterns: Dict[str, int] = field(default_factory=dict)
    issues: List[NetworkIssue] = field(default_factory=list)


class NetworkStandardizer:
    """
    Standardizes Docker network configurations across the ecosystem.

    Ensures consistent network naming, proper isolation, and security practices.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Standard network naming patterns
        self.standard_networks = {
            'default': 'hackathon_default',
            'frontend': 'hackathon_frontend',
            'backend': 'hackathon_backend',
            'database': 'hackathon_database',
            'monitoring': 'hackathon_monitoring',
            'external': 'hackathon_external'
        }

    def analyze_networks(self) -> NetworkAnalysis:
        """
        Analyze network configurations across all Docker Compose files.

        Returns:
            Comprehensive analysis of network configuration patterns
        """
        analysis = NetworkAnalysis()

        # Find all docker-compose files
        compose_files = []
        for pattern in ["docker-compose*.yml", "docker-compose*.yaml"]:
            compose_files.extend(list(self.project_root.rglob(pattern)))

        # Also check service-specific docker-compose files
        for service_dir in self.project_root.glob("services/*"):
            if service_dir.is_dir():
                compose_files.extend(list(service_dir.glob("docker-compose*.yml")))
                compose_files.extend(list(service_dir.glob("docker-compose*.yaml")))

        # Remove duplicates
        compose_files = list(set(compose_files))

        print(f"🔍 Analyzing {len(compose_files)} Docker Compose files for network configurations...")

        for compose_file in compose_files:
            service_name = compose_file.parent.name
            if service_name == 'services':
                service_name = compose_file.name.replace('docker-compose', '').replace('.yml', '').replace('.yaml', '').strip('-')

            analysis.total_services += 1

            try:
                network_config = self._extract_networks_from_compose(compose_file)
                analysis.total_networks += len(network_config.get('networks', {}))

                issues = self._analyze_network_issues(service_name, compose_file, network_config)
                analysis.issues.extend(issues)
                analysis.issues_found += len(issues)

                # Update issue type counts
                for issue in issues:
                    analysis.issues_by_type[issue.issue_type] = analysis.issues_by_type.get(issue.issue_type, 0) + 1

                # Track network patterns
                self._track_network_patterns(network_config, analysis.network_patterns)

            except Exception as e:
                print(f"❌ Error analyzing {compose_file}: {e}")

        return analysis

    def _extract_networks_from_compose(self, compose_file: Path) -> Dict[str, Any]:
        """Extract network configurations from a docker-compose file."""
        networks = {'networks': {}, 'services': {}}

        try:
            import yaml
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)

            if not config:
                return networks

            # Extract networks section
            if 'networks' in config:
                networks['networks'] = config['networks']

            # Extract service network configurations
            if 'services' in config:
                for svc_name, svc_config in config['services'].items():
                    if 'networks' in svc_config:
                        networks['services'][svc_name] = svc_config['networks']

        except Exception as e:
            print(f"Error parsing {compose_file}: {e}")

        return networks

    def _analyze_network_issues(self, service_name: str, compose_file: Path, network_config: Dict[str, Any]) -> List[NetworkIssue]:
        """Analyze network configurations for issues."""
        issues = []

        # Check for missing networks section when services define networks
        if network_config['services'] and not network_config['networks']:
            for svc_name, svc_networks in network_config['services'].items():
                issues.append(NetworkIssue(
                    file_path=str(compose_file),
                    service_name=svc_name,
                    issue_type=NetworkIssueType.MISSING_NETWORKS_SECTION,
                    severity='warning',
                    description="Services define networks but no networks section exists",
                    current_config=svc_networks,
                    recommended_config=self._generate_networks_section(svc_networks),
                    can_auto_fix=True
                ))

        # Check for inconsistent network naming
        all_network_names = set(network_config['networks'].keys())
        for svc_name, svc_networks in network_config['services'].items():
            if isinstance(svc_networks, list):
                for network in svc_networks:
                    if isinstance(network, str) and network not in all_network_names:
                        issues.append(NetworkIssue(
                            file_path=str(compose_file),
                            service_name=svc_name,
                            issue_type=NetworkIssueType.INCONSISTENT_NETWORK_NAMES,
                            severity='info',
                            description=f"Service references undefined network: {network}",
                            current_config=network,
                            recommended_config=self._suggest_standard_network(network),
                            can_auto_fix=True
                        ))

        # Check for default network usage - but don't flag infrastructure files with proper named networks
        has_default_network = any('default' in str(networks) for networks in network_config['services'].values())
        has_named_network = any(isinstance(networks, (list, dict)) and networks for networks in network_config['services'].values())

        # Only suggest default network for application services, not infrastructure/monitoring/prod/simulation
        is_infrastructure = ('infrastructure' in str(compose_file).lower() or
                           'infrastructure' in service_name.lower() or
                           'monitoring' in str(compose_file).lower() or
                           'monitoring' in service_name.lower() or
                           'prod' in str(compose_file).lower() or
                           'simulation' in str(compose_file).lower() or
                           'simulation' in service_name.lower())

        if not has_default_network and not is_infrastructure and has_named_network and network_config['services']:
            issues.append(NetworkIssue(
                file_path=str(compose_file),
                service_name=service_name,
                issue_type=NetworkIssueType.MISSING_DEFAULT_NETWORK,
                severity='info',
                description="Consider adding a default network for service communication",
                current_config=None,
                recommended_config={'default': {'driver': 'bridge'}},
                can_auto_fix=True
            ))

        return issues

    def _track_network_patterns(self, network_config: Dict[str, Any], patterns: Dict[str, int]):
        """Track network usage patterns."""
        for network_name in network_config['networks'].keys():
            patterns[network_name] = patterns.get(network_name, 0) + 1

    def _generate_networks_section(self, service_networks: Any) -> Dict[str, Any]:
        """Generate a networks section based on service network usage."""
        networks = {}
        if isinstance(service_networks, list):
            for network in service_networks:
                if isinstance(network, str):
                    networks[network] = {'driver': 'bridge'}
        elif isinstance(service_networks, dict):
            for network_name in service_networks.keys():
                networks[network_name] = {'driver': 'bridge'}

        return networks

    def _suggest_standard_network(self, network_name: str) -> str:
        """Suggest a standardized network name."""
        # Try to map to standard networks based on keywords
        network_lower = network_name.lower()

        if 'frontend' in network_lower or 'web' in network_lower:
            return self.standard_networks['frontend']
        elif 'backend' in network_lower or 'api' in network_lower:
            return self.standard_networks['backend']
        elif 'database' in network_lower or 'db' in network_lower:
            return self.standard_networks['database']
        elif 'monitoring' in network_lower or 'metrics' in network_lower:
            return self.standard_networks['monitoring']
        else:
            return self.standard_networks['default']

    def generate_standardization_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive network standardization report.

        Returns:
            Report with analysis and recommendations
        """
        print("🔧 Network Standardization Analysis")
        print("=" * 50)

        analysis = self.analyze_networks()

        report = {
            'analysis': {
                'services_analyzed': analysis.total_services,
                'total_networks': analysis.total_networks,
                'issues_found': analysis.issues_found,
                'issues_by_type': {k.value: v for k, v in analysis.issues_by_type.items()},
                'network_patterns': analysis.network_patterns
            },
            'issues': [self._issue_to_dict(issue) for issue in analysis.issues[:20]],  # First 20 issues
            'recommendations': self._generate_recommendations(analysis),
            'standard_networks': self.standard_networks
        }

        print(f"📊 Analysis Results:")
        print(f"  Services analyzed: {analysis.total_services}")
        print(f"  Total networks defined: {analysis.total_networks}")
        print(f"  Issues found: {analysis.issues_found}")

        if analysis.network_patterns:
            print(f"\n🔍 Network Usage Patterns:")
            for network, count in sorted(analysis.network_patterns.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {network}: used in {count} files")

        if analysis.issues_by_type:
            print(f"\n🔍 Issues by Type:")
            for issue_type, count in analysis.issues_by_type.items():
                print(f"  • {issue_type.value}: {count}")

        if analysis.issues:
            print(f"\n⚠️  Sample Issues:")
            for issue in analysis.issues[:5]:
                print(f"  • {issue.service_name}: {issue.description[:60]}...")

        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in report['recommendations'][:5]:
                print(f"  • {rec}")

        return report

    def _issue_to_dict(self, issue: NetworkIssue) -> Dict[str, Any]:
        """Convert NetworkIssue to dictionary."""
        return {
            'file_path': issue.file_path,
            'service_name': issue.service_name,
            'issue_type': issue.issue_type.value,
            'severity': issue.severity,
            'description': issue.description,
            'current_config': issue.current_config,
            'recommended_config': issue.recommended_config,
            'can_auto_fix': issue.can_auto_fix
        }

    def _generate_recommendations(self, analysis: NetworkAnalysis) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        if analysis.issues_by_type.get(NetworkIssueType.MISSING_NETWORKS_SECTION, 0) > 0:
            recommendations.append("Add networks sections to docker-compose files that reference networks")

        if analysis.issues_by_type.get(NetworkIssueType.INCONSISTENT_NETWORK_NAMES, 0) > 0:
            recommendations.append("Standardize network naming conventions across all services")

        if len(analysis.network_patterns) > 10:
            recommendations.append("Consider consolidating similar networks into standard network categories")

        recommendations.extend([
            "Implement network isolation for security",
            "Use internal networks for service-to-service communication",
            "Document network architecture and connectivity",
            "Consider network segmentation by service type",
            "Implement consistent network driver usage"
        ])

        return recommendations

    def standardize_networks(self, mode: str = "analyze") -> Dict[str, Any]:
        """
        Standardize network configurations across all services.

        Args:
            mode: 'analyze', 'dry-run', or 'apply'

        Returns:
            Standardization results
        """
        if mode == "analyze":
            return self.generate_standardization_report()

        # For dry-run and apply modes, we'd implement the fixes
        # For now, just return analysis
        return self.generate_standardization_report()


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Network Standardization System")
    parser.add_argument('--mode', '-m', choices=['analyze', 'dry-run', 'apply'],
                       default='analyze', help='Standardization mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    standardizer = NetworkStandardizer()

    try:
        result = standardizer.standardize_networks(mode=args.mode)

        if args.verbose:
            print("\n📋 Detailed Results:")
            print(f"Mode: {args.mode}")
            print(f"Services analyzed: {result['analysis']['services_analyzed']}")
            print(f"Total networks: {result['analysis']['total_networks']}")
            print(f"Issues found: {result['analysis']['issues_found']}")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Standardization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
