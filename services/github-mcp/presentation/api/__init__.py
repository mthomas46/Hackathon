"""GitHub MCP API presentation layer."""

from fastapi import APIRouter
from .routes import github, tools, repositories, pull_requests, issues

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include route modules
api_router.include_router(
    github.router,
    prefix="/github",
    tags=["github"]
)

api_router.include_router(
    tools.router,
    prefix="/tools",
    tags=["tools"]
)

api_router.include_router(
    repositories.router,
    prefix="/repositories",
    tags=["repositories"]
)

api_router.include_router(
    pull_requests.router,
    prefix="/pull-requests",
    tags=["pull-requests"]
)

api_router.include_router(
    issues.router,
    prefix="/issues",
    tags=["issues"]
)

__all__ = ["api_router"]
