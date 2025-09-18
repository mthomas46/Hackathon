"""
Comprehensive Interpreter Service Endpoint Tests

Tests for all 18 endpoints of the interpreter service including:
- Health and system endpoints
- Query interpretation and execution  
- Workflow management and templates
- Document generation and persistence
- Provenance tracking and downloads
- Legacy compatibility endpoints
"""

import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from typing import Dict, Any, List

# Import test utilities
from .test_utils import load_interpreter_service, _assert_http_ok


@pytest.fixture(scope="module")
def client():
    """Test client fixture for interpreter service."""
    app = load_interpreter_service()
    return TestClient(app)


@pytest.fixture
def sample_user_query():
    """Sample user query for testing."""
    return {
        "query": "Create API documentation for user authentication service",
        "user_id": f"test_user_{uuid.uuid4().hex[:8]}",
        "context": {"source": "test", "priority": "normal"}
    }


@pytest.fixture
def sample_execution_request():
    """Sample execution request for testing."""
    return {
        "query": "Generate comprehensive API documentation",
        "format": "markdown",
        "user_id": f"test_user_{uuid.uuid4().hex[:8]}",
        "parameters": {"include_examples": True}
    }


@pytest.fixture
def sample_workflow_request():
    """Sample workflow request for testing."""
    return {
        "name": "document_generation",
        "parameters": {
            "content_type": "api_documentation",
            "format": "json",
            "include_metadata": True
        },
        "user_id": f"test_user_{uuid.uuid4().hex[:8]}"
    }


class TestBasicEndpoints:
    """Test basic service endpoints."""

    def test_health_endpoint(self, client):
        """Test GET /health endpoint."""
        response = client.get("/health")
        _assert_http_ok(response)
        
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        assert data["service"] == "interpreter"

    def test_interpret_endpoint(self, client, sample_user_query):
        """Test POST /interpret endpoint."""
        response = client.post("/interpret", json=sample_user_query)
        _assert_http_ok(response)
        
        data = response.json()
        assert "intent" in data
        assert "entities" in data
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0

    def test_intents_endpoint(self, client):
        """Test GET /intents endpoint."""
        response = client.get("/intents")
        _assert_http_ok(response)
        
        data = response.json()
        assert "supported_intents" in data
        assert isinstance(data["supported_intents"], list)
        
        # Verify intent structure
        if data["supported_intents"]:
            intent = data["supported_intents"][0]
            assert "name" in intent
            assert "description" in intent
            assert "examples" in intent

    def test_ecosystem_capabilities_endpoint(self, client):
        """Test GET /ecosystem/capabilities endpoint."""
        response = client.get("/ecosystem/capabilities")
        _assert_http_ok(response)
        
        data = response.json()
        assert "ecosystem_capabilities" in data
        assert "service_integrations" in data
        assert "workflow_types" in data
        assert isinstance(data["workflow_types"], list)

    def test_ecosystem_health_endpoint(self, client):
        """Test GET /health/ecosystem endpoint."""
        response = client.get("/health/ecosystem")
        _assert_http_ok(response)
        
        data = response.json()
        assert "ecosystem_health" in data
        assert "services" in data
        assert "overall_status" in data
        
        # Verify service health structure
        services = data["services"]
        for service_name, service_health in services.items():
            assert "status" in service_health
            assert "response_time" in service_health


class TestWorkflowExecutionEndpoints:
    """Test workflow execution endpoints."""

    def test_execute_basic_workflow_endpoint(self, client):
        """Test POST /execute endpoint (legacy compatibility)."""
        request_data = {
            "workflow_type": "document_generation",
            "parameters": {"test": "data"},
            "user_id": "test_user"
        }
        
        response = client.post("/execute", json=request_data)
        
        # Should accept request or return appropriate error
        assert response.status_code in [200, 202, 400, 422, 501]
        
        if response.status_code in [200, 202]:
            data = response.json()
            assert "status" in data or "execution_id" in data

    def test_execute_workflow_legacy_endpoint(self, client):
        """Test POST /execute-workflow endpoint (legacy compatibility)."""
        request_data = {
            "workflow_name": "api_documentation",
            "input_data": {"content": "test"},
            "user_id": "test_user"
        }
        
        response = client.post("/execute-workflow", json=request_data)
        
        # Should handle legacy format or return appropriate error
        assert response.status_code in [200, 202, 400, 422, 501]
        
        if response.status_code in [200, 202]:
            data = response.json()
            assert "workflow_id" in data or "execution_id" in data or "status" in data

    def test_execute_query_endpoint(self, client, sample_execution_request):
        """Test POST /execute-query endpoint (main document generation)."""
        response = client.post("/execute-query", json=sample_execution_request)
        
        # Should accept request (may be async)
        assert response.status_code in [200, 202, 400, 422]
        
        if response.status_code in [200, 202]:
            data = response.json()
            
            # Should contain execution information
            expected_fields = ["execution_id", "document_id", "file_id", "status", "download_url"]
            assert any(field in data for field in expected_fields)

    def test_execute_workflow_direct_endpoint(self, client, sample_workflow_request):
        """Test POST /workflows/execute-direct endpoint."""
        response = client.post("/workflows/execute-direct", json=sample_workflow_request)
        
        # Should handle direct workflow execution
        assert response.status_code in [200, 202, 400, 422]
        
        if response.status_code in [200, 202]:
            data = response.json()
            assert "execution_id" in data or "result" in data or "status" in data

    def test_execution_status_endpoint(self, client):
        """Test GET /execution/{execution_id}/status endpoint."""
        test_execution_id = "test_exec_123"
        
        response = client.get(f"/execution/{test_execution_id}/status")
        
        # Should return status information or 404 for unknown execution
        assert response.status_code in [200, 404, 501]
        
        if response.status_code == 200:
            data = response.json()
            assert "execution_id" in data
            assert "status" in data
            assert data["execution_id"] == test_execution_id


class TestOutputAndFormatEndpoints:
    """Test output and format management endpoints."""

    def test_supported_formats_endpoint(self, client):
        """Test GET /outputs/formats endpoint."""
        response = client.get("/outputs/formats")
        _assert_http_ok(response)
        
        data = response.json()
        assert "supported_formats" in data
        
        formats = data["supported_formats"]
        assert isinstance(formats, list)
        assert len(formats) > 0
        
        # Verify expected formats are present
        expected_formats = ["json", "markdown", "csv", "txt"]
        for expected_format in expected_formats:
            assert expected_format in formats

    def test_workflow_templates_endpoint(self, client):
        """Test GET /workflows/templates endpoint."""
        response = client.get("/workflows/templates")
        _assert_http_ok(response)
        
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)
        
        # Verify template structure if templates exist
        if data["templates"]:
            template = data["templates"][0]
            assert "name" in template
            assert "description" in template
            assert "parameters" in template

    def test_download_output_file_endpoint(self, client):
        """Test GET /outputs/download/{file_id} endpoint."""
        test_file_id = "test_file_123"
        
        response = client.get(f"/outputs/download/{test_file_id}")
        
        # Should return file or 404 for unknown file
        assert response.status_code in [200, 404, 501]
        
        if response.status_code == 200:
            # Should have appropriate content headers
            assert "content-type" in response.headers
            assert response.content is not None


class TestDocumentManagementEndpoints:
    """Test document management and provenance endpoints."""

    def test_document_provenance_endpoint(self, client):
        """Test GET /documents/{document_id}/provenance endpoint."""
        test_document_id = "test_doc_123"
        
        response = client.get(f"/documents/{test_document_id}/provenance")
        
        # Should return provenance data or 404 for unknown document
        assert response.status_code in [200, 404, 501]
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify provenance structure
            expected_fields = ["workflow_execution", "services_chain", "user_context", "data_lineage"]
            assert any(field in data for field in expected_fields)

    def test_workflow_execution_trace_endpoint(self, client):
        """Test GET /workflows/{execution_id}/trace endpoint."""
        test_execution_id = "test_exec_trace_456"
        
        response = client.get(f"/workflows/{test_execution_id}/trace")
        
        # Should return trace data or 404 for unknown execution
        assert response.status_code in [200, 404, 501]
        
        if response.status_code == 200:
            data = response.json()
            assert "execution_id" in data or "trace" in data or "steps" in data

    def test_documents_by_workflow_endpoint(self, client):
        """Test GET /documents/by-workflow/{workflow_name} endpoint."""
        test_workflow_name = "api_documentation"
        
        response = client.get(f"/documents/by-workflow/{test_workflow_name}")
        
        # Should return document list or empty list
        assert response.status_code in [200, 404, 501]
        
        if response.status_code == 200:
            data = response.json()
            assert "documents" in data or "items" in data
            
            # Test with limit parameter
            response_with_limit = client.get(f"/documents/by-workflow/{test_workflow_name}?limit=10")
            assert response_with_limit.status_code in [200, 404, 501]

    def test_download_document_from_doc_store_endpoint(self, client):
        """Test GET /documents/{document_id}/download endpoint."""
        test_document_id = "test_doc_download_789"
        
        response = client.get(f"/documents/{test_document_id}/download")
        
        # Should return document or 404 for unknown document
        assert response.status_code in [200, 404, 501]
        
        if response.status_code == 200:
            # Should have appropriate download headers
            assert response.content is not None
            # May have content-disposition header for downloads
            headers = {k.lower(): v for k, v in response.headers.items()}
            if "content-disposition" in headers:
                assert "attachment" in headers["content-disposition"]

    def test_recent_workflow_executions_endpoint(self, client):
        """Test GET /workflows/executions/recent endpoint."""
        response = client.get("/workflows/executions/recent")
        
        # Should return recent executions
        assert response.status_code in [200, 501]
        
        if response.status_code == 200:
            data = response.json()
            assert "executions" in data or "items" in data
            
            # Test with limit parameter
            response_with_limit = client.get("/workflows/executions/recent?limit=5")
            assert response_with_limit.status_code in [200, 501]


class TestEndpointErrorHandling:
    """Test error handling across all endpoints."""

    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON in POST requests."""
        endpoints_with_json = [
            "/interpret",
            "/execute",
            "/execute-workflow", 
            "/execute-query",
            "/workflows/execute-direct"
        ]
        
        for endpoint in endpoints_with_json:
            # Test with invalid JSON structure
            response = client.post(endpoint, data="invalid json")
            assert response.status_code in [400, 422, 500]

    def test_missing_required_fields(self, client):
        """Test handling of missing required fields in requests."""
        # Test interpret endpoint with missing fields
        response = client.post("/interpret", json={})
        assert response.status_code in [400, 422]
        
        # Test execute-query with missing fields
        response = client.post("/execute-query", json={"query": ""})
        assert response.status_code in [400, 422]

    def test_invalid_parameter_types(self, client):
        """Test handling of invalid parameter types."""
        invalid_requests = [
            {
                "endpoint": "/interpret",
                "data": {"query": 123, "user_id": None}  # Wrong types
            },
            {
                "endpoint": "/execute-query",
                "data": {"query": "test", "format": 123}  # Wrong format type
            }
        ]
        
        for test_case in invalid_requests:
            response = client.post(test_case["endpoint"], json=test_case["data"])
            assert response.status_code in [400, 422]

    def test_nonexistent_resource_handling(self, client):
        """Test handling of requests for nonexistent resources."""
        nonexistent_tests = [
            ("/execution/nonexistent_id/status", 404),
            ("/documents/nonexistent_doc/provenance", 404),
            ("/workflows/nonexistent_exec/trace", 404),
            ("/documents/nonexistent_doc/download", 404),
            ("/outputs/download/nonexistent_file", 404)
        ]
        
        for endpoint, expected_status in nonexistent_tests:
            response = client.get(endpoint)
            assert response.status_code in [expected_status, 501]  # 501 if not implemented

    def test_large_request_handling(self, client):
        """Test handling of very large requests."""
        large_query = {
            "query": "x" * 100000,  # Very large query
            "user_id": "test_user"
        }
        
        response = client.post("/interpret", json=large_query)
        # Should handle large requests gracefully
        assert response.status_code in [200, 400, 413, 422]


class TestEndpointParameterValidation:
    """Test parameter validation across endpoints."""

    def test_query_parameter_validation(self, client):
        """Test query parameter validation."""
        test_cases = [
            {"query": "", "expected_status": [400, 422]},  # Empty query
            {"query": None, "expected_status": [400, 422]},  # Null query
            {"query": "valid query", "expected_status": [200]}  # Valid query
        ]
        
        for test_case in test_cases:
            request_data = {"query": test_case["query"], "user_id": "test_user"}
            response = client.post("/interpret", json=request_data)
            assert response.status_code in test_case["expected_status"]

    def test_format_parameter_validation(self, client):
        """Test format parameter validation in execution endpoints."""
        valid_formats = ["json", "markdown", "csv", "txt", "pdf"]
        invalid_formats = ["invalid", "xml", 123, None]
        
        for format_value in valid_formats:
            request_data = {
                "query": "test query",
                "format": format_value,
                "user_id": "test_user"
            }
            response = client.post("/execute-query", json=request_data)
            # Should accept valid formats
            assert response.status_code in [200, 202, 400]  # 400 might be for other validation
        
        for format_value in invalid_formats:
            request_data = {
                "query": "test query", 
                "format": format_value,
                "user_id": "test_user"
            }
            response = client.post("/execute-query", json=request_data)
            # Should reject invalid formats
            assert response.status_code in [400, 422]

    def test_limit_parameter_validation(self, client):
        """Test limit parameter validation in list endpoints."""
        # Test valid limits
        valid_limits = [1, 10, 50, 100]
        for limit in valid_limits:
            response = client.get(f"/workflows/executions/recent?limit={limit}")
            assert response.status_code in [200, 501]
        
        # Test invalid limits
        invalid_limits = [-1, 0, 10000, "invalid"]
        for limit in invalid_limits:
            response = client.get(f"/workflows/executions/recent?limit={limit}")
            # Should handle invalid limits gracefully
            assert response.status_code in [200, 400, 422, 501]


class TestEndpointResponseStructure:
    """Test response structure consistency across endpoints."""

    def test_success_response_structure(self, client):
        """Test that successful responses have consistent structure."""
        # Test endpoints that should always return success
        always_successful_endpoints = [
            "/health",
            "/intents",
            "/ecosystem/capabilities",
            "/outputs/formats",
            "/workflows/templates"
        ]
        
        for endpoint in always_successful_endpoints:
            response = client.get(endpoint)
            _assert_http_ok(response)
            
            # Should return valid JSON
            data = response.json()
            assert isinstance(data, dict)
            
            # Should have meaningful content
            assert len(data) > 0

    def test_error_response_structure(self, client):
        """Test that error responses have consistent structure."""
        # Force error by sending invalid data
        response = client.post("/interpret", json={"invalid": "data"})
        
        if response.status_code >= 400:
            # Should return JSON error
            try:
                error_data = response.json()
                assert isinstance(error_data, dict)
                
                # Common error fields
                error_fields = ["detail", "message", "error", "status_code"]
                assert any(field in error_data for field in error_fields)
                
            except json.JSONDecodeError:
                # Some errors might return plain text, which is acceptable
                assert response.text is not None

    def test_content_type_headers(self, client):
        """Test that endpoints return appropriate content-type headers."""
        json_endpoints = [
            "/health",
            "/intents", 
            "/ecosystem/capabilities",
            "/outputs/formats",
            "/workflows/templates"
        ]
        
        for endpoint in json_endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                assert "application/json" in content_type


class TestEndpointSecurity:
    """Test security aspects of endpoints."""

    def test_sql_injection_prevention(self, client):
        """Test that endpoints prevent SQL injection attempts."""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]
        
        for payload in sql_injection_payloads:
            # Test in various endpoints
            response = client.get(f"/documents/{payload}/provenance")
            # Should not return database errors
            assert response.status_code in [400, 404, 422]
            
            if response.status_code >= 400:
                response_text = response.text.lower()
                # Should not expose database internals
                dangerous_keywords = ["sql", "database", "table", "column", "syntax error"]
                for keyword in dangerous_keywords:
                    assert keyword not in response_text

    def test_xss_prevention(self, client):
        """Test that endpoints prevent XSS attacks."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for payload in xss_payloads:
            request_data = {"query": payload, "user_id": "test_user"}
            response = client.post("/interpret", json=request_data)
            
            # Should not return unescaped script content
            if response.status_code == 200:
                response_text = response.text
                assert "<script>" not in response_text
                assert "javascript:" not in response_text

    def test_input_length_limits(self, client):
        """Test that endpoints enforce reasonable input length limits."""
        # Test extremely long input
        very_long_query = "x" * 1000000  # 1MB string
        
        request_data = {"query": very_long_query, "user_id": "test_user"}
        response = client.post("/interpret", json=request_data)
        
        # Should reject or handle very long input appropriately
        assert response.status_code in [200, 400, 413, 422]


class TestEndpointPerformance:
    """Test performance characteristics of endpoints."""

    def test_response_time_expectations(self, client):
        """Test that endpoints respond within reasonable time."""
        import time
        
        fast_endpoints = [
            "/health",
            "/intents",
            "/outputs/formats",
            "/workflows/templates"
        ]
        
        for endpoint in fast_endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Fast endpoints should respond quickly
            assert response_time < 5.0, f"Endpoint {endpoint} too slow: {response_time}s"
            
            if response.status_code == 200:
                # Successful responses should be even faster
                assert response_time < 2.0, f"Successful response too slow: {response_time}s"

    def test_concurrent_request_handling(self, client):
        """Test that endpoints can handle concurrent requests."""
        import concurrent.futures
        import time
        
        def make_request():
            return client.get("/health")
        
        # Make 5 concurrent requests
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in futures]
        end_time = time.time()
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Concurrent requests should not take much longer than single request
        total_time = end_time - start_time
        assert total_time < 10.0, f"Concurrent requests too slow: {total_time}s"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
