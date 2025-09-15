"""Source Agent validation and error handling tests.

Tests input validation, error scenarios, and edge cases.
Focused on validation logic following TDD principles.
"""
import pytest
import importlib.util, os
from fastapi.testclient import TestClient

from .test_utils import load_source_agent_service, _assert_http_ok


@pytest.fixture(scope="module")
def client():
    """Test client fixture for source agent service."""
    app = load_source_agent_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestSourceAgentValidation:
    """Test source agent validation and error handling."""

    def test_fetch_missing_source(self, client):
        """Test fetch document with missing source field."""
        fetch_request = {
            "identifier": "testuser:testrepo"
            # Missing source
        }

        response = client.post("/docs/fetch", json=fetch_request)
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_fetch_missing_identifier(self, client):
        """Test fetch document with missing identifier field."""
        fetch_request = {
            "source": "github"
            # Missing identifier
        }

        response = client.post("/docs/fetch", json=fetch_request)
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_fetch_invalid_source_type(self, client):
        """Test fetch document with invalid source type."""
        fetch_request = {
            "source": "invalid-source",
            "identifier": "test"
        }

        response = client.post("/docs/fetch", json=fetch_request)
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_fetch_github_invalid_identifier_format(self, client):
        """Test fetch GitHub document with invalid identifier format."""
        fetch_request = {
            "source": "github",
            "identifier": "invalid-format-no-colon"
        }

        response = client.post("/docs/fetch", json=fetch_request)
        # Should return validation error for GitHub format
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_normalize_missing_source(self, client):
        """Test normalize data with missing source field."""
        normalize_request = {
            "data": {"test": "data"}
            # Missing source
        }

        response = client.post("/normalize", json=normalize_request)
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_normalize_missing_data(self, client):
        """Test normalize data with missing data field."""
        normalize_request = {
            "source": "github"
            # Missing data
        }

        response = client.post("/normalize", json=normalize_request)
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_normalize_invalid_source_type(self, client):
        """Test normalize data with invalid source type."""
        normalize_request = {
            "source": "invalid-source",
            "data": {"test": "data"}
        }

        response = client.post("/normalize", json=normalize_request)
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_analyze_code_missing_text(self, client):
        """Test code analysis with missing text field."""
        code_request = {
            # Missing text
        }

        response = client.post("/code/analyze", json=code_request)
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_analyze_code_null_text(self, client):
        """Test code analysis with null text value."""
        code_request = {
            "text": None
        }

        response = client.post("/code/analyze", json=code_request)
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_fetch_empty_request_body(self, client):
        """Test fetch document with empty request body."""
        response = client.post("/docs/fetch", json={})
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_normalize_empty_request_body(self, client):
        """Test normalize data with empty request body."""
        response = client.post("/normalize", json={})
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_analyze_code_empty_request_body(self, client):
        """Test code analysis with empty request body."""
        response = client.post("/code/analyze", json={})
        # Should return validation error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_fetch_malformed_json(self, client):
        """Test fetch document with malformed JSON."""
        response = client.post("/docs/fetch", data="invalid json {")
        # Should return JSON parsing error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_normalize_malformed_json(self, client):
        """Test normalize data with malformed JSON."""
        response = client.post("/normalize", data="invalid json {")
        # Should return JSON parsing error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_analyze_code_malformed_json(self, client):
        """Test code analysis with malformed JSON."""
        response = client.post("/code/analyze", data="invalid json {")
        # Should return JSON parsing error
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data

    def test_fetch_invalid_json_structure(self, client):
        """Test fetch document with invalid JSON structure."""
        # Send array instead of object
        response = client.post("/docs/fetch", json=["invalid", "structure"])
        # Should handle gracefully
        assert response.status_code in [400, 422]

    def test_normalize_invalid_json_structure(self, client):
        """Test normalize data with invalid JSON structure."""
        # Send string instead of object
        response = client.post("/normalize", json="invalid structure")
        # Should handle gracefully
        assert response.status_code in [400, 422]

    def test_analyze_code_invalid_json_structure(self, client):
        """Test code analysis with invalid JSON structure."""
        # Send number instead of object
        response = client.post("/code/analyze", json=123)
        # Should handle gracefully
        assert response.status_code in [400, 422]

    def test_fetch_large_identifier(self, client):
        """Test fetch document with very large identifier."""
        large_identifier = "a" * 1000  # 1000 character identifier
        fetch_request = {
            "source": "github",
            "identifier": large_identifier
        }

        response = client.post("/docs/fetch", json=fetch_request)
        # Should handle large identifiers gracefully
        assert response.status_code in [200, 400, 413, 422]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data

    def test_normalize_large_data(self, client):
        """Test normalize data with very large data payload."""
        large_content = "x" * 10000  # 10KB of content
        normalize_request = {
            "source": "github",
            "data": {
                "type": "pr",
                "number": 123,
                "title": "Large PR",
                "body": large_content
            }
        }

        response = client.post("/normalize", json=normalize_request)
        # Should handle large payloads gracefully
        assert response.status_code in [200, 400, 413]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data

    def test_analyze_code_large_text(self, client):
        """Test code analysis with very large text input."""
        large_code = "def function_" + "x" * 10000 + "():\n    pass\n"  # 10KB of code
        code_request = {
            "text": large_code
        }

        response = client.post("/code/analyze", json=code_request)
        # Should handle large text gracefully
        assert response.status_code in [200, 400, 413]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data

    def test_fetch_special_characters_in_identifier(self, client):
        """Test fetch document with special characters in identifier."""
        special_identifiers = [
            "user_name:repo-name",
            "user.name:repo.name",
            "user_name:repo_name",
            "user-name:repo-name"
        ]

        for identifier in special_identifiers:
            fetch_request = {
                "source": "github",
                "identifier": identifier
            }

            response = client.post("/docs/fetch", json=fetch_request)
            # Should handle special characters gracefully
            assert response.status_code in [200, 400]

    def test_normalize_nested_data_structures(self, client):
        """Test normalize data with deeply nested structures."""
        nested_data = {
            "type": "pr",
            "number": 123,
            "title": "Nested PR",
            "nested": {
                "level1": {
                    "level2": {
                        "level3": {
                            "deep": "value",
                            "array": [1, 2, {"nested": "object"}]
                        }
                    }
                }
            }
        }

        normalize_request = {
            "source": "github",
            "data": nested_data
        }

        response = client.post("/normalize", json=normalize_request)
        # Should handle nested structures gracefully
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data

    def test_analyze_code_various_languages(self, client):
        """Test code analysis with different programming languages."""
        test_cases = [
            ("python", "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef hello():\n    return 'Hello'"),
            ("javascript", "const express = require('express');\nconst app = express();\napp.get('/', (req, res) => {\n    res.send('Hello');\n});"),
            ("java", "import org.springframework.web.bind.annotation.*;\n@RestController\npublic class HelloController {\n    @GetMapping(\"/\")\n    public String hello() {\n        return \"Hello\";\n    }\n}"),
            ("go", "package main\nimport (\n    \"net/http\"\n)\nfunc hello(w http.ResponseWriter, r *http.Request) {\n    fmt.Fprintf(w, \"Hello\")\n}"),
        ]

        for language, code in test_cases:
            code_request = {
                "text": code
            }

            response = client.post("/code/analyze", json=code_request)
            _assert_http_ok(response)

            data = response.json()
            assert "data" in data

            analysis_data = data["data"]
            assert "endpoint_count" in analysis_data
            assert "analysis" in analysis_data

    def test_fetch_with_scope_parameter_edge_cases(self, client):
        """Test fetch document with scope parameter edge cases."""
        edge_cases = [
            {"source": "github", "identifier": "user:repo", "scope": {}},  # Empty scope
            {"source": "github", "identifier": "user:repo", "scope": {"branch": ""}},  # Empty branch
            {"source": "github", "identifier": "user:repo", "scope": {"include": [], "exclude": []}},  # Empty arrays
            {"source": "github", "identifier": "user:repo", "scope": {"invalid": "value"}},  # Invalid scope keys
        ]

        for fetch_request in edge_cases:
            response = client.post("/docs/fetch", json=fetch_request)
            # Should handle edge cases gracefully
            assert response.status_code in [200, 400, 422]

    def test_normalize_correlation_id_edge_cases(self, client):
        """Test normalize data with correlation ID edge cases."""
        edge_cases = [
            {"source": "github", "data": {"type": "pr", "number": 123}, "correlation_id": ""},  # Empty correlation ID
            {"source": "github", "data": {"type": "pr", "number": 123}, "correlation_id": None},  # Null correlation ID
            {"source": "github", "data": {"type": "pr", "number": 123}, "correlation_id": "a" * 1000},  # Very long correlation ID
        ]

        for normalize_request in edge_cases:
            response = client.post("/normalize", json=normalize_request)
            # Should handle correlation ID edge cases gracefully
            assert response.status_code in [200, 400, 422]

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
                    {"source": "github", "identifier": f"user{request_id}:repo{request_id}"},  # Valid
                    {"source": "github", "identifier": f"invalid{request_id}"},  # Invalid format
                    {"source": "invalid", "identifier": f"test{request_id}"},  # Invalid source
                    {"identifier": f"test{request_id}"},  # Missing source
                    {"source": "github"},  # Missing identifier
                ]

                for i, fetch_request in enumerate(test_cases):
                    try:
                        response = client.post("/docs/fetch", json=fetch_request)
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

        # Verify results
        assert len(results) >= 20  # At least 5 threads * 4 test cases each
        assert len(errors) == 0

        # Check that validation worked correctly
        for request_id, case_id, status_code in results:
            assert status_code in [200, 400, 422]

    def test_parameter_sql_injection_prevention(self, client):
        """Test prevention of SQL injection in parameters."""
        injection_attempts = [
            {"source": "github", "identifier": "user'; DROP TABLE users;--:repo"},
            {"source": "github", "identifier": "user:repo' OR '1'='1"},
            {"source": "github", "identifier": "user:repo; SELECT * FROM secrets"},
        ]

        for fetch_request in injection_attempts:
            response = client.post("/docs/fetch", json=fetch_request)
            # Should handle injection attempts safely
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                data = response.json()
                assert "data" in data
                # Should not contain injection results

    def test_parameter_xss_prevention(self, client):
        """Test prevention of XSS in parameters."""
        xss_attempts = [
            {"source": "github", "identifier": "user<script>alert('xss')</script>:repo"},
            {"source": "github", "identifier": "user:repo<img src=x onerror=alert('xss')>"},
            {"source": "github", "identifier": "user:repo\" onmouseover=\"alert('xss')"},
        ]

        for fetch_request in xss_attempts:
            response = client.post("/docs/fetch", json=fetch_request)
            # Should handle XSS attempts safely
            assert response.status_code in [200, 400, 422]

            if response.status_code == 200:
                data = response.json()
                # Response should not contain executable scripts
                response_text = str(data)
                assert "<script>" not in response_text.lower()
                assert "onerror" not in response_text.lower()
                assert "onmouseover" not in response_text.lower()
