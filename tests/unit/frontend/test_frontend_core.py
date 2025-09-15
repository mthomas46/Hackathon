"""Frontend Service core functionality tests.

Tests UI rendering, service integration, and core frontend operations.
Focused on essential frontend operations following TDD principles.
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


class TestFrontendCore:
    """Test core frontend service functionality."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data

    def test_info_endpoint(self, client):
        """Test service information endpoint."""
        response = client.get("/info")
        _assert_http_ok(response)

        data = response.json()
        assert "message" in data
        assert "data" in data

        info_data = data["data"]
        assert "service" in info_data
        assert "version" in info_data
        assert "env" in info_data

        env_data = info_data["env"]
        assert "REPORTING_URL" in env_data
        assert "DOC_STORE_URL" in env_data
        assert "CONSISTENCY_ENGINE_URL" in env_data

    def test_config_effective_endpoint(self, client):
        """Test effective configuration endpoint."""
        response = client.get("/config/effective")
        _assert_http_ok(response)

        data = response.json()
        assert "message" in data
        assert "data" in data

        config_data = data["data"]
        # Should contain service URLs
        assert isinstance(config_data, dict)
        assert len(config_data) > 0

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        _assert_http_ok(response)

        data = response.json()
        assert "message" in data
        assert "data" in data

        metrics_data = data["data"]
        assert "service" in metrics_data
        assert "routes" in metrics_data
        assert isinstance(metrics_data["routes"], int)

    def test_index_page_html(self, client):
        """Test main index page returns HTML."""
        response = client.get("/")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        assert "<body>" in response.text.lower()

    def test_owner_coverage_page_html(self, client):
        """Test owner coverage page returns HTML."""
        response = client.get("/owner-coverage")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_topics_page_html(self, client):
        """Test topics page returns HTML."""
        response = client.get("/topics")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_confluence_consolidation_page_html(self, client):
        """Test confluence consolidation page returns HTML."""
        response = client.get("/confluence/consolidation")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_search_page_html(self, client):
        """Test search page returns HTML."""
        response = client.get("/search")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_search_with_query_parameter(self, client):
        """Test search page with query parameter."""
        response = client.get("/search?q=kubernetes")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_docs_quality_page_html(self, client):
        """Test document quality page returns HTML."""
        response = client.get("/docs/quality")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_findings_page_html(self, client):
        """Test findings page returns HTML."""
        response = client.get("/findings")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_findings_by_severity_page_html(self, client):
        """Test findings by severity page returns HTML."""
        response = client.get("/findings/by-severity")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_findings_by_type_page_html(self, client):
        """Test findings by type page returns HTML."""
        response = client.get("/findings/by-type")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_report_page_html(self, client):
        """Test comprehensive report page returns HTML."""
        response = client.get("/report")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_jira_staleness_page_html(self, client):
        """Test Jira staleness report page returns HTML."""
        response = client.get("/reports/jira/staleness")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_jira_staleness_with_parameters(self, client):
        """Test Jira staleness page with query parameters."""
        response = client.get("/reports/jira/staleness?min_confidence=0.5&limit=25&summarize=true")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_duplicate_clusters_page_html(self, client):
        """Test duplicate clusters page returns HTML."""
        response = client.get("/duplicates/clusters")
        _assert_http_ok(response)

        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()

    def test_invalid_endpoint_returns_404(self, client):
        """Test invalid endpoint returns 404."""
        response = client.get("/invalid-endpoint")
        assert response.status_code == 404

    def test_search_empty_query_parameter(self, client):
        """Test search with empty query parameter."""
        response = client.get("/search?q=")
        _assert_http_ok(response)

        # Should still return HTML content
        assert "text/html" in response.headers.get("content-type", "")

    def test_jira_staleness_parameter_validation(self, client):
        """Test Jira staleness parameter validation."""
        # Test with valid parameters
        response = client.get("/reports/jira/staleness?min_confidence=0.8&min_duplicate_confidence=0.9&limit=100")
        _assert_http_ok(response)

        # Test with invalid parameters
        response = client.get("/reports/jira/staleness?min_confidence=1.5&limit=-1")
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_search_special_characters(self, client):
        """Test search with special characters in query."""
        special_queries = [
            "kubernetes+redis",
            "fastapi&postgres",
            "openapi spec",
            "microservices-architecture"
        ]

        for query in special_queries:
            response = client.get(f"/search?q={query}")
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

    def test_multiple_page_access(self, client):
        """Test accessing multiple pages in sequence."""
        endpoints = [
            "/", "/findings", "/report", "/search", "/docs/quality",
            "/findings/by-severity", "/findings/by-type", "/topics"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")
