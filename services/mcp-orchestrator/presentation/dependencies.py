"""Dependency injection for FastAPI."""

import redis.asyncio as redis
from fastapi import Depends

from services.mcp_orchestrator.application.use_cases.create_workflow_use_case import CreateWorkflowUseCase
from services.mcp_orchestrator.application.use_cases.execute_workflow_use_case import ExecuteWorkflowUseCase
from services.mcp_orchestrator.application.use_cases.get_workflow_use_case import GetWorkflowUseCase
from services.mcp_orchestrator.domain.repositories.workflow_repository import WorkflowRepository
from services.mcp_orchestrator.infrastructure.config.settings import Settings, get_settings
from services.mcp_orchestrator.infrastructure.repositories.redis_workflow_repository import RedisWorkflowRepository

# Global instances (initialized on startup)
_redis_client: redis.Redis = None
_workflow_repository: WorkflowRepository = None


def init_dependencies(redis_client: redis.Redis, workflow_repo: WorkflowRepository):
    """Initialize global dependencies (called on startup)."""
    global _redis_client, _workflow_repository
    _redis_client = redis_client
    _workflow_repository = workflow_repo


async def get_redis_client() -> redis.Redis:
    """Get Redis client dependency."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client


async def get_workflow_repository() -> WorkflowRepository:
    """Get workflow repository dependency."""
    if _workflow_repository is None:
        raise RuntimeError("Workflow repository not initialized")
    return _workflow_repository


async def get_create_workflow_use_case(
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
    settings: Settings = Depends(get_settings)
) -> CreateWorkflowUseCase:
    """Get CreateWorkflowUseCase dependency."""
    # MCP Gateway client would be injected here in production
    return CreateWorkflowUseCase(
        workflow_repository=workflow_repo,
        mcp_gateway_client=None,  # Would be MCPGatewayClient
    )


async def get_execute_workflow_use_case(
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository),
    settings: Settings = Depends(get_settings)
) -> ExecuteWorkflowUseCase:
    """Get ExecuteWorkflowUseCase dependency."""
    # Clients would be injected here in production
    return ExecuteWorkflowUseCase(
        workflow_repository=workflow_repo,
        mcp_gateway_client=None,  # Would be MCPGatewayClient
        llm_gateway_client=None,  # Would be LLMGatewayClient
    )


async def get_get_workflow_use_case(
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository)
) -> GetWorkflowUseCase:
    """Get GetWorkflowUseCase dependency."""
    return GetWorkflowUseCase(workflow_repository=workflow_repo)

