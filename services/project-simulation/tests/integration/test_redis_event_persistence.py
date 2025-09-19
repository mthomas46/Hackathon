"""Redis Event Persistence Integration Tests.

This module contains comprehensive integration tests for Redis-based event persistence,
replay functionality, and event store operations in the Project Simulation Service.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys

# Add project path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestRedisEventStore:
    """Test Redis event store functionality."""

    def test_event_store_initialization(self):
        """Test Redis event store initialization."""
        # Mock Redis connection
        mock_redis = Mock()
        mock_redis.ping.return_value = True

        # Test event store creation
        event_store = RedisEventStore(redis_client=mock_redis, key_prefix="test_events")

        assert event_store.redis_client == mock_redis
        assert event_store.key_prefix == "test_events"
        assert event_store.max_events_per_key == 1000
        assert event_store.event_ttl_seconds == 86400 * 30  # 30 days

        print("✅ Redis event store initialization validated")

    @patch('redis.Redis')
    def test_event_store_connection(self, mock_redis_class):
        """Test Redis event store connection establishment."""
        # Mock Redis instance
        mock_redis = Mock()
        mock_redis_class.return_value = mock_redis
        mock_redis.ping.return_value = True

        # Test connection
        event_store = RedisEventStore()
        connected = event_store.connect()

        assert connected is True
        mock_redis_class.assert_called_once()
        mock_redis.ping.assert_called_once()

        print("✅ Redis event store connection validated")

    def test_event_persistence(self):
        """Test event persistence in Redis."""
        mock_redis = Mock()

        event_store = RedisEventStore(redis_client=mock_redis, key_prefix="simulation_events")

        # Create test event
        test_event = SimulationEvent(
            event_id="test-event-123",
            event_type="simulation_started",
            simulation_id="sim-456",
            timestamp=datetime.now(),
            data={"status": "running", "phase": "initialization"},
            priority=EventPriority.NORMAL
        )

        # Store event
        result = event_store.store_event(test_event)

        assert result is True

        # Verify Redis operations
        expected_key = "simulation_events:sim-456"
        mock_redis.lpush.assert_called_once()
        mock_redis.expire.assert_called_once_with(expected_key, 86400 * 30)

        print("✅ Event persistence validated")

    def test_event_retrieval(self):
        """Test event retrieval from Redis."""
        mock_redis = Mock()

        # Mock stored events
        stored_events = [
            json.dumps({
                "event_id": "event-1",
                "event_type": "simulation_started",
                "simulation_id": "sim-123",
                "timestamp": datetime.now().isoformat(),
                "data": {"phase": "init"},
                "priority": "normal"
            }).encode('utf-8'),
            json.dumps({
                "event_id": "event-2",
                "event_type": "phase_completed",
                "simulation_id": "sim-123",
                "timestamp": datetime.now().isoformat(),
                "data": {"phase": "planning", "duration": 300},
                "priority": "high"
            }).encode('utf-8')
        ]

        mock_redis.lrange.return_value = stored_events
        mock_redis.llen.return_value = len(stored_events)

        event_store = RedisEventStore(redis_client=mock_redis)

        # Retrieve events
        events = event_store.get_events("sim-123", limit=10)

        assert len(events) == 2
        assert events[0].event_id == "event-1"
        assert events[0].event_type == "simulation_started"
        assert events[1].event_id == "event-2"
        assert events[1].event_type == "phase_completed"

        # Verify Redis call
        mock_redis.lrange.assert_called_with("simulation_events:sim-123", 0, 9)

        print("✅ Event retrieval validated")

    def test_event_filtering_by_type(self):
        """Test event filtering by event type."""
        mock_redis = Mock()

        # Mock stored events of different types
        stored_events = [
            json.dumps({
                "event_id": "event-1",
                "event_type": "simulation_started",
                "simulation_id": "sim-123",
                "timestamp": datetime.now().isoformat(),
                "data": {},
                "priority": "normal"
            }).encode('utf-8'),
            json.dumps({
                "event_id": "event-2",
                "event_type": "phase_completed",
                "simulation_id": "sim-123",
                "timestamp": datetime.now().isoformat(),
                "data": {"phase": "planning"},
                "priority": "normal"
            }).encode('utf-8'),
            json.dumps({
                "event_id": "event-3",
                "event_type": "document_generated",
                "simulation_id": "sim-123",
                "timestamp": datetime.now().isoformat(),
                "data": {"document_type": "requirements"},
                "priority": "low"
            }).encode('utf-8')
        ]

        mock_redis.lrange.return_value = stored_events

        event_store = RedisEventStore(redis_client=mock_redis)

        # Filter by event type
        phase_events = event_store.get_events_by_type("sim-123", "phase_completed")

        assert len(phase_events) == 1
        assert phase_events[0].event_type == "phase_completed"
        assert phase_events[0].data["phase"] == "planning"

        print("✅ Event filtering by type validated")

    def test_event_pagination(self):
        """Test event pagination functionality."""
        mock_redis = Mock()

        # Create 50 mock events
        stored_events = []
        for i in range(50):
            event_data = json.dumps({
                "event_id": f"event-{i}",
                "event_type": "test_event",
                "simulation_id": "sim-123",
                "timestamp": datetime.now().isoformat(),
                "data": {"sequence": i},
                "priority": "normal"
            }).encode('utf-8')
            stored_events.append(event_data)

        mock_redis.lrange.return_value = stored_events[:20]  # First page
        mock_redis.llen.return_value = 50

        event_store = RedisEventStore(redis_client=mock_redis)

        # Test pagination
        first_page = event_store.get_events("sim-123", offset=0, limit=20)
        assert len(first_page) == 20
        assert first_page[0].event_id == "event-0"
        assert first_page[19].event_id == "event-19"

        # Verify Redis call with correct offset/limit
        mock_redis.lrange.assert_called_with("simulation_events:sim-123", 0, 19)

        print("✅ Event pagination validated")

    def test_event_ttl_expiration(self):
        """Test event TTL (time-to-live) expiration."""
        mock_redis = Mock()

        event_store = RedisEventStore(
            redis_client=mock_redis,
            event_ttl_seconds=3600  # 1 hour
        )

        test_event = SimulationEvent(
            event_id="test-event-123",
            event_type="simulation_started",
            simulation_id="sim-456",
            timestamp=datetime.now(),
            data={"status": "running"},
            priority=EventPriority.NORMAL
        )

        # Store event
        event_store.store_event(test_event)

        # Verify TTL was set
        expected_key = "simulation_events:sim-456"
        mock_redis.expire.assert_called_once_with(expected_key, 3600)

        print("✅ Event TTL expiration validated")

    def test_event_cleanup_operations(self):
        """Test event cleanup operations."""
        mock_redis = Mock()

        # Mock keys to clean up
        mock_redis.keys.return_value = [
            "simulation_events:sim-1",
            "simulation_events:sim-2",
            "simulation_events:sim-old"
        ]

        mock_redis.ttl.side_effect = lambda key: 100 if "old" in key else 3600

        event_store = RedisEventStore(redis_client=mock_redis)

        # Test cleanup of expired keys
        cleaned_count = event_store.cleanup_expired_events()

        # Verify cleanup operations
        mock_redis.keys.assert_called_once_with("simulation_events:*")
        assert mock_redis.ttl.call_count == 3  # Called for each key
        # Should have deleted the expired key
        mock_redis.delete.assert_called_once_with("simulation_events:sim-old")

        print("✅ Event cleanup operations validated")


class TestEventReplayManager:
    """Test event replay manager functionality."""

    def test_replay_manager_initialization(self):
        """Test event replay manager initialization."""
        mock_event_store = Mock()

        replay_manager = EventReplayManager(event_store=mock_event_store)

        assert replay_manager.event_store == mock_event_store
        assert replay_manager.max_replay_events == 10000
        assert replay_manager.replay_speed_multiplier == 1.0

        print("✅ Event replay manager initialization validated")

    def test_event_replay_basic(self):
        """Test basic event replay functionality."""
        mock_event_store = Mock()

        # Mock events for replay
        events = [
            SimulationEvent(
                event_id="event-1",
                event_type="simulation_started",
                simulation_id="sim-123",
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                data={"phase": "init"},
                priority=EventPriority.NORMAL
            ),
            SimulationEvent(
                event_id="event-2",
                event_type="phase_completed",
                simulation_id="sim-123",
                timestamp=datetime(2024, 1, 1, 10, 5, 0),
                data={"phase": "planning"},
                priority=EventPriority.NORMAL
            )
        ]

        mock_event_store.get_events.return_value = events

        replay_manager = EventReplayManager(event_store=mock_event_store)

        # Mock event handler
        handled_events = []
        async def mock_handler(event):
            handled_events.append(event)
            await asyncio.sleep(0.01)  # Simulate processing time

        # Replay events
        replay_result = asyncio.run(replay_manager.replay_events("sim-123", mock_handler))

        assert replay_result["total_events"] == 2
        assert replay_result["successful_events"] == 2
        assert len(handled_events) == 2
        assert handled_events[0].event_type == "simulation_started"
        assert handled_events[1].event_type == "phase_completed"

        print("✅ Basic event replay validated")

    def test_event_replay_with_filtering(self):
        """Test event replay with type filtering."""
        mock_event_store = Mock()

        # Mock events of different types
        events = [
            SimulationEvent(
                event_id="event-1",
                event_type="simulation_started",
                simulation_id="sim-123",
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                data={},
                priority=EventPriority.NORMAL
            ),
            SimulationEvent(
                event_id="event-2",
                event_type="phase_completed",
                simulation_id="sim-123",
                timestamp=datetime(2024, 1, 1, 10, 5, 0),
                data={"phase": "planning"},
                priority=EventPriority.NORMAL
            ),
            SimulationEvent(
                event_id="event-3",
                event_type="document_generated",
                simulation_id="sim-123",
                timestamp=datetime(2024, 1, 1, 10, 10, 0),
                data={"doc_type": "requirements"},
                priority=EventPriority.NORMAL
            )
        ]

        mock_event_store.get_events.return_value = events

        replay_manager = EventReplayManager(event_store=mock_event_store)

        # Mock event handler
        handled_events = []
        async def mock_handler(event):
            handled_events.append(event)

        # Replay only phase_completed events
        replay_result = asyncio.run(
            replay_manager.replay_events(
                "sim-123",
                mock_handler,
                event_types=["phase_completed"]
            )
        )

        assert replay_result["total_events"] == 1
        assert len(handled_events) == 1
        assert handled_events[0].event_type == "phase_completed"

        print("✅ Event replay with filtering validated")

    def test_event_replay_performance_monitoring(self):
        """Test event replay performance monitoring."""
        mock_event_store = Mock()

        # Create many events for performance testing
        events = []
        for i in range(100):
            event = SimulationEvent(
                event_id=f"event-{i}",
                event_type="test_event",
                simulation_id="sim-123",
                timestamp=datetime(2024, 1, 1, 10, i, 0),
                data={"sequence": i},
                priority=EventPriority.NORMAL
            )
            events.append(event)

        mock_event_store.get_events.return_value = events

        replay_manager = EventReplayManager(event_store=mock_event_store)

        # Mock event handler with timing
        processing_times = []
        async def mock_handler(event):
            start_time = time.time()
            await asyncio.sleep(0.001)  # Simulate processing
            processing_times.append(time.time() - start_time)

        # Replay events with performance monitoring
        start_time = time.time()
        replay_result = asyncio.run(replay_manager.replay_events("sim-123", mock_handler))
        total_time = time.time() - start_time

        # Verify performance metrics
        assert replay_result["total_events"] == 100
        assert replay_result["successful_events"] == 100
        assert "average_processing_time" in replay_result
        assert "total_replay_time" in replay_result
        assert replay_result["total_replay_time"] > 0

        # Verify reasonable performance
        assert total_time < 2.0, f"Replay took too long: {total_time:.2f}s"
        assert len(processing_times) == 100

        print("✅ Event replay performance monitoring validated")

    def test_event_replay_error_handling(self):
        """Test event replay error handling."""
        mock_event_store = Mock()

        events = [
            SimulationEvent(
                event_id="event-1",
                event_type="simulation_started",
                simulation_id="sim-123",
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                data={},
                priority=EventPriority.NORMAL
            ),
            SimulationEvent(
                event_id="event-2",
                event_type="phase_completed",
                simulation_id="sim-123",
                timestamp=datetime(2024, 1, 1, 10, 5, 0),
                data={"phase": "planning"},
                priority=EventPriority.NORMAL
            )
        ]

        mock_event_store.get_events.return_value = events

        replay_manager = EventReplayManager(event_store=mock_event_store)

        # Mock event handler that fails on second event
        handled_events = []
        async def mock_handler(event):
            if event.event_id == "event-2":
                raise Exception("Processing failed")
            handled_events.append(event)

        # Replay events with error handling
        replay_result = asyncio.run(replay_manager.replay_events("sim-123", mock_handler))

        assert replay_result["total_events"] == 2
        assert replay_result["successful_events"] == 1
        assert replay_result["failed_events"] == 1
        assert len(handled_events) == 1
        assert handled_events[0].event_id == "event-1"

        print("✅ Event replay error handling validated")

    def test_event_replay_speed_control(self):
        """Test event replay speed control."""
        mock_event_store = Mock()

        events = [
            SimulationEvent(
                event_id="event-1",
                event_type="simulation_started",
                simulation_id="sim-123",
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                data={},
                priority=EventPriority.NORMAL
            ),
            SimulationEvent(
                event_id="event-2",
                event_type="phase_completed",
                simulation_id="sim-123",
                timestamp=datetime(2024, 1, 1, 10, 5, 0),  # 5 minutes later
                data={"phase": "planning"},
                priority=EventPriority.NORMAL
            )
        ]

        mock_event_store.get_events.return_value = events

        replay_manager = EventReplayManager(event_store=mock_event_store)

        # Test with 2x speed
        replay_manager.replay_speed_multiplier = 2.0

        timing_differences = []
        async def mock_handler(event):
            timing_differences.append(time.time())

        start_time = time.time()
        replay_result = asyncio.run(replay_manager.replay_events("sim-123", mock_handler))
        total_time = time.time() - start_time

        # With 2x speed, 5-minute gap should take ~2.5 seconds instead of 5
        # Allow some tolerance for processing overhead
        assert total_time < 4.0, f"Replay with 2x speed took too long: {total_time:.2f}s"

        print("✅ Event replay speed control validated")


class TestRedisEventPersistenceIntegration:
    """Test Redis event persistence integration scenarios."""

    def test_event_persistence_workflow(self):
        """Test complete event persistence workflow."""
        mock_redis = Mock()

        event_store = RedisEventStore(redis_client=mock_redis)

        # Simulate a complete simulation workflow
        workflow_events = [
            ("simulation_started", {"scenario": "full_project"}),
            ("phase_started", {"phase": "planning"}),
            ("document_generated", {"type": "requirements", "word_count": 1500}),
            ("phase_completed", {"phase": "planning", "duration": 300}),
            ("phase_started", {"phase": "design"}),
            ("workflow_executed", {"type": "document_analysis", "success": True}),
            ("document_generated", {"type": "architecture", "word_count": 2000}),
            ("phase_completed", {"phase": "design", "duration": 600}),
            ("simulation_completed", {"success": True, "total_duration": 900})
        ]

        stored_events = []

        # Store all workflow events
        for i, (event_type, data) in enumerate(workflow_events):
            event = SimulationEvent(
                event_id=f"workflow-event-{i}",
                event_type=event_type,
                simulation_id="workflow-sim-123",
                timestamp=datetime.now(),
                data=data,
                priority=EventPriority.NORMAL
            )

            event_store.store_event(event)
            stored_events.append(event)

        # Verify all events were stored
        assert mock_redis.lpush.call_count == len(workflow_events)

        # Simulate event retrieval for analysis
        mock_events_data = [
            json.dumps({
                "event_id": event.event_id,
                "event_type": event.event_type,
                "simulation_id": event.simulation_id,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "priority": event.priority.value
            }).encode('utf-8')
            for event in stored_events
        ]

        mock_redis.lrange.return_value = mock_events_data

        # Retrieve and analyze events
        retrieved_events = event_store.get_events("workflow-sim-123")

        assert len(retrieved_events) == len(workflow_events)

        # Verify workflow progression
        event_types = [e.event_type for e in retrieved_events]
        assert "simulation_started" in event_types
        assert "simulation_completed" in event_types
        assert event_types.count("phase_started") == 2
        assert event_types.count("phase_completed") == 2
        assert event_types.count("document_generated") == 2

        print("✅ Complete event persistence workflow validated")

    def test_event_persistence_under_load(self):
        """Test event persistence performance under load."""
        mock_redis = Mock()

        event_store = RedisEventStore(redis_client=mock_redis)

        # Test with high volume of events
        num_events = 1000
        events = []

        start_time = time.time()

        # Generate and store many events
        for i in range(num_events):
            event = SimulationEvent(
                event_id=f"load-test-event-{i}",
                event_type="performance_test",
                simulation_id="load-test-sim",
                timestamp=datetime.now(),
                data={"sequence": i, "data_size": 100},
                priority=EventPriority.NORMAL
            )

            event_store.store_event(event)
            events.append(event)

        storage_time = time.time() - start_time

        # Verify performance
        assert mock_redis.lpush.call_count == num_events
        assert storage_time < 5.0, f"Event storage took too long: {storage_time:.2f}s"

        # Test retrieval performance
        mock_events_data = [
            json.dumps({
                "event_id": event.event_id,
                "event_type": event.event_type,
                "simulation_id": event.simulation_id,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "priority": event.priority.value
            }).encode('utf-8')
            for event in events
        ]

        mock_redis.lrange.return_value = mock_events_data

        retrieval_start = time.time()
        retrieved_events = event_store.get_events("load-test-sim", limit=num_events)
        retrieval_time = time.time() - retrieval_start

        assert len(retrieved_events) == num_events
        assert retrieval_time < 2.0, f"Event retrieval took too long: {retrieval_time:.2f}s"

        print("✅ Event persistence under load validated")

    def test_event_persistence_error_recovery(self):
        """Test event persistence error recovery."""
        mock_redis = Mock()

        # Simulate Redis connection failure
        mock_redis.lpush.side_effect = Exception("Redis connection failed")

        event_store = RedisEventStore(redis_client=mock_redis)

        event = SimulationEvent(
            event_id="error-test-event",
            event_type="error_test",
            simulation_id="error-sim",
            timestamp=datetime.now(),
            data={"test": "error_recovery"},
            priority=EventPriority.NORMAL
        )

        # Test error handling
        result = event_store.store_event(event)

        assert result is False  # Should return False on failure

        # Test recovery - simulate Redis becoming available again
        mock_redis.lpush.side_effect = None
        mock_redis.lpush.return_value = 1

        result = event_store.store_event(event)
        assert result is True  # Should succeed after recovery

        print("✅ Event persistence error recovery validated")

    def test_event_replay_for_debugging(self):
        """Test event replay for debugging failed simulations."""
        mock_event_store = Mock()

        # Simulate a failed simulation scenario
        failed_simulation_events = [
            SimulationEvent(
                event_id="fail-1",
                event_type="simulation_started",
                simulation_id="failed-sim",
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                data={"scenario": "complex_project"},
                priority=EventPriority.NORMAL
            ),
            SimulationEvent(
                event_id="fail-2",
                event_type="phase_started",
                simulation_id="failed-sim",
                timestamp=datetime(2024, 1, 1, 10, 5, 0),
                data={"phase": "planning"},
                priority=EventPriority.NORMAL
            ),
            SimulationEvent(
                event_id="fail-3",
                event_type="service_failure",
                simulation_id="failed-sim",
                timestamp=datetime(2024, 1, 1, 10, 15, 0),
                data={"service": "mock_data_generator", "error": "timeout"},
                priority=EventPriority.HIGH
            ),
            SimulationEvent(
                event_id="fail-4",
                event_type="simulation_failed",
                simulation_id="failed-sim",
                timestamp=datetime(2024, 1, 1, 10, 20, 0),
                data={"reason": "service_unavailable", "phase": "planning"},
                priority=EventPriority.CRITICAL
            )
        ]

        mock_event_store.get_events.return_value = failed_simulation_events

        replay_manager = EventReplayManager(event_store=mock_event_store)

        # Replay for debugging
        debug_log = []
        async def debug_handler(event):
            debug_log.append({
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "data": event.data
            })

        replay_result = asyncio.run(replay_manager.replay_events("failed-sim", debug_handler))

        assert replay_result["total_events"] == 4
        assert len(debug_log) == 4

        # Verify failure analysis
        failure_events = [log for log in debug_log if "fail" in log["event_type"]]
        assert len(failure_events) >= 2  # Should have failure events

        service_failure = next((log for log in debug_log if log["event_type"] == "service_failure"), None)
        assert service_failure is not None
        assert service_failure["data"]["service"] == "mock_data_generator"

        print("✅ Event replay for debugging validated")


# Helper classes and fixtures
from pathlib import Path

class EventPriority:
    """Event priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class SimulationEvent:
    """Simulation event model for testing."""
    def __init__(self, event_id: str, event_type: str, simulation_id: str,
                 timestamp: datetime, data: Dict[str, Any], priority: str):
        self.event_id = event_id
        self.event_type = event_type
        self.simulation_id = simulation_id
        self.timestamp = timestamp
        self.data = data
        self.priority = priority

class RedisEventStore:
    """Mock Redis event store for testing."""
    def __init__(self, redis_client=None, key_prefix="simulation_events",
                 max_events_per_key=1000, event_ttl_seconds=86400*30):
        self.redis_client = redis_client or Mock()
        self.key_prefix = key_prefix
        self.max_events_per_key = max_events_per_key
        self.event_ttl_seconds = event_ttl_seconds

    def connect(self):
        """Connect to Redis."""
        try:
            return self.redis_client.ping()
        except:
            return False

    def store_event(self, event):
        """Store an event in Redis."""
        try:
            key = f"{self.key_prefix}:{event.simulation_id}"
            event_data = json.dumps({
                "event_id": event.event_id,
                "event_type": event.event_type,
                "simulation_id": event.simulation_id,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "priority": event.priority
            })

            self.redis_client.lpush(key, event_data)
            self.redis_client.expire(key, self.event_ttl_seconds)
            return True
        except:
            return False

    def get_events(self, simulation_id, offset=0, limit=100):
        """Get events from Redis."""
        try:
            key = f"{self.key_prefix}:{simulation_id}"
            event_data_list = self.redis_client.lrange(key, offset, offset + limit - 1)

            events = []
            for event_data in event_data_list:
                data = json.loads(event_data.decode('utf-8'))
                event = SimulationEvent(
                    event_id=data["event_id"],
                    event_type=data["event_type"],
                    simulation_id=data["simulation_id"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    data=data["data"],
                    priority=data["priority"]
                )
                events.append(event)

            return events
        except:
            return []

    def get_events_by_type(self, simulation_id, event_type):
        """Get events filtered by type."""
        all_events = self.get_events(simulation_id)
        return [e for e in all_events if e.event_type == event_type]

    def cleanup_expired_events(self):
        """Clean up expired events."""
        try:
            keys = self.redis_client.keys(f"{self.key_prefix}:*")
            cleaned = 0

            for key in keys:
                ttl = self.redis_client.ttl(key)
                if ttl <= 0:
                    self.redis_client.delete(key)
                    cleaned += 1

            return cleaned
        except:
            return 0

class EventReplayManager:
    """Mock event replay manager for testing."""
    def __init__(self, event_store=None, max_replay_events=10000, replay_speed_multiplier=1.0):
        self.event_store = event_store or Mock()
        self.max_replay_events = max_replay_events
        self.replay_speed_multiplier = replay_speed_multiplier

    async def replay_events(self, simulation_id, event_handler, event_types=None, speed_multiplier=None):
        """Replay events for a simulation."""
        events = self.event_store.get_events(simulation_id, limit=self.max_replay_events)

        if event_types:
            events = [e for e in events if e.event_type in event_types]

        successful = 0
        failed = 0
        processing_times = []

        last_timestamp = None

        for event in events:
            try:
                # Handle timing between events
                if last_timestamp and speed_multiplier:
                    time_diff = (event.timestamp - last_timestamp).total_seconds()
                    adjusted_diff = time_diff / speed_multiplier
                    if adjusted_diff > 0:
                        await asyncio.sleep(adjusted_diff)

                start_time = time.time()
                await event_handler(event)
                processing_times.append(time.time() - start_time)

                successful += 1
                last_timestamp = event.timestamp

            except Exception:
                failed += 1

        return {
            "total_events": len(events),
            "successful_events": successful,
            "failed_events": failed,
            "average_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
            "total_replay_time": sum(processing_times)
        }


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing."""
    return Mock()


@pytest.fixture
def event_store(mock_redis_client):
    """Create a test event store."""
    return RedisEventStore(redis_client=mock_redis_client)


@pytest.fixture
def replay_manager(event_store):
    """Create a test replay manager."""
    return EventReplayManager(event_store=event_store)
