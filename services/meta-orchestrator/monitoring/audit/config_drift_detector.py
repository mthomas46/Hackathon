#!/usr/bin/env python3
"""
Configuration Drift Detection for Meta-Orchestrator

Integrated configuration drift detection capabilities from scripts/safeguards/config_drift_detector.py
Provides comprehensive drift detection across Docker, YAML, and Pydantic configurations.
"""

import json
import yaml
import os
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging
from configparser import ConfigParser
import tomllib
import re
from collections import defaultdict
import sys

try:
    import jsonschema
    from jsonschema import validate, ValidationError, SchemaError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# JSON Schema definitions for configuration validation
SCHEMAS = {
    "docker-compose": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "version": {"type": ["string", "number"]},
            "services": {
                "type": "object",
                "patternProperties": {
                    "^[a-zA-Z][a-zA-Z0-9_-]*$": {
                        "oneOf": [
                            {"type": "object"},  # Normal service definition
                            {"type": ["string", "null"]}  # Can be a string or null for extends
                        ]
                    }
                }
            }
        },
        "additionalProperties": True
    },

    "service-config": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "server": {
                "type": "object",
                "properties": {
                    "host": {"type": ["string", "null"]},
                    "port": {"type": ["integer", "string"], "minimum": 1000, "maximum": 65535},
                    "debug": {"type": ["boolean", "string"]},
                    "workers": {"type": ["integer", "string"], "minimum": 1},
                    "timeout": {"type": ["integer", "string"], "minimum": 1},
                    "cors_origins": {"type": ["array", "string"], "items": {"type": "string"}}
                }
            },
            "logging": {
                "type": "object",
                "properties": {
                    "level": {"type": ["string", "null"]},  # Allow env vars like ${LOG_LEVEL:-INFO}
                    "format": {"type": ["string", "null"]},
                    "file_path": {"type": ["string", "null"]},
                    "max_size": {"type": ["integer", "string"]},
                    "backup_count": {"type": ["integer", "string"]},
                    "structured": {"type": ["boolean", "string"]},
                    "console": {"type": ["boolean", "string"]}
                }
            },
        },
        "additionalProperties": True
    },

    "health-config": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "health_check": {
                "type": "object",
                "properties": {
                    "endpoint": {"type": "string"},
                    "interval": {"type": ["integer", "string"]},
                    "timeout": {"type": ["integer", "string"]},
                    "retries": {"type": ["integer", "string"]},
                    "start_period": {"type": ["integer", "string"]}
                }
            }
        },
        "additionalProperties": True
    }
}


@dataclass
class ConfigFile:
    """Represents a configuration file."""
    path: Path
    content_hash: str
    last_modified: datetime
    format: str  # 'yaml', 'json', 'ini', 'toml', 'env'
    parsed_content: Optional[Dict[str, Any]] = None


@dataclass
class DockerContainer:
    """Represents a running Docker container."""
    name: str
    image: str
    ports: Dict[str, Any]
    env_vars: Dict[str, Any]
    volumes: List[str]
    status: str


@dataclass
class DockerComposeService:
    """Represents a service from docker-compose.yml."""
    name: str
    compose_file: Path
    config: Dict[str, Any]

    @property
    def path(self) -> Path:
        """Return the compose file path for compatibility."""
        return self.compose_file


@dataclass
class DriftIssue:
    """Represents a configuration drift issue."""
    issue_type: str  # 'docker_vs_compose', 'compose_vs_pydantic', 'docker_vs_pydantic'
    severity: str  # 'high', 'medium', 'low'
    description: str
    source_a: Union[ConfigFile, DockerContainer, DockerComposeService]
    source_b: Union[ConfigFile, DockerContainer, DockerComposeService]
    field_path: str
    value_a: Any
    value_b: Any
    can_auto_fix: bool = False
    suggested_fix: Optional[Dict[str, Any]] = None


@dataclass
class DriftDetectionResult:
    """Complete result of drift detection."""
    success: bool
    total_issues: int = 0
    high_severity: int = 0
    medium_severity: int = 0
    low_severity: int = 0
    issues: List[DriftIssue] = field(default_factory=list)
    scanned_files: int = 0
    scanned_containers: int = 0
    validation_errors: List[str] = field(default_factory=list)
    schema_validation_passed: bool = False


class ConfigurationDriftDetector:
    """
    Comprehensive configuration drift detection system.

    Detects drift between:
    - Docker containers vs docker-compose.yml
    - Docker containers vs Pydantic configurations
    - docker-compose.yml vs Pydantic configurations
    """

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.schemas_available = JSONSCHEMA_AVAILABLE

        # Files and directories to skip during scanning
        self.skip_patterns = {
            'dirs': {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 'htmlcov'},
            'files': {'audit-results', 'ci_reports', 'reports'},
            'extensions': {'.pyc', '.pyo', '.pyd', '.so', '.dylib', '.dll'},
            'infrastructure': {'infrastructure'}  # Skip Kubernetes manifests
        }

    def detect_all_drift(self, dev_only: bool = True) -> DriftDetectionResult:
        """
        Perform comprehensive drift detection across all configuration sources.

        Args:
            dev_only: If True, skip cross-environment comparisons

        Returns:
            Complete drift detection result
        """
        result = DriftDetectionResult(success=True)

        try:
            # Scan configuration files
            config_files = self.scan_configurations()
            result.scanned_files = len(config_files)

            # Get running containers
            containers = self.get_running_containers()
            result.scanned_containers = len(containers)

            # Detect various types of drift
            self._detect_docker_vs_compose_drift(containers, config_files, result)
            self._detect_docker_vs_pydantic_drift(containers, config_files, result)
            self._detect_compose_vs_pydantic_drift(config_files, result)

            if not dev_only:
                self._detect_cross_environment_drift(config_files, result)

            # Validate against schemas
            if self.schemas_available:
                self._validate_against_schemas(config_files, result)

            # Count issues by severity
            result.total_issues = len(result.issues)
            result.high_severity = len([i for i in result.issues if i.severity == 'high'])
            result.medium_severity = len([i for i in result.issues if i.severity == 'medium'])
            result.low_severity = len([i for i in result.issues if i.severity == 'low'])

        except Exception as e:
            result.success = False
            result.validation_errors.append(f"Drift detection failed: {str(e)}")
            logger.error(f"Drift detection failed: {e}", exc_info=True)

        return result

    def scan_configurations(self) -> Dict[str, ConfigFile]:
        """Scan and parse all configuration files."""
        config_files = {}

        # Scan for various config file types
        patterns = {
            'docker-compose': ['docker-compose*.yml', 'docker-compose*.yaml'],
            'service-config': ['services/*/config*.yml', 'services/*/config*.yaml'],
            'env-files': ['.env*', 'env*'],
            'json-configs': ['*.json'],
            'ini-configs': ['*.ini', '*.cfg'],
            'toml-configs': ['*.toml']
        }

        for config_type, file_patterns in patterns.items():
            for pattern in file_patterns:
                for file_path in self.workspace_path.rglob(pattern):
                    if self._should_skip_file(file_path):
                        continue

                    try:
                        config_file = self._parse_config_file(file_path)
                        if config_file:
                            key = f"{config_type}:{file_path.relative_to(self.workspace_path)}"
                            config_files[key] = config_file
                    except Exception as e:
                        logger.warning(f"Failed to parse {file_path}: {e}")

        return config_files

    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped during scanning."""
        # Skip directories
        if file_path.is_dir():
            return True

        # Skip by directory name
        for part in file_path.parts:
            if part in self.skip_patterns['dirs']:
                return True

        # Skip by filename
        if file_path.name in self.skip_patterns['files']:
            return True

        # Skip by extension
        if file_path.suffix in self.skip_patterns['extensions']:
            return True

        # Skip infrastructure files
        if any(skip_dir in file_path.parts for skip_dir in self.skip_patterns['infrastructure']):
            return True

        return False

    def _parse_config_file(self, file_path: Path) -> Optional[ConfigFile]:
        """Parse a configuration file."""
        try:
            content = file_path.read_text()
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)

            # Determine format
            if file_path.suffix in ['.yml', '.yaml']:
                parsed = yaml.safe_load(content)
                format_type = 'yaml'
            elif file_path.suffix == '.json':
                parsed = json.loads(content)
                format_type = 'json'
            elif file_path.name.startswith('.env') or file_path.name.startswith('env'):
                parsed = self._parse_env_file(content)
                format_type = 'env'
            elif file_path.suffix in ['.ini', '.cfg']:
                parsed = self._parse_ini_file(content)
                format_type = 'ini'
            elif file_path.suffix == '.toml':
                parsed = tomllib.loads(content)
                format_type = 'toml'
            else:
                return None

            return ConfigFile(
                path=file_path,
                content_hash=content_hash,
                last_modified=last_modified,
                format=format_type,
                parsed_content=parsed
            )

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return None

    def _parse_env_file(self, content: str) -> Dict[str, str]:
        """Parse .env file content."""
        env_vars = {}
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        return env_vars

    def _parse_ini_file(self, content: str) -> Dict[str, Any]:
        """Parse INI file content."""
        config = ConfigParser()
        config.read_string(content)
        result = {}
        for section in config.sections():
            result[section] = dict(config[section])
        return result

    def get_running_containers(self) -> Dict[str, DockerContainer]:
        """Get information about running Docker containers."""
        containers = {}

        try:
            # Get container information using docker inspect
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True, text=True, check=True
            )

            container_names = result.stdout.strip().split('\n') if result.stdout.strip() else []

            for name in container_names:
                if name:
                    try:
                        # Get detailed container info
                        inspect_result = subprocess.run(
                            ['docker', 'inspect', name],
                            capture_output=True, text=True, check=True
                        )

                        container_data = json.loads(inspect_result.stdout)[0]

                        # Extract relevant information
                        config = container_data.get('Config', {})
                        host_config = container_data.get('HostConfig', {})

                        containers[name] = DockerContainer(
                            name=name,
                            image=config.get('Image', ''),
                            ports=self._extract_ports(container_data),
                            env_vars=self._extract_env_vars(config.get('Env', [])),
                            volumes=host_config.get('Binds', []),
                            status=container_data.get('State', {}).get('Status', 'unknown')
                        )

                    except subprocess.CalledProcessError as e:
                        logger.warning(f"Failed to inspect container {name}: {e}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse container data for {name}: {e}")

        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to get running containers: {e}")

        return containers

    def _extract_ports(self, container_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract port mappings from container data."""
        ports = {}

        network_settings = container_data.get('NetworkSettings', {})
        if network_settings:
            port_bindings = network_settings.get('Ports', {})
            for container_port, host_bindings in port_bindings.items():
                if host_bindings:
                    for binding in host_bindings:
                        host_ip = binding.get('HostIp', '0.0.0.0')
                        host_port = binding.get('HostPort', '')
                        if host_port:
                            ports[container_port] = f"{host_ip}:{host_port}"

        return ports

    def _extract_env_vars(self, env_list: List[str]) -> Dict[str, str]:
        """Extract environment variables from container data."""
        env_vars = {}
        for env_item in env_list:
            if '=' in env_item:
                key, value = env_item.split('=', 1)
                env_vars[key] = value
        return env_vars

    def _detect_docker_vs_compose_drift(self, containers: Dict[str, DockerContainer],
                                      config_files: Dict[str, ConfigFile],
                                      result: DriftDetectionResult):
        """Detect drift between running containers and docker-compose configuration."""
        # Find docker-compose files
        compose_files = {k: v for k, v in config_files.items() if k.startswith('docker-compose:')}

        for compose_key, compose_file in compose_files.items():
            try:
                compose_config = compose_file.parsed_content
                if not compose_config or 'services' not in compose_config:
                    continue

                for service_name, service_config in compose_config['services'].items():
                    if isinstance(service_config, dict):
                        # Check if container is running
                        container_name = f"hackathon-{service_name}"
                        if container_name in containers:
                            container = containers[container_name]
                            self._compare_container_vs_compose(container, service_config, service_name, result)
                        else:
                            # Container not running - this could be an issue
                            result.issues.append(DriftIssue(
                                issue_type='docker_vs_compose',
                                severity='medium',
                                description=f"Service '{service_name}' defined in docker-compose but container not running",
                                source_a=compose_file,
                                source_b=None,
                                field_path=f"services.{service_name}",
                                value_a=service_config,
                                value_b=None
                            ))

            except Exception as e:
                logger.warning(f"Failed to analyze {compose_key}: {e}")

    def _compare_container_vs_compose(self, container: DockerContainer, compose_config: Dict[str, Any],
                                    service_name: str, result: DriftDetectionResult):
        """Compare a running container against its docker-compose configuration."""
        compose_service = DockerComposeService(
            name=service_name,
            compose_file=Path("docker-compose.dev.yml"),  # Placeholder
            config=compose_config
        )

        # Compare ports
        if 'ports' in compose_config:
            compose_ports = self._normalize_ports(compose_config['ports'])
            container_ports = self._normalize_ports(list(container.ports.values()))

            if set(compose_ports) != set(container_ports):
                result.issues.append(DriftIssue(
                    issue_type='docker_vs_compose',
                    severity='high',
                    description=f"Port mapping mismatch for service '{service_name}'",
                    source_a=container,
                    source_b=compose_service,
                    field_path='ports',
                    value_a=container_ports,
                    value_b=compose_ports
                ))

        # Compare environment variables
        if 'environment' in compose_config:
            compose_env = self._normalize_env_vars(compose_config['environment'])
            container_env = container.env_vars

            # Only check for missing environment variables (running containers may have additional env vars)
            missing_env = set(compose_env.keys()) - set(container_env.keys())
            if missing_env:
                result.issues.append(DriftIssue(
                    issue_type='docker_vs_compose',
                    severity='medium',
                    description=f"Missing environment variables in container '{service_name}': {missing_env}",
                    source_a=container,
                    source_b=compose_service,
                    field_path='environment',
                    value_a=container_env,
                    value_b=compose_env
                ))

        # Compare volumes
        if 'volumes' in compose_config:
            compose_volumes = self._normalize_volumes(compose_config['volumes'])
            container_volumes = self._normalize_volumes(container.volumes)

            if set(compose_volumes) != set(container_volumes):
                result.issues.append(DriftIssue(
                    issue_type='docker_vs_compose',
                    severity='medium',
                    description=f"Volume mount mismatch for service '{service_name}'",
                    source_a=container,
                    source_b=compose_service,
                    field_path='volumes',
                    value_a=container_volumes,
                    value_b=compose_volumes
                ))

    def _detect_docker_vs_pydantic_drift(self, containers: Dict[str, DockerContainer],
                                       config_files: Dict[str, ConfigFile],
                                       result: DriftDetectionResult):
        """Detect drift between running containers and Pydantic configurations."""
        service_configs = {k: v for k, v in config_files.items() if k.startswith('service-config:')}

        for container_name, container in containers.items():
            # Extract service name from container name (remove hackathon- prefix)
            if container_name.startswith('hackathon-'):
                service_name = container_name[10:]  # Remove 'hackathon-' prefix

                # Find corresponding service config
                config_key = f"service-config:services/{service_name}/config.yaml"
                if config_key in service_configs:
                    config_file = service_configs[config_key]
                    self._compare_container_vs_pydantic(container, config_file, service_name, result)

    def _compare_container_vs_pydantic(self, container: DockerContainer, config_file: ConfigFile,
                                    service_name: str, result: DriftDetectionResult):
        """Compare a running container against its Pydantic configuration."""
        if not config_file.parsed_content:
            return

        config_data = config_file.parsed_content

        # Compare ports if server config exists
        if 'server' in config_data:
            server_config = config_data['server']
            if 'port' in server_config:
                config_port = str(server_config['port'])
                # Check if any container port matches the config port
                container_ports = [port.split(':')[-1] for port in container.ports.values()]
                if config_port not in container_ports:
                    result.issues.append(DriftIssue(
                        issue_type='docker_vs_pydantic',
                        severity='medium',
                        description=f"Port mismatch between container and config for '{service_name}'",
                        source_a=container,
                        source_b=config_file,
                        field_path='server.port',
                        value_a=container_ports,
                        value_b=config_port
                    ))

        # Compare environment variables that should match config
        if 'environment' in config_data:
            config_env = config_data['environment']
            container_env = container.env_vars

            for env_key, config_value in config_env.items():
                if env_key in container_env:
                    container_value = container_env[env_key]
                    if str(config_value) != str(container_value):
                        result.issues.append(DriftIssue(
                            issue_type='docker_vs_pydantic',
                            severity='low',
                            description=f"Environment variable mismatch for '{env_key}' in '{service_name}'",
                            source_a=container,
                            source_b=config_file,
                            field_path=f'environment.{env_key}',
                            value_a=container_value,
                            value_b=config_value
                        ))

    def _detect_compose_vs_pydantic_drift(self, config_files: Dict[str, ConfigFile],
                                        result: DriftDetectionResult):
        """Detect drift between docker-compose and Pydantic configurations."""
        compose_files = {k: v for k, v in config_files.items() if k.startswith('docker-compose:')}
        service_configs = {k: v for k, v in config_files.items() if k.startswith('service-config:')}

        for compose_key, compose_file in compose_files.items():
            try:
                compose_config = compose_file.parsed_content
                if not compose_config or 'services' not in compose_config:
                    continue

                for service_name, service_config in compose_config['services'].items():
                    if isinstance(service_config, dict):
                        # Find corresponding service config
                        config_key = f"service-config:services/{service_name}/config.yaml"
                        if config_key in service_configs:
                            pydantic_config = service_configs[config_key]
                            self._compare_compose_vs_pydantic(service_config, pydantic_config, service_name, result)

            except Exception as e:
                logger.warning(f"Failed to compare compose vs pydantic for {compose_key}: {e}")

    def _compare_compose_vs_pydantic(self, compose_config: Dict[str, Any], pydantic_file: ConfigFile,
                                   service_name: str, result: DriftDetectionResult):
        """Compare docker-compose service config against Pydantic configuration."""
        if not pydantic_file.parsed_content:
            return

        pydantic_config = pydantic_file.parsed_content

        # Compare ports
        if 'ports' in compose_config and 'server' in pydantic_config:
            compose_ports = self._extract_container_ports(compose_config['ports'])
            pydantic_port = str(pydantic_config['server'].get('port', ''))

            if pydantic_port and pydantic_port not in compose_ports:
                result.issues.append(DriftIssue(
                    issue_type='compose_vs_pydantic',
                    severity='medium',
                    description=f"Port mismatch between compose and pydantic config for '{service_name}'",
                    source_a=pydantic_file,
                    source_b=DockerComposeService(service_name, Path("docker-compose.dev.yml"), compose_config),
                    field_path='server.port',
                    value_a=pydantic_port,
                    value_b=compose_ports
                ))

        # Compare environment variables
        if 'environment' in compose_config and 'environment' in pydantic_config:
            compose_env = self._normalize_env_vars(compose_config['environment'])
            pydantic_env = pydantic_config['environment']

            for env_key, pydantic_value in pydantic_env.items():
                if env_key in compose_env:
                    compose_value = compose_env[env_key]
                    if str(pydantic_value) != str(compose_value):
                        result.issues.append(DriftIssue(
                            issue_type='compose_vs_pydantic',
                            severity='low',
                            description=f"Environment variable mismatch for '{env_key}' in '{service_name}'",
                            source_a=pydantic_file,
                            source_b=DockerComposeService(service_name, Path("docker-compose.dev.yml"), compose_config),
                            field_path=f'environment.{env_key}',
                            value_a=pydantic_value,
                            value_b=compose_value
                        ))

    def _detect_cross_environment_drift(self, config_files: Dict[str, ConfigFile],
                                      result: DriftDetectionResult):
        """Detect drift between different environments (dev, staging, prod)."""
        # This is a simplified version - in a full implementation, you'd compare
        # configs across different environment files
        pass

    def _validate_against_schemas(self, config_files: Dict[str, ConfigFile],
                                result: DriftDetectionResult):
        """Validate configuration files against JSON schemas."""
        if not self.schemas_available:
            return

        result.schema_validation_passed = True

        for file_key, config_file in config_files.items():
            if not config_file.parsed_content:
                continue

            # Determine schema type
            schema_type = None
            if file_key.startswith('docker-compose:'):
                schema_type = 'docker-compose'
            elif file_key.startswith('service-config:'):
                schema_type = 'service-config'

            if schema_type and schema_type in SCHEMAS:
                try:
                    validate(config_file.parsed_content, SCHEMAS[schema_type])
                except (ValidationError, SchemaError) as e:
                    result.schema_validation_passed = False
                    result.issues.append(DriftIssue(
                        issue_type='schema_validation',
                        severity='low',
                        description=f"Schema validation failed for {file_key}: {e.message}",
                        source_a=config_file,
                        source_b=None,
                        field_path=e.absolute_path[0] if e.absolute_path else 'root',
                        value_a=e.instance,
                        value_b=None
                    ))

    # Helper methods for normalization
    def _normalize_ports(self, ports: List[Any]) -> List[str]:
        """Normalize port specifications to comparable format."""
        normalized = []
        for port in ports:
            if isinstance(port, str):
                # Handle "host:container" format
                if ':' in port:
                    parts = port.split(':')
                    normalized.append(f"{parts[0]}:{parts[1]}")
            elif isinstance(port, dict):
                # Handle dict format
                if 'published' in port and 'target' in port:
                    normalized.append(f"{port['published']}:{port['target']}")
        return sorted(normalized)

    def _normalize_env_vars(self, env_vars: Union[Dict, List]) -> Dict[str, str]:
        """Normalize environment variables to dict format."""
        if isinstance(env_vars, dict):
            return {k: str(v) for k, v in env_vars.items()}
        elif isinstance(env_vars, list):
            result = {}
            for item in env_vars:
                if isinstance(item, str) and '=' in item:
                    key, value = item.split('=', 1)
                    result[key] = value
                elif isinstance(item, dict):
                    result.update(item)
            return result
        return {}

    def _normalize_volumes(self, volumes: List[str]) -> List[str]:
        """Normalize volume specifications."""
        return sorted([str(v) for v in volumes])

    def _extract_container_ports(self, ports_config: List[Any]) -> List[str]:
        """Extract container ports from compose port configuration."""
        container_ports = []
        for port in ports_config:
            if isinstance(port, str) and ':' in port:
                container_ports.append(port.split(':')[-1])
            elif isinstance(port, dict) and 'target' in port:
                container_ports.append(str(port['target']))
        return container_ports
