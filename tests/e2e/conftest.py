"""Pytest configuration for E2E tests."""

import os
import pytest
import asyncio
import httpx
from typing import Dict, Any
import uuid


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--mode",
        action="store",
        default=os.getenv("TEST_MODE", "code"),
        help="Test mode: code or live"
    )


@pytest.fixture(scope="session")
def test_mode(request):
    """Get test mode from command line or environment."""
    return request.config.getoption("--mode")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def service_urls(test_mode):
    """Service URLs based on test mode."""
    if test_mode == "live":
        return {
            "kafka-ingestion": "http://localhost:5700",
            "llm-tagging": "http://localhost:8021",
            "mcp-local-llm": "http://localhost:8014",
            "mcp-package-manager": "http://localhost:8103",
            "mcp-evergreen-docs": "http://localhost:8104",
            "mcp-logs": "http://localhost:8016",
            "mcp-training": "http://localhost:8100",
            "mcp-store": "http://localhost:8101",
            "mcp-registry": "http://localhost:8102",
        }
    else:
        # Code mode uses test server or mocks
        return {
            "kafka-ingestion": "http://test-kafka-ingestion:5700",
            "llm-tagging": "http://test-llm-tagging:8021",
            "mcp-local-llm": "http://test-mcp-local-llm:8014",
            "mcp-package-manager": "http://test-mcp-package-manager:8103",
            "mcp-evergreen-docs": "http://test-mcp-evergreen-docs:8104",
            "mcp-logs": "http://test-mcp-logs:8016",
        }


@pytest.fixture
async def http_client():
    """Async HTTP client for tests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
def correlation_id():
    """Generate unique correlation ID for request tracking."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "document_id": f"doc_{uuid.uuid4().hex[:8]}",
        "event_type": "DOCUMENT_CREATED",
        "source": "e2e_test",
        "content": "This is a test document for E2E validation.",
        "metadata": {
            "title": "E2E Test Document",
            "author": "E2E Tester",
            "tags": ["test", "e2e", "validation"]
        }
    }


@pytest.fixture
def sample_large_document():
    """Large document for testing."""
    return {
        "document_id": f"doc_large_{uuid.uuid4().hex[:8]}",
        "event_type": "DOCUMENT_CREATED",
        "source": "e2e_test",
        "content": "Large document content. " * 10000,  # ~240KB
        "metadata": {
            "title": "Large E2E Test Document",
            "size": "large"
        }
    }


@pytest.fixture
async def wait_for_service():
    """Helper to wait for service availability."""
    async def _wait(url: str, timeout: int = 30) -> bool:
        import time
        start = time.time()
        async with httpx.AsyncClient() as client:
            while time.time() - start < timeout:
                try:
                    response = await client.get(f"{url}/health")
                    if response.status_code == 200:
                        return True
                except:
                    pass
                await asyncio.sleep(1)
        return False
    return _wait


@pytest.fixture
async def wait_for_log():
    """Helper to wait for log entry to appear."""
    async def _wait(
        mcp_logs_url: str,
        correlation_id: str,
        timeout: int = 10
    ) -> Dict[str, Any]:
        import time
        start = time.time()
        async with httpx.AsyncClient() as client:
            while time.time() - start < timeout:
                try:
                    response = await client.get(
                        f"{mcp_logs_url}/api/v1/logs",
                        params={"correlation_id": correlation_id}
                    )
                    if response.status_code == 200:
                        logs = response.json()
                        entries = logs.get("entries", [])
                        if len(entries) > 0:
                            return entries
                except:
                    pass
                await asyncio.sleep(0.5)
        return []
    return _wait