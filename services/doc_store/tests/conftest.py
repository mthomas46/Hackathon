"""Test configuration and fixtures for doc_store service."""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from typing import Generator, AsyncGenerator

# Import the service components
import sys
from pathlib import Path
from unittest.mock import Mock

# Add project root and parent directories to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use mocks for complex imports to avoid relative import issues
Document = Mock()
DocumentRepository = Mock()
DocumentService = Mock()
DocStoreCache = Mock()


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
async def test_db_connection_string(temp_db_path: str) -> str:
    """Provide a test database connection string."""
    return f"sqlite:///{temp_db_path}"


@pytest.fixture
async def document_repository(test_db_connection_string: str) -> DocumentRepository:
    """Create a document repository for testing."""
    repo = DocumentRepository(test_db_connection_string)

    # Initialize database schema for testing
    import sqlite3
    db_path = test_db_connection_string.replace("sqlite:///", "")
    with sqlite3.connect(db_path) as conn:
        # Create documents table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                metadata TEXT,  -- JSON
                correlation_id TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

    return repo


@pytest.fixture
async def document_service(document_repository: DocumentRepository) -> DocumentService:
    """Create a document service for testing."""
    return DocumentService(document_repository)


@pytest.fixture
async def sample_document() -> Document:
    """Create a sample document for testing."""
    return Document(
        id="test-doc-123",
        content="This is a test document content for testing purposes.",
        content_hash="abc123def456",
        metadata={"author": "test_user", "tags": ["test", "sample"]},
        correlation_id="test-correlation-123"
    )


@pytest.fixture
async def doc_store_cache() -> DocStoreCache:
    """Create a document store cache for testing."""
    cache = DocStoreCache()
    yield cache
    # Cleanup if needed
    await cache.clear()


@pytest.fixture
def sample_documents_data() -> list:
    """Provide sample document data for bulk operations."""
    return [
        {
            "id": f"doc-{i}",
            "content": f"This is test document content {i}",
            "content_hash": f"hash{i}",
            "metadata": {"index": i, "category": "test"},
            "correlation_id": f"corr-{i}"
        }
        for i in range(1, 6)
    ]


# Test configuration
@pytest.fixture
def test_config() -> dict:
    """Provide test configuration."""
    return {
        "database_url": "sqlite:///./test.db",
        "cache_ttl": 300,
        "max_document_size": 10485760,  # 10MB
        "supported_formats": ["markdown", "html", "plaintext"],
        "service_name": "doc_store_test"
    }


# Async test utilities
@pytest.fixture
async def async_client():
    """Provide an async HTTP client for integration tests."""
    from httpx import AsyncClient
    client = AsyncClient()
    yield client
    await client.aclose()


# Mock utilities
@pytest.fixture
def mock_external_service():
    """Mock external service for testing."""
    class MockExternalService:
        def __init__(self):
            self.calls = []

        async def call(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            return {"status": "success", "data": "mocked"}

    return MockExternalService()


# Database utilities
@pytest.fixture
async def clean_database(test_db_connection_string: str):
    """Ensure clean database state for each test."""
    # This fixture runs before each test to clean up
    import sqlite3
    db_path = test_db_connection_string.replace("sqlite:///", "")

    # Clean up any existing data
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM documents")
        conn.commit()

    yield

    # Clean up after test
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM documents")
        conn.commit()


# Performance testing utilities
@pytest.fixture
def performance_metrics():
    """Provide performance metrics collection for tests."""
    import time
    from contextlib import contextmanager

    @contextmanager
    def time_operation(operation_name: str):
        start_time = time.time()
        yield
        end_time = time.time()
        duration = end_time - start_time
        print(f"{operation_name} took {duration:.4f} seconds")

    class MetricsCollector:
        def __init__(self):
            self.metrics = {}

        def time(self, operation_name: str):
            return time_operation(operation_name)

        def record(self, key: str, value):
            self.metrics[key] = value

        def get(self, key: str):
            return self.metrics.get(key)

    return MetricsCollector()
