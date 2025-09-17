#!/usr/bin/env python3
"""
Domain Layer Tests for Health Monitoring

Tests the core domain logic for health monitoring including value objects and services.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

from services.orchestrator.domain.health_monitoring.value_objects import (
    HealthStatus, HealthCheckResult, ServiceHealth, SystemHealth
)
from services.orchestrator.domain.health_monitoring.services import (
    HealthCheckService, SystemMonitoringService
)


class TestHealthStatus:
    """Test HealthStatus enum."""

    def test_health_status_values(self):
        """Test health status enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNKNOWN.value == "unknown"
        assert HealthStatus.MAINTENANCE.value == "maintenance"

    def test_is_healthy_property(self):
        """Test is_healthy property."""
        assert HealthStatus.HEALTHY.is_healthy is True
        assert HealthStatus.UNHEALTHY.is_healthy is False
        assert HealthStatus.DEGRADED.is_healthy is False
        assert HealthStatus.UNKNOWN.is_healthy is False
        assert HealthStatus.MAINTENANCE.is_healthy is False

    def test_is_operational_property(self):
        """Test is_operational property."""
        assert HealthStatus.HEALTHY.is_operational is True
        assert HealthStatus.DEGRADED.is_operational is True
        assert HealthStatus.UNHEALTHY.is_operational is False
        assert HealthStatus.UNKNOWN.is_operational is False
        assert HealthStatus.MAINTENANCE.is_operational is False

    def test_from_string(self):
        """Test creating HealthStatus from string."""
        assert HealthStatus.from_string("healthy") == HealthStatus.HEALTHY
        assert HealthStatus.from_string("unhealthy") == HealthStatus.UNHEALTHY
        assert HealthStatus.from_string("invalid") == HealthStatus.UNKNOWN

    def test_string_representation(self):
        """Test string representation."""
        assert str(HealthStatus.HEALTHY) == "healthy"
        assert str(HealthStatus.UNHEALTHY) == "unhealthy"


class TestHealthCheckResult:
    """Test HealthCheckResult value object."""

    def test_create_success_result(self):
        """Test creating a successful health check result."""
        result = HealthCheckResult.success("Service is healthy", {"version": "1.0.0"}, 150.5)

        assert result.status == HealthStatus.HEALTHY
        assert result.message == "Service is healthy"
        assert result.details == {"version": "1.0.0"}
        assert result.response_time_ms == 150.5
        assert result.error_message is None
        assert result.is_successful is True

    def test_create_failure_result(self):
        """Test creating a failed health check result."""
        result = HealthCheckResult.failure(
            "Service is down",
            "Connection timeout",
            {"endpoint": "/health"},
            5000.0
        )

        assert result.status == HealthStatus.UNHEALTHY
        assert result.message == "Service is down"
        assert result.error_message == "Connection timeout"
        assert result.response_time_ms == 5000.0
        assert result.is_successful is False

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = HealthCheckResult.success("OK", {"test": "data"}, 100.0)
        data = result.to_dict()

        assert data["status"] == "healthy"
        assert data["message"] == "OK"
        assert data["details"] == {"test": "data"}
        assert data["response_time_ms"] == 100.0
        assert "timestamp" in data
        assert "error_message" not in data

    def test_equality(self):
        """Test result equality."""
        result1 = HealthCheckResult.success("OK")
        result2 = HealthCheckResult.success("OK")
        result3 = HealthCheckResult.success("Different")

        assert result1 == result2
        assert result1 != result3


class TestServiceHealth:
    """Test ServiceHealth value object."""

    def test_create_service_health(self):
        """Test creating service health."""
        result = HealthCheckResult.success("OK")
        service_health = ServiceHealth(
            service_name="test_service",
            status=HealthStatus.HEALTHY,
            check_result=result,
            metadata={"version": "1.0.0"}
        )

        assert service_health.service_name == "test_service"
        assert service_health.status == HealthStatus.HEALTHY
        assert service_health.is_healthy is True
        assert service_health.is_operational is True
        assert service_health.check_result == result
        assert service_health.metadata == {"version": "1.0.0"}

    def test_update_status(self):
        """Test updating service status."""
        service_health = ServiceHealth("test", HealthStatus.HEALTHY)
        new_result = HealthCheckResult.failure("Failed")

        service_health.update_status(HealthStatus.UNHEALTHY, new_result)

        assert service_health.status == HealthStatus.UNHEALTHY
        assert service_health.is_healthy is False
        assert service_health.check_result == new_result

    def test_to_dict(self):
        """Test converting service health to dictionary."""
        result = HealthCheckResult.success("OK")
        service_health = ServiceHealth("test", HealthStatus.HEALTHY, check_result=result)
        data = service_health.to_dict()

        assert data["service_name"] == "test"
        assert data["status"] == "healthy"
        assert data["is_healthy"] is True
        assert data["is_operational"] is True
        assert "last_check" in data
        assert "last_result" in data


class TestSystemHealth:
    """Test SystemHealth value object."""

    def test_create_system_health(self):
        """Test creating system health."""
        service1 = ServiceHealth("service1", HealthStatus.HEALTHY)
        service2 = ServiceHealth("service2", HealthStatus.UNHEALTHY)

        system_health = SystemHealth.from_service_health_list([service1, service2])

        assert system_health.overall_status == HealthStatus.UNHEALTHY
        assert len(system_health.service_health) == 2
        assert system_health.healthy_services_count == 1
        assert system_health.total_services_count == 2

    def test_overall_status_all_healthy(self):
        """Test overall status when all services are healthy."""
        services = [
            ServiceHealth("service1", HealthStatus.HEALTHY),
            ServiceHealth("service2", HealthStatus.HEALTHY)
        ]

        system_health = SystemHealth.from_service_health_list(services)
        assert system_health.overall_status == HealthStatus.HEALTHY

    def test_overall_status_with_degraded(self):
        """Test overall status with degraded services."""
        services = [
            ServiceHealth("service1", HealthStatus.HEALTHY),
            ServiceHealth("service2", HealthStatus.DEGRADED)
        ]

        system_health = SystemHealth.from_service_health_list(services)
        assert system_health.overall_status == HealthStatus.DEGRADED

    def test_get_service_health(self):
        """Test getting specific service health."""
        service1 = ServiceHealth("service1", HealthStatus.HEALTHY)
        service2 = ServiceHealth("service2", HealthStatus.UNHEALTHY)

        system_health = SystemHealth.from_service_health_list([service1, service2])

        assert system_health.get_service_health("service1") == service1
        assert system_health.get_service_health("service2") == service2
        assert system_health.get_service_health("unknown").status == HealthStatus.UNKNOWN

    def test_to_dict(self):
        """Test converting system health to dictionary."""
        services = [ServiceHealth("service1", HealthStatus.HEALTHY)]
        system_health = SystemHealth.from_service_health_list(services)

        data = system_health.to_dict()

        assert data["overall_status"] == "healthy"
        assert data["overall_healthy"] is True
        assert data["summary"]["total_services"] == 1
        assert data["summary"]["healthy_services"] == 1
        assert "services" in data
        assert "timestamp" in data


class TestHealthCheckService:
    """Test HealthCheckService domain service."""

    @pytest.fixture
    def health_check_service(self):
        """Create health check service for testing."""
        return HealthCheckService()

    @pytest.mark.asyncio
    async def test_check_service_health_success(self, health_check_service):
        """Test successful service health check."""
        service_health = await health_check_service.check_service_health("test_service")

        # Since we don't have real service endpoints, this will simulate a successful check
        assert service_health.service_name == "test_service"
        assert service_health.check_result is not None
        assert isinstance(service_health.last_check, datetime)

    @pytest.mark.asyncio
    async def test_register_custom_check(self, health_check_service):
        """Test registering custom health check."""
        async def custom_check():
            return HealthCheckResult.success("Custom check passed")

        health_check_service.register_custom_check("custom_service", custom_check)

        service_health = await health_check_service.check_service_health("custom_service")

        assert service_health.service_name == "custom_service"
        assert service_health.status == HealthStatus.HEALTHY
        assert service_health.check_result.message == "Custom check passed"

    @pytest.mark.asyncio
    async def test_check_multiple_services(self, health_check_service):
        """Test checking multiple services concurrently."""
        services = ["service1", "service2", "service3"]
        results = await health_check_service.check_multiple_services(services)

        assert len(results) == 3
        assert all(r.service_name in services for r in results)

    def test_get_registered_checks(self, health_check_service):
        """Test getting registered custom checks."""
        async def check_func():
            return HealthCheckResult.success("OK")

        health_check_service.register_custom_check("test", check_func)

        registered = health_check_service.get_registered_checks()
        assert "test" in registered


class TestSystemMonitoringService:
    """Test SystemMonitoringService domain service."""

    @pytest.fixture
    def system_monitoring_service(self):
        """Create system monitoring service for testing."""
        health_check_service = HealthCheckService()
        return SystemMonitoringService(health_check_service)

    @pytest.mark.asyncio
    async def test_perform_system_health_check(self, system_monitoring_service):
        """Test performing system health check."""
        system_health = await system_monitoring_service.perform_system_health_check()

        assert isinstance(system_health, SystemHealth)
        assert system_health.overall_status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY, HealthStatus.UNKNOWN]
        assert len(system_health.service_health) > 0

    def test_get_known_services(self, system_monitoring_service):
        """Test getting known services."""
        services = system_monitoring_service.get_known_services()

        assert isinstance(services, list)
        assert len(services) > 0
        assert "orchestrator" in services

    def test_add_remove_known_service(self, system_monitoring_service):
        """Test adding and removing known services."""
        system_monitoring_service.add_known_service("new_service")
        assert "new_service" in system_monitoring_service.get_known_services()

        system_monitoring_service.remove_known_service("new_service")
        assert "new_service" not in system_monitoring_service.get_known_services()

    def test_get_system_info(self, system_monitoring_service):
        """Test getting system information."""
        info = system_monitoring_service.get_system_info()

        assert info["service"] == "orchestrator"
        assert "version" in info
        assert "capabilities" in info
        assert "known_services" in info

    def test_get_system_config(self, system_monitoring_service):
        """Test getting system configuration."""
        config = system_monitoring_service.get_system_config()

        assert isinstance(config, dict)
        assert "redis_enabled" in config
        assert "service_discovery_enabled" in config

    def test_get_system_metrics(self, system_monitoring_service):
        """Test getting system metrics."""
        metrics = system_monitoring_service.get_system_metrics()

        assert isinstance(metrics, dict)
        assert "service" in metrics
        assert "timestamp" in metrics

    def test_is_system_ready(self, system_monitoring_service):
        """Test system readiness check."""
        is_ready = system_monitoring_service.is_system_ready()

        assert isinstance(is_ready, bool)
        # System should be ready in our mock implementation
        assert is_ready is True

    def test_update_system_metrics(self, system_monitoring_service):
        """Test updating system metrics."""
        system_monitoring_service.update_system_metrics({"active_workflows": 5})

        metrics = system_monitoring_service.get_system_metrics()
        assert metrics.get("active_workflows") == 5
