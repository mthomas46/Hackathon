"""Integration tests for the Meta-Orchestration API"""

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from unittest.mock import Mock, AsyncMock

from main import app
from core.orchestrator import MetaOrchestrator
from models.service import ServiceInfo, ServiceStatus
from models.result import OperationResult


@pytest.mark.integration
class TestMetaOrchestratorAPI:
    """Integration tests for the complete API"""

    @pytest.fixture
    async def client(self):
        """Test client for the FastAPI app"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            yield client

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator with test services"""
        orchestrator = Mock(spec=MetaOrchestrator)

        # Mock services
        services = [
            ServiceInfo(
                name="redis",
                status=ServiceStatus.RUNNING,
                config={"image": "redis:7-alpine"},
                ports=["6379:6379"],
                environment={"REDIS_PASSWORD": "test"}
            ),
            ServiceInfo(
                name="user-store",
                status=ServiceStatus.STOPPED,
                config={"build": {"dockerfile": "services/user-store/Dockerfile"}},
                ports=["8106:5150"],
                environment={"SERVICE_NAME": "user-store", "SERVICE_API_PORT": "5150"}
            )
        ]

        orchestrator.get_service_status = AsyncMock(return_value=services)
        orchestrator.start_service = AsyncMock(return_value=Mock(
            service_name="user-store",
            action="start",
            success=True,
            message="Service started successfully",
            timestamp=1234567890
        ))
        orchestrator.stop_service = AsyncMock(return_value=Mock(
            service_name="user-store",
            action="stop",
            success=True,
            message="Service stopped successfully",
            timestamp=1234567890
        ))
        orchestrator.restart_service = AsyncMock(return_value=Mock(
            service_name="user-store",
            action="restart",
            success=True,
            message="Service restarted successfully",
            timestamp=1234567890
        ))
        orchestrator.update_service_config = AsyncMock(return_value=Mock(
            service_name="user-store",
            action="update_config",
            success=True,
            message="Configuration updated successfully",
            timestamp=1234567890
        ))
        orchestrator.get_service_logs = AsyncMock(return_value="Sample log output")

        return orchestrator

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "meta-orchestrator"
        assert data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_list_services(self, client, mock_orchestrator):
        """Test listing all services"""
        # Mock the global orchestrator
        import api.routes
        original_orchestrator = api.routes.meta_orchestrator
        api.routes.meta_orchestrator = mock_orchestrator

        try:
            response = await client.get("/api/v1/services")

            assert response.status_code == 200
            services = response.json()

            assert len(services) == 2
            assert services[0]["name"] == "redis"
            assert services[0]["status"] == "running"
            assert services[1]["name"] == "user-store"
            assert services[1]["status"] == "stopped"

        finally:
            # Restore original orchestrator
            api.routes.meta_orchestrator = original_orchestrator

    @pytest.mark.asyncio
    async def test_get_specific_service(self, client, mock_orchestrator):
        """Test getting a specific service"""
        # Mock the global orchestrator
        import api.routes
        original_orchestrator = api.routes.meta_orchestrator
        api.routes.meta_orchestrator = mock_orchestrator

        try:
            response = await client.get("/api/v1/services/user-store")

            assert response.status_code == 200
            service = response.json()

            assert service["name"] == "user-store"
            assert service["status"] == "stopped"
            assert "8106:5150" in service["ports"]

        finally:
            # Restore original orchestrator
            api.routes.meta_orchestrator = original_orchestrator

    @pytest.mark.asyncio
    async def test_start_service(self, client, mock_orchestrator):
        """Test starting a service"""
        # Mock the global orchestrator
        import api.routes
        original_orchestrator = api.routes.meta_orchestrator
        api.routes.meta_orchestrator = mock_orchestrator

        try:
            response = await client.post("/api/v1/services/user-store/start")

            assert response.status_code == 200
            result = response.json()

            assert result["service_name"] == "user-store"
            assert result["action"] == "start"
            assert result["success"] is True
            assert "started successfully" in result["message"]

        finally:
            # Restore original orchestrator
            api.routes.meta_orchestrator = original_orchestrator

    @pytest.mark.asyncio
    async def test_stop_service(self, client, mock_orchestrator):
        """Test stopping a service"""
        # Mock the global orchestrator
        import api.routes
        original_orchestrator = api.routes.meta_orchestrator
        api.routes.meta_orchestrator = mock_orchestrator

        try:
            response = await client.post("/api/v1/services/user-store/stop")

            assert response.status_code == 200
            result = response.json()

            assert result["service_name"] == "user-store"
            assert result["action"] == "stop"
            assert result["success"] is True

        finally:
            # Restore original orchestrator
            api.routes.meta_orchestrator = original_orchestrator

    @pytest.mark.asyncio
    async def test_restart_service(self, client, mock_orchestrator):
        """Test restarting a service"""
        # Mock the global orchestrator
        import api.routes
        original_orchestrator = api.routes.meta_orchestrator
        api.routes.meta_orchestrator = mock_orchestrator

        try:
            response = await client.post("/api/v1/services/user-store/restart")

            assert response.status_code == 200
            result = response.json()

            assert result["service_name"] == "user-store"
            assert result["action"] == "restart"
            assert result["success"] is True

        finally:
            # Restore original orchestrator
            api.routes.meta_orchestrator = original_orchestrator

    @pytest.mark.asyncio
    async def test_update_service_config(self, client, mock_orchestrator):
        """Test updating service configuration"""
        # Mock the global orchestrator
        import api.routes
        original_orchestrator = api.routes.meta_orchestrator
        api.routes.meta_orchestrator = mock_orchestrator

        try:
            config_update = {
                "environment": {
                    "NEW_CONFIG_VAR": "test_value",
                    "SERVICE_API_PORT": "8080"
                }
            }

            response = await client.put(
                "/api/v1/services/user-store/config",
                json=config_update
            )

            assert response.status_code == 200
            result = response.json()

            assert result["service_name"] == "user-store"
            assert result["action"] == "update_config"
            assert result["success"] is True

        finally:
            # Restore original orchestrator
            api.routes.meta_orchestrator = original_orchestrator

    @pytest.mark.asyncio
    async def test_get_service_logs(self, client, mock_orchestrator):
        """Test getting service logs"""
        # Mock the global orchestrator
        import api.routes
        original_orchestrator = api.routes.meta_orchestrator
        api.routes.meta_orchestrator = mock_orchestrator

        try:
            response = await client.get("/api/v1/services/user-store/logs?lines=50")

            assert response.status_code == 200
            result = response.json()

            assert result["service"] == "user-store"
            assert result["logs"] == "Sample log output"

        finally:
            # Restore original orchestrator
            api.routes.meta_orchestrator = original_orchestrator

    @pytest.mark.asyncio
    async def test_service_not_found(self, client, mock_orchestrator):
        """Test handling of non-existent service"""
        # Mock the global orchestrator to raise exception
        import api.routes
        original_orchestrator = api.routes.meta_orchestrator
        mock_orchestrator.start_service.side_effect = Exception("Service 'nonexistent' not found")
        api.routes.meta_orchestrator = mock_orchestrator

        try:
            response = await client.post("/api/v1/services/nonexistent/start")

            assert response.status_code == 500
            result = response.json()
            assert "not found" in result["detail"]

        finally:
            # Restore original orchestrator
            api.routes.meta_orchestrator = original_orchestrator

    @pytest.mark.asyncio
    async def test_orchestrator_not_initialized(self, client):
        """Test handling when orchestrator is not initialized"""
        # Temporarily set orchestrator to None
        import api.routes
        original_orchestrator = api.routes.meta_orchestrator
        api.routes.meta_orchestrator = None

        try:
            response = await client.get("/api/v1/services")

            assert response.status_code == 503
            result = response.json()
            assert "not initialized" in result["detail"]

        finally:
            # Restore original orchestrator
            api.routes.meta_orchestrator = original_orchestrator
