"""
Pytest configuration and shared fixtures for all tests.

Provides:
- Test database setup/teardown
- Mock fixtures
- Integration test markers
- Performance test configuration
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (may be slow)"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create a temporary database for testing."""
    db_dir = tmp_path_factory.mktemp("test_db")
    db_path = db_dir / "test_doc_store.db"
    return str(db_path)


@pytest.fixture(scope="function")
def clean_db(test_db_path):
    """Provide a clean database for each test."""
    # Setup: Initialize clean database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Initialize schema
    from services.doc_store.db.schema import init_database
    init_database()
    
    yield test_db_path
    
    # Teardown: Clean up
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def sample_document():
    """Provide a sample document for testing."""
    return {
        "id": "test-doc-001",
        "content": "This is test content for semantic search testing.",
        "metadata": {"source": "test", "created_at": "2024-01-01T00:00:00Z"},
        "tags": ["test", "sample"],
    }


@pytest.fixture
def sample_embedding():
    """Provide a sample embedding vector for testing."""
    # 384-dimensional vector (all-MiniLM-L6-v2 dimension)
    return [float(i) / 384 for i in range(384)]


@pytest.fixture
def mock_embedding_model():
    """Mock the embedding model to avoid loading actual models in tests."""
    from unittest.mock import Mock, MagicMock
    
    mock_model = Mock()
    mock_model.encode.return_value = [0.1] * 384
    mock_model.get_sentence_embedding_dimension.return_value = 384
    mock_model.max_seq_length = 256
    
    return mock_model


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset embedding service singleton between tests."""
    yield
    
    # Reset singleton
    import services.doc_store.domain.embeddings.service as embedding_module
    embedding_module._embedding_service = None


# Performance test configuration
@pytest.fixture
def performance_threshold():
    """Define performance thresholds for tests."""
    return {
        "embedding_generation_ms": 100,  # Single embedding
        "batch_embedding_ms_per_doc": 10,  # Per document in batch
        "semantic_search_ms": 500,  # Search across 100 documents
        "cosine_similarity_us": 10,  # Microseconds for single calculation
    }


# Integration test fixtures
@pytest.fixture(scope="session")
def integration_test_enabled():
    """Check if integration tests should run."""
    return os.getenv("RUN_INTEGRATION_TESTS", "false").lower() == "true"


@pytest.fixture
def skip_if_no_integration(integration_test_enabled):
    """Skip test if integration tests are disabled."""
    if not integration_test_enabled:
        pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=true to enable.")


# Mock HTTP clients
@pytest.fixture
def mock_httpx_client():
    """Provide mock httpx client for API testing."""
    from unittest.mock import AsyncMock, Mock
    
    client = Mock()
    client.post = AsyncMock()
    client.get = AsyncMock()
    
    return client

