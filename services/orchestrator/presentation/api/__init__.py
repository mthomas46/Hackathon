"""Orchestrator REST API with comprehensive OpenAPI documentation."""

from fastapi import APIRouter

# Import the comprehensive orchestrator router
from .routes.orchestration import create_orchestrator_router

# Create API router with all orchestration endpoints
api_router = APIRouter()
api_router.include_router(create_orchestrator_router())

__all__ = ["api_router"]