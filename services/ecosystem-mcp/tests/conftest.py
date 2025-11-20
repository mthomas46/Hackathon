"""
Shared test fixtures and configuration for all tests.

This file is automatically loaded by pytest and provides:
- Database fixtures
- Service fixtures
- Mock fixtures
- Test data fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator
from uuid import uuid4

# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for multiple components"
    )
    config.addinivalue_line(
        "markers", "functional: Functional tests for API endpoints"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end workflow tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests"
    )
    config.addinivalue_line(
        "markers", "benchmark: Performance benchmark tests"
    )


# ============================================================================
# Async Support
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def test_db():
    """Create test database connection."""
    # Note: In production, this would set up a test database
    # For now, we'll use mocks
    yield None


@pytest.fixture(scope="function")
async def db_session(test_db):
    """Create database session for each test."""
    # Create session
    # Yield it
    # Rollback/cleanup after test
    yield None


# ============================================================================
# Service Fixtures
# ============================================================================

@pytest.fixture
def template_manager():
    """Get template manager instance."""
    from src.services.templates.template_manager import get_template_manager
    return get_template_manager()


@pytest.fixture
def discovery_service():
    """Get discovery service instance."""
    from src.services.adaptive.discovery_service import get_discovery_service
    return get_discovery_service()


@pytest.fixture
def prompt_tracker():
    """Get prompt tracker instance."""
    from src.services.adaptive.prompt_tracker import get_prompt_tracker
    return get_prompt_tracker()


@pytest.fixture
def citation_manager():
    """Get citation manager instance."""
    from src.services.adaptive.citation_manager import get_citation_manager
    return get_citation_manager()


@pytest.fixture
def transparency_logger():
    """Get transparency logger instance."""
    from src.services.adaptive.transparency_logger import get_transparency_logger
    return get_transparency_logger()


@pytest.fixture
def adaptive_orchestrator():
    """Get adaptive orchestrator instance."""
    from src.services.documentation.adaptive_orchestrator import get_adaptive_orchestrator
    return get_adaptive_orchestrator()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def valid_template_structure():
    """Provide valid template structure for testing."""
    return {
        "sections": [
            {
                "name": "Overview",
                "required": True,
                "prompt_template": "What is {service_name}?",
                "documents_needed": 10,
                "subsections": []
            },
            {
                "name": "Details",
                "required": False,
                "prompt_template": "Provide details about {service_name}",
                "documents_needed": 15,
                "subsections": []
            }
        ],
        "metadata": {
            "version": "1.0",
            "author": "test"
        }
    }


@pytest.fixture
def mock_repository_context():
    """Provide mock repository context."""
    return {
        "service_name": "testservice",
        "primary_language": "Python",
        "languages": {"Python": 100, "JavaScript": 20},
        "primary_framework": "FastAPI",
        "frameworks": ["FastAPI", "SQLAlchemy"],
        "architecture_type": "microservice",
        "total_files": 150,
        "code_structure": {
            "api": 25,
            "models": 30,
            "services": 40,
            "utils": 15
        },
        "dependencies": ["fastapi", "sqlalchemy", "redis", "postgresql"]
    }


@pytest.fixture
def mock_rag_response():
    """Provide mock RAG response."""
    return {
        "answer": "This is a comprehensive answer about the service.",
        "sources": [
            {
                "document_id": str(uuid4()),
                "score": 0.95,
                "content": "Source document content 1"
            },
            {
                "document_id": str(uuid4()),
                "score": 0.87,
                "content": "Source document content 2"
            }
        ],
        "metadata": {
            "query_time_ms": 150,
            "documents_searched": 1000
        }
    }


@pytest.fixture
def sample_template():
    """Provide sample template for testing."""
    return {
        "id": str(uuid4()),
        "name": "test_template",
        "category": "api_reference",
        "version": 1,
        "description": "Test template for unit tests",
        "structure": {
            "sections": [
                {
                    "name": "Overview",
                    "required": True,
                    "prompt_template": "Describe {service_name}",
                    "documents_needed": 10
                }
            ]
        },
        "render_options": {
            "include_toc": True,
            "format": "markdown"
        },
        "target_framework": None,
        "target_audience": "developers",
        "usage_count": 0,
        "is_system_template": False
    }


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    from unittest.mock import AsyncMock, Mock
    
    mock = AsyncMock()
    mock.generate.return_value = "Generated LLM response"
    return mock


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    from unittest.mock import AsyncMock
    
    mock = AsyncMock()
    mock.embed.return_value = [0.1] * 384  # Mock embedding vector
    return mock


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup after each test."""
    yield
    # Cleanup logic here
    # - Clear test data
    # - Reset mocks
    # - Close connections
    pass


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_session():
    """Cleanup after entire test session."""
    yield
    # Final cleanup
    pass


# ============================================================================
# Utility Functions
# ============================================================================

def create_test_template(**kwargs):
    """Helper to create test template with defaults."""
    defaults = {
        "name": f"test_{uuid4().hex[:8]}",
        "category": "api_reference",
        "structure": {
            "sections": [
                {
                    "name": "Test",
                    "required": True,
                    "prompt_template": "Test",
                    "documents_needed": 10
                }
            ]
        }
    }
    defaults.update(kwargs)
    return defaults


def create_test_context(**kwargs):
    """Helper to create test repository context with defaults."""
    defaults = {
        "service_name": "testservice",
        "primary_language": "Python",
        "frameworks": ["FastAPI"]
    }
    defaults.update(kwargs)
    return defaults


# Export helpers
pytest.create_test_template = create_test_template
pytest.create_test_context = create_test_context
