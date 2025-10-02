#!/usr/bin/env python3
"""
Production Readiness Validator for Meta-Orchestrator

Integrated production readiness validation from scripts/hardening/validation/production_readiness_validator.py
Provides comprehensive validation of ecosystem production readiness.
"""

import json
import time
import subprocess
import urllib.request
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import yaml
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class ReadinessLevel(Enum):
    """Production readiness levels"""
    PRODUCTION_READY = "production_ready"
    DEVELOPMENT_READY = "development_ready"
    TESTING_READY = "testing_ready"
    NOT_READY = "not_ready"


@dataclass
class ReadinessCheck:
    """Individual readiness check configuration"""
    check_name: str
    category: str
    severity: str  # "critical", "high", "medium", "low"
    description: str
    validation_function: str
    required_for_production: bool = True


@dataclass
class ReadinessResult:
    """Result of a single readiness check"""
    check_name: str
    success: bool
    score: float  # 0.0 to 1.0
    message: str
    details: Optional[Dict[str, Any]] = None
    issues: List[str] = None
    recommendations: List[str] = None


@dataclass
class ProductionReadinessReport:
    """Complete production readiness validation report"""
    overall_readiness: ReadinessLevel
    overall_score: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    critical_failures: int
    results: List[ReadinessResult] = None
    summary: Dict[str, Any] = None
    recommendations: List[str] = None


class ProductionReadinessValidator:
    """Comprehensive production readiness validation system"""

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.readiness_checks = self._load_readiness_checks()

    def _load_readiness_checks(self) -> List[ReadinessCheck]:
        """Load all production readiness checks"""
        return [
            # Infrastructure Readiness
            ReadinessCheck(
                check_name="docker_containers_health",
                category="infrastructure",
                severity="critical",
                description="All Docker containers must be healthy",
                validation_function="validate_docker_health",
                required_for_production=True
            ),
            ReadinessCheck(
                check_name="service_connectivity",
                category="infrastructure",
                severity="critical",
                description="All services must be reachable and responsive",
                validation_function="validate_service_connectivity",
                required_for_production=True
            ),
            ReadinessCheck(
                check_name="port_mappings",
                category="infrastructure",
                severity="high",
                description="Port mappings must be consistent and conflict-free",
                validation_function="validate_port_mappings",
                required_for_production=True
            ),

            # API Readiness
            ReadinessCheck(
                check_name="api_schema_compliance",
                category="api",
                severity="critical",
                description="All API responses must comply with defined schemas",
                validation_function="validate_api_schemas",
                required_for_production=True
            ),
            ReadinessCheck(
                check_name="api_error_handling",
                category="api",
                severity="high",
                description="APIs must handle errors gracefully with proper status codes",
                validation_function="validate_error_handling",
                required_for_production=True
            ),

            # Configuration Readiness
            ReadinessCheck(
                check_name="config_consistency",
                category="configuration",
                severity="high",
                description="Configuration files must be consistent across services",
                validation_function="validate_config_consistency",
                required_for_production=True
            ),
            ReadinessCheck(
                check_name="schema_validation",
                category="configuration",
                severity="low",
                description="Configuration files must comply with JSON schemas",
                validation_function="validate_schema_compliance",
                required_for_production=False
            ),

            # Integration Readiness
            ReadinessCheck(
                check_name="service_dependencies",
                category="integration",
                severity="high",
                description="Service dependencies must be properly configured",
                validation_function="validate_service_dependencies",
                required_for_production=True
            ),
            ReadinessCheck(
                check_name="health_checks",
                category="integration",
                severity="medium",
                description="All services must have proper health checks",
                validation_function="validate_health_checks",
                required_for_production=True
            ),
        ]

    def validate_readiness(self, target_level: ReadinessLevel = ReadinessLevel.DEVELOPMENT_READY) -> ProductionReadinessReport:
        """
        Perform comprehensive production readiness validation.

        Args:
            target_level: Target readiness level to validate against

        Returns:
            Complete readiness validation report
        """
        report = ProductionReadinessReport(
            overall_readiness=ReadinessLevel.NOT_READY,
            overall_score=0.0,
            total_checks=len(self.readiness_checks),
            passed_checks=0,
            failed_checks=0,
            critical_failures=0,
            results=[],
            summary={},
            recommendations=[]
        )

        # Run all checks
        for check in self.readiness_checks:
            result = self._run_readiness_check(check)
            report.results.append(result)

            if result.success:
                report.passed_checks += 1
            else:
                report.failed_checks += 1
                if check.severity == "critical":
                    report.critical_failures += 1

        # Calculate overall score
        report.overall_score = report.passed_checks / report.total_checks if report.total_checks > 0 else 0

        # Determine readiness level
        report.overall_readiness = self._calculate_readiness_level(report, target_level)

        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)

        return report

    def _run_readiness_check(self, check: ReadinessCheck) -> ReadinessResult:
        """Run a single readiness check"""
        result = ReadinessResult(
            check_name=check.check_name,
            success=False,
            score=0.0,
            message="",
            issues=[],
            recommendations=[]
        )

        try:
            # Map function names to actual methods
            func_map = {
                "validate_docker_health": self.validate_docker_health,
                "validate_service_connectivity": self.validate_service_connectivity,
                "validate_port_mappings": self.validate_port_mappings,
                "validate_api_schemas": self.validate_api_schemas,
                "validate_error_handling": self.validate_error_handling,
                "validate_config_consistency": self.validate_config_consistency,
                "validate_schema_compliance": self.validate_schema_compliance,
                "validate_service_dependencies": self.validate_service_dependencies,
                "validate_health_checks": self.validate_health_checks,
            }

            if check.validation_function in func_map:
                check_result = func_map[check.validation_function]()
                result.success = check_result["success"]
                result.score = check_result["score"]
                result.message = check_result["message"]
                result.details = check_result.get("details", {})
                result.issues = check_result.get("issues", [])
                result.recommendations = check_result.get("recommendations", [])
            else:
                result.message = f"Validation function {check.validation_function} not implemented"
                result.issues = ["Unknown validation function"]

        except Exception as e:
            result.message = f"Check failed with error: {str(e)}"
            result.issues = [str(e)]

        return result

    def validate_docker_health(self) -> Dict[str, Any]:
        """Validate Docker container health"""
        result = {
            "success": False,
            "score": 0.0,
            "message": "",
            "issues": [],
            "recommendations": []
        }

        try:
            # Get container status
            process = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if process.returncode != 0:
                result["message"] = "Failed to get Docker Compose status"
                result["issues"] = ["Docker Compose command failed"]
                return result

            # Parse container status (simplified parsing)
            lines = process.stdout.strip().split('\n')
            total_containers = len([l for l in lines if l.strip()])
            healthy_containers = len([l for l in lines if '"State":"running"' in l or '"State":"Up"' in l])

            if total_containers == 0:
                result["message"] = "No containers found"
                result["issues"] = ["No Docker containers are running"]
                return result

            health_ratio = healthy_containers / total_containers
            result["score"] = health_ratio

            if health_ratio >= 0.85:  # 85% healthy threshold
                result["success"] = True
                result["message"] = f"{healthy_containers}/{total_containers} containers healthy"
            else:
                result["message"] = f"Only {healthy_containers}/{total_containers} containers healthy"
                result["issues"] = ["Low container health ratio"]
                result["recommendations"] = [
                    "Check container logs for errors",
                    "Verify service dependencies are met",
                    "Ensure sufficient system resources"
                ]

            result["details"] = {
                "total_containers": total_containers,
                "healthy_containers": healthy_containers,
                "health_ratio": health_ratio
            }

        except subprocess.TimeoutExpired:
            result["message"] = "Docker health check timed out"
            result["issues"] = ["Timeout checking container health"]
        except Exception as e:
            result["message"] = f"Docker health check failed: {str(e)}"
            result["issues"] = [str(e)]

        return result

    def validate_service_connectivity(self) -> Dict[str, Any]:
        """Validate service connectivity and responsiveness"""
        result = {
            "success": False,
            "score": 0.0,
            "message": "",
            "issues": [],
            "recommendations": []
        }

        # Service endpoints to check (simplified - would be loaded from config)
        services = {
            "orchestrator": {"port": 8085, "endpoint": "/health"},
            "doc_store": {"port": 8086, "endpoint": "/health"},
            "analysis-service": {"port": 8087, "endpoint": "/health"},
            "llm-gateway": {"port": 8092, "endpoint": "/health"},
            "discovery-agent": {"port": 8095, "endpoint": "/health"},
            "prompt_store": {"port": 8097, "endpoint": "/health"},
        }

        successful_checks = 0
        total_checks = len(services)

        for service_name, config in services.items():
            try:
                url = f"http://localhost:{config['port']}{config['endpoint']}"
                req = urllib.request.Request(url, method='GET')

                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        successful_checks += 1
                    else:
                        result["issues"].append(f"{service_name}: HTTP {response.status}")

            except urllib.error.URLError as e:
                result["issues"].append(f"{service_name}: Connection failed - {str(e)}")
            except Exception as e:
                result["issues"].append(f"{service_name}: Unexpected error - {str(e)}")

        success_ratio = successful_checks / total_checks if total_checks > 0 else 0
        result["score"] = success_ratio

        if success_ratio >= 0.5:  # 50% connectivity threshold for development
            result["success"] = True
            result["message"] = f"{successful_checks}/{total_checks} services reachable"
        else:
            result["message"] = f"Only {successful_checks}/{total_checks} services reachable"
            result["recommendations"] = [
                "Start missing services",
                "Check service logs for startup errors",
                "Verify port configurations"
            ]

        result["details"] = {
            "total_services": total_checks,
            "reachable_services": successful_checks,
            "connectivity_ratio": success_ratio
        }

        return result

    def validate_port_mappings(self) -> Dict[str, Any]:
        """Validate port mappings are consistent and conflict-free"""
        result = {
            "success": True,
            "score": 1.0,
            "message": "Port mappings validated",
            "issues": [],
            "recommendations": []
        }

        try:
            # Load docker-compose config
            compose_file = self.workspace_path / "docker-compose.dev.yml"
            if not compose_file.exists():
                result["success"] = False
                result["message"] = "docker-compose.dev.yml not found"
                return result

            with open(compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)

            used_ports = set()
            conflicts = []

            if 'services' in compose_config:
                for service_name, service in compose_config['services'].items():
                    if isinstance(service, dict) and 'ports' in service:
                        for port_mapping in service['ports']:
                            if isinstance(port_mapping, str) and ':' in port_mapping:
                                host_port = port_mapping.split(':')[0]
                                try:
                                    port_int = int(host_port)
                                    if port_int in used_ports:
                                        conflicts.append(f"Port {port_int} used by multiple services")
                                    else:
                                        used_ports.add(port_int)
                                except ValueError:
                                    result["issues"].append(f"Invalid port in {service_name}: {host_port}")

            if conflicts:
                result["success"] = False
                result["score"] = 0.0
                result["message"] = f"Found {len(conflicts)} port conflicts"
                result["issues"] = conflicts
                result["recommendations"] = [
                    "Review and resolve port conflicts",
                    "Update service port configurations",
                    "Ensure unique host port assignments"
                ]
            else:
                result["message"] = f"No port conflicts found ({len(used_ports)} unique ports)"

        except Exception as e:
            result["success"] = False
            result["score"] = 0.0
            result["message"] = f"Port validation failed: {str(e)}"
            result["issues"] = [str(e)]

        return result

    def validate_api_schemas(self) -> Dict[str, Any]:
        """Validate API responses comply with schemas"""
        result = {
            "success": True,
            "score": 1.0,
            "message": "API schema validation completed",
            "issues": [],
            "recommendations": []
        }

        # Simplified schema validation - would check actual API responses
        # against predefined schemas
        api_services = [
            {"name": "orchestrator", "port": 8085},
            {"name": "doc_store", "port": 8086},
            {"name": "analysis-service", "port": 8087},
        ]

        schema_compliant = 0
        for service in api_services:
            try:
                # Check if service responds and returns expected JSON structure
                url = f"http://localhost:{service['port']}/health"
                req = urllib.request.Request(url, method='GET')

                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        try:
                            data = json.loads(response.read().decode())
                            # Basic schema check - has required fields
                            if isinstance(data, dict) and ('status' in data or 'healthy' in str(data).lower()):
                                schema_compliant += 1
                            else:
                                result["issues"].append(f"{service['name']}: Unexpected response format")
                        except json.JSONDecodeError:
                            result["issues"].append(f"{service['name']}: Invalid JSON response")
                    else:
                        result["issues"].append(f"{service['name']}: HTTP {response.status}")

            except Exception as e:
                result["issues"].append(f"{service['name']}: {str(e)}")

        compliance_ratio = schema_compliant / len(api_services) if api_services else 1.0
        result["score"] = compliance_ratio

        if compliance_ratio < 0.6:  # 60% schema compliance threshold
            result["success"] = False
            result["message"] = f"Low API schema compliance: {schema_compliant}/{len(api_services)}"
            result["recommendations"] = [
                "Update API responses to match expected schemas",
                "Add proper error response formats",
                "Implement consistent response structures"
            ]

        return result

    def validate_error_handling(self) -> Dict[str, Any]:
        """Validate API error handling"""
        result = {
            "success": True,
            "score": 1.0,
            "message": "Error handling validation completed",
            "issues": [],
            "recommendations": []
        }

        # Test error scenarios
        test_cases = [
            {"service": "doc_store", "port": 8086, "endpoint": "/documents/invalid_id"},
            {"service": "analysis-service", "port": 8087, "endpoint": "/analyze/invalid"},
        ]

        proper_errors = 0
        for test_case in test_cases:
            try:
                url = f"http://localhost:{test_case['port']}{test_case['endpoint']}"
                req = urllib.request.Request(url, method='GET')

                with urllib.request.urlopen(req, timeout=5) as response:
                    if 400 <= response.status < 500:
                        proper_errors += 1
                    else:
                        result["issues"].append(
                            f"{test_case['service']}: Expected 4xx error, got {response.status}"
                        )

            except urllib.error.HTTPError as e:
                if 400 <= e.code < 500:
                    proper_errors += 1
                else:
                    result["issues"].append(
                        f"{test_case['service']}: Unexpected error code {e.code}"
                    )
            except Exception as e:
                result["issues"].append(f"{test_case['service']}: {str(e)}")

        error_ratio = proper_errors / len(test_cases) if test_cases else 1.0
        result["score"] = error_ratio

        if error_ratio < 0.8:  # 80% proper error handling threshold
            result["success"] = False
            result["message"] = f"Poor error handling: {proper_errors}/{len(test_cases)} proper errors"
            result["recommendations"] = [
                "Implement proper HTTP error codes (4xx for client errors)",
                "Add consistent error response formats",
                "Handle edge cases gracefully"
            ]

        return result

    def validate_config_consistency(self) -> Dict[str, Any]:
        """Validate configuration consistency"""
        result = {
            "success": True,
            "score": 1.0,
            "message": "Configuration consistency validated",
            "issues": [],
            "recommendations": []
        }

        # Basic config file existence checks
        required_configs = [
            "docker-compose.dev.yml",
            "services/orchestrator/config.yaml",
            "services/doc_store/config.yaml",
        ]

        missing_configs = []
        for config_file in required_configs:
            config_path = self.workspace_path / config_file
            if not config_path.exists():
                missing_configs.append(config_file)

        if missing_configs:
            result["success"] = False
            result["score"] = 0.0
            result["message"] = f"Missing configuration files: {missing_configs}"
            result["issues"] = missing_configs
            result["recommendations"] = [
                "Create missing configuration files",
                "Ensure all services have proper configuration",
                "Validate configuration file formats"
            ]

        return result

    def validate_schema_compliance(self) -> Dict[str, Any]:
        """Validate configuration schema compliance"""
        result = {
            "success": True,
            "score": 1.0,
            "message": "Schema compliance validated",
            "issues": [],
            "recommendations": []
        }

        # Basic schema validation - would use JSON Schema validation
        # For now, just check YAML syntax
        config_files = [
            "docker-compose.dev.yml",
            "services/orchestrator/config.yaml",
            "services/doc_store/config.yaml",
        ]

        valid_files = 0
        for config_file in config_files:
            config_path = self.workspace_path / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        if config_file.endswith('.yml') or config_file.endswith('.yaml'):
                            yaml.safe_load(f)
                        valid_files += 1
                except Exception as e:
                    result["issues"].append(f"{config_file}: {str(e)}")

        syntax_ratio = valid_files / len(config_files) if config_files else 1.0
        result["score"] = syntax_ratio

        if syntax_ratio < 1.0:
            result["success"] = False
            result["message"] = f"Schema validation issues: {len(result['issues'])} files with problems"
            result["recommendations"] = [
                "Fix YAML/JSON syntax errors",
                "Validate configuration file formats",
                "Use configuration validation tools"
            ]

        return result

    def validate_service_dependencies(self) -> Dict[str, Any]:
        """Validate service dependencies"""
        result = {
            "success": True,
            "score": 1.0,
            "message": "Service dependencies validated",
            "issues": [],
            "recommendations": []
        }

        try:
            # Load docker-compose config
            compose_file = self.workspace_path / "docker-compose.dev.yml"
            if not compose_file.exists():
                result["success"] = False
                result["message"] = "Cannot validate dependencies: docker-compose.dev.yml not found"
                return result

            with open(compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)

            dependency_issues = []

            if 'services' in compose_config:
                for service_name, service in compose_config['services'].items():
                    if isinstance(service, dict) and 'depends_on' in service:
                        depends_on = service['depends_on']
                        if isinstance(depends_on, str):
                            dependency_issues.append(f"{service_name}: depends_on should be a list, not string")
                        elif isinstance(depends_on, list):
                            for dep in depends_on:
                                if dep not in compose_config['services']:
                                    dependency_issues.append(f"{service_name}: depends on unknown service '{dep}'")

            if dependency_issues:
                result["success"] = False
                result["score"] = 0.0
                result["message"] = f"Found {len(dependency_issues)} dependency issues"
                result["issues"] = dependency_issues
                result["recommendations"] = [
                    "Fix dependency declarations in docker-compose.yml",
                    "Ensure all referenced services exist",
                    "Use proper dependency syntax"
                ]

        except Exception as e:
            result["success"] = False
            result["message"] = f"Dependency validation failed: {str(e)}"
            result["issues"] = [str(e)]

        return result

    def validate_health_checks(self) -> Dict[str, Any]:
        """Validate health check configurations"""
        result = {
            "success": True,
            "score": 1.0,
            "message": "Health checks validated",
            "issues": [],
            "recommendations": []
        }

        try:
            # Load docker-compose config
            compose_file = self.workspace_path / "docker-compose.dev.yml"
            if not compose_file.exists():
                result["success"] = False
                result["message"] = "Cannot validate health checks: docker-compose.dev.yml not found"
                return result

            with open(compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)

            services_with_health_checks = 0
            services_without_health_checks = []

            if 'services' in compose_config:
                for service_name, service in compose_config['services'].items():
                    if isinstance(service, dict):
                        if 'healthcheck' in service:
                            services_with_health_checks += 1
                            # Check health check configuration
                            healthcheck = service['healthcheck']
                            if not isinstance(healthcheck, dict):
                                result["issues"].append(f"{service_name}: healthcheck should be a dictionary")
                        else:
                            services_without_health_checks.append(service_name)

            total_services = len(compose_config.get('services', {}))
            health_check_ratio = services_with_health_checks / total_services if total_services > 0 else 1.0

            result["score"] = health_check_ratio
            result["details"] = {
                "total_services": total_services,
                "services_with_health_checks": services_with_health_checks,
                "health_check_ratio": health_check_ratio
            }

            if health_check_ratio < 0.7:  # 70% health check coverage threshold
                result["success"] = False
                result["message"] = f"Low health check coverage: {services_with_health_checks}/{total_services}"
                result["issues"] = [f"Missing health checks: {services_without_health_checks}"]
                result["recommendations"] = [
                    "Add health checks to services without them",
                    "Use appropriate health check endpoints",
                    "Configure proper health check intervals and timeouts"
                ]

        except Exception as e:
            result["success"] = False
            result["message"] = f"Health check validation failed: {str(e)}"
            result["issues"] = [str(e)]

        return result

    def _calculate_readiness_level(self, report: ProductionReadinessReport,
                                 target_level: ReadinessLevel) -> ReadinessLevel:
        """Calculate overall readiness level based on results"""

        # Production ready: All critical checks pass, high score
        if (report.critical_failures == 0 and
            report.overall_score >= 0.9 and
            target_level == ReadinessLevel.PRODUCTION_READY):
            return ReadinessLevel.PRODUCTION_READY

        # Development ready: Most checks pass, reasonable score
        elif (report.critical_failures <= 1 and
              report.overall_score >= 0.7):
            return ReadinessLevel.DEVELOPMENT_READY

        # Testing ready: Basic functionality works
        elif (report.failed_checks <= report.total_checks * 0.3 and
              report.overall_score >= 0.5):
            return ReadinessLevel.TESTING_READY

        else:
            return ReadinessLevel.NOT_READY

    def _generate_summary(self, report: ProductionReadinessReport) -> Dict[str, Any]:
        """Generate summary statistics"""
        summary = {
            "overall_score": report.overall_score,
            "passed_checks": report.passed_checks,
            "failed_checks": report.failed_checks,
            "critical_failures": report.critical_failures,
            "readiness_level": report.overall_readiness.value,
        }

        # Category breakdown
        categories = {}
        for result in report.results:
            if result.check_name in [c.check_name for c in self.readiness_checks]:
                check = next(c for c in self.readiness_checks if c.check_name == result.check_name)
                cat = check.category
                if cat not in categories:
                    categories[cat] = {"total": 0, "passed": 0, "failed": 0}
                categories[cat]["total"] += 1
                if result.success:
                    categories[cat]["passed"] += 1
                else:
                    categories[cat]["failed"] += 1

        summary["categories"] = categories
        return summary

    def _generate_recommendations(self, report: ProductionReadinessReport) -> List[str]:
        """Generate recommendations based on failed checks"""
        recommendations = []

        for result in report.results:
            if not result.success and result.recommendations:
                recommendations.extend(result.recommendations)

        # Remove duplicates and prioritize critical issues
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                unique_recommendations.append(rec)
                seen.add(rec)

        return unique_recommendations[:10]  # Limit to top 10
