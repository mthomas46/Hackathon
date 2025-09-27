"""Notification service REST API."""

from fastapi import APIRouter
from .routes.notifications import create_notification_router

# Import dependencies (these would normally come from dependency injection)
from ...application.use_cases.send_notification_use_case import SendNotificationUseCase
from ...domain.services.notification_sender import NotificationSender
from ...domain.services.owner_resolver import OwnerResolver

# Create dependencies
_notification_sender = NotificationSender()
_owner_resolver = OwnerResolver()
_send_notification_use_case = SendNotificationUseCase(_notification_sender, _owner_resolver)

# Create API router
api_router = APIRouter()
api_router.include_router(create_notification_router(_send_notification_use_case))

__all__ = ["api_router"]
