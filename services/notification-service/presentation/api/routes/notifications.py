"""Notification REST API routes."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, field_validator
import re

from ....application.use_cases.send_notification_use_case import (
    SendNotificationUseCase,
    SendNotificationRequest,
    SendNotificationResponse
)

# Pydantic models for API
class SendNotificationRequestModel(BaseModel):
    """API model for send notification request with input validation and sanitization."""
    owners: List[str] = Field(..., description="List of owner names to notify", min_items=1, max_items=50)
    title: str = Field(..., description="Notification title", min_length=1, max_length=200)
    message: str = Field(..., description="Notification message", min_length=1, max_length=5000)
    channel: Optional[str] = Field(None, description="Notification channel (email, webhook, slack, sms)")
    priority: str = Field("normal", description="Notification priority (low, normal, high, urgent, critical)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    labels: Optional[List[str]] = Field(None, description="Notification labels")

    @field_validator('owners')
    @classmethod
    def validate_owners(cls, v):
        """Validate and sanitize owner names."""
        if not v:
            raise ValueError('At least one owner must be specified')

        sanitized_owners = []
        for owner in v:
            # Sanitize owner name - remove potentially dangerous characters
            sanitized = re.sub(r'[^\w\-_.@]', '', str(owner)).strip()
            if not sanitized:
                raise ValueError(f'Invalid owner name: {owner}')
            if len(sanitized) > 100:
                raise ValueError(f'Owner name too long: {owner}')
            sanitized_owners.append(sanitized)

        return sanitized_owners

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate and sanitize notification title."""
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')

        # Sanitize title - basic HTML/XSS prevention
        sanitized = re.sub(r'[<>]', '', str(v)).strip()
        if len(sanitized) > 200:
            raise ValueError('Title too long (max 200 characters)')

        return sanitized

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        """Validate and sanitize notification message."""
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')

        # Basic sanitization - remove script tags and other potentially dangerous content
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', str(v), flags=re.IGNORECASE)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)

        if len(sanitized) > 5000:
            raise ValueError('Message too long (max 5000 characters)')

        return sanitized

    @field_validator('channel')
    @classmethod
    def validate_channel(cls, v):
        """Validate notification channel."""
        if v is not None:
            valid_channels = ['email', 'webhook', 'slack', 'sms', 'teams', 'discord']
            if str(v).lower() not in valid_channels:
                raise ValueError(f'Invalid channel: {v}. Must be one of: {valid_channels}')
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate notification priority."""
        valid_priorities = ['low', 'normal', 'high', 'urgent', 'critical']
        if str(v).lower() not in valid_priorities:
            raise ValueError(f'Invalid priority: {v}. Must be one of: {valid_priorities}')
        return str(v).lower()

    @field_validator('labels')
    @classmethod
    def validate_labels(cls, v):
        """Validate and sanitize notification labels."""
        if v is not None:
            sanitized_labels = []
            for label in v:
                # Sanitize label - alphanumeric, hyphens, underscores only
                sanitized = re.sub(r'[^\w\-_]', '', str(label)).strip()
                if sanitized and len(sanitized) <= 50:
                    sanitized_labels.append(sanitized)
                if len(sanitized_labels) >= 10:  # Max 10 labels
                    break
            return sanitized_labels if sanitized_labels else None
        return v


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
