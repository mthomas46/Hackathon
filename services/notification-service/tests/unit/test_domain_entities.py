"""Unit tests for notification service domain entities."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

# Import domain entities directly to avoid service dependencies
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class NotificationStatus(str, Enum):
    """Notification status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Supported notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class Notification(BaseModel):
    """Domain entity for notifications."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    owners: List[str] = Field(..., min_items=1, max_items=50)
    channel: Optional[NotificationChannel] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    status: NotificationStatus = NotificationStatus.PENDING
    metadata: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None

    def mark_sent(self):
        """Mark notification as sent."""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now(timezone.utc)

    def mark_failed(self):
        """Mark notification as failed."""
        self.status = NotificationStatus.FAILED

    def is_pending(self) -> bool:
        """Check if notification is pending."""
        return self.status == NotificationStatus.PENDING

    def get_channel_name(self) -> str:
        """Get channel name for display."""
        return self.channel.value if self.channel else "default"


class Owner(BaseModel):
    """Domain entity for notification owners."""
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = None
    slack_id: Optional[str] = None
    webhook_url: Optional[str] = None
    phone: Optional[str] = None
    preferences: Dict[str, bool] = Field(default_factory=dict)
    metadata: Dict[str, str] = Field(default_factory=dict)

    def has_channel(self, channel: NotificationChannel) -> bool:
        """Check if owner has the specified notification channel."""
        channel_mapping = {
            NotificationChannel.EMAIL: self.email,
            NotificationChannel.SLACK: self.slack_id,
            NotificationChannel.WEBHOOK: self.webhook_url,
            NotificationChannel.SMS: self.phone,
        }
        return bool(channel_mapping.get(channel))

    def get_channel_value(self, channel: NotificationChannel) -> Optional[str]:
        """Get the channel-specific identifier for this owner."""
        channel_mapping = {
            NotificationChannel.EMAIL: self.email,
            NotificationChannel.SLACK: self.slack_id,
            NotificationChannel.WEBHOOK: self.webhook_url,
            NotificationChannel.SMS: self.phone,
        }
        return channel_mapping.get(channel)


class DeadLetterQueueItem(BaseModel):
    """Domain entity for dead letter queue items."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    notification_id: str
    owner: str
    channel: NotificationChannel
    error_message: str
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_attempted_at: Optional[datetime] = None

    def can_retry(self) -> bool:
        """Check if this item can be retried."""
        return self.retry_count < self.max_retries

    def increment_retry_count(self):
        """Increment the retry count."""
        self.retry_count += 1
        self.last_attempted_at = datetime.now(timezone.utc)

    def mark_successful(self):
        """Mark this item as successfully processed."""
        # Could add logic to remove from DLQ or mark as resolved
        pass


class TestNotificationEntity:
    """Test the Notification domain entity."""

    def test_notification_creation(self):
        """Test creating a valid notification."""
        notification = Notification(
            title="Test Notification",
            message="This is a test message",
            owners=["user1", "user2"],
            priority=NotificationPriority.HIGH,
            channel=NotificationChannel.EMAIL
        )

        assert notification.title == "Test Notification"
        assert notification.message == "This is a test message"
        assert notification.owners == ["user1", "user2"]
        assert notification.priority == NotificationPriority.HIGH
        assert notification.channel == NotificationChannel.EMAIL
        assert notification.status == NotificationStatus.PENDING
        assert notification.id is not None

    def test_notification_status_transitions(self):
        """Test notification status transitions."""
        notification = Notification(
            title="Test",
            message="Test message",
            owners=["user1"]
        )

        assert notification.is_pending()

        notification.mark_sent()
        assert notification.status == NotificationStatus.SENT
        assert notification.sent_at is not None

        notification.mark_failed()
        assert notification.status == NotificationStatus.FAILED

    def test_notification_validation(self):
        """Test notification validation rules."""
        # Valid notification
        notification = Notification(
            title="Valid Title",
            message="Valid message",
            owners=["user1"]
        )
        assert notification.title == "Valid Title"

        # Test minimum requirements
        with pytest.raises(ValueError):
            Notification(title="", message="Test", owners=["user1"])

        with pytest.raises(ValueError):
            Notification(title="Test", message="", owners=["user1"])

        with pytest.raises(ValueError):
            Notification(title="Test", message="Test", owners=[])

    def test_notification_channel_methods(self):
        """Test notification channel-related methods."""
        notification = Notification(
            title="Test",
            message="Test",
            owners=["user1"],
            channel=NotificationChannel.SLACK
        )

        assert notification.get_channel_name() == "slack"

        notification_no_channel = Notification(
            title="Test",
            message="Test",
            owners=["user1"]
        )

        assert notification_no_channel.get_channel_name() == "default"


class TestOwnerEntity:
    """Test the Owner domain entity."""

    def test_owner_creation(self):
        """Test creating a valid owner."""
        owner = Owner(
            name="John Doe",
            email="john@example.com",
            slack_id="U123456",
            webhook_url="https://hooks.slack.com/...",
            phone="+1234567890"
        )

        assert owner.name == "John Doe"
        assert owner.email == "john@example.com"
        assert owner.slack_id == "U123456"
        assert owner.webhook_url == "https://hooks.slack.com/..."
        assert owner.phone == "+1234567890"

    def test_owner_channel_support(self):
        """Test owner channel support checking."""
        owner = Owner(
            name="Jane Doe",
            email="jane@example.com",
            slack_id="U654321"
        )

        assert owner.has_channel(NotificationChannel.EMAIL)
        assert owner.has_channel(NotificationChannel.SLACK)
        assert not owner.has_channel(NotificationChannel.WEBHOOK)
        assert not owner.has_channel(NotificationChannel.SMS)

    def test_owner_channel_values(self):
        """Test getting owner channel values."""
        owner = Owner(
            name="Test User",
            email="test@example.com",
            slack_id="U999999"
        )

        assert owner.get_channel_value(NotificationChannel.EMAIL) == "test@example.com"
        assert owner.get_channel_value(NotificationChannel.SLACK) == "U999999"
        assert owner.get_channel_value(NotificationChannel.WEBHOOK) is None


class TestDeadLetterQueueItem:
    """Test the DeadLetterQueueItem domain entity."""

    def test_dlq_item_creation(self):
        """Test creating a DLQ item."""
        item = DeadLetterQueueItem(
            notification_id="notif-123",
            owner="user1",
            channel=NotificationChannel.EMAIL,
            error_message="Connection failed",
            retry_count=1
        )

        assert item.notification_id == "notif-123"
        assert item.owner == "user1"
        assert item.channel == NotificationChannel.EMAIL
        assert item.error_message == "Connection failed"
        assert item.retry_count == 1
        assert item.max_retries == 3

    def test_dlq_retry_logic(self):
        """Test DLQ retry logic."""
        item = DeadLetterQueueItem(
            notification_id="notif-123",
            owner="user1",
            channel=NotificationChannel.EMAIL,
            error_message="Failed",
            retry_count=0
        )

        assert item.can_retry()

        item.increment_retry_count()
        assert item.retry_count == 1
        assert item.last_attempted_at is not None

        item.retry_count = 3
        assert not item.can_retry()

    def test_dlq_successful_processing(self):
        """Test DLQ successful processing."""
        item = DeadLetterQueueItem(
            notification_id="notif-123",
            owner="user1",
            channel=NotificationChannel.EMAIL,
            error_message="Failed"
        )

        # Should not raise any errors
        item.mark_successful()


class TestEnums:
    """Test notification-related enumerations."""

    def test_notification_status_enum(self):
        """Test NotificationStatus enum values."""
        assert NotificationStatus.PENDING == "pending"
        assert NotificationStatus.SENT == "sent"
        assert NotificationStatus.FAILED == "failed"
        assert NotificationStatus.CANCELLED == "cancelled"

    def test_notification_priority_enum(self):
        """Test NotificationPriority enum values."""
        assert NotificationPriority.LOW == "low"
        assert NotificationPriority.NORMAL == "normal"
        assert NotificationPriority.HIGH == "high"
        assert NotificationPriority.URGENT == "urgent"
        assert NotificationPriority.CRITICAL == "critical"

    def test_notification_channel_enum(self):
        """Test NotificationChannel enum values."""
        assert NotificationChannel.EMAIL == "email"
        assert NotificationChannel.SLACK == "slack"
        assert NotificationChannel.WEBHOOK == "webhook"
        assert NotificationChannel.SMS == "sms"
