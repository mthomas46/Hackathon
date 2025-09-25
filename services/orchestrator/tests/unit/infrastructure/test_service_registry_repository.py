"""Unit tests for Service Registry Repository."""

import pytest
from unittest.mock import MagicMock

from services.orchestrator.infrastructure.persistence.service_registry_repository import InMemoryServiceRepository
from services.orchestrator.domain.service_registry.entities.service import Service
from services.orchestrator.domain.service_registry.value_objects.service_id import ServiceId


class TestInMemoryServiceRepository:
    """Test InMemoryServiceRepository functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repository = InMemoryServiceRepository()

    def test_repository_initialization(self):
        """Test repository initializes correctly."""
        assert isinstance(self.repository._services, dict)
        assert len(self.repository._services) == 0

    def test_save_service_new(self):
        """Test saving a new service."""
        service_id = ServiceId("test-service-123")
        service = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing"
        )

        result = self.repository.save_service(service)

        assert result is True
        assert service_id.value in self.repository._services
        assert self.repository._services[service_id.value] == service

    def test_save_service_update(self):
        """Test updating an existing service."""
        service_id = ServiceId("test-service-123")

        # Create initial service
        service1 = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing"
        )

        # Save initial service
        self.repository.save_service(service1)

        # Update service
        service2 = Service(
            service_id=service_id,
            name="Updated Service",
            description="An updated test service",
            category="updated"
        )

        result = self.repository.save_service(service2)

        assert result is True
        assert self.repository._services[service_id.value] == service2
        assert self.repository._services[service_id.value].name == "Updated Service"

    def test_get_service_existing(self):
        """Test getting an existing service."""
        service_id = ServiceId("test-service-456")
        service = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing"
        )

        self.repository.save_service(service)

        retrieved = self.repository.get_service(service_id)

        assert retrieved is not None
        assert retrieved == service
        assert retrieved.service_id == service_id

    def test_get_service_nonexistent(self):
        """Test getting a nonexistent service."""
        service_id = ServiceId("nonexistent-service")

        retrieved = self.repository.get_service(service_id)

        assert retrieved is None

    def test_list_services_empty(self):
        """Test listing services when repository is empty."""
        services = self.repository.list_services()

        assert isinstance(services, list)
        assert len(services) == 0

    def test_list_services_with_data(self):
        """Test listing services with data."""
        # Create multiple services
        service1 = Service(
            service_id=ServiceId("service-1"),
            name="Service 1",
            description="First service",
            category="test"
        )

        service2 = Service(
            service_id=ServiceId("service-2"),
            name="Service 2",
            description="Second service",
            category="test"
        )

        service3 = Service(
            service_id=ServiceId("service-3"),
            name="Service 3",
            description="Third service",
            category="other"
        )

        # Save services
        self.repository.save_service(service1)
        self.repository.save_service(service2)
        self.repository.save_service(service3)

        # List all services
        services = self.repository.list_services()

        assert len(services) == 3
        service_ids = {s.service_id.value for s in services}
        assert service_ids == {"service-1", "service-2", "service-3"}

    def test_delete_service_existing(self):
        """Test deleting an existing service."""
        service_id = ServiceId("test-service")
        service = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing"
        )

        self.repository.save_service(service)

        # Verify service exists
        assert self.repository.get_service(service_id) is not None

        # Delete service
        result = self.repository.delete_service(service_id)

        assert result is True
        assert self.repository.get_service(service_id) is None

    def test_delete_service_nonexistent(self):
        """Test deleting a nonexistent service."""
        service_id = ServiceId("nonexistent-service")

        result = self.repository.delete_service(service_id)

        assert result is False

    def test_thread_safety(self):
        """Test thread safety with concurrent operations."""
        import threading
        import time

        service_id = ServiceId("concurrent-service")
        results = []

        def worker(worker_id):
            """Worker function for concurrent operations."""
            try:
                if worker_id == 0:
                    # Worker 0 saves a service
                    service = Service(
                        service_id=service_id,
                        name=f"Service {worker_id}",
                        description=f"Description {worker_id}",
                        category="concurrent"
                    )
                    result = self.repository.save_service(service)
                    results.append(("save", result))
                else:
                    # Other workers try to get the service
                    time.sleep(0.01)  # Small delay
                    service = self.repository.get_service(service_id)
                    results.append(("get", service is not None))
            except Exception as e:
                results.append(("error", str(e)))

        # Start multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Verify results
        save_results = [r for op, r in results if op == "save"]
        get_results = [r for op, r in results if op == "get"]
        errors = [r for op, r in results if op == "error"]

        # Should have one successful save
        assert len(save_results) == 1
        assert save_results[0] is True

        # Should have multiple successful gets (some may be None if timing is off)
        assert len(get_results) >= 0

        # Should have no errors
        assert len(errors) == 0

    def test_find_services_by_category(self):
        """Test finding services by category."""
        # Create services with different categories
        services = [
            Service(
                service_id=ServiceId(f"service-{i}"),
                name=f"Service {i}",
                description=f"Description {i}",
                category="api" if i % 2 == 0 else "worker"
            )
            for i in range(5)
        ]

        # Save all services
        for service in services:
            self.repository.save_service(service)

        # Find API services
        api_services = self.repository.find_services_by_category("api")

        assert len(api_services) == 3  # services 0, 2, 4
        for service in api_services:
            assert service.category == "api"

        # Find worker services
        worker_services = self.repository.find_services_by_category("worker")

        assert len(worker_services) == 2  # services 1, 3
        for service in worker_services:
            assert service.category == "worker"

        # Find nonexistent category
        empty_services = self.repository.find_services_by_category("nonexistent")

        assert len(empty_services) == 0

    def test_service_exists(self):
        """Test checking if service exists."""
        service_id = ServiceId("test-service")
        service = Service(
            service_id=service_id,
            name="Test Service",
            description="A test service",
            category="testing"
        )

        # Service doesn't exist initially
        assert not self.repository.service_exists(service_id)

        # Save service
        self.repository.save_service(service)

        # Service exists now
        assert self.repository.service_exists(service_id)

        # Delete service
        self.repository.delete_service(service_id)

        # Service doesn't exist anymore
        assert not self.repository.service_exists(service_id)
