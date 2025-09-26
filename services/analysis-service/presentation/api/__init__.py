"""API package for analysis service."""

from fastapi import APIRouter

from .routers.analysis_router import router as analysis_router
from .routers.distributed_router import router as distributed_router
from .routers.repositories_router import router as repositories_router
from .routers.workflows_router import router as workflows_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(analysis_router)
api_router.include_router(workflows_router)
api_router.include_router(repositories_router)
api_router.include_router(distributed_router)
