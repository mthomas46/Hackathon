"""Test configuration and shared fixtures for the analysis service test suite."""

import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Simple test fixtures using mock objects

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_document_data() -> Dict[str, Any]:
    """Sample document data for testing."""
    return {
        "id": "test-doc-001",
        "title": "Test Document",
        "content": "# Test Document\n\nThis is a test document for unit testing.",
        "file_path": "/path/to/test/document.md",
        "repository_id": "test-repo-001",
        "author": "test-author",
        "version": "1.0.0",
        "metadata": {"language": "markdown", "size": 1024, "lines": 10},
    }


@pytest.fixture
def sample_analysis_data() -> Dict[str, Any]:
    """Sample analysis data for testing."""
    return {
        "id": "test-analysis-001",
        "document_id": "test-doc-001",
        "analysis_type": "semantic_similarity",
        "status": "completed",
        "confidence": 0.85,
        "results": {
            "similarity_score": 0.85,
            "matched_documents": ["doc-002", "doc-003"],
        },
    }


@pytest.fixture
def sample_finding_data() -> Dict[str, Any]:
    """Sample finding data for testing."""
    return {
        "id": "test-finding-001",
        "analysis_id": "test-analysis-001",
        "document_id": "test-doc-001",
        "title": "Test Finding",
        "description": "This is a test finding for unit testing.",
        "severity": "medium",
        "confidence": 0.75,
        "category": "code_quality",
        "recommendation": "Consider refactoring this code for better readability.",
    }


# Mock repositories using unittest.mock
@pytest.fixture
def mock_document_repository():
    """Mock document repository."""
    from unittest.mock import AsyncMock, MagicMock
    repo = MagicMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    repo.find_all = AsyncMock(return_value=[])
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_analysis_repository():
    """Mock analysis repository."""
    from unittest.mock import AsyncMock, MagicMock
    repo = MagicMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    repo.find_all = AsyncMock(return_value=[])
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_finding_repository():
    """Mock finding repository."""
    from unittest.mock import AsyncMock, MagicMock
    repo = MagicMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    repo.find_all = AsyncMock(return_value=[])
    repo.delete = AsyncMock()
    return repo


# Mock services
@pytest.fixture
def mock_document_service(mock_document_repository):
    """Mock document service."""
    from unittest.mock import MagicMock
    service = MagicMock()
    service.repository = mock_document_repository
    service.create_document = AsyncMock()
    service.get_document = AsyncMock()
    service.update_document = AsyncMock()
    service.delete_document = AsyncMock()
    return service


@pytest.fixture
def mock_analysis_service(mock_analysis_repository, mock_document_repository):
    """Mock analysis service."""
    from unittest.mock import MagicMock
    service = MagicMock()
    service.analysis_repository = mock_analysis_repository
    service.document_repository = mock_document_repository
    service.create_analysis = AsyncMock()
    service.get_analysis = AsyncMock()
    service.perform_analysis = AsyncMock()
    return service


# Test configuration
@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration."""
    return {
        "database_url": "sqlite:///:memory:",
        "redis_url": "redis://localhost:6379/1",
        "log_level": "DEBUG",
        "test_timeout": 30,
        "mock_external_services": True,
    }
