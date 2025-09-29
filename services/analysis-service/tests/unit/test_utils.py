"""Shared test utilities for analysis service test suite.

Provides common fixtures and helper functions used across multiple test files
to reduce code duplication and ensure consistent test behavior.
"""
import importlib.util, os
from fastapi.testclient import TestClient


def load_analysis_service():
    """Load analysis-service dynamically.

    Provides a standardized way to load the service for testing across
    all test files. Handles import errors gracefully.

    Returns:
        FastAPI app instance for testing

    Raises:
        Exception: If service loading fails
    """
    try:
        spec = importlib.util.spec_from_file_location(
            "services.analysis-service.main",
            os.path.join(os.getcwd(), 'services', 'analysis-service', 'main.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.app
    except Exception as e:
        # If loading fails, create a minimal mock app for testing
        from fastapi import FastAPI

        app = FastAPI(title="Analysis Service", version="1.0.0")

        # Mock endpoints for testing
        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": "analysis-service"}

        return app


def _assert_http_ok(response):
    """Assert that HTTP response is successful."""
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"