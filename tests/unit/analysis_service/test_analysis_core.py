"""Analysis Service core functionality tests.

Tests document analysis, findings retrieval, and core analysis operations.
Focused on essential analysis operations following TDD principles.
"""
import pytest
import importlib.util, os
from fastapi.testclient import TestClient

from .test_utils import load_analysis_service, _assert_http_ok, sample_analysis_request, sample_report_request


@pytest.fixture(scope="module")
def client():
    """Test client fixture for analysis service."""
    app = load_analysis_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestAnalysisCore:
    """Test core analysis service functionality."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data

    def test_get_findings_basic(self, client):
        """Test basic findings retrieval."""
        response = client.get("/findings")
        _assert_http_ok(response)

        data = response.json()
        assert "findings" in data
        assert "count" in data
        assert "severity_counts" in data
        assert "type_counts" in data

        assert isinstance(data["findings"], list)
        assert data["count"] >= 0

    def test_get_findings_with_filters(self, client):
        """Test findings retrieval with severity filter."""
        response = client.get("/findings?severity=high")
        _assert_http_ok(response)

        data = response.json()
        findings = data["findings"]

        # All returned findings should have high severity
        for finding in findings:
            assert finding.get("severity") == "high"

    def test_get_findings_with_type_filter(self, client):
        """Test findings retrieval with type filter."""
        response = client.get("/findings?finding_type_filter=drift")
        _assert_http_ok(response)

        data = response.json()
        findings = data["findings"]

        # All returned findings should have drift type
        for finding in findings:
            assert finding.get("type") == "drift"

    def test_get_findings_with_limit(self, client):
        """Test findings retrieval with limit."""
        response = client.get("/findings?limit=1")
        _assert_http_ok(response)

        data = response.json()
        findings = data["findings"]

        # Should not exceed the limit
        assert len(findings) <= 1

    def test_get_findings_combined_filters(self, client):
        """Test findings retrieval with multiple filters."""
        response = client.get("/findings?severity=medium&limit=10")
        _assert_http_ok(response)

        data = response.json()
        findings = data["findings"]

        # All returned findings should have medium severity and not exceed limit
        for finding in findings:
            assert finding.get("severity") == "medium"
        assert len(findings) <= 10

    def test_analyze_documents_basic(self, client):
        """Test basic document analysis."""
        analyze_request = {
            "targets": ["doc:readme", "doc:api-docs"],
            "analysis_type": "consistency"
        }

        response = client.post("/analyze", json=analyze_request)
        _assert_http_ok(response)

        data = response.json()
        assert "findings" in data
        assert "count" in data
        assert "severity_counts" in data
        assert "type_counts" in data

    def test_analyze_documents_empty_targets(self, client):
        """Test document analysis with empty targets."""
        analyze_request = {
            "targets": [],
            "analysis_type": "consistency"
        }

        response = client.post("/analyze", json=analyze_request)
        # Should return validation error for empty targets
        assert response.status_code == 422

        data = response.json()
        assert "error" in data
        assert data["error"] == "validation_error"
        assert "detail" in data
        # Should include validation error about empty targets

    def test_analyze_documents_combined_type(self, client):
        """Test document analysis with combined analysis type."""
        analyze_request = {
            "targets": ["doc:readme", "api:users"],
            "analysis_type": "combined"
        }

        response = client.post("/analyze", json=analyze_request)
        _assert_http_ok(response)

        data = response.json()
        assert "findings" in data
        assert "count" in data

    def test_generate_report_summary(self, client):
        """Test summary report generation."""
        report_request = {
            "kind": "summary",
            "format": "json"
        }

        response = client.post("/reports/generate", json=report_request)
        _assert_http_ok(response)

        data = response.json()
        assert "type" in data
        assert data["type"] == "summary"
        assert "total_findings" in data

    def test_generate_report_trends(self, client):
        """Test trends report generation."""
        report_request = {
            "kind": "trends",
            "format": "json",
            "payload": {"time_window": "7d"}
        }

        response = client.post("/reports/generate", json=report_request)
        _assert_http_ok(response)

        data = response.json()
        assert "type" in data
        assert data["type"] == "trends"
        assert "trend_data" in data

    def test_generate_report_life_of_ticket(self, client):
        """Test life of ticket report generation."""
        report_request = {
            "kind": "life_of_ticket",
            "format": "json",
            "payload": {"ticket_id": "PROJ-123"}
        }

        response = client.post("/reports/generate", json=report_request)
        _assert_http_ok(response)

        data = response.json()
        assert "ticket_id" in data
        assert "stages" in data
        assert "current_stage" in data

    def test_generate_report_pr_confidence(self, client):
        """Test PR confidence report generation."""
        report_request = {
            "kind": "pr_confidence",
            "format": "json",
            "payload": {"pr_id": "123"}
        }

        response = client.post("/reports/generate", json=report_request)
        _assert_http_ok(response)

        data = response.json()
        assert "pr_id" in data
        assert "confidence_score" in data
        assert "factors" in data

    def test_generate_report_invalid_kind(self, client):
        """Test report generation with invalid kind."""
        report_request = {
            "kind": "invalid-report-type",
            "format": "json"
        }

        response = client.post("/reports/generate", json=report_request)
        # Should handle invalid report type gracefully
        assert response.status_code in [200, 400, 422]

        if response.status_code == 400:
            data = response.json()
            assert "error" in data

    def test_list_detectors(self, client):
        """Test detectors listing."""
        response = client.get("/detectors")
        _assert_http_ok(response)

        data = response.json()
        assert "detectors" in data
        assert "total_detectors" in data

        detectors = data["detectors"]
        assert isinstance(detectors, list)
        assert len(detectors) > 0

        # Check detector structure
        for detector in detectors:
            assert "name" in detector
            assert "description" in detector
            assert "severity_levels" in detector
            assert "confidence_threshold" in detector

    def test_confluence_consolidation_report(self, client):
        """Test Confluence consolidation report."""
        response = client.get("/reports/confluence/consolidation")
        _assert_http_ok(response)

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "summary" in data

        items = data["items"]
        assert isinstance(items, list)

        if items:
            # Check item structure
            item = items[0]
            assert "id" in item
            assert "confidence" in item
            assert "flags" in item
            assert "documents" in item

    def test_confluence_consolidation_with_confidence_filter(self, client):
        """Test Confluence consolidation with confidence filter."""
        response = client.get("/reports/confluence/consolidation?min_confidence=0.9")
        _assert_http_ok(response)

        data = response.json()
        items = data["items"]

        # All items should meet confidence threshold
        for item in items:
            assert item.get("confidence", 0) >= 0.9

    def test_jira_staleness_report(self, client):
        """Test Jira staleness report."""
        response = client.get("/reports/jira/staleness")
        _assert_http_ok(response)

        data = response.json()
        assert "items" in data
        assert "total" in data

        items = data["items"]
        assert isinstance(items, list)

        if items:
            # Check item structure
            item = items[0]
            assert "id" in item
            assert "confidence" in item
            assert "flags" in item
            assert "reason" in item

    def test_jira_staleness_with_confidence_filter(self, client):
        """Test Jira staleness with confidence filter."""
        response = client.get("/reports/jira/staleness?min_confidence=0.8")
        _assert_http_ok(response)

        data = response.json()
        items = data["items"]

        # All items should meet confidence threshold
        for item in items:
            assert item.get("confidence", 0) >= 0.8

    def test_notify_owners_basic(self, client):
        """Test basic owner notification."""
        findings = [
            {
                "id": "finding-1",
                "title": "Test Finding",
                "severity": "high",
                "type": "drift"
            }
        ]

        response = client.post("/reports/findings/notify-owners", json={
            "findings": findings,
            "channels": ["email"],
            "priority": "high"
        })
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert "findings_processed" in data
        assert "notifications_sent" in data

    def test_notify_owners_multiple_channels(self, client):
        """Test owner notification with multiple channels."""
        findings = [
            {
                "id": "finding-1",
                "title": "Test Finding",
                "severity": "medium"
            }
        ]

        response = client.post("/reports/findings/notify-owners", json={
            "findings": findings,
            "channels": ["email", "slack"],
            "priority": "medium"
        })
        _assert_http_ok(response)

        data = response.json()
        assert "channels_used" in data
        assert len(data["channels_used"]) == 2

    def test_notify_owners_empty_findings(self, client):
        """Test owner notification with empty findings list."""
        response = client.post("/reports/findings/notify-owners", json={
            "findings": [],
            "channels": ["email"]
        })
        # Should return 422 validation error for empty findings
        assert response.status_code == 422

        data = response.json()
        assert "error" in data
        assert "validation_error" in data.get("error", "")

    def test_integration_health_check(self, client):
        """Test integration health check."""
        response = client.get("/integration/health")
        _assert_http_ok(response)

        data = response.json()
        assert "analysis_service" in data
        assert "integrations" in data
        assert "available_services" in data

        available_services = data["available_services"]
        assert isinstance(available_services, list)
        assert len(available_services) > 0
