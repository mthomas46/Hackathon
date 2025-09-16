"""Doc Store Test Configuration and Fixtures.

Provides common fixtures and configuration for Doc Store unit tests.
Sets up the Python path and provides mock fixtures for testing.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

# Setup Python path for doc store modules
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Test environment setup
os.environ.setdefault('TESTING', 'true')
os.environ.setdefault('LOG_LEVEL', 'WARNING')


@pytest.fixture
def mock_execute_db_query():
    """Mock for database query execution."""
    with patch('services.doc_store.modules.shared_utils.execute_db_query') as mock:
        yield mock


@pytest.fixture
def mock_cache():
    """Mock cache instance for testing."""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.invalidate = Mock()
    cache.get_stats = Mock(return_value={
        "cache_hits": 0,
        "cache_misses": 0,
        "hit_ratio": 0.0,
        "local_cache_size": 0
    })
    return cache


@pytest.fixture
def mock_notification_manager():
    """Mock notification manager for testing."""
    manager = Mock()
    manager.emit_event = Mock(return_value="test-event-id")
    manager.get_event_history = Mock(return_value=[])
    manager.get_webhook_deliveries = Mock(return_value=[])
    manager.get_notification_stats = Mock(return_value={
        "period_days": 7,
        "event_distribution": [],
        "webhook_delivery_stats": {"total_deliveries": 0},
        "recent_failures": []
    })
    return manager


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = Mock()
    # Set up common Redis method mocks
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock(return_value=None)
    redis_mock.hget = AsyncMock(return_value=None)
    redis_mock.hset = AsyncMock(return_value=None)
    redis_mock.hincrby = AsyncMock(return_value=None)
    redis_mock.expire = AsyncMock(return_value=None)
    redis_mock.delete = AsyncMock(return_value=None)
    redis_mock.sadd = AsyncMock(return_value=None)
    redis_mock.smembers = AsyncMock(return_value=[])
    redis_mock.config_set = AsyncMock(return_value=None)
    redis_mock.info = AsyncMock(return_value={})
    redis_mock.dbsize = AsyncMock(return_value=0)
    return redis_mock


@pytest.fixture
def mock_service_clients():
    """Mock service clients for testing."""
    clients = Mock()
    clients.doc_store_url = Mock(return_value="http://localhost:5010")
    clients.notification_service_url = Mock(return_value="http://localhost:5095")
    clients.notify_via_service = AsyncMock(return_value={"status": "sent"})
    clients.resolve_owners_via_service = AsyncMock(return_value={"resolved": []})
    return clients


@pytest.fixture
def sample_document():
    """Sample document data for testing."""
    return {
        "id": "test-doc-123",
        "content": "This is a test document with some content for testing purposes.",
        "metadata": {
            "type": "documentation",
            "language": "english",
            "author": "test-author",
            "tags": ["test", "documentation"]
        },
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_webhook():
    """Sample webhook configuration for testing."""
    return {
        "id": "test-webhook",
        "name": "Test Webhook",
        "url": "https://example.com/webhook",
        "events": ["document.created", "document.updated"],
        "secret": "test-secret",
        "is_active": True,
        "retry_count": 3,
        "timeout_seconds": 30
    }


@pytest.fixture
def sample_lifecycle_policy():
    """Sample lifecycle policy for testing."""
    return {
        "id": "test-policy",
        "name": "Test Retention Policy",
        "description": "Test policy for automated retention",
        "conditions": {
            "content_types": ["documentation"],
            "max_age_days": 365
        },
        "actions": {
            "retention_days": 730
        },
        "priority": 5
    }


@pytest.fixture
def sample_relationship():
    """Sample document relationship for testing."""
    return {
        "from_document": "doc1",
        "to_document": "doc2",
        "relationship_type": "references",
        "strength": 0.8,
        "metadata": {"line_number": 42}
    }


@pytest.fixture
def sample_bulk_operation():
    """Sample bulk operation for testing."""
    return {
        "operation_id": "bulk-test-123",
        "operation_type": "create_documents",
        "total_items": 5,
        "processed_items": 3,
        "successful_items": 3,
        "failed_items": 0,
        "status": "processing"
    }


@pytest.fixture
def sample_notification_event():
    """Sample notification event for testing."""
    return {
        "id": "event-test-123",
        "event_type": "document.created",
        "entity_type": "document",
        "entity_id": "doc123",
        "user_id": "user456",
        "metadata": {"content_length": 1000},
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def client():
    """FastAPI test client for API endpoint testing."""
    from services.doc_store.main import app
    return TestClient(app)


# Base test classes for common patterns
class BaseTestCase:
    """Base test case with common utilities."""

    def assert_success_response(self, response):
        """Assert that a response indicates success."""
        # Handle both dict and response object formats
        if hasattr(response, 'model_dump'):
            response = response.model_dump()

        assert "success" in response
        assert response["success"] is True
        assert "data" in response

    def assert_error_response(self, response, error_code: str = None):
        """Assert that a response indicates an error."""
        # Handle both dict and response object formats
        if hasattr(response, 'model_dump'):
            response = response.model_dump()

        assert "success" in response
        assert response["success"] is False
        if error_code:
            assert response.get("error_code") == error_code

    def assert_http_success(self, response):
        """Assert HTTP response is successful."""
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        self.assert_success_response(data)
        return data

    def assert_http_error(self, response, status_code: int = 200, error_code: str = None):
        """Assert HTTP response indicates an error."""
        assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"
        data = response.json()
        self.assert_error_response(data, error_code)
        return data


class AsyncBaseTestCase(BaseTestCase):
    """Base test case for async tests."""

    async def assert_async_success_response(self, response):
        """Assert that an async response indicates success."""
        self.assert_success_response(response)

    async def assert_async_error_response(self, response, error_code: str = None):
        """Assert that an async response indicates an error."""
        self.assert_error_response(response, error_code)
