"""API integration tests for monitoring endpoints"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from main import app
from tests.fixtures.docker_compose_fixture import sample_compose_config


class TestMonitoringAPI:
    """API tests for monitoring endpoints"""

    @pytest.fixture
    def client(self):
        """Test client for the FastAPI app"""
        return TestClient(app)

    @pytest.fixture
    def mock_monitoring_service(self):
        """Mock monitoring service"""
        service = Mock()

        # Mock port conflict detection
        service.detect_port_conflicts = AsyncMock(return_value=[
            {"port": "8080", "services": ["service1", "service2"], "severity": "high"}
        ])

        # Mock inconsistency detection
        service.detect_config_inconsistencies = AsyncMock(return_value=[
            {
                "service_name": "test-service",
                "inconsistency_type": "missing_health_check",
                "description": "Missing health check",
                "severity": "medium",
                "suggested_fix": {"add_health_check": {}}
            }
        ])

        # Mock health status
        service.get_health_status = AsyncMock(return_value={
            "user-store": {"status": "healthy", "response_time": 0.1},
            "api-gateway": {"status": "unhealthy", "error_message": "Connection failed"}
        })

        # Mock drift status
        service.get_drift_status = AsyncMock(return_value={
            "total_unresolved": 2,
            "by_service": {
                "user-store": [{"type": "environment", "severity": "low"}]
            }
        })

        # Mock alerts
        service.get_alerts = AsyncMock(return_value=[
            {
                "id": 1,
                "type": "health",
                "severity": "error",
                "service": "api-gateway",
                "title": "Service Unhealthy",
                "message": "Service is not responding",
                "timestamp": "2024-01-01T00:00:00",
                "acknowledged": False
            }
        ])

        # Mock analytics
        service.get_analytics_report = AsyncMock(return_value={
            "generated_at": "2024-01-01T00:00:00",
            "risk_score": 25,
            "risk_level": "low",
            "drift_statistics": {"total_drifts": 5},
            "health_statistics": {"availability": 95.0},
            "recommendations": [],
            "summary": {"total_unresolved_drifts": 2}
        })

        # Mock config operations
        service.sync_service_configs = AsyncMock(return_value={
            "total_services": 5,
            "successful_syncs": 3,
            "failed_syncs": 2,
            "service_results": {}
        })

        service.get_service_config = AsyncMock(return_value={
            "service_name": "user-store",
            "config_hash": "abc123",
            "config_data": {"version": "1.0.0"},
            "timestamp": "2024-01-01T00:00:00",
            "source": "service_endpoint"
        })

        service.export_service_config = AsyncMock(return_value='{"version": "1.0.0"}')
        service.export_all_configs = AsyncMock(return_value={"user-store": "/tmp/config.json"})
        service.compare_service_configs = AsyncMock(return_value={"status": "compared", "changes_detected": True})
        service.get_service_config_history = AsyncMock(return_value=[])

        service.acknowledge_alert = AsyncMock(return_value=True)
        service.resolve_drift = AsyncMock(return_value=True)

        return service

    def test_get_health_status(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/health endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/health")

            assert response.status_code == 200
            data = response.json()
            assert "health_status" in data
            assert "user-store" in data["health_status"]
            assert data["health_status"]["user-store"]["status"] == "healthy"

    def test_get_drift_status(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/drift endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/drift")

            assert response.status_code == 200
            data = response.json()
            assert "drift_status" in data
            assert data["drift_status"]["total_unresolved"] == 2

    def test_get_alerts(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/alerts endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/alerts")

            assert response.status_code == 200
            data = response.json()
            assert "alerts" in data
            assert len(data["alerts"]) == 1
            assert data["alerts"][0]["service"] == "api-gateway"

    def test_get_monitoring_dashboard(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/dashboard endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/dashboard")

            assert response.status_code == 200
            data = response.json()
            assert "dashboard" in data
            assert "summary" in data["dashboard"]
            assert "health_status" in data["dashboard"]
            assert "drift_status" in data["dashboard"]
            assert "active_alerts" in data["dashboard"]

    def test_detect_port_conflicts(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/config/port-conflicts endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/config/port-conflicts")

            assert response.status_code == 200
            data = response.json()
            assert "port_conflicts" in data
            assert len(data["port_conflicts"]) == 1
            assert data["port_conflicts"][0]["port"] == "8080"

    def test_resolve_port_conflicts(self, client, mock_monitoring_service):
        """Test POST /api/v1/monitoring/config/resolve-port-conflicts endpoint"""
        # Mock the resolution method
        mock_monitoring_service.resolve_port_conflicts = AsyncMock(return_value={
            "status": "resolved",
            "conflicts_found": 1,
            "resolutions_applied": 1,
            "details": {"service1": {"status": "applied"}}
        })

        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.post("/api/v1/monitoring/config/resolve-port-conflicts")

            assert response.status_code == 200
            data = response.json()
            assert "port_conflict_resolution" in data
            assert data["port_conflict_resolution"]["status"] == "resolved"

    def test_detect_config_inconsistencies(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/config/inconsistencies endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/config/inconsistencies")

            assert response.status_code == 200
            data = response.json()
            assert "config_inconsistencies" in data
            assert len(data["config_inconsistencies"]) == 1
            assert data["config_inconsistencies"][0]["service_name"] == "test-service"

    def test_resolve_config_inconsistencies(self, client, mock_monitoring_service):
        """Test POST /api/v1/monitoring/config/resolve-inconsistencies endpoint"""
        # Mock the resolution method
        mock_monitoring_service.resolve_config_inconsistencies = AsyncMock(return_value={
            "status": "resolved",
            "inconsistencies_found": 3,
            "fixes_applied": 2,
            "details": {"service1": {"status": "applied"}}
        })

        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.post("/api/v1/monitoring/config/resolve-inconsistencies")

            assert response.status_code == 200
            data = response.json()
            assert "inconsistency_resolution" in data
            assert data["inconsistency_resolution"]["status"] == "resolved"

    def test_sync_service_configs(self, client, mock_monitoring_service):
        """Test POST /api/v1/monitoring/config/sync endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.post("/api/v1/monitoring/config/sync")

            assert response.status_code == 200
            data = response.json()
            assert "config_sync" in data
            assert data["config_sync"]["total_services"] == 5
            assert data["config_sync"]["successful_syncs"] == 3

    def test_get_service_config(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/config/{service_name} endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/config/user-store")

            assert response.status_code == 200
            data = response.json()
            assert "service_config" in data
            assert data["service_config"]["service_name"] == "user-store"

    def test_get_service_config_not_found(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/config/{service_name} for nonexistent service"""
        mock_monitoring_service.get_service_config = AsyncMock(return_value=None)

        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/config/nonexistent-service")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    def test_export_service_config(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/config/{service_name}/export endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/config/user-store/export?format=json")

            assert response.status_code == 200
            data = response.json()
            assert "service_name" in data
            assert "format" in data
            assert "content" in data
            assert data["service_name"] == "user-store"
            assert data["format"] == "json"

    def test_export_service_config_not_found(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/config/{service_name}/export for nonexistent service"""
        mock_monitoring_service.export_service_config = AsyncMock(return_value=None)

        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/config/nonexistent-service/export")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    def test_export_all_configs(self, client, mock_monitoring_service):
        """Test POST /api/v1/monitoring/config/export-all endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.post("/api/v1/monitoring/config/export-all?format=json")

            assert response.status_code == 200
            data = response.json()
            assert "export_result" in data
            assert "total_exports" in data["export_result"]
            assert "files" in data["export_result"]

    def test_compare_service_configs(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/config/{service_name}/compare endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/config/user-store/compare")

            assert response.status_code == 200
            data = response.json()
            assert "config_comparison" in data
            assert data["config_comparison"]["status"] == "compared"

    def test_get_service_config_history(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/config/{service_name}/history endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/config/user-store/history?limit=5")

            assert response.status_code == 200
            data = response.json()
            assert "config_history" in data
            assert isinstance(data["config_history"], list)

    def test_acknowledge_alert(self, client, mock_monitoring_service):
        """Test POST /api/v1/monitoring/alerts/{alert_id}/acknowledge endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.post("/api/v1/monitoring/alerts/1/acknowledge?user=test_user")

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "acknowledged" in data["message"]

    def test_acknowledge_alert_not_found(self, client, mock_monitoring_service):
        """Test POST /api/v1/monitoring/alerts/{alert_id}/acknowledge for nonexistent alert"""
        mock_monitoring_service.acknowledge_alert = AsyncMock(return_value=False)

        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.post("/api/v1/monitoring/alerts/999/acknowledge")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    def test_resolve_drift(self, client, mock_monitoring_service):
        """Test POST /api/v1/monitoring/drift/{drift_id}/resolve endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.post("/api/v1/monitoring/drift/1/resolve?action=fixed")

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "resolved" in data["message"]

    def test_resolve_drift_not_found(self, client, mock_monitoring_service):
        """Test POST /api/v1/monitoring/drift/{drift_id}/resolve for nonexistent drift"""
        mock_monitoring_service.resolve_drift = AsyncMock(return_value=False)

        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.post("/api/v1/monitoring/drift/999/resolve")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    def test_get_analytics_report(self, client, mock_monitoring_service):
        """Test GET /api/v1/monitoring/analytics endpoint"""
        with patch('api.routes.monitoring_service', mock_monitoring_service):
            response = client.get("/api/v1/monitoring/analytics")

            assert response.status_code == 200
            data = response.json()
            assert "analytics_report" in data
            assert "risk_score" in data["analytics_report"]
            assert "risk_level" in data["analytics_report"]
            assert "recommendations" in data["analytics_report"]

    def test_monitoring_service_unavailable(self, client):
        """Test endpoints when monitoring service is not initialized"""
        # Mock monitoring service as None
        with patch('api.routes.monitoring_service', None):
            response = client.get("/api/v1/monitoring/health")
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
            assert "not initialized" in data["detail"]

    @pytest.mark.parametrize("endpoint,method", [
        ("/api/v1/monitoring/health", "get"),
        ("/api/v1/monitoring/drift", "get"),
        ("/api/v1/monitoring/alerts", "get"),
        ("/api/v1/monitoring/dashboard", "get"),
        ("/api/v1/monitoring/config/port-conflicts", "get"),
        ("/api/v1/monitoring/config/inconsistencies", "get"),
        ("/api/v1/monitoring/analytics", "get"),
    ])
    def test_endpoints_handle_exceptions(self, client, mock_monitoring_service, endpoint, method):
        """Test that endpoints handle exceptions gracefully"""
        # Make the mocked method raise an exception
        if method == "get":
            mock_monitoring_service.get_health_status = AsyncMock(side_effect=Exception("Test error"))
        elif method == "detect_port_conflicts":
            mock_monitoring_service.detect_port_conflicts = AsyncMock(side_effect=Exception("Test error"))

        with patch('api.routes.monitoring_service', mock_monitoring_service):
            if method == "get":
                # Patch the specific method that the endpoint calls
                if "health" in endpoint:
                    mock_monitoring_service.get_health_status = AsyncMock(side_effect=Exception("Test error"))
                elif "drift" in endpoint:
                    mock_monitoring_service.get_drift_status = AsyncMock(side_effect=Exception("Test error"))
                elif "alerts" in endpoint:
                    mock_monitoring_service.get_alerts = AsyncMock(side_effect=Exception("Test error"))
                elif "dashboard" in endpoint:
                    mock_monitoring_service.get_monitoring_dashboard = AsyncMock(side_effect=Exception("Test error"))
                elif "port-conflicts" in endpoint:
                    mock_monitoring_service.detect_port_conflicts = AsyncMock(side_effect=Exception("Test error"))
                elif "inconsistencies" in endpoint:
                    mock_monitoring_service.detect_config_inconsistencies = AsyncMock(side_effect=Exception("Test error"))
                elif "analytics" in endpoint:
                    mock_monitoring_service.get_analytics_report = AsyncMock(side_effect=Exception("Test error"))

                response = client.get(endpoint)
                assert response.status_code == 500
                data = response.json()
                assert "detail" in data
