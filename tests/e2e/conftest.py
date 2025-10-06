"""Pytest configuration and fixtures for E2E tests."""

import asyncio
import os
from typing import AsyncGenerator, Dict

import httpx
import pytest
import redis.asyncio as redis


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def service_urls() -> Dict[str, str]:
    """Service URLs for testing."""
    base_port = int(os.getenv("TEST_BASE_PORT", "8150"))
    
    return {
        "mcp_provisioner": f"http://localhost:{base_port}",  # 8150
        "mcp_infrastructure": f"http://localhost:{base_port + 1}",  # 8151
        "mcp_gateway": f"http://localhost:{base_port + 2}",  # 8152
        "mcp_interpreter": f"http://localhost:{base_port + 3}",  # 8153
        "mcp_orchestrator": f"http://localhost:{base_port + 4}",  # 8154
        "training_coordinator": f"http://localhost:{base_port + 5}",  # 8155
        "mcp_registry": f"http://localhost:{base_port + 6}",  # 8156
    }


@pytest.fixture(scope="session")
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Shared HTTP client for tests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Shared Redis client for tests."""
    client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=0,
        decode_responses=True
    )
    
    try:
        await client.ping()
        yield client
    finally:
        await client.close()


@pytest.fixture
async def clean_redis(redis_client: redis.Redis):
    """Clean Redis before each test."""
    # Clean test keys
    keys = await redis_client.keys("test:*")
    if keys:
        await redis_client.delete(*keys)
    yield
    # Clean after test
    keys = await redis_client.keys("test:*")
    if keys:
        await redis_client.delete(*keys)


@pytest.fixture
def test_mcp_config() -> Dict:
    """Test MCP configuration."""
    return {
        "mcp_id": "test-mcp-001",
        "tier": "project",
        "name": "Test MCP",
        "description": "MCP for E2E testing",
        "cpu_limit": "1.0",
        "memory_limit": "512M",
    }


@pytest.fixture
def test_query() -> str:
    """Test query for interpreter."""
    return "What are the main features of the authentication system?"


@pytest.fixture
def test_training_job_config() -> Dict:
    """Test training job configuration."""
    return {
        "mcp_id": "test-mcp-001",
        "name": "Test Training Job",
        "description": "E2E test training job",
        "data_sources": ["github"],
        "source_config": {
            "github": {
                "repos": ["test/repo"],
                "include_prs": True,
                "include_issues": True,
            }
        },
    }

