"""API package for project simulation service."""

from fastapi import APIRouter

from .routers.discovery_router import router as discovery_router
from .routers.health_router import router as health_router
from .routers.simulation_router import router as simulation_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(health_router)
api_router.include_router(simulation_router)
api_router.include_router(discovery_router)
