#!/usr/bin/env python3
"""
Automated Service Dependency Validation and Auto-Resolution System
Comprehensive dependency analysis and conflict resolution
"""

import json
import yaml
import subprocess
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DependencyInfo:
    """Service dependency information"""
    service_name: str
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    health_status: str = "unknown"
    startup_time: float = 0
    ready_time: float = 0

@dataclass
class DependencyIssue:
    """Dependency-related issue"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'missing', 'circular', 'unhealthy', 'timeout'
    service_name: str
    dependency_name: str
    message: str
    suggestion: str
    auto_fix_available: bool = False

@dataclass
class DependencyGraph:
    """Complete dependency graph for the ecosystem"""
    services: Dict[str, DependencyInfo] = field(default_factory=dict)
    issues: List[DependencyIssue] = field(default_factory=list)
    startup_order: List[str] = field(default_factory=list)
    circular_dependencies: List[List[str]] = field(default_factory=list)

class DependencyValidator:
    """Comprehensive service dependency validation system"""

    def __init__(self, docker_compose_file: str = "docker-compose.dev.yml",
                 port_registry_file: str = "config/standardized/port_registry.json"):
        self.docker_compose_file = Path(docker_compose_file)
        self.port_registry_file = Path(port_registry_file)
        self.timeout_seconds = 300  # 5 minutes timeout for service startup

    def analyze_dependencies(self) -> DependencyGraph:
        """Perform comprehensive dependency analysis"""
        graph = DependencyGraph()

        # Load configurations
        docker_compose_config = self._load_docker_compose_config()
        port_registry = self._load_port_registry()

        # Build dependency graph
        graph.services = self._build_dependency_graph(docker_compose_config, port_registry)

        # Detect circular dependencies
        graph.circular_dependencies = self._detect_circular_dependencies(graph.services)

        # Validate dependency health
        graph.issues = self._validate_dependency_health(graph.services)

        # Calculate optimal startup order
        if not graph.circular_dependencies:
            graph.startup_order = self._calculate_startup_order(graph.services)

        return graph

    def _build_dependency_graph(self, compose_config: Dict[str, Any],
                               port_registry: Dict[str, Any]) -> Dict[str, DependencyInfo]:
        """Build complete dependency graph from configurations"""
        services = {}

        if 'services' not in compose_config:
            return services

        # First pass: Create service nodes
        for service_name in compose_config['services'].keys():
            services[service_name] = DependencyInfo(service_name=service_name)

        # Second pass: Add dependencies
        for service_name, service_config in compose_config['services'].items():
            if 'depends_on' in service_config:
                depends_on = service_config['depends_on']
                if isinstance(depends_on, list):
                    services[service_name].dependencies = depends_on
                elif isinstance(depends_on, dict):
                    # Handle condition-based dependencies
                    services[service_name].dependencies = list(depends_on.keys())

        # Third pass: Add port registry dependencies
        for service_name, registry_info in port_registry.items():
            if service_name in services and 'dependencies' in registry_info:
                registry_deps = registry_info['dependencies']
                if isinstance(registry_deps, list):
                    # Merge with existing dependencies
                    existing = set(services[service_name].dependencies)
                    existing.update(registry_deps)
                    services[service_name].dependencies = list(existing)

        # Fourth pass: Calculate dependents (reverse dependencies)
        for service_name, service_info in services.items():
            for dep in service_info.dependencies:
                if dep in services:
                    services[dep].dependents.append(service_name)

        return services

    def _detect_circular_dependencies(self, services: Dict[str, DependencyInfo]) -> List[List[str]]:
        """Detect circular dependencies using DFS"""
        circular_deps = []
        visited = set()
        rec_stack = set()

        def dfs(service_name: str, path: List[str]) -> Optional[List[str]]:
            if service_name in rec_stack:
                # Found cycle
                cycle_start = path.index(service_name)
                return path[cycle_start:] + [service_name]

            if service_name in visited:
                return None

            visited.add(service_name)
            rec_stack.add(service_name)
            path.append(service_name)

            service_info = services.get(service_name)
            if service_info:
                for dep in service_info.dependencies:
                    cycle = dfs(dep, path)
                    if cycle:
                        return cycle

            path.pop()
            rec_stack.remove(service_name)
            return None

        for service_name in services.keys():
            if service_name not in visited:
                cycle = dfs(service_name, [])
                if cycle:
                    circular_deps.append(cycle)

        return circular_deps

    def _validate_dependency_health(self, services: Dict[str, DependencyInfo]) -> List[DependencyIssue]:
        """Validate health of service dependencies"""
        issues = []

        for service_name, service_info in services.items():
            # Check if dependencies exist
            for dep in service_info.dependencies:
                if dep not in services:
                    issues.append(DependencyIssue(
                        severity='error',
                        category='missing',
                        service_name=service_name,
                        dependency_name=dep,
                        message=f"Service '{service_name}' depends on non-existent service '{dep}'",
                        suggestion="Remove dependency or ensure dependent service exists"
                    ))

            # Check for services with no dependencies but many dependents (potential bottlenecks)
            if len(service_info.dependencies) == 0 and len(service_info.dependents) > 3:
                issues.append(DependencyIssue(
                    severity='info',
                    category='bottleneck',
                    service_name=service_name,
                    dependency_name='',
                    message=f"Service '{service_name}' has {len(service_info.dependents)} dependents but no dependencies",
                    suggestion="Consider if this service should have infrastructure dependencies"
                ))

            # Check for over-dependency
            if len(service_info.dependencies) > 5:
                issues.append(DependencyIssue(
                    severity='warning',
                    category='complexity',
                    service_name=service_name,
                    dependency_name='',
                    message=f"Service '{service_name}' has {len(service_info.dependencies)} dependencies",
                    suggestion="Consider reducing coupling by introducing intermediary services"
                ))

        return issues

    def _calculate_startup_order(self, services: Dict[str, DependencyInfo]) -> List[str]:
        """Calculate optimal startup order using topological sort"""
        # Kahn's algorithm for topological sorting
        in_degree = {}
        queue = []
        order = []

        # Calculate in-degrees
        for service_name in services:
            in_degree[service_name] = len(services[service_name].dependencies)

        # Find services with no dependencies
        for service_name, degree in in_degree.items():
            if degree == 0:
                queue.append(service_name)

        # Process queue
        while queue:
            current = queue.pop(0)
            order.append(current)

            # Reduce in-degree of dependents
            for dependent in services[current].dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for remaining services (indicates cycles, but we already checked)
        if len(order) != len(services):
            logger.warning("Could not determine complete startup order - possible cycles")

        return order

    def validate_startup_sequence(self, startup_order: List[str]) -> List[DependencyIssue]:
        """Validate that services can start in the calculated order"""
        issues = []

        # Test basic connectivity for each service in startup order
        for i, service_name in enumerate(startup_order):
            # Check if all dependencies are earlier in the startup order
            service_info = self.services.get(service_name)
            if service_info:
                for dep in service_info.dependencies:
                    if dep in startup_order:
                        dep_index = startup_order.index(dep)
                        if dep_index >= i:
                            issues.append(DependencyIssue(
                                severity='warning',
                                category='startup_order',
                                service_name=service_name,
                                dependency_name=dep,
                                message=f"Dependency '{dep}' starts after dependent service '{service_name}'",
                                suggestion="Re-evaluate startup order or dependency requirements"
                            ))

        return issues

    def generate_dependency_report(self, graph: DependencyGraph) -> str:
        """Generate comprehensive dependency report"""
        report_lines = [
            "# Service Dependency Analysis Report",
            "",
            "## Dependency Graph Summary",
            f"- Total Services: {len(graph.services)}",
            f"- Circular Dependencies: {len(graph.circular_dependencies)}",
            f"- Dependency Issues: {len(graph.issues)}",
            "",
            "## Startup Order",
        ]

        if graph.startup_order:
            for i, service in enumerate(graph.startup_order, 1):
                report_lines.append(f"{i:2d}. {service}")
        else:
            report_lines.append("❌ Cannot determine startup order due to circular dependencies")

        report_lines.append("")
        report_lines.append("## Service Dependencies")

        for service_name, service_info in graph.services.items():
            report_lines.append(f"### {service_name}")
            if service_info.dependencies:
                report_lines.append("**Depends on:**")
                for dep in service_info.dependencies:
                    status = "✅" if dep in graph.services else "❌"
                    report_lines.append(f"  - {status} {dep}")
            else:
                report_lines.append("**No dependencies**")

            if service_info.dependents:
                report_lines.append("**Required by:**")
                for dep in service_info.dependents:
                    report_lines.append(f"  - {dep}")

            report_lines.append("")

        if graph.issues:
            report_lines.append("## Issues Found")
            for issue in graph.issues:
                severity_icon = "🔴" if issue.severity == 'error' else "🟡" if issue.severity == 'warning' else "ℹ️"
                report_lines.append(f"- {severity_icon} **{issue.service_name}**: {issue.message}")
                if issue.suggestion:
                    report_lines.append(f"  *Suggestion: {issue.suggestion}*")

        if graph.circular_dependencies:
            report_lines.append("")
            report_lines.append("## Circular Dependencies ⚠️")
            for cycle in graph.circular_dependencies:
                report_lines.append(f"- {' → '.join(cycle)}")

        return "\n".join(report_lines)

    def test_dependency_health(self, graph: DependencyGraph) -> Dict[str, Any]:
        """Test actual health of service dependencies"""
        health_results = {}

        def check_service_health(service_name: str) -> Dict[str, Any]:
            """Check if a service is healthy"""
            try:
                # Get port from port registry
                port_registry = self._load_port_registry()
                if service_name in port_registry:
                    external_port = port_registry[service_name].get('external_port')
                    if external_port:
                        # Try to connect to the service
                        import socket
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(5)
                        result = sock.connect_ex(('localhost', external_port))
                        sock.close()

                        return {
                            'healthy': result == 0,
                            'port': external_port,
                            'error': None if result == 0 else f"Connection failed to port {external_port}"
                        }

                return {
                    'healthy': False,
                    'port': None,
                    'error': 'Port not found in registry'
                }

            except Exception as e:
                return {
                    'healthy': False,
                    'port': None,
                    'error': str(e)
                }

        # Check health for all services
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_service = {
                executor.submit(check_service_health, service_name): service_name
                for service_name in graph.services.keys()
            }

            for future in as_completed(future_to_service):
                service_name = future_to_service[future]
                try:
                    health_results[service_name] = future.result()
                except Exception as e:
                    health_results[service_name] = {
                        'healthy': False,
                        'error': str(e)
                    }

        return health_results

    def auto_fix_dependency_issues(self, graph: DependencyGraph) -> Dict[str, Any]:
        """Attempt to automatically fix dependency issues"""
        fixes_applied = {
            'fixed': [],
            'failed': [],
            'suggestions': []
        }

        # Try to fix missing dependencies by suggesting alternatives
        for issue in graph.issues:
            if issue.category == 'missing' and issue.auto_fix_available:
                # Look for similar service names
                missing_dep = issue.dependency_name
                similar_services = [
                    name for name in graph.services.keys()
                    if missing_dep.lower() in name.lower() or name.lower() in missing_dep.lower()
                ]

                if similar_services:
                    fixes_applied['suggestions'].append({
                        'service': issue.service_name,
                        'missing_dependency': missing_dep,
                        'suggestions': similar_services
                    })

        return fixes_applied

    def _load_docker_compose_config(self) -> Dict[str, Any]:
        """Load docker-compose configuration"""
        try:
            with open(self.docker_compose_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load docker-compose config: {e}")
            return {}

    def _load_port_registry(self) -> Dict[str, Any]:
        """Load port registry"""
        try:
            with open(self.port_registry_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load port registry: {e}")
            return {}

    def print_analysis_report(self, graph: DependencyGraph):
        """Print comprehensive dependency analysis report"""
        print("\n" + "="*80)
        print("🔗 SERVICE DEPENDENCY ANALYSIS REPORT")
        print("="*80)

        print(f"\n📊 SUMMARY")
        print(f"  Services Analyzed: {len(graph.services)}")
        print(f"  Total Dependencies: {sum(len(s.dependencies) for s in graph.services.values())}")
        print(f"  Circular Dependencies: {len(graph.circular_dependencies)}")
        print(f"  Dependency Issues: {len(graph.issues)}")

        if graph.startup_order:
            print(f"\n🚀 RECOMMENDED STARTUP ORDER")
            for i, service in enumerate(graph.startup_order, 1):
                print(f"  {i:2d}. {service}")

        print(f"\n🔗 DEPENDENCY GRAPH")
        for service_name, service_info in graph.services.items():
            deps = len(service_info.dependencies)
            deps_text = f"{deps} dependencies" if deps != 1 else "1 dependency"
            print(f"  {service_name}: {deps_text}")

        if graph.issues:
            print(f"\n🚨 DEPENDENCY ISSUES")
            for issue in graph.issues:
                severity_icon = "🔴" if issue.severity == 'error' else "🟡" if issue.severity == 'warning' else "ℹ️"
                print(f"  {severity_icon} {issue.service_name}: {issue.message}")

        if graph.circular_dependencies:
            print(f"\n⚠️ CIRCULAR DEPENDENCIES")
            for cycle in graph.circular_dependencies:
                print(f"  🔄 {' → '.join(cycle)}")

        print("\n" + "="*80)

    def export_dependency_graph(self, graph: DependencyGraph, output_file: str = "dependency_graph.json"):
        """Export dependency graph to JSON file"""
        graph_data = {
            'services': {},
            'startup_order': graph.startup_order,
            'circular_dependencies': graph.circular_dependencies,
            'issues': [
                {
                    'severity': issue.severity,
                    'category': issue.category,
                    'service': issue.service_name,
                    'dependency': issue.dependency_name,
                    'message': issue.message,
                    'suggestion': issue.suggestion
                }
                for issue in graph.issues
            ]
        }

        for service_name, service_info in graph.services.items():
            graph_data['services'][service_name] = {
                'dependencies': service_info.dependencies,
                'dependents': service_info.dependents,
                'health_status': service_info.health_status
            }

        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)

        print(f"✅ Dependency graph exported to: {output_file}")


def main():
    """Main entry point for dependency validation"""
    validator = DependencyValidator()

    try:
        # Analyze dependencies
        graph = validator.analyze_dependencies()

        # Print analysis report
        validator.print_analysis_report(graph)

        # Export dependency graph
        validator.export_dependency_graph(graph)

        # Generate dependency report
        report = validator.generate_dependency_report(graph)
        with open("dependency_analysis_report.md", "w") as f:
            f.write(report)

        print(f"\n📝 Detailed report saved to: dependency_analysis_report.md")

        # Check for critical issues
        critical_issues = [issue for issue in graph.issues if issue.severity == 'error']
        if critical_issues:
            print(f"\n❌ Found {len(critical_issues)} critical dependency issues!")
            exit(1)
        elif graph.circular_dependencies:
            print(f"\n⚠️ Found {len(graph.circular_dependencies)} circular dependencies!")
            exit(1)
        else:
            print(f"\n✅ Dependency analysis completed successfully!")

    except Exception as e:
        logger.error(f"Dependency validation failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
