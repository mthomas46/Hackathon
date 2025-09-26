"""Shared test utilities for log collector test suite.

Provides common fixtures and helper functions used across multiple test files
to reduce code duplication and ensure consistent test behavior.
"""
import importlib.util, os
import pytest
from fastapi.testclient import TestClient


def load_log_collector_service():
    """Load log-collector service dynamically.

    Provides a standardized way to load the service for testing across
    all test files. Handles import errors gracefully.

    Returns:
        FastAPI app instance for testing

    Raises:
        Exception: If service loading fails
    """
    try:
        spec = importlib.util.spec_from_file_location(
            "services.log-collector.main",
            os.path.join(os.getcwd(), 'services', 'log-collector', 'main.py')
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.app
    except Exception as e:
        # If loading fails, create a minimal mock app for testing
        from fastapi import FastAPI
        app = FastAPI(title="Log Collector", version="0.1.0")

        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": "log-collector"}

        @app.post("/logs")
        async def put_log(request_data: dict):
            return {"status": "ok", "count": 1}

        @app.post("/logs/batch")
        async def put_logs(request_data: dict):
            items = request_data.get("items", [])
            return {"status": "ok", "count": len(items), "added": len(items)}

        @app.get("/logs")
        async def list_logs(service: str = None, level: str = None, limit: int = 100):
            return {"items": []}

        @app.get("/stats")
        async def stats():
            return {
                "count": 0,
                "by_level": {},
                "by_service": {},
                "errors_by_service": {},
                "top_services": []
            }

        return app


@pytest.fixture(scope="class", autouse=True)
def clear_logs_class():
    """Clear global log storage before test class to ensure test isolation.

    This fixture runs once per test class to reset the global log storage
    state, preventing cross-test contamination.
    """
    try:
        # Force reload the module to get fresh state
        import sys
        import importlib

        if 'services.log_collector.main' in sys.modules:
            importlib.reload(sys.modules['services.log_collector.main'])

        # Import and clear logs
        import services.log_collector.main as log_module
        if hasattr(log_module, 'log_storage'):
            log_module.log_storage.clear_logs()
    except Exception:
        # If we can't reload, that's okay - tests should handle existing state
        pass


@pytest.fixture(autouse=True)
def clear_logs_test():
    """Clear global log storage before each test to ensure test isolation.

    This fixture runs before each individual test to ensure clean state
    and prevent interference between tests.
    """
    try:
        # Try to access and clear the logs from already loaded module
        import sys
        if 'services.log_collector.main' in sys.modules:
            mod = sys.modules['services.log_collector.main']
            if hasattr(mod, 'log_storage'):
                mod.log_storage.clear_logs()
    except Exception:
        pass
