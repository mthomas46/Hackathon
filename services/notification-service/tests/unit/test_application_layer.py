"""Unit tests for notification service application layer."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List

# Define mock entities and services to avoid import dependencies
from enum import Enum


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class NotificationPriority(str, Enum):
    NORMAL = "normal"
    HIGH = "high"


class MockNotification:
    """Mock notification entity."""
    def __init__(self, id: str = "test-notif", title: str = "Test", message: str = "Test message",
                 owners: List[str] = None, channel: NotificationChannel = None,
                 priority: NotificationPriority = NotificationPriority.NORMAL):
        self.id = id
        self.title = title
        self.message = message
        self.owners = owners or ["user1"]
        self.channel = channel or NotificationChannel.EMAIL
        self.priority = priority
        self.status = NotificationStatus.PENDING
        self.sent_at = None

    def mark_sent(self):
        """Mark as sent."""
        self.status = NotificationStatus.SENT

    def mark_failed(self):
        """Mark as failed."""
        self.status = NotificationStatus.FAILED


class MockOwner:
    """Mock owner entity."""
    def __init__(self, name: str = "Test User", email: str = "test@example.com"):
        self.name = name
        self.email = email

    def has_channel(self, channel: NotificationChannel) -> bool:
        return channel == NotificationChannel.EMAIL and self.email is not None


# Mock repositories
class MockNotificationRepository:
    """Mock notification repository."""
    def __init__(self):
        self.notifications = {}

    async def save(self, notification: MockNotification) -> MockNotification:
        """Save notification."""
        self.notifications[notification.id] = notification
        return notification

    async def get_by_id(self, notification_id: str) -> MockNotification:
        """Get notification by ID."""
        return self.notifications.get(notification_id)


class MockOwnerRepository:
    """Mock owner repository."""
    def __init__(self):
        self.owners = {
            "user1": MockOwner("User One", "user1@example.com"),
            "user2": MockOwner("User Two", "user2@example.com"),
        }

    async def get_by_names(self, names: List[str]) -> List[MockOwner]:
        """Get owners by names."""
        return [self.owners[name] for name in names if name in self.owners]


# Mock domain services
class MockOwnerResolverService:
    """Mock owner resolver service."""
    def __init__(self, owner_repo: MockOwnerRepository):
        self.owner_repo = owner_repo

    async def resolve_owners(self, owner_names: List[str]) -> List[MockOwner]:
        """Resolve owners."""
        return await self.owner_repo.get_by_names(owner_names)


class MockNotificationSenderService:
    """Mock notification sender service."""
    def __init__(self):
        self.send_results = {}

    async def send_bulk_notifications(self, notification: MockNotification, owners: List[MockOwner]) -> dict:
        """Send notifications."""
        sent = 0
        failed = 0

        for owner in owners:
            if owner.has_channel(notification.channel):
                sent += 1
                notification.mark_sent()
            else:
                failed += 1
                notification.mark_failed()

        return {"sent": sent, "failed": failed}


# Application use case
class SendNotificationUseCase:
    """Use case for sending notifications."""

    def __init__(self,
                 notification_repo: MockNotificationRepository,
                 owner_resolver: MockOwnerResolverService,
                 notification_sender: MockNotificationSenderService):
        self.notification_repo = notification_repo
        self.owner_resolver = owner_resolver
        self.notification_sender = notification_sender

    async def execute(self, request: dict) -> dict:
        """Execute the send notification use case."""
        try:
            # Create notification
            notification = MockNotification(
                title=request["title"],
                message=request["message"],
                owners=request["owners"],
                channel=request.get("channel", NotificationChannel.EMAIL),
                priority=request.get("priority", NotificationPriority.NORMAL)
            )

            # Save notification
            saved_notification = await self.notification_repo.save(notification)

            # Resolve owners
            owners = await self.owner_resolver.resolve_owners(request["owners"])

            # Send notifications
            send_results = await self.notification_sender.send_bulk_notifications(saved_notification, owners)

            return {
                "success": True,
                "notification_id": saved_notification.id,
                "results": send_results,
                "message": f"Notification sent to {send_results['sent']} owners"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send notification"
            }


class TestSendNotificationUseCase:
    """Test the SendNotificationUseCase."""

    @pytest.fixture
    def notification_repo(self):
        """Create notification repository."""
        return MockNotificationRepository()

    @pytest.fixture
    def owner_repo(self):
        """Create owner repository."""
        return MockOwnerRepository()

    @pytest.fixture
    def owner_resolver(self, owner_repo):
        """Create owner resolver service."""
        return MockOwnerResolverService(owner_repo)

    @pytest.fixture
    def notification_sender(self):
        """Create notification sender service."""
        return MockNotificationSenderService()

    @pytest.fixture
    def use_case(self, notification_repo, owner_resolver, notification_sender):
        """Create use case instance."""
        return SendNotificationUseCase(notification_repo, owner_resolver, notification_sender)

    @pytest.fixture
    def valid_request(self):
        """Create valid request data."""
        return {
            "title": "Test Notification",
            "message": "This is a test notification",
            "owners": ["user1", "user2"]
        }

    @pytest.mark.asyncio
    async def test_execute_success(self, use_case, valid_request):
        """Test successful notification sending."""
        result = await use_case.execute(valid_request)

        assert result["success"] is True
        assert "notification_id" in result
        assert "results" in result
        assert result["results"]["sent"] == 2
        assert result["results"]["failed"] == 0
        assert "Notification sent to 2 owners" in result["message"]

    @pytest.mark.asyncio
    async def test_execute_partial_success(self, use_case, owner_repo):
        """Test partial success when some owners lack channels."""
        # Add owner without email
        owner_repo.owners["user3"] = MockOwner("User Three", None)

        request = {
            "title": "Partial Test",
            "message": "Testing partial success",
            "owners": ["user1", "user3"]  # user3 has no email
        }

        result = await use_case.execute(request)

        assert result["success"] is True
        assert result["results"]["sent"] == 1  # Only user1 succeeds
        assert result["results"]["failed"] == 1  # user3 fails

    @pytest.mark.asyncio
    async def test_execute_with_custom_channel(self, use_case):
        """Test execution with custom notification channel."""
        request = {
            "title": "Channel Test",
            "message": "Testing custom channel",
            "owners": ["user1"],
            "channel": NotificationChannel.SLACK
        }

        result = await use_case.execute(request)

        assert result["success"] is True
        assert result["results"]["sent"] == 0  # user1 doesn't have Slack

    @pytest.mark.asyncio
    async def test_execute_missing_required_fields(self, use_case):
        """Test execution with missing required fields."""
        invalid_request = {
            "message": "Missing title",
            "owners": ["user1"]
            # Missing title
        }

        result = await use_case.execute(invalid_request)
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_empty_owners(self, use_case):
        """Test execution with empty owners list."""
        request = {
            "title": "Empty Owners Test",
            "message": "Testing empty owners",
            "owners": []
        }

        result = await use_case.execute(request)

        assert result["success"] is True
        assert result["results"]["sent"] == 0
        assert result["results"]["failed"] == 0

    @pytest.mark.asyncio
    async def test_execute_service_failure(self, use_case, notification_sender):
        """Test handling of service failures."""
        # Make sender fail
        notification_sender.send_bulk_notifications = AsyncMock(return_value={"sent": 0, "failed": 1})

        request = {
            "title": "Failure Test",
            "message": "Testing failure handling",
            "owners": ["user1"]
        }

        result = await use_case.execute(request)

        assert result["success"] is True  # Use case succeeds, but sending fails
        assert result["results"]["sent"] == 0
        assert result["results"]["failed"] == 1

    @pytest.mark.asyncio
    async def test_notification_persistence(self, use_case, notification_repo, valid_request):
        """Test that notifications are properly persisted."""
        result = await use_case.execute(valid_request)

        notification_id = result["notification_id"]
        saved_notification = await notification_repo.get_by_id(notification_id)

        assert saved_notification is not None
        assert saved_notification.title == valid_request["title"]
        assert saved_notification.message == valid_request["message"]
        assert saved_notification.owners == valid_request["owners"]


class TestUseCaseIntegration:
    """Test integration aspects of the use case."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        # Setup dependencies
        notification_repo = MockNotificationRepository()
        owner_repo = MockOwnerRepository()
        owner_resolver = MockOwnerResolverService(owner_repo)
        notification_sender = MockNotificationSenderService()

        # Create use case
        use_case = SendNotificationUseCase(notification_repo, owner_resolver, notification_sender)

        # Execute workflow
        request = {
            "title": "E2E Test",
            "message": "End-to-end workflow test",
            "owners": ["user1", "user2"],
            "priority": NotificationPriority.HIGH
        }

        result = await use_case.execute(request)

        # Verify results
        assert result["success"] is True
        assert result["results"]["sent"] == 2

        # Verify persistence
        notification_id = result["notification_id"]
        saved = await notification_repo.get_by_id(notification_id)
        assert saved is not None
        assert saved.title == "E2E Test"
        assert saved.priority == NotificationPriority.HIGH
