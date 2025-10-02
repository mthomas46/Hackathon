#!/usr/bin/env python3
"""
Configuration Audit Script for LLM Documentation Ecosystem

This script audits all services in the ecosystem to understand their configuration management patterns,
identify inconsistencies, and prepare for centralized configuration management.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ServiceConfig:
    """Represents a service's configuration structure."""
    service_name: str
    config_file: Path
    config_data: Dict[str, Any] = field(default_factory=dict)
    env_vars: Set[str] = field(default_factory=set)
    docker_config: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)


@dataclass
class ConfigAudit:
    """Complete configuration audit results."""
    services: Dict[str, ServiceConfig] = field(default_factory=dict)
    common_patterns: Dict[str, List[str]] = field(default_factory=dict)
    inconsistencies: List[str] = field(default_factory=list)
    env_var_usage: Dict[str, List[str]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class ConfigurationAuditor:
    """Audits configuration management across all services."""

    def __init__(self, services_dir: Path):
        self.services_dir = services_dir
        self.audit = ConfigAudit()

    def audit_all_services(self) -> ConfigAudit:
        """Perform complete audit of all services."""
        print("🔍 Starting configuration audit of all services...")

        # Find all services
        service_dirs = [d for d in self.services_dir.iterdir()
                       if d.is_dir() and not d.name.startswith('.') and d.name != 'shared']

        for service_dir in service_dirs:
            self.audit_service(service_dir)

        # Analyze patterns and inconsistencies
        self.analyze_patterns()
        self.identify_inconsistencies()

        print(f"✅ Audit complete. Analyzed {len(self.audit.services)} services.")
        return self.audit

    def audit_service(self, service_dir: Path):
        """Audit a single service."""
        service_name = service_dir.name

        print(f"  Auditing {service_name}...")

        config = ServiceConfig(service_name=service_name, config_file=service_dir)

        # Check for config files
        config_files = [
            service_dir / 'config.yaml',
            service_dir / 'config.yml',
            service_dir / 'Config.yaml',
            service_dir / 'Config.yml'
        ]

        config_file = None
        for cf in config_files:
            if cf.exists():
                config_file = cf
                break

        if config_file:
            config.config_file = config_file
            config.config_data = self.parse_config_file(config_file)

            # Extract environment variables from config
            config.env_vars = self.extract_env_vars(config.config_data)

        # Check for docker-compose files
        docker_compose_files = [
            service_dir / 'docker-compose.yml',
            service_dir / 'docker-compose.yaml',
            self.services_dir.parent / f'docker-compose.{service_name}.yml'
        ]

        docker_config = {}
        for dcf in docker_compose_files:
            if dcf.exists():
                docker_config = self.parse_docker_config(dcf)
                break

        config.docker_config = docker_config

        # Check for main.py to analyze environment variable usage
        main_py = service_dir / 'main.py'
        if main_py.exists():
            env_vars_from_code = self.extract_env_vars_from_code(main_py)
            config.env_vars.update(env_vars_from_code)

        # Validate configuration
        self.validate_service_config(config)

        self.audit.services[service_name] = config

    def parse_config_file(self, config_file: Path) -> Dict[str, Any]:
        """Parse a YAML configuration file."""
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"    ⚠️  Error parsing {config_file}: {e}")
            return {}

    def parse_docker_config(self, docker_file: Path) -> Dict[str, Any]:
        """Parse docker-compose configuration."""
        try:
            with open(docker_file, 'r') as f:
                config = yaml.safe_load(f) or {}
                services = config.get('services', {})

                # Try different service name variations
                service_name = docker_file.parent.name
                service_name_hyphen = service_name.replace('_', '-')
                service_name_underscore = service_name.replace('-', '_')

                # Try exact match first, then variations
                service_config = (services.get(service_name) or
                                services.get(service_name_hyphen) or
                                services.get(service_name_underscore))

                return service_config or {}
        except Exception as e:
            print(f"    ⚠️  Error parsing {docker_file}: {e}")
            return {}

    def extract_env_vars(self, config_data: Dict[str, Any]) -> Set[str]:
        """Extract environment variable references from config data."""
        env_vars = set()

        def _extract_env_vars(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and value.startswith('${') and ':-' in value:
                        # Extract env var name from ${VAR_NAME:-default}
                        env_var = value.split('${')[1].split(':-')[0]
                        env_vars.add(env_var)
                    else:
                        _extract_env_vars(value)
            elif isinstance(obj, list):
                for item in obj:
                    _extract_env_vars(item)

        _extract_env_vars(config_data)
        return env_vars

    def extract_env_vars_from_code(self, main_py: Path) -> Set[str]:
        """Extract environment variable usage from Python code."""
        env_vars = set()
        try:
            with open(main_py, 'r') as f:
                content = f.read()

            # Look for os.environ.get patterns
            import re
            env_patterns = [
                r'os\.environ\.get\(["\']([^"\']+)["\']',
                r'os\.environ\[["\']([^"\']+)["\']',
                r'getenv\(["\']([^"\']+)["\']'
            ]

            for pattern in env_patterns:
                matches = re.findall(pattern, content)
                env_vars.update(matches)

        except Exception as e:
            print(f"    ⚠️  Error analyzing {main_py}: {e}")

        return env_vars

    def validate_service_config(self, config: ServiceConfig):
        """Validate a service's configuration for common issues."""
        issues = []
        service_name = config.service_name

        # Check if config file exists
        if not config.config_file.exists():
            issues.append("No config.yaml file found")
        else:
            # Check if this is a CLI service (doesn't need server section)
            is_cli_service = False
            if config.config_data:
                # Check for CLI indicators in config
                cli_indicators = [
                    "CLI doesn't expose a port" in str(config.config_data),
                    service_name == 'cli',
                    'cli' in str(config.config_data).lower() and 'server' not in config.config_data
                ]
                is_cli_service = any(cli_indicators)

            if not is_cli_service:
                # Check for required sections (only for web services)
                if 'server' not in config.config_data:
                    issues.append("Missing 'server' configuration section")
                elif 'port' not in config.config_data.get('server', {}):
                    issues.append("Missing 'server.port' configuration")

            # Check for hardcoded values that should be environment variables
            if self.has_hardcoded_values(config.config_data):
                issues.append("Contains hardcoded values that should use environment variables")

        # Check docker configuration
        if not config.docker_config:
            issues.append("No docker-compose configuration found")
        else:
            # Check for proper environment variable usage in docker
            env_section = config.docker_config.get('environment', [])
            if not env_section:
                issues.append("Docker service missing environment configuration")

        config.issues = issues

    def has_hardcoded_values(self, config_data: Dict[str, Any]) -> bool:
        """Check if config contains hardcoded values that should be environment variables."""
        hardcoded_indicators = [
            'localhost', '127.0.0.1', 'changeme', 'your-secret-key',
            'http://', 'https://'  # URLs that might be hardcoded
        ]

        def _check_hardcoded(obj) -> bool:
            if isinstance(obj, dict):
                for value in obj.values():
                    if isinstance(value, str):
                        for indicator in hardcoded_indicators:
                            if indicator in value.lower() and not value.startswith('${'):
                                return True
                    elif isinstance(value, (dict, list)):
                        if _check_hardcoded(value):
                            return True
            elif isinstance(obj, list):
                for item in obj:
                    if _check_hardcoded(item):
                        return True
            return False

        return _check_hardcoded(config_data)

    def analyze_patterns(self):
        """Analyze common patterns across services."""
        patterns = defaultdict(list)

        # Group services by configuration patterns
        for service_name, config in self.audit.services.items():
            # Config file patterns
            if config.config_file.exists():
                config_type = 'yaml_config'
            else:
                config_type = 'no_config'
            patterns[config_type].append(service_name)

            # Environment variable patterns
            if config.env_vars:
                patterns['uses_env_vars'].append(service_name)
            else:
                patterns['no_env_vars'].append(service_name)

            # Docker patterns
            if config.docker_config:
                patterns['has_docker_compose'].append(service_name)
            else:
                patterns['no_docker_compose'].append(service_name)

        self.audit.common_patterns = dict(patterns)

    def identify_inconsistencies(self):
        """Identify configuration inconsistencies across services."""
        inconsistencies = []

        # Check for services without config files
        no_config_services = self.audit.common_patterns.get('no_config', [])
        if no_config_services:
            inconsistencies.append(f"Services without config.yaml files: {', '.join(no_config_services)}")

        # Check for inconsistent port configurations
        ports = {}
        for service_name, config in self.audit.services.items():
            port = config.config_data.get('server', {}).get('port')
            if port:
                if port in ports:
                    inconsistencies.append(f"Port {port} used by multiple services: {ports[port]}, {service_name}")
                else:
                    ports[port] = service_name

        # Check for environment variable naming inconsistencies
        all_env_vars = set()
        for config in self.audit.services.values():
            all_env_vars.update(config.env_vars)

        # Group by prefix
        env_prefixes = defaultdict(list)
        for env_var in all_env_vars:
            prefix = env_var.split('_')[0] if '_' in env_var else 'MISC'
            env_prefixes[prefix].append(env_var)

        # Check for inconsistent naming
        if len(env_prefixes) > 1:
            inconsistencies.append(f"Multiple environment variable prefixes found: {list(env_prefixes.keys())}")

        self.audit.inconsistencies = inconsistencies

        # Track environment variable usage
        env_usage = defaultdict(list)
        for service_name, config in self.audit.services.items():
            for env_var in config.env_vars:
                env_usage[env_var].append(service_name)
        self.audit.env_var_usage = dict(env_usage)

    def generate_recommendations(self):
        """Generate recommendations for configuration management improvements."""
        recommendations = []

        # Recommend centralized configuration management
        recommendations.append("Implement centralized configuration management library")
        recommendations.append("Standardize environment variable naming conventions")
        recommendations.append("Move hardcoded values to environment variables")
        recommendations.append("Create shared configuration validation")
        recommendations.append("Implement configuration hot-reloading")
        recommendations.append("Add configuration migration scripts")

        self.audit.recommendations = recommendations


def main():
    """Main audit function."""
    services_dir = Path('services')

    if not services_dir.exists():
        print("❌ Services directory not found!")
        return

    auditor = ConfigurationAuditor(services_dir)
    audit = auditor.audit_all_services()
    auditor.generate_recommendations()

    # Print audit summary
    print("\n" + "="*80)
    print("📊 CONFIGURATION AUDIT SUMMARY")
    print("="*80)

    print(f"\n🔢 Total services analyzed: {len(audit.services)}")

    print(f"\n📁 Configuration file patterns:")
    for pattern, services in audit.common_patterns.items():
        print(f"  {pattern}: {len(services)} services")

    print(f"\n⚠️  Configuration issues found:")
    total_issues = 0
    for service_name, config in audit.services.items():
        if config.issues:
            print(f"  {service_name}: {len(config.issues)} issues")
            total_issues += len(config.issues)
    print(f"  Total issues: {total_issues}")

    if audit.inconsistencies:
        print(f"\n🔄 Configuration inconsistencies:")
        for inconsistency in audit.inconsistencies:
            print(f"  • {inconsistency}")

    print(f"\n💡 Recommendations:")
    for recommendation in audit.recommendations:
        print(f"  • {recommendation}")

    # Save detailed audit results
    audit_file = Path('configuration_audit_results.json')
    audit_data = {
        'services': {
            name: {
                'config_file': str(config.config_file),
                'env_vars': list(config.env_vars),
                'issues': config.issues,
                'has_docker_config': bool(config.docker_config)
            }
            for name, config in audit.services.items()
        },
        'patterns': audit.common_patterns,
        'inconsistencies': audit.inconsistencies,
        'env_var_usage': audit.env_var_usage,
        'recommendations': audit.recommendations
    }

    with open(audit_file, 'w') as f:
        json.dump(audit_data, f, indent=2)

    print(f"\n💾 Detailed results saved to {audit_file}")


if __name__ == '__main__':
    main()
