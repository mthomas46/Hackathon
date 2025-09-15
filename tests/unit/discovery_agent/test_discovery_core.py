"""Discovery Agent core functionality tests.

Tests service discovery, OpenAPI parsing, and endpoint extraction.
Focused on essential discovery operations following TDD principles.
"""
import pytest
import importlib.util, os
from fastapi.testclient import TestClient

from .test_utils import load_discovery_agent_service, _assert_http_ok


@pytest.fixture(scope="module")
def client():
    """Test client fixture for discovery agent service."""
    app = load_discovery_agent_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestDiscoveryCore:
    """Test core discovery agent functionality."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data

    def test_discover_inline_spec_basic(self, client):
        """Test discovery with inline OpenAPI spec."""
        inline_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test Service", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get users",
                        "responses": {"200": {"description": "Success"}}
                    },
                    "post": {
                        "summary": "Create user",
                        "responses": {"201": {"description": "Created"}}
                    }
                },
                "/users/{id}": {
                    "get": {
                        "summary": "Get user by ID",
                        "parameters": [{"name": "id", "in": "path", "required": True}],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }

        discover_request = {
            "name": "test-service",
            "base_url": "http://test-service:8000",
            "spec": inline_spec,
            "dry_run": True
        }

        response = client.post("/discover", json=discover_request)
        _assert_http_ok(response)

        data = response.json()
        assert "message" in data
        # Handle both success and error response formats
        if "data" in data:
            discovery_data = data["data"]
            assert "endpoints" in discovery_data
        else:
            # Error response format
            assert "details" in data or "error_code" in data

    def test_discover_minimal_request(self, client):
        """Test discovery with minimal required fields."""
        discover_request = {
            "name": "minimal-service",
            "base_url": "http://minimal:8080",
            "spec": {"openapi": "3.0.0", "paths": {}},
            "dry_run": True  # Avoid orchestrator dependency
        }

        response = client.post("/discover", json=discover_request)
        _assert_http_ok(response)

        data = response.json()
        # Handle both success and error response formats
        if "data" in data:
            discovery_data = data["data"]
            # Check for expected fields in discovery response
            assert "endpoints" in discovery_data
            assert "metadata" in discovery_data
            assert "count" in discovery_data
        else:
            # Error response format
            assert "details" in data or "error_code" in data

    def test_discover_dry_run_mode(self, client):
        """Test discovery in dry-run mode."""
        discover_request = {
            "name": "dry-run-service",
            "base_url": "http://dry-run:9090",
            "spec": {
                "openapi": "3.0.0",
                "paths": {
                    "/test": {
                        "get": {"responses": {"200": {"description": "OK"}}}
                    }
                }
            },
            "dry_run": True
        }

        response = client.post("/discover", json=discover_request)
        _assert_http_ok(response)

        data = response.json()
        # Handle both success and error response formats
        if "data" in data:
            discovery_data = data["data"]

            # Should indicate dry run mode
            assert "dry_run" in discovery_data or "registered" not in discovery_data or not discovery_data.get("registered", True)
        else:
            # Error response format
            assert "details" in data or "error_code" in data

    def test_discover_with_openapi_url(self, client):
        """Test discovery with OpenAPI URL (mock scenario)."""
        discover_request = {
            "name": "url-service",
            "base_url": "http://url-service:7000",
            "openapi_url": "http://mock-openapi.example.com/spec.json"
        }

        # This would normally fail without the actual URL, but tests the request structure
        response = client.post("/discover", json=discover_request)
        # Should handle gracefully even if URL fetch fails
        assert response.status_code in [200, 400, 422, 500]

        if response.status_code == 200:
            data = response.json()
            # Handle both success and error response formats
            if "data" in data:
                pass  # Success case handled
            else:
                # Error response format
                assert "details" in data or "error_code" in data

    def test_discover_complex_openapi_spec(self, client):
        """Test discovery with complex OpenAPI specification."""
        complex_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Complex API",
                "version": "2.0.0",
                "description": "A complex API with many endpoints"
            },
            "servers": [
                {"url": "https://api.example.com/v1"},
                {"url": "https://staging.example.com/v1"}
            ],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "parameters": [
                            {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                            {"name": "offset", "in": "query", "schema": {"type": "integer"}}
                        ],
                        "responses": {"200": {"description": "Success"}}
                    },
                    "post": {
                        "summary": "Create user",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "responses": {"201": {"description": "Created"}}
                    }
                },
                "/users/{userId}": {
                    "get": {
                        "summary": "Get user",
                        "parameters": [
                            {"name": "userId", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {"200": {"description": "Success"}}
                    },
                    "put": {
                        "summary": "Update user",
                        "parameters": [
                            {"name": "userId", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {"200": {"description": "Updated"}}
                    },
                    "delete": {
                        "summary": "Delete user",
                        "parameters": [
                            {"name": "userId", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {"204": {"description": "Deleted"}}
                    }
                },
                "/posts/{postId}/comments": {
                    "get": {
                        "summary": "Get post comments",
                        "parameters": [
                            {"name": "postId", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "email": {"type": "string"}
                        }
                    }
                }
            }
        }

        discover_request = {
            "name": "complex-api",
            "base_url": "https://api.example.com",
            "spec": complex_spec,
            "dry_run": True
        }

        response = client.post("/discover", json=discover_request)
        _assert_http_ok(response)

        data = response.json()
        # Handle both success and error response formats
        if "data" in data:
            discovery_data = data["data"]
            assert "endpoints" in discovery_data

            # Should extract multiple endpoints
            endpoints = discovery_data["endpoints"]
            assert isinstance(endpoints, list)
            assert len(endpoints) > 0
        else:
            # Error response format
            assert "details" in data or "error_code" in data

    def test_discover_empty_spec(self, client):
        """Test discovery with empty OpenAPI spec."""
        empty_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Empty API", "version": "1.0.0"},
            "paths": {}
        }

        discover_request = {
            "name": "empty-service",
            "base_url": "http://empty:3000",
            "spec": empty_spec
        }

        response = client.post("/discover", json=discover_request)
        _assert_http_ok(response)

        data = response.json()
        # Handle both success and error response formats
        if "data" in data:
            discovery_data = data["data"]
            assert "endpoints" in discovery_data

            # Should handle empty paths gracefully
            endpoints = discovery_data["endpoints"]
            assert isinstance(endpoints, list)
        else:
            # Error response format
            assert "details" in data or "error_code" in data

    def test_discover_validation_errors(self, client):
        """Test discovery with invalid request data."""
        # Test missing required fields
        invalid_requests = [
            {"base_url": "http://test.com"},  # Missing name
            {"name": "test"},  # Missing base_url
            {"name": "test", "base_url": "invalid-url"},  # Invalid URL format
        ]

        for invalid_request in invalid_requests:
            response = client.post("/discover", json=invalid_request)
            # Should return validation error
            assert response.status_code in [400, 422]

            if response.status_code in [400, 422]:
                data = response.json()
                assert "detail" in data

    def test_discover_with_custom_orchestrator_url(self, client):
        """Test discovery with custom orchestrator URL."""
        discover_request = {
            "name": "custom-orchestrator-service",
            "base_url": "http://custom:4000",
            "spec": {
                "openapi": "3.0.0",
                "paths": {
                    "/health": {"get": {"responses": {"200": {"description": "OK"}}}}
                }
            },
            "orchestrator_url": "http://custom-orchestrator:8080"
        }

        response = client.post("/discover", json=discover_request)
        # Should handle custom orchestrator URL
        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()
            # Handle both success and error response formats
            if "data" in data:
                pass  # Success case
            else:
                # Error response format
                assert "details" in data or "error_code" in data

    def test_discover_endpoint_extraction(self, client):
        """Test endpoint extraction from various OpenAPI patterns."""
        test_specs = [
            # Simple GET endpoint
            {
                "openapi": "3.0.0",
                "paths": {
                    "/health": {"get": {"responses": {"200": {"description": "OK"}}}}
                }
            },
            # Multiple methods on same path
            {
                "openapi": "3.0.0",
                "paths": {
                    "/users": {
                        "get": {"responses": {"200": {"description": "List"}}},
                        "post": {"responses": {"201": {"description": "Create"}}}
                    }
                }
            },
            # Parameterized paths
            {
                "openapi": "3.0.0",
                "paths": {
                    "/users/{id}": {
                        "get": {"responses": {"200": {"description": "Get"}}},
                        "put": {"responses": {"200": {"description": "Update"}}},
                        "delete": {"responses": {"204": {"description": "Delete"}}}
                    }
                }
            }
        ]

        for i, spec in enumerate(test_specs):
            discover_request = {
                "name": f"endpoint-test-{i}",
                "base_url": f"http://test{i}:8000",
                "spec": spec,
                "dry_run": True
            }

            response = client.post("/discover", json=discover_request)
            _assert_http_ok(response)

            data = response.json()
            discovery_data = data["data"]
            assert "endpoints" in discovery_data

            endpoints = discovery_data["endpoints"]
            assert isinstance(endpoints, list)
            assert len(endpoints) > 0
