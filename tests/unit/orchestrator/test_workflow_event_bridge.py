#!/usr/bin/env python3
"""
Unit Tests for Workflow Event Bridge

Comprehensive test suite for WorkflowEventBridge covering:
- Multi-channel event emission
- Workflow lifecycle event handling
- Event correlation and processing
- Error handling and resilience
- Integration with event store and streaming
"""

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call
import pytest
from datetime import datetime

# Add services to path for testing
import sys
from pathlib import Path
services_path = Path(__file__).parent.parent.parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from services.orchestrator.modules.workflow_event_bridge import (
    WorkflowEventBridge,
    emit_workflow_created_event,
    emit_workflow_started_event,
    emit_workflow_completed_event,
    emit_workflow_failed_event,
    emit_step_event,
    get_workflow_events,
    replay_workflow_events
)

from services.orchestrator.modules.event_driven_orchestration import (
    WorkflowEvent,
    EventType
)


class TestWorkflowEventBridge:
    """Test Workflow Event Bridge functionality."""

    @pytest.fixture
    def event_bridge(self):
        """Create event bridge for testing."""
        return WorkflowEventBridge()

    @pytest.fixture
    def mock_redis_manager(self):
        """Mock Redis manager."""
        mock_manager = AsyncMock()
        mock_manager.publish_event = AsyncMock(return_value=True)
        return mock_manager

    @pytest.fixture
    def mock_event_store(self):
        """Mock event store."""
        mock_store = AsyncMock()
        mock_store.store_event = AsyncMock(return_value=True)
        mock_store.get_aggregate_events = AsyncMock(return_value=[])
        mock_store.replay_events = AsyncMock(return_value={"current_state": "completed"})
        return mock_store

    @pytest.fixture
    def mock_event_stream_processor(self):
        """Mock event stream processor."""
        mock_processor = AsyncMock()
        mock_processor.publish_event = AsyncMock(return_value=True)
        return mock_processor

    def test_event_bridge_initialization(self, event_bridge):
        """Test event bridge initialization."""
        assert event_bridge.event_handlers_registered is False
        assert hasattr(event_bridge, '_register_event_handlers')

    @pytest.mark.asyncio
    async def test_initialize_bridge(self, event_bridge, mock_event_store):
        """Test bridge initialization."""
        with patch('services.orchestrator.modules.workflow_event_bridge.event_store', mock_event_store), \
             patch('services.orchestrator.modules.workflow_event_bridge.event_driven_engine') as mock_engine:

            mock_engine.register_event_processor = MagicMock()

            await event_bridge.initialize_bridge()

            assert event_bridge.event_handlers_registered is True

            # Verify event handler registrations
            mock_store.register_event_handler.assert_has_calls([
                call(EventType.WORKFLOW_STARTED, event_bridge._handle_workflow_started_event),
                call(EventType.WORKFLOW_COMPLETED, event_bridge._handle_workflow_completed_event),
                call(EventType.WORKFLOW_FAILED, event_bridge._handle_workflow_failed_event)
            ])

            mock_engine.register_event_processor.assert_has_calls([
                call(EventType.WORKFLOW_STARTED, event_bridge._process_workflow_started),
                call(EventType.WORKFLOW_COMPLETED, event_bridge._process_workflow_completed),
                call(EventType.WORKFLOW_FAILED, event_bridge._process_workflow_failed)
            ])

    @pytest.mark.asyncio
    async def test_emit_workflow_event_multi_channel_success(self, event_bridge, mock_redis_manager, mock_event_store):
        """Test successful multi-channel event emission."""
        with patch('services.orchestrator.modules.workflow_event_bridge.redis_manager', mock_redis_manager), \
             patch('services.orchestrator.modules.workflow_event_bridge.event_store', mock_event_store), \
             patch('services.orchestrator.modules.workflow_event_bridge.EVENT_STREAMING_AVAILABLE', False):

            success = await event_bridge.emit_workflow_event(
                "test_event",
                "workflow-123",
                {"action": "test", "data": "value"},
                "correlation-456",
                "user-789"
            )

            assert success is True

            # Verify Redis publish was called
            mock_redis_manager.publish_event.assert_called_once()
            publish_call = mock_redis_manager.publish_event.call_args
            channel, payload, correlation_id = publish_call[0]

            assert channel == "workflow.test_event"
            assert correlation_id == "correlation-456"

            # Verify event store was called
            mock_event_store.store_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_workflow_event_with_streaming(self, event_bridge, mock_redis_manager, mock_event_store, mock_event_stream_processor):
        """Test event emission with streaming enabled."""
        with patch('services.orchestrator.modules.workflow_event_bridge.redis_manager', mock_redis_manager), \
             patch('services.orchestrator.modules.workflow_event_bridge.event_store', mock_event_store), \
             patch('services.orchestrator.modules.workflow_event_bridge.EVENT_STREAMING_AVAILABLE', True), \
             patch('services.orchestrator.modules.workflow_event_bridge.event_stream_processor', mock_event_stream_processor):

            success = await event_bridge.emit_workflow_event(
                "test_event",
                "workflow-123",
                {"action": "test", "data": "value"},
                "correlation-456",
                "user-789"
            )

            assert success is True

            # Verify all three channels were used
            mock_redis_manager.publish_event.assert_called_once()
            mock_event_store.store_event.assert_called_once()
            mock_event_stream_processor.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_emit_workflow_event_partial_failure(self, event_bridge, mock_redis_manager, mock_event_store):
        """Test event emission with partial failures."""
        # Make Redis fail but event store succeed
        mock_redis_manager.publish_event.return_value = False
        mock_event_store.store_event.return_value = True

        with patch('services.orchestrator.modules.workflow_event_bridge.redis_manager', mock_redis_manager), \
             patch('services.orchestrator.modules.workflow_event_bridge.event_store', mock_event_store), \
             patch('services.orchestrator.modules.workflow_event_bridge.EVENT_STREAMING_AVAILABLE', False):

            success = await event_bridge.emit_workflow_event(
                "test_event",
                "workflow-123",
                {"action": "test"},
                "correlation-456"
            )

            # Should still be successful since event store worked
            assert success is True

    @pytest.mark.asyncio
    async def test_emit_workflow_event_complete_failure(self, event_bridge, mock_redis_manager, mock_event_store):
        """Test event emission with complete failure."""
        # Make all channels fail
        mock_redis_manager.publish_event.return_value = False
        mock_event_store.store_event.return_value = False

        with patch('services.orchestrator.modules.workflow_event_bridge.redis_manager', mock_redis_manager), \
             patch('services.orchestrator.modules.workflow_event_bridge.event_store', mock_event_store), \
             patch('services.orchestrator.modules.workflow_event_bridge.EVENT_STREAMING_AVAILABLE', False):

            success = await event_bridge.emit_workflow_event(
                "test_event",
                "workflow-123",
                {"action": "test"},
                "correlation-456"
            )

            # Should fail when all channels fail
            assert success is False

    @pytest.mark.asyncio
    async def test_emit_workflow_created_event(self, event_bridge):
        """Test workflow created event emission."""
        with patch.object(event_bridge, 'emit_workflow_event', new_callable=AsyncMock) as mock_emit:
            mock_emit.return_value = True

            workflow_data = {
                "name": "Test Workflow",
                "description": "Test description",
                "parameters": [{"name": "param1"}],
                "actions": [{"name": "action1"}]
            }

            success = await event_bridge.emit_workflow_created(
                "workflow-123",
                workflow_data,
                "user-456"
            )

            assert success is True

            # Verify event emission
            mock_emit.assert_called_once_with(
                "created",
                "workflow-123",
                {
                    "action": "created",
                    "workflow_name": "Test Workflow",
                    "workflow_description": "Test description",
                    "parameters_count": 1,
                    "actions_count": 1
                },
                None,  # correlation_id
                "user-456"
            )

    @pytest.mark.asyncio
    async def test_emit_workflow_started_event(self, event_bridge):
        """Test workflow started event emission."""
        with patch.object(event_bridge, 'emit_workflow_event', new_callable=AsyncMock) as mock_emit:
            mock_emit.return_value = True

            parameters = {"input": "test_value", "count": 5}

            success = await event_bridge.emit_workflow_started(
                "workflow-123",
                "execution-456",
                parameters,
                "user-789"
            )

            assert success is True

            mock_emit.assert_called_once_with(
                "started",
                "workflow-123",
                {
                    "action": "started",
                    "execution_id": "execution-456",
                    "parameters": parameters,
                    "parameter_count": 2
                },
                None,
                "user-789"
            )

    @pytest.mark.asyncio
    async def test_emit_workflow_completed_event(self, event_bridge):
        """Test workflow completed event emission."""
        with patch.object(event_bridge, 'emit_workflow_event', new_callable=AsyncMock) as mock_emit:
            mock_emit.return_value = True

            result = {"output": "success", "metrics": {"time": 1.5}}

            success = await event_bridge.emit_workflow_completed(
                "workflow-123",
                "execution-456",
                result,
                2.5,
                "user-789"
            )

            assert success is True

            mock_emit.assert_called_once_with(
                "completed",
                "workflow-123",
                {
                    "action": "completed",
                    "execution_id": "execution-456",
                    "result": result,
                    "duration_seconds": 2.5,
                    "success": True
                },
                None,
                "user-789"
            )

    @pytest.mark.asyncio
    async def test_emit_workflow_failed_event(self, event_bridge):
        """Test workflow failed event emission."""
        with patch.object(event_bridge, 'emit_workflow_event', new_callable=AsyncMock) as mock_emit:
            mock_emit.return_value = True

            error = "Workflow execution failed due to timeout"

            success = await event_bridge.emit_workflow_failed(
                "workflow-123",
                "execution-456",
                error,
                1.2,
                "user-789"
            )

            assert success is True

            mock_emit.assert_called_once_with(
                "failed",
                "workflow-123",
                {
                    "action": "failed",
                    "execution_id": "execution-456",
                    "error": error,
                    "duration_seconds": 1.2,
                    "success": False
                },
                None,
                "user-789"
            )

    @pytest.mark.asyncio
    async def test_emit_step_event(self, event_bridge):
        """Test workflow step event emission."""
        with patch.object(event_bridge, 'emit_workflow_event', new_callable=AsyncMock) as mock_emit:
            mock_emit.return_value = True

            step_data = {"progress": 75, "current_step": "processing"}

            success = await event_bridge.emit_step_event(
                "workflow-123",
                "execution-456",
                "step-789",
                "Data Processing",
                "completed",
                step_data,
                "user-999"
            )

            assert success is True

            mock_emit.assert_called_once_with(
                "step_completed",
                "workflow-123",
                {
                    "action": "step_completed",
                    "execution_id": "execution-456",
                    "step_id": "step-789",
                    "step_name": "Data Processing",
                    "status": "completed",
                    **step_data
                },
                None,
                "user-999"
            )

    @pytest.mark.asyncio
    async def test_event_handler_methods(self, event_bridge):
        """Test event handler methods."""
        with patch('services.orchestrator.modules.workflow_event_bridge.fire_and_forget') as mock_fire_and_forget:
            # Create mock workflow event
            mock_event = MagicMock()
            mock_event.event_id = "event-123"
            mock_event.correlation_id = "correlation-456"
            mock_event.workflow_id = "workflow-789"
            mock_event.payload = {"duration_seconds": 2.5, "error": "test error"}

            # Test started event handler
            await event_bridge._handle_workflow_started_event(mock_event)
            mock_fire_and_forget.assert_called_with(
                "info",
                "Workflow started event received: workflow-789",
                "orchestrator",
                {
                    "event_id": "event-123",
                    "correlation_id": "correlation-456"
                }
            )

            # Reset mock
            mock_fire_and_forget.reset_mock()

            # Test completed event handler
            await event_bridge._handle_workflow_completed_event(mock_event)
            mock_fire_and_forget.assert_called_with(
                "info",
                "Workflow completed event received: workflow-789",
                "orchestrator",
                {
                    "event_id": "event-123",
                    "correlation_id": "correlation-456",
                    "duration": 2.5
                }
            )

            # Reset mock
            mock_fire_and_forget.reset_mock()

            # Test failed event handler
            await event_bridge._handle_workflow_failed_event(mock_event)
            mock_fire_and_forget.assert_called_with(
                "warning",
                "Workflow failed event received: workflow-789",
                "orchestrator",
                {
                    "event_id": "event-123",
                    "correlation_id": "correlation-456",
                    "error": "test error"
                }
            )

    @pytest.mark.asyncio
    async def test_event_processor_methods(self, event_bridge):
        """Test event processor methods."""
        with patch('services.orchestrator.modules.workflow_event_bridge.fire_and_forget') as mock_fire_and_forget:
            # Create mock workflow event
            mock_event = MagicMock()
            mock_event.workflow_id = "workflow-123"

            # Test started processor
            await event_bridge._process_workflow_started(mock_event)
            mock_fire_and_forget.assert_called_with(
                "debug",
                "Processing workflow started: workflow-123",
                "orchestrator"
            )

            # Reset mock
            mock_fire_and_forget.reset_mock()

            # Test completed processor
            await event_bridge._process_workflow_completed(mock_event)
            mock_fire_and_forget.assert_called_with(
                "debug",
                "Processing workflow completed: workflow-123",
                "orchestrator"
            )

            # Reset mock
            mock_fire_and_forget.reset_mock()

            # Test failed processor
            await event_bridge._process_workflow_failed(mock_event)
            mock_fire_and_forget.assert_called_with(
                "debug",
                "Processing workflow failed: workflow-123",
                "orchestrator"
            )

    @pytest.mark.asyncio
    async def test_get_workflow_events_success(self, event_bridge, mock_event_store):
        """Test successful workflow events retrieval."""
        # Mock event store to return events
        mock_events = [
            MagicMock(
                event_id="event-1",
                event_type=MagicMock(value="WORKFLOW_STARTED"),
                timestamp=datetime.now(),
                correlation_id="corr-1",
                payload={"action": "started"},
                metadata={"source": "test"}
            ),
            MagicMock(
                event_id="event-2",
                event_type=MagicMock(value="WORKFLOW_COMPLETED"),
                timestamp=datetime.now(),
                correlation_id="corr-2",
                payload={"action": "completed"},
                metadata={"source": "test"}
            )
        ]

        mock_event_store.get_aggregate_events.return_value = mock_events

        with patch('services.orchestrator.modules.workflow_event_bridge.event_store', mock_event_store):
            events = await event_bridge.get_workflow_events("workflow-123", limit=10)

            assert len(events) == 2
            assert events[0]["event_id"] == "event-1"
            assert events[0]["event_type"] == "WORKFLOW_STARTED"
            assert events[1]["event_id"] == "event-2"
            assert events[1]["event_type"] == "WORKFLOW_COMPLETED"

    @pytest.mark.asyncio
    async def test_get_workflow_events_failure(self, event_bridge, mock_event_store):
        """Test failed workflow events retrieval."""
        mock_event_store.get_aggregate_events.side_effect = Exception("Database error")

        with patch('services.orchestrator.modules.workflow_event_bridge.event_store', mock_event_store), \
             patch('services.orchestrator.modules.workflow_event_bridge.fire_and_forget') as mock_fire_and_forget:

            events = await event_bridge.get_workflow_events("workflow-123")

            assert events == []

            # Verify error logging
            mock_fire_and_forget.assert_called_with(
                "error",
                "Failed to get workflow events for workflow-123: Database error",
                "orchestrator"
            )

    @pytest.mark.asyncio
    async def test_replay_workflow_events_success(self, event_bridge, mock_event_store):
        """Test successful workflow events replay."""
        mock_state = {
            "current_state": "completed",
            "event_count": 5,
            "last_event_timestamp": datetime.now().isoformat()
        }
        mock_event_store.replay_events.return_value = mock_state

        with patch('services.orchestrator.modules.workflow_event_bridge.event_store', mock_event_store):
            result = await event_bridge.replay_workflow_events("workflow-123")

            assert result == mock_state

    @pytest.mark.asyncio
    async def test_replay_workflow_events_failure(self, event_bridge, mock_event_store):
        """Test failed workflow events replay."""
        mock_event_store.replay_events.side_effect = Exception("Replay failed")

        with patch('services.orchestrator.modules.workflow_event_bridge.event_store', mock_event_store), \
             patch('services.orchestrator.modules.workflow_event_bridge.fire_and_forget') as mock_fire_and_forget:

            result = await event_bridge.replay_workflow_events("workflow-123")

            assert result == {"error": "Replay failed"}

            # Verify error logging
            mock_fire_and_forget.assert_called_with(
                "error",
                "Failed to replay workflow events for workflow-123: Replay failed",
                "orchestrator"
            )

    def test_map_event_type(self, event_bridge):
        """Test event type mapping."""
        # Test successful mappings
        assert event_bridge._map_event_type("created") == EventType.WORKFLOW_STARTED
        assert event_bridge._map_event_type("started") == EventType.WORKFLOW_STARTED
        assert event_bridge._map_event_type("completed") == EventType.WORKFLOW_COMPLETED
        assert event_bridge._map_event_type("failed") == EventType.WORKFLOW_FAILED
        assert event_bridge._map_event_type("error") == EventType.ERROR_OCCURRED
        assert event_bridge._map_event_type("step_started") == EventType.STEP_STARTED
        assert event_bridge._map_event_type("step_completed") == EventType.STEP_COMPLETED
        assert event_bridge._map_event_type("step_failed") == EventType.STEP_FAILED

        # Test default mapping
        assert event_bridge._map_event_type("unknown") == EventType.STATE_CHANGED


class TestWorkflowEventBridgeConvenienceFunctions:
    """Test convenience functions for workflow event bridge."""

    @pytest.fixture
    def mock_workflow_event_bridge(self):
        """Mock global workflow event bridge."""
        mock_bridge = AsyncMock()
        mock_bridge.emit_workflow_created.return_value = True
        mock_bridge.emit_workflow_started.return_value = True
        mock_bridge.emit_workflow_completed.return_value = True
        mock_bridge.emit_workflow_failed.return_value = True
        mock_bridge.emit_step_event.return_value = True
        mock_bridge.get_workflow_events.return_value = []
        mock_bridge.replay_workflow_events.return_value = {"state": "completed"}
        return mock_bridge

    @pytest.mark.asyncio
    async def test_emit_workflow_created_event_convenience(self, mock_workflow_event_bridge):
        """Test convenience function for workflow created event."""
        with patch('services.orchestrator.modules.workflow_event_bridge.workflow_event_bridge', mock_workflow_event_bridge):
            success = await emit_workflow_created_event(
                "workflow-123",
                {"name": "Test"},
                "user-456"
            )

            assert success is True
            mock_workflow_event_bridge.emit_workflow_created.assert_called_once_with(
                "workflow-123",
                {"name": "Test"},
                "user-456"
            )

    @pytest.mark.asyncio
    async def test_emit_workflow_started_event_convenience(self, mock_workflow_event_bridge):
        """Test convenience function for workflow started event."""
        with patch('services.orchestrator.modules.workflow_event_bridge.workflow_event_bridge', mock_workflow_event_bridge):
            success = await emit_workflow_started_event(
                "workflow-123",
                "exec-456",
                {"param": "value"},
                "user-789"
            )

            assert success is True
            mock_workflow_event_bridge.emit_workflow_started.assert_called_once_with(
                "workflow-123",
                "exec-456",
                {"param": "value"},
                "user-789"
            )

    @pytest.mark.asyncio
    async def test_emit_workflow_completed_event_convenience(self, mock_workflow_event_bridge):
        """Test convenience function for workflow completed event."""
        with patch('services.orchestrator.modules.workflow_event_bridge.workflow_event_bridge', mock_workflow_event_bridge):
            success = await emit_workflow_completed_event(
                "workflow-123",
                "exec-456",
                {"result": "success"},
                2.5,
                "user-789"
            )

            assert success is True
            mock_workflow_event_bridge.emit_workflow_completed.assert_called_once_with(
                "workflow-123",
                "exec-456",
                {"result": "success"},
                2.5,
                "user-789"
            )

    @pytest.mark.asyncio
    async def test_emit_workflow_failed_event_convenience(self, mock_workflow_event_bridge):
        """Test convenience function for workflow failed event."""
        with patch('services.orchestrator.modules.workflow_event_bridge.workflow_event_bridge', mock_workflow_event_bridge):
            success = await emit_workflow_failed_event(
                "workflow-123",
                "exec-456",
                "Error occurred",
                1.2,
                "user-789"
            )

            assert success is True
            mock_workflow_event_bridge.emit_workflow_failed.assert_called_once_with(
                "workflow-123",
                "exec-456",
                "Error occurred",
                1.2,
                "user-789"
            )

    @pytest.mark.asyncio
    async def test_emit_step_event_convenience(self, mock_workflow_event_bridge):
        """Test convenience function for step event."""
        with patch('services.orchestrator.modules.workflow_event_bridge.workflow_event_bridge', mock_workflow_event_bridge):
            success = await emit_step_event(
                "workflow-123",
                "exec-456",
                "step-789",
                "Process Data",
                "completed",
                {"progress": 100},
                "user-999"
            )

            assert success is True
            mock_workflow_event_bridge.emit_step_event.assert_called_once_with(
                "workflow-123",
                "exec-456",
                "step-789",
                "Process Data",
                "completed",
                {"progress": 100},
                "user-999"
            )

    @pytest.mark.asyncio
    async def test_get_workflow_events_convenience(self, mock_workflow_event_bridge):
        """Test convenience function for getting workflow events."""
        with patch('services.orchestrator.modules.workflow_event_bridge.workflow_event_bridge', mock_workflow_event_bridge):
            events = await get_workflow_events("workflow-123", limit=50)

            assert events == []
            mock_workflow_event_bridge.get_workflow_events.assert_called_once_with("workflow-123", 50)

    @pytest.mark.asyncio
    async def test_replay_workflow_events_convenience(self, mock_workflow_event_bridge):
        """Test convenience function for replaying workflow events."""
        with patch('services.orchestrator.modules.workflow_event_bridge.workflow_event_bridge', mock_workflow_event_bridge):
            state = await replay_workflow_events("workflow-123")

            assert state == {"state": "completed"}
            mock_workflow_event_bridge.replay_workflow_events.assert_called_once_with("workflow-123")


class TestWorkflowEventBridgeIntegration:
    """Integration tests for Workflow Event Bridge."""

    @pytest.mark.asyncio
    async def test_full_workflow_lifecycle_events(self):
        """Test complete workflow lifecycle event emission."""
        bridge = WorkflowEventBridge()

        workflow_id = "test-workflow-" + str(uuid.uuid4())
        execution_id = "exec-" + str(uuid.uuid4())
        user_id = "user-test"

        # Mock all dependencies
        with patch('services.orchestrator.modules.workflow_event_bridge.redis_manager') as mock_redis, \
             patch('services.orchestrator.modules.workflow_event_bridge.event_store') as mock_store, \
             patch('services.orchestrator.modules.workflow_event_bridge.EVENT_STREAMING_AVAILABLE', False):

            mock_redis.publish_event.return_value = True
            mock_store.store_event.return_value = True

            # Test workflow created
            success = await bridge.emit_workflow_created(
                workflow_id,
                {"name": "Integration Test", "actions": []},
                user_id
            )
            assert success is True

            # Test workflow started
            success = await bridge.emit_workflow_started(
                workflow_id,
                execution_id,
                {"input": "test"},
                user_id
            )
            assert success is True

            # Test step events
            success = await bridge.emit_step_event(
                workflow_id,
                execution_id,
                "step-1",
                "Initialize",
                "completed",
                {"progress": 25},
                user_id
            )
            assert success is True

            success = await bridge.emit_step_event(
                workflow_id,
                execution_id,
                "step-2",
                "Process",
                "started",
                {"progress": 50},
                user_id
            )
            assert success is True

            # Test workflow completed
            success = await bridge.emit_workflow_completed(
                workflow_id,
                execution_id,
                {"result": "success", "output": "done"},
                3.2,
                user_id
            )
            assert success is True

            # Verify all events were published
            assert mock_redis.publish_event.call_count == 4
            assert mock_store.store_event.call_count == 4

    @pytest.mark.asyncio
    async def test_error_handling_in_event_emission(self):
        """Test error handling during event emission."""
        bridge = WorkflowEventBridge()

        with patch('services.orchestrator.modules.workflow_event_bridge.redis_manager') as mock_redis, \
             patch('services.orchestrator.modules.workflow_event_bridge.event_store') as mock_store, \
             patch('services.orchestrator.modules.workflow_event_bridge.EVENT_STREAMING_AVAILABLE', False), \
             patch('services.orchestrator.modules.workflow_event_bridge.fire_and_forget') as mock_fire_and_forget:

            # Make Redis fail but event store succeed
            mock_redis.publish_event.side_effect = Exception("Redis connection failed")
            mock_store.store_event.return_value = True

            # Event emission should still succeed
            success = await bridge.emit_workflow_event(
                "test",
                "workflow-123",
                {"data": "test"},
                "correlation-456"
            )

            assert success is True

            # Verify error was logged
            mock_fire_and_forget.assert_called_with(
                "warning",
                "Failed to publish workflow event to Redis: Redis connection failed",
                "orchestrator"
            )

    @pytest.mark.asyncio
    async def test_event_correlation_and_replay(self):
        """Test event correlation and replay functionality."""
        bridge = WorkflowEventBridge()

        workflow_id = "correlation-test-" + str(uuid.uuid4())

        # Mock event store
        mock_events = [
            MagicMock(
                event_id="event-1",
                event_type=MagicMock(value="WORKFLOW_STARTED"),
                timestamp=datetime(2024, 1, 1, 12, 0, 0),
                correlation_id="corr-1",
                payload={"action": "started"},
                metadata={"source": "test"}
            ),
            MagicMock(
                event_id="event-2",
                event_type=MagicMock(value="STEP_COMPLETED"),
                timestamp=datetime(2024, 1, 1, 12, 1, 0),
                correlation_id="corr-2",
                payload={"step": "init"},
                metadata={"source": "test"}
            ),
            MagicMock(
                event_id="event-3",
                event_type=MagicMock(value="WORKFLOW_COMPLETED"),
                timestamp=datetime(2024, 1, 1, 12, 2, 0),
                correlation_id="corr-3",
                payload={"action": "completed", "result": "success"},
                metadata={"source": "test"}
            )
        ]

        with patch('services.orchestrator.modules.workflow_event_bridge.event_store') as mock_store:
            mock_store.get_aggregate_events.return_value = mock_events
            mock_store.replay_events.return_value = {
                "current_state": "completed",
                "event_count": 3,
                "started_at": datetime(2024, 1, 1, 12, 0, 0),
                "completed_at": datetime(2024, 1, 1, 12, 2, 0)
            }

            # Test getting events
            events = await bridge.get_workflow_events(workflow_id)
            assert len(events) == 3
            assert events[0]["event_type"] == "WORKFLOW_STARTED"
            assert events[2]["event_type"] == "WORKFLOW_COMPLETED"

            # Test replaying events
            state = await bridge.replay_workflow_events(workflow_id)
            assert state["current_state"] == "completed"
            assert state["event_count"] == 3


if __name__ == "__main__":
    pytest.main([__file__])
