"""Dependency injection for FastAPI."""

import redis.asyncio as redis
from fastapi import Depends

from services.mcp_registry.application.use_cases.export_mcp_use_case import ExportMCPUseCase
from services.mcp_registry.application.use_cases.import_mcp_use_case import ImportMCPUseCase
from services.mcp_registry.application.use_cases.get_registry_entry_use_case import GetRegistryEntryUseCase
from services.mcp_registry.application.use_cases.search_registry_use_case import SearchRegistryUseCase
from services.mcp_registry.domain.repositories.registry_repository import RegistryRepository
from services.mcp_registry.domain.repositories.package_storage_repository import PackageStorageRepository
from services.mcp_registry.infrastructure.config.settings import Settings, get_settings

# Global instances (initialized on startup)
_redis_client: redis.Redis = None
_registry_repository: RegistryRepository = None
_storage_repository: PackageStorageRepository = None


def init_dependencies(
    redis_client: redis.Redis,
    registry_repo: RegistryRepository,
    storage_repo: PackageStorageRepository
):
    """Initialize global dependencies (called on startup)."""
    global _redis_client, _registry_repository, _storage_repository
    _redis_client = redis_client
    _registry_repository = registry_repo
    _storage_repository = storage_repo


async def get_redis_client() -> redis.Redis:
    """Get Redis client dependency."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client


async def get_registry_repository() -> RegistryRepository:
    """Get registry repository dependency."""
    if _registry_repository is None:
        raise RuntimeError("Registry repository not initialized")
    return _registry_repository


async def get_storage_repository() -> PackageStorageRepository:
    """Get storage repository dependency."""
    if _storage_repository is None:
        raise RuntimeError("Storage repository not initialized")
    return _storage_repository


async def get_export_use_case(
    registry_repo: RegistryRepository = Depends(get_registry_repository),
    storage_repo: PackageStorageRepository = Depends(get_storage_repository)
) -> ExportMCPUseCase:
    """Get ExportMCPUseCase dependency."""
    return ExportMCPUseCase(registry_repo, storage_repo)


async def get_import_use_case(
    registry_repo: RegistryRepository = Depends(get_registry_repository),
    storage_repo: PackageStorageRepository = Depends(get_storage_repository)
) -> ImportMCPUseCase:
    """Get ImportMCPUseCase dependency."""
    return ImportMCPUseCase(registry_repo, storage_repo)


async def get_get_entry_use_case(
    registry_repo: RegistryRepository = Depends(get_registry_repository)
) -> GetRegistryEntryUseCase:
    """Get GetRegistryEntryUseCase dependency."""
    return GetRegistryEntryUseCase(registry_repo)


async def get_search_use_case(
    registry_repo: RegistryRepository = Depends(get_registry_repository)
) -> SearchRegistryUseCase:
    """Get SearchRegistryUseCase dependency."""
    return SearchRegistryUseCase(registry_repo)

