"""Test configuration and fixtures for orchestrator tests."""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add services to path
services_root = project_root / "services"
if str(services_root) not in sys.path:
    sys.path.insert(0, str(services_root))


@pytest.fixture
def sample_service_data():
    """Sample service data for testing."""
    return {
        "service_id": "test-service-123",
        "name": "Test Service",
        "description": "A test service for unit tests",
        "category": "testing",
        "base_url": "https://api.test.com",
        "openapi_url": "https://api.test.com/openapi.json",
        "metadata": {"version": "1.0.0", "environment": "test"}
    }


@pytest.fixture
def sample_service_id():
    """Sample service ID for testing."""
    from services.orchestrator.domain.service_registry.value_objects.service_id import ServiceId
    return ServiceId("test-service-123")


@pytest.fixture
def sample_service(sample_service_id):
    """Sample service entity for testing."""
    from services.orchestrator.domain.service_registry.entities.service import Service
    return Service(
        service_id=sample_service_id,
        name="Test Service",
        description="A test service for unit tests",
        category="testing",
        base_url="https://api.test.com",
        metadata={"version": "1.0.0"}
    )


@pytest.fixture
def in_memory_repository():
    """In-memory service repository for testing."""
    from services.orchestrator.infrastructure.persistence.service_registry_repository import InMemoryServiceRepository
    return InMemoryServiceRepository()
