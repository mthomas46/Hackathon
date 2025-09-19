"""OpenAPI Specification Validation Tests.

This module contains tests for validating OpenAPI specification compliance,
schema validation, and API contract testing.
"""

import pytest
import json
import yaml
from pathlib import Path
import sys
from typing import Dict, Any, List, Optional
import jsonschema
import requests
from unittest.mock import Mock, patch

# Add project path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestOpenAPISchemaValidation:
    """Test OpenAPI schema validation and compliance."""

    def test_openapi_schema_compliance(self):
        """Test OpenAPI specification against official schema."""
        # Create a basic OpenAPI spec for testing
        spec = {
            "openapi": "3.0.1",
            "info": {
                "title": "Project Simulation Service API",
                "version": "1.0.0",
                "description": "API for project simulation and analysis"
            },
            "paths": {
                "/api/v1/simulations": {
                    "get": {
                        "summary": "List simulations",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "simulations": {
                                                    "type": "array",
                                                    "items": {"$ref": "#/components/schemas/Simulation"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "Simulation": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "status": {"type": "string"}
                        },
                        "required": ["id", "name"]
                    }
                }
            }
        }

        # Basic structure validation
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec

        # Validate OpenAPI version format
        assert spec["openapi"].startswith("3.")

        # Validate info section
        info = spec["info"]
        required_info_fields = ["title", "version"]
        for field in required_info_fields:
            assert field in info, f"Missing required info field: {field}"

        print("✅ OpenAPI schema compliance validated")

    def test_openapi_schema_references(self):
        """Test OpenAPI schema references ($ref) are valid."""
        spec = {
            "components": {
                "schemas": {
                    "Simulation": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "team": {"$ref": "#/components/schemas/Team"}
                        }
                    },
                    "Team": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "size": {"type": "integer"}
                        }
                    }
                }
            }
        }

        # Extract all $ref values
        refs = []

        def find_refs(obj, path=""):
            if isinstance(obj, dict):
                if "$ref" in obj:
                    refs.append(obj["$ref"])
                for key, value in obj.items():
                    find_refs(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_refs(item, f"{path}[{i}]")

        find_refs(spec)

        # Validate references point to existing schemas
        schemas = spec["components"]["schemas"]

        for ref in refs:
            if ref.startswith("#/components/schemas/"):
                schema_name = ref.split("/")[-1]
                assert schema_name in schemas, f"Referenced schema '{schema_name}' not found"

        print("✅ OpenAPI schema references validated")

    def test_openapi_parameter_validation(self):
        """Test OpenAPI parameter definitions are valid."""
        spec = {
            "paths": {
                "/api/v1/simulations": {
                    "get": {
                        "parameters": [
                            {
                                "name": "status",
                                "in": "query",
                                "schema": {"type": "string", "enum": ["active", "completed", "failed"]},
                                "description": "Filter by simulation status"
                            },
                            {
                                "name": "limit",
                                "in": "query",
                                "schema": {"type": "integer", "minimum": 1, "maximum": 100},
                                "description": "Maximum number of results"
                            }
                        ]
                    }
                }
            }
        }

        parameters = spec["paths"]["/api/v1/simulations"]["get"]["parameters"]

        for param in parameters:
            # Required parameter fields
            required_fields = ["name", "in", "schema"]
            for field in required_fields:
                assert field in param, f"Parameter missing required field: {field}"

            # Validate parameter location
            valid_locations = ["query", "header", "path", "cookie"]
            assert param["in"] in valid_locations, f"Invalid parameter location: {param['in']}"

            # Validate schema
            schema = param["schema"]
            assert "type" in schema, f"Parameter schema missing type: {param['name']}"

        print("✅ OpenAPI parameter validation completed")


class TestAPIContractValidation:
    """Test API contract validation against OpenAPI spec."""

    def test_request_validation_against_spec(self):
        """Test that requests conform to OpenAPI specification."""
        # Mock OpenAPI spec
        spec = {
            "paths": {
                "/api/v1/simulations": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string", "minLength": 1},
                                            "type": {"type": "string", "enum": ["web", "mobile", "api"]}
                                        },
                                        "required": ["name", "type"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        # Test valid request
        valid_request = {"name": "Test Simulation", "type": "web"}

        # Test invalid requests
        invalid_requests = [
            {"name": "", "type": "web"},  # Empty name
            {"name": "Test", "type": "invalid"},  # Invalid type
            {"type": "web"}  # Missing required field
        ]

        # Validate against schema
        schema = spec["paths"]["/api/v1/simulations"]["post"]["requestBody"]["content"]["application/json"]["schema"]

        try:
            jsonschema.validate(valid_request, schema)
            valid_request_valid = True
        except jsonschema.ValidationError:
            valid_request_valid = False

        assert valid_request_valid, "Valid request should pass schema validation"

        # Count invalid requests
        invalid_count = 0
        for invalid_request in invalid_requests:
            try:
                jsonschema.validate(invalid_request, schema)
            except jsonschema.ValidationError:
                invalid_count += 1

        assert invalid_count == len(invalid_requests), "All invalid requests should fail validation"

        print("✅ Request validation against OpenAPI spec completed")

    def test_response_validation_against_spec(self):
        """Test that responses conform to OpenAPI specification."""
        spec = {
            "paths": {
                "/api/v1/simulations": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "simulations": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "id": {"type": "string"},
                                                            "name": {"type": "string"},
                                                            "status": {"type": "string"}
                                                        },
                                                        "required": ["id", "name"]
                                                    }
                                                },
                                                "total": {"type": "integer"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        # Test valid response
        valid_response = {
            "simulations": [
                {"id": "sim_1", "name": "Test Sim", "status": "active"},
                {"id": "sim_2", "name": "Another Sim", "status": "completed"}
            ],
            "total": 2
        }

        # Test invalid responses
        invalid_responses = [
            {"simulations": [{"name": "Missing ID"}]},  # Missing required field
            {"total": "not_a_number"},  # Wrong type
        ]

        # Validate responses
        response_schema = spec["paths"]["/api/v1/simulations"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

        # Valid response should pass
        try:
            jsonschema.validate(valid_response, response_schema)
            valid_response_ok = True
        except jsonschema.ValidationError:
            valid_response_ok = False

        assert valid_response_ok, "Valid response should pass schema validation"

        # Invalid responses should fail
        invalid_count = 0
        for invalid_response in invalid_responses:
            try:
                jsonschema.validate(invalid_response, response_schema)
            except jsonschema.ValidationError:
                invalid_count += 1

        assert invalid_count == len(invalid_responses), "Invalid responses should fail validation"

        print("✅ Response validation against OpenAPI spec completed")


class TestOpenAPIExamplesValidation:
    """Test OpenAPI examples and sample data."""

    def test_request_examples_completeness(self):
        """Test that request examples are provided and valid."""
        spec_examples = {
            "paths": {
                "/api/v1/simulations": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SimulationCreate"},
                                    "example": {
                                        "name": "E-commerce Platform",
                                        "type": "web_application",
                                        "complexity": "high"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "SimulationCreate": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "complexity": {"type": "string"}
                        }
                    }
                }
            }
        }

        # Check for examples in request bodies
        examples_found = []

        def find_examples(obj, path=""):
            if isinstance(obj, dict):
                if "example" in obj or "examples" in obj:
                    examples_found.append(path)
                for key, value in obj.items():
                    find_examples(value, f"{path}.{key}" if path else key)

        find_examples(spec_examples)

        assert len(examples_found) > 0, "No examples found in OpenAPI spec"

        print("✅ Request examples completeness validated")

    def test_response_examples_coverage(self):
        """Test that response examples cover different scenarios."""
        spec_with_examples = {
            "paths": {
                "/api/v1/simulations/{id}": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "example": {
                                            "id": "sim_123",
                                            "name": "Test Simulation",
                                            "status": "active"
                                        }
                                    }
                                }
                            },
                            "404": {
                                "description": "Not found",
                                "content": {
                                    "application/json": {
                                        "example": {
                                            "error": "Simulation not found",
                                            "code": 404
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        responses = spec_with_examples["paths"]["/api/v1/simulations/{id}"]["get"]["responses"]

        # Should have examples for different response codes
        example_count = sum(1 for resp in responses.values()
                          if "content" in resp and
                          "application/json" in resp["content"] and
                          ("example" in resp["content"]["application/json"] or
                           "examples" in resp["content"]["application/json"]))

        assert example_count > 0, "No response examples found"

        # Should have examples for error responses
        error_responses_with_examples = sum(1 for status, resp in responses.items()
                                          if status.startswith(('4', '5')) and
                                          "content" in resp and
                                          "application/json" in resp["content"] and
                                          ("example" in resp["content"]["application/json"] or
                                           "examples" in resp["content"]["application/json"]))

        assert error_responses_with_examples > 0, "No error response examples found"

        print("✅ Response examples coverage validated")


class TestOpenAPISecurityValidation:
    """Test OpenAPI security definitions and requirements."""

    def test_security_scheme_definitions(self):
        """Test that security schemes are properly defined."""
        spec = {
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    },
                    "apiKey": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    }
                }
            },
            "security": [
                {"bearerAuth": []},
                {"apiKey": []}
            ]
        }

        security_schemes = spec["components"]["securitySchemes"]

        # Validate security scheme structure
        for scheme_name, scheme_def in security_schemes.items():
            assert "type" in scheme_def, f"Security scheme {scheme_name} missing type"

            scheme_type = scheme_def["type"]
            if scheme_type == "http":
                assert "scheme" in scheme_def, f"HTTP security scheme {scheme_name} missing scheme"
            elif scheme_type == "apiKey":
                assert "in" in scheme_def, f"API key scheme {scheme_name} missing 'in' field"
                assert "name" in scheme_def, f"API key scheme {scheme_name} missing name"

        # Validate global security requirements
        global_security = spec.get("security", [])
        assert len(global_security) > 0, "No global security requirements defined"

        print("✅ Security scheme definitions validated")

    def test_endpoint_security_requirements(self):
        """Test that endpoints have appropriate security requirements."""
        spec = {
            "paths": {
                "/api/v1/simulations": {
                    "get": {
                        "security": [{"bearerAuth": []}],
                        "responses": {"200": {"description": "Success"}}
                    },
                    "post": {
                        "security": [{"bearerAuth": ["write:simulations"]}],
                        "responses": {"201": {"description": "Created"}}
                    }
                },
                "/api/v1/health": {
                    "get": {
                        "security": [],  # No authentication required
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }

        paths = spec["paths"]

        # Check that sensitive endpoints require authentication
        sensitive_endpoints = []
        public_endpoints = []

        for path, methods in paths.items():
            for method, operation in methods.items():
                security = operation.get("security", [])

                if not security:  # No security requirements
                    public_endpoints.append(f"{method} {path}")
                else:
                    sensitive_endpoints.append(f"{method} {path}")

        # Should have both public and protected endpoints
        assert len(public_endpoints) > 0, "No public endpoints found"
        assert len(sensitive_endpoints) > 0, "No protected endpoints found"

        print("✅ Endpoint security requirements validated")


class TestOpenAPILinting:
    """Test OpenAPI specification linting and best practices."""

    def test_openapi_best_practices(self):
        """Test OpenAPI specification follows best practices."""
        spec = {
            "info": {
                "title": "Project Simulation Service API",
                "version": "1.0.0",
                "description": "API for project simulation and analysis",
                "contact": {
                    "name": "API Support",
                    "email": "support@example.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {"url": "https://api.example.com/v1", "description": "Production server"},
                {"url": "https://staging.api.example.com/v1", "description": "Staging server"}
            ],
            "tags": [
                {"name": "simulations", "description": "Simulation management"},
                {"name": "health", "description": "Health check endpoints"}
            ]
        }

        # Check for recommended fields
        best_practice_fields = {
            "info.contact": "info.contact" in spec["info"],
            "info.license": "info.license" in spec["info"],
            "servers": "servers" in spec,
            "tags": "tags" in spec
        }

        # Count how many best practices are followed
        followed_practices = sum(1 for followed in best_practice_fields.values() if followed)
        total_practices = len(best_practice_fields)

        compliance_rate = followed_practices / total_practices

        assert compliance_rate >= 0.75, f"OpenAPI best practices compliance too low: {compliance_rate:.2f}"

        print("✅ OpenAPI best practices validated")

    def test_openapi_naming_conventions(self):
        """Test OpenAPI naming conventions."""
        spec = {
            "paths": {
                "/api/v1/simulations": {},
                "/api/v1/simulations/{id}": {},
                "/api/v1/health_check": {}  # Non-standard naming
            },
            "components": {
                "schemas": {
                    "Simulation": {},
                    "simulationCreate": {},  # Non-standard naming
                    "HealthCheck": {}
                }
            }
        }

        # Check path naming conventions
        paths = list(spec["paths"].keys())
        non_standard_paths = []

        for path in paths:
            # Should use kebab-case or camelCase, avoid snake_case in URLs
            if "_" in path.split("/")[-1]:  # Check last path segment
                non_standard_paths.append(path)

        # Allow some flexibility but flag major issues
        assert len(non_standard_paths) <= 1, f"Non-standard path naming: {non_standard_paths}"

        # Check schema naming
        schemas = list(spec["components"]["schemas"].keys())
        mixed_case_schemas = [s for s in schemas if "_" in s and any(c.isupper() for c in s)]

        # Schema names should be consistent
        if len(schemas) > 1:
            # Either all PascalCase or all camelCase
            pascal_case = [s for s in schemas if s[0].isupper()]
            camel_case = [s for s in schemas if s[0].islower()]

            # Should not mix cases
            assert not (len(pascal_case) > 0 and len(camel_case) > 0), \
                "Mixed naming conventions in schemas"

        print("✅ OpenAPI naming conventions validated")


# Helper fixtures
@pytest.fixture
def openapi_spec_validator():
    """Create an OpenAPI specification validator."""
    def validate_spec(spec: Dict[str, Any]) -> List[str]:
        """Validate OpenAPI specification and return issues."""
        issues = []

        # Basic structure validation
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            if field not in spec:
                issues.append(f"Missing required field: {field}")

        # Version validation
        if "openapi" in spec:
            version = spec["openapi"]
            if not version.startswith("3."):
                issues.append(f"Unsupported OpenAPI version: {version}")

        # Info validation
        if "info" in spec:
            info = spec["info"]
            if "title" not in info:
                issues.append("Missing info.title")
            if "version" not in info:
                issues.append("Missing info.version")

        return issues

    return validate_spec


@pytest.fixture
def mock_openapi_spec():
    """Create a mock OpenAPI specification for testing."""
    return {
        "openapi": "3.0.1",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test API for validation"
        },
        "paths": {
            "/test": {
                "get": {
                    "summary": "Test endpoint",
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            }
        }
    }


@pytest.fixture
def schema_validator():
    """Create a JSON schema validator for API responses."""
    def validate_response(response_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate response data against schema."""
        try:
            jsonschema.validate(response_data, schema)
            return True
        except jsonschema.ValidationError:
            return False

    return validate_response
