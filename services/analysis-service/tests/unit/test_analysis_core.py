"""Analysis Service core functionality tests.

Tests core analysis service endpoints and functionality.
Focused on essential operations following TDD principles.
"""
import pytest
import importlib.util, os
from fastapi.testclient import TestClient

from .test_utils import load_analysis_service, _assert_http_ok


@pytest.fixture(scope="module")
def client():
    """Test client fixture for analysis service."""
    app = load_analysis_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestAnalysisCore:
    """Test core analysis service functionality."""

    def test_root_endpoint(self, client):
        """Test root endpoint health check."""
        response = client.get("/")
        _assert_http_ok(response)

        data = response.json()
        assert data["success"] is True
        assert "message" in data["data"]
        assert "Analysis Service is running" in data["data"]["message"]

    def test_analysis_status_endpoint(self, client):
        """Test analysis status endpoint."""
        response = client.get("/api/analysis/status")
        _assert_http_ok(response)

        data = response.json()
        assert data["success"] is True
        assert "service" in data["data"]
        assert data["data"]["service"] == "analysis-service"
        assert "status" in data["data"]
        assert data["data"]["status"] == "operational"

    def test_analysis_status_v1_endpoint(self, client):
        """Test v1 analysis status endpoint."""
        response = client.get("/api/v1/analysis/status")
        _assert_http_ok(response)

        data = response.json()
        # This endpoint returns data directly, not wrapped in success response
        assert "service" in data
        assert data["service"] == "analysis-service"
        assert "capabilities" in data
        assert "detectors_available" in data

    def test_get_findings_basic(self, client):
        """Test basic findings retrieval."""
        response = client.get("/findings")
        _assert_http_ok(response)

        data = response.json()
        assert data["success"] is True
        assert "findings" in data["data"]
        assert "total" in data["data"]
        assert isinstance(data["data"]["findings"], list)
        assert data["data"]["total"] >= 0

    def test_get_detectors(self, client):
        """Test detectors listing."""
        response = client.get("/detectors")
        _assert_http_ok(response)

        data = response.json()
        assert data["success"] is True
        assert "detectors" in data["data"]

        detectors = data["data"]["detectors"]
        assert isinstance(detectors, list)
        assert len(detectors) > 0
        # Check that expected detectors are present
        expected_detectors = [
            "semantic_similarity", "sentiment_analysis", "tone_analysis",
            "quality_assessment", "trend_analysis", "risk_assessment"
        ]
        for detector in expected_detectors:
            assert detector in detectors

    def test_generate_reports(self, client):
        """Test report generation."""
        report_request = {
            "kind": "summary",
            "format": "json"
        }

        response = client.post("/reports/generate", json=report_request)
        _assert_http_ok(response)

        data = response.json()
        assert data["success"] is True
        assert "report_id" in data["data"]
        assert "status" in data["data"]
        assert data["data"]["status"] == "generated"

    def test_generate_reports_trends(self, client):
        """Test trends report generation."""
        report_request = {
            "kind": "trends",
            "format": "json",
            "payload": {"time_window": "7d"}
        }

        response = client.post("/reports/generate", json=report_request)
        _assert_http_ok(response)

        data = response.json()
        assert data["success"] is True
        assert "report_id" in data["data"]
        assert data["data"]["status"] == "generated"

    def test_generate_reports_invalid_kind(self, client):
        """Test report generation with invalid kind."""
        report_request = {
            "kind": "invalid-report-type",
            "format": "json"
        }

        response = client.post("/reports/generate", json=report_request)
        # Should still succeed as the endpoint handles invalid types gracefully
        _assert_http_ok(response)

        data = response.json()
        assert data["success"] is True
        assert "report_id" in data["data"]

    def test_integration_health_check(self, client):
        """Test integration health check."""
        response = client.get("/integration/health")
        _assert_http_ok(response)

        data = response.json()
        assert data["success"] is True
        assert "status" in data["data"]
        assert "services" in data["data"]
        assert data["data"]["status"] == "healthy"
        assert isinstance(data["data"]["services"], list)

    def test_analyze_code_basic(self, client):
        """Test basic code analysis."""
        response = client.post("/api/analysis/analyze")
        _assert_http_ok(response)

        data = response.json()
        assert data["success"] is True
        assert "analysis_id" in data["data"]
        assert "status" in data["data"]
        assert data["data"]["status"] == "completed"
