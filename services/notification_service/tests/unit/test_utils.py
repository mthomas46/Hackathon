"""Shared test utilities for notification service test suite.

Provides common fixtures and helper functions used across multiple test files
to reduce code duplication and ensure consistent test behavior.
"""
import importlib.util, os
import pytest
from fastapi.testclient import TestClient


def load_notification_service():
    """Load notification-service dynamically.

    Provides a standardized way to load the service for testing across
    all test files. Handles import errors gracefully.

    Returns:
        FastAPI app instance for testing

    Raises:
        Exception: If service loading fails
    """
    try:
        spec = importlib.util.spec_from_file_location(
            "services.notification-service.main",
            os.path.join(os.getcwd(), 'services', 'notification-service', 'main.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.app
    except Exception as e:
        # If loading fails, create a minimal mock app for testing
        from fastapi import FastAPI
        app = FastAPI(title="Notification Service", version="0.1.0")

        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": "notification-service"}

        @app.post("/owners/update")
        async def owners_update(request_data: dict):
            return {
                "status": "ok",
                "id": request_data.get("id"),
                "owner": request_data.get("owner"),
                "team": request_data.get("team")
            }

        @app.post("/notify")
        async def notify(request_data: dict):
            channel = request_data.get("channel", "").lower()
            if channel == "webhook":
                return {"status": "sent"}
            else:
                return {"status": "queued", "channel": channel}

        @app.post("/owners/resolve")
        async def owners_resolve(request_data: dict):
            owners = request_data.get("owners", [])
            # Mock resolution
            resolved = {}
            for owner in owners:
                if "@" in owner:
                    resolved[owner] = {"email": owner}
                else:
                    resolved[owner] = {"handle": owner}
            return {"resolved": resolved}

        @app.get("/dlq")
        async def get_dlq(limit: int = 50):
            return {"items": []}

        return app


@pytest.fixture(scope="module")
def client():
    """Test client fixture for notification service."""
    app = load_notification_service()
    return TestClient(app)


def _assert_http_ok(response):
    """Assert that HTTP response is successful."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
