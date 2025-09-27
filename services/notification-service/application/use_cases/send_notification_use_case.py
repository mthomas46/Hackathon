"""Send notification use case."""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from ...domain.entities.notification import Notification
from ...domain.entities.owner import Owner
from ...domain.value_objects.notification_channel import NotificationChannel
from ...domain.value_objects.notification_priority import NotificationPriority
from ...domain.services.notification_sender import NotificationSender
from ...domain.services.owner_resolver import OwnerResolver


@dataclass
class SendNotificationRequest:
    """Request DTO for sending notifications."""
    owners: list[str]
    title: str
    message: str
    channel: Optional[str] = None
    priority: str = "normal"
    metadata: Optional[Dict[str, Any]] = None
    labels: Optional[list[str]] = None


@dataclass
class SendNotificationResponse:
    """Response DTO for sending notifications."""
    success: bool
    notifications_sent: int
    notifications_failed: int
    results: list[Dict[str, Any]]
    message: str


class SendNotificationUseCase:
    """Use case for sending notifications to owners.

    Orchestrates the process of resolving owners, creating notifications,
    and sending them through the appropriate channels.
    """

    def __init__(
        self,
        notification_sender: NotificationSender,
        owner_resolver: OwnerResolver
    ):
        """Initialize use case with dependencies."""
        self._notification_sender = notification_sender
        self._owner_resolver = owner_resolver

    async def execute(self, request: SendNotificationRequest) -> SendNotificationResponse:
        """Execute the send notification use case.

        Args:
            request: The send notification request

        Returns:
            Response indicating success/failure and details
        """
        try:
            # Resolve owners to their notification targets
            owner_targets = self._owner_resolver.resolve_owners(request.owners)

            results = []
            sent_count = 0
            failed_count = 0

            # Send notifications to each resolved owner
            for owner_name, targets in owner_targets.items():
                # Determine channel to use
                channel = request.channel
                if not channel:
                    # Find owner's preferred channel
                    owner_obj = self._create_owner_from_targets(owner_name, targets)
                    channel = owner_obj.primary_channel or "email"

                # Get target for the channel
                target = targets.get(channel)
                if not target:
                    results.append({
                        "owner": owner_name,
                        "success": False,
                        "error": f"No target found for channel {channel}"
                    })
                    failed_count += 1
                    continue

                try:
                    # Send notification
                    result = await self._notification_sender.send_notification(
                        channel=channel,
                        target=target,
                        title=request.title,
                        message=request.message,
                        metadata=request.metadata,
                        labels=request.labels
                    )

                    results.append({
                        "owner": owner_name,
                        "channel": channel,
                        "target": target,
                        "success": True,
                        "result": result
                    })
                    sent_count += 1

                except Exception as e:
                    results.append({
                        "owner": owner_name,
                        "channel": channel,
                        "success": False,
                        "error": str(e)
                    })
                    failed_count += 1

            success = sent_count > 0
            message = f"Sent {sent_count} notifications, {failed_count} failed"

            return SendNotificationResponse(
                success=success,
                notifications_sent=sent_count,
                notifications_failed=failed_count,
                results=results,
                message=message
            )

        except Exception as e:
            return SendNotificationResponse(
                success=False,
                notifications_sent=0,
                notifications_failed=len(request.owners),
                results=[],
                message=f"Failed to send notifications: {str(e)}"
            )

    def _create_owner_from_targets(self, name: str, targets: Dict[str, str]) -> Owner:
        """Create an Owner entity from resolved targets."""
        owner = Owner(name=name)

        # Map targets to owner attributes
        if "email" in targets:
            owner.email = targets["email"]
        if "webhook" in targets:
            owner.webhook_url = targets["webhook"]
        if "slack" in targets:
            owner.slack_channel = targets["slack"]

        return owner
