"""Pytest configuration and fixtures for MCP Gateway tests."""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import redis.asyncio as redis
from fastapi.testclient import TestClient

from services.mcp_gateway.domain.entities.mcp_instance import MCPInstance
from services.mcp_gateway.domain.value_objects.mcp_instance_status import MCPInstanceStatus
from services.mcp_gateway.infrastructure.config.settings import Settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings() -> Settings:
    """Provide test settings."""
    return Settings(
        service_name="mcp-gateway-test",
        service_api_port=5300,
        redis_host="localhost",
        redis_port=6379,
        redis_db=15,  # Use separate DB for tests
        redis_key_prefix="test:mcp:gateway:",
        health_check_enabled=False,  # Disable for unit tests
        circuit_breaker_enabled=False,  # Disable for unit tests
        debug_mode=True
    )


@pytest.fixture
async def redis_client(settings: Settings) -> AsyncGenerator[redis.Redis, None]:
    """Provide Redis client for tests."""
    client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=False
    )
    
    try:
        # Clear test database
        await client.flushdb()
        yield client
    finally:
        # Cleanup
        await client.flushdb()
        await client.close()


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """Provide mock Redis client for unit tests."""
    mock = AsyncMock(spec=redis.Redis)
    mock.ping = AsyncMock(return_value=True)
    mock.set = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.delete = AsyncMock(return_value=1)
    mock.smembers = AsyncMock(return_value=set())
    mock.sadd = AsyncMock(return_value=1)
    mock.srem = AsyncMock(return_value=1)
    mock.scard = AsyncMock(return_value=0)
    mock.pipeline = MagicMock()
    mock.pipeline.return_value = mock
    mock.execute = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def sample_mcp_instance() -> MCPInstance:
    """Provide a sample MCP instance for tests."""
    return MCPInstance(
        id="test-instance-1",
        mcp_id="client-acme",
        name="ACME Test MCP",
        host="localhost",
        port=3000,
        tier=0,
        priority=100,
        weight=100,
        max_concurrent_requests=50,
        status=MCPInstanceStatus.AVAILABLE
    )


@pytest.fixture
def multiple_mcp_instances() -> list[MCPInstance]:
    """Provide multiple MCP instances for load balancing tests."""
    return [
        MCPInstance(
            id=f"test-instance-{i}",
            mcp_id="client-acme",
            name=f"ACME MCP {i}",
            host="localhost",
            port=3000 + i,
            tier=0,
            priority=100,
            weight=100,
            max_concurrent_requests=50,
            status=MCPInstanceStatus.AVAILABLE
        )
        for i in range(3)
    ]

