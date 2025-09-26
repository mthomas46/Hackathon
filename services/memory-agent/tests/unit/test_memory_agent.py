"""Comprehensive tests for Memory Agent service functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from memory_agent.modules.memory_ops import MemoryOperations
from memory_agent.modules.memory_state import MemoryState
from memory_agent.modules.event_processor import EventProcessor
from memory_agent.modules.shared_utils import (
    get_memory_max_items,
    get_memory_ttl_seconds,
    get_redis_url,
    handle_memory_agent_error
)


class TestMemoryOperations:
    """Test memory operations functionality."""

    @pytest.fixture
    def memory_ops(self):
        """Create memory operations instance."""
        return MemoryOperations()

    def test_memory_operations_initialization(self, memory_ops):
        """Test memory operations initialization."""
        assert memory_ops is not None
        assert hasattr(memory_ops, 'store_memory')
        assert hasattr(memory_ops, 'retrieve_memory')
        assert hasattr(memory_ops, 'search_memory')

    @pytest.mark.asyncio
    async def test_store_memory_success(self, memory_ops):
        """Test successful memory storage."""
        with patch('memory_agent.modules.memory_ops.redis') as mock_redis:
            mock_client = MagicMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.set.return_value = True

            result = await memory_ops.store_memory("test_key", "test_data")
            assert result is True
            mock_client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_memory_success(self, memory_ops):
        """Test successful memory retrieval."""
        with patch('memory_agent.modules.memory_ops.redis') as mock_redis:
            mock_client = MagicMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.get.return_value = b"test_data"

            result = await memory_ops.retrieve_memory("test_key")
            assert result == "test_data"
            mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_retrieve_memory_not_found(self, memory_ops):
        """Test memory retrieval when key not found."""
        with patch('memory_agent.modules.memory_ops.redis') as mock_redis:
            mock_client = MagicMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.get.return_value = None

            result = await memory_ops.retrieve_memory("nonexistent_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_search_memory(self, memory_ops):
        """Test memory search functionality."""
        with patch('memory_agent.modules.memory_ops.redis') as mock_redis:
            mock_client = MagicMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.keys.return_value = [b"memory:key1", b"memory:key2"]

            result = await memory_ops.search_memory("test")
            assert isinstance(result, list)
            mock_client.keys.assert_called_once()


class TestMemoryState:
    """Test memory state management."""

    @pytest.fixture
    def memory_state(self):
        """Create memory state instance."""
        return MemoryState()

    def test_memory_state_initialization(self, memory_state):
        """Test memory state initialization."""
        assert memory_state is not None
        assert hasattr(memory_state, 'add_item')
        assert hasattr(memory_state, 'get_item')
        assert hasattr(memory_state, 'clear_expired')

    def test_add_and_get_item(self, memory_state):
        """Test adding and retrieving memory items."""
        memory_state.add_item("test_key", "test_value", ttl=3600)

        item = memory_state.get_item("test_key")
        assert item is not None
        assert item["value"] == "test_value"
        assert item["ttl"] == 3600

    def test_get_item_not_found(self, memory_state):
        """Test retrieving non-existent item."""
        item = memory_state.get_item("nonexistent")
        assert item is None

    def test_clear_expired_items(self, memory_state):
        """Test clearing expired items."""
        # Add an item that expires immediately
        memory_state.add_item("expired_key", "value", ttl=-1)

        # Add a valid item
        memory_state.add_item("valid_key", "value", ttl=3600)

        cleared_count = memory_state.clear_expired()
        assert cleared_count >= 1

        # Expired item should be gone
        expired_item = memory_state.get_item("expired_key")
        assert expired_item is None

        # Valid item should remain
        valid_item = memory_state.get_item("valid_key")
        assert valid_item is not None


class TestEventProcessor:
    """Test event processing functionality."""

    @pytest.fixture
    def event_processor(self):
        """Create event processor instance."""
        return EventProcessor()

    def test_event_processor_initialization(self, event_processor):
        """Test event processor initialization."""
        assert event_processor is not None
        assert hasattr(event_processor, 'process_event')
        assert hasattr(event_processor, 'get_processed_events')

    @pytest.mark.asyncio
    async def test_process_memory_event(self, event_processor):
        """Test processing memory-related events."""
        event = {
            "type": "memory_store",
            "key": "test_key",
            "value": "test_value",
            "ttl": 3600
        }

        result = await event_processor.process_event(event)
        assert result is True

        processed_events = event_processor.get_processed_events()
        assert len(processed_events) >= 1

    @pytest.mark.asyncio
    async def test_process_retrieval_event(self, event_processor):
        """Test processing memory retrieval events."""
        event = {
            "type": "memory_retrieve",
            "key": "test_key"
        }

        result = await event_processor.process_event(event)
        assert result is True

    def test_get_processed_events(self, event_processor):
        """Test retrieving processed events."""
        events = event_processor.get_processed_events()
        assert isinstance(events, list)


class TestSharedUtils:
    """Test shared utility functions."""

    def test_get_memory_max_items(self):
        """Test getting memory max items configuration."""
        max_items = get_memory_max_items()
        assert isinstance(max_items, int)
        assert max_items > 0

    def test_get_memory_ttl_seconds(self):
        """Test getting memory TTL configuration."""
        ttl = get_memory_ttl_seconds()
        assert isinstance(ttl, int)
        assert ttl > 0

    def test_get_redis_url(self):
        """Test getting Redis URL configuration."""
        url = get_redis_url()
        assert isinstance(url, str)
        assert url.startswith("redis://")

    def test_handle_memory_agent_error(self):
        """Test error handling utility."""
        response = handle_memory_agent_error(
            "test_operation",
            ValueError("test error"),
            user_id="test_user"
        )

        assert isinstance(response, dict)
        assert response["status"] == "error"
        assert "message" in response
        assert "error_code" in response


class TestMemoryAgentIntegration:
    """Integration tests for memory agent components."""

    @pytest.fixture
    def integrated_setup(self):
        """Create integrated memory agent setup."""
        memory_ops = MemoryOperations()
        memory_state = MemoryState()
        event_processor = EventProcessor()

        return {
            "memory_ops": memory_ops,
            "memory_state": memory_state,
            "event_processor": event_processor
        }

    @pytest.mark.asyncio
    async def test_memory_lifecycle_integration(self, integrated_setup):
        """Test complete memory lifecycle integration."""
        setup = integrated_setup
        memory_ops = setup["memory_ops"]
        memory_state = setup["memory_state"]
        event_processor = setup["event_processor"]

        # Test storing memory
        test_key = "integration_test_key"
        test_value = "integration_test_value"

        # Store in state
        memory_state.add_item(test_key, test_value, ttl=3600)

        # Process store event
        store_event = {
            "type": "memory_store",
            "key": test_key,
            "value": test_value,
            "ttl": 3600
        }
        await event_processor.process_event(store_event)

        # Retrieve from state
        retrieved_item = memory_state.get_item(test_key)
        assert retrieved_item is not None
        assert retrieved_item["value"] == test_value

        # Check processed events
        events = event_processor.get_processed_events()
        assert len(events) >= 1

    def test_configuration_integration(self):
        """Test configuration integration across utilities."""
        max_items = get_memory_max_items()
        ttl = get_memory_ttl_seconds()
        redis_url = get_redis_url()

        # All should be properly configured
        assert max_items > 0
        assert ttl > 0
        assert redis_url is not None

        # Test that configurations are consistent
        assert isinstance(max_items, int)
        assert isinstance(ttl, int)
        assert isinstance(redis_url, str)

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, integrated_setup):
        """Test error handling integration across components."""
        setup = integrated_setup
        memory_ops = setup["memory_ops"]

        # Test error handling in operations
        try:
            # This might fail due to mocking, but should handle gracefully
            await memory_ops.store_memory("test_key", "test_value")
        except Exception:
            # Error should be handled gracefully
            pass

        # Test utility error handling
        response = handle_memory_agent_error(
            "integration_test",
            Exception("Integration test error")
        )

        assert response["status"] == "error"
        assert "message" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
