"""Workflow Controller - Handles workflow and webhook endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ...modules.models import (
    WorkflowEventRequest,
    WorkflowStatusRequest,
    WebhookConfigRequest
)
from ...modules.analysis_handlers import analysis_handlers


class WorkflowController:
    """Controller for workflow-related endpoints."""

    def __init__(self):
        """Initialize controller."""
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.post("/workflows/events")
        async def process_workflow_events_endpoint(req: WorkflowEventRequest):
            """Process workflow events and trigger appropriate analyses.

            Processes events from external systems (GitHub, GitLab, CI/CD) and
            triggers automated analysis workflows based on configured rules and conditions.
            """
            return await analysis_handlers.handle_workflow_event(req)

        @self.router.get("/workflows/{workflow_id}")
        async def get_workflow_status_endpoint(workflow_id: str):
            """Get the status of a workflow analysis.

            Retrieves detailed status information for a specific workflow analysis
            including progress, results, and any errors encountered.
            """
            return await analysis_handlers.handle_workflow_status(
                WorkflowStatusRequest(workflow_id=workflow_id)
            )

        @self.router.get("/workflows/queue/status")
        async def get_workflow_queue_status_endpoint():
            """Get the status of workflow analysis queues.

            Provides comprehensive view of workflow analysis queue including
            pending tasks, processing status, and performance metrics.
            """
            return await analysis_handlers.handle_workflow_queue_status()

        @self.router.post("/workflows/webhook/config")
        async def configure_webhook_endpoint(req: WebhookConfigRequest):
            """Configure webhook settings for workflow integration.

            Configures webhook endpoints and settings for integration with
            external systems like GitHub, GitLab, and CI/CD pipelines.
            """
            return await analysis_handlers.handle_webhook_config(req)

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for this controller."""
        return self.router
