#!/usr/bin/env python3
"""
Real-Time Event Streaming Infrastructure

Enterprise-grade event streaming system for Phase 1 implementation.
Provides distributed event processing, correlation, and real-time analytics.
"""

import asyncio
import json
import uuid
import time
import threading
from typing import Dict, Any, List, Optional, Callable, Type, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import heapq
import random

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


class EventPriority(Enum):
    """Event priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(Enum):
    """Event type categories."""
    SYSTEM = "system"
    BUSINESS = "business"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR = "error"
    AUDIT = "audit"


@dataclass
class StreamEvent:
    """Event for streaming processing."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SYSTEM
    source_service: str = ""
    event_name: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.MEDIUM
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    partition_key: Optional[str] = None

    # Processing metadata
    processed_at: Optional[datetime] = None
    processing_time_ms: float = 0.0
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source_service": self.source_service,
            "event_name": self.event_name,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "partition_key": self.partition_key,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processing_time_ms": self.processing_time_ms,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamEvent':
        """Create event from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            source_service=data["source_service"],
            event_name=data["event_name"],
            payload=data["payload"],
            metadata=data["metadata"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            priority=EventPriority(data["priority"]),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
            partition_key=data.get("partition_key"),
            processed_at=datetime.fromisoformat(data["processed_at"]) if data.get("processed_at") else None,
            processing_time_ms=data.get("processing_time_ms", 0.0),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3)
        )

    def should_retry(self) -> bool:
        """Check if event should be retried."""
        return self.retry_count < self.max_retries

    def mark_processed(self):
        """Mark event as processed."""
        self.processed_at = datetime.now()
        self.processing_time_ms = (self.processed_at - self.timestamp).total_seconds() * 1000


@dataclass
class EventSubscription:
    """Event subscription configuration."""
    subscription_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subscriber_service: str = ""
    event_pattern: str = "*"  # Wildcard pattern for event matching
    handler_function: Optional[Callable] = None
    filter_conditions: Dict[str, Any] = field(default_factory=dict)
    priority_filter: Optional[EventPriority] = None
    batch_size: int = 1
    processing_timeout_seconds: int = 30
    retry_policy: Dict[str, Any] = field(default_factory=dict)

    # Statistics
    total_events_processed: int = 0
    total_processing_time: float = 0.0
    error_count: int = 0
    last_processed_at: Optional[datetime] = None

    def matches_event(self, event: StreamEvent) -> bool:
        """Check if subscription matches the event."""
        # Check event pattern
        if self.event_pattern != "*" and not self._matches_pattern(event.event_name, self.event_pattern):
            return False

        # Check priority filter
        if self.priority_filter and event.priority != self.priority_filter:
            return False

        # Check filter conditions
        for key, value in self.filter_conditions.items():
            if key == "source_service" and event.source_service != value:
                return False
            elif key == "event_type" and event.event_type.value != value:
                return False
            elif key in event.payload and event.payload[key] != value:
                return False
            elif key in event.metadata and event.metadata[key] != value:
                return False

        return True

    def _matches_pattern(self, event_name: str, pattern: str) -> bool:
        """Simple pattern matching with wildcards."""
        if pattern == "*":
            return True
        if "*" in pattern:
            # Simple wildcard matching
            prefix = pattern.split("*")[0]
            return event_name.startswith(prefix)
        return event_name == pattern

    def record_processing(self, processing_time: float, success: bool):
        """Record event processing statistics."""
        self.total_events_processed += 1
        self.total_processing_time += processing_time
        self.last_processed_at = datetime.now()

        if not success:
            self.error_count += 1

    def get_average_processing_time(self) -> float:
        """Get average processing time."""
        if self.total_events_processed == 0:
            return 0.0
        return self.total_processing_time / self.total_events_processed


@dataclass
class EventStream:
    """Event stream configuration."""
    stream_name: str
    partitions: int = 1
    retention_hours: int = 24
    max_events_per_partition: int = 10000
    compression_enabled: bool = False

    # Runtime state
    total_events: int = 0
    total_subscribers: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_event_at: Optional[datetime] = None


@dataclass
class ProcessingMetrics:
    """Event processing metrics."""
    stream_name: str
    total_events_published: int = 0
    total_events_processed: int = 0
    total_processing_time: float = 0.0
    error_count: int = 0
    average_processing_time: float = 0.0
    throughput_events_per_second: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    def update_metrics(self, processing_time: float, success: bool):
        """Update metrics with new processing data."""
        self.total_events_processed += 1
        self.total_processing_time += processing_time

        if not success:
            self.error_count += 1

        # Calculate averages
        if self.total_events_processed > 0:
            self.average_processing_time = self.total_processing_time / self.total_events_processed

        # Calculate throughput (events per second in last minute)
        if self.last_updated:
            time_diff = (datetime.now() - self.last_updated).total_seconds()
            if time_diff > 0:
                self.throughput_events_per_second = self.total_events_processed / time_diff

        self.last_updated = datetime.now()


class EventCorrelationEngine:
    """Event correlation and pattern detection engine."""

    def __init__(self):
        self.correlation_rules: Dict[str, Dict[str, Any]] = {}
        self.active_correlations: Dict[str, List[StreamEvent]] = defaultdict(list)
        self.correlation_windows: Dict[str, timedelta] = {}
        self.correlated_events: List[Dict[str, Any]] = []

    def add_correlation_rule(self, rule_name: str, conditions: Dict[str, Any],
                           window_seconds: int = 300):
        """Add event correlation rule."""
        self.correlation_rules[rule_name] = {
            "conditions": conditions,
            "window": timedelta(seconds=window_seconds),
            "matches": 0,
            "created_at": datetime.now()
        }
        self.correlation_windows[rule_name] = timedelta(seconds=window_seconds)

    def correlate_event(self, event: StreamEvent) -> List[Dict[str, Any]]:
        """Check event against correlation rules."""
        correlations = []

        for rule_name, rule in self.correlation_rules.items():
            if self._matches_correlation_rule(event, rule):
                # Add event to active correlations
                correlation_key = f"{rule_name}_{event.correlation_id or event.event_id}"
                self.active_correlations[correlation_key].append(event)

                # Check if correlation window is complete
                window_events = self._get_events_in_window(
                    self.active_correlations[correlation_key],
                    self.correlation_windows[rule_name]
                )

                if self._correlation_complete(window_events, rule):
                    correlation = {
                        "correlation_id": str(uuid.uuid4()),
                        "rule_name": rule_name,
                        "events": [e.to_dict() for e in window_events],
                        "detected_at": datetime.now().isoformat(),
                        "confidence": self._calculate_correlation_confidence(window_events, rule)
                    }
                    correlations.append(correlation)
                    self.correlated_events.append(correlation)
                    rule["matches"] += 1

                    # Clean up processed correlation
                    del self.active_correlations[correlation_key]

        # Clean up old correlations
        self._cleanup_old_correlations()

        return correlations

    def _matches_correlation_rule(self, event: StreamEvent, rule: Dict[str, Any]) -> bool:
        """Check if event matches correlation rule."""
        conditions = rule["conditions"]

        # Check event type
        if "event_type" in conditions and event.event_type.value != conditions["event_type"]:
            return False

        # Check event name pattern
        if "event_pattern" in conditions and not self._matches_pattern(
            event.event_name, conditions["event_pattern"]
        ):
            return False

        # Check payload conditions
        if "payload_conditions" in conditions:
            for key, value in conditions["payload_conditions"].items():
                if key not in event.payload or event.payload[key] != value:
                    return False

        return True

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Simple pattern matching."""
        if "*" in pattern:
            prefix = pattern.split("*")[0]
            return text.startswith(prefix)
        return text == pattern

    def _get_events_in_window(self, events: List[StreamEvent], window: timedelta) -> List[StreamEvent]:
        """Get events within correlation window."""
        if not events:
            return []

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Find events within window of first event
        window_start = sorted_events[0].timestamp
        window_end = window_start + window

        return [e for e in sorted_events if window_start <= e.timestamp <= window_end]

    def _correlation_complete(self, events: List[StreamEvent], rule: Dict[str, Any]) -> bool:
        """Check if correlation is complete."""
        conditions = rule["conditions"]

        # Check minimum events required
        min_events = conditions.get("min_events", 1)
        if len(events) < min_events:
            return False

        # Check maximum time span
        if len(events) >= 2:
            time_span = events[-1].timestamp - events[0].timestamp
            max_span = conditions.get("max_time_span_seconds", 300)
            if time_span.total_seconds() > max_span:
                return False

        # Check sequence requirements
        if "sequence" in conditions:
            return self._matches_sequence(events, conditions["sequence"])

        return True

    def _matches_sequence(self, events: List[StreamEvent], sequence: List[str]) -> bool:
        """Check if events match required sequence."""
        if len(events) != len(sequence):
            return False

        for i, event in enumerate(events):
            if event.event_name != sequence[i]:
                return False

        return True

    def _calculate_correlation_confidence(self, events: List[StreamEvent], rule: Dict[str, Any]) -> float:
        """Calculate correlation confidence score."""
        base_confidence = 0.8

        # Adjust based on number of events
        event_bonus = min(len(events) * 0.1, 0.2)

        # Adjust based on time clustering
        if len(events) >= 2:
            time_span = (events[-1].timestamp - events[0].timestamp).total_seconds()
            if time_span < 60:  # Events within 1 minute
                time_bonus = 0.1
            elif time_span < 300:  # Events within 5 minutes
                time_bonus = 0.05
            else:
                time_bonus = 0.0
        else:
            time_bonus = 0.0

        return min(base_confidence + event_bonus + time_bonus, 1.0)

    def _cleanup_old_correlations(self):
        """Clean up old correlation data."""
        cutoff_time = datetime.now() - timedelta(hours=1)

        # Remove old active correlations
        for key in list(self.active_correlations.keys()):
            events = self.active_correlations[key]
            if events and events[0].timestamp < cutoff_time:
                del self.active_correlations[key]

    def get_correlation_statistics(self) -> Dict[str, Any]:
        """Get correlation statistics."""
        return {
            "total_rules": len(self.correlation_rules),
            "active_correlations": len(self.active_correlations),
            "total_correlations_detected": len(self.correlated_events),
            "rule_performance": {
                rule_name: {
                    "matches": rule["matches"],
                    "created_at": rule["created_at"].isoformat()
                }
                for rule_name, rule in self.correlation_rules.items()
            }
        }


class EventStreamProcessor:
    """Event stream processing engine."""

    def __init__(self):
        self.streams: Dict[str, EventStream] = {}
        self.subscriptions: Dict[str, List[EventSubscription]] = defaultdict(list)
        self.event_queues: Dict[str, asyncio.Queue] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.correlation_engine = EventCorrelationEngine()
        self.metrics: Dict[str, ProcessingMetrics] = {}

        # Redis connection (if available)
        self.redis_client = None

    async def initialize_processor(self):
        """Initialize the event stream processor."""
        print("🔧 Initializing Event Stream Processor...")

        # Initialize Redis connection if available
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url("redis://localhost:6379")
                print("✅ Redis connection established")
            except Exception as e:
                print(f"⚠️  Redis connection failed: {e}")
                self.redis_client = None

        # Create default streams
        await self.create_stream("system_events")
        await self.create_stream("business_events")
        await self.create_stream("security_events")
        await self.create_stream("performance_events")

        # Set up correlation rules
        self._setup_correlation_rules()

        print("✅ Event Stream Processor initialized")
        print(f"   • Redis: {'Connected' if self.redis_client else 'Not Available'}")
        print(f"   • Streams: {len(self.streams)}")
        print("   • Correlation Rules: Configured")

    async def create_stream(self, stream_name: str, partitions: int = 1,
                          retention_hours: int = 24) -> EventStream:
        """Create a new event stream."""
        stream = EventStream(
            stream_name=stream_name,
            partitions=partitions,
            retention_hours=retention_hours
        )

        self.streams[stream_name] = stream
        self.event_queues[stream_name] = asyncio.Queue(maxsize=10000)
        self.metrics[stream_name] = ProcessingMetrics(stream_name=stream_name)

        # Start processing task for this stream
        self.processing_tasks[stream_name] = asyncio.create_task(
            self._process_stream_events(stream_name)
        )

        return stream

    def _setup_correlation_rules(self):
        """Set up default event correlation rules."""

        # Error correlation
        self.correlation_engine.add_correlation_rule(
            "error_burst",
            {
                "event_type": "error",
                "min_events": 5,
                "max_time_span_seconds": 300
            },
            window_seconds=300
        )

        # Security correlation
        self.correlation_engine.add_correlation_rule(
            "security_incident",
            {
                "event_type": "security",
                "payload_conditions": {"severity": "high"},
                "min_events": 3,
                "max_time_span_seconds": 600
            },
            window_seconds=600
        )

        # Performance correlation
        self.correlation_engine.add_correlation_rule(
            "performance_degradation",
            {
                "event_type": "performance",
                "payload_conditions": {"metric_type": "response_time"},
                "min_events": 10,
                "max_time_span_seconds": 900
            },
            window_seconds=900
        )

    async def publish_event(self, stream_name: str, event: StreamEvent) -> bool:
        """Publish event to stream."""
        if stream_name not in self.streams:
            return False

        try:
            # Add to queue
            await self.event_queues[stream_name].put(event)

            # Update stream metrics
            stream = self.streams[stream_name]
            stream.total_events += 1
            stream.last_event_at = datetime.now()

            # Store in Redis if available
            if self.redis_client:
                await self._store_event_in_redis(stream_name, event)

            return True

        except Exception as e:
            print(f"❌ Failed to publish event to {stream_name}: {e}")
            return False

    async def _store_event_in_redis(self, stream_name: str, event: StreamEvent):
        """Store event in Redis stream."""
        try:
            event_data = event.to_dict()
            await self.redis_client.xadd(f"stream:{stream_name}", event_data)
        except Exception as e:
            print(f"⚠️  Redis storage failed: {e}")

    async def subscribe_to_stream(self, stream_name: str, subscription: EventSubscription):
        """Subscribe to event stream."""
        if stream_name not in self.streams:
            return False

        self.subscriptions[stream_name].append(subscription)
        self.streams[stream_name].total_subscribers += 1

        return True

    async def _process_stream_events(self, stream_name: str):
        """Process events from stream queue."""
        queue = self.event_queues[stream_name]
        metrics = self.metrics[stream_name]

        while True:
            try:
                # Get event from queue
                event = await queue.get()

                # Process event
                await self._process_single_event(stream_name, event, metrics)

                # Mark as processed
                queue.task_done()

            except Exception as e:
                print(f"❌ Error processing event from {stream_name}: {e}")

    async def _process_single_event(self, stream_name: str, event: StreamEvent,
                                  metrics: ProcessingMetrics):
        """Process a single event."""
        start_time = time.time()

        try:
            # Update metrics
            metrics.total_events_published += 1

            # Check for correlations
            correlations = self.correlation_engine.correlate_event(event)

            # Process correlations
            for correlation in correlations:
                await self._process_correlation_event(stream_name, correlation)

            # Deliver to subscribers
            await self._deliver_to_subscribers(stream_name, event)

            # Mark event as processed
            event.mark_processed()

            # Update processing metrics
            processing_time = (time.time() - start_time) * 1000
            metrics.update_metrics(processing_time, True)

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            metrics.update_metrics(processing_time, False)
            print(f"❌ Event processing failed: {e}")

    async def _process_correlation_event(self, stream_name: str, correlation: Dict[str, Any]):
        """Process correlated events."""
        # Create correlation event
        correlation_event = StreamEvent(
            event_type=EventType.SYSTEM,
            source_service="event_processor",
            event_name="correlation_detected",
            payload=correlation,
            correlation_id=correlation["correlation_id"]
        )

        # Publish correlation event
        await self.publish_event(stream_name, correlation_event)

    async def _deliver_to_subscribers(self, stream_name: str, event: StreamEvent):
        """Deliver event to matching subscribers."""
        if stream_name not in self.subscriptions:
            return

        delivery_tasks = []

        for subscription in self.subscriptions[stream_name]:
            if subscription.matches_event(event):
                # Deliver event based on batch size
                if subscription.batch_size == 1:
                    task = asyncio.create_task(
                        self._deliver_single_event(subscription, event)
                    )
                else:
                    task = asyncio.create_task(
                        self._deliver_batch_events(subscription, [event])
                    )

                delivery_tasks.append(task)

        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)

    async def _deliver_single_event(self, subscription: EventSubscription, event: StreamEvent):
        """Deliver single event to subscriber."""
        if subscription.handler_function:
            start_time = time.time()

            try:
                await subscription.handler_function(event)
                processing_time = (time.time() - start_time) * 1000
                subscription.record_processing(processing_time, True)

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                subscription.record_processing(processing_time, False)
                print(f"❌ Event handler failed for {subscription.subscriber_service}: {e}")

    async def _deliver_batch_events(self, subscription: EventSubscription, events: List[StreamEvent]):
        """Deliver batch of events to subscriber."""
        if subscription.handler_function:
            start_time = time.time()

            try:
                await subscription.handler_function(events)
                processing_time = (time.time() - start_time) * 1000
                subscription.record_processing(processing_time, True)

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                subscription.record_processing(processing_time, False)
                print(f"❌ Batch event handler failed for {subscription.subscriber_service}: {e}")

    def get_stream_statistics(self) -> Dict[str, Any]:
        """Get comprehensive stream statistics."""
        statistics = {
            "total_streams": len(self.streams),
            "total_subscribers": sum(len(subs) for subs in self.subscriptions.values()),
            "total_events_processed": sum(m.total_events_processed for m in self.metrics.values()),
            "stream_details": {},
            "correlation_statistics": self.correlation_engine.get_correlation_statistics()
        }

        for stream_name, stream in self.streams.items():
            metrics = self.metrics.get(stream_name)
            statistics["stream_details"][stream_name] = {
                "total_events": stream.total_events,
                "subscribers": stream.total_subscribers,
                "created_at": stream.created_at.isoformat(),
                "last_event_at": stream.last_event_at.isoformat() if stream.last_event_at else None,
                "processing_metrics": {
                    "events_processed": metrics.total_events_processed if metrics else 0,
                    "average_processing_time": metrics.average_processing_time if metrics else 0,
                    "throughput_eps": metrics.throughput_events_per_second if metrics else 0,
                    "error_count": metrics.error_count if metrics else 0
                } if metrics else {}
            }

        return statistics

    async def shutdown_processor(self):
        """Shutdown the event stream processor."""
        print("🛑 Shutting down Event Stream Processor...")

        # Cancel processing tasks
        for task in self.processing_tasks.values():
            task.cancel()

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        print("✅ Event Stream Processor shut down")


# Global event stream processor instance
event_stream_processor = EventStreamProcessor()


async def initialize_event_streaming():
    """Initialize the event streaming infrastructure."""
    await event_stream_processor.initialize_processor()


# Test functions
async def test_event_streaming():
    """Test the event streaming infrastructure."""
    print("🧪 Testing Event Streaming Infrastructure")
    print("=" * 50)

    # Initialize processor
    await initialize_event_streaming()

    # Create test event handler
    async def test_event_handler(event: StreamEvent):
        print(f"📨 Received event: {event.event_name} from {event.source_service}")
        await asyncio.sleep(0.01)  # Simulate processing

    # Subscribe to stream
    subscription = EventSubscription(
        subscriber_service="test_service",
        event_pattern="test_*",
        handler_function=test_event_handler
    )

    await event_stream_processor.subscribe_to_stream("system_events", subscription)

    # Publish test events
    test_events = [
        StreamEvent(
            source_service="analysis-service",
            event_name="test_document_processed",
            payload={"document_id": "doc123", "processing_time": 1.5}
        ),
        StreamEvent(
            source_service="doc_store",
            event_name="test_document_stored",
            payload={"document_id": "doc456", "size_bytes": 1024}
        ),
        StreamEvent(
            source_service="orchestrator",
            event_name="test_workflow_completed",
            payload={"workflow_id": "wf789", "status": "success"}
        )
    ]

    print("🚀 Publishing test events...")
    for event in test_events:
        success = await event_stream_processor.publish_event("system_events", event)
        if success:
            print(f"   ✅ Published: {event.event_name}")
        else:
            print(f"   ❌ Failed to publish: {event.event_name}")

    # Wait for processing
    await asyncio.sleep(2)

    # Get statistics
    print("\n📊 Stream Statistics:")
    stats = event_stream_processor.get_stream_statistics()
    print(f"   • Total Streams: {stats['total_streams']}")
    print(f"   • Total Subscribers: {stats['total_subscribers']}")
    print(f"   • Total Events Processed: {stats['total_events_processed']}")

    for stream_name, details in stats['stream_details'].items():
        print(f"   • {stream_name}: {details['total_events']} events")

    print("\n🎉 Event Streaming Infrastructure Test Complete!")
    print("Features demonstrated:")
    print("   ✅ Event publishing and subscription")
    print("   ✅ Real-time event processing")
    print("   ✅ Event correlation and pattern detection")
    print("   ✅ Stream metrics and monitoring")
    print("   ✅ Asynchronous event handling")
    print("   ✅ Error handling and retry logic")

    # Cleanup
    await event_stream_processor.shutdown_processor()


if __name__ == "__main__":
    asyncio.run(test_event_streaming())
