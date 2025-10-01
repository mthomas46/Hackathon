#!/usr/bin/env python3
"""
CI/CD Validation System

Comprehensive validation system for CI/CD pipelines to ensure
configuration standardization and prevent regressions.
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ValidationType(Enum):
    """Types of validations to perform."""
    CONFIGURATION_STANDARDIZATION = "configuration_standardization"
    DOCKER_VALIDATION = "docker_validation"
    DEPENDENCY_VALIDATION = "dependency_validation"
    PORT_CONFLICT_CHECK = "port_conflict_check"
    ENVIRONMENT_VARIABLES = "environment_variables"
    NETWORK_CONFIGURATION = "network_configuration"
    VOLUME_CONFIGURATION = "volume_configuration"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    validation_type: ValidationType
    passed: bool
    issues_found: int = 0
    warnings: int = 0
    errors: int = 0
    details: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class CIValidationReport:
    """Comprehensive CI/CD validation report."""
    overall_passed: bool = False
    validations_run: int = 0
    validations_passed: int = 0
    total_issues: int = 0
    total_warnings: int = 0
    total_errors: int = 0
    results: List[ValidationResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class CICheckValidator:
    """
    Comprehensive CI/CD validation system that runs all standardization checks.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.start_time = None

    def run_full_validation(self, fail_on_warnings: bool = False) -> CIValidationReport:
        """
        Run comprehensive validation suite for CI/CD.

        Args:
            fail_on_warnings: If True, warnings will cause validation to fail

        Returns:
            Complete validation report
        """
        import time
        self.start_time = time.time()

        print("🚀 Starting CI/CD Configuration Validation Suite")
        print("=" * 60)

        report = CIValidationReport()

        # Define validation checks to run
        validations = [
            (ValidationType.CONFIGURATION_STANDARDIZATION, self._validate_configuration_standardization),
            (ValidationType.DOCKER_VALIDATION, self._validate_docker_configurations),
            (ValidationType.DEPENDENCY_VALIDATION, self._validate_dependencies),
            (ValidationType.PORT_CONFLICT_CHECK, self._validate_port_conflicts),
            (ValidationType.ENVIRONMENT_VARIABLES, self._validate_environment_variables),
            (ValidationType.NETWORK_CONFIGURATION, self._validate_network_configuration),
            (ValidationType.VOLUME_CONFIGURATION, self._validate_volume_configuration),
        ]

        for validation_type, validation_func in validations:
            print(f"\n🔍 Running {validation_type.value.replace('_', ' ').title()} validation...")

            try:
                result = validation_func()
                report.results.append(result)
                report.validations_run += 1

                if result.passed:
                    report.validations_passed += 1
                    print(f"✅ PASSED ({result.duration_seconds:.2f}s)")
                else:
                    print(f"❌ FAILED ({result.duration_seconds:.2f}s)")
                    if result.details:
                        for detail in result.details[:5]:  # Show first 5 issues
                            print(f"   • {detail}")

                report.total_issues += result.issues_found
                report.total_warnings += result.warnings
                report.total_errors += result.errors

            except Exception as e:
                print(f"❌ ERROR: {e}")
                result = ValidationResult(
                    validation_type=validation_type,
                    passed=False,
                    errors=1,
                    details=[f"Validation failed with error: {e}"]
                )
                report.results.append(result)
                report.validations_run += 1
                report.total_errors += 1

        # Determine overall result
        report.overall_passed = (
            report.validations_passed == report.validations_run and
            (not fail_on_warnings or report.total_warnings == 0)
        )

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        self._print_final_report(report)
        return report

    def _validate_configuration_standardization(self) -> ValidationResult:
        """Validate configuration standardization."""
        import time
        start_time = time.time()

        try:
            # Check for configuration files existence and basic structure
            config_files = list(self.project_root.glob("services/*/config.yaml"))
            issues_found = 0
            details = []

            for config_file in config_files[:20]:  # Check first 20 for speed
                if not config_file.exists():
                    issues_found += 1
                    details.append(f"Missing config.yaml: {config_file.parent.name}")
                    continue

                # Basic YAML validation
                try:
                    import yaml
                    with open(config_file, 'r') as f:
                        yaml.safe_load(f)
                except Exception as e:
                    issues_found += 1
                    details.append(f"Invalid YAML in {config_file.parent.name}: {str(e)[:50]}...")

            passed = issues_found == 0

            return ValidationResult(
                validation_type=ValidationType.CONFIGURATION_STANDARDIZATION,
                passed=passed,
                issues_found=issues_found,
                errors=issues_found,
                details=details,
                duration_seconds=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.CONFIGURATION_STANDARDIZATION,
                passed=False,
                errors=1,
                details=[f"Configuration validation failed: {e}"],
                duration_seconds=time.time() - start_time
            )

    def _validate_docker_configurations(self) -> ValidationResult:
        """Validate Docker configurations with detailed error reporting."""
        import time
        start_time = time.time()

        try:
            # Basic Docker Compose validation using docker-compose config
            compose_files = []
            for pattern in ["docker-compose*.yml", "docker-compose*.yaml"]:
                compose_files.extend(list(self.project_root.rglob(pattern)))

            issues_found = 0
            details = []

            # Services that legitimately depend on other services (dashboards, analysis services)
            services_with_legitimate_cross_deps = [
                'simulation-dashboard', 'analysis-service', 'data-services-dashboard'
            ]

            # Pre-validation patterns for common issues (speeds up processing)
            common_patterns = {
                'missing_volumes': [],  # Will be populated during validation
                'missing_redis': [],    # Services that depend on redis but don't define it
                'obsolete_versions': [], # Files with version attributes
                'self_contained_candidates': []  # Services that could be made self-contained
            }

            # Check all files, not just first 10
            for compose_file in compose_files:
                # Skip template and standardized files entirely as they are not production configurations
                if ('template' in compose_file.name.lower() or 'template' in str(compose_file) or
                    'standardized' in str(compose_file)):
                    continue

                # Check if this file contains services with legitimate cross-dependencies
                file_has_legitimate_cross_deps = False
                file_service_names = []

                # Pre-analyze file for common patterns (speeds up validation)
                try:
                    with open(compose_file, 'r') as f:
                        import yaml
                        compose_data = yaml.safe_load(f)

                        if compose_data:
                            # Check for obsolete version
                            if 'version' in compose_data:
                                common_patterns['obsolete_versions'].append(str(compose_file))

                            if 'services' in compose_data:
                                services = compose_data.get('services', {})
                                volumes = compose_data.get('volumes', {})

                                for svc_name, svc_config in services.items():
                                    file_service_names.append(svc_name)

                                    # Check for legitimate cross-dependencies
                                    if svc_name in services_with_legitimate_cross_deps:
                                        file_has_legitimate_cross_deps = True

                                    # Pre-check volume patterns
                                    if 'volumes' in svc_config:
                                        for volume in svc_config['volumes']:
                                            if isinstance(volume, str):
                                                volume_parts = volume.split(':')
                                                if len(volume_parts) >= 2:
                                                    volume_name = volume_parts[0]
                                                    # Only check for named volumes, not host paths
                                                    # Named volumes don't contain '/' and don't start with '.' or '..'
                                                    if (not volume_name.startswith('.') and
                                                        not volume_name.startswith('..') and
                                                        '/' not in volume_name and
                                                        volume_name not in volumes):
                                                        common_patterns['missing_volumes'].append({
                                                            'file': str(compose_file),
                                                            'service': svc_name,
                                                            'volume': volume_name
                                                        })

                                    # Pre-check dependency patterns
                                    if 'depends_on' in svc_config:
                                        depends_on = svc_config['depends_on']
                                        if isinstance(depends_on, (list, dict)):
                                            deps = depends_on if isinstance(depends_on, list) else list(depends_on.keys())
                                            if 'redis' in deps and 'redis' not in services:
                                                common_patterns['missing_redis'].append({
                                                    'file': str(compose_file),
                                                    'service': svc_name
                                                })

                except Exception as e:
                    # If pre-analysis fails, continue with normal validation
                    pass

                try:
                    result = subprocess.run(
                        ['docker-compose', '-f', str(compose_file), 'config', '--quiet'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode != 0:
                        file_name = compose_file.name
                        service_name = compose_file.parent.name if compose_file.parent.name != 'Hackathon' else 'root'

                        # Try to extract error details from stderr
                        error_msg = result.stderr.strip()
                        if error_msg:
                            # Extract the key error information
                            if 'depends on undefined service' in error_msg:
                                # Skip dependency errors for services with legitimate cross-dependencies
                                if not file_has_legitimate_cross_deps:
                                    issues_found += 1
                                    error_type = "❌ DEPENDENCY ERROR"
                                    details.append(f"{error_type} {service_name}/{file_name}: Cross-file service reference issue")
                            elif 'obsolete' in error_msg:
                                issues_found += 1
                                error_type = "⚠️  LEGACY SYNTAX"
                                details.append(f"{error_type} {service_name}/{file_name}: Contains obsolete version attribute")
                            elif 'undefined volume' in error_msg or 'invalid compose project' in error_msg:
                                issues_found += 1
                                error_type = "❌ VOLUME ERROR"
                                details.append(f"{error_type} {service_name}/{file_name}: Undefined volume reference")
                            else:
                                issues_found += 1
                                error_type = "❌ SYNTAX ERROR"
                                details.append(f"{error_type} {service_name}/{file_name}: {error_msg[:100]}...")
                        else:
                            issues_found += 1
                            details.append(f"❌ VALIDATION FAILED {service_name}/{file_name}: Unknown error")


                    # Enhanced validation: Check for common issues even if basic validation passes
                    # Skip template files and files with legitimate cross-dependencies for enhanced checks
                    if 'template' in compose_file.name.lower() or file_has_legitimate_cross_deps:
                        continue

                    try:
                        import yaml
                        with open(compose_file, 'r') as f:
                            compose_data = yaml.safe_load(f)

                        if compose_data and 'services' in compose_data:
                            services = compose_data.get('services', {})
                            volumes = compose_data.get('volumes', {})

                            # Check for undefined volume references (pattern from our fixes)
                            for svc_name, svc_config in services.items():
                                if 'volumes' in svc_config:
                                    for volume in svc_config['volumes']:
                                        if isinstance(volume, str):
                                            # Format: host_path:container_path or volume_name:container_path
                                            volume_parts = volume.split(':')
                                            if len(volume_parts) >= 2:
                                                volume_name = volume_parts[0]
                                                # Only check for named volumes, not host paths
                                                # Named volumes don't contain '/' and don't start with '.' or '..'
                                                if (not volume_name.startswith('.') and
                                                    not volume_name.startswith('..') and
                                                    '/' not in volume_name and
                                                    volume_name not in volumes):
                                                    issues_found += 1
                                                    details.append(f"❌ VOLUME ERROR {service_name}/{file_name}: Service '{svc_name}' references undefined volume '{volume_name}'")

                            # Check for services depending on infrastructure but not defining it locally
                            # Allow legitimate business dependencies (dashboards depending on services they display, analysis depending on storage)
                            legitimate_cross_deps = {
                                'simulation-dashboard': ['project-simulation', 'unified-api-dashboard'],
                                'analysis-service': ['doc_store'],
                                'data-services-dashboard': ['unified-api-dashboard']
                            }

                            for svc_name, svc_config in services.items():
                                if 'depends_on' in svc_config:
                                    depends_on = svc_config['depends_on']
                                    if isinstance(depends_on, dict):
                                        # Handle dict format with conditions
                                        dep_services = list(depends_on.keys())
                                    elif isinstance(depends_on, list):
                                        dep_services = depends_on
                                    else:
                                        continue

                                    # Check each dependency
                                    for dep in dep_services:
                                        # Skip legitimate business dependencies
                                        if svc_name in legitimate_cross_deps and dep in legitimate_cross_deps[svc_name]:
                                            continue

                                        # Flag infrastructure dependencies that should be local
                                        if dep in ['redis', 'postgres'] and dep not in services:
                                            issues_found += 1
                                            details.append(f"❌ DEPENDENCY ERROR {service_name}/{file_name}: Service '{svc_name}' depends on {dep} but {dep} service not defined locally")
                                        elif dep not in services and dep not in ['redis', 'postgres']:
                                            # For other services, check if they exist elsewhere or if this is a legitimate cross-dependency
                                            # This is more lenient for business services
                                            pass

                    except yaml.YAMLError as e:
                        issues_found += 1
                        details.append(f"❌ SYNTAX ERROR {service_name}/{file_name}: YAML parsing error - {str(e)}")
                    except Exception:
                        # If enhanced checks fail, continue with basic validation
                        pass

                except subprocess.TimeoutExpired:
                    issues_found += 1
                    file_name = compose_file.name
                    service_name = compose_file.parent.name if compose_file.parent.name != 'Hackathon' else 'root'
                    details.append(f"⏰ TIMEOUT {service_name}/{file_name}: Validation took too long")

                except FileNotFoundError:
                    # docker-compose not available, skip validation
                    details.append("⚠️  SKIPPING: docker-compose command not available")
                    break

            # Add pattern analysis summary for faster future fixes
            if common_patterns['missing_volumes']:
                details.append(f"📊 PATTERN DETECTED: {len(common_patterns['missing_volumes'])} missing *_code volumes across services")
            if common_patterns['missing_redis']:
                details.append(f"📊 PATTERN DETECTED: {len(common_patterns['missing_redis'])} services depend on redis but don't define it")
            if common_patterns['obsolete_versions']:
                details.append(f"📊 PATTERN DETECTED: {len(common_patterns['obsolete_versions'])} files have obsolete version attributes")

            passed = issues_found == 0

            if issues_found > 0:
                details.insert(0, f"❌ CRITICAL: {issues_found} Docker Compose files have validation errors")

            return ValidationResult(
                validation_type=ValidationType.DOCKER_VALIDATION,
                passed=passed,
                issues_found=issues_found,
                errors=issues_found,
                details=details,
                duration_seconds=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.DOCKER_VALIDATION,
                passed=False,
                errors=1,
                details=[f"Docker validation failed: {e}"],
                duration_seconds=time.time() - start_time
            )

    def _validate_dependencies(self) -> ValidationResult:
        """Validate service dependencies."""
        import time
        start_time = time.time()

        try:
            sys.path.insert(0, str(self.project_root / "scripts" / "hardening"))
            from dependency_standardizer import DependencyStandardizer

            standardizer = DependencyStandardizer()
            analysis = standardizer.analyze_dependencies()

            issues_found = analysis.issues_found
            coverage_percentage = (analysis.services_with_dependencies / analysis.total_services * 100) if analysis.total_services > 0 else 0

            passed = issues_found == 0 and coverage_percentage >= 80  # Require 80% coverage

            details = []
            if coverage_percentage < 80:
                details.append(f"Dependency coverage too low: {coverage_percentage:.1f}% (need ≥80%)")

            if analysis.issues:
                details.extend([f"{issue.service_name}: {issue.description}" for issue in analysis.issues[:5]])

            return ValidationResult(
                validation_type=ValidationType.DEPENDENCY_VALIDATION,
                passed=passed,
                issues_found=issues_found,
                errors=issues_found,
                details=details,
                duration_seconds=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.DEPENDENCY_VALIDATION,
                passed=False,
                errors=1,
                details=[f"Dependency validation failed: {e}"],
                duration_seconds=time.time() - start_time
            )

    def _validate_port_conflicts(self) -> ValidationResult:
        """Validate port conflicts with smart infrastructure handling."""
        import time
        start_time = time.time()

        try:
            sys.path.insert(0, str(self.project_root / "scripts" / "hardening"))
            from port_registry import PortRegistry

            registry = PortRegistry()
            # Use the registry's smart filtering method for consistency
            filtered_conflicts = registry.check_conflicts_smart()

            issues_found = len(filtered_conflicts)
            passed = issues_found == 0

            details = []
            if filtered_conflicts:
                details.append(f"❌ CRITICAL: {len(filtered_conflicts)} non-infrastructure port conflicts found")

                # Group conflicts by port for better readability
                conflicts_by_port = {}
                for conflict in filtered_conflicts:
                    if conflict.port not in conflicts_by_port:
                        conflicts_by_port[conflict.port] = []
                    conflicts_by_port[conflict.port].extend(conflict.conflicting_services)

                # Show detailed breakdown
                for port, services in sorted(conflicts_by_port.items()):
                    severity = "🔴 CRITICAL" if port < 1024 else "🟡 WARNING"
                    details.append(f"  {severity} Port {port}: {len(services)} conflicting services")

                    # Show file paths for each conflicting service
                    for service_info in services[:3]:  # Show first 3 to avoid spam
                        # Extract file path from service_info format: "service (file_path)"
                        if '(' in service_info and ')' in service_info:
                            service_name = service_info.split('(')[0].strip()
                            file_path = service_info.split('(')[1].split(')')[0]
                            file_name = Path(file_path).name
                            details.append(f"    • {service_name} → {file_name}")

                    if len(services) > 3:
                        details.append(f"    • ... and {len(services) - 3} more services")

                details.append("  ℹ️  Note: Infrastructure services (Redis, PostgreSQL, etc.) are allowed to share standard ports")
            else:
                details.append("✅ No problematic port conflicts found (infrastructure conflicts allowed)")

            return ValidationResult(
                validation_type=ValidationType.PORT_CONFLICT_CHECK,
                passed=passed,
                issues_found=issues_found,
                errors=issues_found,
                details=details,
                duration_seconds=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.PORT_CONFLICT_CHECK,
                passed=False,
                errors=1,
                details=[f"Port validation failed: {e}"],
                duration_seconds=time.time() - start_time
            )

    def _validate_environment_variables(self) -> ValidationResult:
        """Validate environment variable standardization."""
        import time
        start_time = time.time()

        try:
            # Check for common environment variable patterns
            compose_files = list(self.project_root.glob("services/*/docker-compose.yml"))
            issues_found = 0
            details = []

            # Check for ENABLE_* variables that should be FEATURE_*
            for compose_file in compose_files[:10]:  # Check first 10 for speed
                try:
                    with open(compose_file, 'r') as f:
                        content = f.read()
                        if 'ENABLE_' in content:
                            issues_found += 1
                            details.append(f"ENABLE_ variables found in {compose_file.parent.name} (should be FEATURE_*)")
                except Exception:
                    pass

            # Check for inconsistent prefixes
            inconsistent_prefixes = []
            for compose_file in compose_files[:5]:
                try:
                    with open(compose_file, 'r') as f:
                        content = f.read()
                        # Look for non-standard prefixes
                        if 'DB_' in content and 'DATABASE_' in content:
                            inconsistent_prefixes.append(compose_file.parent.name)
                except Exception:
                    pass

            if inconsistent_prefixes:
                issues_found += len(inconsistent_prefixes)
                details.append(f"Inconsistent DB_ vs DATABASE_ prefixes in: {', '.join(inconsistent_prefixes[:3])}")

            passed = issues_found == 0

            return ValidationResult(
                validation_type=ValidationType.ENVIRONMENT_VARIABLES,
                passed=passed,
                issues_found=issues_found,
                errors=issues_found,
                details=details,
                duration_seconds=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.ENVIRONMENT_VARIABLES,
                passed=False,
                errors=1,
                details=[f"Environment variable validation failed: {e}"],
                duration_seconds=time.time() - start_time
            )

    def _validate_network_configuration(self) -> ValidationResult:
        """Validate network configuration standardization with file correlation."""
        import time
        start_time = time.time()

        try:
            sys.path.insert(0, str(self.project_root / "scripts" / "hardening"))
            from network_standardizer import NetworkStandardizer

            standardizer = NetworkStandardizer()
            analysis = standardizer.analyze_networks()

            issues_found = analysis.issues_found
            passed = issues_found == 0

            details = []
            if analysis.issues:
                details.append(f"⚠️  {issues_found} network configuration issues found")

                # Group issues by file for better correlation
                issues_by_file = {}
                for issue in analysis.issues:
                    file_name = Path(issue.file_path).name
                    service_name = issue.service_name
                    key = f"{service_name}/{file_name}"

                    if key not in issues_by_file:
                        issues_by_file[key] = []
                    issues_by_file[key].append(issue.description)

                # Show file correlation
                for file_key, issue_list in sorted(issues_by_file.items())[:5]:  # Show first 5 files
                    details.append(f"  📁 {file_key}: {len(issue_list)} issues")
                    for issue in issue_list[:2]:  # Show first 2 issues per file
                        details.append(f"    • {issue}")

                    if len(issue_list) > 2:
                        details.append(f"    • ... and {len(issue_list) - 2} more issues")

            return ValidationResult(
                validation_type=ValidationType.NETWORK_CONFIGURATION,
                passed=passed,
                issues_found=issues_found,
                warnings=issues_found,  # Network issues are warnings, not errors
                details=details,
                duration_seconds=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.NETWORK_CONFIGURATION,
                passed=False,
                errors=1,
                details=[f"Network validation failed: {e}"],
                duration_seconds=time.time() - start_time
            )

    def _validate_volume_configuration(self) -> ValidationResult:
        """Validate volume configuration standardization with file correlation."""
        import time
        start_time = time.time()

        try:
            sys.path.insert(0, str(self.project_root / "scripts" / "hardening"))
            from volume_standardizer import VolumeStandardizer

            standardizer = VolumeStandardizer()
            analysis = standardizer.analyze_volumes()

            issues_found = analysis.issues_found
            passed = issues_found == 0

            details = []
            if analysis.issues:
                details.append(f"⚠️  {issues_found} volume configuration issues found")

                # Group issues by file for better correlation
                issues_by_file = {}
                for issue in analysis.issues:
                    file_name = Path(issue.file_path).name
                    service_name = issue.service_name
                    key = f"{service_name}/{file_name}"

                    if key not in issues_by_file:
                        issues_by_file[key] = []
                    issues_by_file[key].append(issue.description)

                # Show file correlation
                for file_key, issue_list in sorted(issues_by_file.items())[:5]:  # Show first 5 files
                    details.append(f"  📁 {file_key}: {len(issue_list)} duplicate mounts")
                    for issue in issue_list[:2]:  # Show first 2 issues per file
                        details.append(f"    • {issue}")

                    if len(issue_list) > 2:
                        details.append(f"    • ... and {len(issue_list) - 2} more duplicates")

            return ValidationResult(
                validation_type=ValidationType.VOLUME_CONFIGURATION,
                passed=passed,
                issues_found=issues_found,
                warnings=issues_found,  # Volume issues are warnings, not critical errors
                details=details,
                duration_seconds=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.VOLUME_CONFIGURATION,
                passed=False,
                errors=1,
                details=[f"Volume validation failed: {e}"],
                duration_seconds=time.time() - start_time
            )

    def _generate_recommendations(self, report: CIValidationReport) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        failed_validations = [r for r in report.results if not r.passed]

        if failed_validations:
            recommendations.append("❌ CRITICAL: Fix all failed validations before merging")

        if report.total_warnings > 0:
            recommendations.append(f"⚠️  Address {report.total_warnings} warnings to improve code quality")

        # Specific recommendations based on failure types
        if any(r.validation_type == ValidationType.CONFIGURATION_STANDARDIZATION and not r.passed
               for r in report.results):
            recommendations.append("🔧 Run configuration standardization tools to fix config issues")

        if any(r.validation_type == ValidationType.DOCKER_VALIDATION and not r.passed
               for r in report.results):
            recommendations.append("🐳 Fix Docker Compose syntax errors and dependency issues")

        if any(r.validation_type == ValidationType.DEPENDENCY_VALIDATION and not r.passed
               for r in report.results):
            recommendations.append("🔗 Add missing service dependencies for proper startup")

        if any(r.validation_type == ValidationType.PORT_CONFLICT_CHECK and not r.passed
               for r in report.results):
            recommendations.append("🚫 CRITICAL: Resolve ALL port conflicts - no exceptions allowed")

        recommendations.extend([
            "Run full validation suite locally before pushing",
            "Review CI/CD pipeline for additional validation steps",
            "Consider adding pre-commit hooks for basic validation"
        ])

        return recommendations

    def _print_final_report(self, report: CIValidationReport):
        """Print comprehensive validation report."""
        print("\n" + "=" * 60)
        print("📊 CI/CD VALIDATION REPORT")
        print("=" * 60)

        print(f"Overall Result: {'✅ PASSED' if report.overall_passed else '❌ FAILED'}")
        print(f"Validations Run: {report.validations_run}")
        print(f"Validations Passed: {report.validations_passed}")
        print(f"Total Issues: {report.total_issues}")
        print(f"Total Warnings: {report.total_warnings}")
        print(f"Total Errors: {report.total_errors}")

        print(f"\n🔍 Validation Results:")
        for result in report.results:
            status = "✅" if result.passed else "❌"
            print(f"  {status} {result.validation_type.value.replace('_', ' ').title()}")
            if not result.passed and result.details:
                for detail in result.details[:3]:
                    print(f"     • {detail}")

        if report.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in report.recommendations:
                print(f"  • {rec}")

        print(f"\n{'🎉 All validations passed!' if report.overall_passed else '⚠️  Some validations failed - please review above issues'}")


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="CI/CD Configuration Validation System")
    parser.add_argument('--fail-on-warnings', '-w', action='store_true',
                       help='Fail validation if warnings are found')
    parser.add_argument('--junit-output', '-j', help='Output JUnit XML report to file')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode (less output)')

    args = parser.parse_args()

    validator = CICheckValidator()

    try:
        report = validator.run_full_validation(fail_on_warnings=args.fail_on_warnings)

        # Output JUnit XML if requested
        if args.junit_output:
            validator._output_junit_xml(report, args.junit_output)

        # Exit with appropriate code
        sys.exit(0 if report.overall_passed else 1)

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
