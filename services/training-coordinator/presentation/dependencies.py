"""Dependency injection for FastAPI."""

import redis.asyncio as redis
from fastapi import Depends

from services.training_coordinator.application.use_cases.create_job_use_case import CreateJobUseCase
from services.training_coordinator.application.use_cases.get_job_use_case import GetJobUseCase
from services.training_coordinator.application.use_cases.execute_job_use_case import ExecuteJobUseCase
from services.training_coordinator.domain.repositories.job_repository import JobRepository
from services.training_coordinator.infrastructure.config.settings import Settings, get_settings

# Global instances
_redis_client: redis.Redis = None
_job_repository: JobRepository = None


def init_dependencies(redis_client: redis.Redis, job_repo: JobRepository):
    """Initialize global dependencies."""
    global _redis_client, _job_repository
    _redis_client = redis_client
    _job_repository = job_repo


async def get_redis_client() -> redis.Redis:
    """Get Redis client dependency."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client


async def get_job_repository() -> JobRepository:
    """Get job repository dependency."""
    if _job_repository is None:
        raise RuntimeError("Job repository not initialized")
    return _job_repository


async def get_create_job_use_case(
    job_repo: JobRepository = Depends(get_job_repository)
) -> CreateJobUseCase:
    """Get CreateJobUseCase dependency."""
    return CreateJobUseCase(job_repo)


async def get_get_job_use_case(
    job_repo: JobRepository = Depends(get_job_repository)
) -> GetJobUseCase:
    """Get GetJobUseCase dependency."""
    return GetJobUseCase(job_repo)


async def get_execute_job_use_case(
    job_repo: JobRepository = Depends(get_job_repository)
) -> ExecuteJobUseCase:
    """Get ExecuteJobUseCase dependency."""
    return ExecuteJobUseCase(job_repo)

