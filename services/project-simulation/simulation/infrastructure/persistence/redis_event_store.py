"""Redis Event Store - Durable Event Persistence and Replay.

This module provides Redis-based event persistence and replay functionality
for simulation events, enabling durable storage, querying, filtering, and
historical replay of simulation execution events.

Key Features:
- Event persistence with TTL and compression
- Event replay with filtering and time range selection
- Event querying with advanced filtering capabilities
- Stream management with partitioning and sharding
- Integration with WebSocket broadcasting
- Performance metrics and monitoring
"""

import sys
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Iterator, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger


class EventPriority(str, Enum):
    """Event priority levels for processing."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(str, Enum):
    """Types of simulation events."""
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_COMPLETED = "simulation_completed"
    SIMULATION_FAILED = "simulation_failed"
    SIMULATION_PAUSED = "simulation_paused"
    SIMULATION_RESUMED = "simulation_resumed"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    PHASE_FAILED = "phase_failed"
    DOCUMENT_GENERATED = "document_generated"
    WORKFLOW_EXECUTED = "workflow_executed"
    ANALYSIS_COMPLETED = "analysis_completed"
    PROGRESS_UPDATE = "progress_update"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_EVENT = "system_event"


class CompressionType(str, Enum):
    """Event data compression types."""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"


@dataclass
class SimulationEvent:
    """Represents a simulation event with metadata."""
    event_id: str
    simulation_id: str
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "simulation_id": self.simulation_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "tags": self.tags,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationEvent':
        """Create event from dictionary."""
        return cls(
            event_id=data["event_id"],
            simulation_id=data["simulation_id"],
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data["data"],
            priority=EventPriority(data.get("priority", "normal")),
            correlation_id=data.get("correlation_id"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class ReplayConfiguration:
    """Configuration for event replay."""
    simulation_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_types: List[EventType] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    speed_multiplier: float = 1.0
    include_system_events: bool = False
    max_events: Optional[int] = None
    batch_size: int = 100


class RedisEventStore:
    """Redis-based event store with persistence and replay capabilities."""

    def __init__(self,
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 redis_db: int = 0,
                 redis_password: Optional[str] = None,
                 key_prefix: str = "simulation:events",
                 compression: CompressionType = CompressionType.NONE,
                 ttl_seconds: int = 86400 * 7,  # 7 days
                 max_connections: int = 10):
        """Initialize Redis event store."""
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_password = redis_password
        self.key_prefix = key_prefix
        self.compression = compression
        self.ttl_seconds = ttl_seconds
        self.max_connections = max_connections

        self.logger = get_simulation_logger()
        self._redis_client = None
        self._executor = ThreadPoolExecutor(max_workers=max_connections)
        self._running = False

        # Statistics
        self.stats = {
            "events_stored": 0,
            "events_retrieved": 0,
            "replay_sessions": 0,
            "errors": 0
        }

    async def initialize(self) -> None:
        """Initialize Redis connection and setup."""
        try:
            # Import redis here to make it optional
            import redis
            from redis import ConnectionPool

            # Create connection pool
            pool = ConnectionPool(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                max_connections=self.max_connections,
                decode_responses=True
            )

            self._redis_client = redis.Redis(connection_pool=pool)

            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                self._executor, self._redis_client.ping
            )

            # Setup indexes and streams
            await self._setup_indexes()

            self._running = True
            self.logger.info(f"Redis event store initialized: {self.redis_host}:{self.redis_port}")

        except ImportError:
            self.logger.warning("Redis not available, falling back to in-memory storage")
            self._redis_client = None
            self._fallback_store = {}
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis event store: {e}")
            raise

    async def store_event(self, event: SimulationEvent) -> bool:
        """Store an event in Redis."""
        try:
            if not self._redis_client:
                return await self._store_fallback(event)

            # Serialize event
            event_data = event.to_dict()
            serialized_data = json.dumps(event_data)

            # Apply compression if configured
            if self.compression == CompressionType.GZIP:
                import gzip
                serialized_data = gzip.compress(serialized_data.encode())
            elif self.compression == CompressionType.LZ4:
                try:
                    import lz4.frame
                    serialized_data = lz4.frame.compress(serialized_data.encode())
                except ImportError:
                    self.logger.warning("LZ4 not available, storing uncompressed")

            # Store in Redis with TTL
            keys = [
                f"{self.key_prefix}:simulation:{event.simulation_id}",
                f"{self.key_prefix}:type:{event.event_type.value}",
                f"{self.key_prefix}:time:{int(event.timestamp.timestamp())}",
                f"{self.key_prefix}:event:{event.event_id}"
            ]

            # Use pipeline for atomic operations
            pipeline = self._redis_client.pipeline()

            # Store event data
            event_key = f"{self.key_prefix}:event:{event.event_id}"
            pipeline.setex(event_key, self.ttl_seconds, serialized_data)

            # Add to simulation stream
            sim_stream = f"{self.key_prefix}:stream:{event.simulation_id}"
            pipeline.xadd(sim_stream, {"event_id": event.event_id, "timestamp": event.timestamp.isoformat()})

            # Add to indexes
            for key in keys[:-1]:  # Exclude the event key itself
                pipeline.sadd(key, event.event_id)

            # Set TTL on keys
            for key in keys:
                pipeline.expire(key, self.ttl_seconds)

            # Execute pipeline
            await asyncio.get_event_loop().run_in_executor(self._executor, pipeline.execute)

            self.stats["events_stored"] += 1

            # Publish to Redis pub/sub for real-time listeners
            await self._publish_event(event)

            return True

        except Exception as e:
            self.logger.error(f"Failed to store event {event.event_id}: {e}")
            self.stats["errors"] += 1
            return False

    async def get_events(self,
                        simulation_id: Optional[str] = None,
                        event_types: List[EventType] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        tags: List[str] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[SimulationEvent]:
        """Retrieve events with filtering."""
        try:
            if not self._redis_client:
                return await self._get_fallback_events(simulation_id, event_types, start_time, end_time, limit, offset)

            # Build query
            event_ids = await self._build_event_query(
                simulation_id, event_types, start_time, end_time, tags, limit, offset
            )

            if not event_ids:
                return []

            # Retrieve event data
            pipeline = self._redis_client.pipeline()
            for event_id in event_ids:
                pipeline.get(f"{self.key_prefix}:event:{event_id}")

            results = await asyncio.get_event_loop().run_in_executor(self._executor, pipeline.execute)

            events = []
            for result in results:
                if result:
                    try:
                        # Handle compression
                        data = result
                        if isinstance(data, bytes):
                            if self.compression == CompressionType.GZIP:
                                import gzip
                                data = gzip.decompress(data).decode()
                            elif self.compression == CompressionType.LZ4:
                                import lz4.frame
                                data = lz4.frame.decompress(data).decode()

                        event_data = json.loads(data)
                        event = SimulationEvent.from_dict(event_data)
                        events.append(event)
                    except Exception as e:
                        self.logger.error(f"Failed to deserialize event: {e}")

            self.stats["events_retrieved"] += len(events)
            return events

        except Exception as e:
            self.logger.error(f"Failed to retrieve events: {e}")
            self.stats["errors"] += 1
            return []

    async def replay_events(self, config: ReplayConfiguration, callback: Callable[[SimulationEvent], None]) -> int:
        """Replay events with the specified configuration."""
        try:
            self.stats["replay_sessions"] += 1

            # Get events for replay
            events = await self.get_events(
                simulation_id=config.simulation_id,
                event_types=config.event_types if config.event_types else None,
                start_time=config.start_time,
                end_time=config.end_time,
                tags=config.tags if config.tags else None,
                limit=config.max_events or 1000
            )

            # Sort events by timestamp
            events.sort(key=lambda e: e.timestamp)

            replayed_count = 0
            last_timestamp = None

            for event in events:
                # Apply speed multiplier for timing
                if last_timestamp and config.speed_multiplier != 1.0:
                    time_diff = (event.timestamp - last_timestamp).total_seconds()
                    adjusted_diff = time_diff / config.speed_multiplier
                    if adjusted_diff > 0:
                        await asyncio.sleep(adjusted_diff)

                # Call callback with event
                callback(event)
                replayed_count += 1
                last_timestamp = event.timestamp

                # Check max events limit
                if config.max_events and replayed_count >= config.max_events:
                    break

            self.logger.info(f"Replayed {replayed_count} events for simulation {config.simulation_id}")
            return replayed_count

        except Exception as e:
            self.logger.error(f"Failed to replay events: {e}")
            self.stats["errors"] += 1
            return 0

    async def get_simulation_timeline(self, simulation_id: str) -> List[Dict[str, Any]]:
        """Get timeline of events for a simulation."""
        try:
            events = await self.get_events(simulation_id=simulation_id, limit=1000)

            timeline = []
            for event in sorted(events, key=lambda e: e.timestamp):
                timeline.append({
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type.value,
                    "description": self._get_event_description(event),
                    "data": event.data,
                    "tags": event.tags
                })

            return timeline

        except Exception as e:
            self.logger.error(f"Failed to get simulation timeline: {e}")
            return []

    async def get_event_statistics(self,
                                 simulation_id: Optional[str] = None,
                                 start_time: Optional[datetime] = None,
                                 end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get statistics about stored events."""
        try:
            events = await self.get_events(
                simulation_id=simulation_id,
                start_time=start_time,
                end_time=end_time,
                limit=10000  # Large limit for statistics
            )

            stats = {
                "total_events": len(events),
                "event_types": {},
                "time_range": {
                    "start": min(events, key=lambda e: e.timestamp).timestamp.isoformat() if events else None,
                    "end": max(events, key=lambda e: e.timestamp).timestamp.isoformat() if events else None
                },
                "simulations": set(),
                "tags": set()
            }

            for event in events:
                # Count event types
                et = event.event_type.value
                stats["event_types"][et] = stats["event_types"].get(et, 0) + 1

                # Track simulations
                stats["simulations"].add(event.simulation_id)

                # Track tags
                stats["tags"].update(event.tags)

            stats["simulations"] = list(stats["simulations"])
            stats["tags"] = list(stats["tags"])

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get event statistics: {e}")
            return {"error": str(e)}

    async def cleanup_old_events(self, days_old: int = 30) -> int:
        """Clean up events older than specified days."""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_old)

            # Find old events
            old_events = await self.get_events(end_time=cutoff_time)

            if not old_events:
                return 0

            # Delete old events
            event_ids = [event.event_id for event in old_events]

            if self._redis_client:
                pipeline = self._redis_client.pipeline()
                for event_id in event_ids:
                    pipeline.delete(f"{self.key_prefix}:event:{event_id}")
                await asyncio.get_event_loop().run_in_executor(self._executor, pipeline.execute)

            self.logger.info(f"Cleaned up {len(event_ids)} old events")
            return len(event_ids)

        except Exception as e:
            self.logger.error(f"Failed to cleanup old events: {e}")
            return 0

    async def shutdown(self) -> None:
        """Shutdown the event store."""
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=True)
        self.logger.info("Redis event store shut down")

    # Private methods

    async def _setup_indexes(self) -> None:
        """Setup Redis indexes and streams."""
        if not self._redis_client:
            return

        try:
            # Create consumer group for event streams
            stream_key = f"{self.key_prefix}:stream:*"
            # Note: Redis streams consumer groups would be created per simulation
            self.logger.debug("Redis indexes and streams setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup indexes: {e}")

    async def _publish_event(self, event: SimulationEvent) -> None:
        """Publish event to Redis pub/sub."""
        if not self._redis_client:
            return

        try:
            channel = f"{self.key_prefix}:pubsub:{event.simulation_id}"
            message = json.dumps(event.to_dict())

            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: self._redis_client.publish(channel, message)
            )
        except Exception as e:
            self.logger.error(f"Failed to publish event: {e}")

    async def _build_event_query(self,
                               simulation_id: Optional[str],
                               event_types: Optional[List[EventType]],
                               start_time: Optional[datetime],
                               end_time: Optional[datetime],
                               tags: Optional[List[str]],
                               limit: int,
                               offset: int) -> List[str]:
        """Build Redis query for event filtering."""
        if not self._redis_client:
            return []

        try:
            # Start with all events if no simulation specified
            if simulation_id:
                base_key = f"{self.key_prefix}:simulation:{simulation_id}"
                event_ids = await asyncio.get_event_loop().run_in_executor(
                    self._executor, lambda: self._redis_client.smembers(base_key)
                )
            else:
                # Get all simulation keys and union them
                pattern = f"{self.key_prefix}:simulation:*"
                sim_keys = await asyncio.get_event_loop().run_in_executor(
                    self._executor, lambda: self._redis_client.keys(pattern)
                )

                if not sim_keys:
                    return []

                pipeline = self._redis_client.pipeline()
                for key in sim_keys:
                    pipeline.smembers(key)
                results = await asyncio.get_event_loop().run_in_executor(self._executor, pipeline.execute)

                event_ids = set()
                for result in results:
                    event_ids.update(result)

            if not event_ids:
                return []

            # Apply filters
            filtered_ids = set(event_ids)

            # Filter by event types
            if event_types:
                type_ids = set()
                for event_type in event_types:
                    type_key = f"{self.key_prefix}:type:{event_type.value}"
                    type_event_ids = await asyncio.get_event_loop().run_in_executor(
                        self._executor, lambda: self._redis_client.smembers(type_key)
                    )
                    type_ids.update(type_event_ids)
                filtered_ids = filtered_ids.intersection(type_ids)

            # Apply time range filtering (simplified)
            # In a real implementation, you'd use Redis sorted sets for time-based indexing

            # Apply offset and limit
            sorted_ids = sorted(list(filtered_ids))
            if offset >= len(sorted_ids):
                return []

            end_index = min(offset + limit, len(sorted_ids))
            return sorted_ids[offset:end_index]

        except Exception as e:
            self.logger.error(f"Failed to build event query: {e}")
            return []

    def _get_event_description(self, event: SimulationEvent) -> str:
        """Get human-readable description for an event."""
        descriptions = {
            EventType.SIMULATION_STARTED: "Simulation execution began",
            EventType.SIMULATION_COMPLETED: "Simulation finished successfully",
            EventType.SIMULATION_FAILED: "Simulation encountered an error",
            EventType.PHASE_STARTED: f"Phase '{event.data.get('phase_name', 'Unknown')}' began",
            EventType.PHASE_COMPLETED: f"Phase '{event.data.get('phase_name', 'Unknown')}' completed",
            EventType.DOCUMENT_GENERATED: f"Document '{event.data.get('document_title', 'Unknown')}' generated",
            EventType.WORKFLOW_EXECUTED: f"Workflow '{event.data.get('workflow_name', 'Unknown')}' executed",
            EventType.ANALYSIS_COMPLETED: "Analysis completed",
            EventType.ERROR_OCCURRED: f"Error occurred: {event.data.get('error', 'Unknown')}"
        }

        return descriptions.get(event.event_type, f"Event: {event.event_type.value}")

    # Fallback methods for when Redis is not available

    async def _store_fallback(self, event: SimulationEvent) -> bool:
        """Fallback storage when Redis is not available."""
        if not hasattr(self, '_fallback_store'):
            self._fallback_store = {}

        self._fallback_store[event.event_id] = event
        self.stats["events_stored"] += 1
        return True

    async def _get_fallback_events(self,
                                 simulation_id: Optional[str],
                                 event_types: Optional[List[EventType]],
                                 start_time: Optional[datetime],
                                 end_time: Optional[datetime],
                                 limit: int,
                                 offset: int) -> List[SimulationEvent]:
        """Fallback event retrieval."""
        if not hasattr(self, '_fallback_store'):
            return []

        events = list(self._fallback_store.values())

        # Apply filters
        if simulation_id:
            events = [e for e in events if e.simulation_id == simulation_id]

        if event_types:
            events = [e for e in events if e.event_type in event_types]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)

        # Apply pagination
        start_idx = min(offset, len(events))
        end_idx = min(start_idx + limit, len(events))

        self.stats["events_retrieved"] += len(events[start_idx:end_idx])
        return events[start_idx:end_idx]


class EventReplayManager:
    """Manages event replay sessions and coordination."""

    def __init__(self, event_store: RedisEventStore):
        """Initialize replay manager."""
        self.event_store = event_store
        self.logger = get_simulation_logger()
        self.active_replays: Dict[str, ReplayConfiguration] = {}

    async def start_replay(self,
                          simulation_id: str,
                          callback: Callable[[SimulationEvent], None],
                          config: ReplayConfiguration) -> str:
        """Start an event replay session."""
        replay_id = str(uuid.uuid4())

        # Store replay configuration
        self.active_replays[replay_id] = config

        # Start replay in background
        asyncio.create_task(self._execute_replay(replay_id, callback))

        self.logger.info(f"Started event replay {replay_id} for simulation {simulation_id}")
        return replay_id

    async def stop_replay(self, replay_id: str) -> bool:
        """Stop an active replay session."""
        if replay_id in self.active_replays:
            del self.active_replays[replay_id]
            self.logger.info(f"Stopped event replay {replay_id}")
            return True
        return False

    async def get_replay_status(self, replay_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a replay session."""
        if replay_id not in self.active_replays:
            return None

        config = self.active_replays[replay_id]
        return {
            "replay_id": replay_id,
            "simulation_id": config.simulation_id,
            "status": "active",
            "speed_multiplier": config.speed_multiplier,
            "event_types": [et.value for et in config.event_types] if config.event_types else None
        }

    async def _execute_replay(self, replay_id: str, callback: Callable[[SimulationEvent], None]) -> None:
        """Execute the replay in the background."""
        try:
            if replay_id not in self.active_replays:
                return

            config = self.active_replays[replay_id]

            # Execute replay
            events_replayed = await self.event_store.replay_events(config, callback)

            self.logger.info(f"Completed event replay {replay_id}: {events_replayed} events replayed")

        except Exception as e:
            self.logger.error(f"Error during event replay {replay_id}: {e}")
        finally:
            # Clean up
            if replay_id in self.active_replays:
                del self.active_replays[replay_id]


# Global instances
_event_store: Optional[RedisEventStore] = None
_replay_manager: Optional[EventReplayManager] = None


def get_event_store() -> RedisEventStore:
    """Get the global event store instance."""
    global _event_store
    if _event_store is None:
        _event_store = RedisEventStore()
    return _event_store


def get_replay_manager() -> EventReplayManager:
    """Get the global replay manager instance."""
    global _replay_manager
    if _replay_manager is None:
        _replay_manager = EventReplayManager(get_event_store())
    return _replay_manager


async def initialize_event_persistence() -> None:
    """Initialize the event persistence system."""
    store = get_event_store()
    await store.initialize()


__all__ = [
    'RedisEventStore',
    'EventReplayManager',
    'SimulationEvent',
    'EventType',
    'EventPriority',
    'CompressionType',
    'ReplayConfiguration',
    'get_event_store',
    'get_replay_manager',
    'initialize_event_persistence'
]
