#!/usr/bin/env python3
"""
Docker Compose Validator for Pre-Flight Checks

Validates Docker configurations specifically for docker-compose operations.
Used as a pre-flight check before docker-compose commands.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.shared.infrastructure.config.docker_pydantic import (
    validate_docker_compose_file, PYDANTIC_AVAILABLE
)


def validate_docker_compose_for_startup(compose_file: str = "docker-compose.dev.yml") -> bool:
    """
    Validate Docker Compose file specifically for startup operations.
    Based on lessons learned from getting all services running together.

    Args:
        compose_file: Path to docker-compose file to validate

    Returns:
        True if validation passes, False otherwise
    """
    if not PYDANTIC_AVAILABLE:
        print("❌ Pydantic not available for Docker validation")
        return False

    compose_path = project_root / compose_file
    if not compose_path.exists():
        print(f"❌ Docker Compose file not found: {compose_file}")
        return False

    try:
        config = validate_docker_compose_file(compose_path)

        # Additional startup-specific validations based on real-world issues
        issues = []
        warnings = []

        # Check for port conflicts - critical for multi-service startup
        used_ports = set()
        port_conflicts = []

        for service_name, service in config.services.items():
            if service.ports:
                for port_mapping in service.ports:
                    if isinstance(port_mapping, str):
                        # Parse "host:container" or "host:container/protocol"
                        if ':' in port_mapping:
                            host_port = port_mapping.split(':')[0]
                            try:
                                host_port_int = int(host_port)
                                if host_port_int in used_ports:
                                    port_conflicts.append(f"Service '{service_name}' port {host_port_int} conflicts with another service")
                                else:
                                    used_ports.add(host_port_int)
                            except ValueError:
                                warnings.append(f"Service '{service_name}' has non-numeric port: {host_port}")
                    elif isinstance(port_mapping, dict):
                        # Handle dictionary format: {"target": port, "published": port, "protocol": "tcp"}
                        if 'published' in port_mapping:
                            try:
                                host_port_int = int(port_mapping['published'])
                                if host_port_int in used_ports:
                                    port_conflicts.append(f"Service '{service_name}' port {host_port_int} conflicts with another service")
                                else:
                                    used_ports.add(host_port_int)
                            except (ValueError, TypeError):
                                warnings.append(f"Service '{service_name}' has invalid published port: {port_mapping.get('published')}")

        # Check for missing shared volume mounts - critical for service imports
        # Services that actually import from services.shared and need this volume mount
        services_needing_shared = [
            'summarizer-hub', 'project-simulation', 'simulation-dashboard',
            'unified-api-dashboard', 'user-store'
        ]

        for service_name, service in config.services.items():
            if service_name in services_needing_shared:
                has_shared_volume = False
                if service.volumes:
                    for volume in service.volumes:
                        if isinstance(volume, str) and 'services/shared' in volume:
                            has_shared_volume = True
                            break

                if not has_shared_volume:
                    issues.append(f"Service '{service_name}' missing required shared volume mount")

        # Check for services with build but no context
        for service_name, service in config.services.items():
            if service.build and isinstance(service.build, dict):
                if 'context' not in service.build:
                    issues.append(f"Service '{service_name}' has build section but no context")

        # Check for services with depends_on as strings instead of lists
        for service_name, service in config.services.items():
            if isinstance(service.depends_on, str):
                issues.append(f"Service '{service_name}' depends_on should be a list, not a string")

        # Check for health checks that might be too aggressive
        for service_name, service in config.services.items():
            if service.healthcheck:
                # Check for health checks that start immediately (no start_period)
                if hasattr(service.healthcheck, 'start_period') and service.healthcheck.start_period:
                    try:
                        start_period = int(service.healthcheck.start_period)
                        if start_period < 10:
                            warnings.append(f"Service '{service_name}' has very short health check start_period ({start_period}s)")
                    except (ValueError, TypeError):
                        warnings.append(f"Service '{service_name}' has invalid start_period value: {service.healthcheck.start_period}")
                elif not hasattr(service.healthcheck, 'start_period'):
                    warnings.append(f"Service '{service_name}' missing start_period in health check")

        # Check for services that might have circular dependencies
        dependency_graph = {}
        for service_name, service in config.services.items():
            if service.depends_on:
                if isinstance(service.depends_on, dict):
                    # New format: {'service': {'condition': 'service_started'}}
                    deps = list(service.depends_on.keys())
                elif isinstance(service.depends_on, list):
                    # Old format: ['service1', 'service2']
                    deps = service.depends_on
                else:
                    # String format: 'service'
                    deps = [service.depends_on]
                dependency_graph[service_name] = deps

        # Simple cycle detection
        for service, deps in dependency_graph.items():
            for dep in deps:
                if dep in dependency_graph and service in dependency_graph.get(dep, []):
                    issues.append(f"Circular dependency detected between '{service}' and '{dep}'")

        # Report issues
        if issues:
            print("❌ Docker Compose startup validation issues:")
            for issue in issues:
                print(f"  • {issue}")
            return False

        # Report warnings
        if warnings:
            print("⚠️  Docker Compose startup validation warnings:")
            for warning in warnings:
                print(f"  • {warning}")

        if port_conflicts:
            print("❌ Port conflicts detected:")
            for conflict in port_conflicts:
                print(f"  • {conflict}")
            return False

        print(f"✅ Docker Compose file validated for startup: {len(config.services)} services")
        print(f"   • Port conflicts: {len(port_conflicts)}")
        print(f"   • Configuration issues: {len(issues)}")
        print(f"   • Configuration warnings: {len(warnings)}")

        return True

    except Exception as e:
        print(f"❌ Docker Compose validation failed: {str(e)[:100]}...")
        return False


def validate_docker_compose_pre_flight(compose_files: List[str] = None) -> bool:
    """
    Run pre-flight validation for Docker Compose operations.

    Args:
        compose_files: List of docker-compose files to validate

    Returns:
        True if all validations pass
    """
    if compose_files is None:
        compose_files = ["docker-compose.dev.yml"]

    all_valid = True

    for compose_file in compose_files:
        print(f"🔍 Validating {compose_file}...")
        if not validate_docker_compose_for_startup(compose_file):
            all_valid = False

    return all_valid


def main():
    """Main validation script for docker-compose operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Docker Compose Pre-Flight Validator")
    parser.add_argument('--files', '-f', nargs='*', default=["docker-compose.dev.yml"],
                       help='Docker Compose files to validate')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet mode - no output, just exit code')

    args = parser.parse_args()

    if not args.quiet:
        print("🐳 Docker Compose Pre-Flight Validation")
        print("=" * 50)

    success = validate_docker_compose_pre_flight(args.files)

    if not args.quiet:
        if success:
            print("\n✅ All Docker Compose files validated for startup")
        else:
            print("\n❌ Docker Compose validation failed")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
