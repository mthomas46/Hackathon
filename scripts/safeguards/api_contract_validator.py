#!/usr/bin/env python3
"""
API Contract Validation System
==============================

Comprehensive system for validating API contracts between services.
Ensures API interfaces remain compatible and detects breaking changes.

Features:
- Automatic API endpoint discovery from OpenAPI/Swagger specs
- Request/response schema validation
- Breaking change detection
- Cross-environment API contract comparison
- Integration with CI/CD pipelines
- Detailed contract validation reports

Author: Ecosystem Hardening Framework
"""

import json
import yaml
import requests
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
import re
from urllib.parse import urljoin, urlparse
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIEndpoint:
    """Represents an API endpoint"""
    service_name: str
    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False


@dataclass
class ContractViolation:
    """Represents an API contract violation"""
    violation_type: str  # "breaking_change", "missing_endpoint", "schema_change", "parameter_change"
    severity: str        # "breaking", "warning", "info"
    service_name: str
    endpoint_path: str
    endpoint_method: str
    description: str
    breaking_change: bool = False
    suggested_fix: str = ""
    old_spec: Optional[Dict[str, Any]] = None
    new_spec: Optional[Dict[str, Any]] = None


@dataclass
class ContractValidationReport:
    """Comprehensive API contract validation report"""
    total_services: int
    total_endpoints: int
    total_violations: int
    breaking_changes: int
    warning_violations: int
    info_violations: int
    services_analyzed: List[str]
    violations_by_service: Dict[str, List[ContractViolation]]
    violations_by_type: Dict[str, List[ContractViolation]]
    recommendations: List[str]
    validation_timestamp: datetime = field(default_factory=datetime.now)
    validation_duration: float = 0.0


class APIContractValidator:
    """
    API Contract Validation System.

    This class provides comprehensive validation of API contracts between services,
    detecting breaking changes and ensuring interface compatibility.
    """

    def __init__(self, workspace_path: Optional[str] = None):
        """Initialize the API contract validator"""
        self.workspace_path = Path(workspace_path or Path.cwd())
        self.services: Dict[str, Dict[str, Any]] = {}
        self.endpoints: Dict[str, List[APIEndpoint]] = {}
        self.violations: List[ContractViolation] = []
        self.reports_dir = self.workspace_path / "reports" / "api_contracts"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Common OpenAPI/Swagger spec file patterns
        self.spec_patterns = [
            "openapi*.yaml", "openapi*.yml", "swagger*.yaml", "swagger*.yml",
            "api*.yaml", "api*.yml", "*.swagger.json", "*.openapi.json",
            "docs/api*.yaml", "docs/swagger*.yaml", "docs/openapi*.yaml"
        ]

        # Breaking change patterns
        self.breaking_change_patterns = {
            "endpoint_removed": "API endpoint has been removed",
            "method_changed": "HTTP method changed for endpoint",
            "parameter_removed": "Required parameter removed from endpoint",
            "parameter_type_changed": "Parameter type changed",
            "response_removed": "Response code removed from endpoint",
            "response_schema_changed": "Response schema changed for successful responses",
            "request_schema_changed": "Request body schema changed"
        }

        logger.info("🔗 API Contract Validator initialized")

    def discover_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover services and their API specifications.

        Returns:
            Dictionary mapping service names to their API specs
        """
        logger.info("🔍 Discovering services and API specifications...")

        services = {}

        # Look for service directories
        services_dir = self.workspace_path / "services"
        if services_dir.exists():
            for service_dir in services_dir.iterdir():
                if service_dir.is_dir() and not service_dir.name.startswith('.'):
                    service_name = service_dir.name
                    api_spec = self._find_api_spec(service_dir)
                    if api_spec:
                        services[service_name] = {
                            "name": service_name,
                            "directory": service_dir,
                            "api_spec": api_spec,
                            "spec_path": api_spec["path"],
                            "spec_format": api_spec["format"]
                        }
                        logger.info(f"✅ Found API spec for service: {service_name}")
                    else:
                        # Try to discover endpoints from running service
                        services[service_name] = {
                            "name": service_name,
                            "directory": service_dir,
                            "api_spec": None,
                            "spec_path": None,
                            "spec_format": None
                        }
                        logger.info(f"⚠️ No API spec found for service: {service_name}")

        self.services = services
        logger.info(f"🔍 Discovered {len(services)} services")
        return services

    def _find_api_spec(self, service_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Find API specification file in service directory.

        Args:
            service_dir: Service directory path

        Returns:
            API spec information or None if not found
        """
        # Look for OpenAPI/Swagger files
        for pattern in self.spec_patterns:
            for spec_file in service_dir.rglob(pattern):
                try:
                    if spec_file.suffix in ['.yaml', '.yml']:
                        with open(spec_file, 'r', encoding='utf-8') as f:
                            spec_content = yaml.safe_load(f)
                    elif spec_file.suffix == '.json':
                        with open(spec_file, 'r', encoding='utf-8') as f:
                            spec_content = json.load(f)

                    if self._is_valid_api_spec(spec_content):
                        return {
                            "path": spec_file,
                            "format": spec_file.suffix[1:],
                            "content": spec_content,
                            "version": spec_content.get("openapi", spec_content.get("swagger", "unknown"))
                        }
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse {spec_file}: {e}")

        # Look for FastAPI-generated OpenAPI endpoint
        openapi_url = self._get_openapi_url_from_service(service_dir)
        if openapi_url:
            try:
                response = requests.get(openapi_url, timeout=10)
                if response.status_code == 200:
                    spec_content = response.json()
                    if self._is_valid_api_spec(spec_content):
                        return {
                            "path": openapi_url,
                            "format": "json",
                            "content": spec_content,
                            "version": spec_content.get("openapi", spec_content.get("swagger", "unknown")),
                            "from_service": True
                        }
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch OpenAPI from {openapi_url}: {e}")

        return None

    def _load_spec_file(self, spec_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load an API specification file.

        Args:
            spec_path: Path to the specification file

        Returns:
            Specification content or None if failed
        """
        try:
            if spec_path.suffix in ['.yaml', '.yml']:
                with open(spec_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            elif spec_path.suffix == '.json':
                with open(spec_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load spec file {spec_path}: {e}")

        return None

    def _is_valid_api_spec(self, spec: Dict[str, Any]) -> bool:
        """Check if content is a valid API specification"""
        # Check for OpenAPI 3.x
        if "openapi" in spec and spec["openapi"].startswith("3."):
            return True

        # Check for Swagger 2.0
        if "swagger" in spec and spec["swagger"] == "2.0":
            return True

        # Check for basic API structure
        if "paths" in spec and isinstance(spec["paths"], dict):
            return True

        return False

    def _get_openapi_url_from_service(self, service_dir: Path) -> Optional[str]:
        """Try to determine OpenAPI URL from service configuration"""
        # Look for main.py or similar entry points
        main_files = ["main.py", "app.py", "server.py", "start.py"]
        for main_file in main_files:
            main_path = service_dir / main_file
            if main_path.exists():
                try:
                    with open(main_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Look for common patterns
                    if "uvicorn" in content and "app" in content:
                        # Likely FastAPI app
                        return f"http://localhost:8000/openapi.json"

                    # Look for port configuration
                    port_match = re.search(r'port\s*=\s*(\d+)', content)
                    if port_match:
                        port = port_match.group(1)
                        return f"http://localhost:{port}/openapi.json"

                except Exception as e:
                    logger.warning(f"⚠️ Failed to analyze {main_file}: {e}")

        return None

    def parse_endpoints(self) -> Dict[str, List[APIEndpoint]]:
        """
        Parse API endpoints from all discovered specifications.

        Returns:
            Dictionary mapping service names to their endpoints
        """
        logger.info("🔍 Parsing API endpoints...")

        endpoints = {}

        for service_name, service_info in self.services.items():
            service_endpoints = []

            if service_info["api_spec"]:
                spec_content = service_info["api_spec"]["content"]

                # Parse OpenAPI/Swagger spec
                if "paths" in spec_content:
                    for path, path_item in spec_content["paths"].items():
                        for method, operation in path_item.items():
                            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                                endpoint = self._parse_operation(
                                    service_name, path, method.upper(), operation, spec_content
                                )
                                service_endpoints.append(endpoint)

            endpoints[service_name] = service_endpoints
            logger.info(f"✅ Parsed {len(service_endpoints)} endpoints for {service_name}")

        self.endpoints = endpoints
        logger.info(f"🔍 Total parsed endpoints: {sum(len(eps) for eps in endpoints.values())}")
        return endpoints

    def _parse_operation(self, service_name: str, path: str, method: str,
                        operation: Dict[str, Any], spec: Dict[str, Any]) -> APIEndpoint:
        """Parse a single API operation"""
        endpoint = APIEndpoint(
            service_name=service_name,
            path=path,
            method=method,
            summary=operation.get("summary"),
            description=operation.get("description"),
            parameters=operation.get("parameters", []),
            responses=operation.get("responses", {}),
            tags=operation.get("tags", []),
            deprecated=operation.get("deprecated", False)
        )

        # Parse request body
        if "requestBody" in operation:
            request_body = operation["requestBody"]
            if "content" in request_body:
                # Take the first content type (usually application/json)
                content_types = list(request_body["content"].keys())
                if content_types:
                    first_content_type = content_types[0]
                    endpoint.request_body = request_body["content"][first_content_type]

        return endpoint

    def validate_contracts(self) -> List[ContractViolation]:
        """
        Validate API contracts across all services.

        Returns:
            List of contract violations found
        """
        logger.info("🔍 Validating API contracts...")

        violations = []

        # Validate contracts between services that communicate
        violations.extend(self._validate_service_interactions())

        # Validate endpoint consistency within services
        violations.extend(self._validate_endpoint_consistency())

        # Validate schema compliance
        violations.extend(self._validate_schema_compliance())

        self.violations = violations
        logger.info(f"🔍 Found {len(violations)} contract violations")
        return violations

    def _validate_service_interactions(self) -> List[ContractViolation]:
        """Validate contracts between services that interact"""
        violations = []

        # This would analyze service dependencies and validate contracts
        # For now, we'll focus on basic endpoint validation
        for service_name, endpoints in self.endpoints.items():
            for endpoint in endpoints:
                violations.extend(self._validate_endpoint_contract(endpoint))

        return violations

    def _validate_endpoint_contract(self, endpoint: APIEndpoint) -> List[ContractViolation]:
        """Validate a single endpoint's contract"""
        violations = []

        # Check for missing required parameters
        for param in endpoint.parameters:
            if param.get("required", False) and not param.get("schema"):
                violations.append(ContractViolation(
                    violation_type="parameter_change",
                    severity="breaking",
                    service_name=endpoint.service_name,
                    endpoint_path=endpoint.path,
                    endpoint_method=endpoint.method,
                    description=f"Required parameter '{param.get('name', 'unknown')}' missing schema",
                    breaking_change=True,
                    suggested_fix="Add schema definition for required parameter"
                ))

        # Check for responses without schemas (for successful responses)
        for status_code, response in endpoint.responses.items():
            if status_code.startswith("2") and "content" in response:
                content_types = list(response["content"].keys())
                if content_types and "application/json" in content_types:
                    json_content = response["content"]["application/json"]
                    if "schema" not in json_content:
                        violations.append(ContractViolation(
                            violation_type="response_schema_changed",
                            severity="warning",
                            service_name=endpoint.service_name,
                            endpoint_path=endpoint.path,
                            endpoint_method=endpoint.method,
                            description=f"Successful response ({status_code}) missing schema",
                            breaking_change=False,
                            suggested_fix="Add response schema for successful responses"
                        ))

        # Check for deprecated endpoints
        if endpoint.deprecated:
            violations.append(ContractViolation(
                violation_type="breaking_change",
                severity="info",
                service_name=endpoint.service_name,
                endpoint_path=endpoint.path,
                endpoint_method=endpoint.method,
                description="Endpoint is marked as deprecated",
                breaking_change=False,
                suggested_fix="Consider removing deprecated endpoint or updating clients"
            ))

        return violations

    def _validate_endpoint_consistency(self) -> List[ContractViolation]:
        """Validate endpoint consistency across similar services"""
        violations = []

        # Group endpoints by path pattern
        path_patterns = {}
        for service_name, endpoints in self.endpoints.items():
            for endpoint in endpoints:
                # Extract base path pattern (remove IDs, etc.)
                base_path = self._extract_base_path(endpoint.path)
                if base_path not in path_patterns:
                    path_patterns[base_path] = []
                path_patterns[base_path].append((service_name, endpoint))

        # Check for inconsistent methods on same paths
        for base_path, service_endpoints in path_patterns.items():
            if len(service_endpoints) > 1:
                methods = set(ep.method for _, ep in service_endpoints)
                if len(methods) > 1:
                    violations.append(ContractViolation(
                        violation_type="breaking_change",
                        severity="warning",
                        service_name="multiple",
                        endpoint_path=base_path,
                        endpoint_method=",".join(methods),
                        description=f"Inconsistent HTTP methods for path pattern '{base_path}'",
                        breaking_change=False,
                        suggested_fix="Standardize HTTP methods across similar endpoints"
                    ))

        return violations

    def _extract_base_path(self, path: str) -> str:
        """Extract base path pattern by removing dynamic parts"""
        # Remove path parameters like /users/{id} -> /users
        base_path = re.sub(r'/{[^}]+}', '', path)
        # Remove query parameters
        base_path = base_path.split('?')[0]
        return base_path

    def _validate_schema_compliance(self) -> List[ContractViolation]:
        """Validate schema compliance and best practices"""
        violations = []

        for service_name, endpoints in self.endpoints.items():
            for endpoint in endpoints:
                # Check for missing operation IDs
                if not hasattr(endpoint, 'operationId') or not endpoint.summary:
                    violations.append(ContractViolation(
                        violation_type="schema_change",
                        severity="info",
                        service_name=endpoint.service_name,
                        endpoint_path=endpoint.path,
                        endpoint_method=endpoint.method,
                        description="Endpoint missing summary or operationId",
                        breaking_change=False,
                        suggested_fix="Add summary and operationId to endpoint"
                    ))

        return violations

    def compare_contracts(self, old_spec: Dict[str, Any], new_spec: Dict[str, Any],
                         service_name: str) -> List[ContractViolation]:
        """
        Compare two API specifications for breaking changes.

        Args:
            old_spec: Previous API specification
            new_spec: New API specification
            service_name: Name of the service

        Returns:
            List of contract violations
        """
        violations = []

        # Compare paths
        old_paths = set(old_spec.get("paths", {}).keys())
        new_paths = set(new_spec.get("paths", {}).keys())

        # Removed endpoints
        removed_paths = old_paths - new_paths
        for path in removed_paths:
            violations.append(ContractViolation(
                violation_type="breaking_change",
                severity="breaking",
                service_name=service_name,
                endpoint_path=path,
                endpoint_method="any",
                description=f"API endpoint '{path}' has been removed",
                breaking_change=True,
                suggested_fix="Restore removed endpoint or provide migration guide"
            ))

        # Compare common endpoints
        common_paths = old_paths & new_paths
        for path in common_paths:
            old_path_spec = old_spec["paths"][path]
            new_path_spec = new_spec["paths"][path]

            path_violations = self._compare_path_spec(path, old_path_spec, new_path_spec, service_name)
            violations.extend(path_violations)

        return violations

    def _compare_path_spec(self, path: str, old_spec: Dict[str, Any],
                          new_spec: Dict[str, Any], service_name: str) -> List[ContractViolation]:
        """Compare path specifications for breaking changes"""
        violations = []

        old_methods = set(old_spec.keys())
        new_methods = set(new_spec.keys())

        # Removed methods
        removed_methods = old_methods - new_methods
        for method in removed_methods:
            violations.append(ContractViolation(
                violation_type="method_changed",
                severity="breaking",
                service_name=service_name,
                endpoint_path=path,
                endpoint_method=method.upper(),
                description=f"HTTP method '{method.upper()}' removed from endpoint '{path}'",
                breaking_change=True,
                suggested_fix="Restore HTTP method or update client code"
            ))

        # Compare common methods
        common_methods = old_methods & new_methods
        for method in common_methods:
            method_violations = self._compare_method_spec(
                path, method, old_spec[method], new_spec[method], service_name
            )
            violations.extend(method_violations)

        return violations

    def _compare_method_spec(self, path: str, method: str, old_spec: Dict[str, Any],
                           new_spec: Dict[str, Any], service_name: str) -> List[ContractViolation]:
        """Compare method specifications for breaking changes"""
        violations = []

        # Compare parameters
        old_params = {p.get("name"): p for p in old_spec.get("parameters", [])}
        new_params = {p.get("name"): p for p in new_spec.get("parameters", [])}

        # Removed required parameters
        for param_name, param_spec in old_params.items():
            if param_spec.get("required", False):
                if param_name not in new_params:
                    violations.append(ContractViolation(
                        violation_type="parameter_removed",
                        severity="breaking",
                        service_name=service_name,
                        endpoint_path=path,
                        endpoint_method=method.upper(),
                        description=f"Required parameter '{param_name}' removed",
                        breaking_change=True,
                        suggested_fix="Restore required parameter or make it optional"
                    ))

        # Changed parameter types
        for param_name in set(old_params.keys()) & set(new_params.keys()):
            old_type = self._extract_param_type(old_params[param_name])
            new_type = self._extract_param_type(new_params[param_name])

            if old_type != new_type:
                violations.append(ContractViolation(
                    violation_type="parameter_type_changed",
                    severity="breaking",
                    service_name=service_name,
                    endpoint_path=path,
                    endpoint_method=method.upper(),
                    description=f"Parameter '{param_name}' type changed: {old_type} -> {new_type}",
                    breaking_change=True,
                    suggested_fix="Revert parameter type or update client code"
                ))

        # Compare responses
        old_responses = old_spec.get("responses", {})
        new_responses = new_spec.get("responses", {})

        # Removed success responses
        old_success_codes = {code for code in old_responses.keys() if code.startswith("2")}
        new_success_codes = {code for code in new_responses.keys() if code.startswith("2")}

        removed_codes = old_success_codes - new_success_codes
        for code in removed_codes:
            violations.append(ContractViolation(
                violation_type="response_removed",
                severity="breaking",
                service_name=service_name,
                endpoint_path=path,
                endpoint_method=method.upper(),
                description=f"Success response code '{code}' removed",
                breaking_change=True,
                suggested_fix="Restore response code or update client expectations"
            ))

        return violations

    def _extract_param_type(self, param_spec: Dict[str, Any]) -> str:
        """Extract parameter type from parameter specification"""
        schema = param_spec.get("schema", {})
        param_type = schema.get("type", "unknown")

        if param_type == "array":
            items = schema.get("items", {})
            item_type = items.get("type", "unknown")
            return f"array[{item_type}]"

        return param_type

    def generate_report(self) -> ContractValidationReport:
        """
        Generate a comprehensive contract validation report.

        Returns:
            ContractValidationReport with detailed analysis
        """
        # Group violations
        violations_by_service = {}
        violations_by_type = {}

        for violation in self.violations:
            # By service
            if violation.service_name not in violations_by_service:
                violations_by_service[violation.service_name] = []
            violations_by_service[violation.service_name].append(violation)

            # By type
            if violation.violation_type not in violations_by_type:
                violations_by_type[violation.violation_type] = []
            violations_by_type[violation.violation_type].append(violation)

        # Count violations by severity
        breaking_changes = sum(1 for v in self.violations if v.breaking_change)
        warning_violations = sum(1 for v in self.violations if v.severity == "warning")
        info_violations = sum(1 for v in self.violations if v.severity == "info")

        # Generate recommendations
        recommendations = self._generate_recommendations()

        # Count total endpoints
        total_endpoints = sum(len(endpoints) for endpoints in self.endpoints.values())

        report = ContractValidationReport(
            total_services=len(self.services),
            total_endpoints=total_endpoints,
            total_violations=len(self.violations),
            breaking_changes=breaking_changes,
            warning_violations=warning_violations,
            info_violations=info_violations,
            services_analyzed=list(self.services.keys()),
            violations_by_service=violations_by_service,
            violations_by_type=violations_by_type,
            recommendations=recommendations
        )

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on violations found"""
        recommendations = []

        if not self.violations:
            recommendations.append("✅ No API contract violations detected - contracts are compatible!")
            return recommendations

        breaking_count = sum(1 for v in self.violations if v.breaking_change)
        if breaking_count > 0:
            recommendations.append(f"🔴 CRITICAL: {breaking_count} breaking changes detected - fix before deployment")

        # Violation type recommendations
        violation_types = set(v.violation_type for v in self.violations)

        if "breaking_change" in violation_types:
            recommendations.append("🔧 Breaking changes found - ensure backward compatibility")
        if "parameter_removed" in violation_types:
            recommendations.append("📝 Required parameters removed - update client code")
        if "response_removed" in violation_types:
            recommendations.append("🔄 Response codes removed - update error handling")
        if "method_changed" in violation_types:
            recommendations.append("⚡ HTTP methods changed - update API calls")

        # General recommendations
        recommendations.extend([
            "📋 Implement API versioning for breaking changes",
            "🔒 Use OpenAPI specifications for all services",
            "🧪 Add contract tests to CI/CD pipeline",
            "📊 Monitor API usage patterns for deprecated endpoints",
            "🔄 Implement gradual migration strategies for breaking changes"
        ])

        return recommendations

    def print_report(self, report: ContractValidationReport, verbose: bool = True):
        """
        Print a formatted contract validation report.

        Args:
            report: ContractValidationReport to print
            verbose: Whether to include detailed violation information
        """
        print("\n" + "="*80)
        print("🔗 API CONTRACT VALIDATION REPORT")
        print("="*80)
        print(f"🏗️  Services Analyzed: {report.total_services}")
        print(f"🔗 Endpoints Found: {report.total_endpoints}")
        print(f"⚠️  Total Violations: {report.total_violations}")
        print(f"🔴 Breaking Changes: {report.breaking_changes}")
        print(f"🟡 Warnings: {report.warning_violations}")
        print(f"ℹ️  Info: {report.info_violations}")

        if verbose and report.violations_by_type:
            print("\n📋 Violations by Type:")
            for violation_type, violations in report.violations_by_type.items():
                print(f"  • {violation_type}: {len(violations)} violations")

        if verbose and report.total_violations > 0:
            print("\n🔍 Top Violations:")
            # Show top 10 most critical violations
            sorted_violations = sorted(
                report.violations_by_service.get("multiple", []) +
                [v for service_violations in report.violations_by_service.values()
                 for v in service_violations if service_violations != "multiple"],
                key=lambda x: (x.breaking_change, {"breaking": 3, "warning": 2, "info": 1}[x.severity]),
                reverse=True
            )

            for i, violation in enumerate(sorted_violations[:10]):
                severity_icon = "🔴" if violation.breaking_change else {"warning": "🟡", "info": "ℹ️"}.get(violation.severity, "❓")
                print(f"  {i+1}. {severity_icon} [{violation.service_name}] {violation.endpoint_method} {violation.endpoint_path}")
                print(f"      {violation.description}")

        if report.recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for rec in report.recommendations:
                print(f"  • {rec}")

        print("="*80)

    def save_report(self, report: ContractValidationReport, filename: Optional[str] = None) -> Path:
        """
        Save contract validation report to JSON file.

        Args:
            report: ContractValidationReport to save
            filename: Optional custom filename

        Returns:
            Path to saved report file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_contract_report_{timestamp}.json"

        report_path = self.reports_dir / filename

        # Convert to serializable format
        report_dict = {
            "total_services": report.total_services,
            "total_endpoints": report.total_endpoints,
            "total_violations": report.total_violations,
            "breaking_changes": report.breaking_changes,
            "warning_violations": report.warning_violations,
            "info_violations": report.info_violations,
            "services_analyzed": report.services_analyzed,
            "validation_timestamp": report.validation_timestamp.isoformat(),
            "validation_duration": report.validation_duration,
            "recommendations": report.recommendations,
            "violations_by_type": {
                violation_type: [{
                    "service_name": v.service_name,
                    "endpoint_path": v.endpoint_path,
                    "endpoint_method": v.endpoint_method,
                    "severity": v.severity,
                    "breaking_change": v.breaking_change,
                    "description": v.description,
                    "suggested_fix": v.suggested_fix
                } for v in violations]
                for violation_type, violations in report.violations_by_type.items()
            }
        }

        with open(report_path, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)

        logger.info(f"💾 Report saved to: {report_path}")
        return report_path


def main():
    """Main entry point for API contract validation"""
    import argparse

    parser = argparse.ArgumentParser(description="API Contract Validator")
    parser.add_argument("--workspace", help="Workspace path")
    parser.add_argument("--service", help="Specific service to validate")
    parser.add_argument("--compare", nargs=2, metavar=("OLD_SPEC", "NEW_SPEC"),
                       help="Compare two API specifications")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--save-report", action="store_true", help="Save detailed report")
    parser.add_argument("--report-file", help="Custom report filename")

    args = parser.parse_args()

    # Initialize validator
    validator = APIContractValidator(args.workspace)

    try:
        print("🔗 API Contract Validator")
        print("=" * 50)

        if args.compare:
            # Compare two specifications
            old_spec_path, new_spec_path = args.compare

            print(f"Comparing specifications:")
            print(f"  Old: {old_spec_path}")
            print(f"  New: {new_spec_path}")

            # Load specifications
            old_spec = validator._load_spec_file(Path(old_spec_path))
            new_spec = validator._load_spec_file(Path(new_spec_path))

            if not old_spec or not new_spec:
                print("❌ Failed to load specifications")
                return 1

            service_name = args.service or "comparison"
            violations = validator.compare_contracts(old_spec, new_spec, service_name)

            print(f"\n🔍 Found {len(violations)} violations:")
            for violation in violations:
                severity_icon = "🔴" if violation.breaking_change else "🟡"
                print(f"  {severity_icon} {violation.description}")

        else:
            # Full ecosystem validation
            # Discover services
            services = validator.discover_services()

            if not services:
                print("❌ No services discovered!")
                return 1

            # Parse endpoints
            endpoints = validator.parse_endpoints()

            # Validate contracts
            violations = validator.validate_contracts()

            # Generate and print report
            report = validator.generate_report()
            validator.print_report(report, args.verbose)

            # Save report if requested
            if args.save_report:
                report_path = validator.save_report(report, args.report_file)
                print(f"💾 Report saved: {report_path}")

            # Return appropriate exit code
            if report.breaking_changes > 0:
                print("❌ CRITICAL: Breaking changes detected")
                return 1
            elif report.warning_violations > 0:
                print("⚠️ WARNING: Contract violations detected")
                return 0
            else:
                print("✅ No critical contract violations")
                return 0

    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
