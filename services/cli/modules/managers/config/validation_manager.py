"""Configuration Validation Manager for CLI operations."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import yaml
import re

from ...base.base_manager import BaseManager
from ...formatters.display_utils import DisplayManager


class ValidationManager(BaseManager):
    """Manager for configuration validation operations."""

    async def validate_yaml_syntax(self):
        """Validate YAML syntax in configuration files."""
        try:
            config_files = await self._find_all_config_files()
            validation_results = []

            with self.display.show_progress("Validating YAML syntax") as progress:
                for config_file in config_files:
                    result = await self._validate_yaml_file(config_file)
                    validation_results.append(result)

            # Display results
            valid_count = sum(1 for r in validation_results if r['valid'])
            total_count = len(validation_results)

            table_data = []
            for result in validation_results:
                status = "✅ Valid" if result['valid'] else "❌ Invalid"
                message = "OK" if result['valid'] else result.get('error', 'Unknown error')
                table_data.append([result['file'], status, message])

            self.display.show_table(
                f"YAML Syntax Validation ({valid_count}/{total_count} valid)",
                ["File", "Status", "Message"],
                table_data
            )

            if valid_count == total_count:
                self.display.show_success("All YAML files are syntactically valid!")
            else:
                self.display.show_error(f"{total_count - valid_count} YAML files have syntax errors")

        except Exception as e:
            self.display.show_error(f"Error validating YAML syntax: {e}")

    async def validate_configuration_schema(self):
        """Validate configuration against schemas."""
        try:
            self.display.show_info("Schema validation feature coming soon!")
            self.display.show_info("This will validate configurations against JSON schemas")

        except Exception as e:
            self.display.show_error(f"Error validating configuration schema: {e}")

    async def check_configuration_consistency(self):
        """Check configuration consistency across services."""
        try:
            consistency_issues = await self._perform_configuration_consistency_check()

            if not consistency_issues:
                self.display.show_success("No configuration consistency issues found!")
                return

            # Display issues
            table_data = []
            for issue in consistency_issues:
                severity = "🔴 Critical" if issue['severity'] == 'critical' else "🟡 Warning" if issue['severity'] == 'warning' else "ℹ️ Info"
                table_data.append([issue['service'], severity, issue['issue'], issue.get('suggestion', '')])

            self.display.show_table(
                "Configuration Consistency Issues",
                ["Service", "Severity", "Issue", "Suggestion"],
                table_data
            )

        except Exception as e:
            self.display.show_error(f"Error checking configuration consistency: {e}")

    async def validate_environment_references(self):
        """Validate environment variable references in configurations."""
        try:
            self.display.show_info("Environment reference validation feature coming soon!")
            self.display.show_info("This will check that all ${VAR} references are defined")

        except Exception as e:
            self.display.show_error(f"Error validating environment references: {e}")

    async def configuration_health_check(self):
        """Perform comprehensive configuration health check."""
        try:
            health_results = await self._perform_configuration_health_check()

            # Overall health score
            healthy_items = sum(1 for result in health_results.values() if result[0] == 'healthy')
            total_items = len(health_results)

            health_score = (healthy_items / total_items * 100) if total_items > 0 else 0

            self.display.show_info(f"Configuration Health Score: {health_score:.1f}% ({healthy_items}/{total_items} healthy)")

            # Display detailed results
            table_data = []
            for check_name, (status, message) in health_results.items():
                status_icon = "✅" if status == 'healthy' else "❌" if status == 'unhealthy' else "⚠️"
                table_data.append([check_name, f"{status_icon} {status}", message])

            self.display.show_table(
                "Configuration Health Check Results",
                ["Check", "Status", "Details"],
                table_data
            )

            if health_score >= 90:
                self.display.show_success("Configuration health is excellent!")
            elif health_score >= 70:
                self.display.show_warning("Configuration health is good but could be improved")
            else:
                self.display.show_error("Configuration health needs attention")

        except Exception as e:
            self.display.show_error(f"Error performing configuration health check: {e}")

    async def _find_all_config_files(self) -> List[Path]:
        """Find all configuration files in the project."""
        config_files = []

        # Common extensions
        extensions = ['*.yaml', '*.yml', '*.json', '*.toml', '*.ini']

        # Search in common directories
        search_dirs = [
            Path('config'),
            Path('services'),
            Path('infrastructure'),
            Path('.'),
        ]

        for search_dir in search_dirs:
            if search_dir.exists():
                for ext in extensions:
                    config_files.extend(search_dir.glob(f'**/{ext}'))

        # Remove duplicates and sort
        return sorted(list(set(config_files)))

    async def _validate_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a single YAML file."""
        result = {
            'file': str(file_path),
            'valid': False,
            'error': None
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Try to parse as YAML
            yaml.safe_load(content)
            result['valid'] = True

        except yaml.YAMLError as e:
            result['error'] = str(e)
        except Exception as e:
            result['error'] = f"Unexpected error: {e}"

        return result

    async def _perform_configuration_consistency_check(self) -> List[Dict[str, Any]]:
        """Perform configuration consistency checks."""
        issues = []

        try:
            # Check for common consistency issues
            config_files = await self._find_all_config_files()

            # Group by service
            service_configs = {}
            for config_file in config_files:
                # Extract service name from path
                parts = config_file.parts
                if 'services' in parts:
                    service_index = parts.index('services')
                    if service_index + 1 < len(parts):
                        service_name = parts[service_index + 1]
                        if service_name not in service_configs:
                            service_configs[service_name] = []
                        service_configs[service_name].append(config_file)

            # Check for missing required configurations
            for service_name, configs in service_configs.items():
                # Check if service has a main config file
                has_main_config = any('config.yaml' in str(c) or f'{service_name}.yaml' in str(c) for c in configs)
                if not has_main_config:
                    issues.append({
                        'service': service_name,
                        'severity': 'warning',
                        'issue': 'Missing main configuration file',
                        'suggestion': f'Create config.yaml or {service_name}.yaml'
                    })

                # Check for duplicate configurations
                config_names = [c.name for c in configs]
                duplicates = set([name for name in config_names if config_names.count(name) > 1])
                if duplicates:
                    issues.append({
                        'service': service_name,
                        'severity': 'warning',
                        'issue': f'Duplicate configuration files: {", ".join(duplicates)}',
                        'suggestion': 'Consolidate duplicate configurations'
                    })

        except Exception as e:
            issues.append({
                'service': 'system',
                'severity': 'error',
                'issue': f'Error during consistency check: {e}',
                'suggestion': 'Review configuration structure'
            })

        return issues

    async def _perform_configuration_health_check(self) -> Dict[str, str]:
        """Perform comprehensive configuration health check."""
        health_results = {}

        try:
            # Check YAML syntax
            config_files = await self._find_all_config_files()
            yaml_issues = 0

            for config_file in config_files:
                if config_file.suffix in ['.yaml', '.yml']:
                    result = await self._validate_yaml_file(config_file)
                    if not result['valid']:
                        yaml_issues += 1

            health_results['yaml_syntax'] = (
                'healthy' if yaml_issues == 0 else 'unhealthy',
                f"{len(config_files)} files checked, {yaml_issues} syntax errors"
            )

            # Check for required configurations
            required_configs = ['config/config.yaml', 'config/app.yaml']
            missing_configs = []

            for required_config in required_configs:
                if not Path(required_config).exists():
                    missing_configs.append(required_config)

            health_results['required_configs'] = (
                'healthy' if not missing_configs else 'unhealthy',
                f"Missing: {', '.join(missing_configs)}" if missing_configs else "All required configs present"
            )

            # Check environment variables
            env_issues = await self._check_environment_health()
            health_results['environment_variables'] = env_issues

            # Check service configurations
            service_issues = await self._check_service_configurations()
            health_results['service_configurations'] = service_issues

        except Exception as e:
            health_results['health_check_error'] = ('unhealthy', f"Health check failed: {e}")

        return health_results

    async def _check_environment_health(self) -> Tuple[str, str]:
        """Check environment variable health."""
        try:
            # Check for critical environment variables
            critical_vars = ['ENVIRONMENT']
            missing_critical = []

            for var in critical_vars:
                if var not in os.environ:
                    missing_critical.append(var)

            if missing_critical:
                return 'unhealthy', f"Missing critical variables: {', '.join(missing_critical)}"
            else:
                return 'healthy', "Critical environment variables are set"

        except Exception as e:
            return 'unhealthy', f"Environment check failed: {e}"

    async def _check_service_configurations(self) -> Tuple[str, str]:
        """Check service configuration health."""
        try:
            services_dir = Path('services')
            if not services_dir.exists():
                return 'unhealthy', "Services directory not found"

            service_dirs = [d for d in services_dir.iterdir() if d.is_dir()]
            configured_services = 0

            for service_dir in service_dirs:
                config_files = list(service_dir.glob('*.yaml')) + list(service_dir.glob('config/*.yaml'))
                if config_files:
                    configured_services += 1

            health_percentage = (configured_services / len(service_dirs) * 100) if service_dirs else 0

            if health_percentage >= 80:
                return 'healthy', f"{configured_services}/{len(service_dirs)} services configured"
            elif health_percentage >= 50:
                return 'warning', f"{configured_services}/{len(service_dirs)} services configured - some missing configs"
            else:
                return 'unhealthy', f"{configured_services}/{len(service_dirs)} services configured - many missing configs"

        except Exception as e:
            return 'unhealthy', f"Service configuration check failed: {e}"
