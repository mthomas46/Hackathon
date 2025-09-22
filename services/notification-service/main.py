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

import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from services.shared.core.constants_new import ServiceNames
from services.shared.utilities import attach_self_register  # type: ignore
from services.shared.utilities.logging_client import get_log_collector_client
from services.shared.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore

from .modules.dlq_manager import dlq_manager
from .modules.notification_sender import notification_sender
from .modules.owner_resolver import owner_resolver

# Service configuration constants
SERVICE_NAME = "notification-service"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = int(os.environ.get("SERVICE_PORT", 5020))

# Default limits and constraints
DEFAULT_DLQ_LIMIT = 50
MAX_DLQ_LIMIT = 500

# Initialize log collector client
logger_client = None

app = FastAPI(
    title="Notification Service",
    version=SERVICE_VERSION,
    description="Centralized notification service with owner resolution, deduplication, and dead letter queue",
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)
attach_self_register(app, SERVICE_NAME)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global logger_client
    try:
        logger_client = await get_log_collector_client(ServiceNames.NOTIFICATION_SERVICE)
        if logger_client:
            await logger_client.log_business_event(
                "notification_service_startup",
                {
                    "version": SERVICE_VERSION,
                    "capabilities": [
                        "owner_resolution",
                        "notification_delivery",
                        "deduplication",
                        "dead_letter_queue",
                        "multi_channel_support",
                    ],
                    "integrations": ["email", "slack", "webhooks", "cache"],
                    "features": ["spam_prevention", "failure_retry", "delivery_tracking", "owner_caching"],
                },
            )
            await logger_client.log_info(
                "Notification service started",
                {
                    "channels": ["email", "slack", "webhook"],
                    "deduplication_enabled": True,
                    "dlq_enabled": True,
                    "owner_cache_enabled": True,
                },
            )
    except Exception as e:
        print(f"Failed to initialize log collector client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if logger_client:
        try:
            await logger_client.log_info("Notification service shutting down")
        except Exception:
            pass


class OwnerUpdate(BaseModel):
    """
    Request model for updating owner information in the system.

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
        "description": "Notification service is operational",
    }


@app.post("/owners/update")
async def owners_update(req: OwnerUpdate):
    """
    Update owner information in the ownership registry.

    This endpoint allows updating the mapping of entities to their
    owners and teams. In a production system, this would persist to a
    database or configuration repository.

    Currently implemented as a stub for testing purposes.
    """
    # Stub: in a real system, update ownership registry (DB or config repo)
    return {"status": "ok", "id": req.id, "owner": req.owner, "team": req.team}


class NotifyPayload(BaseModel):
    """
    Request model for sending notifications through various channels.

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
    """
    Send a notification through the specified channel with automatic
    deduplication.

    Processes the notification request, applies deduplication logic to
    prevent spam, and delivers through the appropriate channel. Failed
    notifications are automatically added to the dead letter queue for
    retry or analysis.
    """
    start_time = time.time()
    request_id = f"notify_{int(time.time() * 1000)}"

    try:
        # Log notification send start
        if logger_client:
            await logger_client.log_business_event(
                "notification_send_started",
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "target": req.target,
                    "title": req.title,
                    "has_metadata": bool(req.metadata),
                    "has_labels": bool(req.labels),
                    "message_length": len(req.message) if req.message else 0,
                },
            )

            await logger_client.log_info(
                "Sending notification",
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "target_type": "webhook" if req.channel == "webhook" else "address",
                    "has_deduplication": True,
                    "dlq_enabled": True,
                },
            )

        result = await notification_sender.send_notification(
            channel=req.channel,
            target=req.target,
            title=req.title,
            message=req.message,
            metadata=req.metadata,
            labels=req.labels,
        )

        processing_time = time.time() - start_time

        # Log successful notification delivery
        if logger_client:
            delivery_status = result.get("status", "unknown")
            was_deduplicated = result.get("deduplicated", False)

            await logger_client.log_business_event(
                "notification_delivered",
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "target": req.target,
                    "delivery_status": delivery_status,
                    "was_deduplicated": was_deduplicated,
                    "processing_time_seconds": processing_time,
                    "success": True,
                },
            )

            await logger_client.log_performance_metric(
                "notification_delivery",
                processing_time,
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "delivery_success": True,
                    "was_deduplicated": was_deduplicated,
                },
            )

        return result

    except Exception as e:
        error_time = time.time() - start_time

        # Add failed notification to DLQ for later analysis
        dlq_manager.add_failed_notification(req.model_dump(), str(e))

        # Log notification delivery failure
        if logger_client:
            await logger_client.log_error(
                f"Notification delivery failed: {str(e)}",
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "target": req.target,
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                    "dlq_queued": True,
                },
                error=e,
            )

            await logger_client.log_business_event(
                "notification_delivery_failed",
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "target": req.target,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_seconds": error_time,
                    "dlq_queued": True,
                },
            )

        raise


class ResolveOwnersRequest(BaseModel):
    """
    Request model for resolving multiple owners to their notification targets.

    Used to batch-resolve owner names to their corresponding
    notification channels and targets for efficient bulk operations.
    """

    owners: List[str]
    """List of owner names to resolve."""


@app.post("/owners/resolve")
async def owners_resolve(req: ResolveOwnersRequest):
    """
    Resolve a list of owner names to their notification targets.

    Takes multiple owner identifiers and returns their resolved
    notification targets (email addresses, webhook URLs, etc.) using
    cached mappings and fallback heuristics.
    """
    start_time = time.time()
    request_id = f"owner_resolve_{int(time.time() * 1000)}"

    try:
        # Log owner resolution start
        if logger_client:
            await logger_client.log_business_event(
                "owner_resolution_started",
                {
                    "request_id": request_id,
                    "owner_count": len(req.owners),
                    "owners": req.owners[:5] if len(req.owners) > 5 else req.owners,  # Limit for log size
                },
            )

            await logger_client.log_info(
                "Resolving owner targets",
                {"request_id": request_id, "owner_count": len(req.owners), "cache_enabled": True},
            )

        resolved_targets = owner_resolver.resolve_owners(req.owners)
        processing_time = time.time() - start_time

        resolved_count = sum(1 for target in resolved_targets.values() if target)
        unresolved_count = len(req.owners) - resolved_count

        # Log successful owner resolution
        if logger_client:
            await logger_client.log_business_event(
                "owner_resolution_completed",
                {
                    "request_id": request_id,
                    "total_owners": len(req.owners),
                    "resolved_count": resolved_count,
                    "unresolved_count": unresolved_count,
                    "processing_time_seconds": processing_time,
                    "success": True,
                },
            )

            await logger_client.log_performance_metric(
                "owner_resolution",
                processing_time,
                {
                    "request_id": request_id,
                    "resolution_success": True,
                    "resolved_count": resolved_count,
                    "unresolved_count": unresolved_count,
                },
            )

        return {"resolved": resolved_targets}

    except Exception as e:
        error_time = time.time() - start_time

        # Log owner resolution failure
        if logger_client:
            await logger_client.log_error(
                f"Owner resolution failed: {str(e)}",
                {
                    "request_id": request_id,
                    "owner_count": len(req.owners),
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                },
                error=e,
            )

            await logger_client.log_business_event(
                "owner_resolution_failed",
                {
                    "request_id": request_id,
                    "owner_count": len(req.owners),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_seconds": error_time,
                },
            )

        raise


@app.get("/dlq")
async def get_dlq(limit: int = 50):
    """
    Retrieve entries from the dead letter queue for failed notifications.

    Returns the most recent failed notification attempts for monitoring
    and debugging purposes. Limited to prevent excessive response sizes.
    """
    start_time = time.time()
    request_id = f"dlq_query_{int(time.time() * 1000)}"

    try:
        # Apply safety limits to prevent excessive memory usage
        safe_limit = min(limit, MAX_DLQ_LIMIT) if limit > 0 else DEFAULT_DLQ_LIMIT

        # Log DLQ query start
        if logger_client:
            await logger_client.log_business_event(
                "dlq_query_started",
                {
                    "request_id": request_id,
                    "requested_limit": limit,
                    "applied_limit": safe_limit,
                    "limit_was_capped": limit > MAX_DLQ_LIMIT if limit > 0 else False,
                },
            )

            await logger_client.log_info(
                "Querying dead letter queue",
                {"request_id": request_id, "applied_limit": safe_limit, "safety_limits_applied": True},
            )

        failed_notifications = dlq_manager.get_dlq_entries(safe_limit)
        processing_time = time.time() - start_time

        # Log successful DLQ query
        if logger_client:
            await logger_client.log_business_event(
                "dlq_query_completed",
                {
                    "request_id": request_id,
                    "entries_returned": len(failed_notifications),
                    "applied_limit": safe_limit,
                    "processing_time_seconds": processing_time,
                    "success": True,
                },
            )

            await logger_client.log_performance_metric(
                "dlq_query",
                processing_time,
                {"request_id": request_id, "entries_returned": len(failed_notifications), "query_success": True},
            )

        return {"items": failed_notifications}

    except Exception as e:
        error_time = time.time() - start_time

        # Log DLQ query failure
        if logger_client:
            await logger_client.log_error(
                f"DLQ query failed: {str(e)}",
                {
                    "request_id": request_id,
                    "requested_limit": limit,
                    "applied_limit": safe_limit if "safe_limit" in locals() else DEFAULT_DLQ_LIMIT,
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                },
                error=e,
            )

            await logger_client.log_business_event(
                "dlq_query_failed",
                {
                    "request_id": request_id,
                    "requested_limit": limit,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_seconds": error_time,
                },
            )

        raise


if __name__ == "__main__":
    """Run the Notification Service directly."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
