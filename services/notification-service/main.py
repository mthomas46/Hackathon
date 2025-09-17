"""Service: Notification Service

Endpoints:
- POST /owners/update: Update owner information in the system
- POST /owners/resolve: Resolve owners to their notification targets
- POST /notify: Send notifications with deduplication and error handling
- GET /dlq: Retrieve failed notifications from dead letter queue
- GET /health: Service health check

Responsibilities:
- Resolve owner names to notification targets (email, Slack, webhooks)
- Send notifications with automatic deduplication to prevent spam
- Maintain a dead-letter queue for failed notification delivery
- Cache owner resolutions with configurable TTL for performance

Dependencies: shared middlewares for request tracking; httpx for webhook delivery.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from services.shared.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore
from services.shared.utilities import attach_self_register  # type: ignore

from .modules.owner_resolver import owner_resolver
from .modules.notification_sender import notification_sender
from .modules.dlq_manager import dlq_manager

# Service configuration constants
SERVICE_NAME = "notification-service"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 5095

# Default limits and constraints
DEFAULT_DLQ_LIMIT = 50
MAX_DLQ_LIMIT = 500

app = FastAPI(
    title="Notification Service",
    version=SERVICE_VERSION,
    description="Centralized notification service with owner resolution, deduplication, and dead letter queue"
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)
attach_self_register(app, SERVICE_NAME)


class OwnerUpdate(BaseModel):
    """Request model for updating owner information in the system.

    Used to update the ownership registry that maps entities to their
    responsible owners and teams for notification routing.
    """
    id: str
    """Unique identifier for the entity being updated."""

    owner: Optional[str] = None
    """Individual owner name or handle."""

    team: Optional[str] = None
    """Team name that owns this entity."""


@app.get("/health")
async def health():
    """Health check endpoint returning service status and basic information."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "Notification service is operational"
    }


@app.post("/owners/update")
async def owners_update(req: OwnerUpdate):
    """Update owner information in the ownership registry.

    This endpoint allows updating the mapping of entities to their owners
    and teams. In a production system, this would persist to a database
    or configuration repository.

    Currently implemented as a stub for testing purposes.
    """
    # Stub: in a real system, update ownership registry (DB or config repo)
    return {
        "status": "ok",
        "id": req.id,
        "owner": req.owner,
        "team": req.team
    }


class NotifyPayload(BaseModel):
    """Request model for sending notifications through various channels.

    Supports multiple notification channels with automatic deduplication
    and metadata enrichment for better notification management.
    """
    channel: str
    """Notification channel: 'slack', 'email', or 'webhook'."""

    target: str
    """Delivery target: webhook URL for webhooks, email address for email, etc."""

    title: str
    """Notification title or subject line."""

    message: str
    """Main notification message content."""

    metadata: Dict[str, Any] = {}
    """Additional structured metadata for the notification."""

    labels: List[str] = []
    """Categorization labels for filtering and routing."""


@app.post("/notify")
async def notify(req: NotifyPayload):
    """Send a notification through the specified channel with automatic deduplication.

    Processes the notification request, applies deduplication logic to prevent
    spam, and delivers through the appropriate channel. Failed notifications
    are automatically added to the dead letter queue for retry or analysis.
    """
    try:
        result = await notification_sender.send_notification(
            channel=req.channel,
            target=req.target,
            title=req.title,
            message=req.message,
            metadata=req.metadata,
            labels=req.labels
        )
        return result
    except Exception as e:
        # Add failed notification to DLQ for later analysis
        dlq_manager.add_failed_notification(req.model_dump(), str(e))
        raise


class ResolveOwnersRequest(BaseModel):
    """Request model for resolving multiple owners to their notification targets.

    Used to batch-resolve owner names to their corresponding notification
    channels and targets for efficient bulk operations.
    """
    owners: List[str]
    """List of owner names to resolve."""


@app.post("/owners/resolve")
async def owners_resolve(req: ResolveOwnersRequest):
    """Resolve a list of owner names to their notification targets.

    Takes multiple owner identifiers and returns their resolved notification
    targets (email addresses, webhook URLs, etc.) using cached mappings
    and fallback heuristics.
    """
    resolved_targets = owner_resolver.resolve_owners(req.owners)
    return {"resolved": resolved_targets}


@app.get("/dlq")
async def get_dlq(limit: int = 50):
    """Retrieve entries from the dead letter queue for failed notifications.

    Returns the most recent failed notification attempts for monitoring
    and debugging purposes. Limited to prevent excessive response sizes.
    """
    # Apply safety limits to prevent excessive memory usage
    safe_limit = min(limit, MAX_DLQ_LIMIT) if limit > 0 else DEFAULT_DLQ_LIMIT
    failed_notifications = dlq_manager.get_dlq_entries(safe_limit)
    return {"items": failed_notifications}


if __name__ == "__main__":
    """Run the Notification Service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )


