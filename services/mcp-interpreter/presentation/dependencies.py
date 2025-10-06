"""Dependency injection for FastAPI."""

import redis.asyncio as redis
from fastapi import Depends

from services.mcp_interpreter.application.use_cases.parse_query_use_case import ParseQueryUseCase
from services.mcp_interpreter.domain.repositories.query_cache_repository import QueryCacheRepository
from services.mcp_interpreter.infrastructure.config.settings import Settings, get_settings
from services.mcp_interpreter.infrastructure.repositories.redis_query_cache_repository import RedisQueryCacheRepository

# Global instances (initialized on startup)
_redis_client: redis.Redis = None
_cache_repository: QueryCacheRepository = None


def init_dependencies(redis_client: redis.Redis, cache_repo: QueryCacheRepository):
    """Initialize global dependencies (called on startup)."""
    global _redis_client, _cache_repository
    _redis_client = redis_client
    _cache_repository = cache_repo


async def get_redis_client() -> redis.Redis:
    """Get Redis client dependency."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client


async def get_cache_repository() -> QueryCacheRepository:
    """Get cache repository dependency."""
    if _cache_repository is None:
        raise RuntimeError("Cache repository not initialized")
    return _cache_repository


async def get_parse_query_use_case(
    cache_repo: QueryCacheRepository = Depends(get_cache_repository),
    settings: Settings = Depends(get_settings)
) -> ParseQueryUseCase:
    """Get ParseQueryUseCase dependency."""
    # NLP service and intent classifier would be injected here
    # For now, use None (fallback to simple methods)
    return ParseQueryUseCase(
        cache_repository=cache_repo if settings.cache_enabled else None,
        nlp_service=None,  # Would be NLPService with spaCy
        intent_classifier=None,  # Would be IntentClassifier with LLM
    )

