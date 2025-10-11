"""
Integration tests for request ID logging.

Tests that request IDs are properly propagated to log context.
"""

import pytest
import structlog
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.api.middleware.request_id import RequestIDMiddleware


@pytest.fixture
def app_with_logging():
    """Create test app with request ID middleware and structured logging."""
    from src.utils.logging_config import configure_structured_logging
    
    # Configure structured logging for test
    configure_structured_logging(log_level="INFO", json_logs=False)
    
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    
    @app.get("/test-logging")
    async def test_endpoint(request: Request):
        """Test endpoint that logs with structlog."""
        import structlog as struct_logger
        import structlog.contextvars as ctx_vars
        
        logger = struct_logger.get_logger(__name__)
        logger.info("test.message", action="testing", value=123)
        
        # Check that request_id is in context
        ctx = ctx_vars.get_contextvars()
        
        return {
            "request_id": request.state.request_id,
            "context_vars": ctx
        }
    
    return app


def test_request_id_in_context(app_with_logging):
    """Test that request ID is available in context vars."""
    client = TestClient(app_with_logging)
    
    # Make request with custom request ID
    response = client.get(
        "/test-logging",
        headers={"X-Request-ID": "test-12345"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Request ID should be in response
    assert data["request_id"] == "test-12345"
    
    # Request ID should have been in context vars
    assert "request_id" in data["context_vars"]
    assert data["context_vars"]["request_id"] == "test-12345"


def test_request_id_generated_if_not_provided(app_with_logging):
    """Test that request ID is auto-generated if not provided."""
    client = TestClient(app_with_logging)
    
    # Make request WITHOUT custom request ID
    response = client.get("/test-logging")
    
    assert response.status_code == 200
    data = response.json()
    
    # Request ID should be auto-generated (UUID)
    assert "request_id" in data
    assert len(data["request_id"]) == 36  # UUID length
    
    # Should also be in context
    assert data["request_id"] in data["context_vars"].values()


def test_request_id_in_response_header(app_with_logging):
    """Test that request ID is in response headers."""
    client = TestClient(app_with_logging)
    
    response = client.get(
        "/test-logging",
        headers={"X-Request-ID": "test-xyz"}
    )
    
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"] == "test-xyz"


def test_context_cleared_between_requests(app_with_logging):
    """Test that context is cleared between requests."""
    client = TestClient(app_with_logging)
    
    # First request
    response1 = client.get(
        "/test-logging",
        headers={"X-Request-ID": "request-1"}
    )
    data1 = response1.json()
    
    # Second request
    response2 = client.get(
        "/test-logging",
        headers={"X-Request-ID": "request-2"}
    )
    data2 = response2.json()
    
    # Request IDs should be different
    assert data1["request_id"] == "request-1"
    assert data2["request_id"] == "request-2"
    
    # Context should be independent
    assert data1["context_vars"]["request_id"] == "request-1"
    assert data2["context_vars"]["request_id"] == "request-2"

