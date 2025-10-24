"""
Fixtures for E2E tests.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provide async HTTP client for E2E testing.
    
    Note: These E2E tests are currently placeholders and don't make actual API calls.
    When fully implemented, this fixture should create a client connected to the FastAPI app.
    """
    from src.api.app import create_app
    
    app = create_app()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

