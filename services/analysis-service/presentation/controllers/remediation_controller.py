"""Remediation Controller - Handles automated remediation endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ...modules.models import AutomatedRemediationRequest, RemediationPreviewRequest
from ...modules.analysis_handlers import analysis_handlers


class RemediationController:
    """Controller for remediation-related endpoints."""

    def __init__(self):
        """Initialize controller."""
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.post("/remediate")
        async def remediate_endpoint(req: AutomatedRemediationRequest):
            """Apply automated fixes to documentation issues.

            Applies automated fixes to common documentation problems including
            formatting inconsistencies, terminology issues, and structural problems.
            Provides detailed reports of changes made and recommendations for review.
            """
            return await analysis_handlers.handle_automated_remediation(req)

        @self.router.post("/remediate/preview")
        async def remediate_preview_endpoint(req: RemediationPreviewRequest):
            """Preview automated remediation changes without applying them.

            Shows what changes would be made by automated remediation without
            actually applying them, allowing for review and approval before execution.
            """
            return await analysis_handlers.handle_remediation_preview(req)

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for this controller."""
        return self.router
