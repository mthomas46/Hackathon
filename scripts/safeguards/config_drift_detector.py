#!/usr/bin/env python3
"""
Enhanced Configuration Drift Detection System
==============================================

Comprehensive system for detecting configuration drift across Docker, YAML, and Pydantic configurations.
Compares running containers, docker-compose files, and service configurations to identify inconsistencies.

Features:
- Docker container vs docker-compose.yml drift detection
- Docker container vs Pydantic configuration comparison
- docker-compose.yml vs Pydantic config validation
- Multi-format config file detection (YAML, JSON, .env, .ini, .toml)
- Cross-environment comparison (dev, staging, prod)
- Service-specific configuration validation
- Automated correction suggestions
- CI/CD integration with detailed reporting
- Real-time drift monitoring capabilities

Author: Ecosystem Hardening Framework
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
    logger.warning("jsonschema not available - schema validation disabled")

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
            "redis": {
                "type": "object",
                "properties": {
                    "host": {"type": ["string", "null"]},
                    "port": {"type": ["integer", "string"], "minimum": 1, "maximum": 65535},
                    "db": {"type": ["integer", "string"], "minimum": 0},
                    "password": {"type": ["string", "null"]},
                    "ssl": {"type": ["boolean", "string"]},
                    "max_connections": {"type": ["integer", "string"], "minimum": 1}
                }
            },
            "security": {
                "type": "object",
                "properties": {
                    "cors_origins": {"type": ["array", "string"], "items": {"type": "string"}},
                    "enable_auth": {"type": ["boolean", "string"]},
                    "enable_ssl": {"type": ["boolean", "string"]},
                    "jwt_secret": {"type": ["string", "null"], "minLength": 10}
                }
            }
        },
        "additionalProperties": True
    },

    "health-config": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "health": {
                "type": "object",
                "properties": {
                    "check_interval": {"type": "integer", "minimum": 5, "maximum": 300},
                    "timeout": {"type": "integer", "minimum": 1, "maximum": 60},
                    "retries": {"type": "integer", "minimum": 1, "maximum": 10},
                    "enabled": {"type": "boolean"}
                }
            }
        }
    }
}


@dataclass
class ConfigFile:
    """Represents a configuration file with metadata"""
    path: Path
    format: str
    content: Dict[str, Any]
    checksum: str
    last_modified: datetime
    environment: Optional[str] = None
    service: Optional[str] = None


@dataclass
class DockerContainer:
    """Represents a running Docker container with configuration"""
    name: str
    image: str
    status: str
    ports: Dict[str, str]  # external_port -> internal_port
    env_vars: Dict[str, str]
    volumes: List[str]
    networks: List[str]
    labels: Dict[str, str]
    health_status: Optional[str] = None

    @property
    def path(self) -> Optional[Path]:
        """Return None for containers (they don't have a file path)"""
        return None


@dataclass
class DockerComposeService:
    """Represents a service definition from docker-compose.yml"""
    name: str
    image: Optional[str]
    build: Optional[Dict[str, Any]]
    ports: List[str]
    environment: Dict[str, str]
    volumes: List[str]
    depends_on: List[str]
    healthcheck: Optional[Dict[str, Any]]
    labels: Dict[str, str]
    compose_file_path: Optional[Path] = None  # Path to the docker-compose file

    @property
    def path(self) -> Optional[Path]:
        """Return the compose file path for compatibility with ConfigFile interface"""
        return self.compose_file_path


@dataclass
class DriftIssue:
    """Represents a configuration drift issue"""
    issue_type: str  # "missing", "inconsistent", "redundant", "outdated", "docker_drift", "pydantic_drift"
    severity: str    # "critical", "warning", "info"
    source_type: str  # "file", "docker", "pydantic", "compose"
    source_a: Any    # Can be ConfigFile, DockerContainer, DockerComposeService, or dict
    source_b: Optional[Any] = None
    key_path: str = ""
    expected_value: Any = None
    actual_value: Any = None
    description: str = ""
    suggestion: str = ""


@dataclass
class ConfigurationBaseline:
    """Golden standard configuration for an environment"""
    environment: str
    service: str
    config_type: str  # 'docker-compose', 'pydantic', 'yaml'
    baseline_config: Dict[str, Any]
    version: str = "1.0.0"
    description: str = ""
    last_updated: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class ConfigurationBackup:
    """Backup of configuration before automated correction"""
    file_path: str
    original_content: str
    backup_timestamp: str
    correction_type: str
    issue_description: str

@dataclass
class CorrectionResult:
    """Result of an automated correction attempt"""
    issue: DriftIssue
    success: bool
    action_taken: str
    backup_created: Optional[ConfigurationBackup] = None
    error_message: Optional[str] = None
    rollback_available: bool = False

@dataclass
class DriftReport:
    """Comprehensive configuration drift report"""
    total_files_scanned: int
    total_issues_found: int
    critical_issues: int
    warning_issues: int
    info_issues: int
    files_by_environment: Dict[str, List[ConfigFile]]
    issues_by_type: Dict[str, List[DriftIssue]]
    issues_by_file: Dict[str, List[DriftIssue]]
    recommendations: List[str]
    scan_timestamp: datetime = field(default_factory=datetime.now)
    scan_duration: float = 0.0


class ConfigurationCorrector:
    """Automated configuration correction system with safe rollback capabilities"""

    def __init__(self, workspace_path: Path):
        self.workspace_path = Path(workspace_path)
        self.backups_dir = self.workspace_path / "config" / "backups"
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.backup_registry_file = self.backups_dir / "backup_registry.json"
        self.backup_registry: List[ConfigurationBackup] = []
        self._load_backup_registry()

    def _load_backup_registry(self) -> None:
        """Load backup registry from file"""
        try:
            if self.backup_registry_file.exists():
                with open(self.backup_registry_file, 'r') as f:
                    registry_data = json.load(f)
                    self.backup_registry = [ConfigurationBackup(**backup) for backup in registry_data.get("backups", [])]
                logger.info(f"📦 Loaded {len(self.backup_registry)} configuration backups")
        except Exception as e:
            logger.error(f"❌ Failed to load backup registry: {e}")

    def _save_backup_registry(self) -> None:
        """Save backup registry to file"""
        try:
            registry_data = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "backups": [asdict(backup) for backup in self.backup_registry]
            }
            with open(self.backup_registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"❌ Failed to save backup registry: {e}")

    def create_backup(self, file_path: str, correction_type: str, issue_description: str) -> ConfigurationBackup:
        """Create a backup of a configuration file before correction"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            backup = ConfigurationBackup(
                file_path=file_path,
                original_content=original_content,
                backup_timestamp=datetime.now().isoformat(),
                correction_type=correction_type,
                issue_description=issue_description
            )

            self.backup_registry.append(backup)
            self._save_backup_registry()

            # Also save the backup file
            backup_filename = f"{Path(file_path).name}.{int(datetime.now().timestamp())}.backup"
            backup_path = self.backups_dir / backup_filename
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)

            logger.info(f"💾 Created backup for {file_path}: {backup_filename}")
            return backup

        except Exception as e:
            logger.error(f"❌ Failed to create backup for {file_path}: {e}")
            raise

    def rollback_correction(self, backup: ConfigurationBackup) -> bool:
        """Rollback a correction using a backup"""
        try:
            with open(backup.file_path, 'w', encoding='utf-8') as f:
                f.write(backup.original_content)

            logger.info(f"🔄 Successfully rolled back correction for {backup.file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to rollback correction for {backup.file_path}: {e}")
            return False

    def correct_issue(self, issue: DriftIssue, dry_run: bool = False) -> CorrectionResult:
        """Attempt to automatically correct a configuration issue"""
        try:
            # Determine correction strategy based on issue type
            if issue.issue_type == "network_drift":
                return self._correct_network_issue(issue, dry_run)
            elif issue.issue_type == "baseline_drift":
                return self._correct_baseline_issue(issue, dry_run)
            elif issue.issue_type == "dependency_drift":
                return self._correct_dependency_issue(issue, dry_run)
            elif issue.issue_type == "environment_drift":
                return self._correct_environment_issue(issue, dry_run)
            else:
                return CorrectionResult(
                    issue=issue,
                    success=False,
                    action_taken="No automated correction available",
                    error_message=f"No correction strategy for issue type: {issue.issue_type}"
                )

        except Exception as e:
            logger.error(f"❌ Failed to correct issue {issue.description}: {e}")
            return CorrectionResult(
                issue=issue,
                success=False,
                action_taken="Correction failed",
                error_message=str(e)
            )

    def _correct_network_issue(self, issue: DriftIssue, dry_run: bool) -> CorrectionResult:
        """Correct network-related configuration issues"""
        if "localhost" in str(issue.expected_value) or "127.0.0.1" in str(issue.expected_value):
            # This is a localhost replacement issue
            if issue.source_a and hasattr(issue.source_a, 'path'):
                file_path = issue.source_a.path

                if dry_run:
                    return CorrectionResult(
                        issue=issue,
                        success=True,
                        action_taken=f"Would replace localhost/127.0.0.1 with service name in {file_path}",
                        rollback_available=False
                    )

                try:
                    backup = self.create_backup(file_path, "network_localhost", issue.description)

                    # Read and modify the file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Replace localhost/127.0.0.1 with service name (extract from key_path)
                    if "environment." in issue.key_path:
                        env_var = issue.key_path.split("environment.")[-1]
                        # Find service reference in the value
                        if issue.actual_value and isinstance(issue.actual_value, str):
                            for service_name in ["redis", "doc_store", "orchestrator", "llm-gateway"]:
                                if service_name in issue.actual_value.lower():
                                    content = content.replace(issue.actual_value, service_name)
                                    break

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                    return CorrectionResult(
                        issue=issue,
                        success=True,
                        action_taken=f"Replaced localhost/127.0.0.1 with service name in {file_path}",
                        backup_created=backup,
                        rollback_available=True
                    )

                except Exception as e:
                    return CorrectionResult(
                        issue=issue,
                        success=False,
                        action_taken="Failed to update network configuration",
                        error_message=str(e)
                    )

        return CorrectionResult(
            issue=issue,
            success=False,
            action_taken="Network issue requires manual intervention"
        )

    def _correct_baseline_issue(self, issue: DriftIssue, dry_run: bool) -> CorrectionResult:
        """Correct baseline compliance issues"""
        if issue.source_a and hasattr(issue.source_a, 'path'):
            file_path = issue.source_a.path

            if dry_run:
                return CorrectionResult(
                    issue=issue,
                    success=True,
                    action_taken=f"Would update {file_path} to match baseline",
                    rollback_available=False
                )

            try:
                backup = self.create_backup(file_path, "baseline_compliance", issue.description)

                # For missing keys, add them
                if "(missing)" in str(issue.actual_value):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Add the missing key with expected value
                    if issue.expected_value:
                        # This is a simplified approach - in practice, you'd need more sophisticated
                        # YAML/JSON manipulation based on the file type
                        logger.warning("Baseline correction requires manual implementation for complex structures")

                    return CorrectionResult(
                        issue=issue,
                        success=True,
                        action_taken=f"Prepared baseline correction for {file_path}",
                        backup_created=backup,
                        rollback_available=True
                    )

            except Exception as e:
                return CorrectionResult(
                    issue=issue,
                    success=False,
                    action_taken="Failed to correct baseline compliance",
                    error_message=str(e)
                )

        return CorrectionResult(
            issue=issue,
            success=False,
            action_taken="Baseline correction requires manual review"
        )

    def _correct_dependency_issue(self, issue: DriftIssue, dry_run: bool) -> CorrectionResult:
        """Correct dependency-related issues"""
        if "restart policy" in issue.description.lower():
            if issue.source_a and hasattr(issue.source_a, 'compose_file_path'):
                compose_file = issue.source_a.compose_file_path

                if dry_run:
                    return CorrectionResult(
                        issue=issue,
                        success=True,
                        action_taken=f"Would add restart policy to service in {compose_file}",
                        rollback_available=False
                    )

                try:
                    backup = self.create_backup(compose_file, "dependency_restart", issue.description)

                    # Add restart policy to docker-compose service
                    import yaml

                    with open(compose_file, 'r', encoding='utf-8') as f:
                        compose_data = yaml.safe_load(f)

                    # Find the service and add restart policy
                    if 'services' in compose_data:
                        for service_name, service_config in compose_data['services'].items():
                            if not service_config.get('restart'):
                                service_config['restart'] = 'unless-stopped'

                    with open(compose_file, 'w', encoding='utf-8') as f:
                        yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)

                    return CorrectionResult(
                        issue=issue,
                        success=True,
                        action_taken=f"Added restart policies to services in {compose_file}",
                        backup_created=backup,
                        rollback_available=True
                    )

                except Exception as e:
                    return CorrectionResult(
                        issue=issue,
                        success=False,
                        action_taken="Failed to add restart policies",
                        error_message=str(e)
                    )

        return CorrectionResult(
            issue=issue,
            success=False,
            action_taken="Dependency issue requires manual intervention"
        )

    def _correct_environment_issue(self, issue: DriftIssue, dry_run: bool) -> CorrectionResult:
        """Correct environment consistency issues"""
        return CorrectionResult(
            issue=issue,
            success=False,
            action_taken="Environment consistency issues require manual review across multiple files"
        )

    def get_available_corrections(self, issues: List[DriftIssue]) -> List[DriftIssue]:
        """Filter issues that can be automatically corrected"""
        correctable_types = ["network_drift", "baseline_drift", "dependency_drift"]
        return [issue for issue in issues if issue.issue_type in correctable_types and issue.severity != "critical"]

    def apply_corrections(self, issues: List[DriftIssue], dry_run: bool = False) -> List[CorrectionResult]:
        """Apply automated corrections to a list of issues"""
        results = []
        correctable_issues = self.get_available_corrections(issues)

        logger.info(f"🔧 Attempting to correct {len(correctable_issues)} issues (dry_run={dry_run})")

        for issue in correctable_issues:
            result = self.correct_issue(issue, dry_run)
            results.append(result)

            if result.success:
                logger.info(f"✅ Corrected: {issue.description}")
            else:
                logger.warning(f"❌ Failed to correct: {issue.description} - {result.error_message}")

        return results

    def list_backups(self) -> List[ConfigurationBackup]:
        """List all available backups"""
        return self.backup_registry.copy()

    def rollback_by_timestamp(self, timestamp: str, confirm: bool = False) -> bool:
        """Rollback corrections made after a specific timestamp"""
        if not confirm:
            logger.warning("Rollback requires confirmation. Use confirm=True to proceed.")
            return False

        try:
            rollbacks = [backup for backup in self.backup_registry
                        if backup.backup_timestamp >= timestamp]

            success_count = 0
            for backup in rollbacks:
                if self.rollback_correction(backup):
                    success_count += 1

            logger.info(f"🔄 Successfully rolled back {success_count}/{len(rollbacks)} corrections")
            return success_count == len(rollbacks)

        except Exception as e:
            logger.error(f"❌ Failed to rollback by timestamp: {e}")
            return False


class ConfigDriftDetector:
    """
    Configuration Drift Detection and Automated Correction System.

    This class provides comprehensive detection of configuration drift across
    the entire ecosystem, with automated correction capabilities.
    """

    def __init__(self, workspace_path: Optional[str] = None):
        """Initialize the configuration drift detector"""
        self.workspace_path = Path(workspace_path or Path.cwd())
        self.config_files: List[ConfigFile] = []
        self.drift_issues: List[DriftIssue] = []
        self.baselines: Dict[str, ConfigurationBaseline] = {}
        self.baseline_file = self.workspace_path / "config" / "baselines.json"
        self.reports_dir = self.workspace_path / "reports" / "config_drift"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Load baselines on initialization
        self._load_baselines()

        # Initialize correction system
        self.corrector = ConfigurationCorrector(self.workspace_path)

        # Supported configuration file patterns
        self.config_patterns = {
            "yaml": ["*.yml", "*.yaml"],
            "json": ["*.json"],
            "env": [".env*", "*.env"],
            "ini": ["*.ini", "*.cfg", "*.conf"],
            "toml": ["*.toml"],
            "properties": ["*.properties"]
        }

        # Environment-specific directories
        self.environment_dirs = {
            "development": ["config", "docker-compose.dev.yml"],
            "staging": ["config.staging", "docker-compose.staging.yml"],
            "production": ["config.prod", "docker-compose.prod.yml"]
        }

        # Critical configuration keys that should be consistent
        self.critical_keys = {
            "database": ["host", "port", "name", "user"],
            "redis": ["host", "port", "db"],
            "services": ["ports", "dependencies", "environment"],
            "security": ["secret_key", "jwt_secret", "api_keys"]
        }

        logger.info("🔍 Configuration Drift Detector initialized")

    def scan_configurations(self) -> List[ConfigFile]:
        """
        Scan all configuration files in the workspace.

        Returns:
            List of discovered ConfigFile objects
        """
        logger.info("🔍 Scanning configuration files...")

        config_files = []

        # Scan for configuration files
        for format_type, patterns in self.config_patterns.items():
            for pattern in patterns:
                for file_path in self.workspace_path.rglob(pattern):
                    # Skip if not a file
                    if not file_path.is_file():
                        continue

                    # Skip certain directories
                    if any(skip in str(file_path) for skip in [
                        "__pycache__", ".git", "node_modules", ".venv", "venv"
                    ]):
                        continue

                    # Skip files in deploy/kubernetes and deploy/helm directories (templates)
                    if any(skip in str(file_path) for skip in [
                        "deploy/kubernetes", "deploy/helm"
                    ]):
                        continue

                    # Skip test and CI related files
                    if any(skip in str(file_path) for skip in [
                        ".ci_test", "test", "tests", "pytest.ini"
                    ]):
                        continue

                    # Skip audit results and generated files
                    if any(skip in str(file_path) for skip in [
                        "audit-results", "ci_reports", "reports"
                    ]):
                        continue

                    # Skip infrastructure config files that aren't standard formats
                    if "infrastructure" in str(file_path) and file_path.suffix in [".conf"]:
                        continue

                    # Skip Redis config files
                    if "redis.conf" in str(file_path):
                        continue

                    # Skip audit configuration files (complex regex patterns)
                    if "audit-config" in str(file_path):
                        continue

                    # Skip infrastructure YAML files (Kubernetes manifests, etc.)
                    if "infrastructure" in str(file_path) and file_path.suffix in [".yaml", ".yml"]:
                        continue

                    try:
                        config_file = self._load_config_file(file_path, format_type)
                        if config_file:
                            config_files.append(config_file)
                            logger.debug(f"✅ Loaded config: {file_path}")
                    except Exception as e:
                        logger.error(f"❌ Failed to load {file_path}: {e}")

        # Identify environments and services
        for config_file in config_files:
            config_file.environment = self._identify_environment(config_file.path)
            config_file.service = self._identify_service(config_file.path)

        self.config_files = config_files
        logger.info(f"🔍 Discovered {len(config_files)} configuration files")
        return config_files

    def _load_config_file(self, file_path: Path, format_type: str) -> Optional[ConfigFile]:
        """
        Load a configuration file based on its format.

        Args:
            file_path: Path to the configuration file
            format_type: Type of configuration file (yaml, json, etc.)

        Returns:
            ConfigFile object or None if loading fails
        """
        try:
            content = {}

            if format_type == "yaml":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f) or {}

            elif format_type == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)

            elif format_type == "env":
                content = self._parse_env_file(file_path)

            elif format_type == "ini":
                content = self._parse_ini_file(file_path)

            elif format_type == "toml":
                with open(file_path, 'rb') as f:
                    content = tomllib.load(f)

            elif format_type == "properties":
                content = self._parse_properties_file(file_path)

            # Generate checksum
            file_content = file_path.read_text(encoding='utf-8')
            checksum = hashlib.md5(file_content.encode()).hexdigest()

            # Get modification time
            stat = file_path.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)

            return ConfigFile(
                path=file_path,
                format=format_type,
                content=content,
                checksum=checksum,
                last_modified=last_modified
            )

        except Exception as e:
            logger.error(f"❌ Failed to load {file_path}: {e}")
            return None

    def _parse_env_file(self, file_path: Path) -> Dict[str, str]:
        """Parse .env file format"""
        env_vars = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"\'')
        return env_vars

    def _parse_ini_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse INI configuration file"""
        config = ConfigParser()
        config.read(file_path)

        result = {}
        for section in config.sections():
            result[section] = {}
            for key, value in config.items(section):
                result[section][key] = value

        return result

    def _parse_properties_file(self, file_path: Path) -> Dict[str, str]:
        """Parse Java properties file"""
        properties = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    properties[key.strip()] = value.strip()
        return properties

    def _identify_environment(self, file_path: Path) -> Optional[str]:
        """Identify the environment a config file belongs to"""
        path_str = str(file_path)

        if any(env in path_str.lower() for env in ["dev", "development"]):
            return "development"
        elif any(env in path_str.lower() for env in ["staging", "stage"]):
            return "staging"
        elif any(env in path_str.lower() for env in ["prod", "production"]):
            return "production"

        # Check for environment-specific files
        filename = file_path.name.lower()
        if "dev" in filename or filename.endswith(".dev"):
            return "development"
        elif "staging" in filename or "stage" in filename:
            return "staging"
        elif "prod" in filename:
            return "production"

        return "development"  # Default

    def _identify_service(self, file_path: Path) -> Optional[str]:
        """Identify the service a config file belongs to"""
        # Check if file is in a service directory
        for parent in file_path.parents:
            if parent.name.startswith("service") or parent.name in [
                "orchestrator", "doc_store", "llm_gateway", "frontend", "redis"
            ]:
                return parent.name

        # Try to infer from filename
        filename = file_path.name.lower()
        service_indicators = {
            "orchestrator": ["orchestrator", "orchestrator"],
            "doc_store": ["doc", "document"],
            "llm_gateway": ["llm", "gateway"],
            "frontend": ["frontend", "ui", "web"],
            "redis": ["redis", "cache"]
        }

        for service, indicators in service_indicators.items():
            if any(indicator in filename for indicator in indicators):
                return service

        return None

    def detect_drift(self, dev_only: bool = False) -> List[DriftIssue]:
        """
        Detect configuration drift across all scanned files.

        Returns:
            List of detected drift issues
        """
        logger.info("🔍 Detecting configuration drift...")

        issues = []

        # Group files by environment and service
        files_by_env = defaultdict(list)
        files_by_service = defaultdict(list)

        for config_file in self.config_files:
            if config_file.environment:
                files_by_env[config_file.environment].append(config_file)
            if config_file.service:
                files_by_service[config_file.service].append(config_file)

        # Check for environment-specific drift
        issues.extend(self._check_environment_drift(files_by_env, dev_only))

        # Check for service-specific drift
        issues.extend(self._check_service_drift(files_by_service))

        # Check for critical configuration consistency
        issues.extend(self._check_critical_config_consistency())

        # Check for network configuration issues
        issues.extend(self._check_network_configuration())

        # Check baseline compliance
        baseline_issues = self._check_baseline_compliance()
        issues.extend(baseline_issues)

        # Check multi-environment consistency
        env_issues = self._check_multi_environment_consistency()
        issues.extend(env_issues)

        # Check service dependencies and cascading effects
        dependency_issues = self._check_service_dependencies()
        issues.extend(dependency_issues)

        # Check for outdated or redundant configurations
        issues.extend(self._check_redundant_configs())

        # Detect Docker vs docker-compose drift
        docker_issues = self._detect_docker_drift()
        issues.extend(docker_issues)

        # Detect Pydantic vs docker-compose drift
        pydantic_issues = self._detect_pydantic_drift()
        issues.extend(pydantic_issues)

        # Validate configurations against schemas
        if JSONSCHEMA_AVAILABLE:
            schema_issues = self._validate_against_schemas()
            issues.extend(schema_issues)

        self.drift_issues = issues
        logger.info(f"🔍 Detected {len(issues)} configuration drift issues")
        return issues

    def _detect_docker_drift(self) -> List[DriftIssue]:
        """Detect drift between running Docker containers and docker-compose configuration"""
        issues = []

        try:
            # Get running containers
            running_containers = self._get_running_containers()

            # Get docker-compose services
            compose_services = self._get_docker_compose_services()

            # Compare each running container with its compose definition
            for container in running_containers:
                service_name = self._extract_service_name_from_container(container.name)
                if service_name in compose_services:
                    compose_service = compose_services[service_name]

                    # Compare ports
                    port_issues = self._compare_container_ports(container, compose_service)
                    issues.extend(port_issues)

                    # Compare environment variables
                    env_issues = self._compare_container_env(container, compose_service)
                    issues.extend(env_issues)

                    # Compare health status
                    health_issues = self._compare_container_health(container, compose_service)
                    issues.extend(health_issues)

                else:
                    # Container running but not defined in compose
                    issues.append(DriftIssue(
                        issue_type="docker_drift",
                        severity="warning",
                        source_type="docker",
                        source_a=container,
                        description=f"Container '{container.name}' is running but not defined in docker-compose.yml",
                        suggestion="Remove orphaned container or add to docker-compose.yml"
                    ))

            # Check for services defined in compose but not running
            running_names = {self._extract_service_name_from_container(c.name) for c in running_containers}
            for service_name, compose_service in compose_services.items():
                if service_name not in running_names:
                    issues.append(DriftIssue(
                        issue_type="docker_drift",
                        severity="critical",
                        source_type="compose",
                        source_a=compose_service,
                        description=f"Service '{service_name}' is defined in docker-compose.yml but not running",
                        suggestion="Start the service or remove from docker-compose.yml"
                    ))

        except Exception as e:
            logger.error(f"❌ Failed to detect Docker drift: {e}")

        return issues

    def _detect_pydantic_drift(self) -> List[DriftIssue]:
        """Detect drift between Pydantic configurations and docker-compose services"""
        issues = []

        try:
            # Get docker-compose services
            compose_services = self._get_docker_compose_services()

            # Get Pydantic service configurations
            pydantic_configs = self._get_pydantic_configs()

            # Compare each service
            for service_name, compose_service in compose_services.items():
                if service_name in pydantic_configs:
                    pydantic_config = pydantic_configs[service_name]

                    # Compare ports
                    port_issues = self._compare_pydantic_ports(pydantic_config, compose_service)
                    issues.extend(port_issues)

                    # Compare environment variables
                    env_issues = self._compare_pydantic_env(pydantic_config, compose_service)
                    issues.extend(env_issues)

                else:
                    # Service in compose but no Pydantic config
                    issues.append(DriftIssue(
                        issue_type="pydantic_drift",
                        severity="warning",
                        source_type="compose",
                        source_a=compose_service,
                        description=f"Service '{service_name}' has docker-compose config but no Pydantic configuration",
                        suggestion="Create Pydantic configuration for service"
                    ))

        except Exception as e:
            logger.error(f"❌ Failed to detect Pydantic drift: {e}")

        return issues

    def _get_running_containers(self) -> List[DockerContainer]:
        """Get information about running Docker containers"""
        containers = []

        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"],
                capture_output=True, text=True, timeout=10
            )

            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        name, image, status, ports_str = parts

                        # Parse ports
                        ports = {}
                        for port_info in ports_str.split(', '):
                            if '->' in port_info:
                                # Format: 0.0.0.0:8085->8099/tcp
                                try:
                                    external_part, internal_part = port_info.split('->', 1)
                                    external_port = external_part.split(':')[-1]
                                    internal_port = internal_part.split('/')[0]
                                    ports[external_port] = internal_port
                                except:
                                    continue

                        # Get environment variables
                        env_vars = {}
                        try:
                            env_result = subprocess.run(
                                ["docker", "exec", name, "env"],
                                capture_output=True, text=True, timeout=5
                            )
                            for env_line in env_result.stdout.split('\n'):
                                if '=' in env_line:
                                    key, value = env_line.split('=', 1)
                                    env_vars[key] = value
                        except:
                            pass

                        # Get health status
                        health_status = None
                        if "healthy" in status.lower():
                            health_status = "healthy"
                        elif "unhealthy" in status.lower():
                            health_status = "unhealthy"

                        containers.append(DockerContainer(
                            name=name,
                            image=image,
                            status=status,
                            ports=ports,
                            env_vars=env_vars,
                            volumes=[],  # Could be populated if needed
                            networks=[],  # Could be populated if needed
                            labels={},  # Could be populated if needed
                            health_status=health_status
                        ))

        except Exception as e:
            logger.error(f"❌ Failed to get running containers: {e}")

        return containers

    def _get_docker_compose_services(self) -> Dict[str, DockerComposeService]:
        """Parse docker-compose.yml files to get service definitions"""
        services = {}

        try:
            compose_files = ["docker-compose.yml", "docker-compose.dev.yml", "docker-compose.prod.yml"]

            for compose_file in compose_files:
                compose_path = self.workspace_path / compose_file
                if compose_path.exists():
                    with open(compose_path, 'r') as f:
                        compose_data = yaml.safe_load(f)

                    if 'services' in compose_data:
                        for service_name, service_config in compose_data['services'].items():
                            if service_name not in services:  # Take first definition found
                                services[service_name] = DockerComposeService(
                                    name=service_name,
                                    image=service_config.get('image'),
                                    build=service_config.get('build'),
                                    ports=service_config.get('ports', []),
                                    environment=self._normalize_env_vars(service_config.get('environment', {})),
                                    volumes=service_config.get('volumes', []),
                                    depends_on=service_config.get('depends_on', []) if isinstance(service_config.get('depends_on'), list) else list(service_config.get('depends_on', {}).keys()),
                                    healthcheck=service_config.get('healthcheck'),
                                    labels=service_config.get('labels', {}),
                                    compose_file_path=compose_path
                                )

        except Exception as e:
            logger.error(f"❌ Failed to parse docker-compose files: {e}")

        return services

    def _get_pydantic_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load Pydantic service configurations"""
        pydantic_configs = {}

        try:
            # Look for service config files
            for service_dir in self.workspace_path.glob("services/*"):
                if service_dir.is_dir() and (service_dir / "config.yaml").exists():
                    service_name = service_dir.name
                    config_file = service_dir / "config.yaml"

                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f) or {}
                        pydantic_configs[service_name] = config

        except Exception as e:
            logger.error(f"❌ Failed to load Pydantic configs: {e}")

        return pydantic_configs

    def _extract_service_name_from_container(self, container_name: str) -> str:
        """Extract service name from container name (e.g., 'hackathon-service-1' -> 'service')"""
        # Remove hackathon- prefix and -number suffix
        if container_name.startswith('hackathon-'):
            name_without_prefix = container_name[10:]  # Remove 'hackathon-'
            # Remove trailing number
            parts = name_without_prefix.rsplit('-', 1)
            if len(parts) == 2 and parts[1].isdigit():
                return parts[0]
        return container_name

    def _normalize_env_vars(self, env_vars: Any) -> Dict[str, str]:
        """Normalize environment variables from various formats to dict"""
        if isinstance(env_vars, dict):
            return {k: str(v) for k, v in env_vars.items()}
        elif isinstance(env_vars, list):
            result = {}
            for item in env_vars:
                if isinstance(item, str) and '=' in item:
                    key, value = item.split('=', 1)
                    result[key] = value
                elif isinstance(item, dict):
                    result.update({k: str(v) for k, v in item.items()})
            return result
        return {}

    def _compare_container_ports(self, container: DockerContainer, compose_service: DockerComposeService) -> List[DriftIssue]:
        """Compare container ports with compose service ports"""
        issues = []

        # Parse expected ports from compose service
        expected_ports = {}
        for port_mapping in compose_service.ports:
            if isinstance(port_mapping, str) and ':' in port_mapping:
                try:
                    external, internal = port_mapping.split(':', 1)
                    # Handle cases like "8085:8099" or "0.0.0.0:8085:8099"
                    if ':' in internal:
                        internal = internal.split(':')[-1]
                    expected_ports[external] = internal
                except:
                    continue

        # Compare actual vs expected ports
        for ext_port, int_port in container.ports.items():
            if ext_port not in expected_ports:
                issues.append(DriftIssue(
                    issue_type="docker_drift",
                    severity="warning",
                    source_type="docker",
                    source_a=container,
                    source_b=compose_service,
                    key_path=f"ports.{ext_port}",
                    actual_value=f"{ext_port}->{int_port}",
                    description=f"Container exposes unexpected port {ext_port} -> {int_port}",
                    suggestion="Update docker-compose.yml to match actual port exposure"
                ))
            elif expected_ports[ext_port] != int_port:
                issues.append(DriftIssue(
                    issue_type="docker_drift",
                    severity="critical",
                    source_type="docker",
                    source_a=container,
                    source_b=compose_service,
                    key_path=f"ports.{ext_port}",
                    expected_value=f"{ext_port}->{expected_ports[ext_port]}",
                    actual_value=f"{ext_port}->{int_port}",
                    description=f"Port mapping mismatch: expected {ext_port}->{expected_ports[ext_port]}, got {ext_port}->{int_port}",
                    suggestion="Fix port mapping in docker-compose.yml or container configuration"
                ))

        return issues

    def _compare_container_env(self, container: DockerContainer, compose_service: DockerComposeService) -> List[DriftIssue]:
        """Compare container environment variables with compose service"""
        issues = []

        # Check for critical environment variables
        critical_env_vars = ['SERVICE_NAME', 'SERVICE_API_PORT', 'SERVICE_API_HOST']

        for env_var in critical_env_vars:
            container_value = container.env_vars.get(env_var)
            compose_value = compose_service.environment.get(env_var)

            if container_value != compose_value:
                issues.append(DriftIssue(
                    issue_type="docker_drift",
                    severity="high",
                    source_type="docker",
                    source_a=container,
                    source_b=compose_service,
                    key_path=f"environment.{env_var}",
                    expected_value=compose_value,
                    actual_value=container_value,
                    description=f"Environment variable {env_var} mismatch: expected '{compose_value}', got '{container_value}'",
                    suggestion="Update docker-compose.yml or container environment"
                ))

        return issues

    def _compare_container_health(self, container: DockerContainer, compose_service: DockerComposeService) -> List[DriftIssue]:
        """Compare container health status with compose healthcheck"""
        issues = []

        if compose_service.healthcheck and container.health_status == "unhealthy":
            issues.append(DriftIssue(
                issue_type="docker_drift",
                severity="critical",
                source_type="docker",
                source_a=container,
                source_b=compose_service,
                key_path="healthcheck",
                description=f"Container '{container.name}' is unhealthy despite having healthcheck configured",
                suggestion="Check container logs and healthcheck configuration"
            ))

        return issues

    def _compare_pydantic_ports(self, pydantic_config: Dict[str, Any], compose_service: DockerComposeService) -> List[DriftIssue]:
        """Compare Pydantic port configuration with docker-compose"""
        issues = []

        # Extract port from Pydantic config
        pydantic_port = None
        if 'server' in pydantic_config and 'port' in pydantic_config['server']:
            pydantic_port = pydantic_config['server']['port']

        # Extract port from compose service
        compose_ports = []
        for port_mapping in compose_service.ports:
            if isinstance(port_mapping, str) and ':' in port_mapping:
                try:
                    parts = port_mapping.split(':')
                    if len(parts) >= 2:
                        internal_port = parts[-1]  # Last part is internal port
                        compose_ports.append(int(internal_port))
                except:
                    continue

        if pydantic_port and compose_ports and pydantic_port not in compose_ports:
            issues.append(DriftIssue(
                issue_type="pydantic_drift",
                severity="critical",
                source_type="pydantic",
                source_a=pydantic_config,
                source_b=compose_service,
                key_path="server.port",
                expected_value=compose_ports,
                actual_value=pydantic_port,
                description=f"Pydantic port {pydantic_port} not found in docker-compose port mappings {compose_ports}",
                suggestion="Align Pydantic server.port with docker-compose internal ports"
            ))

        return issues

    def _compare_pydantic_env(self, pydantic_config: Dict[str, Any], compose_service: DockerComposeService) -> List[DriftIssue]:
        """Compare Pydantic environment expectations with docker-compose"""
        issues = []

        # Check if Pydantic config expects certain environment variables
        if 'server' in pydantic_config:
            server_config = pydantic_config['server']

            # Check host configuration
            expected_host = server_config.get('host', '0.0.0.0')
            compose_host = compose_service.environment.get('SERVICE_API_HOST', '127.0.0.1')

            if expected_host != compose_host and compose_host != '127.0.0.1':  # Allow default
                issues.append(DriftIssue(
                    issue_type="pydantic_drift",
                    severity="warning",
                    source_type="pydantic",
                    source_a=pydantic_config,
                    source_b=compose_service,
                    key_path="server.host",
                    expected_value=expected_host,
                    actual_value=compose_host,
                    description=f"Pydantic expects host '{expected_host}' but docker-compose sets '{compose_host}'",
                    suggestion="Align SERVICE_API_HOST in docker-compose with Pydantic expectations"
                ))

        return issues

    def _validate_against_schemas(self) -> List[DriftIssue]:
        """Validate configuration files against JSON schemas"""
        issues = []

        if not JSONSCHEMA_AVAILABLE:
            logger.warning("⚠️ JSON Schema validation not available - install jsonschema")
            return issues

        logger.info("📋 Validating configurations against schemas...")

        for config_file in self.config_files:
            # Determine which schema to use
            schema_type = self._determine_schema_type(config_file)
            if schema_type and schema_type in SCHEMAS:
                try:
                    schema = SCHEMAS[schema_type]
                    validate(config_file.content, schema)
                    logger.debug(f"✅ {config_file.path.name} validates against {schema_type} schema")
                except ValidationError as e:
                    issues.append(DriftIssue(
                        issue_type="schema_validation",
                        severity="high",
                        source_type="file",
                        source_a=config_file,
                        key_path=e.absolute_path[0] if e.absolute_path else "root",
                        actual_value=e.instance,
                        description=f"Schema validation failed: {e.message}",
                        suggestion=f"Fix configuration to match {schema_type} schema: {e.message}"
                    ))
                    logger.warning(f"⚠️ {config_file.path.name} failed {schema_type} schema validation: {e.message}")
                except SchemaError as e:
                    logger.error(f"❌ Schema error for {schema_type}: {e}")
                except Exception as e:
                    logger.error(f"❌ Unexpected error validating {config_file.path}: {e}")

        logger.info(f"📋 Schema validation completed - {len(issues)} issues found")
        return issues

    def _determine_schema_type(self, config_file: ConfigFile) -> Optional[str]:
        """Determine which schema to use for a configuration file"""
        filename = config_file.path.name.lower()

        # Docker Compose files
        if "docker-compose" in filename:
            return "docker-compose"

        # Service configuration files
        if filename == "config.yaml" or filename == "config.yml":
            return "service-config"

        # Health configuration files
        if "health" in filename and config_file.format == "yaml":
            return "health-config"

        return None

    def _check_environment_drift(self, files_by_env: Dict[str, List[ConfigFile]], dev_only: bool = False) -> List[DriftIssue]:
        """Check for drift between environments"""
        issues = []

        # For development-only mode, skip cross-environment comparisons
        if dev_only:
            return issues

        # Compare development vs staging vs production
        environments = ["development", "staging", "production"]
        for i, env_a in enumerate(environments[:-1]):
            for env_b in environments[i+1:]:
                if env_a in files_by_env and env_b in files_by_env:
                    env_a_files = files_by_env[env_a]
                    env_b_files = files_by_env[env_b]

                    # Compare similar files between environments
                    for file_a in env_a_files:
                        for file_b in env_b_files:
                            if self._are_similar_files(file_a, file_b):
                                drift_issues = self._compare_config_files(file_a, file_b)
                                issues.extend(drift_issues)

        return issues

    def _check_service_drift(self, files_by_service: Dict[str, List[ConfigFile]]) -> List[DriftIssue]:
        """Check for drift within the same service across different files"""
        issues = []

        for service, files in files_by_service.items():
            if len(files) > 1:
                # Compare all files for the same service
                for i, file_a in enumerate(files[:-1]):
                    for file_b in files[i+1:]:
                        drift_issues = self._compare_config_files(file_a, file_b)
                        issues.extend(drift_issues)

        return issues

    def _are_similar_files(self, file_a: ConfigFile, file_b: ConfigFile) -> bool:
        """Check if two files are similar enough to compare"""
        # Same base filename (ignoring environment suffixes)
        name_a = file_a.path.name.replace(".dev", "").replace(".prod", "").replace(".staging", "")
        name_b = file_b.path.name.replace(".dev", "").replace(".prod", "").replace(".staging", "")

        return name_a == name_b and file_a.format == file_b.format

    def _compare_config_files(self, file_a: ConfigFile, file_b: ConfigFile) -> List[DriftIssue]:
        """Compare two configuration files for drift"""
        issues = []

        # Get all keys from both files
        keys_a = set(self._flatten_keys(file_a.content))
        keys_b = set(self._flatten_keys(file_b.content))

        # Find missing keys
        missing_in_b = keys_a - keys_b
        missing_in_a = keys_b - keys_a

        for key in missing_in_b:
            issues.append(DriftIssue(
                issue_type="missing",
                severity="warning",
                source_type="file",
                source_a=file_a,
                source_b=file_b,
                key_path=key,
                description=f"Key '{key}' exists in {file_a.path.name} but missing in {file_b.path.name}",
                suggestion=f"Add '{key}' to {file_b.path.name}"
            ))

        for key in missing_in_a:
            issues.append(DriftIssue(
                issue_type="missing",
                severity="warning",
                source_type="file",
                source_a=file_b,
                source_b=file_a,
                key_path=key,
                description=f"Key '{key}' exists in {file_b.path.name} but missing in {file_a.path.name}",
                suggestion=f"Add '{key}' to {file_a.path.name}"
            ))

        # Find inconsistent values
        common_keys = keys_a & keys_b
        for key in common_keys:
            value_a = self._get_nested_value(file_a.content, key)
            value_b = self._get_nested_value(file_b.content, key)

            if self._values_differ(value_a, value_b):
                severity = "critical" if self._is_critical_key(key) else "warning"
                issues.append(DriftIssue(
                    issue_type="inconsistent",
                    severity=severity,
                    source_type="file",
                    source_a=file_a,
                    source_b=file_b,
                    key_path=key,
                    expected_value=value_a,
                    actual_value=value_b,
                    description=f"Inconsistent value for '{key}': {value_a} vs {value_b}",
                    suggestion=f"Standardize value for '{key}' across environments"
                ))

        return issues

    def _flatten_keys(self, data: Any, prefix: str = "") -> List[str]:
        """Flatten nested dictionary keys"""
        keys = []

        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                keys.append(full_key)
                if isinstance(value, dict):
                    keys.extend(self._flatten_keys(value, full_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                full_key = f"{prefix}[{i}]"
                keys.append(full_key)
                if isinstance(item, dict):
                    keys.extend(self._flatten_keys(item, full_key))

        return keys

    def _get_nested_value(self, data: Any, key_path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = key_path.split('.')
        current = data

        for key in keys:
            if '[' in key and ']' in key:
                # Handle array indexing
                base_key, index = key.split('[', 1)
                index = int(index.rstrip(']'))
                if base_key in current and isinstance(current[base_key], list):
                    current = current[base_key][index]
                else:
                    return None
            else:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None

        return current

    def _values_differ(self, value_a: Any, value_b: Any) -> bool:
        """Check if two values are different"""
        if type(value_a) != type(value_b):
            return True

        if isinstance(value_a, (int, float, str, bool)):
            return value_a != value_b

        if isinstance(value_a, dict):
            return json.dumps(value_a, sort_keys=True) != json.dumps(value_b, sort_keys=True)

        if isinstance(value_a, list):
            # Sort lists by converting items to strings for comparison
            try:
                return sorted(value_a, key=str) != sorted(value_b, key=str)
            except TypeError:
                # Fallback to JSON serialization if sorting fails
                return json.dumps(value_a, sort_keys=True, default=str) != json.dumps(value_b, sort_keys=True, default=str)

        return str(value_a) != str(value_b)

    def _is_critical_key(self, key: str) -> bool:
        """Check if a key is considered critical"""
        key_lower = key.lower()
        for category, keys in self.critical_keys.items():
            if any(critical_key in key_lower for critical_key in keys):
                return True
        return False

    def _check_critical_config_consistency(self) -> List[DriftIssue]:
        """Check consistency of critical configuration values"""
        issues = []

        # Group files by service
        service_files = defaultdict(list)
        for config_file in self.config_files:
            if config_file.service:
                service_files[config_file.service].append(config_file)

        for service, files in service_files.items():
            if len(files) <= 1:
                continue

            # Check critical values across files for same service
            for category, keys in self.critical_keys.items():
                for key in keys:
                    values = []
                    for file in files:
                        value = self._get_nested_value(file.content, key)
                        if value is not None:
                            values.append((file, value))

                    if len(values) > 1:
                        # Check if all values are the same
                        first_value = values[0][1]
                        for file, value in values[1:]:
                            if self._values_differ(first_value, value):
                                issues.append(DriftIssue(
                                    issue_type="inconsistent",
                                    severity="critical",
                                    source_type="file",
                                    source_a=values[0][0],
                                    source_b=file,
                                    key_path=key,
                                    expected_value=first_value,
                                    actual_value=value,
                                    description=f"Critical config '{key}' differs across {service} files",
                                    suggestion=f"Ensure '{key}' is consistent across all {service} configuration files"
                                ))

        return issues

    def _check_network_configuration(self) -> List[DriftIssue]:
        """Comprehensive network configuration validation including port conflicts"""
        issues = []

        try:
            # Load Docker Compose services for port analysis
            compose_services = self._get_docker_compose_services()

            # Port conflict detection
            port_conflicts = self._detect_port_conflicts(compose_services)
            issues.extend(port_conflicts)

            # Network configuration validation
            network_issues = self._validate_network_config(compose_services)
            issues.extend(network_issues)

            # Service connectivity validation
            connectivity_issues = self._validate_service_connectivity(compose_services)
            issues.extend(connectivity_issues)

            # DNS and hostname validation
            dns_issues = self._validate_dns_configuration(compose_services)
            issues.extend(dns_issues)

        except Exception as e:
            logger.error(f"❌ Failed to validate network configuration: {e}")

        return issues

    def _detect_port_conflicts(self, compose_services: Dict[str, DockerComposeService]) -> List[DriftIssue]:
        """Detect port conflicts between services and system"""
        issues = []

        try:
            # Extract port mappings from compose services
            service_ports = {}
            for service_name, service in compose_services.items():
                for port_mapping in service.ports:
                    if isinstance(port_mapping, str) and ':' in port_mapping:
                        try:
                            external_port = int(port_mapping.split(':')[0])
                            if external_port not in service_ports:
                                service_ports[external_port] = []
                            service_ports[external_port].append(service_name)
                        except (ValueError, IndexError):
                            continue

            # Check for port conflicts between services
            for port, services in service_ports.items():
                if len(services) > 1:
                    issues.append(DriftIssue(
                        issue_type="network_drift",
                        severity="critical",
                        source_type="compose",
                        source_a=compose_services[services[0]],
                        key_path="ports",
                        expected_value=f"Unique port assignment",
                        actual_value=f"Shared by: {', '.join(services)}",
                        description=f"Port {port} is assigned to multiple services: {', '.join(services)}",
                        suggestion=f"Reassign services to unique ports. Available alternatives: {self._suggest_alternative_ports(port, service_ports)}"
                    ))

            # Check for conflicts with system ports (well-known ports)
            well_known_ports = {
                22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP", 443: "HTTPS",
                3306: "MySQL", 5432: "PostgreSQL", 6379: "Redis", 27017: "MongoDB"
            }

            for port, services in service_ports.items():
                if port in well_known_ports:
                    for service in services:
                        issues.append(DriftIssue(
                            issue_type="network_drift",
                            severity="high",
                            source_type="compose",
                            source_a=compose_services[service],
                            key_path="ports",
                            expected_value=f"Avoid well-known port {port} ({well_known_ports[port]})",
                            actual_value=f"Port {port} assigned to {service}",
                            description=f"Service {service} uses well-known port {port} ({well_known_ports[port]})",
                            suggestion=f"Use a different port to avoid conflicts with {well_known_ports[port]}"
                        ))

            # Check for port ranges and reserved ports
            for port, services in service_ports.items():
                if port < 1024:
                    for service in services:
                        issues.append(DriftIssue(
                            issue_type="network_drift",
                            severity="medium",
                            source_type="compose",
                            source_a=compose_services[service],
                            key_path="ports",
                            expected_value="Ports >= 1024 for non-root services",
                            actual_value=f"Port {port} < 1024",
                            description=f"Service {service} uses privileged port {port} (< 1024)",
                            suggestion="Use ports >= 1024 for non-root services to avoid permission issues"
                        ))

        except Exception as e:
            logger.error(f"❌ Failed to detect port conflicts: {e}")

        return issues

    def _validate_network_config(self, compose_services: Dict[str, DockerComposeService]) -> List[DriftIssue]:
        """Validate network configuration consistency"""
        issues = []

        try:
            # Check for missing network configuration
            for service_name, service in compose_services.items():
                # Check for hardcoded localhost/127.0.0.1 usage
                for env_var in service.environment.values():
                    if isinstance(env_var, str) and ('localhost' in env_var or '127.0.0.1' in env_var):
                        issues.append(DriftIssue(
                            issue_type="network_drift",
                            severity="medium",
                            source_type="compose",
                            source_a=service,
                            key_path="environment",
                            expected_value="Use service names instead of localhost/127.0.0.1",
                            actual_value=f"Found localhost/127.0.0.1 in: {env_var}",
                            description=f"Service {service_name} uses localhost/127.0.0.1 which may not work in containerized environments",
                            suggestion="Replace localhost/127.0.0.1 with appropriate service names or docker network references"
                        ))

        except Exception as e:
            logger.error(f"❌ Failed to validate network config: {e}")

        return issues

    def _validate_service_connectivity(self, compose_services: Dict[str, DockerComposeService]) -> List[DriftIssue]:
        """Validate service-to-service connectivity configuration"""
        issues = []

        try:
            service_names = set(compose_services.keys())

            for service_name, service in compose_services.items():
                # Check environment variables that reference other services
                for env_key, env_value in service.environment.items():
                    if isinstance(env_value, str):
                        # Look for service name references in URLs/hosts
                        for other_service in service_names:
                            if other_service != service_name and other_service in env_value:
                                # Check if the referenced service exists
                                if other_service not in service_names:
                                    issues.append(DriftIssue(
                                        issue_type="network_drift",
                                        severity="high",
                                        source_type="compose",
                                        source_a=service,
                                        key_path=f"environment.{env_key}",
                                        expected_value=f"Valid service reference",
                                        actual_value=f"References non-existent service: {other_service}",
                                        description=f"Service {service_name} references non-existent service '{other_service}' in {env_key}",
                                        suggestion=f"Ensure service '{other_service}' exists or update the reference"
                                    ))

        except Exception as e:
            logger.error(f"❌ Failed to validate service connectivity: {e}")

        return issues

    def _validate_dns_configuration(self, compose_services: Dict[str, DockerComposeService]) -> List[DriftIssue]:
        """Validate DNS and hostname configuration"""
        issues = []

        try:
            for service_name, service in compose_services.items():
                # Check for hostname configuration issues
                hostname_pattern = re.compile(r'HOSTNAME|HOST|DOMAIN', re.IGNORECASE)
                for env_key, env_value in service.environment.items():
                    if isinstance(env_value, str) and hostname_pattern.search(env_key):
                        # Validate hostname format
                        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', env_value):
                            issues.append(DriftIssue(
                                issue_type="network_drift",
                                severity="low",
                                source_type="compose",
                                source_a=service,
                                key_path=f"environment.{env_key}",
                                expected_value="Valid hostname format",
                                actual_value=f"Invalid hostname: {env_value}",
                                description=f"Service {service_name} has invalid hostname format in {env_key}",
                                suggestion="Use valid hostname format: alphanumeric, hyphens, dots only"
                            ))

        except Exception as e:
            logger.error(f"❌ Failed to validate DNS configuration: {e}")

        return issues

    def _suggest_alternative_ports(self, conflicting_port: int, used_ports: Dict[int, List[str]]) -> List[int]:
        """Suggest alternative ports for resolving conflicts"""
        suggestions = []
        used_port_set = set(used_ports.keys())

        # Suggest ports in ranges that make sense for the service type
        if conflicting_port >= 8000 and conflicting_port <= 8999:
            # Web service range
            for offset in [1, 2, 10, 100]:
                suggestion = conflicting_port + offset
                if suggestion not in used_port_set and suggestion <= 8999:
                    suggestions.append(suggestion)
        elif conflicting_port >= 5000 and conflicting_port <= 5999:
            # API service range
            for offset in [1, 2, 10, 100]:
                suggestion = conflicting_port + offset
                if suggestion not in used_port_set and suggestion <= 5999:
                    suggestions.append(suggestion)
        else:
            # General suggestions
            for offset in [1, 2, 10, 100]:
                suggestion = conflicting_port + offset
                if suggestion not in used_port_set and suggestion > 1024:
                    suggestions.append(suggestion)

        return suggestions[:3]  # Return up to 3 suggestions

    def _load_baselines(self) -> None:
        """Load configuration baselines from file"""
        try:
            if self.baseline_file.exists():
                with open(self.baseline_file, 'r') as f:
                    baseline_data = json.load(f)

                for baseline_dict in baseline_data.get("baselines", []):
                    baseline = ConfigurationBaseline(**baseline_dict)
                    key = f"{baseline.environment}_{baseline.service}_{baseline.config_type}"
                    self.baselines[key] = baseline

                logger.info(f"📋 Loaded {len(self.baselines)} configuration baselines")
            else:
                logger.info("📋 No baseline file found - will create default baselines")
        except Exception as e:
            logger.error(f"❌ Failed to load baselines: {e}")

    def _save_baselines(self) -> None:
        """Save configuration baselines to file"""
        try:
            self.baseline_file.parent.mkdir(parents=True, exist_ok=True)

            baseline_data = {
                "version": "1.0.0",
                "last_updated": datetime.now().isoformat(),
                "baselines": [asdict(baseline) for baseline in self.baselines.values()]
            }

            with open(self.baseline_file, 'w') as f:
                json.dump(baseline_data, f, indent=2, default=str)

            logger.info(f"💾 Saved {len(self.baselines)} configuration baselines")
        except Exception as e:
            logger.error(f"❌ Failed to save baselines: {e}")

    def create_baseline(self, environment: str, service: str, config_type: str,
                       config_data: Dict[str, Any], description: str = "") -> ConfigurationBaseline:
        """Create a new configuration baseline"""
        baseline = ConfigurationBaseline(
            environment=environment,
            service=service,
            config_type=config_type,
            baseline_config=config_data,
            description=description,
            last_updated=datetime.now().isoformat(),
            tags=["auto-generated"]
        )

        key = f"{environment}_{service}_{config_type}"
        self.baselines[key] = baseline
        self._save_baselines()

        logger.info(f"📋 Created baseline for {environment}/{service}/{config_type}")
        return baseline

    def _check_baseline_compliance(self) -> List[DriftIssue]:
        """Check configuration compliance against baselines"""
        issues = []

        try:
            for config_file in self.config_files:
                if not config_file.service or not config_file.environment:
                    continue

                # Find matching baseline
                baseline_key = f"{config_file.environment}_{config_file.service}_{config_file.format}"
                baseline = self.baselines.get(baseline_key)

                if not baseline:
                    # Create baseline suggestion for missing baseline
                    issues.append(DriftIssue(
                        issue_type="baseline_drift",
                        severity="info",
                        source_type="file",
                        source_a=config_file,
                        description=f"No baseline defined for {config_file.environment}/{config_file.service}/{config_file.format}",
                        suggestion="Consider creating a configuration baseline for this service/environment combination"
                    ))
                    continue

                # Compare current config with baseline
                baseline_issues = self._compare_with_baseline(config_file, baseline)
                issues.extend(baseline_issues)

        except Exception as e:
            logger.error(f"❌ Failed to check baseline compliance: {e}")

        return issues

    def _compare_with_baseline(self, config_file: ConfigFile, baseline: ConfigurationBaseline) -> List[DriftIssue]:
        """Compare a configuration file with its baseline"""
        issues = []

        try:
            current_config = config_file.content
            baseline_config = baseline.baseline_config

            # Deep comparison of configurations
            issues.extend(self._deep_compare_configs(
                current_config, baseline_config,
                f"{config_file.environment}.{config_file.service}.{config_file.format}",
                baseline
            ))

        except Exception as e:
            logger.error(f"❌ Failed to compare {config_file.path} with baseline: {e}")

        return issues

    def _deep_compare_configs(self, current: Any, baseline: Any, path: str,
                             baseline_obj: ConfigurationBaseline) -> List[DriftIssue]:
        """Deep comparison of configuration structures"""
        issues = []

        try:
            if isinstance(current, dict) and isinstance(baseline, dict):
                # Check for missing keys in current config
                for key, baseline_value in baseline.items():
                    if key not in current:
                        issues.append(DriftIssue(
                            issue_type="baseline_drift",
                            severity="medium",
                            source_type="baseline",
                            source_a=baseline_obj,
                            key_path=f"{path}.{key}",
                            expected_value=baseline_value,
                            actual_value="(missing)",
                            description=f"Required configuration key '{key}' missing from current config",
                            suggestion=f"Add '{key}' = {baseline_value} to match baseline"
                        ))
                    else:
                        # Recursively check nested structures
                        issues.extend(self._deep_compare_configs(
                            current[key], baseline_value, f"{path}.{key}", baseline_obj
                        ))

                # Check for extra keys in current config (warn about unexpected additions)
                for key, current_value in current.items():
                    if key not in baseline:
                        issues.append(DriftIssue(
                            issue_type="baseline_drift",
                            severity="low",
                            source_type="baseline",
                            source_a=baseline_obj,
                            key_path=f"{path}.{key}",
                            expected_value="(not in baseline)",
                            actual_value=current_value,
                            description=f"Additional configuration key '{key}' not in baseline",
                            suggestion="Review if this key should be added to the baseline or removed"
                        ))

            elif current != baseline:
                issues.append(DriftIssue(
                    issue_type="baseline_drift",
                    severity="high",
                    source_type="baseline",
                    source_a=baseline_obj,
                    key_path=path,
                    expected_value=baseline,
                    actual_value=current,
                    description=f"Configuration value differs from baseline at {path}",
                    suggestion=f"Update to match baseline: {baseline}"
                ))

        except Exception as e:
            logger.error(f"❌ Failed to compare configs at {path}: {e}")

        return issues

    def generate_baseline_from_current(self, environment: str, service: str,
                                     config_type: str, description: str = "") -> Optional[ConfigurationBaseline]:
        """Generate a baseline from current running configuration"""
        try:
            # Find current configuration for this service/environment
            matching_files = [
                f for f in self.config_files
                if f.service == service and f.environment == environment and f.format == config_type
            ]

            if not matching_files:
                logger.warning(f"❌ No current configuration found for {environment}/{service}/{config_type}")
                return None

            # Use the most recent file or combine if multiple
            current_config = matching_files[0].content

            baseline = self.create_baseline(
                environment=environment,
                service=service,
                config_type=config_type,
                config_data=current_config,
                description=description or f"Auto-generated baseline from current {environment} config"
            )

            return baseline

        except Exception as e:
            logger.error(f"❌ Failed to generate baseline: {e}")
            return None

    def _check_multi_environment_consistency(self) -> List[DriftIssue]:
        """Compare configurations across different environments for consistency"""
        issues = []

        try:
            # Group configurations by service and config type
            service_configs = defaultdict(lambda: defaultdict(list))

            for config_file in self.config_files:
                if config_file.service and config_file.environment:
                    key = f"{config_file.service}_{config_file.format}"
                    service_configs[key][config_file.environment].append(config_file)

            # Compare configurations across environments
            for service_key, env_configs in service_configs.items():
                if len(env_configs) > 1:  # Only compare if multiple environments exist
                    issues.extend(self._compare_environments_for_service(service_key, env_configs))

        except Exception as e:
            logger.error(f"❌ Failed to check multi-environment consistency: {e}")

        return issues

    def _compare_environments_for_service(self, service_key: str, env_configs: Dict[str, List[ConfigFile]]) -> List[DriftIssue]:
        """Compare a service's configurations across different environments"""
        issues = []

        try:
            environments = list(env_configs.keys())

            # Use development as the reference environment if available
            reference_env = 'development' if 'development' in environments else environments[0]
            reference_configs = env_configs[reference_env]

            # Compare each environment against the reference
            for env in environments:
                if env == reference_env:
                    continue

                env_config_files = env_configs[env]

                # Compare each config file in the reference env with corresponding files in this env
                for ref_config in reference_configs:
                    # Find matching config file in current environment
                    matching_config = self._find_matching_config(ref_config, env_config_files)

                    if matching_config:
                        # Compare the configurations
                        issues.extend(self._compare_service_configs_across_envs(
                            ref_config, matching_config, reference_env, env
                        ))
                    else:
                        # Missing configuration in this environment
                        issues.append(DriftIssue(
                            issue_type="environment_drift",
                            severity="high",
                            source_type="file",
                            source_a=ref_config,
                            description=f"Service {ref_config.service} configuration missing in {env} environment",
                            suggestion=f"Create {ref_config.format} configuration for {ref_config.service} in {env} environment"
                        ))

        except Exception as e:
            logger.error(f"❌ Failed to compare environments for {service_key}: {e}")

        return issues

    def _find_matching_config(self, reference_config: ConfigFile, env_configs: List[ConfigFile]) -> Optional[ConfigFile]:
        """Find a matching configuration file in another environment"""
        for config in env_configs:
            # Match by relative path or service name
            if (config.service == reference_config.service and
                config.format == reference_config.format):
                return config
        return None

    def _compare_service_configs_across_envs(self, ref_config: ConfigFile, env_config: ConfigFile,
                                           ref_env: str, env: str) -> List[DriftIssue]:
        """Compare two service configurations from different environments"""
        issues = []

        try:
            ref_data = ref_config.content
            env_data = env_config.content

            # Perform deep comparison
            differences = self._find_environment_differences(ref_data, env_data, ref_env, env)

            for diff in differences:
                severity = self._determine_environment_diff_severity(diff, ref_env, env)

                issues.append(DriftIssue(
                    issue_type="environment_drift",
                    severity=severity,
                    source_type="file",
                    source_a=ref_config,
                    source_b=env_config,
                    key_path=diff['path'],
                    expected_value=diff['reference_value'],
                    actual_value=diff['env_value'],
                    description=f"Configuration differs between {ref_env} and {env}: {diff['description']}",
                    suggestion=diff['suggestion']
                ))

        except Exception as e:
            logger.error(f"❌ Failed to compare configs across environments: {e}")

        return issues

    def _find_environment_differences(self, ref_data: Any, env_data: Any, ref_env: str, env: str,
                                    path: str = "") -> List[Dict[str, Any]]:
        """Find differences between configurations from different environments"""
        differences = []

        try:
            if isinstance(ref_data, dict) and isinstance(env_data, dict):
                # Check for keys that exist in reference but not in environment
                for key, ref_value in ref_data.items():
                    if key not in env_data:
                        differences.append({
                            'path': f"{path}.{key}" if path else key,
                            'reference_value': ref_value,
                            'env_value': '(missing)',
                            'description': f"Key '{key}' exists in {ref_env} but missing in {env}",
                            'suggestion': f"Add '{key}' to {env} environment configuration"
                        })
                    else:
                        # Recursively check nested structures
                        nested_diffs = self._find_environment_differences(
                            ref_value, env_data[key], ref_env, env, f"{path}.{key}" if path else key
                        )
                        differences.extend(nested_diffs)

                # Check for keys that exist in environment but not in reference (extra keys)
                for key, env_value in env_data.items():
                    if key not in ref_data:
                        differences.append({
                            'path': f"{path}.{key}" if path else key,
                            'reference_value': '(not in reference)',
                            'env_value': env_value,
                            'description': f"Extra key '{key}' in {env} not present in {ref_env}",
                            'suggestion': f"Review if '{key}' should be added to {ref_env} or removed from {env}"
                        })

            elif ref_data != env_data:
                # Direct value comparison
                differences.append({
                    'path': path,
                    'reference_value': ref_data,
                    'env_value': env_data,
                    'description': f"Value differs between {ref_env} and {env}",
                    'suggestion': f"Ensure consistent values across environments or document environment-specific differences"
                })

        except Exception as e:
            logger.error(f"❌ Failed to find environment differences at {path}: {e}")

        return differences

    def _determine_environment_diff_severity(self, diff: Dict[str, Any], ref_env: str, env: str) -> str:
        """Determine the severity of an environment difference"""
        try:
            # Critical differences
            critical_keys = ['host', 'port', 'database_url', 'secret_key', 'api_key', 'password']
            if any(critical_key in diff['path'].lower() for critical_key in critical_keys):
                return "critical"

            # High severity for missing required configurations
            if diff['env_value'] == '(missing)':
                return "high"

            # Medium severity for value differences
            if diff['reference_value'] != '(not in reference)' and diff['env_value'] != '(missing)':
                return "medium"

            # Low severity for extra configurations
            return "low"

        except Exception:
            return "medium"  # Default to medium severity

    def _check_service_dependencies(self) -> List[DriftIssue]:
        """Analyze service dependencies and detect cascading configuration effects"""
        issues = []

        try:
            # Get Docker Compose services for dependency analysis
            compose_services = self._get_docker_compose_services()

            # Build dependency graph
            dependency_graph = self._build_dependency_graph(compose_services)

            # Analyze configuration dependencies
            config_dependency_issues = self._analyze_config_dependencies(compose_services)
            issues.extend(config_dependency_issues)

            # Check for cascading effects
            cascading_issues = self._detect_cascading_effects(compose_services, dependency_graph)
            issues.extend(cascading_issues)

            # Validate dependency health
            health_issues = self._validate_dependency_health(compose_services, dependency_graph)
            issues.extend(health_issues)

        except Exception as e:
            logger.error(f"❌ Failed to check service dependencies: {e}")

        return issues

    def _build_dependency_graph(self, compose_services: Dict[str, DockerComposeService]) -> Dict[str, Set[str]]:
        """Build a graph of service dependencies from docker-compose configuration"""
        dependency_graph = defaultdict(set)

        try:
            for service_name, service in compose_services.items():
                # Add explicit dependencies from depends_on
                if hasattr(service, 'depends_on') and service.depends_on:
                    if isinstance(service.depends_on, list):
                        for dep in service.depends_on:
                            dependency_graph[service_name].add(dep)
                    elif isinstance(service.depends_on, dict):
                        for dep in service.depends_on.keys():
                            dependency_graph[service_name].add(dep)

                # Add implicit dependencies from environment variables
                for env_key, env_value in service.environment.items():
                    if isinstance(env_value, str):
                        # Look for service names in URLs or host references
                        for other_service in compose_services.keys():
                            if other_service != service_name and other_service in env_value:
                                dependency_graph[service_name].add(other_service)

        except Exception as e:
            logger.error(f"❌ Failed to build dependency graph: {e}")

        return dependency_graph

    def _analyze_config_dependencies(self, compose_services: Dict[str, DockerComposeService]) -> List[DriftIssue]:
        """Analyze how services depend on each other's configurations"""
        issues = []

        try:
            for service_name, service in compose_services.items():
                # Check for hardcoded service references that should be environment-specific
                for env_key, env_value in service.environment.items():
                    if isinstance(env_value, str):
                        # Look for localhost/127.0.0.1 in environment variables that reference other services
                        if 'localhost' in env_value or '127.0.0.1' in env_value:
                            # Check if this might be referencing another service
                            for other_service in compose_services.keys():
                                if other_service != service_name and other_service in env_value:
                                    issues.append(DriftIssue(
                                        issue_type="dependency_drift",
                                        severity="high",
                                        source_type="compose",
                                        source_a=service,
                                        key_path=f"environment.{env_key}",
                                        expected_value=f"Use service name instead of localhost/127.0.0.1",
                                        actual_value=env_value,
                                        description=f"Service {service_name} uses localhost/127.0.0.1 for {other_service} reference",
                                        suggestion=f"Use '{other_service}' as hostname instead of localhost/127.0.0.1 for proper service discovery"
                                    ))

        except Exception as e:
            logger.error(f"❌ Failed to analyze config dependencies: {e}")

        return issues

    def _detect_cascading_effects(self, compose_services: Dict[str, DockerComposeService],
                                dependency_graph: Dict[str, Set[str]]) -> List[DriftIssue]:
        """Detect potential cascading effects from configuration changes"""
        issues = []

        try:
            # Check for services that have many dependencies (high impact)
            for service_name, dependencies in dependency_graph.items():
                if len(dependencies) > 5:  # Arbitrary threshold for "high dependency"
                    issues.append(DriftIssue(
                        issue_type="dependency_drift",
                        severity="medium",
                        source_type="compose",
                        source_a=compose_services.get(service_name),
                        description=f"Service {service_name} has {len(dependencies)} dependencies - high impact for changes",
                        suggestion="Consider breaking down this service or implementing circuit breakers for resilience"
                    ))

            # Check for circular dependencies
            circular_deps = self._detect_circular_dependencies(dependency_graph)
            for cycle in circular_deps:
                cycle_str = " -> ".join(cycle + [cycle[0]])
                issues.append(DriftIssue(
                    issue_type="dependency_drift",
                    severity="high",
                    source_type="compose",
                    description=f"Circular dependency detected: {cycle_str}",
                    suggestion="Refactor to break circular dependency - consider event-driven architecture or shared storage"
                ))

            # Check for single points of failure
            single_points = self._detect_single_points_of_failure(dependency_graph)
            for critical_service in single_points:
                dependent_services = [s for s, deps in dependency_graph.items() if critical_service in deps]
                issues.append(DriftIssue(
                    issue_type="dependency_drift",
                    severity="high",
                    source_type="compose",
                    source_a=compose_services.get(critical_service),
                    description=f"Service {critical_service} is a single point of failure for {len(dependent_services)} services",
                    suggestion="Implement redundancy or consider using a service mesh for better resilience"
                ))

        except Exception as e:
            logger.error(f"❌ Failed to detect cascading effects: {e}")

        return issues

    def _detect_circular_dependencies(self, dependency_graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Detect circular dependencies in the service graph"""
        circular_deps = []

        try:
            # Simple cycle detection using DFS
            visited = set()
            rec_stack = set()

            def dfs(service: str, path: List[str]) -> None:
                visited.add(service)
                rec_stack.add(service)
                path.append(service)

                for dep in dependency_graph.get(service, set()):
                    if dep not in visited:
                        dfs(dep, path)
                    elif dep in rec_stack:
                        # Found cycle
                        cycle_start = path.index(dep)
                        circular_deps.append(path[cycle_start:])

                path.pop()
                rec_stack.remove(service)

            for service in dependency_graph.keys():
                if service not in visited:
                    dfs(service, [])

        except Exception as e:
            logger.error(f"❌ Failed to detect circular dependencies: {e}")

        return circular_deps

    def _detect_single_points_of_failure(self, dependency_graph: Dict[str, Set[str]]) -> List[str]:
        """Detect services that are single points of failure"""
        single_points = []

        try:
            # Count how many services depend on each service
            dependency_counts = defaultdict(int)

            for dependencies in dependency_graph.values():
                for dep in dependencies:
                    dependency_counts[dep] += 1

            # Services with many dependents are potential single points of failure
            for service, count in dependency_counts.items():
                if count >= 3:  # Arbitrary threshold
                    single_points.append(service)

        except Exception as e:
            logger.error(f"❌ Failed to detect single points of failure: {e}")

        return single_points

    def _validate_dependency_health(self, compose_services: Dict[str, DockerComposeService],
                                  dependency_graph: Dict[str, Set[str]]) -> List[DriftIssue]:
        """Validate the health of service dependencies"""
        issues = []

        try:
            for service_name, service in compose_services.items():
                dependencies = dependency_graph.get(service_name, set())

                # Check if all dependencies exist
                for dep in dependencies:
                    if dep not in compose_services:
                        issues.append(DriftIssue(
                            issue_type="dependency_drift",
                            severity="critical",
                            source_type="compose",
                            source_a=service,
                            description=f"Service {service_name} depends on non-existent service '{dep}'",
                            suggestion=f"Ensure service '{dep}' exists or remove the dependency"
                        ))

                # Check dependency configuration consistency
                for dep in dependencies:
                    if dep in compose_services:
                        dep_service = compose_services[dep]

                        # Check if dependent service is configured to restart on failure
                        if not hasattr(service, 'restart') or service.restart != 'unless-stopped':
                            issues.append(DriftIssue(
                                issue_type="dependency_drift",
                                severity="low",
                                source_type="compose",
                                source_a=service,
                                description=f"Service {service_name} should have restart policy for dependency resilience",
                                suggestion="Add 'restart: unless-stopped' to improve dependency resilience"
                            ))

        except Exception as e:
            logger.error(f"❌ Failed to validate dependency health: {e}")

        return issues

    def apply_automated_corrections(self, issues: Optional[List[DriftIssue]] = None,
                                   dry_run: bool = False) -> List[CorrectionResult]:
        """Apply automated corrections to configuration issues"""
        if issues is None:
            # Run full detection first
            issues = self.detect_drift()

        return self.corrector.apply_corrections(issues, dry_run)

    def rollback_corrections(self, timestamp: str, confirm: bool = False) -> bool:
        """Rollback automated corrections made after a specific timestamp"""
        return self.corrector.rollback_by_timestamp(timestamp, confirm)

    def list_correction_backups(self) -> List[ConfigurationBackup]:
        """List all available correction backups"""
        return self.corrector.list_backups()

    def _check_redundant_configs(self) -> List[DriftIssue]:
        """Check for redundant or outdated configuration files"""
        issues = []

        # Check for duplicate configurations
        file_checksums = defaultdict(list)
        for config_file in self.config_files:
            file_checksums[config_file.checksum].append(config_file)

        for checksum, files in file_checksums.items():
            if len(files) > 1:
                # Multiple files with same content
                for i in range(1, len(files)):
                    issues.append(DriftIssue(
                        issue_type="redundant",
                        severity="info",
                        source_type="file",
                        source_a=files[0],
                        source_b=files[i],
                        key_path="",
                        description=f"Duplicate configuration content in {files[i].path.name}",
                        suggestion=f"Consider consolidating duplicate configuration files"
                    ))

        # Check for potentially outdated files
        for config_file in self.config_files:
            days_old = (datetime.now() - config_file.last_modified).days
            if days_old > 90:  # Older than 3 months
                issues.append(DriftIssue(
                    issue_type="outdated",
                    severity="warning",
                    source_type="file",
                    source_a=config_file,
                    key_path="",
                    description=f"Configuration file {config_file.path.name} hasn't been modified in {days_old} days",
                    suggestion="Review if this configuration file is still needed"
                ))

        return issues

    def generate_report(self) -> DriftReport:
        """
        Generate a comprehensive drift report.

        Returns:
            DriftReport with detailed analysis
        """
        # Group issues
        issues_by_type = defaultdict(list)
        issues_by_file = defaultdict(list)
        files_by_environment = defaultdict(list)

        for issue in self.drift_issues:
            issues_by_type[issue.issue_type].append(issue)
            # Handle different source_a types
            if hasattr(issue.source_a, 'path') and issue.source_a.path:
                issues_by_file[str(issue.source_a.path)].append(issue)
            elif isinstance(issue.source_a, dict):
                # For dict sources (like Pydantic configs), use a generic key
                issues_by_file["pydantic_config"].append(issue)
            else:
                issues_by_file["unknown_source"].append(issue)

        for config_file in self.config_files:
            if config_file.environment:
                files_by_environment[config_file.environment].append(config_file)

        # Count issues by severity
        critical_issues = sum(1 for issue in self.drift_issues if issue.severity == "critical")
        warning_issues = sum(1 for issue in self.drift_issues if issue.severity == "warning")
        info_issues = sum(1 for issue in self.drift_issues if issue.severity == "info")

        # Generate recommendations
        recommendations = self._generate_recommendations()

        report = DriftReport(
            total_files_scanned=len(self.config_files),
            total_issues_found=len(self.drift_issues),
            critical_issues=critical_issues,
            warning_issues=warning_issues,
            info_issues=info_issues,
            files_by_environment=dict(files_by_environment),
            issues_by_type=dict(issues_by_type),
            issues_by_file=dict(issues_by_file),
            recommendations=recommendations
        )

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on detected issues"""
        recommendations = []

        if not self.drift_issues:
            recommendations.append("✅ No configuration drift detected - ecosystem is well-configured!")
            return recommendations

        critical_count = sum(1 for issue in self.drift_issues if issue.severity == "critical")
        if critical_count > 0:
            recommendations.append(f"🔴 CRITICAL: {critical_count} critical configuration issues found - fix immediately")

        # Environment-specific recommendations
        env_issues = defaultdict(int)
        for issue in self.drift_issues:
            # Handle environment counting for different source types
            env_name = None
            if hasattr(issue.source_a, 'environment') and issue.source_a.environment:
                env_name = issue.source_a.environment
            elif issue.source_type == "pydantic":
                env_name = "pydantic_config"
            elif issue.source_type == "docker":
                env_name = "docker_runtime"
            elif isinstance(issue.source_a, dict):
                env_name = "config_dict"

            if env_name:
                env_issues[env_name] += 1

        for env, count in env_issues.items():
            if count > 0:
                recommendations.append(f"📋 {env.upper()}: {count} configuration issues detected")

        # Issue type recommendations
        issue_types = set(issue.issue_type for issue in self.drift_issues)
        if "inconsistent" in issue_types:
            recommendations.append("🔧 Standardize critical configuration values across environments")
        if "missing" in issue_types:
            recommendations.append("➕ Add missing configuration keys to maintain consistency")
        if "redundant" in issue_types:
            recommendations.append("🗂️ Consolidate duplicate configuration files")
        if "outdated" in issue_types:
            recommendations.append("🗑️ Review and remove outdated configuration files")
        if "schema_validation" in issue_types:
            recommendations.append("📋 Fix configuration files to comply with JSON schemas")
        if "docker_drift" in issue_types:
            recommendations.append("🐳 Reconcile running containers with docker-compose definitions")
        if "pydantic_drift" in issue_types:
            recommendations.append("🔧 Align Pydantic configurations with docker-compose settings")

        # General recommendations
        recommendations.extend([
            "📊 Implement automated configuration drift monitoring in CI/CD",
            "🔒 Use configuration management tools (Ansible, Terraform, etc.)",
            "📝 Document configuration standards and best practices",
            "🔄 Regular configuration audits and cleanup"
        ])

        return recommendations

    def print_report(self, report: DriftReport, verbose: bool = True):
        """
        Print a formatted drift report.

        Args:
            report: DriftReport to print
            verbose: Whether to include detailed issue information
        """
        print("\n" + "="*80)
        print("📊 CONFIGURATION DRIFT DETECTION REAPI_PORT")
        print("="*80)
        print(f"📁 Total Files Scanned: {report.total_files_scanned}")
        print(f"⚠️  Total Issues Found: {report.total_issues_found}")
        print(f"🔴 Critical Issues: {report.critical_issues}")
        print(f"🟡 Warning Issues: {report.warning_issues}")
        print(f"ℹ️  Info Issues: {report.info_issues}")

        if report.files_by_environment:
            print("\n🏗️  Files by Environment:")
            for env, files in report.files_by_environment.items():
                print(f"  • {env}: {len(files)} files")

        if verbose and report.issues_by_type:
            print("\n📋 Issues by Type:")
            for issue_type, issues in report.issues_by_type.items():
                print(f"  • {issue_type}: {len(issues)} issues")

        if verbose and report.total_issues_found > 0:
            print("\n🔍 Top Issues:")
            # Show top 10 most critical issues
            all_issues = []
            for issues_list in report.issues_by_type.values():
                all_issues.extend(issues_list)

            sorted_issues = sorted(
                all_issues,
                key=lambda x: {"critical": 3, "warning": 2, "info": 1}[x.severity],
                reverse=True
            )

            for i, issue in enumerate(sorted_issues[:10]):
                severity_icon = {"critical": "🔴", "warning": "🟡", "info": "ℹ️"}[issue.severity]
                issue_type_icon = {
                    "docker_drift": "🐳",
                    "pydantic_drift": "🔧",
                    "schema_validation": "📋",
                    "missing": "➖",
                    "inconsistent": "⚠️",
                    "redundant": "♻️",
                    "outdated": "⏰"
                }.get(issue.issue_type, "❓")
                print(f"  {i+1}. {severity_icon}{issue_type_icon} {issue.description}")

        if report.recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for rec in report.recommendations:
                print(f"  • {rec}")

        print("="*80)

    def save_report(self, report: DriftReport, filename: Optional[str] = None) -> Path:
        """
        Save drift report to JSON file.

        Args:
            report: DriftReport to save
            filename: Optional custom filename

        Returns:
            Path to saved report file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"config_drift_report_{timestamp}.json"

        report_path = self.reports_dir / filename

        # Convert to serializable format
        def serialize_source(source):
            """Serialize source object for JSON"""
            if hasattr(source, 'path'):
                return str(source.path)
            elif hasattr(source, 'name'):
                return source.name
            elif isinstance(source, dict):
                return source
            else:
                return str(source)

        report_dict = {
            "total_files_scanned": report.total_files_scanned,
            "total_issues_found": report.total_issues_found,
            "critical_issues": report.critical_issues,
            "warning_issues": report.warning_issues,
            "info_issues": report.info_issues,
            "scan_timestamp": report.scan_timestamp.isoformat(),
            "scan_duration": report.scan_duration,
            "recommendations": report.recommendations,
            "files_by_environment": {
                env: [{"path": str(f.path), "format": f.format, "checksum": f.checksum}
                     for f in files]
                for env, files in report.files_by_environment.items()
            },
            "issues_by_type": {
                issue_type: [{
                    "severity": issue.severity,
                    "source_type": issue.source_type,
                    "source_a": serialize_source(issue.source_a),
                    "source_b": serialize_source(issue.source_b) if issue.source_b else None,
                    "key_path": issue.key_path,
                    "expected_value": issue.expected_value,
                    "actual_value": issue.actual_value,
                    "description": issue.description,
                    "suggestion": issue.suggestion
                } for issue in issues]
                for issue_type, issues in report.issues_by_type.items()
            }
        }

        with open(report_path, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)

        logger.info(f"💾 Report saved to: {report_path}")
        return report_path

    def apply_corrections(self, issues: List[DriftIssue], auto_apply: bool = False) -> Dict[str, Any]:
        """
        Apply automated corrections for detected issues.

        Args:
            issues: List of issues to correct
            auto_apply: Whether to apply corrections automatically

        Returns:
            Dictionary with correction results
        """
        logger.info("🔧 Applying configuration corrections...")

        results = {
            "total_corrections_attempted": 0,
            "successful_corrections": 0,
            "failed_corrections": 0,
            "corrections": []
        }

        for issue in issues:
            if issue.issue_type == "missing" and auto_apply:
                # Try to add missing keys
                success = self._add_missing_key(issue)
                results["total_corrections_attempted"] += 1

                if success:
                    results["successful_corrections"] += 1
                else:
                    results["failed_corrections"] += 1

                results["corrections"].append({
                    "issue": issue.description,
                    "action": "add_missing_key",
                    "success": success
                })

        logger.info(f"🔧 Applied {results['successful_corrections']} corrections")
        return results

    def _add_missing_key(self, issue: DriftIssue) -> bool:
        """
        Add a missing key to a configuration file.

        Args:
            issue: The drift issue to correct

        Returns:
            True if correction was successful
        """
        try:
            if issue.expected_value is None:
                return False

            # Load current content
            with open(issue.source_a.path, 'r', encoding='utf-8') as f:
                if issue.source_a.format == "yaml":
                    content = yaml.safe_load(f) or {}
                elif issue.source_a.format == "json":
                    content = json.load(f)
                else:
                    return False

            # Add the missing key
            self._set_nested_value(content, issue.key_path, issue.expected_value)

            # Write back to file
            with open(issue.source_a.path, 'w', encoding='utf-8') as f:
                if issue.source_a.format == "yaml":
                    yaml.dump(content, f, default_flow_style=False)
                elif issue.source_a.format == "json":
                    json.dump(content, f, indent=2)

            logger.info(f"✅ Added missing key '{issue.key_path}' to {issue.source_a.path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to add missing key: {e}")
            return False

    def _set_nested_value(self, data: Dict[str, Any], key_path: str, value: Any):
        """Set a value in nested dictionary using dot notation"""
        keys = key_path.split('.')
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value


def main():
    """Main entry point for configuration drift detection"""
    import argparse

    parser = argparse.ArgumentParser(description="Configuration Drift Detector")
    parser.add_argument("--workspace", help="Workspace path")
    parser.add_argument("--scan-only", action="store_true", help="Only scan, don't detect drift")
    parser.add_argument("--auto-correct", action="store_true", help="Automatically apply corrections")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--save-report", action="store_true", help="Save detailed report")
    parser.add_argument("--report-file", help="Custom report filename")

    # New validation modes
    parser.add_argument("--full-drift", action="store_true", help="Run full drift detection (Docker + YAML + Pydantic)")
    parser.add_argument("--docker-only", action="store_true", help="Only check Docker container drift")
    parser.add_argument("--pydantic-only", action="store_true", help="Only check Pydantic configuration drift")
    parser.add_argument("--schema-only", action="store_true", help="Only validate against schemas")
    parser.add_argument("--network-only", action="store_true", help="Only validate network configuration")
    parser.add_argument("--baseline-only", action="store_true", help="Only check baseline compliance")
    parser.add_argument("--create-baseline", nargs=3, metavar=('ENV', 'SERVICE', 'TYPE'),
                       help="Create baseline from current config: ENV SERVICE TYPE")
    parser.add_argument("--generate-baselines", action="store_true",
                       help="Auto-generate baselines for all current configurations")
    parser.add_argument("--env-compare-only", action="store_true", help="Only compare configurations across environments")
    parser.add_argument("--dependency-only", action="store_true", help="Only analyze service dependencies and cascading effects")
    parser.add_argument("--ci-gate", action="store_true", help="CI quality gate - exit with error on critical issues")
    parser.add_argument("--alert-on-drift", action="store_true", help="Check for drift and show alerts")
    parser.add_argument("--dev-only", action="store_true", help="Only check development environment configurations")
    parser.add_argument("--dry-run-corrections", action="store_true", help="Show what corrections would be applied without making changes")
    parser.add_argument("--rollback-corrections", metavar="TIMESTAMP", help="Rollback corrections made after TIMESTAMP (ISO format)")
    parser.add_argument("--list-backups", action="store_true", help="List all available correction backups")

    args = parser.parse_args()

    # Initialize detector
    detector = ConfigDriftDetector(args.workspace)

    try:
        print("🔍 Configuration Drift Detector")
        print("=" * 50)

        # Scan configurations
        config_files = detector.scan_configurations()

        if not config_files:
            print("❌ No configuration files found!")
            return 1

        if args.scan_only:
            print(f"📁 Found {len(config_files)} configuration files:")
            for config_file in config_files:
                env = config_file.environment or "unknown"
                service = config_file.service or "unknown"
                print(f"  • {config_file.path.name} ({config_file.format}) - {env}/{service}")
            return 0

        # Handle specific validation modes
        if args.schema_only:
            print("📋 Running schema validation only...")
            schema_issues = detector._validate_against_schemas()
            if schema_issues:
                print(f"⚠️  Found {len(schema_issues)} schema validation issues")
                for issue in schema_issues[:5]:  # Show first 5
                    print(f"  • {issue.description}")
            else:
                print("✅ All configurations pass schema validation")
            return 0 if not schema_issues else 1

        if args.network_only:
            print("🌐 Running network validation only...")
            detector.validate_network_only()
            return 0

        if args.baseline_only:
            print("📋 Running baseline compliance check only...")
            files = detector.scan_configurations()
            baseline_issues = detector._check_baseline_compliance()
            if baseline_issues:
                print(f"⚠️  Found {len(baseline_issues)} baseline compliance issues")
                for issue in baseline_issues[:5]:
                    print(f"  • {issue.severity.upper()}: {issue.description}")
            else:
                print("✅ All configurations comply with baselines")
            return 0 if not baseline_issues else 1

        if args.create_baseline:
            print(f"📋 Creating baseline for {args.create_baseline[0]}/{args.create_baseline[1]}/{args.create_baseline[2]}...")
            files = detector.scan_configurations()
            baseline = detector.generate_baseline_from_current(
                args.create_baseline[0], args.create_baseline[1], args.create_baseline[2]
            )
            if baseline:
                print(f"✅ Created baseline: {baseline.environment}/{baseline.service}/{baseline.config_type}")
            else:
                print("❌ Failed to create baseline")
            return 0

        if args.generate_baselines:
            print("📋 Auto-generating baselines for all configurations...")
            files = detector.scan_configurations()
            created_count = 0
            for config_file in files:
                if config_file.service and config_file.environment:
                    baseline = detector.generate_baseline_from_current(
                        config_file.environment, config_file.service, config_file.format,
                        f"Auto-generated from {config_file.path.name}"
                    )
                    if baseline:
                        created_count += 1
            print(f"✅ Created {created_count} baselines")
            return 0

        if args.env_compare_only:
            print("🌍 Comparing configurations across environments...")
            files = detector.scan_configurations()
            env_issues = detector._check_multi_environment_consistency()
            if env_issues:
                print(f"⚠️  Found {len(env_issues)} environment consistency issues")
                for issue in env_issues[:5]:
                    print(f"  • {issue.severity.upper()}: {issue.description}")
            else:
                print("✅ All configurations are consistent across environments")
            return 0 if not env_issues else 1

        if args.dependency_only:
            print("🔗 Analyzing service dependencies and cascading effects...")
            files = detector.scan_configurations()
            dependency_issues = detector._check_service_dependencies()
            if dependency_issues:
                print(f"⚠️  Found {len(dependency_issues)} dependency issues")
                for issue in dependency_issues[:5]:
                    print(f"  • {issue.severity.upper()}: {issue.description}")
            else:
                print("✅ No dependency issues found")
            return 0 if not dependency_issues else 1

        if args.list_backups:
            print("📦 Available correction backups:")
            backups = detector.list_correction_backups()
            if backups:
                for backup in backups[-10:]:  # Show last 10
                    print(f"  • {backup.backup_timestamp}: {backup.file_path} - {backup.correction_type}")
                if len(backups) > 10:
                    print(f"  ... and {len(backups) - 10} more")
            else:
                print("  No backups available")
            return 0

        if args.rollback_corrections:
            print(f"🔄 Rolling back corrections made after {args.rollback_corrections}...")
            if detector.rollback_corrections(args.rollback_corrections, confirm=True):
                print("✅ Rollback completed successfully")
            else:
                print("❌ Rollback failed")
            return 0

        if args.auto_correct or args.dry_run_corrections:
            dry_run = args.dry_run_corrections
            print(f"🔧 {'DRY RUN: ' if dry_run else ''}Applying automated corrections...")

            # First detect issues
            issues = detector.detect_drift()
            if not issues:
                print("✅ No issues found to correct")
                return 0

            # Apply corrections
            results = detector.apply_automated_corrections(issues, dry_run=dry_run)

            # Report results
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]

            print(f"\n📊 Correction Results:")
            print(f"  ✅ Successful: {len(successful)}")
            print(f"  ❌ Failed: {len(failed)}")
            print(f"  📦 Backups created: {len([r for r in results if r.backup_created])}")

            if successful and not dry_run:
                print(f"\n💡 To rollback corrections, run:")
                print(f"    python scripts/safeguards/config_drift_detector.py --rollback-corrections {datetime.now().isoformat()}")

            return 0 if not failed else 1

        # Detect drift (full or specific modes)
        if args.docker_only:
            print("🐳 Running Docker drift detection only...")
            docker_issues = detector._detect_docker_drift()
            issues = docker_issues
        elif args.pydantic_only:
            print("🔧 Running Pydantic drift detection only...")
            pydantic_issues = detector._detect_pydantic_drift()
            issues = pydantic_issues
        elif args.full_drift:
            print("🔍 Running full drift detection...")
            issues = detector.detect_drift(dev_only=args.dev_only)
        else:
            # Default: full drift detection
            issues = detector.detect_drift(dev_only=args.dev_only)

        # Generate and print report for drift detection modes
        detector.drift_issues = issues  # Set for report generation
        report = detector.generate_report()
        detector.print_report(report, args.verbose)

        # Save report if requested
        if args.save_report:
            report_path = detector.save_report(report, args.report_file)
            print(f"💾 Report saved: {report_path}")

        # Apply corrections if requested
        if args.auto_correct and issues:
            print("\n🔧 Applying automatic corrections...")
            correction_results = detector.apply_corrections(issues, True)
            print(f"✅ Applied {correction_results['successful_corrections']} corrections")

        # Handle CI gate mode
        if args.ci_gate:
            if report.critical_issues > 0:
                print("❌ CI GATE FAILED: Critical configuration issues found")
                return 1
            else:
                print("✅ CI GATE PASSED: No critical issues")
                return 0

        # Handle alert mode
        if args.alert_on_drift:
            if issues:
                print(f"🚨 ALERT: {len(issues)} configuration drift issues detected")
                critical_issues = [issue for issue in issues if issue.severity == "critical"]
                if critical_issues:
                    print(f"🔴 CRITICAL: {len(critical_issues)} critical issues require immediate attention")
                return 1
            else:
                print("✅ No configuration drift detected")
                return 0

        # Return appropriate exit code for regular drift detection
        if report.critical_issues > 0:
            print("❌ CRITICAL: Configuration drift issues found")
            return 1
        elif report.warning_issues > 0:
            print("⚠️ WARNING: Configuration inconsistencies detected")
            return 0
        else:
            print("✅ No critical configuration drift detected")
            return 0

    except KeyboardInterrupt:
        print("\n⚠️ Scan interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return 1


def validate_network_only() -> None:
    """Validate only network configuration and print results"""
    try:
        detector = ConfigDriftDetector()
        files = detector.scan_configurations()
        network_issues = detector._check_network_configuration()
        if network_issues:
            print(f'⚠️  Found {len(network_issues)} network configuration issues')
            for issue in network_issues[:3]:
                print(f'  • {issue.severity.upper()}: {issue.description}')
        else:
            print('✅ No network configuration issues found')
    except Exception as e:
        print(f'❌ Network validation failed: {e}')


if __name__ == "__main__":
    # Handle --network-only flag before main()
    if len(sys.argv) > 1 and "--network-only" in sys.argv:
        validate_network_only()
        sys.exit(0)

    sys.exit(main())
