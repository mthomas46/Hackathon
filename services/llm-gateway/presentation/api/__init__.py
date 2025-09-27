"""LLM Gateway REST API with comprehensive OpenAPI documentation."""

from fastapi import APIRouter

# Import the comprehensive LLM router
from .routes.llm import create_llm_router

# Create API router with all LLM endpoints
api_router = APIRouter()
api_router.include_router(create_llm_router())

__all__ = ["api_router"]
