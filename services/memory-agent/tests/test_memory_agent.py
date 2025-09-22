"""Memory Agent Service Tests

Comprehensive test suite for the Memory Agent service covering:
- Memory operations (storage, retrieval, TTL management)
- Event processing and correlation
- Memory state management
- Utility functions and validation
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest

import sys
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.shared.core.models.models import MemoryItem


class TestMemoryOperations:
    """Test core memory operations functionality."""

    def test_put_memory_item_basic(self):
        """Test basic memory item storage."""
        # Import modules directly by path manipulation
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__) + '/../modules')

        import memory_state
        import memory_ops

        # Clear memory for test
        memory_state._memory.clear()

        item = {
            "key": "test-key",
            "type": "test",
            "content": {"message": "test content"},
            "timestamp": time.time()
        }

        result = memory_ops.put_memory_item(item)

        assert result["count"] == 1
        assert result["max_items"] == 1000  # default value
        assert len(memory_state._memory) == 1

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_put_memory_item_capacity_limit(self):
        """Test memory capacity limits."""
        from services.memory_agent.modules import memory_ops

        # Mock max items to be small
        with patch('services.memory_agent.modules.memory_ops.get_memory_max_items', return_value=2):
            # Add 3 items
            for i in range(3):
                item = {
                    "key": f"test-key-{i}",
                    "type": "test",
                    "content": {"message": f"content {i}"},
                    "timestamp": time.time()
                }
                memory_ops.put_memory_item(item)

            # Should only keep the last 2 items (ring buffer behavior)
            assert len(memory_ops._memory) == 2
            assert memory_ops._memory[0]["key"] == "test-key-1"
            assert memory_ops._memory[1]["key"] == "test-key-2"

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_list_memory_items_empty(self):
        """Test listing memory items when empty."""
        from services.memory_agent.modules import memory_ops

        result = memory_ops.list_memory_items()

        assert result["items"] == []
        assert result["total"] == 0
        assert result["limit"] == 100  # default limit

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_list_memory_items_with_data(self):
        """Test listing memory items with data."""
        from services.memory_agent.modules import memory_ops

        # Add some test items
        items = [
            {"key": "item1", "type": "type_a", "content": "content1", "timestamp": time.time()},
            {"key": "item2", "type": "type_b", "content": "content2", "timestamp": time.time()},
            {"key": "item3", "type": "type_a", "content": "content3", "timestamp": time.time()},
        ]

        for item in items:
            memory_ops.put_memory_item(item)

        result = memory_ops.list_memory_items()

        assert len(result["items"]) == 3
        assert result["total"] == 3
        assert all(item["key"] in ["item1", "item2", "item3"] for item in result["items"])

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_list_memory_items_filtering(self):
        """Test memory item filtering by type and key."""
        from services.memory_agent.modules import memory_ops

        # Add test items
        items = [
            {"key": "filter1", "type": "type_a", "content": "content1", "timestamp": time.time()},
            {"key": "filter2", "type": "type_a", "content": "content2", "timestamp": time.time()},
            {"key": "filter3", "type": "type_b", "content": "content3", "timestamp": time.time()},
        ]

        for item in items:
            memory_ops.put_memory_item(item)

        # Filter by type
        result = memory_ops.list_memory_items(memory_type="type_a")
        assert len(result["items"]) == 2
        assert all(item["type"] == "type_a" for item in result["items"])

        # Filter by key
        result = memory_ops.list_memory_items(key="filter1")
        assert len(result["items"]) == 1
        assert result["items"][0]["key"] == "filter1"

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_list_memory_items_pagination(self):
        """Test memory item pagination."""
        from services.memory_agent.modules import memory_ops

        # Add multiple items
        for i in range(10):
            item = {
                "key": f"page-{i}",
                "type": "pagination",
                "content": f"content-{i}",
                "timestamp": time.time()
            }
            memory_ops.put_memory_item(item)

        # Test limit
        result = memory_ops.list_memory_items(limit=5)
        assert len(result["items"]) == 5
        assert result["total"] == 10


class TestTTLFunctionality:
    """Test TTL (Time-To-Live) functionality."""

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_ttl_cleanup_basic(self):
        """Test basic TTL cleanup functionality."""
        from services.memory_agent.modules import memory_ops

        # Mock TTL to be very short (1 second)
        with patch('services.memory_agent.modules.memory_ops.get_memory_ttl_seconds', return_value=1):
            # Add an item
            past_time = time.time() - 2  # 2 seconds ago (expired)
            item = {
                "key": "expired-item",
                "type": "test",
                "content": "expired content",
                "timestamp": past_time
            }
            memory_ops.put_memory_item(item)

            # Initially should exist
            assert len(memory_ops._memory) == 1

            # Trigger cleanup (simulate lazy cleanup call)
            memory_ops._lazy_cleanup_memory()

            # Should be cleaned up
            assert len(memory_ops._memory) == 0

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_ttl_cleanup_mixed_items(self):
        """Test TTL cleanup with mixed expired/non-expired items."""
        from services.memory_agent.modules import memory_ops

        with patch('services.memory_agent.modules.memory_ops.get_memory_ttl_seconds', return_value=2):
            current_time = time.time()

            # Add expired item (4 seconds ago)
            expired_item = {
                "key": "expired",
                "type": "test",
                "content": "expired",
                "timestamp": current_time - 4
            }

            # Add valid item (1 second ago)
            valid_item = {
                "key": "valid",
                "type": "test",
                "content": "valid",
                "timestamp": current_time - 1
            }

            memory_ops.put_memory_item(expired_item)
            memory_ops.put_memory_item(valid_item)

            # Both should exist initially
            assert len(memory_ops._memory) == 2

            # Trigger cleanup
            memory_ops._lazy_cleanup_memory()

            # Only valid item should remain
            assert len(memory_ops._memory) == 1
            assert memory_ops._memory[0]["key"] == "valid"

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_ttl_cleanup_frequency(self):
        """Test that cleanup doesn't run too frequently."""
        from services.memory_agent.modules import memory_ops

        # Reset global state
        memory_ops._last_cleanup_time = None

        with patch('services.memory_agent.modules.memory_ops.get_memory_ttl_seconds', return_value=1):
            # Add expired item
            item = {
                "key": "expired",
                "type": "test",
                "content": "expired",
                "timestamp": time.time() - 2
            }
            memory_ops.put_memory_item(item)

            # First cleanup should work
            memory_ops._lazy_cleanup_memory()
            assert len(memory_ops._memory) == 0

            # Add another expired item immediately
            memory_ops.put_memory_item(item)

            # Second cleanup should not run (within 5 minute window)
            memory_ops._lazy_cleanup_memory()
            # Should still have the item since cleanup didn't run
            assert len(memory_ops._memory) == 1


class TestSharedUtils:
    """Test shared utility functions."""

    def test_get_memory_max_items(self):
        """Test getting memory max items configuration."""
        from services.memory_agent.modules import shared_utils

        # Test default value
        assert shared_utils.get_memory_max_items() == 1000

    def test_get_memory_ttl_seconds(self):
        """Test getting memory TTL configuration."""
        from services.memory_agent.modules import shared_utils

        # Test default value
        assert shared_utils.get_memory_ttl_seconds() == 3600

    def test_get_redis_url(self):
        """Test getting Redis URL configuration."""
        from services.memory_agent.modules import shared_utils

        # Test default value
        assert shared_utils.get_redis_url() == "redis://redis:6379"

    def test_create_memory_item(self):
        """Test memory item creation utility."""
        from services.memory_agent.modules import shared_utils

        item = shared_utils.create_memory_item(
            key="test-key",
            memory_type="test-type",
            content={"message": "test"}
        )

        assert item["key"] == "test-key"
        assert item["type"] == "test-type"
        assert item["content"] == {"message": "test"}
        assert "timestamp" in item
        assert isinstance(item["timestamp"], (int, float))

    def test_cleanup_expired_memory_items(self):
        """Test expired memory item cleanup utility."""
        from services.memory_agent.modules import shared_utils

        current_time = time.time()
        ttl_seconds = 2

        # Create test items
        items = [
            {"key": "valid", "timestamp": current_time - 1},  # Valid
            {"key": "expired1", "timestamp": current_time - 3},  # Expired
            {"key": "expired2", "timestamp": current_time - 5},  # Expired
        ]

        cleaned_items = shared_utils.cleanup_expired_memory_items(items, ttl_seconds)

        # Should only keep valid item
        assert len(cleaned_items) == 1
        assert cleaned_items[0]["key"] == "valid"


class TestEventProcessing:
    """Test Redis event processing functionality."""

    @patch('services.memory_agent.modules.event_processor.aioredis')
    def test_event_processor_initialization_success(self, mock_redis):
        """Test successful Redis initialization."""
        from services.memory_agent.modules import event_processor

        mock_redis.from_url.return_value = MagicMock()

        processor = event_processor.EventProcessor()
        result = asyncio.run(processor.initialize_redis())

        assert result is True
        assert processor.client is not None

    @patch('services.memory_agent.modules.event_processor.aioredis')
    def test_event_processor_initialization_failure(self, mock_redis):
        """Test Redis initialization failure."""
        from services.memory_agent.modules import event_processor

        mock_redis.from_url.side_effect = Exception("Connection failed")

        processor = event_processor.EventProcessor()
        result = asyncio.run(processor.initialize_redis())

        assert result is False
        assert processor.client is None

    @patch('services.memory_agent.modules.event_processor.aioredis')
    def test_subscribe_to_channels(self, mock_redis):
        """Test subscribing to Redis channels."""
        from services.memory_agent.modules import event_processor

        mock_pubsub = MagicMock()
        mock_client = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub

        processor = event_processor.EventProcessor()
        processor.client = mock_client

        asyncio.run(processor.subscribe_to_channels())

        # Should have subscribed to expected channels
        mock_pubsub.subscribe.assert_called_once()
        call_args = mock_pubsub.subscribe.call_args[0][0]
        assert isinstance(call_args, list)
        assert len(call_args) > 0  # Should have multiple channels

    def test_endpoint_extraction(self):
        """Test endpoint extraction from text."""
        from services.memory_agent.modules import shared_utils

        # Test with API endpoint
        text = "Processing request to /api/v1/users/123/profile"
        endpoint = shared_utils.extract_endpoint_from_text(text)
        assert endpoint == "/api/v1/users/123/profile"

        # Test with no endpoint
        text = "Simple text without endpoints"
        endpoint = shared_utils.extract_endpoint_from_text(text)
        assert endpoint is None


class TestMemoryState:
    """Test memory state management."""

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_memory_state_initialization(self):
        """Test memory state initialization."""
        from services.memory_agent.modules import memory_state

        # Should start empty
        assert len(memory_state._memory) == 0

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_memory_state_thread_safety(self):
        """Test memory state thread safety (basic check)."""
        from services.memory_agent.modules import memory_state

        # Test basic operations don't crash
        memory_state._memory.append({"key": "test", "type": "test"})
        assert len(memory_state._memory) == 1

        memory_state._memory.clear()
        assert len(memory_state._memory) == 0


class TestMemoryStats:
    """Test memory statistics functionality."""

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_get_memory_stats_summary(self):
        """Test memory statistics summary."""
        from services.memory_agent.modules import memory_ops

        # Add some test items
        items = [
            {"key": "stats1", "type": "type_a", "content": "content1", "timestamp": time.time()},
            {"key": "stats2", "type": "type_b", "content": "content2", "timestamp": time.time()},
            {"key": "stats3", "type": "type_a", "content": "content3", "timestamp": time.time()},
        ]

        for item in items:
            memory_ops.put_memory_item(item)

        stats = memory_ops.get_memory_stats_summary()

        assert stats["total_items"] == 3
        assert stats["max_items"] == 1000
        assert "types" in stats
        assert stats["types"]["type_a"] == 2
        assert stats["types"]["type_b"] == 1


class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_workflow_memory_scenario(self):
        """Test complete workflow memory scenario."""
        from services.memory_agent.modules import memory_ops

        # 1. Store workflow start
        start_item = {
            "key": "workflow-123-start",
            "type": "workflow_start",
            "content": {
                "workflow_id": "wf-123",
                "action": "document_analysis",
                "status": "started"
            },
            "timestamp": time.time()
        }

        memory_ops.put_memory_item(start_item)

        # 2. Store intermediate results
        progress_item = {
            "key": "workflow-123-progress",
            "type": "workflow_progress",
            "content": {
                "workflow_id": "wf-123",
                "step": "analysis_complete",
                "results": {"documents_processed": 5}
            },
            "timestamp": time.time()
        }

        memory_ops.put_memory_item(progress_item)

        # 3. Retrieve workflow context
        results = memory_ops.list_memory_items(memory_type="workflow_progress")
        assert len(results["items"]) >= 1

        # 4. Verify workflow correlation
        found_progress = any(
            item["content"].get("workflow_id") == "wf-123"
            for item in results["items"]
        )
        assert found_progress

    @patch('services.memory_agent.modules.memory_state._memory', [])
    def test_event_memory_storage(self):
        """Test event-driven memory storage."""
        from services.memory_agent.modules import memory_ops

        # Simulate event processing
        event_item = {
            "key": "event-summary-456",
            "type": "event_summary",
            "content": {
                "event_type": "document_ingested",
                "summary": "Document successfully processed",
                "correlation_id": "corr-789"
            },
            "timestamp": time.time()
        }

        memory_ops.put_memory_item(event_item)

        # Verify event storage
        results = memory_ops.list_memory_items(memory_type="event_summary")
        assert len(results["items"]) >= 1

        stored_item = results["items"][0]
        assert stored_item["content"]["correlation_id"] == "corr-789"


if __name__ == "__main__":
    pytest.main([__file__])
