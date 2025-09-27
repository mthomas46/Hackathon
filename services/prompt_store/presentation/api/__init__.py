"""Prompt Store REST API with comprehensive OpenAPI documentation."""

from fastapi import APIRouter

# Import the comprehensive prompt router
from .routes.prompts import create_prompt_router

# Create API router with all prompt management endpoints
api_router = APIRouter()
api_router.include_router(create_prompt_router())

__all__ = ["api_router"]