#!/usr/bin/env python3
"""
Application Layer Tests for Health Monitoring

Tests the application layer including use cases, commands, and queries.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from services.orchestrator.application.health_monitoring.commands import (
    CheckSystemHealthCommand, CheckServiceHealthCommand
)
from services.orchestrator.application.health_monitoring.use_cases import (
    CheckSystemHealthUseCase, CheckServiceHealthUseCase
)
from tests.unit.orchestrator.test_base import BaseApplicationTest, HealthMonitoringTestMixin


class TestCheckSystemHealthUseCase(BaseApplicationTest, HealthMonitoringTestMixin):
    """Test CheckSystemHealthUseCase."""

    def get_use_case_class(self):
        return CheckSystemHealthUseCase

    def get_repository_mocks(self):
        return {"system_monitoring_service": AsyncMock()}

    @pytest.mark.asyncio
    async def test_check_system_health_success(self):
        """Test successful system health check."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["system_monitoring_service"]

        # Setup mock
        mock_result = {"status": "healthy", "services": {}}
        mock_service.perform_system_health_check.return_value = mock_result

        # Execute
        command = CheckSystemHealthCommand(include_metrics=True)
        result = await use_case.execute(command)

        # Assert
        self.assert_use_case_success(result)
        mock_service.perform_system_health_check.assert_called_once_with(
            timeout_seconds=5.0, include_metrics=True
        )


class TestCheckServiceHealthUseCase(BaseApplicationTest, HealthMonitoringTestMixin):
    """Test CheckServiceHealthUseCase."""

    def get_use_case_class(self):
        return CheckServiceHealthUseCase

    def get_repository_mocks(self):
        return {"health_check_service": Mock()}

    @pytest.mark.asyncio
    async def test_check_service_health_success(self):
        """Test successful service health check."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["health_check_service"]

        # Setup mock
        mock_result = self.create_test_health_check(service_name="test_service", status="healthy")
        mock_service.check_service_health.return_value = mock_result

        # Execute
        command = CheckServiceHealthCommand(service_name="test_service")
        result = await use_case.execute(command)

        # Assert
        self.assert_use_case_success(result)
        mock_service.check_service_health.assert_called_once_with("test_service")


class TestGetSystemHealthUseCase(BaseApplicationTest, HealthMonitoringTestMixin):
    """Test GetSystemHealthUseCase."""

    def get_use_case_class(self):
        return GetSystemHealthUseCase

    def get_repository_mocks(self):
        return {"system_monitoring_service": AsyncMock()}

    @pytest.mark.asyncio
    async def test_get_system_health_success(self):
        """Test successful system health retrieval."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["system_monitoring_service"]

        # Setup mock
        mock_health = Mock()
        mock_service.get_system_health.return_value = mock_health

        # Execute
        query = GetSystemHealthQuery()
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result)
        mock_service.get_system_health.assert_called_once()


class TestGetSystemInfoUseCase(BaseApplicationTest, HealthMonitoringTestMixin):
    """Test GetSystemInfoUseCase."""

    def get_use_case_class(self):
        return GetSystemInfoUseCase

    def get_repository_mocks(self):
        return {"system_monitoring_service": AsyncMock()}

    @pytest.mark.asyncio
    async def test_get_system_info_success(self):
        """Test successful system info retrieval."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["system_monitoring_service"]

        # Setup mock
        mock_info = {"version": "1.0.0", "uptime": "1h 30m"}
        mock_service.get_system_info.return_value = mock_info

        # Execute
        query = GetSystemInfoQuery()
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result, mock_info)
        mock_service.get_system_info.assert_called_once()


class TestGetSystemMetricsUseCase(BaseApplicationTest, HealthMonitoringTestMixin):
    """Test GetSystemMetricsUseCase."""

    def get_use_case_class(self):
        return GetSystemMetricsUseCase

    def get_repository_mocks(self):
        return {"system_monitoring_service": AsyncMock()}

    @pytest.mark.asyncio
    async def test_get_system_metrics_success(self):
        """Test successful system metrics retrieval."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["system_monitoring_service"]

        # Setup mock
        mock_metrics = {"cpu_usage": 45.2, "memory_usage": 67.8}
        mock_service.get_system_metrics.return_value = mock_metrics

        # Execute
        query = GetSystemMetricsQuery()
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result, mock_metrics)
        mock_service.get_system_metrics.assert_called_once()


class TestCheckSystemReadinessUseCase(BaseApplicationTest, HealthMonitoringTestMixin):
    """Test CheckSystemReadinessUseCase."""

    def get_use_case_class(self):
        return CheckSystemReadinessUseCase

    def get_repository_mocks(self):
        return {"system_monitoring_service": AsyncMock()}

    @pytest.mark.asyncio
    async def test_check_system_readiness_success(self):
        """Test successful system readiness check."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["system_monitoring_service"]

        # Setup mock
        mock_readiness = {"ready": True, "checks": ["database", "cache", "services"]}
        mock_service.check_system_readiness.return_value = mock_readiness

        # Execute
        query = CheckSystemReadinessQuery()
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result, mock_readiness)
        mock_service.check_system_readiness.assert_called_once()


class TestListWorkflowsUseCase(BaseApplicationTest, HealthMonitoringTestMixin):
    """Test ListWorkflowsUseCase for health monitoring."""

    def get_use_case_class(self):
        return ListWorkflowsUseCase

    def get_repository_mocks(self):
        return {}  # This use case doesn't use repositories directly

    @pytest.mark.asyncio
    async def test_list_workflows_success(self):
        """Test successful workflow listing."""
        use_case = self.setup_use_case()

        # Execute
        query = ListWorkflowsQuery()
        result = await use_case.execute(query)

        # Assert - this use case returns a simple list
        assert isinstance(result, list)
        # In the actual implementation, this might return mock or empty data
