#!/usr/bin/env python3
"""
Volume Standardization System

Analyzes and standardizes Docker volume configurations across all services
to reduce complexity and ensure consistency.
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


class VolumeIssueType(Enum):
    """Types of volume configuration issues."""
    DUPLICATE_MOUNTS = "duplicate_mounts"
    COMPLEX_RELATIVE_PATHS = "complex_relative_paths"
    INCONSISTENT_PERMISSIONS = "inconsistent_permissions"
    MISSING_NAMED_VOLUMES = "missing_named_volumes"
    REDUNDANT_BIND_MOUNTS = "redundant_bind_mounts"
    INCONSISTENT_VOLUME_NAMING = "inconsistent_volume_naming"


@dataclass
class VolumeIssue:
    """Represents a volume configuration issue."""
    file_path: str
    service_name: str
    issue_type: VolumeIssueType
    severity: str  # 'error', 'warning', 'info'
    description: str
    current_config: Any
    recommended_config: Any
    can_auto_fix: bool = False


@dataclass
class VolumeAnalysis:
    """Analysis results for volume configurations."""
    total_services: int = 0
    total_volumes: int = 0
    issues_found: int = 0
    issues_by_type: Dict[VolumeIssueType, int] = field(default_factory=dict)
    issues: List[VolumeIssue] = field(default_factory=list)
    complexity_score: int = 0


class VolumeStandardizer:
    """
    Standardizes Docker volume configurations across the ecosystem.

    Analyzes volume mounting patterns and provides standardization
    recommendations to reduce complexity and improve maintainability.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Common volume patterns that can be standardized
        self.common_patterns = {
            '../../:/app:ro': 'project_root_readonly',
            './:/app/services/{service}:rw': 'service_code_writable',
            '../../data:/app/data:rw': 'data_directory',
            './logs:/app/logs:rw': 'logs_directory',
            './config:/app/config:ro': 'config_directory'
        }

    def analyze_volumes(self) -> VolumeAnalysis:
        """
        Analyze volume configurations across all Docker Compose files.

        Returns:
            Comprehensive analysis of volume configuration patterns
        """
        analysis = VolumeAnalysis()

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

        print(f"🔍 Analyzing {len(compose_files)} Docker Compose files for volume configurations...")

        for compose_file in compose_files:
            service_name = compose_file.parent.name
            if service_name == 'services':
                service_name = compose_file.name.replace('docker-compose', '').replace('.yml', '').replace('.yaml', '').strip('-')

            analysis.total_services += 1

            try:
                volumes_config = self._extract_volumes_from_compose(compose_file)
                analysis.total_volumes += len(volumes_config)

                issues = self._analyze_volume_issues(service_name, compose_file, volumes_config)
                analysis.issues.extend(issues)
                analysis.issues_found += len(issues)

                # Update issue type counts
                for issue in issues:
                    analysis.issues_by_type[issue.issue_type] = analysis.issues_by_type.get(issue.issue_type, 0) + 1

                # Calculate complexity score
                analysis.complexity_score += self._calculate_complexity_score(volumes_config)

            except Exception as e:
                print(f"❌ Error analyzing {compose_file}: {e}")

        return analysis

    def _extract_volumes_from_compose(self, compose_file: Path) -> List[Dict[str, Any]]:
        """Extract volume configurations from a docker-compose file."""
        volumes = []

        try:
            import yaml
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)

            if not config or 'services' not in config:
                return volumes

            for service_name, service_config in config['services'].items():
                if 'volumes' in service_config:
                    service_volumes = service_config['volumes']
                    if isinstance(service_volumes, list):
                        for volume in service_volumes:
                            volumes.append({
                                'service': service_name,
                                'volume': volume,
                                'file': str(compose_file)
                            })
                    elif isinstance(service_volumes, dict):
                        for vol_name, vol_config in service_volumes.items():
                            volumes.append({
                                'service': service_name,
                                'volume': vol_config,
                                'name': vol_name,
                                'file': str(compose_file)
                            })

        except Exception as e:
            print(f"Error parsing {compose_file}: {e}")

        return volumes

    def _analyze_volume_issues(self, service_name: str, compose_file: Path, volumes: List[Dict[str, Any]]) -> List[VolumeIssue]:
        """Analyze volume configurations for issues."""
        issues = []

        # Check for duplicate mounts - but be smart about legitimate duplicates
        volume_strings = [v['volume'] for v in volumes if isinstance(v['volume'], str)]
        duplicates = self._find_duplicates(volume_strings)

        # Don't flag common legitimate duplicates in dev/infrastructure/prod/service/enhanced/simulation files
        is_dev_file = 'dev' in str(compose_file).lower() or 'development' in str(compose_file).lower()
        is_infra_file = 'infrastructure' in str(compose_file).lower() or 'infra' in str(compose_file).lower()
        is_prod_file = 'prod' in str(compose_file).lower() or 'production' in str(compose_file).lower()
        is_service_file = 'services/' in str(compose_file) and 'docker-compose.yml' in str(compose_file)
        is_enhanced_file = 'enhanced' in str(compose_file).lower() or 'scripts/' in str(compose_file)
        is_simulation_file = 'simulation' in str(compose_file).lower() or 'project-simulation' in str(compose_file)

        legitimate_duplicates = ['../', './:/app:ro', './:/app', './services/shared:/svc/shared', './config.yml', './services/shared', './scripts/', './services:/services', '.:/workspace', '.:/app']

        for dup in duplicates:
            # Skip flagging legitimate duplicates in appropriate files
            volume = dup['volume']
            if (is_dev_file or is_infra_file or is_prod_file or is_service_file or is_enhanced_file or is_simulation_file) and any(legit in volume for legit in legitimate_duplicates):
                continue

            issues.append(VolumeIssue(
                file_path=str(compose_file),
                service_name=service_name,
                issue_type=VolumeIssueType.DUPLICATE_MOUNTS,
                severity='warning',
                description=f"Duplicate volume mount found: {volume}",
                current_config=dup,
                recommended_config={'volume': volume, 'count': dup['count']},
                can_auto_fix=True
            ))

        # Check for complex relative paths
        for volume in volumes:
            if isinstance(volume['volume'], str):
                issues.extend(self._check_complex_paths(service_name, compose_file, volume))

        # Check for inconsistent permissions
        permission_patterns = self._analyze_permissions(volumes)
        for pattern in permission_patterns:
            if pattern['inconsistent']:
                issues.append(VolumeIssue(
                    file_path=str(compose_file),
                    service_name=service_name,
                    issue_type=VolumeIssueType.INCONSISTENT_PERMISSIONS,
                    severity='info',
                    description=f"Inconsistent volume permissions: {pattern['pattern']}",
                    current_config=pattern,
                    recommended_config=self._standardize_permissions(pattern),
                    can_auto_fix=True
                ))

        return issues

    def _find_duplicates(self, volume_list: List[str]) -> List[Dict[str, Any]]:
        """Find duplicate volume mounts."""
        duplicates = []
        seen = {}

        for volume in volume_list:
            if volume in seen:
                seen[volume] += 1
            else:
                seen[volume] = 1

        for volume, count in seen.items():
            if count > 1:
                duplicates.append({
                    'volume': volume,
                    'count': count
                })

        return duplicates

    def _check_complex_paths(self, service_name: str, compose_file: Path, volume: Dict[str, Any]) -> List[VolumeIssue]:
        """Check for complex relative path patterns that can be simplified."""
        issues = []

        volume_str = volume['volume']
        if not isinstance(volume_str, str):
            return issues

        # Check for complex relative paths like ../../:/app:ro
        if '../../:/app:ro' in volume_str:
            issues.append(VolumeIssue(
                file_path=str(compose_file),
                service_name=service_name,
                issue_type=VolumeIssueType.COMPLEX_RELATIVE_PATHS,
                severity='info',
                description="Complex relative path mount can be simplified",
                current_config=volume_str,
                recommended_config="./project:/app:ro",
                can_auto_fix=True
            ))

        # Check for redundant service-specific mounts
        if './:/app/services/' in volume_str and ':rw' in volume_str:
            issues.append(VolumeIssue(
                file_path=str(compose_file),
                service_name=service_name,
                issue_type=VolumeIssueType.REDUNDANT_BIND_MOUNTS,
                severity='warning',
                description="Redundant service code mount - consider using named volume",
                current_config=volume_str,
                recommended_config=f"{service_name}_code:/app:rw",
                can_auto_fix=True
            ))

        return issues

    def _analyze_permissions(self, volumes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze volume permission patterns."""
        patterns = {}

        for volume in volumes:
            if isinstance(volume['volume'], str):
                # Extract permission part (:ro or :rw)
                if ':ro' in volume['volume']:
                    perm = 'ro'
                    path = volume['volume'].replace(':ro', '')
                elif ':rw' in volume['volume']:
                    perm = 'rw'
                    path = volume['volume'].replace(':rw', '')
                else:
                    continue

                key = f"{path}:*"
                if key not in patterns:
                    patterns[key] = {'permissions': set(), 'volumes': []}

                patterns[key]['permissions'].add(perm)
                patterns[key]['volumes'].append(volume)

        # Find inconsistent patterns
        result = []
        for pattern, data in patterns.items():
            result.append({
                'pattern': pattern,
                'permissions': list(data['permissions']),
                'inconsistent': len(data['permissions']) > 1,
                'volumes': data['volumes']
            })

        return result

    def _standardize_permissions(self, pattern: Dict[str, Any]) -> str:
        """Standardize permissions for a pattern (prefer :ro for safety)."""
        # For safety, prefer read-only when there are mixed permissions
        return pattern['pattern'].replace('*', 'ro')

    def _calculate_complexity_score(self, volumes: List[Dict[str, Any]]) -> int:
        """Calculate a complexity score for volume configuration."""
        score = 0

        for volume in volumes:
            volume_str = volume['volume'] if isinstance(volume['volume'], str) else str(volume['volume'])

            # Complex relative paths
            if '../../' in volume_str:
                score += 2

            # Multiple path segments
            if volume_str.count('/') > 2:
                score += 1

            # Named volumes vs bind mounts
            if ':' in volume_str and not volume_str.startswith('./') and not volume_str.startswith('../'):
                score += 1

        return score

    def generate_standardization_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive volume standardization report.

        Returns:
            Report with analysis and recommendations
        """
        print("🔧 Volume Standardization Analysis")
        print("=" * 50)

        analysis = self.analyze_volumes()

        report = {
            'analysis': {
                'services_analyzed': analysis.total_services,
                'total_volumes': analysis.total_volumes,
                'issues_found': analysis.issues_found,
                'complexity_score': analysis.complexity_score,
                'issues_by_type': {k.value: v for k, v in analysis.issues_by_type.items()}
            },
            'issues': [self._issue_to_dict(issue) for issue in analysis.issues[:20]],  # First 20 issues
            'recommendations': self._generate_recommendations(analysis)
        }

        print(f"📊 Analysis Results:")
        print(f"  Services analyzed: {analysis.total_services}")
        print(f"  Total volumes: {analysis.total_volumes}")
        print(f"  Issues found: {analysis.issues_found}")
        print(f"  Complexity score: {analysis.complexity_score}")

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

    def _issue_to_dict(self, issue: VolumeIssue) -> Dict[str, Any]:
        """Convert VolumeIssue to dictionary."""
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

    def _generate_recommendations(self, analysis: VolumeAnalysis) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        if analysis.issues_by_type.get(VolumeIssueType.DUPLICATE_MOUNTS, 0) > 0:
            recommendations.append("Remove duplicate volume mounts to reduce redundancy")

        if analysis.issues_by_type.get(VolumeIssueType.COMPLEX_RELATIVE_PATHS, 0) > 0:
            recommendations.append("Simplify complex relative path mounts using named volumes")

        if analysis.issues_by_type.get(VolumeIssueType.REDUNDANT_BIND_MOUNTS, 0) > 0:
            recommendations.append("Replace redundant bind mounts with named volumes for better persistence")

        if analysis.complexity_score > 50:
            recommendations.append("High volume complexity detected - consider consolidating volume configurations")

        recommendations.extend([
            "Implement consistent volume naming conventions",
            "Use named volumes for persistent data",
            "Document volume mounting patterns",
            "Consider volume driver standardization"
        ])

        return recommendations

    def standardize_volumes(self, mode: str = "analyze") -> Dict[str, Any]:
        """
        Standardize volume configurations across all services.

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

    parser = argparse.ArgumentParser(description="Volume Standardization System")
    parser.add_argument('--mode', '-m', choices=['analyze', 'dry-run', 'apply'],
                       default='analyze', help='Standardization mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    standardizer = VolumeStandardizer()

    try:
        result = standardizer.standardize_volumes(mode=args.mode)

        if args.verbose:
            print("\n📋 Detailed Results:")
            print(f"Mode: {args.mode}")
            print(f"Services analyzed: {result['analysis']['services_analyzed']}")
            print(f"Total volumes: {result['analysis']['total_volumes']}")
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
