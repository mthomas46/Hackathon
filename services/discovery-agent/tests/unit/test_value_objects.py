"""Unit tests for value objects."""

import pytest

import sys
from pathlib import Path

# Add project root to path - navigate up from test file location
# tests/unit/test_value_objects.py -> discovery-agent -> services -> project root
current_dir = Path(__file__).parent  # tests/unit
tests_dir = current_dir.parent       # tests
service_dir = tests_dir.parent       # discovery-agent
services_dir = service_dir.parent    # services
project_root = services_dir.parent   # project root

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(services_dir))

from services.discovery_agent.domain.value_objects import (
    DiscoverySpec, HttpMethod, ApiPath, EndpointMetadata, ServiceMetadata
)
from services.discovery_agent.domain.exceptions import (
    DiscoveryConfigurationError, MalformedUrlError,
    InvalidOpenApiSpecError, UnsupportedApiVersionError
)


class TestDiscoverySpec:
    """Test DiscoverySpec value object."""

    def test_discovery_spec_with_url(self):
        """Test discovery spec with URL."""
        spec = DiscoverySpec(url="https://api.example.com/openapi.json")

        assert spec.url == "https://api.example.com/openapi.json"
        assert spec.content is None
        assert spec.has_url is True
        assert spec.has_content is False

    def test_discovery_spec_with_content(self):
        """Test discovery spec with inline content."""
        content = {"openapi": "3.0.0", "info": {"title": "Test API"}, "paths": {}}
        spec = DiscoverySpec(content=content)

        assert spec.content == content
        assert spec.url is None
        assert spec.has_content is True
        assert spec.has_url is False

    def test_discovery_spec_invalid(self):
        """Test discovery spec with neither URL nor content."""
        with pytest.raises(DiscoveryConfigurationError):
            DiscoverySpec()

    def test_discovery_spec_invalid_url(self):
        """Test discovery spec with invalid URL."""
        with pytest.raises(MalformedUrlError):
            DiscoverySpec(url="invalid-url")

    def test_discovery_spec_invalid_content(self):
        """Test discovery spec with invalid content."""
        with pytest.raises(InvalidOpenApiSpecError):
            DiscoverySpec(content="not a dict")

        with pytest.raises(InvalidOpenApiSpecError):
            DiscoverySpec(content={"invalid": "content"})

    def test_discovery_spec_unsupported_version(self):
        """Test discovery spec with unsupported OpenAPI version."""
        content = {
            "openapi": "2.0.0",
            "info": {"title": "Test API"},
            "paths": {}
        }
        with pytest.raises(UnsupportedApiVersionError):
            DiscoverySpec(content=content)


class TestHttpMethod:
    """Test HttpMethod value object."""

    def test_valid_http_methods(self):
        """Test valid HTTP methods."""
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
            http_method = HttpMethod(method=method)
            assert http_method.method == method

            # Test case insensitivity
            http_method_lower = HttpMethod(method=method.lower())
            assert http_method_lower.method == method.lower()

    def test_invalid_http_method(self):
        """Test invalid HTTP method."""
        with pytest.raises(Exception):  # ValidationError from domain
            HttpMethod(method="INVALID")

    def test_http_method_properties(self):
        """Test HTTP method properties."""
        get_method = HttpMethod(method="GET")
        assert get_method.is_safe is True
        assert get_method.is_idempotent is True

        post_method = HttpMethod(method="POST")
        assert post_method.is_safe is False
        assert post_method.is_idempotent is False


class TestApiPath:
    """Test ApiPath value object."""

    def test_valid_api_paths(self):
        """Test valid API paths."""
        valid_paths = [
            "/api/users",
            "/api/users/{user_id}",
            "/v1/api/test",
            "/"
        ]

        for path in valid_paths:
            api_path = ApiPath(path=path)
            assert api_path.path == path

    def test_invalid_api_paths(self):
        """Test invalid API paths."""
        invalid_paths = [
            "api/users",  # Missing leading slash
            "/api/users with spaces",  # Contains spaces
        ]

        for path in invalid_paths:
            with pytest.raises(Exception):  # ValidationError from domain
                ApiPath(path=path)

    def test_api_path_properties(self):
        """Test API path properties."""
        path = ApiPath(path="/api/users/{user_id}/posts/{post_id}")
        assert path.path_segments == ["api", "users", "{user_id}", "posts", "{post_id}"]
        assert path.has_parameters is True

        simple_path = ApiPath(path="/api/users")
        assert simple_path.path_segments == ["api", "users"]
        assert simple_path.has_parameters is False


class TestEndpointMetadata:
    """Test EndpointMetadata value object."""

    def test_endpoint_metadata_creation(self):
        """Test creating endpoint metadata."""
        metadata = EndpointMetadata(
            operation_id="getUsers",
            deprecated=False,
            security_requirements=[{"api_key": []}]
        )

        assert metadata.operation_id == "getUsers"
        assert metadata.deprecated is False
        assert metadata.security_requirements == [{"api_key": []}]

    def test_endpoint_metadata_from_openapi(self):
        """Test creating metadata from OpenAPI operation."""
        operation = {
            "operationId": "createUser",
            "deprecated": False,
            "security": [{"bearerAuth": []}],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {"type": "object"}
                    }
                }
            },
            "responses": {
                "200": {"description": "Success"},
                "400": {"description": "Bad Request"}
            }
        }

        metadata = EndpointMetadata.from_openapi_operation(operation)

        assert metadata.operation_id == "createUser"
        assert metadata.deprecated is False
        assert metadata.security_requirements == [{"bearerAuth": []}]
        assert metadata.request_body_schema is not None
        assert metadata.response_schemas is not None


class TestServiceMetadata:
    """Test ServiceMetadata value object."""

    def test_service_metadata_creation(self):
        """Test creating service metadata."""
        metadata = ServiceMetadata(
            title="Test API",
            description="A test API service",
            version="1.0.0",
            contact={"name": "API Team", "email": "api@example.com"}
        )

        assert metadata.title == "Test API"
        assert metadata.description == "A test API service"
        assert metadata.version == "1.0.0"
        assert metadata.contact["email"] == "api@example.com"

    def test_service_metadata_from_openapi_info(self):
        """Test creating metadata from OpenAPI info."""
        info = {
            "title": "User Management API",
            "description": "API for managing users",
            "version": "2.1.0",
            "contact": {
                "name": "Support Team",
                "email": "support@example.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        }

        metadata = ServiceMetadata.from_openapi_info(info)

        assert metadata.title == "User Management API"
        assert metadata.description == "API for managing users"
        assert metadata.version == "2.1.0"
        assert metadata.contact["email"] == "support@example.com"
        assert metadata.license["name"] == "MIT"
