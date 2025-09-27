"""Simulation Dashboard API presentation layer."""

from fastapi import APIRouter
from .routes import simulations, insights, analytics, audit

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include route modules
api_router.include_router(
    simulations.router,
    prefix="/simulations",
    tags=["simulations"]
)

api_router.include_router(
    insights.router,
    prefix="/insights",
    tags=["insights"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)

api_router.include_router(
    audit.router,
    prefix="/audit",
    tags=["audit"]
)

__all__ = ["api_router"]
