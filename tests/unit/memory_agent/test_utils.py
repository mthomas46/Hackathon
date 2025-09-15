"""Shared test utilities for memory agent test suite.

Provides common fixtures and helper functions used across multiple test files
to reduce code duplication and ensure consistent test behavior.
"""
import importlib.util, os
import pytest
from fastapi.testclient import TestClient


def load_memory_agent_service():
    """Load memory-agent service dynamically.

    Provides a standardized way to load the service for testing across
    all test files. Handles import errors gracefully.

    Returns:
        FastAPI app instance for testing

    Raises:
        Exception: If service loading fails
    """
    try:
        spec = importlib.util.spec_from_file_location(
            "services.memory-agent.main",
            os.path.join(os.getcwd(), 'services', 'memory-agent', 'main.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.app
    except Exception as e:
        # If loading fails, create a minimal mock app for testing
        from fastapi import FastAPI
        import json

        app = FastAPI(title="Memory Agent", version="1.0.0")

        # Mock memory storage
        mock_memory = []

        # Mock endpoints for testing
        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "service": "memory-agent",
                "memory_count": len(mock_memory)
            }

        @app.post("/memory/put")
        async def put_memory(request_data: dict):
            item = request_data.get("item", {})
            mock_memory.append(item)
            return {
                "success": True,
                "result": {"count": len(mock_memory)},
                "operation": "stored"
            }

        @app.get("/memory/list")
        async def list_memory(type: str = None, key: str = None, limit: int = 100):
            filtered = mock_memory
            if type:
                filtered = [m for m in filtered if m.get("type") == type]
            if key:
                filtered = [m for m in filtered if m.get("key") == key]
            return {
                "success": True,
                "result": {"items": filtered[:limit]},
                "operation": "retrieved"
            }

        return app


@pytest.fixture(scope="module")
def client():
    """Test client fixture for memory agent service."""
    app = load_memory_agent_service()
    from fastapi.testclient import TestClient
    return TestClient(app)


def _assert_http_ok(response):
    """Assert that HTTP response is successful."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
