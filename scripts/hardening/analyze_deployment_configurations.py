#!/usr/bin/env python3
"""
Deployment Configuration Analysis Script
Analyzes and compares configurations across different deployment methods:
- Local development
- Docker Compose
- Docker standalone containers
- Production deployments
"""

import json
import yaml
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DeploymentConfiguration:
    """Configuration for a specific deployment method"""
    name: str
    service_configs: Dict[str, Any]
    environment_variables: Dict[str, str]
    port_mappings: Dict[str, Dict[str, int]]
    health_checks: Dict[str, str]
    dependencies: Dict[str, List[str]]

@dataclass
class ConfigurationDifference:
    """Represents a difference between deployment configurations"""
    service_name: str
    config_type: str  # 'ports', 'environment', 'health', 'dependencies'
    deployment_a: str
    deployment_b: str
    difference: str
    severity: str = 'medium'

class DeploymentConfigurationAnalyzer:
    """
    Analyzes configuration consistency across different deployment methods
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.services_dir = self.project_root / "services"
        self.config_dir = self.project_root / "config"
        self.scripts_dir = self.project_root / "scripts"

        # Load standardized configurations
        self.service_ports_config = self._load_service_ports_config()
        self.docker_compose_config = self._load_docker_compose_config()
        self.service_discovery_config = self._load_service_discovery_config()

    def _load_service_ports_config(self) -> Dict[str, Any]:
        """Load standardized service ports configuration"""
        config_path = self.config_dir / "service-ports.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def _load_docker_compose_config(self) -> Dict[str, Any]:
        """Load docker-compose.dev.yml configuration"""
        compose_path = self.project_root / "docker-compose.dev.yml"
        if compose_path.exists():
            with open(compose_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def _load_service_discovery_config(self) -> Dict[str, Any]:
        """Load service discovery configuration"""
        discovery_path = self.config_dir / "service-discovery.json"
        if discovery_path.exists():
            with open(discovery_path, 'r') as f:
                return json.load(f)
        return {}

    def analyze_deployment_methods(self) -> Dict[str, Any]:
        """Analyze configurations across different deployment methods"""
        logger.info("Analyzing deployment configuration methods...")

        # Extract configurations for each deployment method
        deployments = {
            'docker_compose': self._extract_docker_compose_deployment(),
            'docker_standalone': self._extract_docker_standalone_deployment(),
            'local_development': self._extract_local_development_deployment(),
            'standardized_config': self._extract_standardized_deployment()
        }

        # Compare configurations
        differences = self._compare_deployment_configurations(deployments)

        # Generate recommendations
        recommendations = self._generate_deployment_recommendations(differences, deployments)

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'deployment_methods_analyzed': list(deployments.keys()),
            'configuration_differences': [
                {
                    'service': diff.service_name,
                    'type': diff.config_type,
                    'deployments': f"{diff.deployment_a} vs {diff.deployment_b}",
                    'difference': diff.difference,
                    'severity': diff.severity
                }
                for diff in differences
            ],
            'recommendations': recommendations,
            'deployment_summaries': {
                name: self._summarize_deployment_config(deployment)
                for name, deployment in deployments.items()
            },
            'consistency_score': self._calculate_consistency_score(differences, deployments)
        }

        return analysis

    def _extract_docker_compose_deployment(self) -> DeploymentConfiguration:
        """Extract configuration from docker-compose setup"""
        services = {}
        ports = {}
        health_checks = {}
        dependencies = {}

        if 'services' in self.docker_compose_config:
            for service_name, service_config in self.docker_compose_config['services'].items():
                services[service_name] = service_config

                # Extract port mappings
                if 'ports' in service_config:
                    port_info = self._parse_docker_ports(service_config['ports'])
                    if port_info:
                        ports[service_name] = port_info

                # Extract health checks
                if 'healthcheck' in service_config:
                    health_checks[service_name] = service_config['healthcheck']

                # Extract dependencies
                if 'depends_on' in service_config:
                    deps = service_config['depends_on']
                    if isinstance(deps, list):
                        dependencies[service_name] = deps
                    elif isinstance(deps, dict):
                        dependencies[service_name] = list(deps.keys())

        # Extract environment variables
        env_vars = {}
        for service_name, service_config in services.items():
            if 'environment' in service_config:
                env = service_config['environment']
                if isinstance(env, list):
                    for env_var in env:
                        if isinstance(env_var, str) and '=' in env_var:
                            key, value = env_var.split('=', 1)
                            env_vars[f"{service_name}.{key}"] = value
                elif isinstance(env, dict):
                    for key, value in env.items():
                        env_vars[f"{service_name}.{key}"] = str(value)

        return DeploymentConfiguration(
            name='docker_compose',
            service_configs=services,
            environment_variables=env_vars,
            port_mappings=ports,
            health_checks=health_checks,
            dependencies=dependencies
        )

    def _extract_docker_standalone_deployment(self) -> DeploymentConfiguration:
        """Extract configuration for standalone Docker containers"""
        # This would analyze individual docker run commands or container configurations
        # For now, simulate based on Dockerfiles and standardized config

        ports = {}
        env_vars = {}
        health_checks = {}

        # Extract from Dockerfiles and service discovery
        for service_name, service_info in self.service_discovery_config.get('service_registry', {}).items():
            ports[service_name] = {
                'external': service_info['port'],
                'internal': service_info['internal_port']
            }

            # Simulate environment variables for standalone containers
            env_vars[f"{service_name}.SERVICE_API_PORT"] = str(service_info['internal_port'])
            env_vars[f"{service_name}.ENVIRONMENT"] = "standalone"

        return DeploymentConfiguration(
            name='docker_standalone',
            service_configs={},  # Would be populated from docker run commands
            environment_variables=env_vars,
            port_mappings=ports,
            health_checks=health_checks,
            dependencies={}
        )

    def _extract_local_development_deployment(self) -> DeploymentConfiguration:
        """Extract configuration for local development"""
        ports = {}
        env_vars = {}
        health_checks = {}

        # Extract from service discovery (local development uses host ports)
        for service_name, service_info in self.service_discovery_config.get('service_registry', {}).items():
            ports[service_name] = {
                'external': service_info['port'],  # Local uses external port directly
                'internal': service_info['port']
            }

            # Local development environment variables
            env_vars[f"{service_name}.SERVICE_API_PORT"] = str(service_info['port'])
            env_vars[f"{service_name}.ENVIRONMENT"] = "development"
            env_vars[f"{service_name}.LOG_COLLECTOR_ENABLED"] = "true"

        return DeploymentConfiguration(
            name='local_development',
            service_configs={},
            environment_variables=env_vars,
            port_mappings=ports,
            health_checks=health_checks,
            dependencies={}
        )

    def _extract_standardized_deployment(self) -> DeploymentConfiguration:
        """Extract the standardized configuration as baseline"""
        ports = {}
        env_vars = {}
        health_checks = {}

        # Use service discovery as the standard
        for service_name, service_info in self.service_discovery_config.get('service_registry', {}).items():
            ports[service_name] = {
                'external': service_info['port'],
                'internal': service_info['internal_port']
            }

            # Standardized environment variables
            env_vars[f"{service_name}.SERVICE_API_PORT"] = str(service_info['internal_port'])
            env_vars[f"{service_name}.ENVIRONMENT"] = "standardized"

            # Add health endpoint
            health_checks[service_name] = service_info['health_endpoint']

        return DeploymentConfiguration(
            name='standardized_config',
            service_configs={},
            environment_variables=env_vars,
            port_mappings=ports,
            health_checks=health_checks,
            dependencies=self.service_discovery_config.get('service_dependencies', {})
        )

    def _parse_docker_ports(self, ports_config: List[str]) -> Optional[Dict[str, int]]:
        """Parse Docker port mapping configuration"""
        if not ports_config or not isinstance(ports_config, list):
            return None

        # Take the first port mapping
        port_mapping = ports_config[0]
        if ':' in port_mapping:
            parts = port_mapping.split(':')
            if len(parts) >= 2:
                try:
                    external = int(parts[-2])
                    internal = int(parts[-1])
                    return {'external': external, 'internal': internal}
                except ValueError:
                    pass
        return None

    def _compare_deployment_configurations(self, deployments: Dict[str, DeploymentConfiguration]) -> List[ConfigurationDifference]:
        """Compare configurations between deployment methods"""
        differences = []

        # Compare ports between deployments
        port_differences = self._compare_port_configurations(deployments)
        differences.extend(port_differences)

        # Compare environment variables
        env_differences = self._compare_environment_configurations(deployments)
        differences.extend(env_differences)

        # Compare health checks
        health_differences = self._compare_health_configurations(deployments)
        differences.extend(health_differences)

        return differences

    def _compare_port_configurations(self, deployments: Dict[str, DeploymentConfiguration]) -> List[ConfigurationDifference]:
        """Compare port configurations between deployments"""
        differences = []

        # Get all service names across deployments
        all_services = set()
        for deployment in deployments.values():
            all_services.update(deployment.port_mappings.keys())

        # Compare each service's port configuration
        for service_name in all_services:
            port_configs = {}
            for deployment_name, deployment in deployments.items():
                if service_name in deployment.port_mappings:
                    port_configs[deployment_name] = deployment.port_mappings[service_name]

            # Compare against standardized config
            if 'standardized_config' in port_configs:
                standard_ports = port_configs['standardized_config']

                for deployment_name, ports in port_configs.items():
                    if deployment_name != 'standardized_config':
                        if ports != standard_ports:
                            diff_desc = f"Port mismatch: {deployment_name} {ports} vs standard {standard_ports}"
                            differences.append(ConfigurationDifference(
                                service_name=service_name,
                                config_type='ports',
                                deployment_a=deployment_name,
                                deployment_b='standardized_config',
                                difference=diff_desc,
                                severity='high' if ports['external'] != standard_ports['external'] else 'medium'
                            ))

        return differences

    def _compare_environment_configurations(self, deployments: Dict[str, DeploymentConfiguration]) -> List[ConfigurationDifference]:
        """Compare environment variable configurations"""
        differences = []

        # Compare environment variables that should be consistent
        critical_env_vars = ['SERVICE_API_PORT', 'ENVIRONMENT', 'LOG_COLLECTOR_ENABLED']

        for service_name in deployments['standardized_config'].environment_variables.keys():
            if '.' in service_name:
                service, var_name = service_name.split('.', 1)
                if var_name in critical_env_vars:
                    std_value = deployments['standardized_config'].environment_variables[service_name]

                    for deployment_name, deployment in deployments.items():
                        if deployment_name != 'standardized_config':
                            dep_key = f"{service}.{var_name}"
                            if dep_key in deployment.environment_variables:
                                dep_value = deployment.environment_variables[dep_key]
                                if dep_value != std_value:
                                    differences.append(ConfigurationDifference(
                                        service_name=service,
                                        config_type='environment',
                                        deployment_a=deployment_name,
                                        deployment_b='standardized_config',
                                        difference=f"{var_name}: '{dep_value}' vs '{std_value}'",
                                        severity='high' if var_name == 'SERVICE_API_PORT' else 'medium'
                                    ))

        return differences

    def _compare_health_configurations(self, deployments: Dict[str, DeploymentConfiguration]) -> List[ConfigurationDifference]:
        """Compare health check configurations"""
        differences = []

        # Compare health endpoints
        for service_name in deployments['standardized_config'].health_checks.keys():
            std_health = deployments['standardized_config'].health_checks[service_name]

            for deployment_name, deployment in deployments.items():
                if deployment_name != 'standardized_config' and service_name in deployment.health_checks:
                    dep_health = deployment.health_checks[service_name]
                    if dep_health != std_health:
                        differences.append(ConfigurationDifference(
                            service_name=service_name,
                            config_type='health',
                            deployment_a=deployment_name,
                            deployment_b='standardized_config',
                            difference=f"Health endpoint: '{dep_health}' vs '{std_health}'",
                            severity='medium'
                        ))

        return differences

    def _generate_deployment_recommendations(self, differences: List[ConfigurationDifference],
                                           deployments: Dict[str, DeploymentConfiguration]) -> List[str]:
        """Generate recommendations for deployment configuration improvements"""
        recommendations = []

        # Count differences by type and severity
        diff_counts = {
            'ports': {'high': 0, 'medium': 0, 'low': 0},
            'environment': {'high': 0, 'medium': 0, 'low': 0},
            'health': {'high': 0, 'medium': 0, 'low': 0}
        }

        for diff in differences:
            diff_counts[diff.config_type][diff.severity] += 1

        # Generate recommendations based on difference patterns
        if diff_counts['ports']['high'] > 0:
            recommendations.append("Critical: Synchronize port configurations across all deployment methods")

        if diff_counts['environment']['high'] > 0:
            recommendations.append("Critical: Standardize SERVICE_API_PORT environment variables")

        if diff_counts['health']['medium'] > 0:
            recommendations.append("Standardize health check endpoints across deployments")

        # General recommendations
        recommendations.extend([
            "Implement automated configuration validation in CI/CD pipeline",
            "Create deployment-specific configuration templates",
            "Document deployment method differences and use cases",
            "Establish configuration drift detection for production"
        ])

        return recommendations

    def _summarize_deployment_config(self, deployment: DeploymentConfiguration) -> Dict[str, Any]:
        """Create summary of deployment configuration"""
        return {
            'services_configured': len(deployment.service_configs),
            'ports_mapped': len(deployment.port_mappings),
            'environment_variables': len(deployment.environment_variables),
            'health_checks': len(deployment.health_checks),
            'dependencies_defined': len(deployment.dependencies)
        }

    def _calculate_consistency_score(self, differences: List[ConfigurationDifference],
                                   deployments: Dict[str, DeploymentConfiguration]) -> float:
        """Calculate overall configuration consistency score"""
        if not differences:
            return 100.0

        # Weight differences by severity
        severity_weights = {'high': 3, 'medium': 2, 'low': 1}
        total_weighted_differences = sum(severity_weights[diff.severity] for diff in differences)

        # Calculate score based on total possible configurations
        total_services = len(deployments['standardized_config'].port_mappings)
        total_configs = total_services * len(deployments) * 3  # ports, env, health per service per deployment

        # Score = 100 - (weighted_differences / total_configs * 100)
        score = max(0, 100 - (total_weighted_differences / total_configs * 100))
        return round(score, 1)

    def print_deployment_analysis_report(self, analysis: Dict[str, Any]):
        """Print comprehensive deployment analysis report"""
        print("\\n" + "="*80)
        print("🚀 DEPLOYMENT CONFIGURATION ANALYSIS REAPI_PORT")
        print("="*80)

        print(f"\\n📊 OVERALL CONSISTENCY SCORE: {analysis['consistency_score']}/100")

        # Deployment summaries
        print(f"\\n🏗️  DEPLOYMENT METHOD SUMMARIES")
        for name, summary in analysis['deployment_summaries'].items():
            print(f"  {name}:")
            print(f"    Services: {summary['services_configured']}")
            print(f"    Port Mappings: {summary['ports_mapped']}")
            print(f"    Environment Vars: {summary['environment_variables']}")
            print(f"    Health Checks: {summary['health_checks']}")

        # Configuration differences
        differences = analysis['configuration_differences']
        if differences:
            print(f"\\n⚠️  CONFIGURATION DIFFERENCES ({len(differences)} total)")

            # Group by severity
            high_diffs = [d for d in differences if d['severity'] == 'high']
            medium_diffs = [d for d in differences if d['severity'] == 'medium']

            if high_diffs:
                print("  🔴 HIGH PRIORITY:")
                for diff in high_diffs[:3]:  # Show first 3
                    print(f"    {diff['service']} ({diff['type']}): {diff['difference']}")

            if medium_diffs:
                print("  🟠 MEDIUM PRIORITY:")
                for diff in medium_diffs[:3]:  # Show first 3
                    print(f"    {diff['service']} ({diff['type']}): {diff['difference']}")

        # Recommendations
        recommendations = analysis['recommendations']
        if recommendations:
            print(f"\\n💡 RECOMMENDATIONS")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")

        print("\\n" + "="*80)


def main():
    """Main entry point"""
    analyzer = DeploymentConfigurationAnalyzer()

    # Analyze deployment methods
    analysis = analyzer.analyze_deployment_methods()
    analyzer.print_deployment_analysis_report(analysis)

    # Save detailed analysis
    analysis_path = Path("deployment_configuration_analysis.json")
    with open(analysis_path, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)

    print(f"\\n💾 Detailed analysis saved to: {analysis_path}")

    # Exit with error code if consistency score is low
    if analysis['consistency_score'] < 70:
        print("\\n❌ Low configuration consistency detected!")
        return 1

    print("\\n✅ Deployment configuration analysis complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
