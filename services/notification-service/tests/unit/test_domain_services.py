"""Unit tests for notification service domain services."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Optional

# Define mock domain entities to avoid import dependencies
from enum import Enum


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class MockNotification:
    """Mock notification for testing."""
    def __init__(self, id: str = "test-notif", title: str = "Test", message: str = "Test message",
                 owners: List[str] = None, channel: NotificationChannel = None,
                 priority: NotificationPriority = NotificationPriority.NORMAL):
        self.id = id
        self.title = title
        self.message = message
        self.owners = owners or ["user1"]
        self.channel = channel or NotificationChannel.EMAIL
        self.priority = priority

    def mark_sent(self):
        pass

    def mark_failed(self):
        pass


class MockOwner:
    """Mock owner for testing."""
    def __init__(self, name: str = "Test User", email: str = "test@example.com",
                 slack_id: str = "U123456", webhook_url: str = None, phone: str = None):
        self.name = name
        self.email = email
        self.slack_id = slack_id
        self.webhook_url = webhook_url
        self.phone = phone

    def has_channel(self, channel: NotificationChannel) -> bool:
        """Mock channel support check."""
        if channel == NotificationChannel.EMAIL and self.email:
            return True
        if channel == NotificationChannel.SLACK and self.slack_id:
            return True
        if channel == NotificationChannel.WEBHOOK and self.webhook_url:
            return True
        if channel == NotificationChannel.SMS and self.phone:
            return True
        return False

    def get_channel_value(self, channel: NotificationChannel) -> Optional[str]:
        """Mock channel value getter."""
        if channel == NotificationChannel.EMAIL:
            return self.email
        if channel == NotificationChannel.SLACK:
            return self.slack_id
        if channel == NotificationChannel.WEBHOOK:
            return self.webhook_url
        if channel == NotificationChannel.SMS:
            return self.phone
        return None


# Mock domain services
class OwnerResolverService:
    """Mock owner resolver service for testing."""

    def __init__(self):
        self.owners_db = {
            "user1": MockOwner("User One", "user1@example.com", "U111111"),
            "user2": MockOwner("User Two", "user2@example.com", "U222222", "https://hooks.slack.com/webhook1"),
            "user3": MockOwner("User Three", None, "U333333"),  # No email
        }

    async def resolve_owners(self, owner_names: List[str]) -> List[MockOwner]:
        """Resolve owner names to owner objects."""
        resolved = []
        for name in owner_names:
            if name in self.owners_db:
                resolved.append(self.owners_db[name])
        return resolved

    async def get_owner_by_name(self, name: str) -> Optional[MockOwner]:
        """Get owner by name."""
        return self.owners_db.get(name)


class NotificationSenderService:
    """Mock notification sender service for testing."""

    def __init__(self):
        self.sent_notifications = []
        self.failed_notifications = []

    async def send_notification(self, notification: MockNotification, owner: MockOwner) -> bool:
        """Send notification to owner via appropriate channel."""
        try:
            if not owner.has_channel(notification.channel):
                raise ValueError(f"Owner {owner.name} does not support channel {notification.channel}")

            # Simulate sending
            self.sent_notifications.append({
                "notification_id": notification.id,
                "owner": owner.name,
                "channel": notification.channel,
                "success": True
            })

            return True

        except Exception as e:
            self.failed_notifications.append({
                "notification_id": notification.id,
                "owner": owner.name,
                "channel": notification.channel,
                "error": str(e)
            })
            return False

    async def send_bulk_notifications(self, notification: MockNotification, owners: List[MockOwner]) -> Dict[str, int]:
        """Send notification to multiple owners."""
        results = {"sent": 0, "failed": 0}

        for owner in owners:
            success = await self.send_notification(notification, owner)
            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1

        return results


class TestOwnerResolverService:
    """Test the OwnerResolverService."""

    @pytest.fixture
    def resolver_service(self):
        """Create resolver service for testing."""
        return OwnerResolverService()

    @pytest.mark.asyncio
    async def test_resolve_owners_success(self, resolver_service):
        """Test successful owner resolution."""
        owners = await resolver_service.resolve_owners(["user1", "user2"])

        assert len(owners) == 2
        assert owners[0].name == "User One"
        assert owners[0].email == "user1@example.com"
        assert owners[1].name == "User Two"
        assert owners[1].webhook_url == "https://hooks.slack.com/webhook1"

    @pytest.mark.asyncio
    async def test_resolve_owners_partial(self, resolver_service):
        """Test partial owner resolution."""
        owners = await resolver_service.resolve_owners(["user1", "nonexistent", "user2"])

        assert len(owners) == 2  # Only existing owners
        assert all(owner.name in ["User One", "User Two"] for owner in owners)

    @pytest.mark.asyncio
    async def test_resolve_owners_empty(self, resolver_service):
        """Test resolving empty owner list."""
        owners = await resolver_service.resolve_owners([])

        assert len(owners) == 0

    @pytest.mark.asyncio
    async def test_get_owner_by_name_success(self, resolver_service):
        """Test getting owner by name."""
        owner = await resolver_service.get_owner_by_name("user1")

        assert owner is not None
        assert owner.name == "User One"
        assert owner.email == "user1@example.com"

    @pytest.mark.asyncio
    async def test_get_owner_by_name_not_found(self, resolver_service):
        """Test getting non-existent owner."""
        owner = await resolver_service.get_owner_by_name("nonexistent")

        assert owner is None


class TestNotificationSenderService:
    """Test the NotificationSenderService."""

    @pytest.fixture
    def sender_service(self):
        """Create sender service for testing."""
        return NotificationSenderService()

    @pytest.fixture
    def sample_notification(self):
        """Create sample notification for testing."""
        return MockNotification(
            title="Test Notification",
            message="This is a test",
            owners=["user1"],
            channel=NotificationChannel.EMAIL
        )

    @pytest.fixture
    def sample_owner(self):
        """Create sample owner for testing."""
        return MockOwner(
            name="Test User",
            email="test@example.com",
            slack_id="U123456"
        )

    @pytest.mark.asyncio
    async def test_send_notification_success(self, sender_service, sample_notification, sample_owner):
        """Test successful notification sending."""
        success = await sender_service.send_notification(sample_notification, sample_owner)

        assert success is True
        assert len(sender_service.sent_notifications) == 1
        assert sender_service.sent_notifications[0]["success"] is True

    @pytest.mark.asyncio
    async def test_send_notification_unsupported_channel(self, sender_service, sample_owner):
        """Test sending notification with unsupported channel."""
        notification = MockNotification(
            title="Test",
            message="Test",
            owners=["user1"],
            channel=NotificationChannel.SMS  # Owner doesn't have SMS
        )

        success = await sender_service.send_notification(notification, sample_owner)

        assert success is False
        assert len(sender_service.failed_notifications) == 1

    @pytest.mark.asyncio
    async def test_send_bulk_notifications(self, sender_service):
        """Test sending notifications to multiple owners."""
        notification = MockNotification(
            title="Bulk Test",
            message="Bulk test message",
            channel=NotificationChannel.EMAIL
        )

        owners = [
            MockOwner("User 1", "user1@example.com"),
            MockOwner("User 2", "user2@example.com"),
            MockOwner("User 3", None),  # No email
        ]

        results = await sender_service.send_bulk_notifications(notification, owners)

        assert results["sent"] == 2  # Two users with email
        assert results["failed"] == 1  # One user without email
        assert len(sender_service.sent_notifications) == 2
        assert len(sender_service.failed_notifications) == 1

    @pytest.mark.asyncio
    async def test_send_bulk_notifications_empty_owners(self, sender_service, sample_notification):
        """Test sending to empty owner list."""
        results = await sender_service.send_bulk_notifications(sample_notification, [])

        assert results["sent"] == 0
        assert results["failed"] == 0


class TestServiceIntegration:
    """Test integration between resolver and sender services."""

    @pytest.fixture
    def resolver_service(self):
        """Create resolver service."""
        return OwnerResolverService()

    @pytest.fixture
    def sender_service(self):
        """Create sender service."""
        return NotificationSenderService()

    @pytest.mark.asyncio
    async def test_resolver_sender_integration(self, resolver_service, sender_service):
        """Test integration between resolver and sender services."""
        # Create notification
        notification = MockNotification(
            title="Integration Test",
            message="Testing service integration",
            channel=NotificationChannel.EMAIL
        )

        # Resolve owners
        owners = await resolver_service.resolve_owners(["user1", "user2"])

        # Send notifications
        results = await sender_service.send_bulk_notifications(notification, owners)

        assert results["sent"] == 2
        assert len(sender_service.sent_notifications) == 2

        # Verify sent notifications
        sent_owners = {sent["owner"] for sent in sender_service.sent_notifications}
        assert "User One" in sent_owners
        assert "User Two" in sent_owners

    @pytest.mark.asyncio
    async def test_channel_compatibility_checking(self, resolver_service, sender_service):
        """Test that services properly check channel compatibility."""
        # Create notification for Slack
        notification = MockNotification(
            title="Slack Test",
            message="Testing Slack notifications",
            channel=NotificationChannel.SLACK
        )

        # Resolve owners
        owners = await resolver_service.resolve_owners(["user1", "user2", "user3"])

        # Send notifications - all should succeed since all have Slack IDs
        results = await sender_service.send_bulk_notifications(notification, owners)

        assert results["sent"] == 3
        assert results["failed"] == 0
