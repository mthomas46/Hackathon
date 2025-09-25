"""Tests for Health Monitoring System."""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock

from services.shared.infrastructure.monitoring.health import (
    HealthMonitor,
    HealthStatus,
    HealthCheck,
    DependencyHealth,
    ServiceClients,
)


class TestHealthMonitor:
    """Test health monitoring functionality."""

    @pytest.fixture
    def health_monitor(self):
        """Create a test health monitor instance."""
        return HealthMonitor(
            service_name="test-service",
            version="1.0.0"
        )

    @pytest.mark.asyncio
    async def test_basic_health_orchestrator(self, health_monitor):
        """Test basic health check for orchestrator service."""
        health_monitor.service_name = "orchestrator"

        health_status = await health_monitor.basic_health()

        assert health_status.service == "orchestrator"
        assert health_status.version == "1.0.0"
        assert health_status.status == "healthy"
        assert health_status.workflows_loaded is True
        assert isinstance(health_status.uptime_seconds, float)

    @pytest.mark.asyncio
    async def test_basic_health_doc_store(self, health_monitor):
        """Test basic health check for doc_store service."""
        health_monitor.service_name = "doc_store"

        health_status = await health_monitor.basic_health()

        assert health_status.service == "doc_store"
        assert health_status.database_connected is True

    @pytest.mark.asyncio
    async def test_basic_health_analysis_service(self, health_monitor):
        """Test basic health check for analysis service."""
        health_monitor.service_name = "analysis-service"

        health_status = await health_monitor.basic_health()

        assert health_status.service == "analysis-service"
        assert health_status.models_loaded is True

    @pytest.mark.asyncio
    async def test_basic_health_frontend(self, health_monitor):
        """Test basic health check for frontend service."""
        health_monitor.service_name = "frontend"

        health_status = await health_monitor.basic_health()

        assert health_status.service == "frontend"
        assert health_status.api_connected is True

    @pytest.mark.asyncio
    async def test_basic_health_summarizer_hub(self, health_monitor):
        """Test basic health check for summarizer hub."""
        health_monitor.service_name = "summarizer-hub"

        health_status = await health_monitor.basic_health()

        assert health_status.service == "summarizer-hub"
        assert health_status.llm_connected is True

    @pytest.mark.asyncio
    async def test_basic_health_llm_gateway(self, health_monitor):
        """Test basic health check for LLM gateway."""
        health_monitor.service_name = "llm-gateway"

        health_status = await health_monitor.basic_health()

        assert health_status.service == "llm-gateway"
        assert health_status.ollama_available is True

    @pytest.mark.asyncio
    async def test_basic_health_mock_data_generator(self, health_monitor):
        """Test basic health check for mock data generator."""
        health_monitor.service_name = "mock-data-generator"

        health_status = await health_monitor.basic_health()

        assert health_status.service == "mock-data-generator"
        assert health_status.data_sources == 5

    @pytest.mark.asyncio
    async def test_basic_health_notification_service(self, health_monitor):
        """Test basic health check for notification service."""
        health_monitor.service_name = "notification-service"

        health_status = await health_monitor.basic_health()

        assert health_status.service == "notification-service"
        assert health_status.email_configured is True

    @pytest.mark.asyncio
    async def test_basic_health_code_analyzer(self, health_monitor):
        """Test basic health check for code analyzer."""
        health_monitor.service_name = "code-analyzer"

        health_status = await health_monitor.basic_health()

        assert health_status.service == "code-analyzer"
        assert health_status.analysis_ready is True

    @pytest.mark.asyncio
    async def test_basic_health_unknown_service(self, health_monitor):
        """Test basic health check for unknown service."""
        health_monitor.service_name = "unknown-service"

        health_status = await health_monitor.basic_health()

        # Should still return basic health info
        assert health_status.service == "unknown-service"
        assert health_status.status == "healthy"
        assert hasattr(health_status, 'uptime_seconds')

    def test_add_health_check(self, health_monitor):
        """Test adding custom health checks."""
        health_monitor.add_health_check(
            name="database",
            description="Database connectivity check",
            critical=True
        )

        assert len(health_monitor.health_checks) == 1
        check = health_monitor.health_checks[0]
        assert check.name == "database"
        assert check.description == "Database connectivity check"
        assert check.critical is True

    @pytest.mark.asyncio
    async def test_dependency_health_success(self, health_monitor):
        """Test dependency health check success."""
        with patch.object(health_monitor.clients, 'get', new_callable=AsyncMock) as mock_get:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "healthy"})
            mock_response.text = AsyncMock(return_value='{"status": "healthy"}')
            mock_get.return_value.__aenter__.return_value = mock_response

            dependency_health = await health_monitor.dependency_health(
                service_name="test-dependency",
                endpoint="/health"
            )

            assert dependency_health.service_name == "test-dependency"
            assert dependency_health.endpoint == "/health"
            assert dependency_health.status == "healthy"

    @pytest.mark.asyncio
    async def test_dependency_health_failure(self, health_monitor):
        """Test dependency health check failure."""
        with patch.object(health_monitor.clients, 'get', new_callable=AsyncMock) as mock_get:
            # Mock failed response
            mock_get.side_effect = Exception("Connection failed")

            dependency_health = await health_monitor.dependency_health(
                service_name="test-dependency",
                endpoint="/health"
            )

            assert dependency_health.service_name == "test-dependency"
            assert dependency_health.status == "unhealthy"
            assert "Connection failed" in dependency_health.error_message

    @pytest.mark.asyncio
    async def test_dependency_health_timeout(self, health_monitor):
        """Test dependency health check timeout."""
        with patch.object(health_monitor.clients, 'get', new_callable=AsyncMock) as mock_get:
            # Mock timeout
            import asyncio
            mock_get.side_effect = asyncio.TimeoutError("Request timeout")

            dependency_health = await health_monitor.dependency_health(
                service_name="test-dependency",
                endpoint="/health"
            )

            assert dependency_health.status == "unhealthy"
            assert "timeout" in dependency_health.error_message.lower()

    def test_health_status_initialization(self, health_monitor):
        """Test health status initialization."""
        # Test that health monitor initializes with correct defaults
        assert health_monitor.service_name == "test-service"
        assert health_monitor.version == "1.0.0"
        assert isinstance(health_monitor.start_time, datetime)
        assert len(health_monitor.health_checks) == 0

        # Test uptime calculation
        uptime = (datetime.now(timezone.utc) - health_monitor.start_time).total_seconds()
        assert uptime >= 0

    @pytest.mark.asyncio
    async def test_service_specific_health_checks_are_independent(self, health_monitor):
        """Test that service-specific health checks don't interfere with each other."""
        # Test orchestrator
        health_monitor.service_name = "orchestrator"
        orchestrator_health = await health_monitor.basic_health()
        assert hasattr(orchestrator_health, 'workflows_loaded')
        assert orchestrator_health.workflows_loaded is True

        # Test doc_store (should not have workflows_loaded attribute)
        health_monitor.service_name = "doc_store"
        doc_store_health = await health_monitor.basic_health()
        assert hasattr(doc_store_health, 'database_connected')
        assert not hasattr(doc_store_health, 'workflows_loaded')

    @pytest.mark.asyncio
    async def test_environment_variable_inclusion(self, health_monitor):
        """Test that environment variables are included in health status."""
        import os
        original_env = os.environ.get("ENVIRONMENT")
        os.environ["ENVIRONMENT"] = "test-environment"

        try:
            health_status = await health_monitor.basic_health()
            assert health_status.environment == "test-environment"
        finally:
            # Restore original environment
            if original_env is not None:
                os.environ["ENVIRONMENT"] = original_env
            else:
                del os.environ["ENVIRONMENT"]

    @pytest.mark.asyncio
    async def test_default_environment_when_not_set(self, health_monitor):
        """Test default environment when ENVIRONMENT variable is not set."""
        import os
        # Ensure ENVIRONMENT is not set
        if "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]

        health_status = await health_monitor.basic_health()
        assert health_status.environment == "development"

    @pytest.mark.asyncio
    async def test_health_status_contains_required_fields(self, health_monitor):
        """Test that health status contains all required fields."""
        health_status = await health_monitor.basic_health()

        # Check required fields are present
        required_fields = [
            'status', 'service', 'version', 'uptime_seconds', 'environment'
        ]

        for field in required_fields:
            assert hasattr(health_status, field), f"Missing required field: {field}"

        # Check field types
        assert isinstance(health_status.status, str)
        assert isinstance(health_status.service, str)
        assert isinstance(health_status.version, str)
        assert isinstance(health_status.uptime_seconds, (int, float))
        assert isinstance(health_status.environment, str)
