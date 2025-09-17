#!/usr/bin/env python3
"""
Application Layer Tests for Service Registry

Tests the application layer including use cases, commands, and queries.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from services.orchestrator.application.service_registry.commands import (
    RegisterServiceCommand, UnregisterServiceCommand
)
from services.orchestrator.application.service_registry.queries import (
    GetServiceQuery, ListServicesQuery
)
from services.orchestrator.application.service_registry.use_cases import (
    RegisterServiceUseCase, UnregisterServiceUseCase, GetServiceUseCase, ListServicesUseCase
)
from tests.unit.orchestrator.test_base import BaseApplicationTest, ServiceRegistryTestMixin


class TestRegisterServiceUseCase(BaseApplicationTest, ServiceRegistryTestMixin):
    """Test RegisterServiceUseCase."""

    def get_use_case_class(self):
        return RegisterServiceUseCase

    def get_repository_mocks(self):
        return {"registration_service": Mock()}

    @pytest.mark.asyncio
    async def test_register_service_success(self):
        """Test successful service registration."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["registration_service"]

        # Setup mock
        mock_registered_service = self.create_test_service()
        mock_service.register_service.return_value = mock_registered_service

        # Execute
        command = RegisterServiceCommand(
            service_id="test_service",
            name="Test Service",
            description="Test service description",
            category="test",
            base_url="http://localhost:8000",
            capabilities=["api_call"]
        )
        result = await use_case.execute(command)

        # Assert
        self.assert_use_case_success(result)
        mock_service.register_service.assert_called_once()


class TestUnregisterServiceUseCase(BaseApplicationTest, ServiceRegistryTestMixin):
    """Test UnregisterServiceUseCase."""

    def get_use_case_class(self):
        return UnregisterServiceUseCase

    def get_repository_mocks(self):
        return {"registration_service": Mock()}

    @pytest.mark.asyncio
    async def test_unregister_service_success(self):
        """Test successful service unregistration."""
        use_case = self.setup_use_case()
        mock_service = self.get_repository_mocks()["registration_service"]

        # Setup mock
        mock_service.unregister_service.return_value = True

        # Execute
        from services.orchestrator.domain.service_registry.value_objects.service_id import ServiceId
        command = UnregisterServiceCommand(service_id=ServiceId("test_service"))
        result = await use_case.execute(command)

        # Assert
        self.assert_use_case_success(result)
        mock_service.unregister_service.assert_called_once()


class TestGetServiceUseCase(BaseApplicationTest, ServiceRegistryTestMixin):
    """Test GetServiceUseCase."""

    def get_use_case_class(self):
        return GetServiceUseCase

    def get_repository_mocks(self):
        return {"discovery_service": Mock(), "registration_service": Mock()}

    @pytest.mark.asyncio
    async def test_get_service_success(self):
        """Test successful service retrieval."""
        use_case = self.setup_use_case()
        mock_discovery = self.get_repository_mocks()["discovery_service"]
        mock_registration = self.get_repository_mocks()["registration_service"]

        # Setup mock
        mock_service = self.create_test_service()
        mock_discovery.get_service.return_value = mock_service

        # Execute
        from services.orchestrator.domain.service_registry.value_objects.service_id import ServiceId
        query = GetServiceQuery(service_id=ServiceId("test_service"))
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result)
        mock_discovery.get_service.assert_called_once()


class TestListServicesUseCase(BaseApplicationTest, ServiceRegistryTestMixin):
    """Test ListServicesUseCase."""

    def get_use_case_class(self):
        return ListServicesUseCase

    def get_repository_mocks(self):
        return {"discovery_service": Mock(), "registration_service": Mock()}

    @pytest.mark.asyncio
    async def test_list_services_success(self):
        """Test successful service listing."""
        use_case = self.setup_use_case()
        mock_discovery = self.get_repository_mocks()["discovery_service"]
        mock_registration = self.get_repository_mocks()["registration_service"]

        # Setup mock
        mock_services = [self.create_test_service()]
        mock_discovery.list_services.return_value = mock_services

        # Execute
        query = ListServicesQuery(limit=10, offset=0)
        result = await use_case.execute(query)

        # Assert
        self.assert_use_case_success(result)
        mock_discovery.list_services.assert_called_once()
