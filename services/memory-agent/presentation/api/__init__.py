"""Memory Agent REST API."""

from fastapi import APIRouter

# Import dependencies (these would normally come from dependency injection)
from ...application.use_cases.analyze_memory_use_case import AnalyzeMemoryUseCase
from ...application.use_cases.optimize_memory_use_case import OptimizeMemoryUseCase

# Create dependencies (mock implementations for now)
_analyze_memory_use_case = AnalyzeMemoryUseCase()
_optimize_memory_use_case = OptimizeMemoryUseCase()

# Import and create routers
from .routes.memory import create_memory_router

# Create API router
api_router = APIRouter()
api_router.include_router(create_memory_router(_analyze_memory_use_case, _optimize_memory_use_case))

__all__ = ["api_router"]