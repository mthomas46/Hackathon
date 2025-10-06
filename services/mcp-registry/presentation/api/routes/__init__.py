"""API Routes for MCP Registry."""

from .registry import router as registry_router
from .health import router as health_router

__all__ = ["registry_router", "health_router"]

