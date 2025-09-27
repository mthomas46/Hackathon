"""Unit tests for memory-agent domain entities."""

import pytest
from datetime import datetime, timezone, timedelta

from services.memory_agent.domain.entities import MemoryItem, MemorySession, MemoryType


class TestMemoryItem:
    """Test cases for MemoryItem entity."""

    def test_memory_item_creation(self):
        """Test basic MemoryItem creation."""
        item = MemoryItem(
            id="mem-123",
            user_id="user-456",
            memory_type=MemoryType.CONVERSATION,
            content="This is a test memory item"
        )

        assert item.id == "mem-123"
        assert item.user_id == "user-456"
        assert item.memory_type == MemoryType.CONVERSATION
        assert item.content == "This is a test memory item"
        assert item.access_count == 0

    def test_memory_item_access_tracking(self):
        """Test memory item access tracking."""
        item = MemoryItem(
            id="access-test",
            user_id="user-123",
            memory_type=MemoryType.CONVERSATION,
            content="Test content"
        )

        assert item.access_count == 0

        item.record_access()
        assert item.access_count == 1
        assert item.last_accessed_at is not None

    def test_memory_item_expiration(self):
        """Test memory item expiration logic."""
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_item = MemoryItem(
            id="expired",
            user_id="user-123",
            memory_type=MemoryType.CONVERSATION,
            content="Expired memory",
            expires_at=expired_time
        )
        assert expired_item.is_expired()

    def test_memory_item_serialization(self):
        """Test memory item serialization."""
        item = MemoryItem(
            id="serialize-test",
            user_id="user-456",
            memory_type=MemoryType.CONTEXT,
            content="Serialization test content"
        )

        data = item.to_dict()
        assert data["id"] == "serialize-test"
        assert data["content"] == "Serialization test content"


class TestMemorySession:
    """Test cases for MemorySession entity."""

    def test_memory_session_creation(self):
        """Test basic MemorySession creation."""
        session = MemorySession(
            id="session-123",
            user_id="user-456",
            context="Weather conversation"
        )

        assert session.id == "session-123"
        assert session.user_id == "user-456"
        assert session.context == "Weather conversation"
        assert session.is_active is True

    def test_memory_session_item_management(self):
        """Test memory session item management."""
        session = MemorySession(
            id="item-mgmt",
            user_id="user-123",
            context="Item management test"
        )

        session.add_memory_item("mem-1")
        session.add_memory_item("mem-2")

        assert len(session.memory_items) == 2
        assert "mem-1" in session.memory_items

    def test_memory_session_state_transitions(self):
        """Test memory session state transitions."""
        session = MemorySession(
            id="state-test",
            user_id="user-123",
            context="State transition test"
        )

        assert session.is_active is True

        session.end_session()
        assert session.is_active is False
        assert session.ended_at is not None


class TestMemoryType:
    """Test cases for MemoryType enum."""

    def test_memory_type_enum_values(self):
        """Test MemoryType enum values."""
        assert MemoryType.CONVERSATION.value == "conversation"
        assert MemoryType.FACT.value == "fact"
        assert MemoryType.PREFERENCE.value == "preference"
        assert MemoryType.CONTEXT.value == "context"
        assert MemoryType.SESSION.value == "session"

    def test_memory_type_from_string(self):
        """Test creating MemoryType from string."""
        assert MemoryType("conversation") == MemoryType.CONVERSATION
        assert MemoryType("fact") == MemoryType.FACT