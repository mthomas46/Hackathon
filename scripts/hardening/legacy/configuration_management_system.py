#!/usr/bin/env python3
"""
LEGACY: Unified Configuration Management System for LLM Documentation Ecosystem

⚠️  DEPRECATED: This script has been superseded by the new centralized configuration
management system. Use `scripts/hardening/unified_config_manager.py` instead.

This legacy system provides:
1. Centralized port configuration management across all deployment methods
2. Service discovery and registration validation
3. Configuration consistency validation between local, Docker, and docker-compose deployments
4. Automated standardization of service configurations
5. Comprehensive reporting and conflict resolution

For new development, use:
  python scripts/hardening/unified_config_manager.py

Migration guide: See CONFIGURATION_STANDARDIZATION_COMPLETE.md
"""

import json
import yaml
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeploymentType(Enum):
    """Types of service deployments"""
    LOCAL = "local"
    DOCKER_COMPOSE = "docker-compose"
    DOCKER_STANDALONE = "docker-standalone"

class ConfigSource(Enum):
    """Sources of configuration data"""
    SERVICE_API_PORTS_YAML = "service-ports.yaml"
    DOCKER_COMPOSE_YAML = "docker-compose.yml"
    DOCKERFILE = "Dockerfile"
    SERVICE_CONFIG_YAML = "config.yml"
    ENVIRONMENT_VARIABLES = "environment"

@dataclass
class PortConfiguration:
    """Standardized port configuration for a service"""
    service_name: str
    internal_port: int
    external_port: int
    protocol: str = "tcp"
    description: str = ""
    deployment_type: DeploymentType = DeploymentType.DOCKER_COMPOSE
    config_source: ConfigSource = ConfigSource.SERVICE_API_PORTS_YAML

@dataclass
class ServiceConfiguration:
    """Complete service configuration"""
    service_name: str
    ports: List[PortConfiguration] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    health_endpoint: str = "/health"
    config_files: List[str] = field(default_factory=list)
    dockerfile_path: Optional[str] = None

@dataclass
class ConfigurationConflict:
    """Represents a configuration conflict"""
    service_name: str
    conflict_type: str
    description: str
    affected_sources: List[ConfigSource]
    severity: str = "medium"
    resolution_suggestion: str = ""

class UnifiedConfigurationManager:
    """
    Unified Configuration Management System

    Provides comprehensive configuration management across all deployment methods:
    - Port standardization and conflict detection
    - Service discovery and registration validation
    - Cross-deployment configuration consistency
    - Automated configuration generation and validation
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.services_dir = self.project_root / "services"
        self.config_dir = self.project_root / "config"
        self.scripts_dir = self.project_root / "scripts"

        # Configuration data
        self.service_ports_config = {}
        self.docker_compose_config = {}
        self.service_configs = {}
        self.dockerfile_configs = {}

        # Analysis results
        self.port_configurations = {}
        self.service_configurations = {}
        self.configuration_conflicts = []
        self.validation_reports = {}

    def load_all_configurations(self) -> Dict[str, Any]:
        """Load all configuration sources"""
        logger.info("Loading all configuration sources...")

        results = {}

        # Load centralized port registry
        results['service_ports'] = self._load_service_ports_config()

        # Load docker-compose configurations
        results['docker_compose'] = self._load_docker_compose_configs()

        # Load individual service configurations
        results['service_configs'] = self._load_service_configs()

        # Load Dockerfile configurations
        results['dockerfiles'] = self._load_dockerfile_configs()

        # Load environment variables
        results['environment'] = self._load_environment_configs()

        return results

    def _load_service_ports_config(self) -> Dict[str, Any]:
        """Load the centralized service-ports.yaml configuration"""
        config_path = self.config_dir / "service-ports.yaml"

        if not config_path.exists():
            logger.warning(f"Service ports config not found: {config_path}")
            return {}

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.service_ports_config = config
                return config
        except Exception as e:
            logger.error(f"Failed to load service ports config: {e}")
            return {}

    def _load_docker_compose_configs(self) -> Dict[str, Any]:
        """Load all docker-compose configuration files"""
        compose_files = [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml",
            "docker-compose.monitoring.yml",
            "docker-compose.infrastructure.yml",
            "docker-compose.services.yml",
            "docker-compose.simulation.yml"
        ]

        configs = {}
        for compose_file in compose_files:
            compose_path = self.project_root / compose_file
            if compose_path.exists():
                try:
                    with open(compose_path, 'r') as f:
                        config = yaml.safe_load(f)
                        configs[compose_file] = config
                        if compose_file == "docker-compose.dev.yml":
                            self.docker_compose_config = config
                except Exception as e:
                    logger.error(f"Failed to load {compose_file}: {e}")

        return configs

    def _load_service_configs(self) -> Dict[str, Any]:
        """Load individual service configuration files"""
        service_configs = {}

        if not self.services_dir.exists():
            return service_configs

        for service_dir in self.services_dir.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith('_'):
                config_path = service_dir / "config.yml"
                if config_path.exists():
                    try:
                        with open(config_path, 'r') as f:
                            config = yaml.safe_load(f)
                            service_configs[service_dir.name] = config
                    except Exception as e:
                        logger.error(f"Failed to load config for {service_dir.name}: {e}")

        self.service_configs = service_configs
        return service_configs

    def _load_dockerfile_configs(self) -> Dict[str, Any]:
        """Extract configuration information from Dockerfiles"""
        dockerfile_configs = {}

        if not self.services_dir.exists():
            return dockerfile_configs

        for service_dir in self.services_dir.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith('_'):
                dockerfile_path = service_dir / "Dockerfile"
                if dockerfile_path.exists():
                    try:
                        config = self._parse_dockerfile(dockerfile_path)
                        dockerfile_configs[service_dir.name] = config
                    except Exception as e:
                        logger.error(f"Failed to parse Dockerfile for {service_dir.name}: {e}")

        self.dockerfile_configs = dockerfile_configs
        return dockerfile_configs

    def _parse_dockerfile(self, dockerfile_path: Path) -> Dict[str, Any]:
        """Parse configuration information from a Dockerfile"""
        config = {
            'env_vars': {},
            'ports': [],
            'working_dir': '/app',
            'entrypoint': None,
            'cmd': None
        }

        try:
            with open(dockerfile_path, 'r') as f:
                content = f.read()

            # Extract ENV variables
            env_matches = re.findall(r'ENV\s+(\w+)\s*=\s*["\']?([^"\']+)["\']?', content, re.IGNORECASE)
            for var_name, var_value in env_matches:
                config['env_vars'][var_name] = var_value

            # Extract EXPOSE directives
            expose_matches = re.findall(r'EXPOSE\s+(\d+)', content, re.IGNORECASE)
            config['ports'] = [int(port) for port in expose_matches]

            # Extract WORKDIR
            workdir_match = re.search(r'WORKDIR\s+([^\n]+)', content, re.IGNORECASE)
            if workdir_match:
                config['working_dir'] = workdir_match.group(1).strip()

            # Extract CMD
            cmd_match = re.search(r'CMD\s*\[(.*?)\]', content, re.DOTALL)
            if cmd_match:
                config['cmd'] = cmd_match.group(1).strip()

        except Exception as e:
            logger.error(f"Error parsing Dockerfile {dockerfile_path}: {e}")

        return config

    def _load_environment_configs(self) -> Dict[str, Any]:
        """Load environment variable configurations"""
        env_config = {}

        # Check for .env files
        env_files = [
            self.project_root / ".env",
            self.project_root / ".env.local",
            self.project_root / ".env.dev"
        ]

        for env_file in env_files:
            if env_file.exists():
                try:
                    with open(env_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                if '=' in line:
                                    key, value = line.split('=', 1)
                                    env_config[key.strip()] = value.strip()
                except Exception as e:
                    logger.error(f"Failed to load env file {env_file}: {e}")

        return env_config

    def standardize_port_configurations(self) -> Dict[str, PortConfiguration]:
        """Create standardized port configurations from all sources"""
        logger.info("Standardizing port configurations...")

        standardized_ports = {}

        # Start with service-ports.yaml as the authoritative source
        for category, services in self.service_ports_config.items():
            if isinstance(services, dict):
                for service_name, config in services.items():
                    if isinstance(config, dict) and 'external_port' in config:
                        port_config = PortConfiguration(
                            service_name=service_name,
                            internal_port=config.get('internal_port', config['external_port']),
                            external_port=config['external_port'],
                            description=config.get('description', ''),
                            config_source=ConfigSource.SERVICE_API_PORTS_YAML
                        )
                        standardized_ports[service_name] = port_config

        # Validate against docker-compose configurations
        if 'services' in self.docker_compose_config:
            for service_name, service_config in self.docker_compose_config['services'].items():
                if service_name in standardized_ports:
                    # Check port mapping consistency
                    expected_port = standardized_ports[service_name]
                    if 'ports' in service_config:
                        actual_ports = self._extract_ports_from_docker_compose(service_config['ports'])
                        if actual_ports and actual_ports[0]['external'] != expected_port.external_port:
                            self.configuration_conflicts.append(ConfigurationConflict(
                                service_name=service_name,
                                conflict_type="port_mapping_mismatch",
                                description=f"Docker Compose external port {actual_ports[0]['external']} != service-ports external port {expected_port.external_port}",
                                affected_sources=[ConfigSource.SERVICE_API_PORTS_YAML, ConfigSource.DOCKER_COMPOSE_YAML],
                                severity="high",
                                resolution_suggestion="Update docker-compose.yml to match service-ports.yaml"
                            ))

        self.port_configurations = standardized_ports
        return standardized_ports

    def _extract_ports_from_docker_compose(self, ports_config: List[str]) -> List[Dict[str, int]]:
        """Extract port mappings from docker-compose port configuration"""
        ports = []

        for port_mapping in ports_config:
            # Handle formats like "5087:5010", "5087:5010/tcp"
            port_part = port_mapping.split('/')[0]

            if ':' in port_part:
                if port_part.count(':') == 1:
                    external, internal = port_part.split(':')
                else:
                    # IP:external:internal format
                    _, external, internal = port_part.split(':')

                try:
                    ports.append({
                        'external': int(external),
                        'internal': int(internal)
                    })
                except ValueError:
                    continue

        return ports

    def validate_service_discovery(self) -> Dict[str, Any]:
        """Validate service discovery and registration configurations"""
        logger.info("Validating service discovery configurations...")

        discovery_validation = {
            'service_registrations': {},
            'dependency_mappings': {},
            'endpoint_consistency': {},
            'environment_variables': {}
        }

        # Check service registrations in docker-compose
        if 'services' in self.docker_compose_config:
            for service_name, service_config in self.docker_compose_config['services'].items():
                registration_info = {
                    'registered': service_name in self.service_ports_config.get('core_services', {}),
                    'ports_configured': 'ports' in service_config,
                    'environment_configured': 'environment' in service_config,
                    'health_check_configured': 'healthcheck' in service_config
                }

                discovery_validation['service_registrations'][service_name] = registration_info

                # Check environment variables for service discovery
                if 'environment' in service_config:
                    env_vars = service_config['environment']
                    if isinstance(env_vars, list):
                        env_dict = {}
                        for env_var in env_vars:
                            if isinstance(env_var, str) and '=' in env_var:
                                key, value = env_var.split('=', 1)
                                env_dict[key] = value
                        env_vars = env_dict

                    if isinstance(env_vars, dict):
                        # Check for service URL environment variables
                        service_urls = {}
                        for key, value in env_vars.items():
                            if '_URL' in key or '_SERVICE_API_HOST' in key:
                                service_urls[key] = value

                        if service_urls:
                            discovery_validation['environment_variables'][service_name] = service_urls

        # Validate dependency mappings
        for service_name, service_config in self.service_configs.items():
            if 'dependencies' in service_config or 'service_dependencies' in service_config:
                deps = service_config.get('dependencies') or service_config.get('service_dependencies', [])
                discovery_validation['dependency_mappings'][service_name] = deps

        return discovery_validation

    def generate_configuration_report(self) -> Dict[str, Any]:
        """Generate comprehensive configuration report"""
        logger.info("Generating configuration report...")

        # Load all configurations
        all_configs = self.load_all_configurations()

        # Standardize port configurations
        standardized_ports = self.standardize_port_configurations()

        # Validate service discovery
        discovery_validation = self.validate_service_discovery()

        # Generate cross-deployment consistency analysis
        consistency_analysis = self._analyze_deployment_consistency()

        # Generate recommendations
        recommendations = self._generate_configuration_recommendations()

        report = {
            'timestamp': datetime.now().isoformat(),
            'configuration_sources': {
                'service_ports_yaml': bool(self.service_ports_config),
                'docker_compose_files': list(all_configs.get('docker_compose', {}).keys()),
                'service_configs': list(all_configs.get('service_configs', {}).keys()),
                'dockerfiles': list(all_configs.get('dockerfiles', {}).keys())
            },
            'port_standardization': {
                'total_services': len(standardized_ports),
                'standardized_ports': [
                    {
                        'service': name,
                        'internal_port': config.internal_port,
                        'external_port': config.external_port,
                        'description': config.description
                    }
                    for name, config in standardized_ports.items()
                ]
            },
            'service_discovery': discovery_validation,
            'deployment_consistency': consistency_analysis,
            'configuration_conflicts': [
                {
                    'service': conflict.service_name,
                    'type': conflict.conflict_type,
                    'description': conflict.description,
                    'severity': conflict.severity,
                    'suggestion': conflict.resolution_suggestion
                }
                for conflict in self.configuration_conflicts
            ],
            'recommendations': recommendations,
            'validation_summary': {
                'total_conflicts': len(self.configuration_conflicts),
                'critical_conflicts': len([c for c in self.configuration_conflicts if c.severity == 'critical']),
                'high_priority_conflicts': len([c for c in self.configuration_conflicts if c.severity == 'high']),
                'services_with_configs': len(all_configs.get('service_configs', {})),
                'services_with_ports': len(standardized_ports)
            }
        }

        return report

    def _analyze_deployment_consistency(self) -> Dict[str, Any]:
        """Analyze consistency between different deployment methods"""
        consistency = {
            'port_consistency': {},
            'environment_consistency': {},
            'dependency_consistency': {}
        }

        # Compare docker-compose vs service-ports.yaml ports
        for service_name, port_config in self.port_configurations.items():
            consistency['port_consistency'][service_name] = {
                'service_ports_config': {
                    'internal': port_config.internal_port,
                    'external': port_config.external_port
                },
                'docker_compose_config': None,
                'consistent': True
            }

            # Check docker-compose configuration
            if 'services' in self.docker_compose_config:
                service_config = self.docker_compose_config['services'].get(service_name, {})
                if 'ports' in service_config:
                    docker_ports = self._extract_ports_from_docker_compose(service_config['ports'])
                    if docker_ports:
                        consistency['port_consistency'][service_name]['docker_compose_config'] = docker_ports[0]

                        # Check consistency
                        docker_external = docker_ports[0]['external']
                        if docker_external != port_config.external_port:
                            consistency['port_consistency'][service_name]['consistent'] = False

        return consistency

    def _generate_configuration_recommendations(self) -> List[str]:
        """Generate configuration improvement recommendations"""
        recommendations = []

        # Port conflict recommendations
        if any(c.conflict_type == 'port_mapping_mismatch' for c in self.configuration_conflicts):
            recommendations.append("Synchronize port mappings between docker-compose.yml and service-ports.yaml")

        # Service discovery recommendations
        discovery_validation = self.validate_service_discovery()
        unregistered_services = [
            service for service, info in discovery_validation['service_registrations'].items()
            if not info['registered']
        ]

        if unregistered_services:
            recommendations.append(f"Register missing services in service-ports.yaml: {', '.join(unregistered_services)}")

        # Environment variable recommendations
        if not discovery_validation['environment_variables']:
            recommendations.append("Add service URL environment variables for inter-service communication")

        # General recommendations
        recommendations.extend([
            "Implement centralized configuration validation in CI/CD pipeline",
            "Document service discovery patterns and conventions",
            "Create configuration drift detection for production deployments",
            "Standardize health check endpoints across all services"
        ])

        return recommendations

    def generate_standardized_configs(self) -> Dict[str, Any]:
        """Generate standardized configuration files"""
        logger.info("Generating standardized configuration files...")

        standardized_configs = {}

        # Generate updated service-ports.yaml
        standardized_configs['service-ports.yaml'] = self._generate_service_ports_yaml()

        # Generate docker-compose service blocks
        standardized_configs['docker-compose-services'] = self._generate_docker_compose_services()

        # Generate environment variable templates
        standardized_configs['environment-template'] = self._generate_environment_template()

        # Generate service discovery configuration
        standardized_configs['service-discovery'] = self._generate_service_discovery_config()

        return standardized_configs

    def _generate_service_ports_yaml(self) -> Dict[str, Any]:
        """Generate standardized service-ports.yaml"""
        # Use existing config as base and ensure consistency
        config = self.service_ports_config.copy()

        # Ensure all required fields are present
        for category in ['core_services', 'ai_services', 'agent_services', 'analysis_services', 'utility_services', 'web_services']:
            if category not in config:
                config[category] = {}

            for service_name, service_config in config[category].items():
                if isinstance(service_config, dict):
                    # Ensure required fields
                    if 'internal_port' not in service_config:
                        service_config['internal_port'] = service_config.get('external_port', 5000)
                    if 'description' not in service_config:
                        service_config['description'] = f"{service_name.replace('-', ' ').title()} service"

        return config

    def _generate_docker_compose_services(self) -> Dict[str, Any]:
        """Generate standardized docker-compose service blocks"""
        services = {}

        for service_name, port_config in self.port_configurations.items():
            service_block = {
                'build': {
                    'context': '.',
                    'dockerfile': f'services/{service_name}/Dockerfile'
                },
                'environment': [
                    'PYTHONPATH=/app',
                    f'SERVICE_API_PORT={port_config.internal_port}',
                    'ENVIRONMENT=development'
                ],
                'ports': [
                    f'{port_config.external_port}:{port_config.internal_port}'
                ],
                'healthcheck': {
                    'test': [
                        'CMD', 'curl', '-f',
                        f'http://localhost:{port_config.internal_port}/health'
                    ],
                    'interval': '30s',
                    'timeout': '10s',
                    'retries': 3
                }
            }

            services[service_name] = service_block

        return services

    def _generate_environment_template(self) -> str:
        """Generate environment variable template"""
        template = "# Environment Variables Template\n"
        template += "# Generated from centralized service configuration\n\n"

        # Add service-specific variables
        for service_name, port_config in self.port_configurations.items():
            service_upper = service_name.upper().replace('-', '_')
            template += f"{service_upper}_API_PORT={port_config.external_port}\n"
            template += f"{service_upper}_INTERNAL_API_PORT={port_config.internal_port}\n"
            template += f"{service_upper}_URL=http://localhost:{port_config.external_port}\n\n"

        return template

    def _generate_service_discovery_config(self) -> Dict[str, Any]:
        """Generate service discovery configuration"""
        discovery_config = {
            'service_registry': {},
            'service_dependencies': {},
            'health_endpoints': {}
        }

        # Build service registry
        for service_name, port_config in self.port_configurations.items():
            discovery_config['service_registry'][service_name] = {
                'host': 'localhost',
                'port': port_config.external_port,
                'internal_port': port_config.internal_port,
                'protocol': port_config.protocol,
                'health_endpoint': '/health',
                'description': port_config.description
            }

            discovery_config['health_endpoints'][service_name] = f"http://localhost:{port_config.external_port}/health"

        # Add service dependencies from validation
        discovery_validation = self.validate_service_discovery()
        discovery_config['service_dependencies'] = discovery_validation.get('dependency_mappings', {})

        return discovery_config

    def apply_configuration_standardization(self) -> Dict[str, Any]:
        """Apply configuration standardization to the project"""
        logger.info("Applying configuration standardization...")

        results = {
            'files_updated': [],
            'files_created': [],
            'errors': []
        }

        try:
            # Generate standardized configs
            standardized_configs = self.generate_standardized_configs()

            # Update service-ports.yaml
            service_ports_path = self.config_dir / "service-ports.yaml"
            with open(service_ports_path, 'w') as f:
                yaml.dump(standardized_configs['service-ports.yaml'], f, default_flow_style=False, sort_keys=False)
            results['files_updated'].append(str(service_ports_path))

            # Create environment template
            env_template_path = self.config_dir / "service-ports.env.template"
            with open(env_template_path, 'w') as f:
                f.write(standardized_configs['environment-template'])
            results['files_created'].append(str(env_template_path))

            # Create service discovery config
            discovery_config_path = self.config_dir / "service-discovery.json"
            with open(discovery_config_path, 'w') as f:
                json.dump(standardized_configs['service-discovery'], f, indent=2)
            results['files_created'].append(str(discovery_config_path))

            # Generate validation script
            validation_script_path = self.scripts_dir / "hardening" / "validate_service_configs.py"
            validation_script = self._generate_validation_script()
            with open(validation_script_path, 'w') as f:
                f.write(validation_script)
            results['files_created'].append(str(validation_script_path))

            # Make validation script executable
            os.chmod(validation_script_path, 0o755)

        except Exception as e:
            results['errors'].append(f"Configuration standardization failed: {e}")

        return results

    def _generate_validation_script(self) -> str:
        """Generate configuration validation script"""
        script = '''#!/usr/bin/env python3
"""
Service Configuration Validation Script
Generated by Unified Configuration Management System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.hardening.configuration_management_system import UnifiedConfigurationManager

def main():
    """Run configuration validation"""
    manager = UnifiedConfigurationManager()

    print("🔍 Validating Service Configurations...")
    print("=" * 50)

    # Generate report
    report = manager.generate_configuration_report()

    # Print summary
    summary = report['validation_summary']
    print(f"Services with configs: {summary['services_with_configs']}")
    print(f"Services with ports: {summary['services_with_ports']}")
    print(f"Configuration conflicts: {summary['total_conflicts']}")
    print(f"Critical conflicts: {summary['critical_conflicts']}")
    print(f"High priority conflicts: {summary['high_priority_conflicts']}")

    # Print conflicts
    if report['configuration_conflicts']:
        print("\\n🚨 Configuration Conflicts:")
        for conflict in report['configuration_conflicts']:
            severity_icon = "🔴" if conflict['severity'] == "critical" else "🟠" if conflict['severity'] == "high" else "🟡"
            print(f"  {severity_icon} {conflict['service']}: {conflict['description']}")
            if conflict['suggestion']:
                print(f"    💡 {conflict['suggestion']}")

    # Print recommendations
    if report['recommendations']:
        print("\\n💡 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")

    # Exit with error code if critical conflicts
    if summary['critical_conflicts'] > 0:
        print("\\n❌ Critical configuration issues found!")
        return 1

    print("\\n✅ Configuration validation complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        return script

    def print_comprehensive_report(self, report: Dict[str, Any]):
        """Print comprehensive configuration report"""
        print("\\n" + "="*80)
        print("🔧 UNIFIED CONFIGURATION MANAGEMENT SYSTEM REAPI_PORT")
        print("="*80)

        summary = report['validation_summary']
        print(f"\\n📊 SUMMARY")
        print(f"  Services with Configurations: {summary['services_with_configs']}")
        print(f"  Services with Port Assignments: {summary['services_with_ports']}")
        print(f"  Configuration Conflicts: {summary['total_conflicts']}")
        print(f"  Critical Issues: {summary['critical_conflicts']}")
        print(f"  High Priority Issues: {summary['high_priority_conflicts']}")

        # Configuration Sources
        sources = report['configuration_sources']
        print(f"\\n📁 CONFIGURATION SOURCES")
        print(f"  Service Ports YAML: {'✅' if sources['service_ports_yaml'] else '❌'}")
        print(f"  Docker Compose Files: {len(sources['docker_compose_files'])}")
        print(f"  Service Configs: {len(sources['service_configs'])}")
        print(f"  Dockerfiles: {len(sources['dockerfiles'])}")

        # Port Standardization
        ports = report['port_standardization']
        print(f"\\n🔌 API_PORT STANDARDIZATION")
        print(f"  Total Services: {ports['total_services']}")

        # Service Discovery
        discovery = report['service_discovery']
        print(f"\\n🔍 SERVICE DISCOVERY")
        registered = sum(1 for s in discovery['service_registrations'].values() if s['registered'])
        total_services = len(discovery['service_registrations'])
        print(f"  Registered Services: {registered}/{total_services}")

        # Configuration Conflicts
        if report['configuration_conflicts']:
            print(f"\\n🚨 CONFIGURATION CONFLICTS")
            for conflict in report['configuration_conflicts'][:5]:  # Show first 5
                severity_icon = "🔴" if conflict['severity'] == "critical" else "🟠" if conflict['severity'] == "high" else "🟡"
                print(f"  {severity_icon} {conflict['service']}: {conflict['description']}")

            if len(report['configuration_conflicts']) > 5:
                print(f"  ... and {len(report['configuration_conflicts']) - 5} more conflicts")

        # Recommendations
        if report['recommendations']:
            print(f"\\n💡 RECOMMENDATIONS")
            for i, rec in enumerate(report['recommendations'][:5], 1):  # Show first 5
                print(f"  {i}. {rec}")

        print("\\n" + "="*80)


def main():
    """Main entry point"""
    manager = UnifiedConfigurationManager()

    # Generate comprehensive report
    report = manager.generate_configuration_report()
    manager.print_comprehensive_report(report)

    # Save detailed report
    report_path = Path("configuration_management_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\\n💾 Detailed report saved to: {report_path}")

    # Offer to apply standardization
    print("\\n🔧 Apply Configuration Standardization?")
    print("This will update configuration files to ensure consistency.")
    response = input("Continue? (y/N): ").strip().lower()

    if response == 'y':
        results = manager.apply_configuration_standardization()

        print("\\n📝 Configuration Standardization Results:")
        if results['files_updated']:
            print("Updated files:")
            for file in results['files_updated']:
                print(f"  • {file}")

        if results['files_created']:
            print("Created files:")
            for file in results['files_created']:
                print(f"  • {file}")

        if results['errors']:
            print("Errors:")
            for error in results['errors']:
                print(f"  ❌ {error}")

        print("\\n✅ Configuration standardization complete!")
    else:
        print("\\nℹ️  Configuration standardization skipped.")


if __name__ == "__main__":
    main()
