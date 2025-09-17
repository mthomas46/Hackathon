#!/usr/bin/env python3
"""
Shared test configuration and fixtures for all shared module tests.

This conftest.py provides common test fixtures and setup used across
all shared module test files.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
import tempfile
import os

from services.shared.core.constants_new import ServiceNames, ErrorCodes
from services.shared.core.models import Document, Finding

# Import enterprise modules with fallback for missing dependencies
try:
    from services.shared.enterprise.error_handling.error_handling import ErrorSeverity, ErrorCategory
except ImportError:
    # Fallback definitions if enterprise module is not available
    from enum import Enum
    class ErrorSeverity(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    class ErrorCategory(Enum):
        NETWORK = "network"
        DATABASE = "database"
        VALIDATION = "validation"

# Import monitoring modules with fallback
try:
    from services.shared.monitoring.health import HealthStatus
except ImportError:
    # Fallback definition if monitoring module is not available
    from enum import Enum
    class HealthStatus(Enum):
        HEALTHY = "healthy"
        DEGRADED = "degraded"
        UNHEALTHY = "unhealthy"
        DOWN = "down"


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return Document(
        id="doc_123",
        title="Test Document",
        content="This is test content for document analysis.",
        source_type="confluence",
        metadata={
            "author": "test_user",
            "last_modified": "2024-01-15T10:00:00Z",
            "space": "TEST"
        },
        flags=["active"],
        created_at="2024-01-15T09:00:00Z",
        updated_at="2024-01-15T10:00:00Z"
    )


@pytest.fixture
def sample_finding():
    """Create a sample analysis finding for testing."""
    return Finding(
        id="finding_123",
        document_id="doc_123",
        finding_type="consistency_issue",
        severity="medium",
        title="Inconsistent terminology",
        description="Found inconsistent use of 'API' vs 'api' in documentation.",
        location={"line": 25, "column": 10},
        suggestions=["Use consistent capitalization for 'API'"],
        metadata={"pattern": "case_variation"},
        created_at="2024-01-15T11:00:00Z"
    )


@pytest.fixture
def mock_service_client():
    """Create a mock service client for testing."""
    client = Mock()
    client.get_json = AsyncMock()
    client.post_json = AsyncMock()
    client.put_json = AsyncMock()
    client.delete = AsyncMock()
    client.doc_store_url = Mock(return_value="http://localhost:8001")
    client.source_agent_url = Mock(return_value="http://localhost:8002")
    client.prompt_store_url = Mock(return_value="http://localhost:8003")
    return client


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=b"test_value")
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    client.exists = AsyncMock(return_value=1)
    client.expire = AsyncMock(return_value=True)
    client.ttl = AsyncMock(return_value=300)
    return client


@pytest.fixture
def sample_error_context():
    """Create a sample error context for testing."""
    return {
        "service_name": "test-service",
        "operation": "test_operation",
        "error_message": "Test error occurred",
        "severity": ErrorSeverity.HIGH,
        "category": ErrorCategory.VALIDATION,
        "metadata": {
            "user_id": "user123",
            "request_id": "req456",
            "endpoint": "/api/test"
        }
    }


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_health_checks():
    """Create sample health check configurations."""
    return [
        {
            "name": "database_check",
            "description": "Check database connectivity",
            "check_function": lambda: True,
            "enabled": True
        },
        {
            "name": "cache_check",
            "description": "Check cache service",
            "check_function": lambda: True,
            "enabled": True
        },
        {
            "name": "external_api_check",
            "description": "Check external API connectivity",
            "check_function": lambda: False,
            "enabled": True
        }
    ]


@pytest.fixture
def sample_cache_entries():
    """Create sample cache entries for testing."""
    return [
        {
            "key": "user:123",
            "value": {"name": "John Doe", "email": "john@example.com"},
            "ttl_seconds": 300
        },
        {
            "key": "document:456",
            "value": {"title": "Test Doc", "content": "Test content"},
            "ttl_seconds": 600
        },
        {
            "key": "config:app_settings",
            "value": {"debug": True, "max_connections": 100},
            "ttl_seconds": 3600
        }
    ]


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration values."""
    return {
        "test_database_url": "sqlite:///:memory:",
        "test_redis_url": "redis://localhost:6379/1",
        "test_service_port": 8000,
        "test_timeout": 30,
        "test_retries": 3
    }


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def sample_api_request():
    """Create a sample API request for testing."""
    return {
        "method": "POST",
        "url": "/api/analyze",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token"
        },
        "body": {
            "target_id": "doc_123",
            "analysis_type": "consistency",
            "options": {"strict": True}
        }
    }


@pytest.fixture
def sample_api_response():
    """Create a sample API response for testing."""
    return {
        "status_code": 200,
        "headers": {"Content-Type": "application/json"},
        "body": {
            "success": True,
            "data": {
                "findings": [],
                "summary": {"total_findings": 0}
            },
            "timestamp": "2024-01-15T12:00:00Z"
        }
    }


# Environment setup fixtures
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    original_env = dict(os.environ)

    # Set test environment variables
    os.environ.update({
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "TESTING": "true",
        "LOG_LEVEL": "DEBUG"
    })

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Async test utilities
@pytest.fixture
def run_async():
    """Helper fixture to run async functions in sync tests."""

    def _run_async(coro):
        """Run a coroutine synchronously."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    return _run_async


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Create a performance timer for benchmarking tests."""
    import time

    class Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            return self

        def __exit__(self, *args):
            self.end = time.perf_counter()
            self.elapsed = self.end - self.start

    return Timer


# Integration test fixtures
@pytest.fixture
def integration_setup():
    """Set up integration test environment."""
    return {
        "services": {
            "doc_store": {"host": "localhost", "port": 8001},
            "analysis_service": {"host": "localhost", "port": 8002},
            "prompt_store": {"host": "localhost", "port": 8003}
        },
        "database": {
            "url": "postgresql://test:test@localhost:5432/test_db"
        },
        "redis": {
            "url": "redis://localhost:6379/1"
        }
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up after each test."""
    yield
    # Add any cleanup logic here if needed


# Test data generators
@pytest.fixture
def generate_test_documents():
    """Generate test documents for bulk testing."""

    def _generate(count: int, source_type: str = "confluence") -> List[Document]:
        documents = []
        for i in range(count):
            doc = Document(
                id=f"doc_{i:03d}",
                title=f"Test Document {i}",
                content=f"This is test content for document {i}.",
                source_type=source_type,
                metadata={
                    "author": f"user_{i % 5}",
                    "last_modified": f"2024-01-{15 + (i % 10):02d}T10:00:00Z",
                    "tags": [f"tag_{i % 3}"]
                },
                flags=["active"] if i % 2 == 0 else [],
                created_at=f"2024-01-{10 + (i % 10):02d}T09:00:00Z",
                updated_at=f"2024-01-{15 + (i % 10):02d}T10:00:00Z"
            )
            documents.append(doc)
        return documents

    return _generate
