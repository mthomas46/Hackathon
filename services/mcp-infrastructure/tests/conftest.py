"""Pytest configuration and fixtures for MCP Infrastructure Service tests."""

import pytest
import asyncio
from typing import AsyncGenerator
from datetime import datetime, timezone
import redis.asyncio as redis

from services.mcp_infrastructure.domain.entities.mcp_context import MCPContext
from services.mcp_infrastructure.domain.value_objects.mcp_context_type import MCPContextType
from services.mcp_infrastructure.domain.value_objects.training_phase import TrainingPhase
from services.mcp_infrastructure.infrastructure.config.settings import Settings
from services.mcp_infrastructure.infrastructure.repositories.redis_mcp_context_repository import (
    RedisMCPContextRepository,
)


# Configure asyncio event loop for tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test settings
@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings."""
    return Settings(
        service_name="mcp-infrastructure-test",
        redis_host="localhost",
        redis_port=6379,
        redis_db=15,  # Use separate DB for tests
        redis_key_prefix="mcp:test:",
    )


# Sample data fixtures
@pytest.fixture
def sample_mcp_id() -> str:
    """Provide a sample MCP ID."""
    return "mcp-test-123"


@pytest.fixture
def sample_context_data() -> dict:
    """Provide sample context data."""
    return {
        "status": "hot",
        "queries_today": 145,
        "avg_response_time_ms": 23,
    }


@pytest.fixture
def sample_metadata() -> dict:
    """Provide sample metadata."""
    return {
        "tier": "0",
        "client_id": "test-client",
    }


@pytest.fixture
def sample_tags() -> list:
    """Provide sample tags."""
    return ["tier-0", "test", "production"]


@pytest.fixture
def sample_context(sample_mcp_id, sample_context_data, sample_metadata, sample_tags) -> MCPContext:
    """Provide a sample MCPContext entity."""
    return MCPContext(
        mcp_id=sample_mcp_id,
        context_type=MCPContextType.INSTANCE,
        data=sample_context_data,
        metadata=sample_metadata,
        ttl=3600,
        tags=sample_tags,
    )


@pytest.fixture
def training_context(sample_mcp_id) -> MCPContext:
    """Provide a sample training context."""
    return MCPContext(
        mcp_id=sample_mcp_id,
        context_type=MCPContextType.TRAINING,
        data={
            "phase": TrainingPhase.EMBEDDING.value,
            "progress": 0.65,
            "entities_processed": 1250,
        },
        ttl=7200,
        tags=["training", "active"],
    )


# Redis fixtures
@pytest.fixture
async def redis_client(test_settings) -> AsyncGenerator[redis.Redis, None]:
    """Provide a Redis client for tests."""
    client = redis.Redis(
        host=test_settings.redis_host,
        port=test_settings.redis_port,
        db=test_settings.redis_db,
        decode_responses=False,
    )
    
    yield client
    
    # Cleanup: flush test database
    await client.flushdb()
    await client.close()


@pytest.fixture
async def redis_repository(
    redis_client, test_settings
) -> RedisMCPContextRepository:
    """Provide a Redis repository for tests."""
    return RedisMCPContextRepository(redis_client, test_settings)


# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup_redis(redis_client):
    """Automatically cleanup Redis after each test."""
    yield
    # Cleanup happens in redis_client fixture

