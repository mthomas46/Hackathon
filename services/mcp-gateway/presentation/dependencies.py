"""Dependency injection for FastAPI."""

import redis.asyncio as redis
from fastapi import Depends

from services.mcp_gateway.application.use_cases.register_instance_use_case import RegisterInstanceUseCase
from services.mcp_gateway.application.use_cases.deregister_instance_use_case import DeregisterInstanceUseCase
from services.mcp_gateway.application.use_cases.route_request_use_case import RouteRequestUseCase
from services.mcp_gateway.application.use_cases.update_health_use_case import UpdateHealthUseCase
from services.mcp_gateway.application.use_cases.get_available_instances_use_case import GetAvailableInstancesUseCase
from services.mcp_gateway.domain.repositories.mcp_registry_repository import MCPRegistryRepository
from services.mcp_gateway.infrastructure.config.settings import Settings, get_settings
from services.mcp_gateway.infrastructure.repositories.redis_mcp_registry_repository import RedisMCPRegistryRepository

# Global instances (initialized on startup)
_redis_client: redis.Redis = None
_registry_repository: MCPRegistryRepository = None


def init_dependencies(redis_client: redis.Redis, registry: MCPRegistryRepository):
    """Initialize global dependencies (called on startup)."""
    global _redis_client, _registry_repository
    _redis_client = redis_client
    _registry_repository = registry


async def get_redis_client() -> redis.Redis:
    """Get Redis client dependency."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client


async def get_registry_repository() -> MCPRegistryRepository:
    """Get registry repository dependency."""
    if _registry_repository is None:
        raise RuntimeError("Registry repository not initialized")
    return _registry_repository


async def get_register_instance_use_case(
    registry: MCPRegistryRepository = Depends(get_registry_repository)
) -> RegisterInstanceUseCase:
    """Get RegisterInstanceUseCase dependency."""
    return RegisterInstanceUseCase(registry)


async def get_deregister_instance_use_case(
    registry: MCPRegistryRepository = Depends(get_registry_repository)
) -> DeregisterInstanceUseCase:
    """Get DeregisterInstanceUseCase dependency."""
    return DeregisterInstanceUseCase(registry)


async def get_route_request_use_case(
    registry: MCPRegistryRepository = Depends(get_registry_repository),
    settings: Settings = Depends(get_settings)
) -> RouteRequestUseCase:
    """Get RouteRequestUseCase dependency."""
    from services.mcp_gateway.domain.value_objects.routing_strategy import RoutingStrategy
    
    # Parse routing strategy from settings
    try:
        strategy = RoutingStrategy(settings.default_routing_strategy)
    except ValueError:
        strategy = RoutingStrategy.LEAST_LOADED
    
    return RouteRequestUseCase(registry, default_strategy=strategy)


async def get_update_health_use_case(
    registry: MCPRegistryRepository = Depends(get_registry_repository)
) -> UpdateHealthUseCase:
    """Get UpdateHealthUseCase dependency."""
    return UpdateHealthUseCase(registry)


async def get_available_instances_use_case(
    registry: MCPRegistryRepository = Depends(get_registry_repository)
) -> GetAvailableInstancesUseCase:
    """Get GetAvailableInstancesUseCase dependency."""
    return GetAvailableInstancesUseCase(registry)

