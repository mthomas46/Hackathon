"""API Routes for MCP Interpreter."""

from .interpreter import router as interpreter_router
from .health import router as health_router

__all__ = ["interpreter_router", "health_router"]

