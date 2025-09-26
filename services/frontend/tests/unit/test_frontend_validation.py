"""Frontend Service validation and error handling tests.

Tests input validation, error scenarios, and edge cases.
Focused on validation logic following TDD principles.
"""
import pytest
import importlib.util, os
from fastapi.testclient import TestClient

from .test_utils import load_frontend_service, _assert_http_ok, _assert_html_response


@pytest.fixture(scope="module")
def client():
    """Test client fixture for frontend service."""
    app = load_frontend_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestFrontendValidation:
    """Test frontend validation and error handling."""

    def test_search_empty_query_validation(self, client):
        """Test search validation with empty query."""
        response = client.get("/search?q=")
        # Should handle empty query gracefully
        assert response.status_code in [200, 400]

        if response.status_code == 400:
            data = response.json()
            assert "detail" in data

    def test_search_whitespace_query_validation(self, client):
        """Test search validation with whitespace-only query."""
        response = client.get("/search?q=   ")
        # Should handle whitespace query gracefully
        assert response.status_code in [200, 400]

        if response.status_code == 400:
            data = response.json()
            assert "detail" in data

    def test_search_missing_query_parameter(self, client):
        """Test search with missing query parameter."""
        response = client.get("/search")
        # Should use default value or handle gracefully
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")

    def test_jira_staleness_min_confidence_validation(self, client):
        """Test Jira staleness min_confidence parameter validation."""
        # Test valid confidence values
        valid_confidences = [0.0, 0.5, 0.8, 1.0]
        for confidence in valid_confidences:
            response = client.get(f"/reports/jira/staleness?min_confidence={confidence}")
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

        # Test invalid confidence values
        invalid_confidences = [-0.1, 1.1, 2.0, -1.0]
        for confidence in invalid_confidences:
            response = client.get(f"/reports/jira/staleness?min_confidence={confidence}")
            # Should handle invalid values gracefully
            assert response.status_code in [200, 400]

            if response.status_code == 400:
                data = response.json()
                assert "detail" in data

    def test_jira_staleness_limit_validation(self, client):
        """Test Jira staleness limit parameter validation."""
        # Test valid limit values
        valid_limits = [1, 25, 50, 100, 500, 1000]
        for limit in valid_limits:
            response = client.get(f"/reports/jira/staleness?limit={limit}")
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

        # Test invalid limit values
        invalid_limits = [0, -1, -100, 1001, 10000]
        for limit in invalid_limits:
            response = client.get(f"/reports/jira/staleness?limit={limit}")
            # Should handle invalid values gracefully
            assert response.status_code in [200, 400]

            if response.status_code == 400:
                data = response.json()
                assert "detail" in data

    def test_jira_staleness_min_duplicate_confidence_validation(self, client):
        """Test Jira staleness min_duplicate_confidence parameter validation."""
        # Test valid values
        valid_values = [0.0, 0.3, 0.7, 1.0]
        for value in valid_values:
            response = client.get(f"/reports/jira/staleness?min_duplicate_confidence={value}")
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

        # Test invalid values
        invalid_values = [-0.5, 1.5, 2.0, -1.0]
        for value in invalid_values:
            response = client.get(f"/reports/jira/staleness?min_duplicate_confidence={value}")
            # Should handle invalid values gracefully
            assert response.status_code in [200, 400]

    def test_jira_staleness_summarize_parameter(self, client):
        """Test Jira staleness summarize parameter."""
        # Test both true and false values
        for summarize in [True, False]:
            response = client.get(f"/reports/jira/staleness?summarize={summarize}")
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

        # Test string representations
        for summarize_str in ["true", "false", "True", "False"]:
            response = client.get(f"/reports/jira/staleness?summarize={summarize_str}")
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

    def test_search_query_length_limits(self, client):
        """Test search query length validation."""
        # Test very long query
        long_query = "a" * 1000
        response = client.get(f"/search?q={long_query}")
        # Should handle long queries gracefully
        assert response.status_code in [200, 400, 414]  # 414 URI Too Long

        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")

    def test_search_special_characters_encoding(self, client):
        """Test search with special characters that need URL encoding."""
        special_chars = ["hello world", "test+query", "search&find", "param=value"]
        for query in special_chars:
            encoded_query = query.replace(" ", "%20").replace("&", "%26").replace("=", "%3D")
            response = client.get(f"/search?q={encoded_query}")
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

    def test_multiple_parameters_combination(self, client):
        """Test multiple query parameters in combination."""
        complex_queries = [
            "/reports/jira/staleness?min_confidence=0.5&limit=25&summarize=true",
            "/reports/jira/staleness?min_confidence=0.8&min_duplicate_confidence=0.9&limit=100",
            "/search?q=kubernetes&limit=50",  # Additional params that might be ignored
        ]

        for query in complex_queries:
            response = client.get(query)
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

    def test_parameter_type_conversion(self, client):
        """Test automatic parameter type conversion."""
        # Test string to float conversion
        response = client.get("/reports/jira/staleness?min_confidence=0.75")
        _assert_http_ok(response)
        assert "text/html" in response.headers.get("content-type", "")

        # Test string to int conversion
        response = client.get("/reports/jira/staleness?limit=42")
        _assert_http_ok(response)
        assert "text/html" in response.headers.get("content-type", "")

        # Test invalid type conversion
        response = client.get("/reports/jira/staleness?limit=not-a-number")
        # Should handle type conversion errors gracefully
        assert response.status_code in [200, 400, 422]

    def test_parameter_case_sensitivity(self, client):
        """Test parameter case sensitivity."""
        # Test different cases for boolean parameter
        cases = ["true", "True", "TRUE", "false", "False", "FALSE"]
        for case in cases:
            response = client.get(f"/reports/jira/staleness?summarize={case}")
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

    def test_missing_optional_parameters(self, client):
        """Test endpoints with missing optional parameters."""
        # All parameters in these endpoints are optional with defaults
        endpoints = [
            "/search",  # q has default
            "/reports/jira/staleness",  # all params have defaults
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

    def test_parameter_boundary_values(self, client):
        """Test parameter boundary values."""
        boundary_tests = [
            ("/reports/jira/staleness", "min_confidence", "0"),
            ("/reports/jira/staleness", "min_confidence", "1"),
            ("/reports/jira/staleness", "min_confidence", "1.0"),
            ("/reports/jira/staleness", "limit", "1"),
            ("/reports/jira/staleness", "limit", "1000"),
        ]

        for endpoint, param, value in boundary_tests:
            response = client.get(f"{endpoint}?{param}={value}")
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

    def test_malformed_query_parameters(self, client):
        """Test malformed query parameter handling."""
        malformed_queries = [
            "/search?q=valid&invalid",
            "/search?q=test%ZZ",  # Invalid URL encoding
            "/reports/jira/staleness?min_confidence=0.5&limit=abc&extra=param",
        ]

        for query in malformed_queries:
            response = client.get(query)
            # Should handle malformed queries gracefully
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                assert "text/html" in response.headers.get("content-type", "")

    def test_parameter_injection_prevention(self, client):
        """Test prevention of parameter injection attacks."""
        injection_attempts = [
            "/search?q=<script>alert('xss')</script>",
            "/search?q=../../../etc/passwd",
            "/reports/jira/staleness?limit=1;DROP TABLE users",
            "/search?q=javascript:alert('xss')",
        ]

        for query in injection_attempts:
            response = client.get(query)
            # Should sanitize or reject malicious input
            assert response.status_code in [200, 400, 422]
            # Should still return safe HTML content
            if response.status_code == 200:
                assert "text/html" in response.headers.get("content-type", "")
                # Should not contain unescaped script tags (they should be escaped)
                assert "<script>" not in response.text or "&lt;script&gt;" in response.text
                assert "javascript:" not in response.text

    def test_concurrent_parameter_validation(self, client):
        """Test parameter validation under concurrent requests."""
        import threading
        import time

        results = []
        errors = []

        def make_request_with_params(request_id):
            try:
                # Use different parameter combinations
                params = [
                    f"/search?q=test-{request_id}",
                    f"/reports/jira/staleness?min_confidence=0.{request_id}&limit={10 + request_id}",
                    f"/search?q=concurrent-{request_id}&extra=param",
                ]
                param = params[request_id % len(params)]

                response = client.get(param)
                results.append((request_id, response.status_code, "text/html" in response.headers.get("content-type", "")))
            except Exception as e:
                errors.append((request_id, str(e)))

        # Make concurrent requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request_with_params, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(results) == 10
        assert len(errors) == 0

        for request_id, status_code, is_html in results:
            assert status_code == 200
            assert is_html

    def test_parameter_validation_performance(self, client):
        """Test parameter validation performance."""
        import time

        start_time = time.time()

        # Make multiple validation requests
        for i in range(50):
            response = client.get(f"/reports/jira/staleness?min_confidence=0.{i%10}&limit={(i%10)+1}")
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete within reasonable time (allow some buffer for CI)
        assert total_time < 10  # 10 seconds for 50 requests
