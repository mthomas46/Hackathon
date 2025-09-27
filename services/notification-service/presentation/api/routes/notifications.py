"""Notification REST API routes."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ....application.use_cases.send_notification_use_case import (
    SendNotificationUseCase,
    SendNotificationRequest,
    SendNotificationResponse
)

# Pydantic models for API
class SendNotificationRequestModel(BaseModel):
    """API model for send notification request."""
    owners: List[str] = Field(..., description="List of owner names to notify")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    channel: Optional[str] = Field(None, description="Notification channel (email, webhook, slack, sms)")
    priority: str = Field("normal", description="Notification priority (low, normal, high, urgent, critical)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    labels: Optional[List[str]] = Field(None, description="Notification labels")


class SendNotificationResponseModel(BaseModel):
    """API model for send notification response."""
    success: bool
    notifications_sent: int
    notifications_failed: int
    results: List[Dict[str, Any]]
    message: str


class NotificationRouter:
    """FastAPI router for notification endpoints."""

    def __init__(self, send_notification_use_case: SendNotificationUseCase):
        """Initialize router with use case."""
        self._send_notification_use_case = send_notification_use_case
        self.router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all notification routes."""

        @self.router.post("/send", response_model=SendNotificationResponseModel)
        async def send_notification(
            request: SendNotificationRequestModel,
            background_tasks: BackgroundTasks
        ) -> SendNotificationResponseModel:
            """Send notification to specified owners.

            Sends notifications to the specified owners using their preferred
            or specified notification channels.
            """
            try:
                # Convert API model to use case request
                use_case_request = SendNotificationRequest(
                    owners=request.owners,
                    title=request.title,
                    message=request.message,
                    channel=request.channel,
                    priority=request.priority,
                    metadata=request.metadata,
                    labels=request.labels
                )

                # Execute use case
                response = await self._send_notification_use_case.execute(use_case_request)

                # Convert use case response to API model
                return SendNotificationResponseModel(
                    success=response.success,
                    notifications_sent=response.notifications_sent,
                    notifications_failed=response.notifications_failed,
                    results=response.results,
                    message=response.message
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to send notification: {str(e)}"
                )

        @self.router.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "notification-service",
                "version": "1.0.0"
            }

        @self.router.post("/test")
        async def test_notification(request: SendNotificationRequestModel) -> Dict[str, Any]:
            """Test notification endpoint (doesn't actually send)."""
            return {
                "status": "test_mode",
                "would_send_to": len(request.owners),
                "owners": request.owners,
                "channel": request.channel or "auto-detect",
                "title": request.title,
                "message_preview": request.message[:50] + "..." if len(request.message) > 50 else request.message
            }


# Factory function to create router
def create_notification_router(
    send_notification_use_case: SendNotificationUseCase
) -> APIRouter:
    """Create notification router with dependencies."""
    router_instance = NotificationRouter(send_notification_use_case)
    return router_instance.router
