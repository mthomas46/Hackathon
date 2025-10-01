#!/usr/bin/env python3
"""
Main Docker Compose Files Standardizer

This script standardizes the main Docker Compose files in the project root
to be consistent with the new configuration management system.

It addresses:
- Inconsistent service configurations
- Complex volume mounts
- Environment variable standardization
- Port mapping consistency
- Health check standardization
"""

import sys
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import re


class MainDockerComposeStandardizer:
    """
    Standardizes main Docker Compose files in the project root.

    Ensures consistency between:
    - docker-compose.dev.yml (development environment)
    - docker-compose.prod.yml (production environment)
    - Other main compose files
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Service port mappings from service-ports.yaml
        self.service_ports = {
            'orchestrator': 5099,
            'doc_store': 5087,
            'analysis-service': 5020,
            'source-agent': 5085,
            'frontend': 3000,
            'memory-agent': 5090,
            'discovery-agent': 5045,
            'notification-service': 5130,
            'prompt_store': 5110,
            'interpreter': 5120,
            'cli': 5130,
            'user-store': 5150,
            'external-service-store': 5140,
            'llm-gateway': 5055,
            'summarizer-hub': 5160,
            'github-mcp': 5030,
            'bedrock-proxy': 5002,
            'secure-analyzer': 5070,
            'code-analyzer': 5025,
            'architecture-digitizer': 5105,
            'project-simulation': 5075,
            'mock-data-generator': 5065,
            'simulation-dashboard': 8501,
            'unified-api-dashboard': 8000,
            'log-collector': 5080
        }

    def standardize_development_compose(self, dry_run: bool = True) -> Dict[str, Any]:
        """Standardize docker-compose.dev.yml for development environment."""
        compose_path = self.project_root / "docker-compose.dev.yml"

        if not compose_path.exists():
            print("❌ docker-compose.dev.yml not found")
            return {}

        print("🔧 Standardizing docker-compose.dev.yml...")

        # Read current compose file
        with open(compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)

        if not compose_config or 'services' not in compose_config:
            print("❌ Invalid docker-compose.dev.yml structure")
            return {}

        standardized_services = {}

        for service_name, service_config in compose_config['services'].items():
            if service_name in ['redis', 'postgres', 'nginx', 'grafana', 'prometheus', 'jaeger']:
                # Infrastructure services - keep as-is for now
                standardized_services[service_name] = service_config
                continue

            # Standardize application services
            standardized_service = self._standardize_service_config(
                service_name, service_config, environment='development'
            )
            standardized_services[service_name] = standardized_service

        # Update the compose config
        compose_config['services'] = standardized_services

        if not dry_run:
            with open(compose_path, 'w') as f:
                yaml.dump(compose_config, f, default_flow_style=False, indent=2, sort_keys=False)
            print("✅ docker-compose.dev.yml standardized")

        return compose_config

    def standardize_production_compose(self, dry_run: bool = True) -> Dict[str, Any]:
        """Standardize docker-compose.prod.yml for production environment."""
        compose_path = self.project_root / "docker-compose.prod.yml"

        if not compose_path.exists():
            print("❌ docker-compose.prod.yml not found")
            return {}

        print("🔧 Standardizing docker-compose.prod.yml...")

        # Read current compose file
        with open(compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)

        if not compose_config or 'services' not in compose_config:
            print("❌ Invalid docker-compose.prod.yml structure")
            return {}

        standardized_services = {}

        for service_name, service_config in compose_config['services'].items():
            if service_name in ['nginx', 'redis', 'postgres', 'grafana', 'prometheus', 'jaeger']:
                # Infrastructure services - keep as-is for now
                standardized_services[service_name] = service_config
                continue

            # Standardize application services with production settings
            standardized_service = self._standardize_service_config(
                service_name, service_config, environment='production'
            )
            standardized_services[service_name] = standardized_service

        # Update the compose config
        compose_config['services'] = standardized_services

        if not dry_run:
            with open(compose_path, 'w') as f:
                yaml.dump(compose_config, f, default_flow_style=False, indent=2, sort_keys=False)
            print("✅ docker-compose.prod.yml standardized")

        return compose_config

    def _standardize_service_config(self, service_name: str, service_config: Dict[str, Any],
                                  environment: str = 'development') -> Dict[str, Any]:
        """Standardize a single service configuration."""
        standardized = service_config.copy()

        # Ensure proper build context for development
        if environment == 'development':
            if 'build' not in standardized:
                standardized['build'] = {
                    'context': '.',
                    'dockerfile': f'services/{service_name}/Dockerfile'
                }
        else:
            # Production uses pre-built images
            if 'image' not in standardized:
                standardized['image'] = f'llm-ecosystem-{service_name}:latest'

        # Standardize working directory
        standardized['working_dir'] = '/app'

        # Simplify volume mounts - remove complex config file mounts
        # Use simple project read-only + service directory approach
        if environment == 'development':
            standardized['volumes'] = [
                './:/app:ro',  # Project read-only
                f'./services/{service_name}:/app/services/{service_name}:rw'  # Service writable
            ]

        # Standardize environment variables
        env_vars = []

        # Add PYTHONPATH
        env_vars.append('PYTHONPATH=/app')

        # Add standard service variables
        if service_name in self.service_ports:
            env_vars.extend([
                f'SERVICE_NAME={service_name}',
                f'SERVICE_API_PORT={self.service_ports[service_name]}',
                f'ENVIRONMENT={environment}'
            ])

        # Add Redis host for services that need it
        redis_services = [
            'orchestrator', 'doc_store', 'analysis-service', 'source-agent',
            'memory-agent', 'code-analyzer', 'prompt_store'
        ]
        if service_name in redis_services:
            env_vars.append('REDIS_API_HOST=redis')

        # Preserve existing service-specific environment variables
        existing_env = service_config.get('environment', [])
        if isinstance(existing_env, list):
            # Filter out duplicates and add new ones
            existing_vars = set()
            for env_item in existing_env:
                if isinstance(env_item, str) and '=' in env_item:
                    var_name = env_item.split('=', 1)[0]
                    existing_vars.add(var_name)

            for env_var in env_vars:
                var_name = env_var.split('=', 1)[0]
                if var_name not in existing_vars:
                    existing_env.append(env_var)
        else:
            # Replace with standardized list
            existing_env = env_vars

        standardized['environment'] = existing_env

        # Standardize ports
        if service_name in self.service_ports:
            port = self.service_ports[service_name]
            standardized['ports'] = [f'{port}:{port}']

        # Add health checks if missing
        if 'healthcheck' not in standardized and service_name in self.service_ports:
            port = self.service_ports[service_name]
            standardized['healthcheck'] = {
                'test': ['CMD', 'curl', '-f', f'http://localhost:{port}/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }

        # Add profiles for development
        if environment == 'development':
            if service_name in ['orchestrator', 'doc_store', 'analysis-service', 'source-agent', 'frontend']:
                standardized['profiles'] = ['core']
            elif service_name in ['memory-agent', 'discovery-agent', 'notification-service', 'log-collector']:
                standardized['profiles'] = ['development']
            elif service_name in ['summarizer-hub', 'bedrock-proxy', 'github-mcp', 'llm-gateway']:
                standardized['profiles'] = ['ai_services']

        return standardized

    def fix_port_inconsistencies(self, compose_file: str, dry_run: bool = True) -> List[str]:
        """Fix port mapping inconsistencies in a compose file."""
        compose_path = self.project_root / compose_file

        if not compose_path.exists():
            return [f"{compose_file} not found"]

        issues = []

        with open(compose_path, 'r') as f:
            compose_config = yaml.safe_load(f)

        if 'services' not in compose_config:
            return [f"No services found in {compose_file}"]

        for service_name, service_config in compose_config['services'].items():
            if service_name not in self.service_ports:
                continue

            expected_port = self.service_ports[service_name]

            # Check SERVICE_API_PORT environment variable
            env_vars = service_config.get('environment', [])
            service_port_env = None

            if isinstance(env_vars, list):
                for env_var in env_vars:
                    if isinstance(env_var, str) and env_var.startswith('SERVICE_API_PORT='):
                        service_port_env = int(env_var.split('=', 1)[1])
                        break

            # Check port mapping
            ports = service_config.get('ports', [])
            actual_port = None

            if ports and isinstance(ports, list) and ports[0]:
                port_mapping = str(ports[0])
                if ':' in port_mapping:
                    external_port = port_mapping.split(':')[0]
                    try:
                        actual_port = int(external_port)
                    except ValueError:
                        pass

            # Report inconsistencies
            if service_port_env and service_port_env != expected_port:
                issues.append(f"{service_name}: SERVICE_API_PORT={service_port_env}, expected {expected_port}")

            if actual_port and actual_port != expected_port:
                issues.append(f"{service_name}: Port mapping {actual_port}:{expected_port}, expected {expected_port}:{expected_port}")

        return issues

    def generate_standardized_service_template(self, service_name: str, environment: str = 'development') -> Dict[str, Any]:
        """Generate a standardized service configuration template."""
        if service_name not in self.service_ports:
            return {}

        port = self.service_ports[service_name]

        template = {
            'build' if environment == 'development' else 'image': {
                'context': '.',
                'dockerfile': f'services/{service_name}/Dockerfile'
            } if environment == 'development' else f'llm-ecosystem-{service_name}:latest',
            'working_dir': '/app',
            'volumes': [
                './:/app:ro',
                f'./services/{service_name}:/app/services/{service_name}:rw'
            ] if environment == 'development' else [],
            'environment': [
                'PYTHONPATH=/app',
                f'SERVICE_NAME={service_name}',
                f'SERVICE_API_PORT={port}',
                f'ENVIRONMENT={environment}'
            ],
            'ports': [f'{port}:{port}'],
            'healthcheck': {
                'test': ['CMD', 'curl', '-f', f'http://localhost:{port}/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        }

        # Add Redis dependency for services that need it
        redis_services = [
            'orchestrator', 'doc_store', 'analysis-service', 'source-agent',
            'memory-agent', 'code-analyzer', 'prompt_store'
        ]
        if service_name in redis_services:
            template['environment'].append('REDIS_API_HOST=redis')
            template['depends_on'] = {
                'redis': {'condition': 'service_healthy'}
            }

        # Add profiles for development
        if environment == 'development':
            if service_name in ['orchestrator', 'doc_store', 'analysis-service', 'source-agent', 'frontend']:
                template['profiles'] = ['core']
            elif service_name in ['memory-agent', 'discovery-agent', 'notification-service', 'log-collector']:
                template['profiles'] = ['development']
            elif service_name in ['summarizer-hub', 'bedrock-proxy', 'github-mcp', 'llm-gateway']:
                template['profiles'] = ['ai_services']

        return template


def main():
    """Main standardization function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Standardize main Docker Compose files for consistency"
    )

    parser.add_argument('action', choices=[
        'standardize-dev', 'standardize-prod', 'check-ports',
        'generate-template', 'audit-all'
    ], help='Action to perform')

    parser.add_argument('--service', help='Service name for template generation')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without applying')
    parser.add_argument('--output', help='Output file for results')

    args = parser.parse_args()

    standardizer = MainDockerComposeStandardizer()

    if args.action == 'standardize-dev':
        result = standardizer.standardize_development_compose(dry_run=args.dry_run)
        if args.dry_run:
            print("📋 Dry run completed. Use --dry-run=false to apply changes.")
        else:
            print("✅ Development compose file standardized.")

    elif args.action == 'standardize-prod':
        result = standardizer.standardize_production_compose(dry_run=args.dry_run)
        if args.dry_run:
            print("📋 Dry run completed. Use --dry-run=false to apply changes.")
        else:
            print("✅ Production compose file standardized.")

    elif args.action == 'check-ports':
        print("🔍 Checking port inconsistencies...")

        dev_issues = standardizer.fix_port_inconsistencies('docker-compose.dev.yml')
        prod_issues = standardizer.fix_port_inconsistencies('docker-compose.prod.yml')

        if dev_issues:
            print("\ndocker-compose.dev.yml issues:")
            for issue in dev_issues:
                print(f"  ❌ {issue}")

        if prod_issues:
            print("\ndocker-compose.prod.yml issues:")
            for issue in prod_issues:
                print(f"  ❌ {issue}")

        if not dev_issues and not prod_issues:
            print("✅ No port inconsistencies found!")

    elif args.action == 'generate-template':
        if not args.service:
            print("❌ --service required for template generation")
            return 1

        template = standardizer.generate_standardized_service_template(args.service)

        if template:
            print(f"📄 Standardized template for {args.service}:")
            print(yaml.dump(template, default_flow_style=False, indent=2))

            if args.output:
                with open(args.output, 'w') as f:
                    yaml.dump(template, f, default_flow_style=False, indent=2)
                print(f"💾 Template saved to {args.output}")
        else:
            print(f"❌ Service {args.service} not found in port registry")

    elif args.action == 'audit-all':
        print("🔍 Comprehensive audit of main Docker Compose files...")

        # Check for inconsistencies
        dev_issues = standardizer.fix_port_inconsistencies('docker-compose.dev.yml')
        prod_issues = standardizer.fix_port_inconsistencies('docker-compose.prod.yml')

        print(f"\n📊 Audit Results:")
        print(f"  Development compose issues: {len(dev_issues)}")
        print(f"  Production compose issues: {len(prod_issues)}")

        if dev_issues or prod_issues:
            print("\n🚨 Issues found:")
            for issue in dev_issues + prod_issues:
                print(f"  ❌ {issue}")
        else:
            print("✅ All main Docker Compose files are consistent!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
