"""
Shared fixtures for integration tests.

These fixtures provide FastAPI TestClient for testing API endpoints
without requiring a running server.
"""

import pytest
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import test database fixtures from main conftest
from tests.conftest import db_session, redis_client


@pytest.fixture(scope="module")
def app():
    """
    Get FastAPI application instance.
    
    This fixture creates the app once per test module for efficiency.
    Uses the create_app() factory function.
    """
    from src.api.app import create_app
    return create_app()


@pytest.fixture(scope="function")
def test_client(app) -> TestClient:
    """
    Provide FastAPI TestClient for synchronous endpoint testing.
    
    The TestClient uses the ASGI app directly without starting a server.
    This is much faster and doesn't require network operations.
    
    Usage:
        def test_endpoint(test_client):
            response = test_client.get("/api/v1/health")
            assert response.status_code == 200
    """
    return TestClient(app)


@pytest.fixture(scope="function")
def client(test_client) -> TestClient:
    """Alias for test_client fixture for backward compatibility."""
    return test_client


@pytest.fixture(scope="function")
async def async_test_client(app) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide async HTTP client for async endpoint testing.
    
    This client uses the ASGI app directly (no server required)
    and supports async operations.
    
    Usage:
        async def test_async_endpoint(async_test_client):
            response = await async_test_client.get("/api/v1/health")
            assert response.status_code == 200
    """
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
def auth_headers() -> dict:
    """
    Provide authentication headers for protected endpoints.
    
    Modify this fixture if your API requires authentication.
    """
    return {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="function")
def mock_services(monkeypatch):
    """
    Mock external services for integration tests.
    
    This fixture can be used to mock services like:
    - Ollama/LLM calls
    - External API calls
    - Long-running operations
    
    Usage:
        def test_with_mocks(test_client, mock_services):
            # Services are already mocked
            response = test_client.get("/api/v1/endpoint")
    """
    # Add service mocking here as needed
    # Example:
    # from unittest.mock import AsyncMock
    # mock_ollama = AsyncMock()
    # monkeypatch.setattr("src.services.llm.ollama_client.OllamaClient", mock_ollama)
    
    return {}


@pytest.fixture(scope="function")
async def test_data_cleanup(db_session):
    """
    Ensure test data is cleaned up after each test.
    
    The db_session fixture already handles rollback,
    but this provides explicit cleanup for integration tests.
    """
    yield
    # Cleanup happens automatically via db_session rollback


@pytest.fixture(scope="function")
def api_base_url() -> str:
    """Provide base URL for API endpoints."""
    return "/api/v1"


@pytest.fixture(scope="function")
def sample_request_data() -> dict:
    """
    Provide sample request data for testing.
    
    Modify this to match your API's expected request format.
    """
    return {
        "query": "test query",
        "limit": 10,
        "filters": {}
    }


# Helper functions for common test operations

def assert_success_response(response, expected_status=200):
    """
    Assert that response is successful.
    
    Args:
        response: FastAPI response object
        expected_status: Expected HTTP status code
    """
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
    return response.json()


def assert_error_response(response, expected_status=400):
    """
    Assert that response is an error.
    
    Args:
        response: FastAPI response object
        expected_status: Expected HTTP status code
    """
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
    data = response.json()
    assert "error" in data or "detail" in data, "Error response should contain error or detail field"
    return data


def assert_json_response(response):
    """
    Assert that response is valid JSON.
    
    Args:
        response: FastAPI response object
    
    Returns:
        Parsed JSON data
    """
    assert response.headers.get("content-type") == "application/json", "Response should be JSON"
    return response.json()

