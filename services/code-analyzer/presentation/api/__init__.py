"""Code Analyzer REST API."""

from fastapi import APIRouter

# Import dependencies (these would normally come from dependency injection)
from ...application.use_cases.analyze_code_use_case import AnalyzeCodeUseCase

# Create dependencies (mock implementations for now)
_analyze_code_use_case = AnalyzeCodeUseCase()

# Import and create routers
from .routes.analysis import create_analysis_router

# Create API router
api_router = APIRouter()
api_router.include_router(create_analysis_router(_analyze_code_use_case))

__all__ = ["api_router"]
