"""Doc Store API Validation Tests.

Tests for input validation, edge cases, security, and parameter handling
at the API endpoint level. These tests ensure proper error handling and
validation of user inputs.
"""

import pytest
import json
from unittest.mock import patch


@pytest.mark.api
class TestDocumentValidation:
    """Test document endpoint validation."""

    def test_put_document_missing_content(self, client):
        """Test validation when document content is missing."""
        response = client.put("/documents/test-doc-123", json={})
        assert response.status_code == 422  # Validation error

    def test_put_document_empty_content(self, client):
        """Test validation when document content is empty."""
        response = client.put("/documents/test-doc-123", json={"content": ""})
        assert response.status_code == 422  # Validation error

    def test_put_document_content_too_large(self, client):
        """Test validation when document content exceeds size limit."""
        large_content = "x" * 1000001  # Over 1MB limit
        response = client.put("/documents/test-doc-123", json={"content": large_content})
        assert response.status_code == 413  # Payload too large

    def test_get_document_empty_id(self, client):
        """Test validation when document ID is empty."""
        response = client.get("/documents/")
        assert response.status_code == 404  # Not found

    def test_get_document_id_too_long(self, client):
        """Test validation when document ID is too long."""
        long_id = "x" * 256  # Over ID length limit
        response = client.get(f"/documents/{long_id}")
        assert response.status_code == 422  # Validation error

    def test_put_analysis_missing_result(self, client):
        """Test validation when analysis result is missing."""
        response = client.put("/documents/test-doc-123/analysis", json={})
        assert response.status_code == 422  # Validation error

    def test_put_analysis_missing_document_and_content(self, client):
        """Test validation when both document and content are missing."""
        response = client.put("/documents/test-doc-123/analysis", json={"analyzer": "test"})
        assert response.status_code == 422  # Validation error

    def test_put_analysis_result_too_large(self, client):
        """Test validation when analysis result is too large."""
        large_result = {"data": "x" * 1000001}  # Over size limit
        response = client.put("/documents/test-doc-123/analysis",
                            json={"result": large_result})
        assert response.status_code == 413  # Payload too large

    def test_list_documents_invalid_limit(self, client):
        """Test validation when limit parameter is invalid."""
        response = client.get("/documents?limit=-1")
        assert response.status_code == 422  # Validation error

    def test_list_documents_zero_limit(self, client):
        """Test validation when limit parameter is zero."""
        response = client.get("/documents?limit=0")
        assert response.status_code == 422  # Validation error

    def test_search_missing_query(self, client):
        """Test validation when search query is missing."""
        response = client.get("/documents/search")
        assert response.status_code == 422  # Validation error

    def test_search_empty_query(self, client):
        """Test validation when search query is empty."""
        response = client.get("/documents/search?q=")
        assert response.status_code == 422  # Validation error

    def test_search_whitespace_only_query(self, client):
        """Test validation when search query contains only whitespace."""
        response = client.get("/documents/search?q=%20%20%20")
        assert response.status_code == 422  # Validation error

    def test_search_query_too_long(self, client):
        """Test validation when search query is too long."""
        long_query = "x" * 1001  # Over query length limit
        response = client.get(f"/documents/search?q={long_query}")
        assert response.status_code == 422  # Validation error

    def test_search_invalid_limit(self, client):
        """Test validation when search limit is invalid."""
        response = client.get("/documents/search?q=test&limit=1001")
        assert response.status_code == 422  # Validation error

    def test_documents_quality_invalid_stale_threshold(self, client):
        """Test validation when quality stale threshold is invalid."""
        response = client.get("/documents/quality?stale_threshold=-1")
        assert response.status_code == 422  # Validation error

    def test_documents_quality_invalid_min_views(self, client):
        """Test validation when quality min_views is invalid."""
        response = client.get("/documents/quality?min_views=-1")
        assert response.status_code == 422  # Validation error

    def test_patch_metadata_missing_updates(self, client):
        """Test validation when metadata updates are missing."""
        response = client.patch("/documents/test-doc-123/metadata", json={})
        assert response.status_code == 422  # Validation error

    def test_patch_metadata_invalid_updates_type(self, client):
        """Test validation when metadata updates have invalid type."""
        response = client.patch("/documents/test-doc-123/metadata", json={"updates": "invalid"})
        assert response.status_code == 422  # Validation error

    def test_patch_metadata_empty_id(self, client):
        """Test validation when document ID is empty for metadata update."""
        response = client.patch("/documents//metadata", json={"updates": {"key": "value"}})
        assert response.status_code == 422  # Validation error

    def test_list_analyses_document_id_too_long(self, client):
        """Test validation when document ID is too long for analyses list."""
        long_id = "x" * 256
        response = client.get(f"/documents/{long_id}/analyses")
        assert response.status_code == 422  # Validation error

    def test_list_style_examples_language_too_long(self, client):
        """Test validation when language parameter is too long."""
        long_lang = "x" * 101  # Over language length limit
        response = client.get(f"/documents/style-examples?language={long_lang}")
        assert response.status_code == 422  # Validation error

    def test_put_document_malformed_json(self, client):
        """Test handling of malformed JSON in document creation."""
        response = client.put("/documents/test-doc-123",
                            data="invalid json content",
                            headers={"Content-Type": "application/json"})
        assert response.status_code == 400  # Bad request

    def test_put_analysis_malformed_json(self, client):
        """Test handling of malformed JSON in analysis creation."""
        response = client.put("/documents/test-doc-123/analysis",
                            data="invalid json content",
                            headers={"Content-Type": "application/json"})
        assert response.status_code == 400  # Bad request

    def test_patch_metadata_malformed_json(self, client):
        """Test handling of malformed JSON in metadata update."""
        response = client.patch("/documents/test-doc-123/metadata",
                              data="invalid json content",
                              headers={"Content-Type": "application/json"})
        assert response.status_code == 400  # Bad request

    def test_put_document_invalid_json_structure(self, client):
        """Test validation when JSON structure is invalid."""
        response = client.put("/documents/test-doc-123", json={"invalid_field": "value"})
        assert response.status_code == 422  # Validation error

    def test_put_analysis_invalid_json_structure(self, client):
        """Test validation when analysis JSON structure is invalid."""
        response = client.put("/documents/test-doc-123/analysis",
                            json={"invalid_field": "value"})
        assert response.status_code == 422  # Validation error

    def test_patch_metadata_invalid_json_structure(self, client):
        """Test validation when metadata JSON structure is invalid."""
        response = client.patch("/documents/test-doc-123/metadata",
                              json={"invalid_field": "value"})
        assert response.status_code == 422  # Validation error

    def test_put_document_nested_metadata(self, client):
        """Test validation with deeply nested metadata."""
        nested_metadata = {"level1": {"level2": {"level3": "x" * 10000}}}
        response = client.put("/documents/test-doc-123",
                            json={"content": "test", "metadata": nested_metadata})
        assert response.status_code == 413  # Payload too large

    def test_put_analysis_complex_result(self, client):
        """Test validation with complex nested analysis result."""
        complex_result = {"nested": {"deeply": {"nested": "x" * 10000}}}
        response = client.put("/documents/test-doc-123/analysis",
                            json={"result": complex_result})
        assert response.status_code == 413  # Payload too large

    def test_parameter_url_encoding(self, client):
        """Test handling of URL-encoded parameters."""
        response = client.get("/documents/search?q=test%20query")
        # Should handle URL encoding properly
        assert response.status_code in [200, 422]  # Success or validation error

    def test_parameter_case_sensitivity(self, client):
        """Test parameter case sensitivity handling."""
        response = client.get("/documents?Limit=10")  # Wrong case
        assert response.status_code == 422  # Should reject wrong case

    def test_parameter_whitespace_handling(self, client):
        """Test whitespace handling in parameters."""
        response = client.get("/documents/search?q=%20%20test%20%20")
        assert response.status_code in [200, 422]  # Should handle whitespace

    @pytest.mark.slow
    def test_concurrent_validation_requests(self, client):
        """Test validation under concurrent load."""
        import threading
        import time

        results = []
        errors = []

        def make_request():
            try:
                response = client.put("/documents/test-doc-123", json={})
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Create multiple concurrent requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should return validation errors
        assert all(code == 422 for code in results)
        assert len(errors) == 0

    @pytest.mark.slow
    def test_validation_performance_under_load(self, client):
        """Test validation performance under load."""
        import time

        start_time = time.time()

        # Make multiple validation requests
        for i in range(100):
            response = client.put(f"/documents/test-doc-{i}", json={})
            assert response.status_code == 422

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time (adjust threshold as needed)
        assert duration < 10.0  # 10 seconds max for 100 requests

    def test_parameter_injection_prevention(self, client):
        """Test prevention of parameter injection attacks."""
        # Try SQL injection-like parameters
        malicious_queries = [
            "'; DROP TABLE documents; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "javascript:alert('xss')"
        ]

        for query in malicious_queries:
            response = client.get(f"/documents/search?q={query}")
            # Should not execute injection, should validate/sanitize
            assert response.status_code in [200, 422, 400]

    def test_boundary_value_validation(self, client):
        """Test boundary value validation."""
        # Test exact limits
        max_id = "x" * 255  # Maximum ID length
        response = client.get(f"/documents/{max_id}")
        assert response.status_code in [200, 404]  # Valid length

        # Test just over limits
        too_long_id = "x" * 256
        response = client.get(f"/documents/{too_long_id}")
        assert response.status_code == 422  # Too long

    def test_malformed_query_parameters(self, client):
        """Test handling of malformed query parameters."""
        malformed_params = [
            "limit=not_a_number",
            "offset=not_a_number",
            "q[invalid]=syntax",
            "multiple=values&multiple=again"
        ]

        for param in malformed_params:
            response = client.get(f"/documents?{param}")
            assert response.status_code in [200, 422, 400]

    def test_nested_parameter_validation(self, client):
        """Test validation of nested parameters."""
        # Complex nested query parameters
        complex_query = "filter[type]=document&filter[language]=en&sort[field]=created_at&sort[order]=desc"
        response = client.get(f"/documents?{complex_query}")
        assert response.status_code in [200, 422, 400]
