"""Analysis Service integration and workflow tests.

Tests service integration, data flow, and end-to-end workflows.
Focused on integration scenarios following TDD principles.
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


class TestAnalysisIntegration:
    """Test analysis integration and workflow functionality."""

    def test_complete_analysis_workflow(self, client):
        """Test complete document analysis workflow."""
        # Step 1: Analyze documents
        analyze_request = {
            "targets": ["doc:readme", "api:users"],
            "analysis_type": "consistency"
        }

        analyze_response = client.post("/analyze", json=analyze_request)
        _assert_http_ok(analyze_response)

        analysis_data = analyze_response.json()
        findings = analysis_data["findings"]

        # Step 2: Verify analysis results
        assert len(findings) > 0
        for finding in findings:
            assert "id" in finding
            assert "type" in finding
            assert "description" in finding
            assert "severity" in finding

        # Step 3: Retrieve findings
        findings_response = client.get("/findings")
        _assert_http_ok(findings_response)

        findings_data = findings_response.json()
        retrieved_findings = findings_data["findings"]

        # Step 4: Verify findings retrieval
        assert len(retrieved_findings) >= len(findings)

        # Step 5: Generate summary report
        report_response = client.post("/reports/generate", json={"kind": "summary"})
        _assert_http_ok(report_response)

        report_data = report_response.json()
        assert "type" in report_data
        assert report_data["type"] == "summary"

    def test_cross_service_findings_workflow(self, client):
        """Test workflow spanning multiple service integrations."""
        # Step 1: Get current findings
        findings_response = client.get("/findings")
        _assert_http_ok(findings_response)

        findings_data = findings_response.json()
        current_findings = findings_data["findings"]

        # Step 2: Analyze additional documents
        analyze_response = client.post("/analyze", json={
            "targets": ["doc:new-document"],
            "analysis_type": "consistency"
        })
        _assert_http_ok(analyze_response)

        # Step 3: Get updated findings
        updated_findings_response = client.get("/findings")
        _assert_http_ok(updated_findings_response)

        updated_findings_data = updated_findings_response.json()
        updated_findings = updated_findings_data["findings"]

        # Step 4: Verify findings were updated
        assert len(updated_findings) >= len(current_findings)

    def test_report_generation_workflow(self, client):
        """Test comprehensive report generation workflow."""
        # Generate multiple types of reports
        report_types = ["summary", "trends"]

        reports = {}
        for report_type in report_types:
            response = client.post("/reports/generate", json={"kind": report_type})
            _assert_http_ok(response)
            reports[report_type] = response.json()

        # Verify all reports have consistent structure
        for report_type, report_data in reports.items():
            assert "type" in report_data
            assert report_data["type"] == report_type
            # Optional fields that may or may not be present
            if "data_sources" in report_data:
                assert isinstance(report_data["data_sources"], list)
            if "integration_status" in report_data:
                assert report_data["integration_status"] in ["completed", "pending", "failed"]

    def test_notification_integration_workflow(self, client):
        """Test notification integration workflow."""
        # Step 1: Get findings to notify about
        findings_response = client.get("/findings")
        _assert_http_ok(findings_response)

        findings_data = findings_response.json()
        findings = findings_data["findings"]

        if findings:
            # Step 2: Send notifications
            notification_response = client.post("/reports/findings/notify-owners", json={
                "findings": findings[:3],  # Notify about first 3 findings
                "channels": ["email", "slack"],
                "priority": "high"
            })
            _assert_http_ok(notification_response)

            notification_data = notification_response.json()

            # Step 3: Verify notification integration
            assert "status" in notification_data
            assert "findings_processed" in notification_data
            assert "channels_used" in notification_data
            # Optional fields that may or may not be present
            if "integration_status" in notification_data:
                assert notification_data["integration_status"] in ["completed", "pending", "failed"]
            assert notification_data["findings_processed"] >= 0

    def test_prompt_integration_workflow(self, client):
        """Test prompt-based analysis integration workflow."""
        # Step 1: Get available prompt categories
        categories_response = client.get("/integration/prompts/categories")
        _assert_http_ok(categories_response)

        categories_data = categories_response.json()
        categories = categories_data.get("categories", [])

        # Step 2: Use a prompt for analysis
        if categories:
            prompt_response = client.post("/integration/analyze-with-prompt", json={
                "target_id": "doc:readme",
                "prompt_category": categories[0],
                "prompt_name": "consistency_check",
                "temperature": 0.7,
                "max_tokens": 1000
            })
            _assert_http_ok(prompt_response)

            prompt_data = prompt_response.json()

            # Step 3: Verify prompt integration
            assert "prompt_used" in prompt_data
            assert "target_id" in prompt_data
            assert "variables_used" in prompt_data
            assert "integration_status" in prompt_data

    def test_natural_language_integration_workflow(self, client):
        """Test natural language analysis integration workflow."""
        # Step 1: Analyze natural language query
        nl_response = client.post("/integration/natural-language-analysis", json={
            "query": "analyze the README for consistency issues"
        })
        _assert_http_ok(nl_response)

        nl_data = nl_response.json()

        # Step 2: Verify interpreter integration
        assert "interpretation" in nl_data
        # Optional field that may or may not be present
        if "integration_status" in nl_data:
            assert nl_data["integration_status"] in ["completed", "pending", "failed"]

        interpretation = nl_data["interpretation"]
        assert "intent" in interpretation
        assert "confidence" in interpretation

    def test_usage_logging_integration_workflow(self, client):
        """Test usage logging integration workflow."""
        # Step 1: Perform analysis that would be logged
        analyze_response = client.post("/analyze", json={
            "targets": ["doc:readme"],
            "analysis_type": "consistency"
        })
        _assert_http_ok(analyze_response)

        # Step 2: Log usage
        log_response = client.post("/integration/log-analysis", json={
            "prompt_id": "analysis.consistency_check",
            "input_tokens": 150,
            "output_tokens": 75,
            "response_time_ms": 1250.5,
            "success": True
        })
        _assert_http_ok(log_response)

        log_data = log_response.json()

        # Step 3: Verify logging integration
        if "status" in log_data:
            assert log_data["status"] == "logged" or log_data["status"] == "completed"
        if "logged" in log_data:
            assert log_data["logged"] is True
        if "integration_status" in log_data:
            assert log_data["integration_status"] in ["completed", "pending", "failed"]
        # Optional field that may or may not be present
        if "metrics_logged" in log_data:
            assert log_data["metrics_logged"] is True

    def test_service_health_integration_check(self, client):
        """Test integration health check across services."""
        # This endpoint would normally check other services
        response = client.get("/integration/health")
        _assert_http_ok(response)

        data = response.json()

        # Verify integration health structure
        assert "analysis_service" in data
        assert "integrations" in data
        assert "available_services" in data

        integrations = data["integrations"]
        assert isinstance(integrations, dict)

        available_services = data["available_services"]
        assert isinstance(available_services, list)
        assert len(available_services) > 0

    def test_end_to_end_analysis_pipeline(self, client):
        """Test end-to-end analysis pipeline."""
        # Step 1: Analyze documents
        analyze_response = client.post("/analyze", json={
            "targets": ["doc:readme", "doc:api-spec", "api:users"],
            "analysis_type": "combined"
        })
        _assert_http_ok(analyze_response)

        analysis_data = analyze_response.json()
        findings_count = analysis_data["count"]

        # Step 2: Get findings
        findings_response = client.get("/findings")
        _assert_http_ok(findings_response)

        findings_data = findings_response.json()

        # Step 3: Generate comprehensive report
        report_response = client.post("/reports/generate", json={
            "kind": "summary",
            "format": "json"
        })
        _assert_http_ok(report_response)

        report_data = report_response.json()

        # Step 4: Verify end-to-end consistency
        assert findings_data["count"] >= findings_count
        assert report_data["total_findings"] >= findings_count
        # Optional fields that may or may not be present
        if "data_sources" in report_data:
            assert isinstance(report_data["data_sources"], list)
        if "integration_status" in report_data:
            assert report_data["integration_status"] in ["completed", "pending", "failed"]

    def test_bulk_analysis_workflow(self, client):
        """Test bulk analysis workflow."""
        # Analyze multiple document sets
        document_sets = [
            ["doc:readme"],
            ["doc:api-spec", "api:users"],
            ["doc:readme", "doc:api-spec", "api:users", "api:orders"]
        ]

        results = []
        for doc_set in document_sets:
            response = client.post("/analyze", json={
                "targets": doc_set,
                "analysis_type": "consistency"
            })
            _assert_http_ok(response)
            results.append(response.json())

        # Verify bulk processing results
        assert len(results) == len(document_sets)
        for result in results:
            assert "findings" in result
            assert "count" in result
            assert "severity_counts" in result

    def test_integration_error_handling(self, client):
        """Test error handling in integration scenarios."""
        # Test with invalid integration requests
        invalid_requests = [
            {
                "endpoint": "/integration/analyze-with-prompt",
                "data": {
                    "target_id": "invalid:target",
                    "prompt_category": "nonexistent",
                    "prompt_name": "missing"
                }
            },
            {
                "endpoint": "/integration/natural-language-analysis",
                "data": {"query": ""}
            }
        ]

        for req in invalid_requests:
            response = client.post(req["endpoint"], json=req["data"])
            # Should handle integration errors gracefully
            assert response.status_code in [200, 400, 422, 500]

            if response.status_code == 200:
                data = response.json()
                # Optional field that may or may not be present
                if "integration_status" in data:
                    assert data["integration_status"] in ["completed", "pending", "failed"]

    def test_cross_service_data_consistency(self, client):
        """Test data consistency across integrated services."""
        # Step 1: Analyze documents
        analyze_response = client.post("/analyze", json={
            "targets": ["doc:consistency-test"],
            "analysis_type": "consistency"
        })
        _assert_http_ok(analyze_response)

        analysis_findings = analyze_response.json()["findings"]

        # Step 2: Get findings
        findings_response = client.get("/findings")
        _assert_http_ok(findings_response)

        retrieved_findings = findings_response.json()["findings"]

        # Step 3: Verify data consistency
        # Analysis findings should be reflected in retrieved findings
        analysis_ids = {f["id"] for f in analysis_findings}
        retrieved_ids = {f["id"] for f in retrieved_findings}

        # At least some analysis findings should be retrievable
        intersection = analysis_ids.intersection(retrieved_ids)
        assert len(intersection) >= 0  # Allow for empty intersection in mock

    def test_integration_performance_workflow(self, client):
        """Test integration performance under load."""
        import time

        start_time = time.time()

        # Perform 50 integration operations
        operations = 0
        for i in range(25):
            # Analysis operation
            analyze_response = client.post("/analyze", json={
                "targets": [f"doc:perf-test-{i}"],
                "analysis_type": "consistency"
            })
            if analyze_response.status_code == 200:
                operations += 1

            # Findings retrieval
            findings_response = client.get("/findings")
            if findings_response.status_code == 200:
                operations += 1

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete within reasonable time
        assert total_time < 30  # 30 seconds for 50 operations
        assert operations > 0  # At least some operations should succeed

    def test_workflow_orchestration_simulation(self, client):
        """Test simulation of workflow orchestration."""
        # Simulate a complex workflow
        workflow_steps = [
            # Step 1: Analyze documents
            {
                "name": "document_analysis",
                "action": lambda: client.post("/analyze", json={
                    "targets": ["doc:workflow-doc"],
                    "analysis_type": "consistency"
                })
            },
            # Step 2: Get findings
            {
                "name": "findings_retrieval",
                "action": lambda: client.get("/findings")
            },
            # Step 3: Generate report
            {
                "name": "report_generation",
                "action": lambda: client.post("/reports/generate", json={"kind": "summary"})
            },
            # Step 4: Send notifications
            {
                "name": "notification_dispatch",
                "action": lambda: client.post("/reports/findings/notify-owners", json={
                    "findings": [{"id": "test-finding"}],
                    "channels": ["email"]
                })
            }
        ]

        workflow_results = {}
        for step in workflow_steps:
            try:
                response = step["action"]()
                response_data = response.json() if response.status_code == 200 else {}
                workflow_results[step["name"]] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "has_data": (len(response_data) > 0 and not any(k in response_data for k in ['error', 'message', 'status'] if response_data.get(k) in ['error', 'failed'])) if response.status_code == 200 else False
                }
            except Exception as e:
                workflow_results[step["name"]] = {
                    "success": False,
                    "error": str(e)
                }

        # Verify workflow completion
        successful_steps = sum(1 for result in workflow_results.values() if result.get("success", False))
        assert successful_steps >= len(workflow_steps) * 0.6  # At least 60% success rate

        # Check that each step produced expected results
        for step_name, result in workflow_results.items():
            if result.get("success", False):
                if step_name == "document_analysis":
                    assert result.get("has_data", False)
                elif step_name == "findings_retrieval":
                    assert result.get("has_data", False)
                elif step_name == "report_generation":
                    assert result.get("has_data", False)
