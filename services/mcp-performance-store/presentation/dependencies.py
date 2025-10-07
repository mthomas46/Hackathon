"""
Dependency injection for FastAPI routes.
"""
from services.mcp_performance_store.infrastructure.config import Settings
from services.mcp_performance_store.infrastructure.repositories import RedisPerformanceRepository
from services.mcp_performance_store.application.use_cases import (
    RecordExecutionUseCase,
    QueryExecutionsUseCase,
    GetPatternPerformanceUseCase
)


# Global instances
_settings = None
_repository = None


def get_settings() -> Settings:
    """Get application settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


async def get_repository() -> RedisPerformanceRepository:
    """Get performance repository."""
    global _repository
    if _repository is None:
        settings = get_settings()
        _repository = RedisPerformanceRepository(settings)
        await _repository.connect()
    return _repository


async def get_record_use_case() -> RecordExecutionUseCase:
    """Get record execution use case."""
    repository = await get_repository()
    return RecordExecutionUseCase(repository)


async def get_query_use_case() -> QueryExecutionsUseCase:
    """Get query executions use case."""
    repository = await get_repository()
    return QueryExecutionsUseCase(repository)


async def get_pattern_performance_use_case() -> GetPatternPerformanceUseCase:
    """Get pattern performance use case."""
    repository = await get_repository()
    return GetPatternPerformanceUseCase(repository)
