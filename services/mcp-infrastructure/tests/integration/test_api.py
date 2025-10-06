"""Integration tests for API endpoints.

These tests use the TestClient to test the API without running the server.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from services.mcp_infrastructure.presentation.api.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test the health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert data["service"] == "mcp-infrastructure"
        assert "dependencies" in data


@pytest.mark.asyncio
async def test_readiness_endpoint():
    """Test the readiness probe endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/ready")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "ready" in data


@pytest.mark.asyncio
async def test_liveness_endpoint():
    """Test the liveness probe endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/live")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["alive"] is True


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test the root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "mcp-infrastructure"
        assert "endpoints" in data


@pytest.mark.asyncio
async def test_docs_endpoint():
    """Test that the docs endpoint is accessible."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/docs")
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_openapi_endpoint():
    """Test that the OpenAPI spec is accessible."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/openapi.json")
        
        assert response.status_code == status.HTTP_200_OK
        spec = response.json()
        assert spec["openapi"].startswith("3.")
        assert "paths" in spec


@pytest.mark.asyncio
async def test_store_context_validation_error():
    """Test that invalid context request returns validation error."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Missing required fields
        response = await client.post("/api/v1/context", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_list_contexts_requires_filter():
    """Test that listing contexts without filters returns error."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/context")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "filter" in data["detail"].lower()

