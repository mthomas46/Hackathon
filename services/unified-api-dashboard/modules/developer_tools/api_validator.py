"""
API Validator

Comprehensive API validation utilities for OpenAPI specifications,
request/response validation, and API compliance checking.
"""

import json
import jsonschema
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import re
from urllib.parse import urlparse, urljoin

from ..discovery.client import DiscoveryClient
from ..api.catalog import APICatalogManager


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(Enum):
    """Categories of validation checks."""
    SPECIFICATION = "specification"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    BEST_PRACTICES = "best_practices"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: ValidationSeverity
    category: ValidationCategory
    rule: str
    message: str
    path: Optional[str] = None
    line: Optional[int] = None
    suggestion: Optional[str] = None
    documentation_url: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    valid: bool
    issues: List[ValidationIssue]
    score: float  # 0-100, percentage of compliance
    metadata: Dict[str, Any]


class APIValidator:
    """
    Enterprise-grade API validation engine.

    Validates:
    - OpenAPI specification compliance
    - Request/response schemas
    - Security configurations
    - Performance best practices
    - API design standards
    """

    def __init__(self, discovery_client: DiscoveryClient, catalog_manager: APICatalogManager):
        self.discovery_client = discovery_client
        self.catalog_manager = catalog_manager

        # Load validation rules
        self.validation_rules = self._load_validation_rules()

    async def validate_openapi_spec(
        self,
        spec: Dict[str, Any],
        service_name: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate an OpenAPI specification against comprehensive rules.

        Args:
            spec: OpenAPI specification as dict
            service_name: Optional service name for context

        Returns:
            ValidationResult with issues and compliance score
        """
        issues = []

        # Basic structure validation
        issues.extend(self._validate_spec_structure(spec))

        # Schema validation
        issues.extend(self._validate_schemas(spec))

        # Security validation
        issues.extend(self._validate_security(spec))

        # API design validation
        issues.extend(self._validate_api_design(spec))

        # Best practices validation
        issues.extend(self._validate_best_practices(spec))

        # Calculate compliance score
        score = self._calculate_compliance_score(issues)

        return ValidationResult(
            valid=len([i for i in issues if i.severity == ValidationSeverity.ERROR]) == 0,
            issues=issues,
            score=score,
            metadata={
                "service_name": service_name,
                "spec_version": spec.get("openapi", "unknown"),
                "endpoints_count": len(spec.get("paths", {})),
                "schemas_count": len(spec.get("components", {}).get("schemas", {}))
            }
        )

    async def validate_api_request(
        self,
        service_name: str,
        endpoint: str,
        method: str,
        request_data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> ValidationResult:
        """
        Validate an API request against the service specification.

        Args:
            service_name: Name of the service
            endpoint: API endpoint path
            method: HTTP method
            request_data: Request body/data
            headers: Request headers

        Returns:
            ValidationResult for the request
        """
        issues = []

        # Get service specification
        spec = await self._get_service_spec(service_name)
        if not spec:
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SPECIFICATION,
                    rule="spec_not_found",
                    message=f"OpenAPI specification not found for service '{service_name}'"
                )],
                score=0.0,
                metadata={"service_name": service_name}
            )

        # Validate endpoint exists
        if "paths" not in spec or endpoint not in spec["paths"]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SPECIFICATION,
                rule="endpoint_not_found",
                message=f"Endpoint '{endpoint}' not found in specification",
                path=endpoint
            ))
        else:
            path_spec = spec["paths"][endpoint]
            if method.lower() not in path_spec:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SPECIFICATION,
                    rule="method_not_allowed",
                    message=f"Method '{method}' not allowed for endpoint '{endpoint}'",
                    path=f"{endpoint}.{method}"
                ))
            else:
                method_spec = path_spec[method.lower()]
                issues.extend(self._validate_request_parameters(method_spec, request_data))
                issues.extend(self._validate_request_body(method_spec, request_data))

        # Validate headers
        if headers:
            issues.extend(self._validate_request_headers(spec, headers))

        score = self._calculate_compliance_score(issues)

        return ValidationResult(
            valid=len([i for i in issues if i.severity == ValidationSeverity.ERROR]) == 0,
            issues=issues,
            score=score,
            metadata={
                "service_name": service_name,
                "endpoint": endpoint,
                "method": method
            }
        )

    async def validate_api_response(
        self,
        service_name: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_data: Any,
        response_headers: Optional[Dict[str, str]] = None
    ) -> ValidationResult:
        """
        Validate an API response against the service specification.

        Args:
            service_name: Name of the service
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP status code
            response_data: Response body/data
            response_headers: Response headers

        Returns:
            ValidationResult for the response
        """
        issues = []

        # Get service specification
        spec = await self._get_service_spec(service_name)
        if not spec:
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SPECIFICATION,
                    rule="spec_not_found",
                    message=f"OpenAPI specification not found for service '{service_name}'"
                )],
                score=0.0,
                metadata={"service_name": service_name}
            )

        # Get response specification
        method_spec = self._get_method_spec(spec, endpoint, method)
        if not method_spec:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SPECIFICATION,
                rule="method_spec_not_found",
                message=f"Method specification not found for {method} {endpoint}"
            ))
        else:
            response_spec = method_spec.get("responses", {}).get(str(status_code))
            if not response_spec:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.SPECIFICATION,
                    rule="response_not_documented",
                    message=f"Response status {status_code} not documented in specification",
                    suggestion="Add response documentation to OpenAPI spec"
                ))
            else:
                # Validate response schema
                issues.extend(self._validate_response_schema(response_spec, response_data))

            # Validate response headers
            if response_headers:
                issues.extend(self._validate_response_headers(response_spec, response_headers))

        score = self._calculate_compliance_score(issues)

        return ValidationResult(
            valid=len([i for i in issues if i.severity == ValidationSeverity.ERROR]) == 0,
            issues=issues,
            score=score,
            metadata={
                "service_name": service_name,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code
            }
        )

    async def validate_service_compliance(
        self,
        service_name: str,
        check_live_api: bool = False
    ) -> ValidationResult:
        """
        Comprehensive compliance validation for a service.

        Args:
            service_name: Name of the service to validate
            check_live_api: Whether to make live API calls for validation

        Returns:
            Complete compliance validation result
        """
        issues = []

        # Get service info
        service_info = await self.catalog_manager.get_service_details(service_name)
        if not service_info:
            return ValidationResult(
                valid=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SPECIFICATION,
                    rule="service_not_found",
                    message=f"Service '{service_name}' not found in catalog"
                )],
                score=0.0,
                metadata={"service_name": service_name}
            )

        # Validate OpenAPI specification
        spec = service_info.get("openapi_spec")
        if spec:
            spec_result = await self.validate_openapi_spec(spec, service_name)
            issues.extend(spec_result.issues)
        else:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SPECIFICATION,
                rule="missing_openapi_spec",
                message="OpenAPI specification not found",
                suggestion="Generate and publish OpenAPI specification for the service"
            ))

        # Live API validation (if requested)
        if check_live_api and spec:
            live_issues = await self._validate_live_api(service_name, spec)
            issues.extend(live_issues)

        # Health check validation
        health_issues = await self._validate_service_health(service_name)
        issues.extend(health_issues)

        score = self._calculate_compliance_score(issues)

        return ValidationResult(
            valid=len([i for i in issues if i.severity == ValidationSeverity.ERROR]) == 0,
            issues=issues,
            score=score,
            metadata={
                "service_name": service_name,
                "live_api_checked": check_live_api,
                "spec_valid": spec is not None
            }
        )

    def _validate_spec_structure(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate basic OpenAPI specification structure."""
        issues = []

        # Check required fields
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            if field not in spec:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SPECIFICATION,
                    rule="missing_required_field",
                    message=f"Missing required field: {field}",
                    path=f"$.{field}"
                ))

        # Validate OpenAPI version
        if "openapi" in spec:
            version = spec["openapi"]
            if not re.match(r"^3\.\d+\.\d+$", version):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.SPECIFICATION,
                    rule="invalid_openapi_version",
                    message=f"OpenAPI version '{version}' may not be fully supported",
                    suggestion="Use OpenAPI 3.0.x or 3.1.x"
                ))

        # Validate info section
        if "info" in spec:
            info = spec["info"]
            if "title" not in info:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SPECIFICATION,
                    rule="missing_api_title",
                    message="API title is required in info section",
                    path="$.info.title"
                ))

        return issues

    def _validate_schemas(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate JSON schemas in the specification."""
        issues = []

        if "components" not in spec or "schemas" not in spec["components"]:
            return issues

        schemas = spec["components"]["schemas"]

        for schema_name, schema in schemas.items():
            try:
                # Validate schema structure
                jsonschema.Draft7Validator.check_schema(schema)

                # Check for best practices
                if "$ref" in schema and len(schema) > 1:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.BEST_PRACTICES,
                        rule="ref_with_additional_properties",
                        message=f"Schema '{schema_name}' has $ref with additional properties",
                        path=f"$.components.schemas.{schema_name}",
                        suggestion="Use allOf instead of mixing $ref with other properties"
                    ))

            except jsonschema.exceptions.SchemaError as e:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SPECIFICATION,
                    rule="invalid_schema",
                    message=f"Invalid JSON schema for '{schema_name}': {e.message}",
                    path=f"$.components.schemas.{schema_name}"
                ))

        return issues

    def _validate_security(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate security configurations."""
        issues = []

        # Check for security schemes
        if "components" not in spec or "securitySchemes" not in spec["components"]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.SECURITY,
                rule="no_security_schemes",
                message="No security schemes defined",
                suggestion="Define authentication methods in components.securitySchemes"
            ))
        else:
            security_schemes = spec["components"]["securitySchemes"]
            has_https = False

            for scheme_name, scheme in security_schemes.items():
                if scheme.get("type") == "http" and scheme.get("scheme") == "basic":
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.SECURITY,
                        rule="basic_auth_used",
                        message=f"Basic authentication used in scheme '{scheme_name}'",
                        suggestion="Consider using OAuth2, JWT, or API keys instead"
                    ))

                if scheme.get("type") == "apiKey" and scheme.get("in") == "header":
                    has_https = True

        # Check global security requirements
        if "security" in spec:
            for security_req in spec["security"]:
                for scheme_name in security_req.keys():
                    if not self._has_security_scheme(spec, scheme_name):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category=ValidationCategory.SECURITY,
                            rule="undefined_security_scheme",
                            message=f"Security scheme '{scheme_name}' is referenced but not defined",
                            path="$.security"
                        ))

        return issues

    def _validate_api_design(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate API design best practices."""
        issues = []

        if "paths" not in spec:
            return issues

        for path, methods in spec["paths"].items():
            # Check for plural nouns in resource paths
            if path.endswith("/"):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.BEST_PRACTICES,
                    rule="trailing_slash",
                    message=f"Path '{path}' ends with trailing slash",
                    path=f"$.paths.{path}",
                    suggestion="Remove trailing slash from resource paths"
                ))

            for method, operation in methods.items():
                if not isinstance(operation, dict):
                    continue

                # Check operationId
                if "operationId" not in operation:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.BEST_PRACTICES,
                        rule="missing_operation_id",
                        message=f"Missing operationId for {method.upper()} {path}",
                        path=f"$.paths.{path}.{method}.operationId",
                        suggestion="Add unique operationId for each operation"
                    ))

                # Check summary and description
                if "summary" not in operation:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category=ValidationCategory.BEST_PRACTICES,
                        rule="missing_summary",
                        message=f"Missing summary for {method.upper()} {path}",
                        path=f"$.paths.{path}.{method}.summary"
                    ))

        return issues

    def _validate_best_practices(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate general best practices."""
        issues = []

        # Check for version in base path
        servers = spec.get("servers", [])
        for server in servers:
            url = server.get("url", "")
            if "/v1" not in url and "/v2" not in url and "/v3" not in url:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category=ValidationCategory.BEST_PRACTICES,
                    rule="no_version_in_url",
                    message=f"Server URL '{url}' does not contain API version",
                    suggestion="Include version in base URL (e.g., /v1/)"
                ))

        return issues

    def _validate_request_parameters(self, method_spec: Dict[str, Any], request_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate request parameters."""
        issues = []

        parameters = method_spec.get("parameters", [])
        for param in parameters:
            param_name = param.get("name")
            param_required = param.get("required", False)
            param_in = param.get("in")

            if param_required:
                if param_in == "query" and param_name not in request_data:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.SPECIFICATION,
                        rule="missing_required_parameter",
                        message=f"Missing required query parameter: {param_name}",
                        path=f"parameters.{param_name}"
                    ))

        return issues

    def _validate_request_body(self, method_spec: Dict[str, Any], request_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate request body against schema."""
        issues = []

        if "requestBody" not in method_spec:
            return issues

        request_body = method_spec["requestBody"]
        if not request_body.get("required", False):
            return issues

        # Check if request body is provided
        if not request_data:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SPECIFICATION,
                rule="missing_request_body",
                message="Request body is required but not provided"
            ))
            return issues

        # Validate against schema if present
        content = request_body.get("content", {})
        for content_type, media_type in content.items():
            if "schema" in media_type:
                schema = media_type["schema"]
                try:
                    jsonschema.validate(request_data, schema)
                except jsonschema.ValidationError as e:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.SPECIFICATION,
                        rule="request_body_schema_validation",
                        message=f"Request body validation failed: {e.message}",
                        path=e.absolute_path[0] if e.absolute_path else None
                    ))

        return issues

    def _validate_response_schema(self, response_spec: Dict[str, Any], response_data: Any) -> List[ValidationIssue]:
        """Validate response against schema."""
        issues = []

        content = response_spec.get("content", {})
        for content_type, media_type in content.items():
            if "schema" in media_type:
                schema = media_type["schema"]
                try:
                    jsonschema.validate(response_data, schema)
                except jsonschema.ValidationError as e:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.SPECIFICATION,
                        rule="response_schema_validation",
                        message=f"Response validation failed: {e.message}",
                        path=str(e.absolute_path[0]) if e.absolute_path else None
                    ))

        return issues

    def _calculate_compliance_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate compliance score based on issues."""
        if not issues:
            return 100.0

        # Weight issues by severity
        error_weight = 10
        warning_weight = 2
        info_weight = 0.5

        total_penalty = 0
        max_penalty = 100  # Assume 10 errors = 0 score

        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                total_penalty += error_weight
            elif issue.severity == ValidationSeverity.WARNING:
                total_penalty += warning_weight
            elif issue.severity == ValidationSeverity.INFO:
                total_penalty += info_weight

        score = max(0, 100 - (total_penalty / max_penalty * 100))
        return round(score, 1)

    async def _get_service_spec(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get OpenAPI specification for a service."""
        try:
            service_info = await self.catalog_manager.get_service_details(service_name)
            return service_info.get("openapi_spec") if service_info else None
        except Exception:
            return None

    def _get_method_spec(self, spec: Dict[str, Any], endpoint: str, method: str) -> Optional[Dict[str, Any]]:
        """Get method specification from OpenAPI spec."""
        try:
            return spec["paths"][endpoint][method.lower()]
        except KeyError:
            return None

    def _has_security_scheme(self, spec: Dict[str, Any], scheme_name: str) -> bool:
        """Check if a security scheme is defined."""
        try:
            return scheme_name in spec["components"]["securitySchemes"]
        except KeyError:
            return False

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules configuration."""
        # In a real implementation, this would load from a config file
        return {
            "required_fields": ["openapi", "info", "paths"],
            "recommended_security": ["oauth2", "bearer", "apiKey"],
            "max_path_length": 200,
            "max_parameter_count": 10
        }

    async def _validate_live_api(self, service_name: str, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate API by making live calls."""
        issues = []

        # This would make actual HTTP calls to validate the API
        # For now, return empty list as this requires live service endpoints

        return issues

    async def _validate_service_health(self, service_name: str) -> List[ValidationIssue]:
        """Validate service health and availability."""
        issues = []

        # Check if service is registered and healthy
        try:
            services = await self.discovery_client.get_all_services()
            if service_name not in services:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.COMPLIANCE,
                    rule="service_not_registered",
                    message=f"Service '{service_name}' not registered with discovery service"
                ))
        except Exception as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.COMPLIANCE,
                rule="discovery_service_error",
                message=f"Could not check service registration: {str(e)}"
            ))

        return issues

    def _validate_request_headers(self, spec: Dict[str, Any], headers: Dict[str, str]) -> List[ValidationIssue]:
        """Validate request headers."""
        issues = []

        # Check for common security headers
        security_headers = ["authorization", "x-api-key", "x-auth-token"]
        has_auth = any(header.lower() in [h.lower() for h in headers.keys()] for header in security_headers)

        if not has_auth:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.SECURITY,
                rule="no_authentication_header",
                message="No authentication header found in request",
                suggestion="Include Authorization, X-API-Key, or similar header"
            ))

        return issues

    def _validate_response_headers(self, response_spec: Dict[str, Any], headers: Dict[str, str]) -> List[ValidationIssue]:
        """Validate response headers."""
        issues = []

        # Check for CORS headers if applicable
        cors_headers = ["access-control-allow-origin", "access-control-allow-methods"]
        has_cors = any(header.lower() in [h.lower() for h in headers.keys()] for header in cors_headers)

        if has_cors:
            # If CORS headers are present, check they're properly configured
            allow_origin = headers.get("access-control-allow-origin", "").lower()
            if allow_origin == "*":
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.SECURITY,
                    rule="cors_wildcard_origin",
                    message="CORS allows all origins (*) - consider restricting to specific domains",
                    suggestion="Specify allowed origins explicitly instead of using wildcard"
                ))

        return issues
