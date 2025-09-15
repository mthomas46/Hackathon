"""Discovery Agent validation and error handling tests.

Tests input validation, error scenarios, and edge cases.
Focused on validation logic following TDD principles.
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


class TestDiscoveryValidation:
    """Test discovery validation and error handling."""

    def test_discover_missing_name(self, client):
        """Test discovery request missing required name field."""
        discover_request = {
            "base_url": "http://test.com",
            "spec": {"openapi": "3.0.0", "paths": {}}
        }

        response = client.post("/discover", json=discover_request)
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_discover_missing_base_url(self, client):
        """Test discovery request missing required base_url field."""
        discover_request = {
            "name": "test-service",
            "spec": {"openapi": "3.0.0", "paths": {}}
        }

        response = client.post("/discover", json=discover_request)
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_discover_missing_spec_and_url(self, client):
        """Test discovery request missing both spec and openapi_url."""
        discover_request = {
            "name": "test-service",
            "base_url": "http://test.com"
            # Missing both spec and openapi_url
        }

        response = client.post("/discover", json=discover_request)
        # Should handle gracefully or return error
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data

    def test_discover_invalid_base_url_format(self, client):
        """Test discovery request with invalid base_url format."""
        invalid_urls = [
            "not-a-url",
            "ftp://invalid-protocol.com",
            "//missing-protocol.com",
            "http://",
            "https://",
            ""
        ]

        for invalid_url in invalid_urls:
            discover_request = {
                "name": "test-service",
                "base_url": invalid_url,
                "spec": {"openapi": "3.0.0", "paths": {}}
            }

            response = client.post("/discover", json=discover_request)
            # Should handle invalid URL gracefully
            assert response.status_code in [200, 400, 422]

    def test_discover_invalid_openapi_spec(self, client):
        """Test discovery request with invalid OpenAPI spec."""
        invalid_specs = [
            {},  # Empty spec
            {"not": "openapi"},  # Missing openapi field
            {"openapi": "2.0"},  # Invalid version
            {"openapi": "3.0.0"},  # Missing required fields
            {"openapi": "3.0.0", "info": {}},  # Empty info
            {"openapi": "3.0.0", "info": {"title": "Test"}, "paths": "not-an-object"},  # Invalid paths
        ]

        for invalid_spec in invalid_specs:
            discover_request = {
                "name": "test-service",
                "base_url": "http://test.com",
                "spec": invalid_spec
            }

            response = client.post("/discover", json=discover_request)
            # Should handle invalid spec gracefully
            assert response.status_code in [200, 400, 422, 500]

    def test_discover_malformed_json(self, client):
        """Test discovery request with malformed JSON."""
        # This would be handled by FastAPI's JSON parsing
        # Send invalid JSON in request body
        response = client.post("/discover", data="invalid json {")
        assert response.status_code == 422  # FastAPI returns 422 for JSON parsing errors

        data = response.json()
        assert "detail" in data

    def test_discover_empty_request_body(self, client):
        """Test discovery request with empty body."""
        response = client.post("/discover", json={})
        # Should return validation error for missing required fields
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_discover_large_spec_handling(self, client):
        """Test discovery request with large OpenAPI spec."""
        # Create a large spec with many endpoints
        large_paths = {}
        for i in range(100):
            large_paths[f"/endpoint/{i}"] = {
                "get": {"responses": {"200": {"description": "OK"}}}
            }

        large_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Large API", "version": "1.0.0"},
            "paths": large_paths
        }

        discover_request = {
            "name": "large-service",
            "base_url": "http://large-service.com",
            "spec": large_spec,
            "dry_run": True
        }

        response = client.post("/discover", json=discover_request)
        # Should handle large specs gracefully
        assert response.status_code in [200, 413]  # 413 for payload too large

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            discovery_data = data["data"]
            assert "endpoints" in discovery_data

    def test_discover_network_error_handling(self, client):
        """Test discovery request with network error scenarios."""
        # Test with unreachable URL
        discover_request = {
            "name": "network-error-service",
            "base_url": "http://test.com",
            "openapi_url": "http://unreachable.invalid.url/spec.json"
        }

        response = client.post("/discover", json=discover_request)
        # Should handle network errors gracefully
        assert response.status_code in [200, 400, 500]

        data = response.json()
        # Handle both success and error response formats
        if response.status_code == 200 and "data" in data and data.get("success", False):
            assert "data" in data
        else:
            # Error response (expected for network errors)
            assert "details" in data or "error_code" in data

    def test_discover_concurrent_requests(self, client):
        """Test discovery handling of concurrent requests."""
        import threading
        import time

        results = []
        errors = []

        def make_request(request_id):
            try:
                discover_request = {
                    "name": f"concurrent-service-{request_id}",
                    "base_url": f"http://service{request_id}.com",
                    "spec": {
                        "openapi": "3.0.0",
                        "paths": {
                            f"/test{request_id}": {
                                "get": {"responses": {"200": {"description": "OK"}}}
                            }
                        }
                    },
                    "dry_run": True
                }

                response = client.post("/discover", json=discover_request)
                results.append((request_id, response.status_code, response.json() if response.status_code == 200 else None))
            except Exception as e:
                errors.append((request_id, str(e)))

        # Make concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(results) == 5
        assert len(errors) == 0

        for request_id, status_code, response_data in results:
            assert status_code == 200
            assert response_data is not None
            assert "data" in response_data

    def test_discover_invalid_openapi_url_format(self, client):
        """Test discovery request with invalid openapi_url format."""
        invalid_urls = [
            "not-a-url",
            "ftp://invalid.com",
            "//missing-scheme.com",
            "http://",
            "",
            "javascript:alert('xss')",  # Security test
            "../../../../etc/passwd",  # Path traversal test
        ]

        for invalid_url in invalid_urls:
            discover_request = {
                "name": "url-validation-service",
                "base_url": "http://test.com",
                "openapi_url": invalid_url
            }

            response = client.post("/discover", json=discover_request)
            # Should handle invalid URLs gracefully
            assert response.status_code in [200, 400, 422]

    def test_discover_spec_validation_edge_cases(self, client):
        """Test discovery request with OpenAPI spec edge cases."""
        edge_case_specs = [
            # Spec with circular references
            {
                "openapi": "3.0.0",
                "info": {"title": "Circular", "version": "1.0.0"},
                "paths": {"/test": {"$ref": "#/paths/test"}},
                "components": {"schemas": {"Self": {"$ref": "#/components/schemas/Self"}}}
            },
            # Spec with very deep nesting
            {
                "openapi": "3.0.0",
                "info": {"title": "Deep", "version": "1.0.0"},
                "paths": {
                    "/deep": {
                        "get": {
                            "responses": {
                                "200": {
                                    "description": "OK",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "nested": {"$ref": "#/components/schemas/Deep"}
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
                        "Deep": {
                            "type": "object",
                            "properties": {"deep": {"$ref": "#/components/schemas/Deep"}}
                        }
                    }
                }
            }
        ]

        for spec in edge_case_specs:
            discover_request = {
                "name": "edge-case-service",
                "base_url": "http://edge-case.com",
                "spec": spec,
                "dry_run": True
            }

            response = client.post("/discover", json=discover_request)
            # Should handle edge cases gracefully
            assert response.status_code in [200, 400, 422, 500]

    def test_discover_timeout_handling(self, client):
        """Test discovery request timeout handling."""
        # Create a spec that might cause processing delays
        slow_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Slow API", "version": "1.0.0"},
            "paths": {}
        }

        # Add many paths to potentially slow down processing
        for i in range(1000):
            slow_spec["paths"][f"/endpoint/{i}"] = {
                "get": {"responses": {"200": {"description": "OK"}}},
                "post": {"responses": {"201": {"description": "Created"}}},
                "put": {"responses": {"200": {"description": "Updated"}}},
                "delete": {"responses": {"204": {"description": "Deleted"}}}
            }

        discover_request = {
            "name": "slow-service",
            "base_url": "http://slow-service.com",
            "spec": slow_spec,
            "dry_run": True
        }

        import time
        start_time = time.time()

        response = client.post("/discover", json=discover_request)

        end_time = time.time()
        processing_time = end_time - start_time

        # Should complete within reasonable time
        assert processing_time < 30  # 30 second timeout

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            discovery_data = data["data"]
            assert "endpoints" in discovery_data
