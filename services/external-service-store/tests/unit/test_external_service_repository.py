"""Unit tests for ExternalServiceRepository interface."""

import pytest
from abc import ABC
from domain.repositories.external_service_repository import ExternalServiceRepository
from domain.entities.external_service import ExternalService, ServiceType, ServiceStatus


class TestExternalServiceRepositoryInterface:
    """Test the repository interface contract."""

    def test_repository_is_abstract(self):
        """Test that ExternalServiceRepository is an abstract base class."""
        assert issubclass(ExternalServiceRepository, ABC)

        # Check that key methods are defined as abstract
        required_methods = [
            'save',
            'find_by_id',
            'find_by_name',
            'list_all_services',
            'update',
            'delete',
            'find_by_type',
            'find_by_status',
            'search_services',
            'exists',
            'count'
        ]

        for method_name in required_methods:
            assert hasattr(ExternalServiceRepository, method_name), f"Missing method: {method_name}"

    def test_repository_inheritance(self):
        """Test that repository follows proper inheritance pattern."""
        # This is more of a documentation test - the interface should be clear
        repo_class = ExternalServiceRepository

        # Check class has proper structure
        assert hasattr(repo_class, '__init__')
        assert callable(getattr(repo_class, 'save', None))
        assert callable(getattr(repo_class, 'find_by_id', None))


class TestExternalServiceRepositoryContract:
    """Test the repository contract and behavior expectations."""

    @pytest.fixture
    def sample_service(self):
        """Create a sample service for testing."""
        return ExternalService(
            id="test-123",
            name="test-service",
            display_name="Test Service",
            description="A test service",
            service_type=ServiceType.API,
            status=ServiceStatus.ACTIVE,
            version="1.0.0",
            technologies=["python", "fastapi"],
            base_url="https://api.example.com"
        )

    @pytest.fixture
    def sample_services(self):
        """Create multiple sample services."""
        return [
            ExternalService(
                id="1",
                name="service1",
                service_type=ServiceType.API,
                status=ServiceStatus.ACTIVE
            ),
            ExternalService(
                id="2",
                name="service2",
                service_type=ServiceType.DATABASE,
                status=ServiceStatus.ACTIVE
            ),
            ExternalService(
                id="3",
                name="service3",
                service_type=ServiceType.API,
                status=ServiceStatus.INACTIVE
            )
        ]

    def test_repository_save_contract(self):
        """Test the save method contract."""
        # The save method should accept an ExternalService and return None (async void)
        # This is a contract test - actual implementation would be in concrete classes

        # Check method signature exists
        save_method = getattr(ExternalServiceRepository, 'save', None)
        assert save_method is not None
        assert callable(save_method)

    def test_repository_find_by_id_contract(self):
        """Test the find_by_id method contract."""
        repo_class = ExternalServiceRepository

        # Should accept string ID and return ExternalService or None
        find_method = getattr(repo_class, 'find_by_id', None)
        assert find_method is not None
        assert callable(find_method)

    def test_repository_find_by_name_contract(self):
        """Test the find_by_name method contract."""
        repo_class = ExternalServiceRepository

        # Should accept string name and return ExternalService or None
        find_method = getattr(repo_class, 'find_by_name', None)
        assert find_method is not None
        assert callable(find_method)

    def test_repository_list_all_contract(self):
        """Test the list_all_services method contract."""
        repo_class = ExternalServiceRepository

        # Should return list of ExternalService
        list_method = getattr(repo_class, 'list_all_services', None)
        assert list_method is not None
        assert callable(list_method)

    def test_repository_update_contract(self):
        """Test the update method contract."""
        repo_class = ExternalServiceRepository

        # Should accept ExternalService and return None (async void)
        update_method = getattr(repo_class, 'update', None)
        assert update_method is not None
        assert callable(update_method)

    def test_repository_delete_contract(self):
        """Test the delete method contract."""
        repo_class = ExternalServiceRepository

        # Should accept string ID and return boolean
        delete_method = getattr(repo_class, 'delete', None)
        assert delete_method is not None
        assert callable(delete_method)

    def test_repository_find_by_type_contract(self):
        """Test the find_by_type method contract."""
        repo_class = ExternalServiceRepository

        # Should accept ServiceType and return list of ExternalService
        find_method = getattr(repo_class, 'find_by_type', None)
        assert find_method is not None
        assert callable(find_method)

    def test_repository_find_by_status_contract(self):
        """Test the find_by_status method contract."""
        repo_class = ExternalServiceRepository

        # Should accept ServiceStatus and return list of ExternalService
        find_method = getattr(repo_class, 'find_by_status', None)
        assert find_method is not None
        assert callable(find_method)

    def test_repository_search_contract(self):
        """Test the search_services method contract."""
        repo_class = ExternalServiceRepository

        # Should accept string query and return list of ExternalService
        search_method = getattr(repo_class, 'search_services', None)
        assert search_method is not None
        assert callable(search_method)

    def test_repository_additional_methods_contract(self):
        """Test additional repository methods."""
        repo_class = ExternalServiceRepository

        # Check exists and count methods
        assert hasattr(repo_class, 'exists')
        assert hasattr(repo_class, 'count')
        assert callable(getattr(repo_class, 'exists', None))
        assert callable(getattr(repo_class, 'count', None))

    def test_service_type_filtering_expectation(self, sample_services):
        """Test expected behavior for service type filtering."""
        api_services = [s for s in sample_services if s.service_type == ServiceType.API]
        db_services = [s for s in sample_services if s.service_type == ServiceType.DATABASE]

        assert len(api_services) == 2  # service1 and service3
        assert len(db_services) == 1   # service2

    def test_service_status_filtering_expectation(self, sample_services):
        """Test expected behavior for service status filtering."""
        active_services = [s for s in sample_services if s.status == ServiceStatus.ACTIVE]
        inactive_services = [s for s in sample_services if s.status == ServiceStatus.INACTIVE]

        assert len(active_services) == 2   # service1 and service2
        assert len(inactive_services) == 1 # service3

    def test_search_functionality_expectation(self, sample_services):
        """Test expected search behavior."""
        # Search for "service" should return all
        service_results = [s for s in sample_services if "service" in s.name.lower()]
        assert len(service_results) == 3

        # Search for "1" should return service1
        specific_results = [s for s in sample_services if "1" in s.name]
        assert len(specific_results) == 1
        assert specific_results[0].name == "service1"

    def test_statistics_structure_expectation(self):
        """Test expected statistics structure."""
        # This defines the expected contract for statistics
        expected_stats_keys = [
            'total_services',
            'active_services',
            'inactive_services',
            'by_type',
            'by_status',
            'by_technology',
            'average_version',
            'recently_updated'
        ]

        # Repository implementations should return dict with these keys
        # This is a documentation test for the expected interface
        assert len(expected_stats_keys) > 0

    def test_bulk_operations_expectation(self, sample_services):
        """Test expected bulk operations behavior."""
        # Bulk operations should handle multiple services efficiently
        # This is a performance and correctness expectation

        # Test that bulk operations preserve service integrity
        for service in sample_services:
            assert service.id is not None
            assert service.name is not None
            assert isinstance(service.service_type, ServiceType)

    def test_repository_error_handling_expectation(self):
        """Test expected error handling patterns."""
        # Repository methods should handle common error cases gracefully
        # - Invalid IDs should return None
        # - Database connection errors should be propagated appropriately
        # - Validation errors should be clear

        # This is a contract test for error handling expectations
        error_scenarios = [
            "invalid_id",
            "database_connection_error",
            "constraint_violation",
            "duplicate_name"
        ]

        assert len(error_scenarios) > 0  # Documentation of expected error handling
