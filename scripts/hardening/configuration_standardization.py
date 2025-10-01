#!/usr/bin/env python3
"""
Configuration Standardization Script

This script helps standardize configuration management across all services
in the LLM Documentation Ecosystem by:

1. Migrating services to use the centralized configuration manager
2. Standardizing environment variable naming
3. Moving hardcoded values to configuration files
4. Updating docker-compose files to use standardized patterns
5. Validating configuration consistency across services
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
from dataclasses import dataclass, asdict
import re
import shutil


@dataclass
class StandardizationResult:
    """Result of configuration standardization for a service."""
    service_name: str
    success: bool
    changes_made: List[str]
    warnings: List[str]
    errors: List[str]


class ConfigurationStandardizer:
    """Standardizes configuration management across services."""

    def __init__(self, services_dir: Path = Path("services")):
        self.services_dir = services_dir
        self.shared_dir = services_dir / "shared"

        # Standardized port mappings
        self.standard_ports = {
            "orchestrator": 5099,
            "doc_store": 5087,
            "analysis-service": 5020,
            "source-agent": 5085,
            "frontend": 3000,
            "memory-agent": 5090,
            "discovery-agent": 5045,
            "prompt_store": 5110,
            "interpreter": 5120,
            "cli": 5130,
            "user-store": 5150,
            "external-service-store": 5140,
            "notification-service": 5130,
            "llm-gateway": 5055,
            "summarizer-hub": 5160,
            "github-mcp": 5030,
            "bedrock-proxy": 5002,
            "secure-analyzer": 5070,
            "code-analyzer": 5025,
            "architecture-digitizer": 5105,
            "project-simulation": 5075,
            "mock-data-generator": 5065,
            "simulation-dashboard": 8501,
            "unified-api-dashboard": 8000,
            "log-collector": 5080
        }

        # Environment variable standardization mappings
        self.env_var_mappings = {
            # Old -> New mappings for consistency
            "ORCHESTRATOR_URL": "ORCHESTRATOR_URL",
            "DOC_STORE_URL": "DOC_STORE_URL",
            "ANALYSIS_SERVICE_URL": "ANALYSIS_SERVICE_URL",
            "SOURCE_AGENT_URL": "SOURCE_AGENT_URL",
            "FRONTEND_URL": "FRONTEND_URL",
            "MEMORY_AGENT_URL": "MEMORY_AGENT_URL",
            "DISCOVERY_AGENT_URL": "DISCOVERY_AGENT_URL",
            "PROMPT_STORE_URL": "PROMPT_STORE_URL",
            "INTERPRETER_URL": "INTERPRETER_URL",
            "CLI_SERVICE_URL": "CLI_SERVICE_URL",
            "USER_STORE_URL": "USER_STORE_URL",
            "EXTERNAL_SERVICE_STORE_URL": "EXTERNAL_SERVICE_STORE_URL",
            "NOTIFICATION_SERVICE_URL": "NOTIFICATION_SERVICE_URL",
            "LLM_GATEWAY_URL": "LLM_GATEWAY_URL",
            "SUMMARIZER_HUB_URL": "SUMMARIZER_HUB_URL",
            "GITHUB_MCP_URL": "GITHUB_MCP_URL",
            "BEDROCK_PROXY_URL": "BEDROCK_PROXY_URL",
            "SECURE_ANALYZER_URL": "SECURE_ANALYZER_URL",
            "CODE_ANALYZER_URL": "CODE_ANALYZER_URL",
            "ARCHITECTURE_DIGITIZER_URL": "ARCHITECTURE_DIGITIZER_URL",
            "PROJECT_SIMULATION_URL": "PROJECT_SIMULATION_URL",
            "MOCK_DATA_GENERATOR_URL": "MOCK_DATA_GENERATOR_URL",
            "SIMULATION_DASHBOARD_URL": "SIMULATION_DASHBOARD_URL",
            "UNIFIED_API_DASHBOARD_URL": "UNIFIED_API_DASHBOARD_URL",
            "LOG_COLLECTOR_URL": "LOG_COLLECTOR_URL",
            # Standardize common patterns
            "REDIS_API_HOST": "REDIS_API_HOST",
            "REDIS_API_PORT": "REDIS_API_PORT",
            "LOG_LEVEL": "LOG_LEVEL",
            "SERVER_API_HOST": "SERVER_API_HOST",
            "SERVER_API_PORT": "SERVER_API_PORT",
            "ENVIRONMENT": "ENVIRONMENT",
            "DEBUG": "DEBUG"
        }

    def standardize_all_services(self, dry_run: bool = True) -> List[StandardizationResult]:
        """Standardize configuration for all services."""
        results = []

        service_dirs = [d for d in self.services_dir.iterdir()
                       if d.is_dir() and not d.name.startswith('.') and d.name not in ['shared', '__pycache__']]

        for service_dir in service_dirs:
            result = self.standardize_service(service_dir, dry_run)
            results.append(result)

        return results

    def standardize_service(self, service_dir: Path, dry_run: bool = True) -> StandardizationResult:
        """Standardize configuration for a single service."""
        service_name = service_dir.name
        result = StandardizationResult(service_name, True, [], [], [])

        try:
            print(f"🔧 Standardizing {service_name}...")

            # 1. Update config.yaml to use standardized format
            config_changes = self._standardize_config_yaml(service_dir, dry_run)
            result.changes_made.extend(config_changes)

            # 2. Update docker-compose.yml
            docker_changes = self._standardize_docker_compose(service_dir, dry_run)
            result.changes_made.extend(docker_changes)

            # 3. Update main.py to use configuration manager
            main_changes = self._update_main_py(service_dir, dry_run)
            result.changes_made.extend(main_changes)

            # 4. Create environment-specific configs if needed
            env_changes = self._create_environment_configs(service_dir, dry_run)
            result.changes_made.extend(env_changes)

            # 5. Check for issues and warnings
            warnings = self._check_configuration_issues(service_dir)
            result.warnings.extend(warnings)

            if dry_run:
                result.changes_made.insert(0, "[DRY RUN] Would make the following changes:")

        except Exception as e:
            result.success = False
            result.errors.append(f"Standardization failed: {str(e)}")

        return result

    def _standardize_config_yaml(self, service_dir: Path, dry_run: bool) -> List[str]:
        """Standardize the config.yaml file."""
        changes = []
        config_path = service_dir / "config.yaml"

        if not config_path.exists():
            changes.append("Create new standardized config.yaml")
            if not dry_run:
                self._create_standard_config_yaml(service_dir)
            return changes

        # Read existing config
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            changes.append(f"Fix malformed config.yaml: {e}")
            if not dry_run:
                self._create_standard_config_yaml(service_dir)
            return changes

        # Standardize the config
        standardized_config = self._standardize_config_dict(config, service_dir.name)

        # Check if changes are needed
        if standardized_config != config:
            changes.append("Update config.yaml to standardized format")
            if not dry_run:
                with open(config_path, 'w') as f:
                    yaml.dump(standardized_config, f, default_flow_style=False, indent=2)

        return changes

    def _standardize_config_dict(self, config: Dict[str, Any], service_name: str) -> Dict[str, Any]:
        """Standardize a configuration dictionary."""
        standardized = {}

        # Ensure server section exists with correct port
        if 'server' not in config:
            config['server'] = {}

        if 'port' not in config['server'] and service_name in self.standard_ports:
            config['server']['port'] = self.standard_ports[service_name]

        # Ensure all required sections exist
        required_sections = ['server', 'redis', 'logging', 'services', 'limits', 'health', 'security']
        for section in required_sections:
            if section not in config:
                config[section] = {}

        # Convert environment variables to standardized format
        def convert_env_vars(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str):
                        # Convert ${VAR} to ${VAR:-default} format
                        if value.startswith('${') and ':-' not in value:
                            # Extract variable name
                            var_match = re.match(r'\$\{([^}]+)\}', value)
                            if var_match:
                                var_name = var_match.group(1)
                                # Use empty string as default if no default specified
                                obj[key] = f"${{{var_name}:-}}"
                    elif isinstance(value, (dict, list)):
                        convert_env_vars(value)
            elif isinstance(obj, list):
                for item in obj:
                    convert_env_vars(item)

        convert_env_vars(config)

        return config

    def _create_standard_config_yaml(self, service_dir: Path):
        """Create a new standardized config.yaml file."""
        service_name = service_dir.name
        port = self.standard_ports.get(service_name, 8080)

        config = {
            "server": {
                "host": "${SERVER_API_HOST:-0.0.0.0}",
                "port": port,
                "debug": "${DEBUG:-false}",
                "workers": "${SERVER_WORKERS:-1}",
                "timeout": "${SERVER_TIMEOUT:-30}"
            },
            "redis": {
                "host": "${REDIS_API_HOST:-redis}",
                "port": "${REDIS_API_PORT:-6379}",
                "db": "${REDIS_DB:-0}",
                "max_connections": "${REDIS_MAX_CONNECTIONS:-10}"
            },
            "logging": {
                "level": "${LOG_LEVEL:-INFO}",
                "format": "${LOG_FORMAT:-json}",
                "structured": "${LOG_STRUCTURED:-true}",
                "console": "${LOG_CONSOLE:-true}"
            },
            "services": {
                "orchestrator_url": "${ORCHESTRATOR_URL:-http://orchestrator:5099}",
                "doc_store_url": "${DOC_STORE_URL:-http://doc_store:5087}",
                "analysis_service_url": "${ANALYSIS_SERVICE_URL:-http://analysis-service:5020}",
                "source_agent_url": "${SOURCE_AGENT_URL:-http://source-agent:5085}",
                "frontend_url": "${FRONTEND_URL:-http://frontend:3000}"
            },
            "limits": {
                "max_items": "${MAX_ITEMS:-1000}",
                "timeout": "${TIMEOUT:-30}",
                "max_connections": "${MAX_CONNECTIONS:-10}",
                "max_message_length": "${MAX_MESSAGE_LENGTH:-1000}"
            },
            "health": {
                "check_interval": "${HEALTH_CHECK_INTERVAL:-30}",
                "timeout": "${HEALTH_TIMEOUT:-10}",
                "enabled": "${HEALTH_ENABLED:-true}"
            },
            "security": {
                "cors_origins": ["${CORS_ORIGINS:-*}"]
            }
        }

        config_path = service_dir / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

    def _standardize_docker_compose(self, service_dir: Path, dry_run: bool) -> List[str]:
        """Standardize docker-compose.yml file."""
        changes = []
        compose_path = service_dir / "docker-compose.yml"

        if not compose_path.exists():
            changes.append("Create standardized docker-compose.yml")
            if not dry_run:
                self._create_standard_docker_compose(service_dir)
            return changes

        # Read and update existing compose file
        try:
            with open(compose_path, 'r') as f:
                compose_config = yaml.safe_load(f) or {}
        except Exception as e:
            changes.append(f"Fix malformed docker-compose.yml: {e}")
            if not dry_run:
                self._create_standard_docker_compose(service_dir)
            return changes

        # Standardize the compose configuration
        standardized_compose = self._standardize_compose_dict(compose_config, service_dir.name)

        if standardized_compose != compose_config:
            changes.append("Update docker-compose.yml to standardized format")
            if not dry_run:
                with open(compose_path, 'w') as f:
                    yaml.dump(standardized_compose, f, default_flow_style=False, indent=2)

        return changes

    def _standardize_compose_dict(self, compose: Dict[str, Any], service_name: str) -> Dict[str, Any]:
        """Standardize a docker-compose configuration dictionary."""
        if 'services' not in compose:
            compose['services'] = {}

        if service_name not in compose['services']:
            compose['services'][service_name] = {}

        service_config = compose['services'][service_name]

        # Ensure standard structure
        if 'image' not in service_config:
            service_config['image'] = 'python:3.12-slim'

        if 'working_dir' not in service_config:
            service_config['working_dir'] = '/app'

        if 'volumes' not in service_config:
            service_config['volumes'] = [
                '../../:/app:ro',
                './:/app/services/' + service_name + ':rw'
            ]

        if 'environment' not in service_config:
            service_config['environment'] = [
                'ENVIRONMENT=development'
            ]

        if 'command' not in service_config:
            service_config['command'] = f'python services/{service_name}/main.py'

        if 'ports' not in service_config and service_name in self.standard_ports:
            port = self.standard_ports[service_name]
            service_config['ports'] = [f'{port}:{port}']

        if 'healthcheck' not in service_config:
            service_config['healthcheck'] = {
                'test': ['CMD', 'curl', '-f', f'http://localhost:{self.standard_ports.get(service_name, 8080)}/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }

        return compose

    def _create_standard_docker_compose(self, service_dir: Path):
        """Create a new standardized docker-compose.yml file."""
        service_name = service_dir.name
        port = self.standard_ports.get(service_name, 8080)

        compose_config = {
            'version': '3.9',
            'services': {
                service_name: {
                    'image': 'python:3.12-slim',
                    'working_dir': '/app',
                    'volumes': [
                        '../../:/app:ro',
                        f'./:/app/services/{service_name}:rw'
                    ],
                    'environment': [
                        'ENVIRONMENT=development'
                    ],
                    'command': f'bash -lc "pip install --no-cache-dir fastapi uvicorn pydantic && python services/{service_name}/main.py"',
                    'ports': [f'{port}:{port}'],
                    'healthcheck': {
                        'test': ['CMD', 'curl', '-f', f'http://localhost:{port}/health'],
                        'interval': '30s',
                        'timeout': '10s',
                        'retries': 3
                    }
                }
            }
        }

        compose_path = service_dir / "docker-compose.yml"
        with open(compose_path, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False, indent=2)

    def _update_main_py(self, service_dir: Path, dry_run: bool) -> List[str]:
        """Update main.py to use the configuration manager."""
        changes = []
        main_path = service_dir / "main.py"

        if not main_path.exists():
            changes.append("Create main.py with configuration manager integration")
            if not dry_run:
                self._create_standard_main_py(service_dir)
            return changes

        # Read the main.py file
        try:
            with open(main_path, 'r') as f:
                content = f.read()
        except Exception as e:
            changes.append(f"Could not read main.py: {e}")
            return changes

        # Check if already using configuration manager
        if 'ConfigurationManager' in content or 'load_service_config' in content:
            changes.append("Already using configuration manager")
            return changes

        # Update the imports and configuration loading
        updated_content = self._update_main_py_content(content, service_dir.name)

        if updated_content != content:
            changes.append("Update main.py to use centralized configuration manager")
            if not dry_run:
                with open(main_path, 'w') as f:
                    f.write(updated_content)

        return changes

    def _update_main_py_content(self, content: str, service_name: str) -> str:
        """Update main.py content to use configuration manager."""
        # Add import for configuration manager
        import_lines = []
        lines = content.split('\n')

        # Find the existing imports
        import_start = -1
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                if import_start == -1:
                    import_start = i
            elif import_start != -1 and not line.startswith('import ') and not line.startswith('from ') and line.strip():
                break

        # Insert configuration manager import
        if import_start != -1:
            config_import = "from services.shared.infrastructure.config import load_service_config"
            if config_import not in content:
                lines.insert(import_start, config_import)
                lines.insert(import_start + 1, "")

        # Find where configuration is loaded (look for hardcoded constants)
        config_section_start = -1
        for i, line in enumerate(lines):
            if 'SERVICE_NAME' in line or 'SERVICE_VERSION' in line or 'DEFAULT_API_PORT' in line:
                config_section_start = i
                break

        if config_section_start != -1:
            # Replace hardcoded configuration with config manager
            config_loading_code = f"""
# Load service configuration
config = load_service_config("{service_name}")

# Extract commonly used configuration values
SERVICE_NAME = config.service_name
SERVICE_VERSION = config.service_version
DEFAULT_API_PORT = config.server.port
"""
            # Find the end of the config section
            config_end = config_section_start
            for i in range(config_section_start, len(lines)):
                if not lines[i].strip() or lines[i].startswith('#'):
                    config_end = i
                elif lines[i].strip() and not lines[i].startswith(' ') and not lines[i].startswith('\t'):
                    break

            # Replace the config section
            lines[config_section_start:config_end + 1] = config_loading_code.split('\n')[1:-1]  # Remove first and last empty lines

        return '\n'.join(lines)

    def _create_standard_main_py(self, service_dir: Path):
        """Create a new main.py file with configuration manager integration."""
        service_name = service_dir.name
        port = self.standard_ports.get(service_name, 8080)

        main_content = f'''"""
{service_name.replace('-', ' ').title()} Service

FastAPI service with centralized configuration management.
"""

import uvicorn
from fastapi import FastAPI
from services.shared.infrastructure.config import load_service_config

# Load service configuration
config = load_service_config("{service_name}")

# Extract commonly used configuration values
SERVICE_NAME = config.service_name
SERVICE_VERSION = config.service_version
DEFAULT_API_PORT = config.server.port

# Create FastAPI application
app = FastAPI(
    title=SERVICE_NAME.replace('-', ' ').title(),
    version=SERVICE_VERSION,
    description=f"{SERVICE_NAME} service with centralized configuration"
)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {{
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "port": DEFAULT_API_PORT
    }}

@app.get("/")
async def root():
    """Root endpoint."""
    return {{"message": f"{SERVICE_NAME} service is running"}}

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        log_level=config.logging.level.lower()
    )
'''

        main_path = service_dir / "main.py"
        with open(main_path, 'w') as f:
            f.write(main_content)

    def _create_environment_configs(self, service_dir: Path, dry_run: bool) -> List[str]:
        """Create environment-specific configuration files."""
        changes = []
        service_name = service_dir.name

        # Create development config
        dev_config_path = service_dir / "config.development.yaml"
        if not dev_config_path.exists():
            changes.append("Create config.development.yaml")
            if not dry_run:
                dev_config = {
                    "server": {
                        "debug": True
                    },
                    "logging": {
                        "level": "DEBUG",
                        "console": True
                    }
                }
                with open(dev_config_path, 'w') as f:
                    yaml.dump(dev_config, f, default_flow_style=False, indent=2)

        # Create production config
        prod_config_path = service_dir / "config.production.yaml"
        if not prod_config_path.exists():
            changes.append("Create config.production.yaml")
            if not dry_run:
                prod_config = {
                    "server": {
                        "debug": False,
                        "workers": 4
                    },
                    "logging": {
                        "level": "INFO",
                        "console": False,
                        "file_path": f"/var/log/{service_name}.log"
                    },
                    "redis": {
                        "max_connections": 50
                    },
                    "security": {
                        "cors_origins": ["https://yourdomain.com"],
                        "rate_limiting": {
                            "enabled": True,
                            "requests_per_minute": 100
                        }
                    }
                }
                with open(prod_config_path, 'w') as f:
                    yaml.dump(prod_config, f, default_flow_style=False, indent=2)

        return changes

    def _check_configuration_issues(self, service_dir: Path) -> List[str]:
        """Check for configuration issues and return warnings."""
        warnings = []
        service_name = service_dir.name

        # Check for hardcoded values in config
        config_path = service_dir / "config.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}

                # Look for potential hardcoded values
                hardcoded_indicators = ['localhost', '127.0.0.1', 'changeme', 'your-secret-key']
                config_str = yaml.dump(config)

                for indicator in hardcoded_indicators:
                    if indicator in config_str.lower():
                        warnings.append(f"Potential hardcoded value found: {indicator}")

            except Exception as e:
                warnings.append(f"Could not parse config.yaml: {e}")

        # Check main.py for old-style configuration
        main_path = service_dir / "main.py"
        if main_path.exists():
            try:
                with open(main_path, 'r') as f:
                    content = f.read()

                if 'os.environ.get' in content and 'ConfigurationManager' not in content:
                    warnings.append("main.py still uses direct environment variable access instead of configuration manager")

            except Exception as e:
                warnings.append(f"Could not check main.py: {e}")

        return warnings


def main():
    """Main standardization function."""
    import argparse

    parser = argparse.ArgumentParser(description="Standardize configuration management across services")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    parser.add_argument("--service", help="Standardize only the specified service")
    parser.add_argument("--output", choices=['text', 'json'], default='text', help="Output format")

    args = parser.parse_args()

    standardizer = ConfigurationStandardizer()

    if args.service:
        # Standardize single service
        service_dir = Path(f"services/{args.service}")
        if not service_dir.exists():
            print(f"❌ Service {args.service} not found")
            return

        result = standardizer.standardize_service(service_dir, args.dry_run)

        if args.output == 'json':
            print(json.dumps({
                "service": result.service_name,
                "success": result.success,
                "changes": result.changes_made,
                "warnings": result.warnings,
                "errors": result.errors
            }, indent=2))
        else:
            print(f"📋 Standardization Result for {result.service_name}:")
            print(f"  Success: {result.success}")
            if result.changes_made:
                print("  Changes:")
                for change in result.changes_made:
                    print(f"    • {change}")
            if result.warnings:
                print("  Warnings:")
                for warning in result.warnings:
                    print(f"    ⚠️  {warning}")
            if result.errors:
                print("  Errors:")
                for error in result.errors:
                    print(f"    ❌ {error}")

    else:
        # Standardize all services
        results = standardizer.standardize_all_services(args.dry_run)

        if args.output == 'json':
            output = []
            for result in results:
                output.append({
                    "service": result.service_name,
                    "success": result.success,
                    "changes": result.changes_made,
                    "warnings": result.warnings,
                    "errors": result.errors
                })
            print(json.dumps(output, indent=2))
        else:
            successful = sum(1 for r in results if r.success)
            total_changes = sum(len(r.changes_made) for r in results)
            total_warnings = sum(len(r.warnings) for r in results)
            total_errors = sum(len(r.errors) for r in results)

            print("\n📊 Standardization Summary:")
            print(f"  Services processed: {len(results)}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {len(results) - successful}")
            print(f"  Total changes: {total_changes}")
            print(f"  Total warnings: {total_warnings}")
            print(f"  Total errors: {total_errors}")

            if not args.dry_run:
                print("\n✅ Standardization complete!")
            else:
                print("\n🔍 Dry run complete. Use --dry-run=false to apply changes.")


if __name__ == "__main__":
    main()
