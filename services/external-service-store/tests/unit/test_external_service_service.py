"""Unit tests for ExternalServiceService domain service."""

import pytest
from unittest.mock import Mock, AsyncMock
from domain.services.external_service_service import ExternalServiceService
from domain.entities.external_service import ExternalService, ServiceType, ServiceStatus
from domain.repositories.external_service_repository import ExternalServiceRepository


class TestExternalServiceService:
    """Test cases for ExternalServiceService."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return Mock(spec=ExternalServiceRepository)

    @pytest.fixture
    def mock_repositories(self):
        """Create all required mock repositories."""
        from unittest.mock import AsyncMock
        return {
            'service_repo': Mock(spec=ExternalServiceRepository),
            'endpoint_repo': AsyncMock(),
            'dependency_repo': AsyncMock(),
            'document_repo': AsyncMock(),
            'user_repo': AsyncMock(),
            'topic_repo': AsyncMock()
        }

    @pytest.fixture
    def service(self, mock_repositories):
        """Create service instance with mock repositories."""
        return ExternalServiceService(
            mock_repositories['service_repo'],
            mock_repositories['endpoint_repo'],
            mock_repositories['dependency_repo'],
            mock_repositories['document_repo'],
            mock_repositories['user_repo'],
            mock_repositories['topic_repo']
        )

    @pytest.mark.asyncio
    async def test_create_service_success(self, service, mock_repositories):
        """Test successful service creation."""
        # Arrange
        service_name = "test-service"
        service_type = "api"
        description = "Test service"

        created_service = ExternalService(
            id="generated-id",
            name=service_name,
            service_type=ServiceType.API,
            description=description
        )

        mock_repositories['service_repo'].find_by_name.return_value = None  # Service doesn't exist
        mock_repositories['service_repo'].save.return_value = None  # save returns None
        # Mock the get_service call that would happen after creation
        mock_repositories['service_repo'].find_by_id.return_value = created_service

        # Act
        result = await service.create_service(
            name=service_name,
            service_type=service_type,
            description=description
        )

        # Assert
        assert result.name == service_name
        assert result.service_type == ServiceType.API
        assert result.description == description
        mock_repositories['service_repo'].find_by_name.assert_called_once_with(service_name)
        mock_repositories['service_repo'].save.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_service_success(self, service, mock_repositories):
        """Test successful service retrieval by ID."""
        # Arrange
        service_id = "test-123"
        expected_service = ExternalService(
            id=service_id,
            name="test-service",
            service_type=ServiceType.API
        )

        mock_repositories['service_repo'].find_by_id.return_value = expected_service

        # Act
        result = await service.get_service(service_id)

        # Assert
        assert result == expected_service
        mock_repositories['service_repo'].find_by_id.assert_called_once_with(service_id)

    @pytest.mark.asyncio
    async def test_get_service_not_found(self, service, mock_repositories):
        """Test service retrieval when service not found."""
        # Arrange
        service_id = "non-existent"
        mock_repositories['service_repo'].find_by_id.return_value = None

        # Act
        result = await service.get_service(service_id)

        # Assert
        assert result is None
        mock_repositories['service_repo'].find_by_id.assert_called_once_with(service_id)

    @pytest.mark.asyncio
    async def test_list_services(self, service, mock_repositories):
        """Test getting all services."""
        # Arrange
        services = [
            ExternalService(id="1", name="service1", service_type=ServiceType.API),
            ExternalService(id="2", name="service2", service_type=ServiceType.DATABASE),
            ExternalService(id="3", name="service3", service_type=ServiceType.CACHE)
        ]

        mock_repositories['service_repo'].list_all_services.return_value = services

        # Act
        result = await service.list_services()

        # Assert
        assert result == services
        mock_repositories['service_repo'].list_all_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_service_success(self, service, mock_repositories):
        """Test successful service update."""
        # Arrange
        service_id = "test-123"
        name = "new-name"
        description = "New description"

        existing_service = ExternalService(
            id=service_id,
            name="old-name",
            service_type=ServiceType.API,
            description="Old description"
        )

        mock_repositories['service_repo'].find_by_id.return_value = existing_service

        # Act
        result = await service.update_service(service_id, name=name, description=description)

        # Assert
        assert result.name == name  # update_service returns updated service
        assert result.description == description
        mock_repositories['service_repo'].find_by_id.assert_called_once_with(service_id)
        # update_service doesn't call save - it modifies the object in place

    @pytest.mark.asyncio
    async def test_delete_service_success(self, service, mock_repositories):
        """Test successful service deletion."""
        # Arrange
        service_id = "test-123"
        mock_repositories['service_repo'].delete.return_value = True

        # Act
        result = await service.delete_service(service_id)

        # Assert
        assert result is True
        mock_repositories['service_repo'].delete.assert_called_once_with(service_id)

    @pytest.mark.asyncio
    async def test_get_services_by_technology(self, service, mock_repositories):
        """Test getting services by technology."""
        # Arrange
        technology = "python"
        services = [
            ExternalService(id="1", name="service1", service_type=ServiceType.API, technologies=["python", "fastapi"]),
            ExternalService(id="2", name="service2", service_type=ServiceType.API, technologies=["python", "django"])
        ]

        mock_repositories['service_repo'].find_services_by_technology.return_value = services

        # Act
        result = await service.get_services_by_technology(technology)

        # Assert
        assert result == services
        mock_repositories['service_repo'].find_services_by_technology.assert_called_once_with(technology)

    @pytest.mark.asyncio
    async def test_search_services(self, service, mock_repositories):
        """Test service search functionality."""
        # Arrange
        query = "test"
        services = [
            ExternalService(id="1", name="test-service1", service_type=ServiceType.API),
            ExternalService(id="2", name="test-service2", service_type=ServiceType.API)
        ]

        mock_repositories['service_repo'].search_services.return_value = services

        # Act
        result = await service.search_services(query)

        # Assert
        assert result == services
        mock_repositories['service_repo'].search_services.assert_called_once_with(query, 50)

    def test_service_initialization(self, mock_repositories):
        """Test service initialization."""
        service = ExternalServiceService(
            mock_repositories['service_repo'],
            mock_repositories['endpoint_repo'],
            mock_repositories['dependency_repo'],
            mock_repositories['document_repo'],
            mock_repositories['user_repo'],
            mock_repositories['topic_repo']
        )

        assert service._service_repo == mock_repositories['service_repo']
        assert service._endpoint_repo == mock_repositories['endpoint_repo']
        assert service._dependency_repo == mock_repositories['dependency_repo']
        assert service._document_repo == mock_repositories['document_repo']
        assert service._user_repo == mock_repositories['user_repo']
        assert service._topic_repo == mock_repositories['topic_repo']
        assert hasattr(service, 'create_service')
        assert hasattr(service, 'get_service')
        assert hasattr(service, 'update_service')
        assert hasattr(service, 'delete_service')
