"""Unit tests for memory-agent domain services."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone, timedelta

from services.memory_agent.domain.services.memory_service import MemoryService
from services.memory_agent.domain.entities.memory_item import MemoryItem, MemoryType
from services.memory_agent.domain.repositories.memory_repository import MemoryRepository


class TestMemoryService:
    """Test cases for MemoryService domain service."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return Mock(spec=MemoryRepository)

    @pytest.fixture
    def memory_service(self, mock_repository):
        """Create memory service instance."""
        return MemoryService(mock_repository)

    @pytest.fixture
    def sample_memory_item(self):
        """Create a sample memory item for testing."""
        return MemoryItem(
            id="mem-123",
            user_id="user-456",
            memory_type=MemoryType.CONVERSATION,
            content="Sample memory content",
            metadata={"source": "test", "importance": "high"}
        )

    @pytest.mark.asyncio
    async def test_store_memory_item_success(self, memory_service, mock_repository, sample_memory_item):
        """Test successful memory item storage."""
        mock_repository.save.return_value = sample_memory_item

        result = await memory_service.store_memory_item(sample_memory_item)

        assert result == sample_memory_item
        mock_repository.save.assert_called_once_with(sample_memory_item)

    @pytest.mark.asyncio
    async def test_retrieve_memory_item_success(self, memory_service, mock_repository, sample_memory_item):
        """Test successful memory item retrieval."""
        mock_repository.find_by_id.return_value = sample_memory_item

        result = await memory_service.retrieve_memory_item("mem-123")

        assert result == sample_memory_item
        mock_repository.find_by_id.assert_called_once_with("mem-123")

    @pytest.mark.asyncio
    async def test_retrieve_memory_item_not_found(self, memory_service, mock_repository):
        """Test memory item retrieval when not found."""
        mock_repository.find_by_id.return_value = None

        result = await memory_service.retrieve_memory_item("non-existent")

        assert result is None
        mock_repository.find_by_id.assert_called_once_with("non-existent")

    @pytest.mark.asyncio
    async def test_update_memory_item_success(self, memory_service, mock_repository, sample_memory_item):
        """Test successful memory item update."""
        updated_content = "Updated memory content"
        mock_repository.find_by_id.return_value = sample_memory_item
        mock_repository.update.return_value = None

        result = await memory_service.update_memory_item("mem-123", content=updated_content)

        assert result is True
        assert sample_memory_item.content == updated_content
        mock_repository.find_by_id.assert_called_once_with("mem-123")
        mock_repository.update.assert_called_once_with(sample_memory_item)

    @pytest.mark.asyncio
    async def test_update_memory_item_not_found(self, memory_service, mock_repository):
        """Test memory item update when not found."""
        mock_repository.find_by_id.return_value = None

        with pytest.raises(ValueError, match="Memory item mem-123 not found"):
            await memory_service.update_memory_item("mem-123", content="new content")

        mock_repository.find_by_id.assert_called_once_with("mem-123")
        mock_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_memory_item_success(self, memory_service, mock_repository, sample_memory_item):
        """Test successful memory item deletion."""
        mock_repository.find_by_id.return_value = sample_memory_item
        mock_repository.delete.return_value = True

        result = await memory_service.delete_memory_item("mem-123")

        assert result is True
        mock_repository.find_by_id.assert_called_once_with("mem-123")
        mock_repository.delete.assert_called_once_with("mem-123")

    @pytest.mark.asyncio
    async def test_delete_memory_item_not_found(self, memory_service, mock_repository):
        """Test memory item deletion when not found."""
        mock_repository.find_by_id.return_value = None

        with pytest.raises(ValueError, match="Memory item mem-123 not found"):
            await memory_service.delete_memory_item("mem-123")

        mock_repository.find_by_id.assert_called_once_with("mem-123")
        mock_repository.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_memory_items_by_user(self, memory_service, mock_repository, sample_memory_item):
        """Test finding memory items by user."""
        memory_items = [sample_memory_item]
        mock_repository.find_by_user_id.return_value = memory_items

        result = await memory_service.find_memory_items_by_user("user-456")

        assert result == memory_items
        mock_repository.find_by_user_id.assert_called_once_with("user-456")

    @pytest.mark.asyncio
    async def test_find_memory_items_by_type(self, memory_service, mock_repository, sample_memory_item):
        """Test finding memory items by type."""
        memory_items = [sample_memory_item]
        mock_repository.find_by_type.return_value = memory_items

        result = await memory_service.find_memory_items_by_type(MemoryType.CONVERSATION)

        assert result == memory_items
        mock_repository.find_by_type.assert_called_once_with(MemoryType.CONVERSATION)

    @pytest.mark.asyncio
    async def test_search_memory_items(self, memory_service, mock_repository, sample_memory_item):
        """Test searching memory items."""
        memory_items = [sample_memory_item]
        mock_repository.search.return_value = memory_items

        result = await memory_service.search_memory_items("test query")

        assert result == memory_items
        mock_repository.search.assert_called_once_with("test query", 50)

    @pytest.mark.asyncio
    async def test_get_memory_statistics(self, memory_service, mock_repository):
        """Test getting memory statistics."""
        stats = {
            "total_items": 100,
            "active_sessions": 5,
            "memory_types": {"conversation": 60, "fact": 40},
            "avg_access_count": 2.5
        }
        mock_repository.get_statistics.return_value = stats

        result = await memory_service.get_memory_statistics()

        assert result == stats
        mock_repository.get_statistics.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_expired_memory_items(self, memory_service, mock_repository):
        """Test cleanup of expired memory items."""
        expired_ids = ["expired-1", "expired-2"]
        mock_repository.find_expired.return_value = expired_ids
        mock_repository.bulk_delete.return_value = 2

        result = await memory_service.cleanup_expired_memory_items()

        assert result == 2
        mock_repository.find_expired.assert_called_once()
        mock_repository.bulk_delete.assert_called_once_with(expired_ids)

    @pytest.mark.asyncio
    async def test_get_recent_memory_items(self, memory_service, mock_repository, sample_memory_item):
        """Test getting recent memory items."""
        recent_items = [sample_memory_item]
        mock_repository.find_recent.return_value = recent_items

        result = await memory_service.get_recent_memory_items("user-456", limit=10)

        assert result == recent_items
        mock_repository.find_recent.assert_called_once_with("user-456", 10)

    def test_validate_memory_item_valid(self, memory_service, sample_memory_item):
        """Test memory item validation with valid data."""
        # Should not raise any exceptions
        memory_service.validate_memory_item(sample_memory_item)

    def test_validate_memory_item_invalid_id(self, memory_service):
        """Test memory item validation with invalid ID."""
        invalid_item = MemoryItem(
            id="",  # Invalid: empty ID
            user_id="user-123",
            memory_type=MemoryType.CONVERSATION,
            content="Test content"
        )

        with pytest.raises(ValueError, match="Memory item ID cannot be empty"):
            memory_service.validate_memory_item(invalid_item)

    def test_validate_memory_item_invalid_content(self, memory_service):
        """Test memory item validation with invalid content."""
        invalid_item = MemoryItem(
            id="mem-123",
            user_id="user-123",
            memory_type=MemoryType.CONVERSATION,
            content=""  # Invalid: empty content
        )

        with pytest.raises(ValueError, match="Memory item content cannot be empty"):
            memory_service.validate_memory_item(invalid_item)

    def test_validate_memory_item_expired(self, memory_service):
        """Test memory item validation with expired item."""
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_item = MemoryItem(
            id="mem-123",
            user_id="user-123",
            memory_type=MemoryType.CONVERSATION,
            content="Test content",
            expires_at=expired_time
        )

        with pytest.raises(ValueError, match="Memory item is already expired"):
            memory_service.validate_memory_item(expired_item)

    @pytest.mark.asyncio
    async def test_bulk_store_memory_items(self, memory_service, mock_repository, sample_memory_item):
        """Test bulk storage of memory items."""
        items = [sample_memory_item]
        mock_repository.bulk_save.return_value = items

        result = await memory_service.bulk_store_memory_items(items)

        assert result == items
        mock_repository.bulk_save.assert_called_once_with(items)

    @pytest.mark.asyncio
    async def test_bulk_delete_memory_items(self, memory_service, mock_repository):
        """Test bulk deletion of memory items."""
        item_ids = ["mem-1", "mem-2", "mem-3"]
        mock_repository.bulk_delete.return_value = 3

        result = await memory_service.bulk_delete_memory_items(item_ids)

        assert result == 3
        mock_repository.bulk_delete.assert_called_once_with(item_ids)
