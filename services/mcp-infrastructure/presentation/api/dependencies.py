"""Dependency Injection - FastAPI dependencies for the MCP Infrastructure Service."""

import logging
from functools import lru_cache
from typing import AsyncGenerator
import redis.asyncio as redis

from services.mcp_infrastructure.infrastructure.config.settings import get_settings, Settings
from services.mcp_infrastructure.infrastructure.repositories.redis_mcp_context_repository import (
    RedisMCPContextRepository,
)
from services.mcp_infrastructure.application.use_cases.store_context_use_case import StoreContextUseCase
from services.mcp_infrastructure.application.use_cases.retrieve_context_use_case import RetrieveContextUseCase
from services.mcp_infrastructure.application.use_cases.list_contexts_use_case import ListContextsUseCase
from services.mcp_infrastructure.application.use_cases.delete_context_use_case import DeleteContextUseCase


logger = logging.getLogger(__name__)

# Global Redis client (initialized on startup)
_redis_client: redis.Redis = None


async def init_redis_client() -> redis.Redis:
    """Initialize Redis client on application startup."""
    global _redis_client
    
    if _redis_client is None:
        settings = get_settings()
        
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            socket_connect_timeout=settings.redis_socket_connect_timeout,
            socket_timeout=settings.redis_socket_timeout,
            decode_responses=False,  # We handle decoding manually
        )
        
        logger.info(
            f"Redis client initialized: {settings.redis_host}:{settings.redis_port} "
            f"(db={settings.redis_db})"
        )
    
    return _redis_client


async def close_redis_client() -> None:
    """Close Redis client on application shutdown."""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis client closed")
        _redis_client = None


async def get_redis_client() -> redis.Redis:
    """
    Dependency to get Redis client.
    
    Returns the global Redis client instance.
    """
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis_client() first.")
    return _redis_client


async def get_repository() -> RedisMCPContextRepository:
    """
    Dependency to get MCP Context Repository.
    
    Creates a repository instance with the Redis client.
    """
    redis_client = await get_redis_client()
    settings = get_settings()
    return RedisMCPContextRepository(redis_client, settings)


async def get_store_context_use_case() -> StoreContextUseCase:
    """Dependency to get Store Context use case."""
    repository = await get_repository()
    return StoreContextUseCase(repository)


async def get_retrieve_context_use_case() -> RetrieveContextUseCase:
    """Dependency to get Retrieve Context use case."""
    repository = await get_repository()
    return RetrieveContextUseCase(repository)


async def get_list_contexts_use_case() -> ListContextsUseCase:
    """Dependency to get List Contexts use case."""
    repository = await get_repository()
    return ListContextsUseCase(repository)


async def get_delete_context_use_case() -> DeleteContextUseCase:
    """Dependency to get Delete Context use case."""
    repository = await get_repository()
    return DeleteContextUseCase(repository)

