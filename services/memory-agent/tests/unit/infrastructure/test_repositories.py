"""Unit tests for memory-agent infrastructure repositories."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone

from services.memory_agent.infrastructure.repositories import MemoryRepository


class TestMemoryRepository:
    """Test cases for MemoryRepository."""

    @pytest.fixture
    def repository(self):
        """Create MemoryRepository instance for testing."""
        return MemoryRepository()

    @pytest.mark.asyncio
    async def test_save_and_retrieve_memory_item(self, repository):
        """Test saving and retrieving a memory item."""
        from services.memory_agent.domain.entities import MemoryItem, MemoryType

        item = MemoryItem(
            id="mem-123",
            user_id="user-456",
            memory_type=MemoryType.CONVERSATION,
            content="Test memory content"
        )

        # Save item
        await repository.save_memory_item(item)

        # Retrieve by ID
        retrieved = await repository.get_memory_item_by_id(item.id)
        assert retrieved is not None
        assert retrieved.id == item.id
        assert retrieved.content == "Test memory content"

    @pytest.mark.asyncio
    async def test_find_memory_items_by_user(self, repository):
        """Test finding memory items by user."""
        from services.memory_agent.domain.entities import MemoryItem, MemoryType

        items = [
            MemoryItem(id="mem-1", user_id="user-123", memory_type=MemoryType.CONVERSATION, content="Content 1"),
            MemoryItem(id="mem-2", user_id="user-123", memory_type=MemoryType.FACT, content="Content 2"),
            MemoryItem(id="mem-3", user_id="user-456", memory_type=MemoryType.CONVERSATION, content="Content 3")
        ]

        for item in items:
            await repository.save_memory_item(item)

        # Find by user
        user_items = await repository.get_memory_items_by_user("user-123")
        assert len(user_items) == 2
        assert all(item.user_id == "user-123" for item in user_items)

    @pytest.mark.asyncio
    async def test_find_memory_items_by_type(self, repository):
        """Test finding memory items by type."""
        from services.memory_agent.domain.entities import MemoryItem, MemoryType

        items = [
            MemoryItem(id="conv-1", user_id="user-1", memory_type=MemoryType.CONVERSATION, content="Conv 1"),
            MemoryItem(id="conv-2", user_id="user-1", memory_type=MemoryType.CONVERSATION, content="Conv 2"),
            MemoryItem(id="fact-1", user_id="user-1", memory_type=MemoryType.FACT, content="Fact 1")
        ]

        for item in items:
            await repository.save_memory_item(item)

        # Find by type
        conv_items = await repository.get_memory_items_by_type("user-1", MemoryType.CONVERSATION)
        assert len(conv_items) == 2
        assert all(item.memory_type == MemoryType.CONVERSATION for item in conv_items)

    @pytest.mark.asyncio
    async def test_update_memory_item(self, repository):
        """Test updating an existing memory item."""
        from services.memory_agent.domain.entities import MemoryItem, MemoryType

        item = MemoryItem(
            id="update-test",
            user_id="user-123",
            memory_type=MemoryType.FACT,
            content="Original content"
        )

        await repository.save_memory_item(item)

        # Update content
        item.content = "Updated content"
        await repository.update_memory_item(item)

        # Verify update
        updated = await repository.get_memory_item_by_id(item.id)
        assert updated.content == "Updated content"

    @pytest.mark.asyncio
    async def test_delete_memory_item(self, repository):
        """Test deleting a memory item."""
        from services.memory_agent.domain.entities import MemoryItem, MemoryType

        item = MemoryItem(
            id="delete-test",
            user_id="user-123",
            memory_type=MemoryType.PREFERENCE,
            content="To be deleted"
        )

        await repository.save_memory_item(item)

        # Verify exists
        assert await repository.get_memory_item_by_id(item.id) is not None

        # Delete
        deleted = await repository.delete_memory_item(item.id)
        assert deleted is True

        # Verify no longer exists
        assert await repository.get_memory_item_by_id(item.id) is None

    @pytest.mark.asyncio
    async def test_memory_session_operations(self, repository):
        """Test memory session operations."""
        from services.memory_agent.domain.entities import MemorySession

        session = MemorySession(
            id="session-123",
            user_id="user-456",
            context="Test session"
        )

        # Save session
        await repository.save_memory_session(session)

        # Retrieve session
        retrieved = await repository.get_memory_session_by_id(session.id)
        assert retrieved is not None
        assert retrieved.id == session.id
        assert retrieved.context == "Test session"

    @pytest.mark.asyncio
    async def test_search_memory_items(self, repository):
        """Test searching memory items."""
        from services.memory_agent.domain.entities import MemoryItem, MemoryType

        items = [
            MemoryItem(id="search-1", user_id="user-1", memory_type=MemoryType.CONVERSATION, content="Weather discussion"),
            MemoryItem(id="search-2", user_id="user-1", memory_type=MemoryType.FACT, content="Paris is capital"),
            MemoryItem(id="search-3", user_id="user-1", memory_type=MemoryType.CONVERSATION, content="Sports conversation")
        ]

        for item in items:
            await repository.save_memory_item(item)

        # Search by content
        weather_results = await repository.search_memory_items("user-1", "weather")
        assert len(weather_results) >= 1

    @pytest.mark.asyncio
    async def test_recent_memory_items(self, repository):
        """Test retrieving recent memory items."""
        from services.memory_agent.domain.entities import MemoryItem, MemoryType
        from datetime import timedelta

        base_time = datetime.now(timezone.utc)
        items = []

        for i in range(5):
            item = MemoryItem(
                id=f"recent-{i}",
                user_id="user-123",
                memory_type=MemoryType.CONVERSATION,
                content=f"Recent content {i}"
            )
            # Simulate different access times
            item.last_accessed_at = base_time - timedelta(minutes=i*10)
            items.append(item)
            await repository.save_memory_item(item)

        # Get recent items
        recent_items = await repository.get_recent_memory_items("user-123", limit=3)
        assert len(recent_items) == 3

    def test_repository_initialization(self, repository):
        """Test repository initialization."""
        assert repository is not None
        assert hasattr(repository, 'save_memory_item')
        assert hasattr(repository, 'get_memory_item_by_id')
        assert hasattr(repository, 'get_memory_items_by_user')
        assert hasattr(repository, 'get_memory_items_by_type')
        assert hasattr(repository, 'update_memory_item')
        assert hasattr(repository, 'delete_memory_item')
        assert hasattr(repository, 'save_memory_session')
        assert hasattr(repository, 'get_memory_session_by_id')
        assert hasattr(repository, 'search_memory_items')
        assert hasattr(repository, 'get_recent_memory_items')

    @pytest.mark.asyncio
    async def test_bulk_operations(self, repository):
        """Test bulk operations."""
        from services.memory_agent.domain.entities import MemoryItem, MemoryType

        # Create multiple items
        items = []
        for i in range(10):
            item = MemoryItem(
                id=f"bulk-{i}",
                user_id="bulk-user",
                memory_type=MemoryType.CONVERSATION,
                content=f"Bulk content {i}"
            )
            items.append(item)

        # Save all items
        for item in items:
            await repository.save_memory_item(item)

        # Retrieve all for user
        retrieved_items = await repository.get_memory_items_by_user("bulk-user")
        assert len(retrieved_items) == 10

    @pytest.mark.asyncio
    async def test_error_handling(self, repository):
        """Test error handling in repository operations."""
        # Test finding non-existent item
        result = await repository.get_memory_item_by_id("non-existent-id")
        assert result is None

        # Test deleting non-existent item
        deleted = await repository.delete_memory_item("non-existent-id")
        assert deleted is False

        # Test searching with no matches
        results = await repository.search_memory_items("user-123", "nonexistentterm")
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repository):
        """Test concurrent repository operations."""
        import asyncio
        from services.memory_agent.domain.entities import MemoryItem, MemoryType

        async def create_and_save_item(index):
            item = MemoryItem(
                id=f"concurrent-{index}",
                user_id="concurrent-user",
                memory_type=MemoryType.CONVERSATION,
                content=f"Concurrent content {index}"
            )
            await repository.save_memory_item(item)
            return item.id

        # Create multiple concurrent operations
        tasks = [create_and_save_item(i) for i in range(5)]
        item_ids = await asyncio.gather(*tasks)

        # Verify all items were created
        assert len(item_ids) == 5
        assert len(set(item_ids)) == 5  # All IDs should be unique