#!/usr/bin/env python3
"""
Unified Docker Standardization for Meta-Orchestrator

Integrated unified Docker standardization capabilities from scripts/hardening/docker/unified_docker_standardizer.py
Provides comprehensive Docker configuration standardization and validation.
"""

import sys
import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from services.shared.infrastructure.config.docker_pydantic import (
        validate_docker_compose_file, validate_dockerfile, DockerComposeConfig,
        DockerService, PortMapping, VolumeMount, EnvironmentVariable,
        PYDANTIC_AVAILABLE
    )
except ImportError:
    PYDANTIC_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StandardizationMode(Enum):
    """Modes for Docker standardization operations."""
    VALIDATE_ONLY = "validate"
    DRY_RUN = "dry_run"
    APPLY_CHANGES = "apply"


@dataclass
class DockerStandardizationIssue:
    """Represents a Docker configuration issue that can be standardized."""
    service_name: Optional[str]
    issue_type: str  # 'port_mapping', 'volume_mount', 'environment_var', 'depends_on', etc.
    severity: str  # 'error', 'warning', 'info'
    description: str
    current_value: Any
    recommended_value: Any
    can_auto_fix: bool = False
    fix_applied: bool = False


@dataclass
class DockerStandardizationReport:
    """Complete report of Docker standardization operations."""
    files_processed: int = 0
    files_modified: int = 0
    issues_found: int = 0
    issues_fixed: int = 0
    validation_errors: int = 0
    pydantic_validation_passed: bool = False
    results: Dict[str, Any] = field(default_factory=dict)
    issues: List[DockerStandardizationIssue] = field(default_factory=list)


class UnifiedDockerStandardizer:
    """
    Unified Docker Standardization and Validation System.

    Combines multiple approaches:
    1. Pydantic validation for type safety and correctness
    2. Standardization for consistency and best practices
    3. Auto-fixing for common issues
    """

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.pydantic_available = PYDANTIC_AVAILABLE

        # Service port mappings from centralized registry
        self.service_ports = self._load_service_ports()

    def _load_service_ports(self) -> Dict[str, int]:
        """Load service port mappings from centralized registry."""
        return {
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
            'log-collector': 5080,
            'meta-orchestrator': 8080
        }

    def standardize_docker_configs(self, mode: StandardizationMode = StandardizationMode.VALIDATE_ONLY) -> DockerStandardizationReport:
        """
        Standardize all Docker configurations in the project.

        Args:
            mode: Standardization mode (validate, dry_run, apply)

        Returns:
            Comprehensive standardization report
        """
        report = DockerStandardizationReport()

        # Step 1: Validate with Pydantic first (if available)
        if self.pydantic_available:
            validation_report = self._validate_all_with_pydantic()
            report.pydantic_validation_passed = validation_report['passed']
            report.validation_errors = validation_report['errors']

        # Step 2: Standardize Docker Compose files
        compose_report = self._standardize_docker_compose_files(mode)
        report.files_processed += compose_report['files_processed']
        report.files_modified += compose_report['files_modified']
        report.issues_found += compose_report['issues_found']
        report.issues_fixed += compose_report['issues_fixed']
        report.issues.extend(compose_report['issues'])

        # Step 3: Validate Dockerfiles
        dockerfile_report = self._validate_dockerfiles()
        report.files_processed += dockerfile_report['files_processed']
        report.issues_found += dockerfile_report['issues_found']
        report.issues.extend(dockerfile_report['issues'])

        return report

    def _validate_all_with_pydantic(self) -> Dict[str, Any]:
        """Validate all Docker configurations using Pydantic."""
        validation_results = {
            'passed': True,
            'errors': 0,
            'details': {}
        }

        # Validate Docker Compose files
        compose_files = list(self.workspace_path.glob("**/docker-compose*.yml"))
        compose_files.extend(list(self.workspace_path.glob("**/docker-compose*.yaml")))

        for compose_file in compose_files:
            try:
                config = validate_docker_compose_file(compose_file)
                validation_results['details'][str(compose_file)] = {
                    'status': 'valid',
                    'services': len(config.services)
                }
            except Exception as e:
                validation_results['passed'] = False
                validation_results['errors'] += 1
                error_msg = str(e)

                # Extract more specific error information
                if "volumes." in error_msg and "Input should be a valid dictionary" in error_msg:
                    error_type = "Volume definition error"
                elif "depends_on" in error_msg and "Input should be a valid list" in error_msg:
                    error_type = "Dependency configuration error"
                elif "environment" in error_msg and "Input should be a valid list" in error_msg:
                    error_type = "Environment variable format error"
                elif "build" in error_msg and "Input should be a valid dictionary" in error_msg:
                    error_type = "Build configuration error"
                else:
                    error_type = "Docker Compose validation error"

                validation_results['details'][str(compose_file)] = {
                    'status': 'invalid',
                    'error': error_msg,
                    'error_type': error_type
                }

        return validation_results

    def _standardize_docker_compose_files(self, mode: StandardizationMode) -> Dict[str, Any]:
        """Standardize Docker Compose files with validation."""
        result = {
            'files_processed': 0,
            'files_modified': 0,
            'issues_found': 0,
            'issues_fixed': 0,
            'issues': []
        }

        # Process main Docker Compose files
        compose_files = [
            self.workspace_path / "docker-compose.dev.yml",
            self.workspace_path / "docker-compose.prod.yml",
            self.workspace_path / "docker-compose.yml"
        ]

        for compose_file in compose_files:
            if not compose_file.exists():
                continue

            result['files_processed'] += 1
            issues = self._standardize_single_compose_file(compose_file, mode)
            result['issues'].extend(issues)
            result['issues_found'] += len(issues)

            if mode == StandardizationMode.APPLY_CHANGES and issues:
                result['files_modified'] += 1
                result['issues_fixed'] += sum(1 for issue in issues if issue.fix_applied)

        return result

    def _standardize_single_compose_file(self, compose_file: Path, mode: StandardizationMode) -> List[DockerStandardizationIssue]:
        """Standardize a single Docker Compose file."""
        issues = []

        try:
            # Read current compose file
            with open(compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)

            if not compose_config or 'services' not in compose_config:
                return issues

            # Analyze and standardize each service
            for service_name, service_config in compose_config['services'].items():
                service_issues = self._standardize_service_config(service_name, service_config)
                issues.extend(service_issues)

            # Apply fixes if in apply mode
            if mode == StandardizationMode.APPLY_CHANGES and any(issue.can_auto_fix for issue in issues):
                fixes_applied = sum(1 for issue in issues if issue.can_auto_fix and issue.fix_applied)
                if fixes_applied > 0:
                    with open(compose_file, 'w') as f:
                        yaml.dump(compose_config, f, default_flow_style=False, indent=2, sort_keys=False)

        except Exception as e:
            logger.error(f"Error processing {compose_file}: {e}")

        return issues

    def _standardize_service_config(self, service_name: str, service_config: Dict[str, Any]) -> List[DockerStandardizationIssue]:
        """Standardize a single service configuration."""
        issues = []

        # Check port standardization
        if 'ports' in service_config and service_name in self.service_ports:
            expected_port = self.service_ports[service_name]
            ports = service_config['ports']

            # Check if expected port is mapped
            port_mapped = False
            for port in ports:
                if isinstance(port, str) and ':' in port:
                    internal_port = int(port.split(':')[-1])
                    if internal_port == expected_port:
                        port_mapped = True
                        break
                elif isinstance(port, dict) and 'target' in port:
                    if int(port['target']) == expected_port:
                        port_mapped = True
                        break

            if not port_mapped:
                issues.append(DockerStandardizationIssue(
                    service_name=service_name,
                    issue_type="port_mapping",
                    severity="warning",
                    description=f"Service should expose standardized port {expected_port}",
                    current_value=ports,
                    recommended_value=f"Add port mapping for {expected_port}",
                    can_auto_fix=False
                ))

        # Check environment variable format
        if 'environment' in service_config:
            env_vars = service_config['environment']
            if isinstance(env_vars, list):
                # Convert list format to dict for consistency
                new_env = {}
                for env_item in env_vars:
                    if isinstance(env_item, str) and '=' in env_item:
                        key, value = env_item.split('=', 1)
                        new_env[key] = value

                issues.append(DockerStandardizationIssue(
                    service_name=service_name,
                    issue_type="environment_format",
                    severity="info",
                    description="Environment variables should use dictionary format for consistency",
                    current_value=env_vars,
                    recommended_value=new_env,
                    can_auto_fix=True
                ))

        # Check volume mount format consistency
        if 'volumes' in service_config:
            volumes = service_config['volumes']
            for volume in volumes:
                if isinstance(volume, str):
                    # Check for common volume mount patterns
                    if volume.count(':') > 1:
                        issues.append(DockerStandardizationIssue(
                            service_name=service_name,
                            issue_type="volume_format",
                            severity="warning",
                            description="Volume mount may have incorrect format",
                            current_value=volume,
                            recommended_value="Check volume mount syntax",
                            can_auto_fix=False
                        ))

        # Check depends_on format
        if 'depends_on' in service_config:
            depends_on = service_config['depends_on']
            if isinstance(depends_on, str):
                issues.append(DockerStandardizationIssue(
                    service_name=service_name,
                    issue_type="dependency_format",
                    severity="warning",
                    description="depends_on should be a list, not a string",
                    current_value=depends_on,
                    recommended_value=[depends_on],
                    can_auto_fix=True
                ))

        # Check for health check configuration
        if 'healthcheck' not in service_config:
            issues.append(DockerStandardizationIssue(
                service_name=service_name,
                issue_type="missing_healthcheck",
                severity="info",
                description="Service should have a health check configured",
                current_value=None,
                recommended_value="Add health check configuration",
                can_auto_fix=False
            ))

        return issues

    def _validate_dockerfiles(self) -> Dict[str, Any]:
        """Validate Dockerfiles for best practices."""
        result = {
            'files_processed': 0,
            'issues_found': 0,
            'issues': []
        }

        # Find all Dockerfiles
        dockerfiles = list(self.workspace_path.glob("**/Dockerfile*"))

        for dockerfile in dockerfiles:
            result['files_processed'] += 1
            issues = self._validate_single_dockerfile(dockerfile)
            result['issues'].extend(issues)
            result['issues_found'] += len(issues)

        return result

    def _validate_single_dockerfile(self, dockerfile: Path) -> List[DockerStandardizationIssue]:
        """Validate a single Dockerfile."""
        issues = []

        try:
            with open(dockerfile, 'r') as f:
                content = f.read()

            # Check for common best practices
            service_name = dockerfile.parent.name

            # Check for USER directive (security)
            if 'USER' not in content:
                issues.append(DockerStandardizationIssue(
                    service_name=service_name,
                    issue_type="security_user",
                    severity="warning",
                    description="Dockerfile should specify a non-root USER",
                    current_value=None,
                    recommended_value="Add USER directive with non-root user",
                    can_auto_fix=False
                ))

            # Check for HEALTHCHECK directive
            if 'HEALTHCHECK' not in content:
                issues.append(DockerStandardizationIssue(
                    service_name=service_name,
                    issue_type="missing_healthcheck",
                    severity="info",
                    description="Dockerfile should include HEALTHCHECK directive",
                    current_value=None,
                    recommended_value="Add HEALTHCHECK directive",
                    can_auto_fix=False
                ))

            # Check for multi-stage builds with unused stages
            from_lines = re.findall(r'^FROM\s+.*\s+AS\s+(\w+)', content, re.MULTILINE | re.IGNORECASE)
            copy_lines = re.findall(r'COPY\s+--from=(\w+)', content, re.IGNORECASE)

            unused_stages = set(from_lines) - set(copy_lines)
            if unused_stages and len(from_lines) > 1:
                issues.append(DockerStandardizationIssue(
                    service_name=service_name,
                    issue_type="unused_build_stages",
                    severity="warning",
                    description=f"Dockerfile has unused build stages: {unused_stages}",
                    current_value=from_lines,
                    recommended_value="Remove or use unused build stages",
                    can_auto_fix=False
                ))

        except Exception as e:
            issues.append(DockerStandardizationIssue(
                service_name=dockerfile.parent.name,
                issue_type="dockerfile_error",
                severity="error",
                description=f"Could not validate Dockerfile: {e}",
                current_value=None,
                recommended_value="Fix Dockerfile syntax",
                can_auto_fix=False
            ))

        return issues
