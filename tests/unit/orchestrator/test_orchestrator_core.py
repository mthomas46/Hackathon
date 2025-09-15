"""Orchestrator Service core functionality tests.

Tests service coordination, workflow management, and core orchestration operations.
Focused on essential orchestrator operations following TDD principles.
"""
import pytest
import importlib.util, os
from fastapi.testclient import TestClient

from .test_utils import load_orchestrator_service, _assert_http_ok, sample_ingestion_request, sample_workflow_request


@pytest.fixture(scope="module")
def client():
    """Test client fixture for orchestrator service."""
    app = load_orchestrator_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestOrchestratorCore:
    """Test core orchestrator functionality."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_info_endpoint(self, client):
        """Test service info endpoint."""
        response = client.get("/info")
        _assert_http_ok(response)

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data

        service_data = data["data"]
        assert "service" in service_data
        assert service_data["service"] == "orchestrator"
        assert "version" in service_data

    def test_system_health_endpoint(self, client):
        """Test system-wide health monitoring."""
        response = client.get("/health/system")
        _assert_http_ok(response)

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data

        health_data = data["data"]
        assert "overall_status" in health_data
        assert "services" in health_data

    def test_workflows_endpoint(self, client):
        """Test workflows listing."""
        response = client.get("/workflows")
        _assert_http_ok(response)

        data = response.json()
        assert "success" in data
        assert "data" in data

        workflows_data = data["data"]
        assert "workflows" in workflows_data

        workflows = workflows_data["workflows"]
        assert isinstance(workflows, list)
        assert len(workflows) > 0

    def test_workflows_history_endpoint(self, client):
        """Test workflow history."""
        response = client.get("/workflows/history")
        _assert_http_ok(response)

        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_metrics_endpoint(self, client):
        """Test service metrics."""
        response = client.get("/metrics")
        _assert_http_ok(response)

        data = response.json()
        assert "data" in data
        metrics_data = data["data"]
        assert "service" in metrics_data
        assert "routes" in metrics_data

    def test_ready_endpoint(self, client):
        """Test readiness check."""
        response = client.get("/ready")
        _assert_http_ok(response)

        data = response.json()
        assert "ready" in data
        assert "service" in data
        assert data["ready"] == True

    def test_config_effective_endpoint(self, client):
        """Test effective configuration."""
        response = client.get("/config/effective")
        _assert_http_ok(response)

        data = response.json()
        # Should return some configuration data
        assert isinstance(data, dict)

    def test_ingest_endpoint(self, client):
        """Test data ingestion request."""
        ingest_data = {
            "source": "github",
            "scope": {"repo": "test/repo"},
            "correlation_id": "ingest-test-123"
        }

        response = client.post("/ingest", json=ingest_data)
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["status"] == "accepted"
        assert "source" in data

    def test_workflows_run_endpoint(self, client):
        """Test workflow execution."""
        workflow_data = {
            "correlation_id": "workflow-test-456",
            "scope": {"target": "all"}
        }

        response = client.post("/workflows/run", json=workflow_data)
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["status"] == "started"
        assert "steps" in data
        assert "correlation_id" in data
        assert "saga_id" in data

        steps = data["steps"]
        assert isinstance(steps, list)
        assert len(steps) > 0

    def test_registry_register_endpoint(self, client):
        """Test service registration."""
        service_data = {
            "name": "test-service",
            "base_url": "http://test-service:8080",
            "openapi_url": "http://test-service:8080/openapi.json",
            "endpoints": [{"path": "/health", "method": "GET"}],
            "metadata": {"version": "1.0.0"}
        }

        response = client.post("/registry/register", json=service_data)
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert data["status"] == "registered"
        assert "count" in data

    def test_registry_list_endpoint(self, client):
        """Test service registry listing."""
        # First register a service
        service_data = {
            "name": "test-service-2",
            "base_url": "http://test-service-2:8080"
        }
        client.post("/registry/register", json=service_data)

        # Then list services
        response = client.get("/registry")
        _assert_http_ok(response)

        data = response.json()
        assert "services" in data

        services = data["services"]
        assert isinstance(services, list)
        assert len(services) >= 1

    def test_demo_e2e_endpoint(self, client):
        """Test end-to-end demo."""
        demo_data = {
            "format": "json",
            "log_service": "orchestrator",
            "log_level": "info",
            "log_limit": 50
        }

        response = client.post("/demo/e2e", json=demo_data)
        _assert_http_ok(response)

        data = response.json()
        assert "summary" in data
        assert "log_analysis" in data

    def test_peers_endpoint(self, client):
        """Test peer orchestrators listing."""
        response = client.get("/peers")
        _assert_http_ok(response)

        data = response.json()
        assert "peers" in data
        assert "count" in data

        peers = data["peers"]
        assert isinstance(peers, list)

    def test_docstore_save_endpoint(self, client):
        """Test document store save shortcut."""
        doc_data = {
            "id": "test-doc-123",
            "content": "Test document content",
            "content_hash": "hash123",
            "metadata": {"title": "Test Doc"}
        }

        response = client.post("/docstore/save", json=doc_data)
        _assert_http_ok(response)

        data = response.json()
        assert "id" in data
        assert "content_hash" in data

    def test_infrastructure_dlq_stats_endpoint(self, client):
        """Test DLQ statistics."""
        response = client.get("/infrastructure/dlq/stats")
        _assert_http_ok(response)

        data = response.json()
        # Should return DLQ statistics
        assert isinstance(data, dict)

    def test_infrastructure_dlq_retry_endpoint(self, client):
        """Test DLQ retry functionality."""
        response = client.post("/infrastructure/dlq/retry")
        _assert_http_ok(response)

        data = response.json()
        assert "retried_events" in data
        assert "total_events" in data

    def test_infrastructure_saga_stats_endpoint(self, client):
        """Test saga statistics."""
        response = client.get("/infrastructure/saga/stats")
        _assert_http_ok(response)

        data = response.json()
        # Should return saga statistics
        assert isinstance(data, dict)

    def test_infrastructure_saga_status_endpoint(self, client):
        """Test saga status retrieval."""
        response = client.get("/infrastructure/saga/existing_saga")
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data

    def test_infrastructure_saga_not_found_endpoint(self, client):
        """Test saga status for non-existent saga."""
        response = client.get("/infrastructure/saga/non_existent_saga")

        # Should return 404 or error response
        assert response.status_code in [404, 422]

    def test_infrastructure_events_history_endpoint(self, client):
        """Test event history retrieval."""
        response = client.get("/infrastructure/events/history")
        _assert_http_ok(response)

        data = response.json()
        assert "events" in data
        assert "count" in data

    def test_infrastructure_events_replay_endpoint(self, client):
        """Test event replay functionality."""
        response = client.post("/infrastructure/events/replay", json={})
        _assert_http_ok(response)

        data = response.json()
        assert "replayed_events" in data
        assert "count" in data

    def test_infrastructure_tracing_stats_endpoint(self, client):
        """Test tracing statistics."""
        response = client.get("/infrastructure/tracing/stats")
        _assert_http_ok(response)

        data = response.json()
        # Should return tracing statistics
        assert isinstance(data, dict)

    def test_infrastructure_tracing_trace_endpoint(self, client):
        """Test trace retrieval."""
        response = client.get("/infrastructure/tracing/trace/test-trace-123")
        _assert_http_ok(response)

        data = response.json()
        assert "trace_id" in data
        assert "spans" in data

    def test_infrastructure_tracing_service_endpoint(self, client):
        """Test service trace retrieval."""
        response = client.get("/infrastructure/tracing/service/doc-store")
        _assert_http_ok(response)

        data = response.json()
        assert "service_name" in data
        assert "traces" in data
        assert "total" in data
        assert data["service_name"] == "doc-store"

    def test_infrastructure_events_clear_endpoint(self, client):
        """Test event clearing functionality."""
        response = client.post("/infrastructure/events/clear")
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert "cleared_count" in data
        assert data["status"] == "cleared"

    def test_jobs_recalc_quality_endpoint(self, client):
        """Test quality recalculation job."""
        response = client.post("/jobs/recalc-quality")
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert "flagged" in data
        assert "timestamp" in data
        assert isinstance(data["flagged"], int)

    def test_jobs_notify_consolidation_endpoint(self, client):
        """Test consolidation notification job."""
        consolidation_data = {
            "min_confidence": 0.8,
            "webhook_url": "https://example.com/webhook",
            "limit": 10
        }

        response = client.post("/jobs/notify-consolidation", json=consolidation_data)
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data

    def test_registry_poll_openapi_endpoint(self, client):
        """Test OpenAPI polling functionality."""
        response = client.post("/registry/poll-openapi", json={})
        _assert_http_ok(response)

        data = response.json()
        assert "results" in data

    def test_natural_language_query_endpoint(self, client):
        """Test natural language query processing."""
        query_data = {
            "query": "analyze the documentation for consistency issues"
        }

        response = client.post("/query", json=query_data)
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert "interpretation" in data

        interpretation = data["interpretation"]
        assert "intent" in interpretation
        assert "confidence" in interpretation
        assert "entities" in interpretation

    def test_execute_natural_language_query_endpoint(self, client):
        """Test natural language query execution."""
        execute_data = {
            "query": "run document analysis workflow"
        }

        response = client.post("/query/execute", json=execute_data)
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert "execution" in data
        assert "interpretation" in data
        assert isinstance(data["execution"], dict)
        assert isinstance(data["interpretation"], dict)

    def test_request_report_endpoint(self, client):
        """Test report request functionality."""
        report_data = {
            "format": "json",
            "type": "summary"
        }

        response = client.post("/report/request", json=report_data)
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data
        assert "content" in data
        assert "report_type" in data
        assert "generated_at" in data
        assert data["status"] == "generated"
        assert data["report_type"] == "summary"

    def test_summarization_suggest_endpoint(self, client):
        """Test summarization suggestion."""
        suggest_data = {
            "content": "This is a long document that needs summarization."
        }

        response = client.post("/summarization/suggest", json=suggest_data)
        _assert_http_ok(response)

        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0

        suggestion = data["suggestions"][0]
        assert "confidence" in suggestion
        assert "reason" in suggestion
        assert "text" in suggestion

    def test_get_prompt_endpoint(self, client):
        """Test prompt retrieval."""
        response = client.get("/prompts/search/analysis/consistency_check")
        _assert_http_ok(response)

        data = response.json()
        assert "category" in data
        assert "name" in data
        assert "prompt" in data
        assert "version" in data
        assert data["category"] == "analysis"
        assert data["name"] == "consistency_check"

    def test_list_prompt_categories_endpoint(self, client):
        """Test prompt categories listing."""
        response = client.get("/prompts/categories")
        _assert_http_ok(response)

        data = response.json()
        assert "categories" in data

        categories = data["categories"]
        assert isinstance(categories, list)

    def test_log_prompt_usage_endpoint(self, client):
        """Test prompt usage logging."""
        usage_data = {
            "prompt_id": "analysis.consistency_check",
            "input_tokens": 150,
            "output_tokens": 75,
            "response_time_ms": 1250.5,
            "success": True
        }

        response = client.post("/prompts/usage", json=usage_data)
        _assert_http_ok(response)

        data = response.json()
        assert "status" in data

    def test_list_services_endpoint(self, client):
        """Test services listing."""
        response = client.get("/services")
        _assert_http_ok(response)

        data = response.json()
        assert "services" in data

        services = data["services"]
        assert isinstance(services, list)
