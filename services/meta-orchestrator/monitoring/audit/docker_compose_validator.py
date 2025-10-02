#!/usr/bin/env python3
"""
Docker Compose Validator for Meta-Orchestrator

Integrated Docker Compose validation capabilities from scripts/hardening/docker_compose_validator.py
Provides comprehensive validation of Docker Compose configurations for startup operations.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from services.shared.infrastructure.config.docker_pydantic import (
        validate_docker_compose_file, PYDANTIC_AVAILABLE
    )
except ImportError:
    PYDANTIC_AVAILABLE = False


@dataclass
class ValidationIssue:
    """Represents a Docker Compose validation issue."""
    service_name: Optional[str]
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    description: str
    can_auto_fix: bool = False
    suggested_fix: Optional[Dict[str, Any]] = None


@dataclass
class PortConflict:
    """Represents a port conflict issue."""
    port: str
    services: List[str]
    severity: str = "error"


@dataclass
class DockerComposeValidationResult:
    """Complete validation result for Docker Compose files."""
    success: bool
    services_count: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    port_conflicts: List[PortConflict] = field(default_factory=list)
    warnings: int = 0
    errors: int = 0
    validation_errors: List[str] = field(default_factory=list)


class DockerComposeValidator:
    """
    Docker Compose Validator for comprehensive startup validation.

    Validates Docker configurations specifically for docker-compose operations.
    Based on lessons learned from getting all services running together.
    """

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.pydantic_available = PYDANTIC_AVAILABLE

        # Services that import from services.shared
        self.services_that_import_shared = [
            'analysis-service', 'architecture-digitizer', 'bedrock-proxy', 'cli',
            'discovery-agent', 'doc_store', 'frontend', 'github-mcp', 'interpreter',
            'llm-gateway', 'memory-agent', 'mock-data-generator', 'orchestrator',
            'project-simulation', 'prompt_store', 'source-agent', 'summarizer-hub'
        ]

    def validate_for_startup(self, compose_file: str = "docker-compose.dev.yml") -> DockerComposeValidationResult:
        """
        Validate Docker Compose file specifically for startup operations.

        Args:
            compose_file: Path to docker-compose file to validate

        Returns:
            Complete validation result
        """
        result = DockerComposeValidationResult(success=True)

        if not self.pydantic_available:
            result.success = False
            result.validation_errors.append("Pydantic not available for Docker validation")
            return result

        compose_path = self.workspace_path / compose_file
        if not compose_path.exists():
            result.success = False
            result.validation_errors.append(f"Docker Compose file not found: {compose_file}")
            return result

        try:
            config = validate_docker_compose_file(compose_path)
            result.services_count = len(config.services)

            # Additional startup-specific validations
            self._validate_port_conflicts(config, result)
            self._validate_shared_volume_mounts(config, result)
            self._validate_build_contexts(config, result)
            self._validate_dependencies(config, result)
            self._validate_health_checks(config, result)
            self._validate_circular_dependencies(config, result)

            # Count issues
            result.errors = len([i for i in result.issues if i.severity == 'error'])
            result.warnings = len([i for i in result.issues if i.severity == 'warning'])

            # Overall success if no errors and no port conflicts
            result.success = result.errors == 0 and len(result.port_conflicts) == 0

        except Exception as e:
            result.success = False
            result.validation_errors.append(f"Docker Compose validation failed: {str(e)[:200]}...")

        return result

    def _validate_port_conflicts(self, config, result: DockerComposeValidationResult):
        """Check for port conflicts - critical for multi-service startup."""
        used_ports = set()

        for service_name, service in config.services.items():
            if service.ports:
                for port_mapping in service.ports:
                    if isinstance(port_mapping, str):
                        # Parse "host:container" or "host:container/protocol"
                        if ':' in port_mapping:
                            host_port = port_mapping.split(':')[0]
                            try:
                                host_port_int = int(host_port)
                                if host_port_int in used_ports:
                                    # Find conflicting services
                                    conflicting_services = []
                                    for s_name, s_config in config.services.items():
                                        if s_config.ports:
                                            for pm in s_config.ports:
                                                if isinstance(pm, str) and pm.startswith(f"{host_port_int}:"):
                                                    conflicting_services.append(s_name)

                                    result.port_conflicts.append(PortConflict(
                                        port=str(host_port_int),
                                        services=conflicting_services,
                                        severity="error"
                                    ))
                                else:
                                    used_ports.add(host_port_int)
                            except ValueError:
                                result.issues.append(ValidationIssue(
                                    service_name=service_name,
                                    issue_type="port_mapping",
                                    severity="warning",
                                    description=f"Non-numeric port: {host_port}"
                                ))
                    elif isinstance(port_mapping, dict):
                        # Handle dictionary format
                        if 'published' in port_mapping:
                            try:
                                host_port_int = int(port_mapping['published'])
                                if host_port_int in used_ports:
                                    result.port_conflicts.append(PortConflict(
                                        port=str(host_port_int),
                                        services=[service_name],
                                        severity="error"
                                    ))
                                else:
                                    used_ports.add(host_port_int)
                            except (ValueError, TypeError):
                                result.issues.append(ValidationIssue(
                                    service_name=service_name,
                                    issue_type="port_mapping",
                                    severity="warning",
                                    description=f"Invalid published port: {port_mapping.get('published')}"
                                ))

    def _validate_shared_volume_mounts(self, config, result: DockerComposeValidationResult):
        """Check for missing shared volume mounts."""
        services_with_shared_volume = []
        services_without_shared_volume = []

        for service_name, service in config.services.items():
            if service.volumes:
                has_shared_volume = False
                for volume in service.volumes:
                    if isinstance(volume, str) and ('services/shared' in volume or './:/app' in volume):
                        has_shared_volume = True
                        services_with_shared_volume.append(service_name)
                        break
                if not has_shared_volume:
                    services_without_shared_volume.append(service_name)

        # Warn about services that have shared imports but no shared volume
        for service_name in self.services_that_import_shared:
            if service_name in services_without_shared_volume:
                result.issues.append(ValidationIssue(
                    service_name=service_name,
                    issue_type="volume_mount",
                    severity="warning",
                    description="Service imports from services.shared but lacks shared volume mount"
                ))

    def _validate_build_contexts(self, config, result: DockerComposeValidationResult):
        """Check for services with build but no context."""
        for service_name, service in config.services.items():
            if service.build and isinstance(service.build, dict):
                if 'context' not in service.build:
                    result.issues.append(ValidationIssue(
                        service_name=service_name,
                        issue_type="build_config",
                        severity="error",
                        description="Service has build section but no context",
                        can_auto_fix=True,
                        suggested_fix={"context": "."}
                    ))

    def _validate_dependencies(self, config, result: DockerComposeValidationResult):
        """Check for dependency format issues."""
        for service_name, service in config.services.items():
            if isinstance(service.depends_on, str):
                result.issues.append(ValidationIssue(
                    service_name=service_name,
                    issue_type="dependency",
                    severity="error",
                    description="depends_on should be a list, not a string",
                    can_auto_fix=True,
                    suggested_fix={"depends_on": [service.depends_on]}
                ))

    def _validate_health_checks(self, config, result: DockerComposeValidationResult):
        """Check for health check configuration issues."""
        for service_name, service in config.services.items():
            if service.healthcheck:
                # Check for health checks that start immediately (no start_period)
                if hasattr(service.healthcheck, 'start_period') and service.healthcheck.start_period:
                    try:
                        start_period = int(service.healthcheck.start_period)
                        if start_period < 10:
                            result.issues.append(ValidationIssue(
                                service_name=service_name,
                                issue_type="health_check",
                                severity="warning",
                                description=f"Very short health check start_period ({start_period}s)"
                            ))
                    except (ValueError, TypeError):
                        result.issues.append(ValidationIssue(
                            service_name=service_name,
                            issue_type="health_check",
                            severity="warning",
                            description=f"Invalid start_period value: {service.healthcheck.start_period}"
                        ))
                elif not hasattr(service.healthcheck, 'start_period'):
                    result.issues.append(ValidationIssue(
                        service_name=service_name,
                        issue_type="health_check",
                        severity="warning",
                        description="Missing start_period in health check"
                    ))

    def _validate_circular_dependencies(self, config, result: DockerComposeValidationResult):
        """Check for circular dependencies."""
        dependency_graph = {}
        for service_name, service in config.services.items():
            if service.depends_on:
                if isinstance(service.depends_on, dict):
                    deps = list(service.depends_on.keys())
                elif isinstance(service.depends_on, list):
                    deps = service.depends_on
                else:
                    deps = [service.depends_on]
                dependency_graph[service_name] = deps

        # Simple cycle detection
        for service, deps in dependency_graph.items():
            for dep in deps:
                if dep in dependency_graph and service in dependency_graph.get(dep, []):
                    result.issues.append(ValidationIssue(
                        service_name=service,
                        issue_type="dependency",
                        severity="error",
                        description=f"Circular dependency detected with '{dep}'"
                    ))

    def validate_multiple_files(self, compose_files: List[str]) -> Dict[str, DockerComposeValidationResult]:
        """
        Validate multiple Docker Compose files.

        Args:
            compose_files: List of docker-compose files to validate

        Returns:
            Dictionary mapping filenames to validation results
        """
        results = {}
        for compose_file in compose_files:
            results[compose_file] = self.validate_for_startup(compose_file)
        return results
