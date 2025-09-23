#!/usr/bin/env python3
"""
API Endpoint Tests for All Bounded Contexts

Tests FastAPI routes and DTO validation across all bounded contexts.
Consolidated into single file following DRY principles.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch

from services.orchestrator.main import app
from tests.unit.orchestrator.test_base import BaseAPITest


@pytest.mark.asyncio
class TestWorkflowManagementAPI(BaseAPITest):
    """Test Workflow Management API endpoints."""

    async def get_api_client(self):
        """Get API client for testing."""
        return AsyncClient(app=app, base_url="http://testserver")

    @patch('services.orchestrator.main.container.list_workflows_use_case')
    async def test_list_workflows_endpoint(self, mock_use_case):
        """Test GET /api/v1/workflows endpoint."""
        # Setup
        client = await self.get_api_client()
        mock_use_case.execute.return_value = [
            Mock(to_dict=lambda: {"id": "wf-1", "name": "Test Workflow"})
        ]

        # Execute
        response = await client.get("/api/v1/workflows")

        # Assert
        self.assert_api_response_success(response)
        assert "workflows" in response.json()
        mock_use_case.execute.assert_called_once()


@pytest.mark.asyncio
class TestHealthMonitoringAPI(BaseAPITest):
    """Test Health Monitoring API endpoints."""

    async def get_api_client(self):
        """Get API client for testing."""
        return AsyncClient(app=app, base_url="http://testserver")

    @patch('services.orchestrator.main.container.get_system_health_use_case')
    async def test_system_health_endpoint(self, mock_use_case):
        """Test GET /api/v1/health/system endpoint."""
        # Setup
        client = await self.get_api_client()
        mock_use_case.execute.return_value = Mock(
            is_success=lambda: True,
            data={"status": "healthy", "services": {}}
        )

        # Execute
        response = await client.get("/api/v1/health/system")

        # Assert
        self.assert_api_response_success(response)
        mock_use_case.execute.assert_called_once()


@pytest.mark.asyncio
class TestInfrastructureAPI(BaseAPITest):
    """Test Infrastructure API endpoints."""

    async def get_api_client(self):
        """Get API client for testing."""
        return AsyncClient(app=app, base_url="http://testserver")

    @patch('services.orchestrator.main.container.start_saga_use_case')
    async def test_start_saga_endpoint(self, mock_use_case):
        """Test POST /api/v1/infrastructure/sagas endpoint."""
        # Setup
        client = await self.get_api_client()
        mock_use_case.execute.return_value = Mock(
            is_success=lambda: True,
            data={"saga_id": "saga-123", "status": "started"}
        )

        # Execute
        response = await client.post("/api/v1/infrastructure/sagas")

        # Assert
        self.assert_api_response_success(response)
        mock_use_case.execute.assert_called_once()

    @patch('services.orchestrator.main.container.get_dlq_stats_use_case')
    async def test_dlq_stats_endpoint(self, mock_use_case):
        """Test GET /api/v1/infrastructure/dlq/stats endpoint."""
        # Setup
        client = await self.get_api_client()
        mock_use_case.execute.return_value = Mock(
            is_success=lambda: True,
            data={"total_events": 10, "failed_events": 3}
        )

        # Execute
        response = await client.get("/api/v1/infrastructure/dlq/stats")

        # Assert
        self.assert_api_response_success(response)
        mock_use_case.execute.assert_called_once()


@pytest.mark.asyncio
class TestIngestionAPI(BaseAPITest):
    """Test Ingestion API endpoints."""

    async def get_api_client(self):
        """Get API client for testing."""
        return AsyncClient(app=app, base_url="http://testserver")

    @patch('services.orchestrator.main.container.start_ingestion_use_case')
    async def test_start_ingestion_endpoint(self, mock_use_case):
        """Test POST /api/v1/ingestion/ingest endpoint."""
        # Setup
        client = await self.get_api_client()
        mock_use_case.execute.return_value = {
            "ingestion_id": "ingest-123",
            "status": "started"
        }

        request_data = {
            "source_url": "https://github.com/test/repo",
            "source_type": "github",
            "parameters": {"include_issues": True}
        }

        # Execute
        response = await client.post("/api/v1/ingestion/ingest", json=request_data)

        # Assert
        self.assert_api_response_success(response)
        mock_use_case.execute.assert_called_once()


@pytest.mark.asyncio
class TestServiceRegistryAPI(BaseAPITest):
    """Test Service Registry API endpoints."""

    async def get_api_client(self):
        """Get API client for testing."""
        return AsyncClient(app=app, base_url="http://testserver")

    @patch('services.orchestrator.main.container.register_service_use_case')
    async def test_register_service_endpoint(self, mock_use_case):
        """Test POST /api/v1/service-registry/register endpoint."""
        # Setup
        client = await self.get_api_client()
        mock_use_case.execute.return_value = Mock(
            is_success=lambda: True,
            data={"name": "test_service", "status": "registered"}
        )

        request_data = {
            "service_name": "test_service",
            "service_url": "http://localhost:8000",
            "capabilities": ["api_call"]
        }

        # Execute
        response = await client.post("/api/v1/service-registry/register", json=request_data)

        # Assert
        self.assert_api_response_success(response)
        mock_use_case.execute.assert_called_once()


@pytest.mark.asyncio
class TestQueryProcessingAPI(BaseAPITest):
    """Test Query Processing API endpoints."""

    async def get_api_client(self):
        """Get API client for testing."""
        return AsyncClient(app=app, base_url="http://testserver")

    @patch('services.orchestrator.main.container.process_natural_language_query_use_case')
    async def test_process_query_endpoint(self, mock_use_case):
        """Test POST /api/v1/queries/process endpoint."""
        # Setup
        client = await self.get_api_client()
        mock_use_case.execute.return_value = {
            "query_id": "query-123",
            "results": [],
            "confidence_score": 0.85
        }

        request_data = {
            "query_text": "find all users",
            "max_results": 50
        }

        # Execute
        response = await client.post("/api/v1/queries/process", json=request_data)

        # Assert
        self.assert_api_response_success(response)
        mock_use_case.execute.assert_called_once()


@pytest.mark.asyncio
class TestReportingAPI(BaseAPITest):
    """Test Reporting API endpoints."""

    async def get_api_client(self):
        """Get API client for testing."""
        return AsyncClient(app=app, base_url="http://testserver")

    @patch('services.orchestrator.main.container.generate_report_use_case')
    async def test_generate_report_endpoint(self, mock_use_case):
        """Test POST /api/v1/reporting/generate endpoint."""
        # Setup
        client = await self.get_api_client()
        mock_use_case.execute.return_value = {
            "report_id": "report-123",
            "status": "generated"
        }

        request_data = {
            "report_type": "analytics",
            "format": "json"
        }

        # Execute
        response = await client.post("/api/v1/reporting/generate", json=request_data)

        # Assert
        self.assert_api_response_success(response)
        mock_use_case.execute.assert_called_once()


# DTO Validation Tests
class TestDTOValidation:
    """Test DTO validation across all bounded contexts."""

    def test_workflow_dto_validation(self):
        """Test workflow DTO validation."""
        from services.orchestrator.presentation.api.workflow_management.dtos import CreateWorkflowRequest

        # Valid data
        valid_data = {
            "name": "Test Workflow",
            "description": "Test description",
            "workflow_type": "automation",
            "parameters": {"param1": "value1"},
            "actions": [{"action_id": "action_1", "service_name": "test", "action_type": "api_call"}],
            "tags": ["test"]
        }
        self.assert_dto_validation(CreateWorkflowRequest, valid_data)

    def test_health_dto_validation(self):
        """Test health monitoring DTO validation."""
        from services.orchestrator.presentation.api.health_monitoring.dtos import HealthCheckRequest

        # Valid data
        valid_data = {"service_name": "test_service", "include_details": True}
        self.assert_dto_validation(HealthCheckRequest, valid_data)

    def test_ingestion_dto_validation(self):
        """Test ingestion DTO validation."""
        from services.orchestrator.presentation.api.ingestion.dtos import IngestRequest

        # Valid data
        valid_data = {
            "source_url": "https://github.com/test/repo",
            "source_type": "github",
            "parameters": {"include_issues": True}
        }
        self.assert_dto_validation(IngestRequest, valid_data)

        # Invalid data
        invalid_data = {
            "source_url": "",  # Empty URL should fail
            "source_type": "github"
        }
        self.assert_dto_validation(IngestRequest, valid_data, invalid_data)

    def test_service_registry_dto_validation(self):
        """Test service registry DTO validation."""
        from services.orchestrator.presentation.api.service_registry.dtos import ServiceRegistrationRequest

        # Valid data
        valid_data = {
            "service_name": "test_service",
            "service_url": "http://localhost:8000",
            "capabilities": ["api_call"]
        }
        self.assert_dto_validation(ServiceRegistrationRequest, valid_data)

    def test_query_processing_dto_validation(self):
        """Test query processing DTO validation."""
        from services.orchestrator.presentation.api.query_processing.dtos import ProcessQueryRequest

        # Valid data
        valid_data = {
            "query_text": "find all users",
            "max_results": 50
        }
        self.assert_dto_validation(ProcessQueryRequest, valid_data)

    def test_reporting_dto_validation(self):
        """Test reporting DTO validation."""
        from services.orchestrator.presentation.api.reporting.dtos import GenerateReportRequest

        # Valid data
        valid_data = {
            "report_type": "analytics",
            "format": "json"
        }
        self.assert_dto_validation(GenerateReportRequest, valid_data)

    def test_infrastructure_dto_validation(self):
        """Test infrastructure DTO validation."""
        from services.orchestrator.presentation.api.infrastructure.dtos import DLQRetryRequest

        # Valid data
        valid_data = {"event_ids": ["event-1", "event-2"], "max_retries": 3}
        self.assert_dto_validation(DLQRetryRequest, valid_data)
