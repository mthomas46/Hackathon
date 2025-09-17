#!/usr/bin/env python3
"""
Tests for Health Monitoring Module

Tests the health check and monitoring functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from services.shared.monitoring.health import (
    HealthStatus,
    HealthCheck,
    HealthMonitor,
    ServiceHealth,
    SystemHealth
)


class TestHealthStatus:
    """Test health status enum."""

    def test_health_status_values(self):
        """Test that health status values are correct."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.DOWN.value == "down"

    def test_health_status_ordering(self):
        """Test that health status levels have proper ordering."""
        assert HealthStatus.HEALTHY > HealthStatus.DEGRADED
        assert HealthStatus.DEGRADED > HealthStatus.UNHEALTHY
        assert HealthStatus.UNHEALTHY > HealthStatus.DOWN


class TestHealthCheck:
    """Test individual health check functionality."""

    def test_health_check_creation(self):
        """Test creating a health check."""
        check = HealthCheck(
            name="test_check",
            description="Test health check",
            check_function=lambda: True
        )

        assert check.name == "test_check"
        assert check.description == "Test health check"
        assert check.enabled is True

    def test_health_check_execution_success(self):
        """Test successful health check execution."""
        check = HealthCheck(
            name="success_check",
            check_function=lambda: True
        )

        result = check.execute()
        assert result.status == HealthStatus.HEALTHY
        assert result.details == {}
        assert result.response_time >= 0

    def test_health_check_execution_failure(self):
        """Test failed health check execution."""
        check = HealthCheck(
            name="failure_check",
            check_function=lambda: False
        )

        result = check.execute()
        assert result.status == HealthStatus.DOWN
        assert result.details == {}

    def test_health_check_with_exception(self):
        """Test health check that raises exception."""
        def failing_check():
            raise ValueError("Check failed")

        check = HealthCheck(
            name="exception_check",
            check_function=failing_check
        )

        result = check.execute()
        assert result.status == HealthStatus.UNHEALTHY
        assert "Check failed" in result.details["error"]

    @pytest.mark.asyncio
    async def test_async_health_check(self):
        """Test async health check execution."""
        async def async_check():
            await asyncio.sleep(0.01)
            return True

        check = HealthCheck(
            name="async_check",
            check_function=async_check,
            is_async=True
        )

        result = await check.execute_async()
        assert result.status == HealthStatus.HEALTHY


class TestHealthMonitor:
    """Test health monitor functionality."""

    def test_health_monitor_initialization(self):
        """Test health monitor initialization."""
        monitor = HealthMonitor(service_name="test-service")

        assert monitor.service_name == "test-service"
        assert len(monitor.checks) == 0

    def test_add_health_check(self):
        """Test adding health checks to monitor."""
        monitor = HealthMonitor(service_name="test")

        check = HealthCheck(
            name="test_check",
            check_function=lambda: True
        )

        monitor.add_check(check)
        assert len(monitor.checks) == 1
        assert monitor.checks["test_check"] == check

    def test_remove_health_check(self):
        """Test removing health checks from monitor."""
        monitor = HealthMonitor(service_name="test")

        check = HealthCheck(name="test_check", check_function=lambda: True)
        monitor.add_check(check)
        assert len(monitor.checks) == 1

        monitor.remove_check("test_check")
        assert len(monitor.checks) == 0

    def test_run_all_checks_success(self):
        """Test running all health checks successfully."""
        monitor = HealthMonitor(service_name="test")

        # Add multiple checks
        monitor.add_check(HealthCheck(
            name="check1",
            check_function=lambda: True
        ))
        monitor.add_check(HealthCheck(
            name="check2",
            check_function=lambda: True
        ))

        results = monitor.run_all_checks()
        assert len(results) == 2
        assert all(result.status == HealthStatus.HEALTHY for result in results.values())

    def test_run_all_checks_mixed(self):
        """Test running health checks with mixed results."""
        monitor = HealthMonitor(service_name="test")

        # Add mixed checks
        monitor.add_check(HealthCheck(
            name="healthy_check",
            check_function=lambda: True
        ))
        monitor.add_check(HealthCheck(
            name="unhealthy_check",
            check_function=lambda: False
        ))

        results = monitor.run_all_checks()
        assert len(results) == 2
        assert results["healthy_check"].status == HealthStatus.HEALTHY
        assert results["unhealthy_check"].status == HealthStatus.DOWN

    def test_overall_health_status(self):
        """Test calculating overall health status."""
        monitor = HealthMonitor(service_name="test")

        # All healthy
        monitor.add_check(HealthCheck(name="check1", check_function=lambda: True))
        monitor.add_check(HealthCheck(name="check2", check_function=lambda: True))

        overall = monitor.get_overall_health()
        assert overall == HealthStatus.HEALTHY

        # Mixed results
        monitor.add_check(HealthCheck(name="check3", check_function=lambda: False))

        overall = monitor.get_overall_health()
        assert overall == HealthStatus.UNHEALTHY

    def test_disabled_checks(self):
        """Test that disabled checks are skipped."""
        monitor = HealthMonitor(service_name="test")

        check = HealthCheck(
            name="disabled_check",
            check_function=lambda: True,
            enabled=False
        )
        monitor.add_check(check)

        results = monitor.run_all_checks()
        assert len(results) == 0


class TestServiceHealth:
    """Test service health representation."""

    def test_service_health_creation(self):
        """Test creating service health object."""
        health = ServiceHealth(
            service_name="test-service",
            status=HealthStatus.HEALTHY,
            version="1.0.0",
            uptime_seconds=3600
        )

        assert health.service_name == "test-service"
        assert health.status == HealthStatus.HEALTHY
        assert health.version == "1.0.0"
        assert health.uptime_seconds == 3600

    def test_service_health_with_checks(self):
        """Test service health with individual check results."""
        check_results = {
            "database": HealthStatus.HEALTHY,
            "cache": HealthStatus.DEGRADED,
            "api": HealthStatus.HEALTHY
        }

        health = ServiceHealth(
            service_name="test",
            status=HealthStatus.DEGRADED,
            checks=check_results
        )

        assert health.checks == check_results
        assert health.status == HealthStatus.DEGRADED

    def test_service_health_to_dict(self):
        """Test converting service health to dictionary."""
        health = ServiceHealth(
            service_name="test",
            status=HealthStatus.HEALTHY,
            version="1.0.0"
        )

        health_dict = health.to_dict()
        assert health_dict["service_name"] == "test"
        assert health_dict["status"] == "healthy"
        assert health_dict["version"] == "1.0.0"
        assert "timestamp" in health_dict


class TestSystemHealth:
    """Test system-wide health monitoring."""

    def test_system_health_creation(self):
        """Test creating system health object."""
        system_health = SystemHealth()

        assert len(system_health.services) == 0
        assert system_health.overall_status == HealthStatus.HEALTHY

    def test_add_service_health(self):
        """Test adding service health to system health."""
        system_health = SystemHealth()

        service_health = ServiceHealth(
            service_name="test-service",
            status=HealthStatus.HEALTHY
        )

        system_health.add_service(service_health)
        assert len(system_health.services) == 1
        assert system_health.services["test-service"] == service_health

    def test_overall_system_status(self):
        """Test calculating overall system status."""
        system_health = SystemHealth()

        # Add healthy service
        system_health.add_service(ServiceHealth(
            service_name="healthy-service",
            status=HealthStatus.HEALTHY
        ))

        assert system_health.overall_status == HealthStatus.HEALTHY

        # Add unhealthy service
        system_health.add_service(ServiceHealth(
            service_name="unhealthy-service",
            status=HealthStatus.DOWN
        ))

        assert system_health.overall_status == HealthStatus.UNHEALTHY

    def test_system_health_summary(self):
        """Test system health summary generation."""
        system_health = SystemHealth()

        system_health.add_service(ServiceHealth(
            service_name="service1",
            status=HealthStatus.HEALTHY
        ))
        system_health.add_service(ServiceHealth(
            service_name="service2",
            status=HealthStatus.DEGRADED
        ))

        summary = system_health.get_summary()
        assert summary["total_services"] == 2
        assert summary["healthy_services"] == 1
        assert summary["degraded_services"] == 1
        assert summary["unhealthy_services"] == 0
        assert summary["overall_status"] == "degraded"


if __name__ == "__main__":
    pytest.main([__file__])
