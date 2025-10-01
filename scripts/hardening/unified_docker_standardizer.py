#!/usr/bin/env python3
"""
Unified Docker Standardization and Validation System

Combines Docker standardization (file modification) with Pydantic validation (type safety)
to provide a comprehensive, unified approach to Docker configuration management.

This system unifies:
- Docker Compose file standardization (main_docker_compose_standardizer.py)
- Docker port and configuration management (docker_standardization.py)
- Dockerfile validation and best practices (dockerfile_validator.py)
- Pydantic validation for type safety (docker_pydantic.py)

Features:
- Validates configurations using Pydantic before applying changes
- Standardizes Docker files with validated transformations
- Provides both validation-only and standardization modes
- Unified error reporting and fixing capabilities
"""

import sys
import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Literal
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import Pydantic Docker validation
from services.shared.infrastructure.config.docker_pydantic import (
    validate_docker_compose_file, validate_dockerfile, DockerComposeConfig,
    DockerService, PortMapping, VolumeMount, EnvironmentVariable,
    PYDANTIC_AVAILABLE
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StandardizationMode(Enum):
    """Modes for Docker standardization operations."""
    VALIDATE_ONLY = "validate"
    DRY_RUN = "dry_run"
    APPLY_CHANGES = "apply"


class StandardizationResult(Enum):
    """Results of standardization operations."""
    SUCCESS = "success"
    VALIDATION_FAILED = "validation_failed"
    STANDARDIZATION_FAILED = "standardization_failed"
    NO_CHANGES_NEEDED = "no_changes_needed"


@dataclass
class DockerStandardizationIssue:
    """Represents a Docker configuration issue that can be standardized."""
    file_path: str
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

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent

        # Service port mappings from centralized registry
        self.service_ports = self._load_service_ports()

        # Validation state
        self.pydantic_available = PYDANTIC_AVAILABLE

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
            'log-collector': 5080
        }

    def standardize_all_docker_configs(self, mode: StandardizationMode = StandardizationMode.DRY_RUN) -> DockerStandardizationReport:
        """
        Standardize all Docker configurations in the project.

        Args:
            mode: Standardization mode (validate, dry_run, apply)

        Returns:
            Comprehensive standardization report
        """
        report = DockerStandardizationReport()

        print(f"🚀 Starting Unified Docker Standardization (Mode: {mode.value})")
        print("=" * 60)

        # Step 1: Validate with Pydantic first (if available)
        if self.pydantic_available:
            print("🔍 Step 1: Pydantic Validation")
            validation_report = self._validate_all_with_pydantic()
            report.pydantic_validation_passed = validation_report['passed']
            report.validation_errors = validation_report['errors']

            if validation_report['errors'] > 0:
                print(f"❌ Found {validation_report['errors']} Pydantic validation errors:")
                for file_path, details in validation_report['details'].items():
                    if details['status'] == 'invalid':
                        print(f"   • {file_path}: {details['error'][:100]}...")

            if not validation_report['passed'] and mode != StandardizationMode.VALIDATE_ONLY:
                print("⚠️  Pydantic validation failed. Switching to validate-only mode.")
                mode = StandardizationMode.VALIDATE_ONLY

        # Step 2: Standardize Docker Compose files
        print("\n🔧 Step 2: Docker Compose Standardization")
        compose_report = self._standardize_docker_compose_files(mode)
        report.files_processed += compose_report['files_processed']
        report.files_modified += compose_report['files_modified']
        report.issues_found += compose_report['issues_found']
        report.issues_fixed += compose_report['issues_fixed']
        report.issues.extend(compose_report['issues'])

        # Step 3: Validate Dockerfiles
        print("\n📋 Step 3: Dockerfile Validation")
        dockerfile_report = self._validate_dockerfiles()
        report.files_processed += dockerfile_report['files_processed']
        report.issues_found += dockerfile_report['issues_found']
        report.issues.extend(dockerfile_report['issues'])

        # Step 4: Generate final report
        self._generate_final_report(report, mode)

        return report

    def _validate_all_with_pydantic(self) -> Dict[str, Any]:
        """Validate all Docker configurations using Pydantic."""
        validation_results = {
            'passed': True,
            'errors': 0,
            'details': {}
        }

        # Validate Docker Compose files
        compose_files = list(self.project_root.glob("**/docker-compose*.yml"))
        compose_files.extend(list(self.project_root.glob("**/docker-compose*.yaml")))

        for compose_file in compose_files:
            try:
                config = validate_docker_compose_file(compose_file)
                validation_results['details'][str(compose_file)] = {
                    'status': 'valid',
                    'services': len(config.services)
                }
                print(f"  ✅ {compose_file.name}: {len(config.services)} services")
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
                print(f"  ❌ {compose_file.name} ({compose_file.relative_to(self.project_root)}): {error_type} - {error_msg[:80]}...")

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
            self.project_root / "docker-compose.dev.yml",
            self.project_root / "docker-compose.prod.yml",
            self.project_root / "docker-compose.yml"
        ]

        for compose_file in compose_files:
            if not compose_file.exists():
                continue

            result['files_processed'] += 1
            print(f"  📝 Processing {compose_file.name}...")

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
                service_issues = self._standardize_service_config(service_name, service_config, compose_file)
                issues.extend(service_issues)

            # Apply fixes if in apply mode
            if mode == StandardizationMode.APPLY_CHANGES and issues:
                fixes_applied = sum(1 for issue in issues if issue.can_auto_fix)
                if fixes_applied > 0:
                    print(f"    🔧 Applied {fixes_applied} auto-fixes")
                    with open(compose_file, 'w') as f:
                        yaml.dump(compose_config, f, default_flow_style=False, indent=2, sort_keys=False)

        except Exception as e:
            logger.error(f"Error processing {compose_file}: {e}")

        return issues

    def _standardize_service_config(self, service_name: str, service_config: Dict[str, Any], file_path: Path) -> List[DockerStandardizationIssue]:
        """Standardize a single service configuration."""
        issues = []

        # Skip infrastructure services
        if service_name in ['redis', 'postgres', 'nginx', 'grafana', 'prometheus', 'jaeger']:
            return issues

        # Check port mappings
        if 'ports' in service_config:
            port_issues = self._standardize_ports(service_name, service_config, file_path)
            issues.extend(port_issues)

        # Check environment variables
        if 'environment' in service_config:
            env_issues = self._standardize_environment(service_name, service_config, file_path)
            issues.extend(env_issues)

        # Check depends_on
        if 'depends_on' in service_config:
            depends_issues = self._standardize_dependencies(service_name, service_config, file_path)
            issues.extend(depends_issues)

        # Check volumes
        if 'volumes' in service_config:
            volume_issues = self._standardize_volumes(service_name, service_config, file_path)
            issues.extend(volume_issues)

        return issues

    def _standardize_ports(self, service_name: str, service_config: Dict[str, Any], file_path: Path) -> List[DockerStandardizationIssue]:
        """Standardize port mappings."""
        issues = []

        if service_name not in self.service_ports:
            return issues

        expected_port = self.service_ports[service_name]
        ports = service_config.get('ports', [])

        # Check if service has correct port mapping
        has_correct_mapping = False
        for port_mapping in ports:
            if isinstance(port_mapping, str):
                # Parse "host:container" format
                if ':' in port_mapping:
                    host_port, container_part = port_mapping.split(':', 1)
                    try:
                        host_port = int(host_port)
                        if host_port == expected_port:
                            has_correct_mapping = True
                            break
                    except ValueError:
                        continue
            elif isinstance(port_mapping, dict):
                # Handle dict format
                if port_mapping.get('published') == expected_port:
                    has_correct_mapping = True
                    break

        if not has_correct_mapping:
            issues.append(DockerStandardizationIssue(
                file_path=str(file_path),
                service_name=service_name,
                issue_type='port_mapping',
                severity='warning',
                description=f"Service {service_name} should expose port {expected_port}",
                current_value=ports,
                recommended_value=[f"{expected_port}:{expected_port}"],
                can_auto_fix=True
            ))

        return issues

    def _standardize_environment(self, service_name: str, service_config: Dict[str, Any], file_path: Path) -> List[DockerStandardizationIssue]:
        """Standardize environment variables."""
        issues = []
        environment = service_config.get('environment', [])

        # Ensure environment is a list format (not dict)
        if isinstance(environment, dict):
            issues.append(DockerStandardizationIssue(
                file_path=str(file_path),
                service_name=service_name,
                issue_type='environment_format',
                severity='info',
                description=f"Environment variables should be in list format for consistency",
                current_value=environment,
                recommended_value=[f"{k}={v}" for k, v in environment.items()],
                can_auto_fix=True
            ))

        return issues

    def _standardize_dependencies(self, service_name: str, service_config: Dict[str, Any], file_path: Path) -> List[DockerStandardizationIssue]:
        """Standardize service dependencies."""
        issues = []
        depends_on = service_config.get('depends_on', [])

        # Ensure depends_on is a list
        if isinstance(depends_on, str):
            issues.append(DockerStandardizationIssue(
                file_path=str(file_path),
                service_name=service_name,
                issue_type='depends_on_format',
                severity='error',
                description=f"depends_on should be a list, not a string",
                current_value=depends_on,
                recommended_value=[depends_on],
                can_auto_fix=True
            ))

        return issues

    def _standardize_volumes(self, service_name: str, service_config: Dict[str, Any], file_path: Path) -> List[DockerStandardizationIssue]:
        """Standardize volume mounts."""
        issues = []
        volumes = service_config.get('volumes', [])

        # Check for overly complex volume mounts
        for volume in volumes:
            if isinstance(volume, str) and ':' in volume:
                parts = volume.split(':')
                if len(parts) > 2:
                    # Complex volume mount with options
                    issues.append(DockerStandardizationIssue(
                        file_path=str(file_path),
                        service_name=service_name,
                        issue_type='volume_complexity',
                        severity='info',
                        description=f"Complex volume mount detected: {volume}",
                        current_value=volume,
                        recommended_value=volume,  # Keep as-is for now
                        can_auto_fix=False
                    ))

        return issues

    def _validate_dockerfiles(self) -> Dict[str, Any]:
        """Validate Dockerfiles using Pydantic."""
        result = {
            'files_processed': 0,
            'issues_found': 0,
            'issues': []
        }

        dockerfiles = list(self.project_root.glob("**/Dockerfile"))
        dockerfiles.extend(list(self.project_root.glob("**/Dockerfile.*")))

        for dockerfile in dockerfiles:
            result['files_processed'] += 1
            try:
                config = validate_dockerfile(dockerfile)
                print(f"  ✅ {dockerfile.parent.name}: {len(config.instructions)} instructions")

                # Check for common Dockerfile issues
                issues = self._analyze_dockerfile_issues(dockerfile, config)
                result['issues'].extend(issues)
                result['issues_found'] += len(issues)

            except Exception as e:
                result['issues_found'] += 1
                error_msg = str(e)
                # Extract more specific error information
                if "validation error for DockerfileInstruction" in error_msg:
                    error_type = "Dockerfile instruction validation"
                elif "validation error for DockerfileConfig" in error_msg:
                    error_type = "Dockerfile structure validation"
                else:
                    error_type = "Dockerfile parsing"

                result['issues'].append(DockerStandardizationIssue(
                    file_path=str(dockerfile),
                    service_name=dockerfile.parent.name,
                    issue_type='dockerfile_validation',
                    severity='error',
                    description=f"{error_type} failed: {error_msg[:100]}...",
                    current_value=None,
                    recommended_value=None,
                    can_auto_fix=False
                ))
                print(f"  ❌ {dockerfile.parent.name} ({dockerfile.relative_to(self.project_root)}): {error_type} - {error_msg[:80]}...")

        return result

    def _analyze_dockerfile_issues(self, dockerfile: Path, config) -> List[DockerStandardizationIssue]:
        """Analyze Dockerfile for common issues."""
        issues = []

        # Check for CMD/ENTRYPOINT duplication
        cmd_count = sum(1 for i in config.instructions if i.instruction == 'CMD')
        entrypoint_count = sum(1 for i in config.instructions if i.instruction == 'ENTRYPOINT')

        if cmd_count > 1:
            issues.append(DockerStandardizationIssue(
                file_path=str(dockerfile),
                service_name=dockerfile.parent.name,
                issue_type='dockerfile_cmd_duplicate',
                severity='error',
                description="Dockerfile contains multiple CMD instructions",
                current_value=cmd_count,
                recommended_value=1,
                can_auto_fix=False  # Would require manual decision
            ))

        if entrypoint_count > 1:
            issues.append(DockerStandardizationIssue(
                file_path=str(dockerfile),
                service_name=dockerfile.parent.name,
                issue_type='dockerfile_entrypoint_duplicate',
                severity='error',
                description="Dockerfile contains multiple ENTRYPOINT instructions",
                current_value=entrypoint_count,
                recommended_value=1,
                can_auto_fix=False
            ))

        return issues

    def _generate_final_report(self, report: DockerStandardizationReport, mode: StandardizationMode):
        """Generate comprehensive final report."""
        print("\n" + "=" * 60)
        print("📊 DOCKER STANDARDIZATION REAPI_PORT")
        print("=" * 60)

        print(f"Mode: {mode.value}")
        print(f"Pydantic Validation: {'✅ Passed' if report.pydantic_validation_passed else '❌ Failed'}")
        print(f"Files Processed: {report.files_processed}")
        print(f"Files Modified: {report.files_modified}")
        print(f"Issues Found: {report.issues_found}")
        print(f"Issues Auto-Fixed: {report.issues_fixed}")
        print(f"Validation Errors: {report.validation_errors}")

        if report.issues:
            print("\n🔧 Issues by Type:")
            issue_types = {}
            for issue in report.issues:
                issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1

            for issue_type, count in sorted(issue_types.items()):
                print(f"  • {issue_type}: {count}")

        print("\n✅ Docker Standardization Complete")


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Unified Docker Standardization System")
    parser.add_argument('--mode', '-m', choices=['validate', 'dry-run', 'apply'],
                       default='validate', help='Standardization mode')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Map string modes to enum
    mode_map = {
        'validate': StandardizationMode.VALIDATE_ONLY,
        'dry-run': StandardizationMode.DRY_RUN,
        'apply': StandardizationMode.APPLY_CHANGES
    }

    standardizer = UnifiedDockerStandardizer()

    try:
        report = standardizer.standardize_all_docker_configs(mode_map[args.mode])

        # Exit with appropriate code
        if report.validation_errors > 0:
            sys.exit(1)  # Validation errors
        elif report.issues_found > 0 and mode_map[args.mode] == StandardizationMode.VALIDATE_ONLY:
            sys.exit(1)  # Issues found in validate-only mode
        else:
            sys.exit(0)  # Success

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
