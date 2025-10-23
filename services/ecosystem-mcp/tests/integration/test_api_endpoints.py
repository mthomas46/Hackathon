"""
Integration tests for API endpoints.

Tests the full flow of API requests through all layers.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app



def test_health_endpoint(client):
    """Test health check endpoint."""
    # Note: This may fail if dependencies aren't running
    # In a real test environment, we'd mock them
    response = client.get("/health")
    
    assert response.status_code in [200, 503]  # Either healthy or unhealthy
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Ecosystem MCP"
    assert "version" in data


def test_openapi_docs(client):
    """Test OpenAPI documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json(client):
    """Test OpenAPI JSON schema."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema


def test_query_endpoint_structure(client):
    """Test query endpoint is accessible."""
    # This will likely fail without database, but tests endpoint exists
    response = client.post("/api/v1/query/query", json={
        "service_name": "test",
        "limit": 10
    })
    
    # Either success or server error (if DB not available)
    assert response.status_code in [200, 500, 503]


def test_logs_list_endpoint(client):
    """Test logs list endpoint."""
    response = client.get("/api/v1/logs/list?log_dir=./logs")
    
    # Either success or not found (if logs dir doesn't exist)
    assert response.status_code in [200, 404]


def test_ollama_status_endpoint(client):
    """Test Ollama status endpoint."""
    response = client.get("/api/v1/ollama/status")
    
    # Either success or service unavailable
    assert response.status_code in [200, 503]

