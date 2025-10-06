"""Entry point for MCP Infrastructure Service.

Run with:
    python -m services.mcp_infrastructure.main

Or with uvicorn:
    uvicorn services.mcp_infrastructure.main:app --reload --port 5500
"""

from services.mcp_infrastructure.presentation.api.main import app

__all__ = ["app"]

