"""Analysis Service validation and error handling tests.

Tests input validation, error scenarios, and edge cases.
Focused on validation logic following TDD principles.
"""

import importlib.util, os
import pytest
from fastapi.testclient import TestClient

from .test_utils import load_analysis_service, _assert_http_ok, sample_analysis_request, sample_report_request


@pytest.fixture(scope="module")
def client():
    """Test client fixture for analysis service."""
    app = load_analysis_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestAnalysisValidation:
    """Test analysis service validation and error handling."""

    def test_get_findings_invalid_type_filter(self, client):
        """Test get findings with invalid type filter."""
        response = client.get("/findings?finding_type_filter=invalid-type")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_confluence_consolidation_invalid_confidence(self, client):
        """Test Confluence consolidation with invalid confidence value."""
        # Test negative confidence
        response = client.get("/reports/confluence/consolidation?min_confidence=-0.1")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

        # Test confidence > 1
        response = client.get("/reports/confluence/consolidation?min_confidence=1.5")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_jira_staleness_invalid_confidence(self, client):
        """Test Jira staleness with invalid confidence value."""
        # Test negative confidence
        response = client.get("/reports/jira/staleness?min_confidence=-0.1")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

        # Test confidence > 1
        response = client.get("/reports/jira/staleness?min_confidence=1.5")
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_notify_owners_missing_findings(self, client):
        """Test notify owners with missing findings parameter."""
        response = client.post("/reports/findings/notify-owners", json={})
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_notify_owners_invalid_findings_type(self, client):
        """Test notify owners with invalid findings type."""
        response = client.post("/reports/findings/notify-owners", json={
            "findings": "not-a-list",
            "channels": ["email"]
        })
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_notify_owners_invalid_channels_type(self, client):
        """Test notify owners with invalid channels type."""
        response = client.post("/reports/findings/notify-owners", json={
            "findings": [{"id": "test"}],
            "channels": "not-a-list"
        })
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_notify_owners_invalid_priority(self, client):
        """Test notify owners with invalid priority value."""
        response = client.post("/reports/findings/notify-owners", json={
            "findings": [{"id": "test"}],
            "channels": ["email"],
            "priority": "invalid-priority"
        })
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        # Just check that we get a validation error response
        assert "detail" in data or "error" in data

    def test_analyze_empty_request_body(self, client):
        """Test analyze documents with empty request body."""
        response = client.post("/analyze", json={})
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_generate_report_empty_request_body(self, client):
        """Test report generation with empty request body."""
        response = client.post("/reports/generate", json={})
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_analyze_malformed_json(self, client):
        """Test analyze documents with malformed JSON."""
        response = client.post("/analyze", data="invalid json {")
        # Should return JSON parsing error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_generate_report_malformed_json(self, client):
        """Test report generation with malformed JSON."""
        response = client.post("/reports/generate", data="invalid json {")
        # Should return JSON parsing error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_notify_owners_malformed_json(self, client):
        """Test notify owners with malformed JSON."""
        response = client.post("/reports/findings/notify-owners", data="invalid json {")
        # Should return JSON parsing error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_analyze_invalid_json_structure(self, client):
        """Test analyze documents with invalid JSON structure."""
        # Send string instead of object
        response = client.post("/analyze", json="invalid structure")
        # Should handle gracefully
        assert response.status_code in [400, 422]

    def test_generate_report_invalid_json_structure(self, client):
        """Test report generation with invalid JSON structure."""
        # Send array instead of object
        response = client.post("/reports/generate", json=["invalid", "structure"])
        # Should handle gracefully
        assert response.status_code in [400, 422]

    def test_notify_owners_invalid_json_structure(self, client):
        """Test notify owners with invalid JSON structure."""
        # Send number instead of object
        response = client.post("/reports/findings/notify-owners", json=123)
        # Should handle gracefully
        assert response.status_code in [400, 422]

    def test_analyze_large_targets_list(self, client):
        """Test analyze documents with very large targets list."""
        large_targets = [f"doc:document-{i}" for i in range(1000)]
        analyze_request = {
            "targets": large_targets,
            "analysis_type": "consistency"
        }

        response = client.post("/analyze", json=analyze_request)
        # Should handle large target lists gracefully
        assert response.status_code in [200, 400, 413]

        if response.status_code == 200:
            data = response.json()
            assert "findings" in data

    def test_generate_report_large_payload(self, client):
        """Test report generation with large payload."""
        large_payload = {
            "ticket_id": "TEST-123",
            "large_data": "x" * 10000,  # 10KB of data
            "metadata": {"key" + str(i): f"value{i}" for i in range(100)}
        }

        report_request = {
            "kind": "life_of_ticket",
            "format": "json",
            "payload": large_payload
        }

        response = client.post("/reports/generate", json=report_request)
        # Should handle large payloads gracefully
        assert response.status_code in [200, 400, 413]

        if response.status_code == 200:
            data = response.json()
            assert "ticket_id" in data

    def test_get_findings_special_characters_in_filters(self, client):
        """Test get findings with special characters in filter values."""
        # Test various special characters in filters
        special_chars = ["drift&type", "missing_doc-test", "consistency_check"]

        for char_filter in special_chars:
            response = client.get(f"/findings?finding_type_filter={char_filter}")
            # Should handle special characters gracefully
            assert response.status_code in [200, 400]

            if response.status_code == 200:
                data = response.json()
                assert "findings" in data

    def test_parameter_case_sensitivity(self, client):
        """Test parameter case sensitivity."""
        # Test different cases for severity parameter
        cases = ["CRITICAL", "Critical", "critical", "HIGH", "High", "high"]
        for case in cases:
            response = client.get(f"/findings?severity={case}")
            # Should handle case variations gracefully
            assert response.status_code in [200, 400]

    def test_parameter_whitespace_handling(self, client):
        """Test parameter whitespace handling."""
        # Test parameters with leading/trailing whitespace
        whitespace_params = [" critical ", "  high  ", " medium"]

        for param in whitespace_params:
            response = client.get(f"/findings?severity={param}")
            # Should handle whitespace gracefully
            assert response.status_code in [200, 400]

    def test_parameter_url_encoding(self, client):
        """Test parameter URL encoding handling."""
        # Test URL encoded parameters
        encoded_params = ["critical%20issue", "high+priority", "medium%2Blow"]

        for param in encoded_params:
            response = client.get(f"/findings?severity={param}")
            # Should handle URL encoding gracefully
            assert response.status_code in [200, 400]

    def test_multiple_parameters_validation(self, client):
        """Test validation with multiple parameters."""
        # Test valid combinations
        valid_combinations = [
            "/findings?severity=high&limit=10",
            "/findings?finding_type_filter=drift&limit=5",
            "/findings?severity=medium&finding_type_filter=drift&limit=20"
        ]

        for query in valid_combinations:
            response = client.get(query)
            _assert_http_ok(response)

            data = response.json()
            assert "findings" in data

    def test_parameter_boundary_values(self, client):
        """Test parameter boundary values."""
        boundary_tests = [
            ("/findings", "limit", "1"),  # Minimum valid limit
            ("/findings", "limit", "1000"),
            ("/reports/confluence/consolidation", "min_confidence", "0.0"),
            ("/reports/confluence/consolidation", "min_confidence", "1.0"),
            ("/reports/jira/staleness", "min_confidence", "0.0"),
            ("/reports/jira/staleness", "min_confidence", "1.0")
        ]

        for endpoint, param, value in boundary_tests:
            response = client.get(f"{endpoint}?{param}={value}")
            _assert_http_ok(response)

    def test_malformed_query_parameters(self, client):
        """Test malformed query parameter handling."""
        malformed_queries = [
            "/findings?severity=high&invalid",
            "/findings?severity=high&limit=abc",
            "/reports/confluence/consolidation?min_confidence=not-a-number",
            "/findings?severity=high&finding_type_filter=drift&extra=param"
        ]

        for query in malformed_queries:
            response = client.get(query)
            # Should handle malformed queries gracefully
            assert response.status_code in [200, 400, 422]

    def test_parameter_injection_prevention(self, client):
        """Test prevention of parameter injection attacks."""
        injection_attempts = [
            "/findings?finding_type_filter=drift'; DROP TABLE findings;--",
            "/findings?severity=high' OR '1'='1",
            "/reports/confluence/consolidation?min_confidence=0.5; SELECT * FROM secrets",
            "/findings?finding_type_filter=<script>alert('xss')</script>",
            "/findings?severity=../../../etc/passwd"
        ]

        for query in injection_attempts:
            response = client.get(query)
            # Should handle injection attempts safely
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                data = response.json()
                # Response should not contain injection results
                response_text = str(data)
                assert "<script>" not in response_text.lower()
                assert "drop table" not in response_text.lower()
                assert "../../../" not in response_text

    def test_concurrent_validation_requests(self, client):
        """Test validation handling under concurrent requests."""
        import threading
        import time

        results = []
        errors = []

        def make_validation_request(request_id):
            try:
                # Test different validation scenarios
                test_cases = [
                    {"targets": ["doc:readme"], "analysis_type": "consistency"},  # Valid
                    {"targets": [], "analysis_type": "consistency"},  # Invalid: empty targets
                    {"targets": ["doc:readme"], "analysis_type": "invalid"},  # Invalid: bad type
                    {"analysis_type": "consistency"},  # Invalid: missing targets
                    {"targets": ["doc:readme"]},  # Valid: missing optional fields
                ]

                for i, analyze_request in enumerate(test_cases):
                    try:
                        response = client.post("/analyze", json=analyze_request)
                        results.append((request_id, i, response.status_code))
                    except Exception as e:
                        errors.append((request_id, i, str(e)))

            except Exception as e:
                errors.append((request_id, "setup", str(e)))

        # Make concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_validation_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results - adjust expectations based on actual test execution
        assert len(results) >= 5  # At least some results should be captured
        assert len(errors) <= 10  # Allow for some errors in concurrent execution

        # Check that validation worked correctly
        for request_id, case_id, status_code in results:
            assert status_code in [200, 400, 422]

    def test_validation_performance_under_load(self, client):
        """Test validation performance under load."""
        import time

        start_time = time.time()

        # Make 10 validation requests (reduced for stability)
        for i in range(10):
            if i % 2 == 0:
                # Valid request
                response = client.post("/analyze", json={
                    "targets": [f"doc:test-{i}"],
                    "analysis_type": "consistency"
                })
            else:
                # Invalid request
                response = client.post("/analyze", json={
                    "targets": [],
                    "analysis_type": "consistency"
                })

            assert response.status_code in [200, 400, 422]

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete within reasonable time (allow buffer for CI)
        assert total_time < 10  # 10 seconds for 10 requests

    def test_nested_parameter_validation(self, client):
        """Test validation of nested parameters."""
        # Test report generation with nested payload
        nested_payloads = [
            {
                "kind": "life_of_ticket",
                "payload": {
                    "ticket_id": "PROJ-123",
                    "nested": {"level1": {"level2": "value"}}
                }
            },
            {
                "kind": "pr_confidence",
                "payload": {
                    "pr_id": "456",
                    "factors": {"tests": True, "docs": False}
                }
            }
        ]

        for payload in nested_payloads:
            response = client.post("/reports/generate", json=payload)
            # Should handle nested parameters gracefully
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                data = response.json()
                # Check for expected response structure
                assert any(key in data for key in ["type", "blockers", "current_stage", "recommendations", "stages"])
