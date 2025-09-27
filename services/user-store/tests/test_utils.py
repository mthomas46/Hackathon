"""Test utilities for user-store service."""

import asyncio
from typing import Dict, Any
from httpx import AsyncClient
import pytest
from fastapi.testclient import TestClient

from ..main import app


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_test_client():
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


def get_test_client():
    """Get a test client instance."""
    return TestClient(app)


async def get_async_test_client():
    """Get an async test client instance."""
    return AsyncClient(app=app, base_url="http://testserver")


def create_test_user_data(user_id: str = "test_user", **overrides) -> Dict[str, Any]:
    """Create test user data."""
    data = {
        "id": user_id,
        "name": "Test User",
        "email": "test@example.com",
        "role": "developer",
        "status": "active",
        "expertise_tags": ["python", "testing"],
        "contact_email": "test@example.com"
    }
    data.update(overrides)
    return data


def create_test_document_relationship_data(
    user_id: str = "test_user",
    document_id: str = "doc_123",
    **overrides
) -> Dict[str, Any]:
    """Create test document relationship data."""
    data = {
        "user_id": user_id,
        "document_id": document_id,
        "relationship_type": "author",
        "tags": ["documentation", "api"],
        "services": ["user-store"],
        "metadata": {"created_at": "2024-01-01"}
    }
    data.update(overrides)
    return data

