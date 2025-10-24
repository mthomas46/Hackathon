"""
Pytest configuration and fixtures for embedding service tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient

# Optional imports for unit tests (not needed for integration/performance tests)
try:
    from src.main import app
    from src.services.fastembed_service import FastEmbedService
    from src.services.cache_service import CacheService
    APP_AVAILABLE = True
except ImportError:
    APP_AVAILABLE = False
    app = None
    FastEmbedService = None
    CacheService = None


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client for API testing."""
    if not APP_AVAILABLE:
        pytest.skip("App not available (missing dependencies)")
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def fastembed_service():
    """Create FastEmbed service instance for testing."""
    if not APP_AVAILABLE:
        pytest.skip("FastEmbed service not available (missing dependencies)")
    service = FastEmbedService()
    service.load_model()
    return service


@pytest.fixture
async def cache_service() -> AsyncGenerator:
    """Create cache service instance for testing."""
    if not APP_AVAILABLE:
        pytest.skip("Cache service not available (missing dependencies)")
    service = CacheService()
    await service.connect()
    yield service
    await service.close()


@pytest.fixture
def sample_text() -> str:
    """Sample text for testing."""
    return "This is a test document for embedding generation."


@pytest.fixture
def sample_texts() -> list[str]:
    """Sample texts for batch testing."""
    return [
        "First test document",
        "Second test document",
        "Third test document with more content",
        "Fourth test document",
        "Fifth test document for comprehensive testing"
    ]

