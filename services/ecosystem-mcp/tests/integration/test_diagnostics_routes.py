"""
Integration tests for diagnostics API routes.

Tests system diagnostics, performance monitoring, and troubleshooting endpoints.
"""

import pytest
import httpx
from datetime import datetime
from uuid import uuid4


pytestmark = pytest.mark.integration


@pytest.fixture
async def http_client():
    """HTTP client for API testing."""
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        yield client


class TestSystemDiagnostics:
    """Test system diagnostics endpoints."""

    async def test_run_diagnostics(self, http_client):
        """Test running system diagnostics."""
        response = await http_client.post("/api/v1/diagnostics/run")
        
        assert response.status_code in [200, 202]
        data = response.json()
        assert "diagnostics_id" in data or "status" in data

    async def test_get_diagnostics_report(self, http_client):
        """Test getting diagnostics report."""
        response = await http_client.get("/api/v1/diagnostics/report")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data or "checks" in data

    async def test_get_diagnostics_history(self, http_client):
        """Test getting diagnostics history."""
        response = await http_client.get("/api/v1/diagnostics/history")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "reports" in data

    async def test_check_database_connectivity(self, http_client):
        """Test database connectivity check."""
        response = await http_client.get("/api/v1/diagnostics/check/database")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["connected", "disconnected", "error"]

    async def test_check_redis_connectivity(self, http_client):
        """Test Redis connectivity check."""
        response = await http_client.get("/api/v1/diagnostics/check/redis")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    async def test_check_chromadb_connectivity(self, http_client):
        """Test ChromaDB connectivity check."""
        response = await http_client.get("/api/v1/diagnostics/check/chromadb")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    async def test_check_ollama_connectivity(self, http_client):
        """Test Ollama connectivity check."""
        response = await http_client.get("/api/v1/diagnostics/check/ollama")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestPerformanceMonitoring:
    """Test performance monitoring endpoints."""

    async def test_get_performance_metrics(self, http_client):
        """Test getting performance metrics."""
        response = await http_client.get("/api/v1/diagnostics/performance/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "cpu_usage" in data or "memory_usage" in data or "response_time" in data

    async def test_get_response_times(self, http_client):
        """Test getting response times."""
        response = await http_client.get("/api/v1/diagnostics/performance/response-times")
        
        assert response.status_code == 200
        data = response.json()
        assert "average" in data or "p95" in data or "p99" in data

    async def test_get_throughput_metrics(self, http_client):
        """Test getting throughput metrics."""
        response = await http_client.get("/api/v1/diagnostics/performance/throughput")
        
        assert response.status_code == 200
        data = response.json()
        assert "requests_per_second" in data or "documents_per_second" in data

    async def test_get_error_rates(self, http_client):
        """Test getting error rates."""
        response = await http_client.get("/api/v1/diagnostics/performance/errors")
        
        assert response.status_code == 200
        data = response.json()
        assert "error_rate" in data or "total_errors" in data

    async def test_get_latency_distribution(self, http_client):
        """Test getting latency distribution."""
        response = await http_client.get("/api/v1/diagnostics/performance/latency")
        
        assert response.status_code == 200
        data = response.json()
        assert "p50" in data or "p95" in data or "p99" in data


class TestHealthChecks:
    """Test health check endpoints."""

    async def test_liveness_probe(self, http_client):
        """Test liveness probe."""
        response = await http_client.get("/api/v1/diagnostics/health/liveness")
        
        assert response.status_code == 200
        data = response.json()
        assert "alive" in data or "status" in data

    async def test_readiness_probe(self, http_client):
        """Test readiness probe."""
        response = await http_client.get("/api/v1/diagnostics/health/readiness")
        
        assert response.status_code in [200, 503]
        data = response.json()
        assert "ready" in data or "status" in data

    async def test_startup_probe(self, http_client):
        """Test startup probe."""
        response = await http_client.get("/api/v1/diagnostics/health/startup")
        
        assert response.status_code in [200, 503]
        data = response.json()
        assert "started" in data or "status" in data

    async def test_component_health(self, http_client):
        """Test component health checks."""
        response = await http_client.get("/api/v1/diagnostics/health/components")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should have health status for each component


class TestLogAnalysis:
    """Test log analysis endpoints."""

    async def test_get_recent_logs(self, http_client):
        """Test getting recent logs."""
        response = await http_client.get("/api/v1/diagnostics/logs/recent")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "logs" in data

    async def test_get_error_logs(self, http_client):
        """Test getting error logs."""
        response = await http_client.get("/api/v1/diagnostics/logs/errors")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "logs" in data

    async def test_search_logs(self, http_client):
        """Test searching logs."""
        response = await http_client.get("/api/v1/diagnostics/logs/search", params={
            "query": "error",
            "limit": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "logs" in data

    async def test_get_log_statistics(self, http_client):
        """Test getting log statistics."""
        response = await http_client.get("/api/v1/diagnostics/logs/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_logs" in data or "error_count" in data


class TestMetricsCollection:
    """Test metrics collection endpoints."""

    async def test_get_all_metrics(self, http_client):
        """Test getting all metrics."""
        response = await http_client.get("/api/v1/diagnostics/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_ingestion_metrics(self, http_client):
        """Test getting ingestion metrics."""
        response = await http_client.get("/api/v1/diagnostics/metrics/ingestion")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data or "documents_per_second" in data

    async def test_get_query_metrics(self, http_client):
        """Test getting query metrics."""
        response = await http_client.get("/api/v1/diagnostics/metrics/queries")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_queries" in data or "average_response_time" in data

    async def test_get_embedding_metrics(self, http_client):
        """Test getting embedding metrics."""
        response = await http_client.get("/api/v1/diagnostics/metrics/embeddings")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_embeddings" in data or "embeddings_per_second" in data

    async def test_reset_metrics(self, http_client):
        """Test resetting metrics."""
        response = await http_client.post("/api/v1/diagnostics/metrics/reset")
        
        # Should require permissions
        assert response.status_code in [200, 202, 403]


class TestTroubleshooting:
    """Test troubleshooting endpoints."""

    async def test_get_common_issues(self, http_client):
        """Test getting common issues."""
        response = await http_client.get("/api/v1/diagnostics/troubleshoot/issues")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "issues" in data

    async def test_run_troubleshooter(self, http_client):
        """Test running troubleshooter."""
        response = await http_client.post("/api/v1/diagnostics/troubleshoot/run")
        
        assert response.status_code in [200, 202]
        data = response.json()
        assert "findings" in data or "recommendations" in data

    async def test_get_recommendations(self, http_client):
        """Test getting recommendations."""
        response = await http_client.get("/api/v1/diagnostics/troubleshoot/recommendations")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "recommendations" in data

    async def test_check_configuration(self, http_client):
        """Test checking configuration."""
        response = await http_client.get("/api/v1/diagnostics/troubleshoot/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data or "issues" in data


class TestAlertingAndNotifications:
    """Test alerting and notification endpoints."""

    async def test_get_active_alerts(self, http_client):
        """Test getting active alerts."""
        response = await http_client.get("/api/v1/diagnostics/alerts/active")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "alerts" in data

    async def test_get_alert_history(self, http_client):
        """Test getting alert history."""
        response = await http_client.get("/api/v1/diagnostics/alerts/history")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "alerts" in data

    async def test_acknowledge_alert(self, http_client):
        """Test acknowledging an alert."""
        alert_id = str(uuid4())
        response = await http_client.post(f"/api/v1/diagnostics/alerts/{alert_id}/acknowledge")
        
        assert response.status_code in [200, 404]

    async def test_configure_alert_rules(self, http_client):
        """Test configuring alert rules."""
        response = await http_client.post("/api/v1/diagnostics/alerts/rules", json={
            "metric": "cpu_usage",
            "threshold": 80,
            "severity": "warning"
        })
        
        # Should require permissions
        assert response.status_code in [200, 201, 403]

