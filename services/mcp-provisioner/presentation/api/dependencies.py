"""Dependency injection for FastAPI."""

import logging
from typing import AsyncGenerator
import redis.asyncio as redis

from services.mcp_provisioner.infrastructure.config.settings import Settings, get_settings
from services.mcp_provisioner.infrastructure.repositories.redis_mcp_repository import RedisMCPRepository
from services.mcp_provisioner.infrastructure.external_services.docker_service import DockerServiceImpl
from services.mcp_provisioner.infrastructure.external_services.port_allocator import PortAllocator
from services.mcp_provisioner.application.use_cases.provision_mcp_use_case import ProvisionMCPUseCase
from services.mcp_provisioner.application.use_cases.start_mcp_use_case import StartMCPUseCase
from services.mcp_provisioner.application.use_cases.stop_mcp_use_case import StopMCPUseCase
from services.mcp_provisioner.application.use_cases.get_mcp_status_use_case import GetMCPStatusUseCase
from services.mcp_provisioner.application.use_cases.list_mcps_use_case import ListMCPsUseCase
from services.mcp_provisioner.application.use_cases.delete_mcp_use_case import DeleteMCPUseCase


logger = logging.getLogger(__name__)


# Global instances (initialized at startup)
_redis_client: redis.Redis = None
_port_allocator: PortAllocator = None
_docker_service: DockerServiceImpl = None


async def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=False,  # We'll handle encoding
        )
        logger.info("Redis client initialized")
    return _redis_client


async def get_port_allocator() -> PortAllocator:
    """Get port allocator instance."""
    global _port_allocator
    if _port_allocator is None:
        settings = get_settings()
        _port_allocator = PortAllocator(settings)
        logger.info("Port allocator initialized")
    return _port_allocator


async def get_docker_service() -> DockerServiceImpl:
    """Get Docker service instance."""
    global _docker_service
    if _docker_service is None:
        settings = get_settings()
        port_allocator = await get_port_allocator()
        _docker_service = DockerServiceImpl(settings, port_allocator)
        logger.info("Docker service initialized")
    return _docker_service


async def get_repository() -> RedisMCPRepository:
    """Get MCP repository instance."""
    redis_client = await get_redis_client()
    settings = get_settings()
    return RedisMCPRepository(redis_client, settings)


async def get_provision_use_case() -> ProvisionMCPUseCase:
    """Get provision use case instance."""
    repository = await get_repository()
    return ProvisionMCPUseCase(repository)


async def get_start_use_case() -> StartMCPUseCase:
    """Get start use case instance."""
    repository = await get_repository()
    docker_service = await get_docker_service()
    return StartMCPUseCase(repository, docker_service)


async def get_stop_use_case() -> StopMCPUseCase:
    """Get stop use case instance."""
    repository = await get_repository()
    docker_service = await get_docker_service()
    return StopMCPUseCase(repository, docker_service)


async def get_get_status_use_case() -> GetMCPStatusUseCase:
    """Get status use case instance."""
    repository = await get_repository()
    return GetMCPStatusUseCase(repository)


async def get_list_use_case() -> ListMCPsUseCase:
    """Get list use case instance."""
    repository = await get_repository()
    return ListMCPsUseCase()


async def get_delete_use_case() -> DeleteMCPUseCase:
    """Get delete use case instance."""
    repository = await get_repository()
    docker_service = await get_docker_service()
    return DeleteMCPUseCase(repository, docker_service)


async def close_dependencies():
    """Close all dependency connections."""
    global _redis_client, _docker_service
    
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis client closed")
    
    if _docker_service:
        _docker_service.close()
        logger.info("Docker service closed")

