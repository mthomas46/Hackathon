#!/usr/bin/env python3
"""
Configuration Drift Detector for Hackathon Ecosystem

This script detects configuration inconsistencies across the ecosystem:
- Environment variable mismatches
- Docker Compose vs service configuration drift
- Port mapping inconsistencies
- Service dependency mismatches
"""

import os
import yaml
import json
import re
from typing import Dict, List, Tuple, Set
from pathlib import Path
import subprocess
import sys

def load_docker_compose_config() -> Dict:
    """Load docker-compose.dev.yml configuration."""
    try:
        with open('docker-compose.dev.yml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading docker-compose.dev.yml: {e}")
        return {}

def load_config_yml() -> Dict:
    """Load config.yml configuration."""
    try:
        with open('config.yml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config.yml: {e}")
        return {}

def get_service_env_vars(service_name: str, docker_config: Dict) -> Dict[str, str]:
    """Extract environment variables for a service from docker-compose."""
    if 'services' not in docker_config or service_name not in docker_config['services']:
        return {}

    service = docker_config['services'][service_name]
    env_vars = {}

    if 'environment' in service:
        env = service['environment']
        if isinstance(env, list):
            for item in env:
                if isinstance(item, str) and '=' in item:
                    key, value = item.split('=', 1)
                    env_vars[key] = value
                elif isinstance(item, dict):
                    env_vars.update(item)
        elif isinstance(env, dict):
            env_vars.update(env)

    return env_vars

def check_environment_variables(docker_config: Dict) -> List[str]:
    """Check for environment variable consistency issues."""
    issues = []

    if 'services' not in docker_config:
        issues.append("No services defined in docker-compose.dev.yml")
        return issues

    # Services that should have standard environment variables (Python/FastAPI services)
    python_services = {
        'orchestrator', 'doc_store', 'analysis-service', 'source-agent', 'frontend',
        'summarizer-hub', 'architecture-digitizer', 'llm-gateway', 'mock-data-generator',
        'memory-agent', 'discovery-agent', 'notification-service', 'prompt_store',
        'interpreter', 'code-analyzer', 'secure-analyzer', 'log-collector',
        'unified-api-dashboard'
    }

    # Infrastructure services that don't need standard env vars
    infra_services = {'redis', 'ollama', 'cli', 'simulation-dashboard', 'data-services-dashboard'}

    for service_name, service_config in docker_config['services'].items():
        env_vars = get_service_env_vars(service_name, docker_config)

        # Only check for required environment variables on Python services
        if service_name in python_services:
            required_vars = ['SERVICE_NAME', 'SERVICE_PORT', 'ENVIRONMENT']
            for var in required_vars:
                if var not in env_vars:
                    issues.append(f"Service '{service_name}' missing required env var: {var}")

            # Check for inconsistent service names
            if 'SERVICE_NAME' in env_vars and env_vars['SERVICE_NAME'] != service_name:
                issues.append(f"Service '{service_name}' has SERVICE_NAME='{env_vars['SERVICE_NAME']}' (should match service name)")

            # Check port consistency
            if 'ports' in service_config and 'SERVICE_PORT' in env_vars:
                ports = service_config['ports']
                service_port = env_vars['SERVICE_PORT']

                # Extract external port from port mappings
                external_ports = []
                for port_mapping in ports:
                    if isinstance(port_mapping, str):
                        # Format: "external:internal" or "port"
                        if ':' in port_mapping:
                            external_port = port_mapping.split(':')[0]
                        else:
                            external_port = port_mapping
                        external_ports.append(external_port)

                if service_port not in external_ports:
                    issues.append(f"Service '{service_name}' SERVICE_PORT='{service_port}' not found in external port mappings {external_ports}")

        # Special handling for services with complex port mappings
        # (This section can be removed now that we check external ports above)

    return issues

def check_service_dependencies(docker_config: Dict) -> List[str]:
    """Check for service dependency consistency."""
    issues = []

    if 'services' not in docker_config:
        return issues

    for service_name, service_config in docker_config['services'].items():
        if 'depends_on' in service_config:
            depends_on = service_config['depends_on']

            # Handle different depends_on formats
            dependencies = set()
            if isinstance(depends_on, list):
                dependencies = set(depends_on)
            elif isinstance(depends_on, dict):
                dependencies = set(depends_on.keys())

            # Check if all dependencies exist
            all_services = set(docker_config['services'].keys())
            missing_deps = dependencies - all_services
            if missing_deps:
                issues.append(f"Service '{service_name}' depends on non-existent services: {missing_deps}")

    return issues

def check_port_conflicts(docker_config: Dict) -> List[str]:
    """Check for port mapping conflicts."""
    issues = []
    port_mappings = {}  # external_port -> [(service, internal_port)]

    if 'services' not in docker_config:
        return issues

    for service_name, service_config in docker_config['services'].items():
        if 'ports' in service_config:
            ports = service_config['ports']
            for port_mapping in ports:
                if isinstance(port_mapping, str):
                    if ':' in port_mapping:
                        external, internal = port_mapping.split(':')
                    else:
                        external = internal = port_mapping

                    try:
                        external_port = int(external)
                        internal_port = int(internal)

                        if external_port in port_mappings:
                            port_mappings[external_port].append((service_name, internal_port))
                        else:
                            port_mappings[external_port] = [(service_name, internal_port)]
                    except ValueError:
                        issues.append(f"Service '{service_name}' has invalid port mapping: {port_mapping}")

    # Check for conflicts
    for external_port, mappings in port_mappings.items():
        if len(mappings) > 1:
            services = [f"{service}({internal})" for service, internal in mappings]
            issues.append(f"Port conflict on external port {external_port}: {services}")

    return issues

def check_volume_consistency(docker_config: Dict) -> List[str]:
    """Check for volume configuration consistency."""
    issues = []

    if 'volumes' not in docker_config:
        return issues

    defined_volumes = set(docker_config['volumes'].keys())

    for service_name, service_config in docker_config['services'].items():
        if 'volumes' in service_config:
            volumes = service_config['volumes']
            for volume in volumes:
                if isinstance(volume, str):
                    # Named volume format: "volume_name:/path" or just "volume_name"
                    volume_name = volume.split(':')[0] if ':' in volume else volume
                    if volume_name not in defined_volumes and not volume_name.startswith('./') and not volume_name.startswith('/'):
                        issues.append(f"Service '{service_name}' uses undefined named volume: {volume_name}")

    return issues

def check_network_consistency(docker_config: Dict) -> List[str]:
    """Check for network configuration consistency."""
    issues = []

    # Check if services reference networks that don't exist
    if 'networks' in docker_config:
        defined_networks = set(docker_config['networks'].keys())
    else:
        defined_networks = set()

    for service_name, service_config in docker_config['services'].items():
        if 'networks' in service_config:
            service_networks = service_config['networks']
            if isinstance(service_networks, list):
                service_network_set = set(service_networks)
            elif isinstance(service_networks, dict):
                service_network_set = set(service_networks.keys())
            else:
                service_network_set = {service_networks}

            undefined_networks = service_network_set - defined_networks
            if undefined_networks:
                issues.append(f"Service '{service_name}' references undefined networks: {undefined_networks}")

    return issues

def main():
    """Main configuration drift detection function."""
    print("🔍 Configuration Drift Detector - Hackathon Ecosystem")
    print("=" * 55)

    # Load configurations
    docker_config = load_docker_compose_config()
    config_yml = load_config_yml()

    if not docker_config:
        print("❌ Cannot proceed without docker-compose.dev.yml")
        sys.exit(1)

    all_issues = []

    # Run various checks
    print("🔧 Checking environment variables...")
    env_issues = check_environment_variables(docker_config)
    all_issues.extend(env_issues)
    print(f"   Found {len(env_issues)} environment variable issues")

    print("🔗 Checking service dependencies...")
    dep_issues = check_service_dependencies(docker_config)
    all_issues.extend(dep_issues)
    print(f"   Found {len(dep_issues)} dependency issues")

    print("🚪 Checking port mappings...")
    port_issues = check_port_conflicts(docker_config)
    all_issues.extend(port_issues)
    print(f"   Found {len(port_issues)} port mapping issues")

    print("💾 Checking volume configurations...")
    volume_issues = check_volume_consistency(docker_config)
    all_issues.extend(volume_issues)
    print(f"   Found {len(volume_issues)} volume issues")

    print("🌐 Checking network configurations...")
    network_issues = check_network_consistency(docker_config)
    all_issues.extend(network_issues)
    print(f"   Found {len(network_issues)} network issues")

    # Report results
    total_issues = len(all_issues)

    if total_issues > 0:
        print(f"\n❌ Found {total_issues} configuration drift issues:")
        print("-" * 50)

        for i, issue in enumerate(all_issues, 1):
            print(f"{i:2d}. {issue}")

        print("\n💡 Fix these configuration inconsistencies to ensure ecosystem stability.")
        sys.exit(1)
    else:
        print("\n✅ No configuration drift detected!")
        print("   All configurations are consistent across the ecosystem.")
        sys.exit(0)

if __name__ == "__main__":
    main()
