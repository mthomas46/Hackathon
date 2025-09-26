"""Presentation layer for Bedrock Proxy service.

This module contains the API endpoints and presentation logic for the service.
"""

from .api.routes import router as api_router

__all__ = ["api_router"]
