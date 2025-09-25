"""Tests for Monitoring System."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

from services.shared.infrastructure.monitoring.monitoring_system import (
    MonitoringSystem,
    ServiceStatus,
    DashboardMetrics,
    Alert,
)


class TestMonitoringSystem:
    """Test monitoring system functionality."""

    @pytest.fixture
    def monitoring_system(self):
        """Create a test monitoring system instance."""
        return MonitoringSystem()

    @pytest.fixture
    def sample_service_status(self):
        """Create a sample service status for testing."""
        return ServiceStatus(
            service_name="test-service",
            status="healthy",
            response_time=0.125,
            last_check=datetime.now(timezone.utc),
            uptime=99.5,
            version="1.0.0"
        )

    def test_initialization(self, monitoring_system):
        """Test monitoring system initialization."""
        assert monitoring_system.services == {}
        assert monitoring_system.alerts == []
        assert monitoring_system.metrics_history == []

    def test_add_service(self, monitoring_system, sample_service_status):
        """Test adding a service to monitoring."""
        monitoring_system.services["test-service"] = sample_service_status

        assert "test-service" in monitoring_system.services
        assert monitoring_system.services["test-service"] == sample_service_status

    def test_update_dashboard_metrics_no_services(self, monitoring_system):
        """Test updating dashboard metrics with no services."""
        monitoring_system._update_dashboard_metrics()

        # Should not crash and metrics_history should remain empty
        assert len(monitoring_system.metrics_history) == 0

    def test_update_dashboard_metrics_with_services(self, monitoring_system, sample_service_status):
        """Test updating dashboard metrics with services."""
        # Add multiple services
        services = {
            "service-1": ServiceStatus("service-1", "healthy", 0.1, datetime.now(timezone.utc), 99.0, "1.0.0"),
            "service-2": ServiceStatus("service-2", "warning", 0.2, datetime.now(timezone.utc), 95.0, "1.0.0"),
            "service-3": ServiceStatus("service-3", "critical", 0.5, datetime.now(timezone.utc), 80.0, "1.0.0"),
            "service-4": ServiceStatus("service-4", "unknown", 1.0, datetime.now(timezone.utc), 0.0, "1.0.0"),
        }

        monitoring_system.services = services

        # Mock the logger get_all_loggers function
        with patch('services.shared.infrastructure.monitoring.monitoring_system.get_all_loggers') as mock_get_loggers:
            mock_logger1 = MagicMock()
            mock_logger2 = MagicMock()

            # Mock health status with metrics
            mock_logger1.get_health_status.return_value = {
                "metrics": {"request_count": 100, "error_count": 5}
            }
            mock_logger2.get_health_status.return_value = {
                "metrics": {"request_count": 200, "error_count": 10}
            }

            mock_get_loggers.return_value = {"logger1": mock_logger1, "logger2": mock_logger2}

            monitoring_system._update_dashboard_metrics()

            assert len(monitoring_system.metrics_history) == 1
            metrics = monitoring_system.metrics_history[0]

            assert metrics.total_services == 4
            assert metrics.healthy_services == 1
            assert metrics.warning_services == 1
            assert metrics.critical_services == 1
            assert metrics.unknown_services == 1
            assert metrics.active_alerts == 0  # No alerts
            assert metrics.total_requests == 300  # 100 + 200
            assert metrics.error_rate == 15/300  # (5 + 10) / 300

    def test_get_latest_metrics_no_history(self, monitoring_system):
        """Test getting latest metrics when no history exists."""
        result = monitoring_system._get_latest_metrics()
        assert result is None

    def test_get_latest_metrics_with_history(self, monitoring_system):
        """Test getting latest metrics when history exists."""
        metrics1 = DashboardMetrics(
            total_services=1, healthy_services=1, warning_services=0,
            critical_services=0, unknown_services=0, active_alerts=0,
            avg_response_time=0.1, total_requests=100, error_rate=0.05
        )
        metrics2 = DashboardMetrics(
            total_services=2, healthy_services=1, warning_services=1,
            critical_services=0, unknown_services=0, active_alerts=1,
            avg_response_time=0.15, total_requests=150, error_rate=0.08
        )

        monitoring_system.metrics_history = [metrics1, metrics2]

        result = monitoring_system._get_latest_metrics()
        assert result == metrics2

    def test_get_active_alerts(self, monitoring_system):
        """Test getting active (unresolved) alerts."""
        resolved_alert = Alert(
            alert_id="alert-1",
            service_name="service-1",
            alert_type="error",
            severity="high",
            message="Test alert 1",
            timestamp=datetime.now(timezone.utc),
            resolved=True,
            resolved_at=datetime.now(timezone.utc)
        )

        unresolved_alert = Alert(
            alert_id="alert-2",
            service_name="service-2",
            alert_type="warning",
            severity="medium",
            message="Test alert 2",
            timestamp=datetime.now(timezone.utc),
            resolved=False
        )

        monitoring_system.alerts = [resolved_alert, unresolved_alert]

        active_alerts = monitoring_system._get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0] == unresolved_alert

    def test_build_service_summary(self, monitoring_system, sample_service_status):
        """Test building service status summary."""
        monitoring_system.services = {
            "service-1": sample_service_status,
            "service-2": ServiceStatus(
                "service-2", "warning", 0.25,
                datetime.now(timezone.utc), 95.0, "2.0.0"
            )
        }

        summary = monitoring_system._build_service_summary()

        assert len(summary) == 2

        # Find service-1 in summary
        service1_summary = next(s for s in summary if s["name"] == "service-1")
        assert service1_summary["status"] == "healthy"
        assert service1_summary["response_time"] == 0.125
        assert service1_summary["uptime"] == 99.5
        assert service1_summary["version"] == "1.0.0"

    def test_format_alerts(self, monitoring_system):
        """Test formatting alerts for dashboard display."""
        alerts = [
            Alert(
                alert_id="alert-1",
                service_name="service-1",
                alert_type="error",
                severity="high",
                message="Critical error occurred",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                resolved=False
            )
        ]

        formatted = monitoring_system._format_alerts(alerts)

        assert len(formatted) == 1
        alert = formatted[0]
        assert alert["id"] == "alert-1"
        assert alert["service"] == "service-1"
        assert alert["type"] == "error"
        assert alert["severity"] == "high"
        assert alert["message"] == "Critical error occurred"
        assert alert["timestamp"] == "2024-01-01T12:00:00+00:00"

    def test_format_metrics_with_data(self, monitoring_system):
        """Test formatting metrics when data is available."""
        metrics = DashboardMetrics(
            total_services=5,
            healthy_services=3,
            warning_services=1,
            critical_services=1,
            unknown_services=0,
            active_alerts=2,
            avg_response_time=0.15,
            total_requests=1000,
            error_rate=0.05
        )

        formatted = monitoring_system._format_metrics(metrics)

        assert formatted["total_services"] == 5
        assert formatted["healthy_services"] == 3
        assert formatted["warning_services"] == 1
        assert formatted["critical_services"] == 1
        assert formatted["unknown_services"] == 0
        assert formatted["active_alerts"] == 2
        assert formatted["avg_response_time"] == 0.15
        assert formatted["total_requests"] == 1000
        assert formatted["error_rate"] == 0.05

    def test_format_metrics_no_data(self, monitoring_system):
        """Test formatting metrics when no data is available."""
        formatted = monitoring_system._format_metrics(None)

        assert formatted == {}

    def test_get_dashboard_data_no_services(self, monitoring_system):
        """Test getting dashboard data when no services are monitored."""
        result = monitoring_system.get_dashboard_data()

        assert result == {"error": "No services monitored"}

    def test_get_dashboard_data_with_services(self, monitoring_system, sample_service_status):
        """Test getting dashboard data when services are available."""
        monitoring_system.services = {"test-service": sample_service_status}

        # Add some metrics history
        metrics = DashboardMetrics(
            total_services=1, healthy_services=1, warning_services=0,
            critical_services=0, unknown_services=0, active_alerts=0,
            avg_response_time=0.125, total_requests=100, error_rate=0.02
        )
        monitoring_system.metrics_history = [metrics]

        result = monitoring_system.get_dashboard_data()

        assert "timestamp" in result
        assert len(result["services"]) == 1
        assert result["services"][0]["name"] == "test-service"
        assert "alerts" in result
        assert "metrics" in result

        # Verify metrics are included
        assert result["metrics"]["total_services"] == 1
        assert result["metrics"]["healthy_services"] == 1
        assert result["metrics"]["avg_response_time"] == 0.125

    def test_store_metrics_history_retention(self, monitoring_system):
        """Test that metrics history respects retention policy."""
        # Add 101 metrics (over the limit of 100)
        for i in range(101):
            metrics = DashboardMetrics(
                total_services=1, healthy_services=1, warning_services=0,
                critical_services=0, unknown_services=0, active_alerts=0,
                avg_response_time=0.1, total_requests=100, error_rate=0.01
            )
            monitoring_system.metrics_history.append(metrics)

        # Call the store method which should trim history
        monitoring_system._store_metrics_history(metrics)

        # Should only keep the last 100 metrics
        assert len(monitoring_system.metrics_history) == 100

    def test_calculate_service_status_counts(self, monitoring_system):
        """Test calculating service status counts."""
        monitoring_system.services = {
            "service-1": ServiceStatus("service-1", "healthy", 0.1, datetime.now(timezone.utc), 99.0, "1.0.0"),
            "service-2": ServiceStatus("service-2", "healthy", 0.2, datetime.now(timezone.utc), 98.0, "1.0.0"),
            "service-3": ServiceStatus("service-3", "warning", 0.3, datetime.now(timezone.utc), 95.0, "1.0.0"),
            "service-4": ServiceStatus("service-4", "critical", 0.4, datetime.now(timezone.utc), 80.0, "1.0.0"),
            "service-5": ServiceStatus("service-5", "unknown", 0.5, datetime.now(timezone.utc), 0.0, "1.0.0"),
        }

        # Add an active alert
        monitoring_system.alerts = [
            Alert("alert-1", "service-1", "error", "high", "Test alert",
                  datetime.now(timezone.utc), resolved=False)
        ]

        counts = monitoring_system._calculate_service_status_counts()

        assert counts["total"] == 5
        assert counts["healthy"] == 2
        assert counts["warning"] == 1
        assert counts["critical"] == 1
        assert counts["unknown"] == 1
        assert counts["active_alerts"] == 1

    def test_calculate_performance_metrics(self, monitoring_system):
        """Test calculating average response time."""
        monitoring_system.services = {
            "service-1": ServiceStatus("service-1", "healthy", 0.1, datetime.now(timezone.utc), 99.0, "1.0.0"),
            "service-2": ServiceStatus("service-2", "healthy", 0.3, datetime.now(timezone.utc), 98.0, "1.0.0"),
            "service-3": ServiceStatus("service-3", "warning", None, datetime.now(timezone.utc), 95.0, "1.0.0"),  # No response time
        }

        metrics = monitoring_system._calculate_performance_metrics()

        # Average of 0.1 and 0.3 = 0.2
        assert metrics["avg_response_time"] == 0.2

    def test_calculate_performance_metrics_no_response_times(self, monitoring_system):
        """Test calculating performance metrics when no response times are available."""
        monitoring_system.services = {
            "service-1": ServiceStatus("service-1", "healthy", None, datetime.now(timezone.utc), 99.0, "1.0.0"),
            "service-2": ServiceStatus("service-2", "warning", None, datetime.now(timezone.utc), 95.0, "1.0.0"),
        }

        metrics = monitoring_system._calculate_performance_metrics()

        assert metrics["avg_response_time"] == 0.0

    @patch('services.shared.infrastructure.monitoring.monitoring_system.get_all_loggers')
    def test_calculate_request_metrics(self, mock_get_loggers, monitoring_system):
        """Test calculating request metrics from loggers."""
        # Mock loggers with health status
        mock_logger1 = MagicMock()
        mock_logger1.get_health_status.return_value = {
            "metrics": {"request_count": 150, "error_count": 3}
        }

        mock_logger2 = MagicMock()
        mock_logger2.get_health_status.return_value = {
            "metrics": {"request_count": 250, "error_count": 7}
        }

        mock_get_loggers.return_value = {"logger1": mock_logger1, "logger2": mock_logger2}

        metrics = monitoring_system._calculate_request_metrics()

        assert metrics["total_requests"] == 400  # 150 + 250
        assert metrics["error_rate"] == 10/400   # (3 + 7) / 400 = 0.025

    @patch('services.shared.infrastructure.monitoring.monitoring_system.get_all_loggers')
    def test_calculate_request_metrics_no_loggers(self, mock_get_loggers, monitoring_system):
        """Test calculating request metrics when no loggers are available."""
        mock_get_loggers.return_value = {}

        metrics = monitoring_system._calculate_request_metrics()

        assert metrics["total_requests"] == 0
        assert metrics["error_rate"] == 0.0

    @patch('services.shared.infrastructure.monitoring.monitoring_system.get_all_loggers')
    def test_calculate_request_metrics_missing_metrics(self, mock_get_loggers, monitoring_system):
        """Test calculating request metrics when loggers have missing metrics."""
        mock_logger = MagicMock()
        mock_logger.get_health_status.return_value = {"metrics": {}}

        mock_get_loggers.return_value = {"logger1": mock_logger}

        metrics = monitoring_system._calculate_request_metrics()

        assert metrics["total_requests"] == 0
        assert metrics["error_rate"] == 0.0
