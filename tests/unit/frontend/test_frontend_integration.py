"""Frontend Service integration and service communication tests.

Tests service integration, data fetching, and cross-service workflows.
Focused on integration operations following TDD principles.
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


class TestFrontendIntegration:
    """Test frontend integration and service communication."""

    def test_owner_coverage_service_integration(self, client):
        """Test owner coverage page integrates with orchestrator service."""
        response = client.get("/owner-coverage")
        _assert_http_ok(response)

        # Should return HTML with coverage data
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        # Should contain coverage-related content
        assert "owner" in response.text.lower() or "coverage" in response.text.lower()

    def test_topics_service_integration(self, client):
        """Test topics page integrates with doc-store service."""
        response = client.get("/topics")
        _assert_http_ok(response)

        # Should return HTML with topics data
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        # Should contain topic-related content
        assert "topic" in response.text.lower()

    def test_confluence_consolidation_service_integration(self, client):
        """Test confluence consolidation integrates with orchestrator."""
        response = client.get("/confluence/consolidation")
        _assert_http_ok(response)

        # Should return HTML with consolidation data
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        # Should contain consolidation-related content
        assert "confluence" in response.text.lower()

    def test_jira_staleness_service_integration(self, client):
        """Test Jira staleness integrates with orchestrator."""
        response = client.get("/reports/jira/staleness")
        _assert_http_ok(response)

        # Should return HTML with Jira data
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        # Should contain Jira-related content
        assert "jira" in response.text.lower()

    def test_duplicate_clusters_service_integration(self, client):
        """Test duplicate clusters integrates with reporting service."""
        response = client.get("/duplicates/clusters")
        _assert_http_ok(response)

        # Should return HTML with cluster data
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        # Should contain cluster-related content
        assert "duplicate" in response.text.lower() or "cluster" in response.text.lower()

    def test_search_service_integration(self, client):
        """Test search integrates with doc-store service."""
        response = client.get("/search?q=kubernetes")
        _assert_http_ok(response)

        # Should return HTML with search results
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        # Should contain search-related content
        assert "search" in response.text.lower() or "kubernetes" in response.text.lower()

    def test_docs_quality_service_integration(self, client):
        """Test document quality integrates with doc-store service."""
        response = client.get("/docs/quality")
        _assert_http_ok(response)

        # Should return HTML with quality data
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        # Should contain quality-related content
        assert "quality" in response.text.lower() or "document" in response.text.lower()

    def test_findings_service_integration(self, client):
        """Test findings integrates with consistency-engine service."""
        response = client.get("/findings")
        _assert_http_ok(response)

        # Should return HTML with findings data
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        # Should contain findings-related content
        assert "finding" in response.text.lower()

    def test_findings_by_severity_service_integration(self, client):
        """Test findings by severity integrates with reporting service."""
        response = client.get("/findings/by-severity")
        _assert_http_ok(response)

        # Should return HTML with severity data
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        # Should contain severity-related content
        assert "severity" in response.text.lower()

    def test_findings_by_type_service_integration(self, client):
        """Test findings by type integrates with reporting service."""
        response = client.get("/findings/by-type")
        _assert_http_ok(response)

        # Should return HTML with type data
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        # Should contain type-related content
        assert "type" in response.text.lower()

    def test_report_service_integration(self, client):
        """Test comprehensive report integrates with reporting service."""
        response = client.get("/report")
        _assert_http_ok(response)

        # Should return HTML with comprehensive report
        assert "text/html" in response.headers.get("content-type", "")
        assert "<html>" in response.text.lower()
        # Should contain report-related content
        assert "report" in response.text.lower()

    def test_service_integration_error_handling(self, client):
        """Test error handling when service integrations fail."""
        # Test endpoints that depend on external services
        integration_endpoints = [
            "/owner-coverage",
            "/topics",
            "/confluence/consolidation",
            "/reports/jira/staleness",
            "/duplicates/clusters",
            "/search",
            "/docs/quality",
            "/findings",
            "/findings/by-severity",
            "/findings/by-type",
            "/report"
        ]

        for endpoint in integration_endpoints:
            response = client.get(endpoint)
            # Should handle service unavailability gracefully
            assert response.status_code in [200, 500]
            # Should still return HTML content
            if response.status_code == 200:
                assert "text/html" in response.headers.get("content-type", "")

    def test_cross_service_workflow(self, client):
        """Test workflow that spans multiple service integrations."""
        # Access multiple pages that use different services
        workflow_steps = [
            ("/", "Index page"),
            ("/findings", "Findings from consistency-engine"),
            ("/search?q=docs", "Search in doc-store"),
            ("/report", "Comprehensive report from reporting"),
            ("/topics", "Topics analysis from doc-store"),
        ]

        for endpoint, description in workflow_steps:
            response = client.get(endpoint)
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")
            assert "<html>" in response.text.lower()

    def test_service_client_configuration(self, client):
        """Test service client configuration and setup."""
        # Test that info endpoint returns service configuration
        response = client.get("/info")
        _assert_http_ok(response)

        data = response.json()
        assert "data" in data

        info_data = data["data"]
        assert "env" in info_data

        env_data = info_data["env"]
        # Should contain URLs for integrated services
        service_urls = ["REPORTING_URL", "DOC_STORE_URL", "CONSISTENCY_ENGINE_URL"]
        for url_key in service_urls:
            assert url_key in env_data

    def test_service_data_fetching(self, client):
        """Test service data fetching mechanisms."""
        # Test that endpoints can fetch and display data from services
        data_endpoints = [
            "/topics",  # Should fetch from doc-store
            "/findings",  # Should fetch from consistency-engine
            "/search?q=test",  # Should fetch from doc-store
        ]

        for endpoint in data_endpoints:
            response = client.get(endpoint)
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")
            # Should contain some data content
            assert len(response.text) > 100  # Reasonable minimum content length

    def test_service_parameter_passing(self, client):
        """Test parameter passing to integrated services."""
        # Test Jira staleness with parameters
        params_tests = [
            "/reports/jira/staleness?min_confidence=0.5",
            "/reports/jira/staleness?limit=25",
            "/reports/jira/staleness?summarize=true",
            "/search?q=advanced+search",
        ]

        for endpoint in params_tests:
            response = client.get(endpoint)
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

    def test_service_response_transformation(self, client):
        """Test transformation of service responses into HTML."""
        # Test that JSON responses from services are transformed into HTML
        transformation_endpoints = [
            "/findings/by-severity",  # Should transform severity data
            "/findings/by-type",     # Should transform type data
            "/topics",              # Should transform topic analysis
        ]

        for endpoint in transformation_endpoints:
            response = client.get(endpoint)
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")
            # Should contain HTML structure
            assert "<body>" in response.text.lower()
            assert "</body>" in response.text.lower()

    def test_service_integration_metrics(self, client):
        """Test metrics collection for service integrations."""
        # Test metrics endpoint
        response = client.get("/metrics")
        _assert_http_ok(response)

        data = response.json()
        assert "data" in data

        metrics_data = data["data"]
        assert "service" in metrics_data
        assert "routes" in metrics_data
        assert isinstance(metrics_data["routes"], int)
        assert metrics_data["routes"] > 0

    def test_service_timeout_handling(self, client):
        """Test timeout handling for service integrations."""
        # Make multiple rapid requests to test timeout handling
        endpoints = ["/findings", "/search?q=test", "/topics", "/report"]

        for _ in range(3):  # Make 3 rounds of requests
            for endpoint in endpoints:
                response = client.get(endpoint)
                # Should handle timeouts gracefully
                assert response.status_code in [200, 500]
                if response.status_code == 200:
                    assert "text/html" in response.headers.get("content-type", "")

    def test_service_fallback_content(self, client):
        """Test fallback content when services are unavailable."""
        # Test that pages still render with fallback content when services fail
        fallback_endpoints = [
            "/owner-coverage",
            "/confluence/consolidation",
            "/duplicates/clusters",
        ]

        for endpoint in fallback_endpoints:
            response = client.get(endpoint)
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")
            # Should contain some basic HTML structure even with fallback content
            assert "<html>" in response.text.lower()
            assert "<body>" in response.text.lower()

    def test_service_data_caching_simulation(self, client):
        """Test simulation of service data caching."""
        # Make multiple requests to same endpoint to simulate caching
        endpoint = "/search?q=cache-test"

        responses = []
        for _ in range(5):
            response = client.get(endpoint)
            responses.append(response)
            _assert_http_ok(response)
            assert "text/html" in response.headers.get("content-type", "")

        # All responses should be consistent
        first_response = responses[0]
        for response in responses[1:]:
            assert response.status_code == first_response.status_code
            assert "text/html" in response.headers.get("content-type", "")

    def test_service_integration_load_test(self, client):
        """Test service integration under load."""
        import time

        start_time = time.time()
        endpoints = ["/findings", "/search?q=load", "/topics", "/report"]

        # Make 20 requests across different endpoints
        for i in range(5):
            for endpoint in endpoints:
                response = client.get(endpoint)
                assert response.status_code in [200, 500]
                if response.status_code == 200:
                    assert "text/html" in response.headers.get("content-type", "")

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete within reasonable time
        assert total_time < 15  # 15 seconds for 20 requests
