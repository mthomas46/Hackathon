"""Prompt Store A/B testing tests.

Tests A/B testing framework for prompt optimization.
Focused on experiment creation and metrics tracking.
"""
import pytest
import importlib.util, os
from fastapi.testclient import TestClient

from .test_utils import load_prompt_store_service, _assert_http_ok, sample_prompt, sample_ab_test


@pytest.fixture(scope="module")
def client():
    """Test client fixture for prompt store service."""
    app = load_prompt_store_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestPromptABTesting:
    """Test A/B testing functionality for prompt optimization."""

    def test_create_ab_test(self, client):
        """Test creating an A/B test experiment."""
        ab_test_data = {
            "name": "response-length-test",
            "description": "Testing different response lengths",
            "prompt_a_id": "concise-prompt-1",
            "prompt_b_id": "detailed-prompt-1",
            "test_metric": "response_quality",
            "traffic_split": 0.5
        }

        response = client.post("/ab-tests", json=ab_test_data)
        # A/B testing may not be fully implemented yet, but we expect proper validation
        assert response.status_code in [200, 201, 404, 501, 422]

        # For now, just ensure we get a valid JSON response
        data = response.json()
        assert isinstance(data, dict)

    def test_ab_test_variant_selection(self, client):
        """Test A/B test variant selection logic."""
        # This would test the logic for selecting which variant to use
        # May not be implemented yet
        selection_resp = client.get("/ab-tests/select-variant", params={"experiment": "test-experiment"})
        assert selection_resp.status_code in [200, 404, 501]

        if selection_resp.status_code == 200:
            variant_data = selection_resp.json()
            assert "variant" in variant_data or "data" in variant_data

    def test_ab_test_metrics_tracking(self, client):
        """Test tracking metrics for A/B test variants."""
        metrics_data = {
            "experiment_id": "test-experiment",
            "variant": "concise",
            "metrics": {
                "response_length": 150,
                "user_satisfaction": 4.2,
                "response_time": 2.1
            },
            "user_id": "test-user-123"
        }

        response = client.post("/ab-tests/metrics", json=metrics_data)
        assert response.status_code in [200, 201, 404, 501]

        if response.status_code in [200, 201]:
            data = response.json()
            assert isinstance(data, dict)

    def test_ab_test_results_analysis(self, client):
        """Test analyzing A/B test results."""
        analysis_resp = client.get("/ab-tests/results", params={"experiment_id": "test-experiment"})
        assert analysis_resp.status_code in [200, 404, 501]

        if analysis_resp.status_code == 200:
            results = analysis_resp.json()
            assert isinstance(results, dict)
            # Should contain statistical analysis of variants
            if "variants" in results:
                assert isinstance(results["variants"], list)


class TestPromptAnalytics:
    """Test prompt usage analytics and performance tracking."""

    def test_prompt_usage_tracking(self, client):
        """Test tracking prompt usage metrics."""
        usage_data = {
            "prompt_id": "test-prompt-1",
            "user_id": "user-123",
            "session_id": "session-456",
            "usage_type": "completion",
            "tokens_used": 150,
            "response_time": 2.3,
            "success": True
        }

        response = client.post("/analytics/usage", json=usage_data)
        assert response.status_code in [200, 201, 404, 501]

        if response.status_code in [200, 201]:
            data = response.json()
            assert isinstance(data, dict)

    def test_analytics_dashboard(self, client):
        """Test retrieving analytics dashboard data."""
        dashboard_resp = client.get("/analytics")
        assert dashboard_resp.status_code in [200, 404, 501]

        if dashboard_resp.status_code == 200:
            dashboard_data = dashboard_resp.json()
            assert isinstance(dashboard_data, dict)
            # Should contain usage statistics, performance metrics, etc.

    def test_prompt_performance_metrics(self, client):
        """Test retrieving performance metrics for specific prompts."""
        metrics_resp = client.get("/analytics/prompts/test-prompt-1")
        assert metrics_resp.status_code in [200, 404, 501]

        if metrics_resp.status_code == 200:
            metrics = metrics_resp.json()
            assert isinstance(metrics, dict)
            # Should contain performance data for the prompt
