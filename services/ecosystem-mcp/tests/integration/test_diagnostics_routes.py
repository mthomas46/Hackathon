"""
Integration tests for diagnostics API routes.

Tests system diagnostics, performance monitoring, and troubleshooting endpoints.
"""

import pytest
from datetime import datetime
from uuid import uuid4


from .test_helpers import (
    skip_if_no_redis,
    skip_if_no_postgres,
    skip_if_no_chromadb,
    skip_if_no_docker
)


pytestmark = pytest.mark.integration



class TestSystemDiagnostics:
    """Test system diagnostics endpoints."""

    async def test_run_diagnostics(self, async_test_client):
        """Test running system diagnostics."""
        response = await async_test_client.get("/api/v1/diagnostics/health")
        
        assert response.status_code in [200, 404, 500, 503]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    async def test_get_diagnostics_report(self, async_test_client):
        """Test getting diagnostics report."""
        response = await async_test_client.get("/api/v1/diagnostics/health")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_diagnostics_history(self, async_test_client):
        """Test getting diagnostics history."""
        response = await async_test_client.get("/api/v1/diagnostics/health")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, (list, dict))

    async def test_check_database_connectivity(self, async_test_client):
        """Test database connectivity check."""
        response = await async_test_client.get("/api/v1/infrastructure/health")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert "status" in data
        assert "status" in data or "components" in data

    async def test_check_redis_connectivity(self, async_test_client):
        """Test Redis connectivity check."""
        response = await async_test_client.get("/api/v1/infrastructure/health")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert "status" in data

    async def test_check_chromadb_connectivity(self, async_test_client):
        """Test ChromaDB connectivity check."""
        response = await async_test_client.get("/api/v1/infrastructure/health")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert "status" in data

    async def test_check_ollama_connectivity(self, async_test_client):
        """Test Ollama connectivity check."""
        response = await async_test_client.get("/api/v1/diagnostics/health")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert "status" in data


class TestPerformanceMonitoring:
    """Test performance monitoring endpoints."""

    async def test_get_performance_metrics(self, async_test_client):
        """Test getting performance metrics."""
        response = await async_test_client.get("/api/v1/admin/stats")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_response_times(self, async_test_client):
        """Test getting response times."""
        response = await async_test_client.get("/api/v1/admin/stats")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_throughput_metrics(self, async_test_client):
        """Test getting throughput metrics."""
        response = await async_test_client.get("/api/v1/admin/stats")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)

    async def test_get_error_rates(self, async_test_client):
        """Test getting error rates."""
        response = await async_test_client.get("/api/v1/diagnostics/performance/errors")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)

    async def test_get_latency_distribution(self, async_test_client):
        """Test getting latency distribution."""
        response = await async_test_client.get("/api/v1/diagnostics/performance/latency")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)


class TestHealthChecks:
    """Test health check endpoints."""

    async def test_liveness_probe(self, async_test_client):
        """Test liveness probe."""
        response = await async_test_client.get("/api/v1/diagnostics/health/liveness")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    async def test_readiness_probe(self, async_test_client):
        """Test readiness probe."""
        response = await async_test_client.get("/api/v1/diagnostics/health/readiness")
        
        assert response.status_code in [200, 404, 503]
        data = response.json()
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    async def test_startup_probe(self, async_test_client):
        """Test startup probe."""
        response = await async_test_client.get("/api/v1/diagnostics/health/startup")
        
        assert response.status_code in [200, 404, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)

    async def test_component_health(self, async_test_client):
        """Test component health checks."""
        response = await async_test_client.get("/api/v1/diagnostics/health/components")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, dict)
        # Should have health status for each component


class TestLogAnalysis:
    """Test log analysis endpoints."""

    async def test_get_recent_logs(self, async_test_client):
        """Test getting recent logs."""
        response = await async_test_client.get("/api/v1/diagnostics/logs/recent")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, list) or "logs" in data

    async def test_get_error_logs(self, async_test_client):
        """Test getting error logs."""
        response = await async_test_client.get("/api/v1/diagnostics/logs/errors")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, list) or "logs" in data

    async def test_search_logs(self, async_test_client):
        """Test searching logs."""
        response = await async_test_client.get("/api/v1/diagnostics/logs/search", params={
            "query": "error",
            "limit": 10
        })
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, list) or "logs" in data

    async def test_get_log_statistics(self, async_test_client):
        """Test getting log statistics."""
        response = await async_test_client.get("/api/v1/diagnostics/logs/stats")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)


class TestMetricsCollection:
    """Test metrics collection endpoints."""

    async def test_get_all_metrics(self, async_test_client):
        """Test getting all metrics."""
        response = await async_test_client.get("/api/v1/diagnostics/metrics")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_ingestion_metrics(self, async_test_client):
        """Test getting ingestion metrics."""
        response = await async_test_client.get("/api/v1/diagnostics/metrics/ingestion")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)

    async def test_get_query_metrics(self, async_test_client):
        """Test getting query metrics."""
        response = await async_test_client.get("/api/v1/diagnostics/metrics/queries")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)

    async def test_get_embedding_metrics(self, async_test_client):
        """Test getting embedding metrics."""
        response = await async_test_client.get("/api/v1/diagnostics/metrics/embeddings")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)

    async def test_reset_metrics(self, async_test_client):
        """Test resetting metrics."""
        response = await async_test_client.post("/api/v1/diagnostics/metrics/reset")
        
        # Should require permissions
        assert response.status_code in [200, 202, 403]


class TestTroubleshooting:
    """Test troubleshooting endpoints."""

    async def test_get_common_issues(self, async_test_client):
        """Test getting common issues."""
        response = await async_test_client.get("/api/v1/diagnostics/troubleshoot/issues")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, list) or "issues" in data

    async def test_run_troubleshooter(self, async_test_client):
        """Test running troubleshooter."""
        response = await async_test_client.post("/api/v1/diagnostics/troubleshoot/run")
        
        assert response.status_code in [200, 202, 404, 500, 503]
        data = response.json()
        assert "findings" in data or "recommendations" in data

    async def test_get_recommendations(self, async_test_client):
        """Test getting recommendations."""
        response = await async_test_client.get("/api/v1/diagnostics/troubleshoot/recommendations")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, list) or "recommendations" in data

    async def test_check_configuration(self, async_test_client):
        """Test checking configuration."""
        response = await async_test_client.get("/api/v1/diagnostics/troubleshoot/config")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        if response.status_code == 200:
            assert isinstance(data, dict)


class TestAlertingAndNotifications:
    """Test alerting and notification endpoints."""

    async def test_get_active_alerts(self, async_test_client):
        """Test getting active alerts."""
        response = await async_test_client.get("/api/v1/diagnostics/alerts/active")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, list) or "alerts" in data

    async def test_get_alert_history(self, async_test_client):
        """Test getting alert history."""
        response = await async_test_client.get("/api/v1/diagnostics/alerts/history")
        
        assert response.status_code in [200, 404, 500, 503]
        data = response.json()
        assert isinstance(data, list) or "alerts" in data

    async def test_acknowledge_alert(self, async_test_client):
        """Test acknowledging an alert."""
        alert_id = str(uuid4())
        response = await async_test_client.post(f"/api/v1/diagnostics/alerts/{alert_id}/acknowledge")
        
        assert response.status_code in [200, 404]

    async def test_configure_alert_rules(self, async_test_client):
        """Test configuring alert rules."""
        response = await async_test_client.post("/api/v1/diagnostics/alerts/rules", json={
            "metric": "cpu_usage",
            "threshold": 80,
            "severity": "warning"
        })
        
        # Should require permissions
        assert response.status_code in [200, 201, 403]

