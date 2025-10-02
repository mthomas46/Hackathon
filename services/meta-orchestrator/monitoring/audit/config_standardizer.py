#!/usr/bin/env python3
"""
Configuration Standardization for Meta-Orchestrator

Integrated configuration standardization capabilities from scripts/hardening/configuration_standardization.py
Provides comprehensive configuration standardization and consistency validation.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple, Optional
from dataclasses import dataclass, field
import re
import shutil
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class StandardizationMode(Enum):
    """Modes for configuration standardization."""
    VALIDATE_ONLY = "validate"
    DRY_RUN = "dry_run"
    APPLY_CHANGES = "apply"


@dataclass
class StandardizationIssue:
    """Represents a configuration standardization issue."""
    service_name: str
    issue_type: str  # 'port_mapping', 'env_var', 'config_format', etc.
    severity: str  # 'error', 'warning', 'info'
    description: str
    current_value: Any
    recommended_value: Any
    can_auto_fix: bool = False
    fix_applied: bool = False


@dataclass
class StandardizationResult:
    """Result of configuration standardization for a service."""
    service_name: str
    success: bool
    changes_made: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    issues: List[StandardizationIssue] = field(default_factory=list)


@dataclass
class ConfigStandardizationReport:
    """Complete configuration standardization report."""
    services_processed: int = 0
    services_standardized: int = 0
    total_issues: int = 0
    total_fixes_applied: int = 0
    results: List[StandardizationResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class ConfigurationStandardizer:
    """
    Standardizes configuration management across services.

    Provides comprehensive configuration standardization including:
    - Port mapping standardization
    - Environment variable naming consistency
    - Configuration file format validation
    - Docker Compose consistency
    - Service configuration validation
    """

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.services_dir = self.workspace_path / "services"

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
            "log-collector": 5080,
            "meta-orchestrator": 8080
        }

        # Environment variable standardization mappings
        self.env_var_mappings = {
            # Service URLs
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
            "META_ORCHESTRATOR_URL": "META_ORCHESTRATOR_URL",
            # Standardize common patterns
            "REDIS_API_HOST": "REDIS_API_HOST",
            "REDIS_API_PORT": "REDIS_API_PORT",
            "LOG_LEVEL": "LOG_LEVEL",
            "SERVER_API_HOST": "SERVER_API_HOST",
            "SERVER_API_PORT": "SERVER_API_PORT",
            "SERVICE_API_HOST": "SERVICE_API_HOST",
            "SERVICE_API_PORT": "SERVICE_API_PORT",
            "ENVIRONMENT": "ENVIRONMENT",
            "DEBUG": "DEBUG",
            "WORKSPACE_PATH": "WORKSPACE_PATH",
            "PYTHONPATH": "PYTHONPATH"
        }

    def standardize_all_services(self, mode: StandardizationMode = StandardizationMode.VALIDATE_ONLY) -> ConfigStandardizationReport:
        """
        Standardize configuration for all services.

        Args:
            mode: Standardization mode (validate, dry_run, apply)

        Returns:
            Complete standardization report
        """
        report = ConfigStandardizationReport()

        service_dirs = [d for d in self.services_dir.iterdir()
                       if d.is_dir() and not d.name.startswith('.') and d.name not in ['shared', '__pycache__']]

        for service_dir in service_dirs:
            result = self.standardize_service(service_dir.name, mode)
            report.results.append(result)
            report.services_processed += 1

            if result.success and result.changes_made:
                report.services_standardized += 1

            report.total_issues += len(result.issues)
            report.total_fixes_applied += sum(1 for issue in result.issues if issue.fix_applied)

        # Generate summary
        report.summary = self._generate_summary(report)

        return report

    def standardize_service(self, service_name: str, mode: StandardizationMode = StandardizationMode.VALIDATE_ONLY) -> StandardizationResult:
        """
        Standardize configuration for a single service.

        Args:
            service_name: Name of the service to standardize
            mode: Standardization mode

        Returns:
            Standardization result for the service
        """
        result = StandardizationResult(service_name=service_name, success=True)
        service_dir = self.services_dir / service_name

        if not service_dir.exists():
            result.success = False
            result.errors.append(f"Service directory not found: {service_dir}")
            return result

        try:
            # 1. Validate and standardize config.yaml
            config_issues = self._validate_config_yaml(service_dir, mode)
            result.issues.extend(config_issues)

            # 2. Validate docker-compose configuration
            docker_issues = self._validate_docker_compose_config(service_name, mode)
            result.issues.extend(docker_issues)

            # 3. Check environment variable consistency
            env_issues = self._validate_environment_variables(service_dir, mode)
            result.issues.extend(env_issues)

            # 4. Validate main.py configuration usage
            main_issues = self._validate_main_py_config(service_dir, mode)
            result.issues.extend(main_issues)

            # Generate changes made summary
            for issue in result.issues:
                if issue.fix_applied:
                    result.changes_made.append(f"Fixed {issue.issue_type}: {issue.description}")
                elif mode == StandardizationMode.VALIDATE_ONLY:
                    result.warnings.append(f"Would fix {issue.issue_type}: {issue.description}")

            # Count issues by severity
            for issue in result.issues:
                if issue.severity == 'error' and not issue.fix_applied:
                    result.errors.append(f"{issue.issue_type}: {issue.description}")
                elif issue.severity == 'warning':
                    result.warnings.append(f"{issue.issue_type}: {issue.description}")

        except Exception as e:
            result.success = False
            result.errors.append(f"Standardization failed: {str(e)}")

        return result

    def _validate_config_yaml(self, service_dir: Path, mode: StandardizationMode) -> List[StandardizationIssue]:
        """Validate and standardize the config.yaml file."""
        issues = []
        config_path = service_dir / "config.yaml"
        service_name = service_dir.name

        if not config_path.exists():
            issues.append(StandardizationIssue(
                service_name=service_name,
                issue_type="missing_config",
                severity="error",
                description="Missing config.yaml file",
                current_value=None,
                recommended_value="Create standardized config.yaml",
                can_auto_fix=True
            ))
            if mode == StandardizationMode.APPLY_CHANGES:
                self._create_standard_config_yaml(service_dir)
                issues[-1].fix_applied = True
            return issues

        # Read existing config
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            issues.append(StandardizationIssue(
                service_name=service_name,
                issue_type="invalid_yaml",
                severity="error",
                description=f"Invalid YAML in config.yaml: {e}",
                current_value=None,
                recommended_value="Fix YAML syntax",
                can_auto_fix=False
            ))
            return issues

        # Validate server section
        if 'server' not in config:
            config['server'] = {}

        # Check port standardization
        if service_name in self.standard_ports:
            expected_port = self.standard_ports[service_name]
            current_port = config.get('server', {}).get('port')

            if current_port != expected_port:
                issues.append(StandardizationIssue(
                    service_name=service_name,
                    issue_type="port_standardization",
                    severity="warning",
                    description=f"Port should be {expected_port} (standardized)",
                    current_value=current_port,
                    recommended_value=expected_port,
                    can_auto_fix=True
                ))
                if mode == StandardizationMode.APPLY_CHANGES:
                    config['server']['port'] = expected_port
                    with open(config_path, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False, indent=2)
                    issues[-1].fix_applied = True

        # Validate environment variable consistency
        if 'environment' in config:
            for env_key in config['environment']:
                if env_key not in self.env_var_mappings:
                    issues.append(StandardizationIssue(
                        service_name=service_name,
                        issue_type="env_var_standardization",
                        severity="info",
                        description=f"Environment variable '{env_key}' not in standardized mappings",
                        current_value=env_key,
                        recommended_value="Consider using standardized naming",
                        can_auto_fix=False
                    ))

        return issues

    def _validate_docker_compose_config(self, service_name: str, mode: StandardizationMode) -> List[StandardizationIssue]:
        """Validate docker-compose configuration for the service."""
        issues = []
        compose_path = self.workspace_path / "docker-compose.dev.yml"

        if not compose_path.exists():
            return issues

        try:
            with open(compose_path, 'r') as f:
                compose_config = yaml.safe_load(f)

            if 'services' not in compose_config or service_name not in compose_config['services']:
                return issues

            service_config = compose_config['services'][service_name]

            # Check port standardization
            if service_name in self.standard_ports and 'ports' in service_config:
                expected_port = self.standard_ports[service_name]
                ports = service_config['ports']

                # Look for the internal port mapping
                internal_ports = []
                for port in ports:
                    if isinstance(port, str) and ':' in port:
                        internal_port = int(port.split(':')[-1])
                        internal_ports.append(internal_port)
                    elif isinstance(port, dict) and 'target' in port:
                        internal_ports.append(int(port['target']))

                if expected_port not in internal_ports:
                    issues.append(StandardizationIssue(
                        service_name=service_name,
                        issue_type="docker_port_standardization",
                        severity="warning",
                        description=f"Docker port should include standardized port {expected_port}",
                        current_value=internal_ports,
                        recommended_value=expected_port,
                        can_auto_fix=False  # Would require updating docker-compose.yml
                    ))

        except Exception as e:
            issues.append(StandardizationIssue(
                service_name=service_name,
                issue_type="docker_compose_validation",
                severity="error",
                description=f"Failed to validate docker-compose config: {e}",
                current_value=None,
                recommended_value="Fix docker-compose.yml syntax",
                can_auto_fix=False
            ))

        return issues

    def _validate_environment_variables(self, service_dir: Path, mode: StandardizationMode) -> List[StandardizationIssue]:
        """Validate environment variable usage in the service."""
        issues = []
        service_name = service_dir.name

        # Check main.py for environment variable usage
        main_py = service_dir / "main.py"
        if main_py.exists():
            try:
                with open(main_py, 'r') as f:
                    content = f.read()

                # Look for os.environ.get patterns
                env_vars = re.findall(r'os\.environ\.get\(["\']([^"\']+)["\']', content)

                for env_var in env_vars:
                    if env_var not in self.env_var_mappings:
                        issues.append(StandardizationIssue(
                            service_name=service_name,
                            issue_type="env_var_usage",
                            severity="info",
                            description=f"Uses non-standardized environment variable '{env_var}'",
                            current_value=env_var,
                            recommended_value="Consider using standardized variable names",
                            can_auto_fix=False
                        ))

            except Exception as e:
                issues.append(StandardizationIssue(
                    service_name=service_name,
                    issue_type="main_py_analysis",
                    severity="warning",
                    description=f"Could not analyze main.py: {e}",
                    current_value=None,
                    recommended_value="Check main.py syntax",
                    can_auto_fix=False
                ))

        return issues

    def _validate_main_py_config(self, service_dir: Path, mode: StandardizationMode) -> List[StandardizationIssue]:
        """Validate main.py configuration usage."""
        issues = []
        service_name = service_dir.name
        main_py = service_dir / "main.py"

        if not main_py.exists():
            return issues

        try:
            with open(main_py, 'r') as f:
                content = f.read()

            # Check for configuration manager usage
            if 'from services.shared.infrastructure.config' not in content:
                issues.append(StandardizationIssue(
                    service_name=service_name,
                    issue_type="config_manager_usage",
                    severity="info",
                    description="Not using centralized configuration manager",
                    current_value="Direct config access",
                    recommended_value="Use services.shared.infrastructure.config",
                    can_auto_fix=False
                ))

            # Check for hardcoded values
            hardcoded_patterns = [
                (r'port\s*=\s*\d+', "Hardcoded port number"),
                (r'host\s*=\s*["\'][^"\']*["\']', "Hardcoded host value"),
                (r'debug\s*=\s*(True|False)', "Hardcoded debug flag")
            ]

            for pattern, description in hardcoded_patterns:
                if re.search(pattern, content):
                    issues.append(StandardizationIssue(
                        service_name=service_name,
                        issue_type="hardcoded_values",
                        severity="warning",
                        description=f"Contains {description.lower()}",
                        current_value="Hardcoded value found",
                        recommended_value="Use configuration values instead",
                        can_auto_fix=False
                    ))

        except Exception as e:
            issues.append(StandardizationIssue(
                service_name=service_name,
                issue_type="main_py_analysis",
                severity="warning",
                description=f"Could not analyze main.py: {e}",
                current_value=None,
                recommended_value="Check main.py syntax",
                can_auto_fix=False
            ))

        return issues

    def _create_standard_config_yaml(self, service_dir: Path):
        """Create a standardized config.yaml file."""
        service_name = service_dir.name
        config_path = service_dir / "config.yaml"

        # Create standard config structure
        config = {
            "server": {
                "host": "${SERVICE_API_HOST:-0.0.0.0}",
                "port": self.standard_ports.get(service_name, 8000),
                "debug": "${DEBUG:-false}",
                "workers": "${WORKERS:-1}"
            },
            "logging": {
                "level": "${LOG_LEVEL:-INFO}",
                "format": "json",
                "file_path": f"/app/logs/{service_name}.log",
                "max_size": "10MB",
                "backup_count": 5,
                "structured": True,
                "console": True
            },
            "environment": {
                "ENVIRONMENT": "${ENVIRONMENT:-development}",
                "SERVICE_NAME": service_name
            }
        }

        # Add service-specific configurations
        if service_name in ["orchestrator", "doc_store", "analysis-service", "llm-gateway"]:
            config["dependencies"] = {
                "redis": {
                    "host": "${REDIS_API_HOST:-redis}",
                    "port": "${REDIS_API_PORT:-6379}"
                }
            }

        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

    def _generate_summary(self, report: ConfigStandardizationReport) -> Dict[str, Any]:
        """Generate summary statistics."""
        summary = {
            "services_processed": report.services_processed,
            "services_standardized": report.services_standardized,
            "total_issues": report.total_issues,
            "fixes_applied": report.total_fixes_applied,
            "standardization_rate": report.services_standardized / report.services_processed if report.services_processed > 0 else 0
        }

        # Issue breakdown by type
        issue_types = {}
        for result in report.results:
            for issue in result.issues:
                issue_type = issue.issue_type
                if issue_type not in issue_types:
                    issue_types[issue_type] = 0
                issue_types[issue_type] += 1

        summary["issue_breakdown"] = issue_types

        return summary
