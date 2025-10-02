#!/usr/bin/env python3
"""
Environment Variable Standardization System

Standardizes environment variable naming conventions across all services
to ensure consistency and maintainability.

This system:
- Analyzes current environment variable usage patterns
- Applies standardized naming conventions
- Provides migration guidance for existing variables
- Ensures consistency across all services
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


class EnvVarCategory(Enum):
    """Categories of environment variables."""
    SERVICE_IDENTIFICATION = "service"
    DEPLOYMENT_ENVIRONMENT = "environment"
    DATABASE_CONFIGURATION = "database"
    REDIS_CONFIGURATION = "redis"
    LOGGING_CONFIGURATION = "logging"
    HEALTH_CHECK_SETTINGS = "health"
    API_CONFIGURATION = "api"
    SECURITY_CONFIGURATION = "security"
    AUTHENTICATION_CONFIGURATION = "auth"
    CORS_CONFIGURATION = "cors"
    PERFORMANCE_CONFIGURATION = "performance"
    MONITORING_CONFIGURATION = "monitoring"
    EXTERNAL_SERVICE_INTEGRATION = "external"
    FEATURE_FLAGS = "feature"
    DEBUG_CONFIGURATION = "debug"


@dataclass
class StandardizedEnvVar:
    """Represents a standardized environment variable."""
    name: str
    category: EnvVarCategory
    description: str
    example_values: List[str] = field(default_factory=list)
    required: bool = False
    default_value: Optional[str] = None
    validation_pattern: Optional[str] = None


@dataclass
class EnvVarIssue:
    """Represents an environment variable standardization issue."""
    file_path: str
    service_name: str
    current_name: str
    recommended_name: str
    category: str
    severity: str  # 'error', 'warning', 'info'
    description: str
    can_auto_fix: bool = False


class EnvironmentVariableStandardizer:
    """
    Standardizes environment variable naming conventions across the ecosystem.

    Implements a comprehensive naming convention that categorizes variables
    by purpose and ensures consistent naming patterns.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Standardized environment variable definitions
        self.standard_variables = self._define_standard_variables()

        # Mapping of old prefixes to new standardized ones
        self.prefix_mapping = self._create_prefix_mapping()

    def _define_standard_variables(self) -> Dict[str, StandardizedEnvVar]:
        """Define the standardized environment variable set."""
        return {
            # Service Identification
            "SERVICE_NAME": StandardizedEnvVar(
                name="SERVICE_NAME",
                category=EnvVarCategory.SERVICE_IDENTIFICATION,
                description="Human-readable service name",
                example_values=["orchestrator", "analysis-service"],
                required=True
            ),
            "SERVICE_VERSION": StandardizedEnvVar(
                name="SERVICE_VERSION",
                category=EnvVarCategory.SERVICE_IDENTIFICATION,
                description="Service version identifier",
                example_values=["1.0.0", "2.1.3"],
                default_value="1.0.0"
            ),
            "SERVICE_API_PORT": StandardizedEnvVar(
                name="SERVICE_API_PORT",
                category=EnvVarCategory.SERVICE_IDENTIFICATION,
                description="Port the service listens on",
                example_values=["8080", "3000"],
                validation_pattern=r"^\d{2,5}$"
            ),

            # Deployment Environment
            "ENVIRONMENT": StandardizedEnvVar(
                name="ENVIRONMENT",
                category=EnvVarCategory.DEPLOYMENT_ENVIRONMENT,
                description="Deployment environment",
                example_values=["development", "staging", "production"],
                required=True,
                default_value="development"
            ),
            "DEPLOYMENT_STAGE": StandardizedEnvVar(
                name="DEPLOYMENT_STAGE",
                category=EnvVarCategory.DEPLOYMENT_ENVIRONMENT,
                description="Deployment stage identifier",
                example_values=["dev", "test", "prod"]
            ),

            # Database Configuration
            "DATABASE_URL": StandardizedEnvVar(
                name="DATABASE_URL",
                category=EnvVarCategory.DATABASE_CONFIGURATION,
                description="Complete database connection URL",
                example_values=["postgresql://user:pass@host:5432/db"],
                required=True
            ),
            "DATABASE_API_HOST": StandardizedEnvVar(
                name="DATABASE_API_HOST",
                category=EnvVarCategory.DATABASE_CONFIGURATION,
                description="Database server hostname",
                example_values=["localhost", "db.example.com"]
            ),
            "DATABASE_API_PORT": StandardizedEnvVar(
                name="DATABASE_API_PORT",
                category=EnvVarCategory.DATABASE_CONFIGURATION,
                description="Database server port",
                example_values=["5432", "3306"],
                validation_pattern=r"^\d{2,5}$"
            ),
            "DATABASE_NAME": StandardizedEnvVar(
                name="DATABASE_NAME",
                category=EnvVarCategory.DATABASE_CONFIGURATION,
                description="Database name",
                example_values=["myapp", "hackathon_db"]
            ),
            "DATABASE_USER": StandardizedEnvVar(
                name="DATABASE_USER",
                category=EnvVarCategory.DATABASE_CONFIGURATION,
                description="Database username",
                example_values=["app_user", "admin"]
            ),

            # Redis Configuration
            "REDIS_URL": StandardizedEnvVar(
                name="REDIS_URL",
                category=EnvVarCategory.REDIS_CONFIGURATION,
                description="Complete Redis connection URL",
                example_values=["redis://localhost:6379", "redis://:password@host:6379"]
            ),
            "REDIS_API_HOST": StandardizedEnvVar(
                name="REDIS_API_HOST",
                category=EnvVarCategory.REDIS_CONFIGURATION,
                description="Redis server hostname",
                example_values=["localhost", "redis.example.com"],
                default_value="redis"
            ),
            "REDIS_API_PORT": StandardizedEnvVar(
                name="REDIS_API_PORT",
                category=EnvVarCategory.REDIS_CONFIGURATION,
                description="Redis server port",
                example_values=["6379", "6380"],
                default_value="6379",
                validation_pattern=r"^\d{2,5}$"
            ),

            # Logging Configuration
            "LOG_LEVEL": StandardizedEnvVar(
                name="LOG_LEVEL",
                category=EnvVarCategory.LOGGING_CONFIGURATION,
                description="Logging verbosity level",
                example_values=["DEBUG", "INFO", "WARNING", "ERROR"],
                default_value="INFO"
            ),
            "LOG_FORMAT": StandardizedEnvVar(
                name="LOG_FORMAT",
                category=EnvVarCategory.LOGGING_CONFIGURATION,
                description="Log output format",
                example_values=["json", "text"],
                default_value="json"
            ),

            # Health Check Settings
            "HEALTH_CHECK_ENABLED": StandardizedEnvVar(
                name="HEALTH_CHECK_ENABLED",
                category=EnvVarCategory.HEALTH_CHECK_SETTINGS,
                description="Enable health check endpoints",
                example_values=["true", "false"],
                default_value="true"
            ),
            "HEALTH_CHECK_INTERVAL": StandardizedEnvVar(
                name="HEALTH_CHECK_INTERVAL",
                category=EnvVarCategory.HEALTH_CHECK_SETTINGS,
                description="Health check interval",
                example_values=["30s", "60s"],
                default_value="30s"
            ),

            # API Configuration
            "API_API_HOST": StandardizedEnvVar(
                name="API_API_HOST",
                category=EnvVarCategory.API_CONFIGURATION,
                description="API server hostname",
                example_values=["0.0.0.0", "localhost"],
                default_value="0.0.0.0"
            ),
            "API_API_PORT": StandardizedEnvVar(
                name="API_API_PORT",
                category=EnvVarCategory.API_CONFIGURATION,
                description="API server port",
                example_values=["8080", "3000"],
                validation_pattern=r"^\d{2,5}$"
            ),

            # Security Configuration
            "SECRET_KEY": StandardizedEnvVar(
                name="SECRET_KEY",
                category=EnvVarCategory.SECURITY_CONFIGURATION,
                description="Application secret key",
                example_values=["your-secret-key-here"],
                required=True
            ),
            "ALLOWED_API_HOSTS": StandardizedEnvVar(
                name="ALLOWED_API_HOSTS",
                category=EnvVarCategory.SECURITY_CONFIGURATION,
                description="Comma-separated list of allowed hosts",
                example_values=["localhost,example.com", "*"]
            ),

            # Authentication Configuration
            "JWT_SECRET": StandardizedEnvVar(
                name="JWT_SECRET",
                category=EnvVarCategory.AUTHENTICATION_CONFIGURATION,
                description="JWT signing secret",
                required=True
            ),
            "JWT_EXPIRATION": StandardizedEnvVar(
                name="JWT_EXPIRATION",
                category=EnvVarCategory.AUTHENTICATION_CONFIGURATION,
                description="JWT token expiration time",
                example_values=["3600", "86400"],
                default_value="3600"
            ),

            # CORS Configuration
            "CORS_ORIGINS": StandardizedEnvVar(
                name="CORS_ORIGINS",
                category=EnvVarCategory.CORS_CONFIGURATION,
                description="Comma-separated list of allowed CORS origins",
                example_values=["http://localhost:3000,https://example.com"]
            ),
            "CORS_METHODS": StandardizedEnvVar(
                name="CORS_METHODS",
                category=EnvVarCategory.CORS_CONFIGURATION,
                description="Allowed CORS HTTP methods",
                example_values=["GET,POST,PUT,DELETE"],
                default_value="GET,POST,PUT,DELETE"
            ),

            # Performance Configuration
            "MAX_WORKERS": StandardizedEnvVar(
                name="MAX_WORKERS",
                category=EnvVarCategory.PERFORMANCE_CONFIGURATION,
                description="Maximum number of worker processes",
                example_values=["4", "8"],
                default_value="4"
            ),
            "WORKER_TIMEOUT": StandardizedEnvVar(
                name="WORKER_TIMEOUT",
                category=EnvVarCategory.PERFORMANCE_CONFIGURATION,
                description="Worker process timeout in seconds",
                example_values=["300", "600"],
                default_value="300"
            ),

            # Monitoring Configuration
            "METRICS_ENABLED": StandardizedEnvVar(
                name="METRICS_ENABLED",
                category=EnvVarCategory.MONITORING_CONFIGURATION,
                description="Enable metrics collection",
                example_values=["true", "false"],
                default_value="true"
            ),
            "METRICS_API_PORT": StandardizedEnvVar(
                name="METRICS_API_PORT",
                category=EnvVarCategory.MONITORING_CONFIGURATION,
                description="Metrics server port",
                example_values=["9090", "8081"],
                default_value="9090"
            ),

            # External Service Integration
            "EXTERNAL_API_URL": StandardizedEnvVar(
                name="EXTERNAL_API_URL",
                category=EnvVarCategory.EXTERNAL_SERVICE_INTEGRATION,
                description="External API base URL",
                example_values=["https://api.example.com"]
            ),
            "EXTERNAL_API_KEY": StandardizedEnvVar(
                name="EXTERNAL_API_KEY",
                category=EnvVarCategory.EXTERNAL_SERVICE_INTEGRATION,
                description="External API authentication key"
            ),

            # Feature Flags
            "FEATURE_ADVANCED_LOGGING": StandardizedEnvVar(
                name="FEATURE_ADVANCED_LOGGING",
                category=EnvVarCategory.FEATURE_FLAGS,
                description="Enable advanced logging features",
                example_values=["true", "false"],
                default_value="false"
            ),

            # Debug Configuration
            "DEBUG_MODE": StandardizedEnvVar(
                name="DEBUG_MODE",
                category=EnvVarCategory.DEBUG_CONFIGURATION,
                description="Enable debug mode",
                example_values=["true", "false"],
                default_value="false"
            ),
            "DEBUG_SQL": StandardizedEnvVar(
                name="DEBUG_SQL",
                category=EnvVarCategory.DEBUG_CONFIGURATION,
                description="Enable SQL query logging",
                example_values=["true", "false"],
                default_value="false"
            )
        }

    def _create_prefix_mapping(self) -> Dict[str, str]:
        """Create mapping from old prefixes to standardized ones."""
        return {
            # Service identification
            "SERVICE_": "SERVICE_",

            # Environment
            "ENVIRONMENT": "ENVIRONMENT",
            "DEPLOYMENT_": "DEPLOYMENT_",

            # Database
            "DATABASE_": "DATABASE_",
            "DB_": "DATABASE_",
            "POSTGRES_": "DATABASE_",
            "MYSQL_": "DATABASE_",

            # Redis
            "REDIS_": "REDIS_",

            # Logging
            "LOG_": "LOG_",
            "LOGGING_": "LOG_",

            # Health
            "HEALTH_": "HEALTH_",

            # API
            "API_": "API_",

            # Security
            "SECRET_": "SECRET_",
            "SSL_": "SSL_",
            "SECURITY_": "SECURITY_",

            # Authentication
            "JWT_": "JWT_",
            "AUTH_": "AUTH_",
            "OAUTH_": "AUTH_",

            # CORS
            "CORS_": "CORS_",

            # Performance
            "MAX_": "MAX_",
            "WORKER_": "WORKER_",
            "PERFORMANCE_": "PERFORMANCE_",

            # Monitoring
            "METRICS_": "METRICS_",
            "MONITORING_": "MONITORING_",
            "PROMETHEUS_": "METRICS_",

            # External services
            "EXTERNAL_": "EXTERNAL_",
            "THIRD_PARTY_": "EXTERNAL_",

            # Feature flags
            "ENABLE_": "FEATURE_",
            "DISABLE_": "FEATURE_",
            "FEATURE_": "FEATURE_",

            # Debug
            "DEBUG_": "DEBUG_",

            # Legacy prefixes to standardize
            "LUCID_": "EXTERNAL_LUCID_",
            "ANTHROPIC_": "EXTERNAL_ANTHROPIC_",
            "OPENAI_": "EXTERNAL_OPENAI_",
            "AWS_": "EXTERNAL_AWS_",
            "GITHUB_": "EXTERNAL_GITHUB_",
            "JIRA_": "EXTERNAL_JIRA_",
            "CONFLUENCE_": "EXTERNAL_CONFLUENCE_",
            "FIGMA_": "EXTERNAL_FIGMA_",
            "MIRO_": "EXTERNAL_MIRO_"
        }

    def analyze_environment_variables(self) -> Dict[str, Any]:
        """
        Analyze current environment variable usage across all services.

        Returns:
            Comprehensive analysis of environment variable patterns
        """
        analysis = {
            'total_services': 0,
            'env_vars_found': 0,
            'unique_prefixes': set(),
            'issues': [],
            'recommendations': []
        }

        # Find all service directories
        service_dirs = [d for d in self.project_root.glob("services/*") if d.is_dir()]

        for service_dir in service_dirs:
            service_name = service_dir.name
            analysis['total_services'] += 1

            # Check docker-compose files
            compose_files = list(service_dir.glob("docker-compose*.yml")) + list(service_dir.glob("docker-compose*.yaml"))

            for compose_file in compose_files:
                env_vars = self._extract_env_vars_from_compose(compose_file)
                analysis['env_vars_found'] += len(env_vars)

                for env_var in env_vars:
                    prefix = self._extract_prefix(env_var)
                    if prefix:
                        analysis['unique_prefixes'].add(prefix)

                    # Check against standards
                    issues = self._check_env_var_standards(service_name, env_var, str(compose_file))
                    analysis['issues'].extend(issues)

            # Check configuration files
            config_files = list(service_dir.glob("config*.yml")) + list(service_dir.glob("config*.yaml"))

            for config_file in config_files:
                env_vars = self._extract_env_vars_from_config(config_file)
                analysis['env_vars_found'] += len(env_vars)

                for env_var in env_vars:
                    prefix = self._extract_prefix(env_var)
                    if prefix:
                        analysis['unique_prefixes'].add(prefix)

        analysis['unique_prefixes'] = sorted(list(analysis['unique_prefixes']))
        analysis['recommendations'] = self._generate_recommendations(analysis)

        return analysis

    def _extract_env_vars_from_compose(self, compose_file: Path) -> List[str]:
        """Extract environment variable names from docker-compose file."""
        env_vars = []

        try:
            import yaml
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)

            if not config or 'services' not in config:
                return env_vars

            for service_name, service_config in config['services'].items():
                if 'environment' in service_config:
                    env_config = service_config['environment']

                    if isinstance(env_config, list):
                        for env_item in env_config:
                            if isinstance(env_item, str):
                                if '=' in env_item:
                                    var_name = env_item.split('=', 1)[0]
                                    env_vars.append(var_name)
                                else:
                                    env_vars.append(env_item)
                    elif isinstance(env_config, dict):
                        env_vars.extend(env_config.keys())

        except Exception as e:
            print(f"Error parsing {compose_file}: {e}")

        return env_vars

    def _extract_env_vars_from_config(self, config_file: Path) -> List[str]:
        """Extract environment variable references from config files."""
        env_vars = []

        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            # Look for ${VAR_NAME} patterns in the config
            def find_env_refs(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, str) and '${' in value:
                            # Extract variable names from ${VAR_NAME} patterns
                            matches = re.findall(r'\$\{([^}]+)\}', value)
                            for match in matches:
                                var_name = match.split(':')[0]  # Remove default values
                                if var_name not in env_vars:
                                    env_vars.append(var_name)
                        else:
                            find_env_refs(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_env_refs(item, f"{path}[{i}]")

            find_env_refs(config)

        except Exception as e:
            print(f"Error parsing {config_file}: {e}")

        return env_vars

    def _extract_prefix(self, env_var: str) -> Optional[str]:
        """Extract the prefix from an environment variable name."""
        if '_' not in env_var:
            return None

        # Find the first underscore and take everything before it
        prefix = env_var.split('_', 1)[0]
        return f"{prefix}_" if prefix else None

    def _check_env_var_standards(self, service_name: str, env_var: str, file_path: str) -> List[EnvVarIssue]:
        """Check if an environment variable follows naming standards."""
        issues = []

        # Check if it's in our standardized set
        if env_var not in self.standard_variables:
            recommended = self._suggest_standard_name(env_var)

            if recommended != env_var:
                issues.append(EnvVarIssue(
                    file_path=file_path,
                    service_name=service_name,
                    current_name=env_var,
                    recommended_name=recommended,
                    category="naming_standard",
                    severity="warning",
                    description=f"Environment variable '{env_var}' should follow standardized naming convention",
                    can_auto_fix=False
                ))

        return issues

    def _suggest_standard_name(self, env_var: str) -> str:
        """Suggest a standardized name for an environment variable."""
        if '_' not in env_var:
            return env_var

        prefix = env_var.split('_', 1)[0]
        standardized_prefix = self.prefix_mapping.get(f"{prefix}_", f"{prefix}_")

        if standardized_prefix != f"{prefix}_":
            # Replace the prefix
            return env_var.replace(f"{prefix}_", standardized_prefix, 1)

        return env_var

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on the analysis."""
        recommendations = []

        if len(analysis['unique_prefixes']) > 20:
            recommendations.append("Consider consolidating the 20+ different environment variable prefixes into standardized categories")

        if analysis['issues']:
            recommendations.append(f"Address {len(analysis['issues'])} environment variable naming issues")

        recommendations.extend([
            "Implement environment variable naming governance",
            "Create environment variable documentation",
            "Add validation for environment variable names in CI/CD",
            "Consider using environment variable groups by category"
        ])

        return recommendations

    def standardize_env_vars(self, mode: str = "analyze") -> Dict[str, Any]:
        """
        Standardize environment variables across all services.

        Args:
            mode: 'analyze', 'dry-run', or 'apply'

        Returns:
            Standardization report
        """
        print(f"🔧 Environment Variable Standardization (Mode: {mode})")
        print("=" * 60)

        # Analyze current state
        analysis = self.analyze_environment_variables()

        print(f"📊 Analysis Results:")
        print(f"  Services analyzed: {analysis['total_services']}")
        print(f"  Environment variables found: {analysis['env_vars_found']}")
        print(f"  Unique prefixes: {len(analysis['unique_prefixes'])}")
        print(f"  Issues found: {len(analysis['issues'])}")

        if analysis['unique_prefixes']:
            print(f"\n🔍 Prefixes found: {', '.join(analysis['unique_prefixes'][:10])}")
            if len(analysis['unique_prefixes']) > 10:
                print(f"  ... and {len(analysis['unique_prefixes']) - 10} more")

        if analysis['issues']:
            print(f"\n⚠️  Sample issues:")
            for issue in analysis['issues'][:5]:
                print(f"  • {issue.service_name}: {issue.current_name} → {issue.recommended_name}")

        if analysis['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in analysis['recommendations']:
                print(f"  • {rec}")

        # For now, just return the analysis (full standardization would require more complex logic)
        return {
            'analysis': analysis,
            'mode': mode,
            'standardized_variables': self.standard_variables,
            'prefix_mapping': self.prefix_mapping
        }


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Environment Variable Standardization System")
    parser.add_argument('--mode', '-m', choices=['analyze', 'dry-run', 'apply'],
                       default='analyze', help='Standardization mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    standardizer = EnvironmentVariableStandardizer()

    try:
        result = standardizer.standardize_env_vars(mode=args.mode)

        if args.verbose:
            print("\n📋 Detailed Results:")
            print(f"Mode: {result['mode']}")
            print(f"Services analyzed: {result['analysis']['total_services']}")
            print(f"Variables found: {result['analysis']['env_vars_found']}")
            print(f"Prefixes identified: {len(result['analysis']['unique_prefixes'])}")

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
