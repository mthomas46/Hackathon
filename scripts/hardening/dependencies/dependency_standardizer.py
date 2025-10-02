#!/usr/bin/env python3
"""
Dependency Standardization System

Analyzes and standardizes Docker service dependency declarations across all services
to ensure proper startup ordering and health check dependencies.
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


class DependencyIssueType(Enum):
    """Types of dependency configuration issues."""
    MISSING_DEPENDENCIES = "missing_dependencies"
    INCONSISTENT_DEPENDENCY_FORMAT = "inconsistent_dependency_format"
    REDUNDANT_DEPENDENCIES = "redundant_dependencies"
    MISSING_HEALTH_CHECKS = "missing_health_checks"
    CIRCULAR_DEPENDENCIES = "circular_dependencies"


@dataclass
class DependencyIssue:
    """Represents a dependency configuration issue."""
    file_path: str
    service_name: str
    issue_type: DependencyIssueType
    severity: str  # 'error', 'warning', 'info'
    description: str
    current_config: Any
    recommended_config: Any
    can_auto_fix: bool = False


@dataclass
class DependencyAnalysis:
    """Analysis results for dependency configurations."""
    total_services: int = 0
    services_with_dependencies: int = 0
    total_dependencies: int = 0
    issues_found: int = 0
    issues_by_type: Dict[DependencyIssueType, int] = field(default_factory=dict)
    common_dependencies: Dict[str, int] = field(default_factory=dict)
    issues: List[DependencyIssue] = field(default_factory=list)


class DependencyStandardizer:
    """
    Standardizes Docker service dependency declarations across the ecosystem.

    Ensures consistent dependency patterns and proper service startup ordering.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Common dependency patterns by service type
        self.common_dependency_patterns = {
            # Infrastructure services
            'redis': [],
            'postgres': [],
            'mongodb': [],
            'rabbitmq': [],

            # API services typically depend on infrastructure
            'api': ['redis'],
            'backend': ['redis', 'postgres'],
            'database_service': ['postgres'],

            # Frontend services depend on APIs
            'frontend': ['api'],
            'dashboard': ['api', 'backend'],
            'web': ['api'],

            # Specialized services
            'worker': ['redis', 'rabbitmq'],
            'scheduler': ['redis', 'postgres'],
            'monitor': ['postgres'],
            'logger': ['redis'],

            # LLM services often depend on external APIs and redis
            'llm': ['redis'],
            'ai': ['redis'],
            'ml': ['redis', 'postgres']
        }

        # Services that commonly need dependencies
        self.services_requiring_dependencies = {
            'orchestrator', 'analysis-service', 'llm-gateway', 'summarizer-hub',
            'doc-store', 'frontend', 'unified-api-dashboard', 'simulation-dashboard',
            'project-simulation', 'data-services-dashboard', 'bedrock-proxy',
            'source-agent', 'memory-agent', 'user-store', 'external-service-store',
            'mock-data-generator', 'secure-analyzer', 'code-analyzer', 'interpreter',
            'architecture-digitizer', 'github-mcp', 'notification-service',
            'log-collector', 'discovery-agent', 'project-planning-service',
            'ollama', 'prompt_store', 'cli'
        }

    def analyze_dependencies(self) -> DependencyAnalysis:
        """
        Analyze dependency configurations across all Docker Compose files.

        Returns:
            Comprehensive analysis of dependency configuration patterns
        """
        analysis = DependencyAnalysis()

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

        print(f"🔍 Analyzing {len(compose_files)} Docker Compose files for service dependencies...")

        for compose_file in compose_files:
            service_name = compose_file.parent.name
            if service_name == 'services':
                service_name = compose_file.name.replace('docker-compose', '').replace('.yml', '').replace('.yaml', '').strip('-')

            analysis.total_services += 1

            try:
                dependency_config = self._extract_dependencies_from_compose(compose_file)
                analysis.total_dependencies += len(dependency_config)

                # Count services with dependencies
                if dependency_config:
                    analysis.services_with_dependencies += 1

                issues = self._analyze_dependency_issues(service_name, compose_file, dependency_config)
                analysis.issues.extend(issues)
                analysis.issues_found += len(issues)

                # Update issue type counts
                for issue in issues:
                    analysis.issues_by_type[issue.issue_type] = analysis.issues_by_type.get(issue.issue_type, 0) + 1

                # Track common dependencies
                self._track_dependency_patterns(dependency_config, analysis.common_dependencies)

            except Exception as e:
                print(f"❌ Error analyzing {compose_file}: {e}")

        return analysis

    def _extract_dependencies_from_compose(self, compose_file: Path) -> Dict[str, Any]:
        """Extract dependency configurations from a docker-compose file."""
        dependencies = {}

        try:
            import yaml
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)

            if not config or 'services' not in config:
                return dependencies

            for service_name, service_config in config['services'].items():
                if 'depends_on' in service_config:
                    dependencies[service_name] = service_config['depends_on']

        except Exception as e:
            print(f"Error parsing {compose_file}: {e}")

        return dependencies

    def _analyze_dependency_issues(self, service_name: str, compose_file: Path, dependencies: Dict[str, Any]) -> List[DependencyIssue]:
        """Analyze dependency configurations for issues."""
        issues = []

        # Check each service for missing dependencies
        for svc_name, svc_config in dependencies.items():
            # Check if this service should have dependencies but doesn't
            if svc_name in self.services_requiring_dependencies and not svc_config:
                recommended_deps = self._suggest_dependencies(svc_name)
                if recommended_deps:
                    issues.append(DependencyIssue(
                        file_path=str(compose_file),
                        service_name=svc_name,
                        issue_type=DependencyIssueType.MISSING_DEPENDENCIES,
                        severity='warning',
                        description=f"Service '{svc_name}' should declare dependencies",
                        current_config=None,
                        recommended_config=recommended_deps,
                        can_auto_fix=True
                    ))

            # Check dependency format consistency
            if svc_config:
                format_issues = self._check_dependency_format(svc_name, svc_config, compose_file)
                issues.extend(format_issues)

        # Check for services that should have dependencies but are completely missing from analysis
        # This would require checking services that exist but have no depends_on at all
        all_services = self._get_all_services_from_file(compose_file)
        for svc_name in all_services:
            if svc_name in self.services_requiring_dependencies and svc_name not in dependencies:
                recommended_deps = self._suggest_dependencies(svc_name)
                if recommended_deps:
                    issues.append(DependencyIssue(
                        file_path=str(compose_file),
                        service_name=svc_name,
                        issue_type=DependencyIssueType.MISSING_DEPENDENCIES,
                        severity='warning',
                        description=f"Service '{svc_name}' is missing dependency declarations",
                        current_config=None,
                        recommended_config=recommended_deps,
                        can_auto_fix=True
                    ))

        return issues

    def _get_all_services_from_file(self, compose_file: Path) -> List[str]:
        """Get all service names from a docker-compose file."""
        services = []

        try:
            import yaml
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)

            if config and 'services' in config:
                services = list(config['services'].keys())

        except Exception:
            pass

        return services

    def _check_dependency_format(self, service_name: str, dependencies: Any, compose_file: Path) -> List[DependencyIssue]:
        """Check dependency format for consistency."""
        issues = []

        if isinstance(dependencies, list):
            # List format is preferred
            pass
        elif isinstance(dependencies, dict):
            # Dict format with conditions is also acceptable
            pass
        else:
            issues.append(DependencyIssue(
                file_path=str(compose_file),
                service_name=service_name,
                issue_type=DependencyIssueType.INCONSISTENT_DEPENDENCY_FORMAT,
                severity='info',
                description=f"Dependency format should be list or dict, got {type(dependencies)}",
                current_config=dependencies,
                recommended_config=self._normalize_dependency_format(dependencies),
                can_auto_fix=True
            ))

        return issues

    def _suggest_dependencies(self, service_name: str) -> Optional[List[str]]:
        """Suggest dependencies for a service based on its name and type."""
        suggestions = []

        # Check service name patterns
        name_lower = service_name.lower()

        # Infrastructure dependencies
        if any(word in name_lower for word in ['api', 'backend', 'service', 'gateway']):
            suggestions.append('redis')

        if any(word in name_lower for word in ['store', 'database', 'data', 'persistence']):
            suggestions.extend(['redis', 'postgres'])

        if any(word in name_lower for word in ['llm', 'ai', 'ml', 'analysis']):
            suggestions.append('redis')

        if any(word in name_lower for word in ['frontend', 'web', 'dashboard']):
            suggestions.append('redis')  # Most frontends need some backend service

        if any(word in name_lower for word in ['worker', 'queue', 'async']):
            suggestions.extend(['redis', 'rabbitmq'])

        if any(word in name_lower for word in ['monitor', 'metrics', 'health']):
            suggestions.append('redis')

        # Remove duplicates and return
        return list(set(suggestions)) if suggestions else None

    def _normalize_dependency_format(self, dependencies: Any) -> List[str]:
        """Normalize dependency format to a list."""
        if isinstance(dependencies, list):
            return dependencies
        elif isinstance(dependencies, dict):
            return list(dependencies.keys())
        elif isinstance(dependencies, str):
            return [dependencies]
        else:
            return []

    def _track_dependency_patterns(self, dependencies: Dict[str, Any], patterns: Dict[str, int]):
        """Track common dependency patterns."""
        for svc_name, deps in dependencies.items():
            if isinstance(deps, list):
                for dep in deps:
                    if isinstance(dep, str):
                        patterns[dep] = patterns.get(dep, 0) + 1
            elif isinstance(deps, dict):
                for dep in deps.keys():
                    patterns[dep] = patterns.get(dep, 0) + 1

    def generate_standardization_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive dependency standardization report.

        Returns:
            Report with analysis and recommendations
        """
        print("🔧 Dependency Standardization Analysis")
        print("=" * 50)

        analysis = self.analyze_dependencies()

        coverage_percentage = (analysis.services_with_dependencies / analysis.total_services * 100) if analysis.total_services > 0 else 0

        report = {
            'analysis': {
                'services_analyzed': analysis.total_services,
                'services_with_dependencies': analysis.services_with_dependencies,
                'dependency_coverage': f"{coverage_percentage:.1f}%",
                'total_dependencies': analysis.total_dependencies,
                'issues_found': analysis.issues_found,
                'issues_by_type': {k.value: v for k, v in analysis.issues_by_type.items()},
                'common_dependencies': analysis.common_dependencies
            },
            'issues': [self._issue_to_dict(issue) for issue in analysis.issues[:20]],  # First 20 issues
            'recommendations': self._generate_recommendations(analysis)
        }

        print(f"📊 Analysis Results:")
        print(f"  Services analyzed: {analysis.total_services}")
        print(f"  Services with dependencies: {analysis.services_with_dependencies} ({coverage_percentage:.1f}%)")
        print(f"  Total dependencies: {analysis.total_dependencies}")
        print(f"  Issues found: {analysis.issues_found}")

        if analysis.common_dependencies:
            print(f"\n🔍 Most Common Dependencies:")
            for dep, count in sorted(analysis.common_dependencies.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  • {dep}: used by {count} services")

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

    def _issue_to_dict(self, issue: DependencyIssue) -> Dict[str, Any]:
        """Convert DependencyIssue to dictionary."""
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

    def _generate_recommendations(self, analysis: DependencyAnalysis) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        coverage_percentage = (analysis.services_with_dependencies / analysis.total_services * 100) if analysis.total_services > 0 else 0

        if coverage_percentage < 50:
            recommendations.append(f"Only {coverage_percentage:.1f}% of services have dependencies - add missing declarations")

        if analysis.issues_by_type.get(DependencyIssueType.MISSING_DEPENDENCIES, 0) > 0:
            recommendations.append("Add dependency declarations to services that require them for proper startup ordering")

        if analysis.issues_by_type.get(DependencyIssueType.INCONSISTENT_DEPENDENCY_FORMAT, 0) > 0:
            recommendations.append("Standardize dependency declaration format (use lists for simple dependencies)")

        recommendations.extend([
            "Use health checks in dependency conditions for robustness",
            "Document service dependency relationships",
            "Consider dependency injection patterns for complex service graphs",
            "Implement dependency validation in CI/CD pipeline"
        ])

        return recommendations

    def standardize_dependencies(self, mode: str = "analyze") -> Dict[str, Any]:
        """
        Standardize dependency configurations across all services.

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

    parser = argparse.ArgumentParser(description="Dependency Standardization System")
    parser.add_argument('--mode', '-m', choices=['analyze', 'dry-run', 'apply'],
                       default='analyze', help='Standardization mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    standardizer = DependencyStandardizer()

    try:
        result = standardizer.standardize_dependencies(mode=args.mode)

        if args.verbose:
            print("\n📋 Detailed Results:")
            print(f"Mode: {args.mode}")
            print(f"Services analyzed: {result['analysis']['services_analyzed']}")
            print(f"Services with dependencies: {result['analysis']['services_with_dependencies']}")
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
