"""Findings Controller - Handles findings management endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ...modules.analysis_handlers import analysis_handlers


class FindingsController:
    """Controller for findings-related endpoints."""

    def __init__(self):
        """Initialize controller."""
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.get("/findings")
        async def get_findings_endpoint():
            """Retrieve analysis findings with filtering by severity and type.

            Provides filtered access to analysis findings with support for
            severity levels, finding types, date ranges, and document-specific queries.
            """
            return await analysis_handlers.handle_list_findings()

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for this controller."""
        return self.router
