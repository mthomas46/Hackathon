"""Consolidated orchestration utilities for distributed operations.

Combines event ordering, dead letter queue, saga patterns, and event replay.
"""
import time
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger(__name__)

# Event Ordering
class EventPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class EventMetadata:
    sequence_id: str
    timestamp: float
    priority: EventPriority
    correlation_id: Optional[str] = None
    source_service: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class EventOrderer:
    """Manages event ordering and deduplication."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._sequence_counter = 0
        self._seen_events: Dict[str, float] = {}

    def create_event_metadata(
        self,
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None
    ) -> EventMetadata:
        self._sequence_counter += 1
        sequence_id = f"{self.service_name}:{int(time.time() * 1000)}:{self._sequence_counter}"

        return EventMetadata(
            sequence_id=sequence_id,
            timestamp=time.time(),
            priority=priority,
            correlation_id=correlation_id,
            source_service=self.service_name
        )

    def is_duplicate(self, event_id: str, ttl_seconds: int = 300) -> bool:
        now = time.time()
        if event_id in self._seen_events:
            if now - self._seen_events[event_id] < ttl_seconds:
                return True
            else:
                del self._seen_events[event_id]
        self._seen_events[event_id] = now
        return False


def create_ordered_event(
    event_type: str,
    payload: Dict[str, Any],
    orderer: EventOrderer,
    priority: EventPriority = EventPriority.NORMAL,
    correlation_id: Optional[str] = None
) -> Dict[str, Any]:
    metadata = orderer.create_event_metadata(priority, correlation_id)
    return {
        "event_type": event_type,
        "payload": payload,
        "metadata": asdict(metadata)
    }


# Dead Letter Queue
class RetryPolicy(Enum):
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"


@dataclass
class DLQEntry:
    event_id: str
    event_type: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    failure_reason: str
    failure_timestamp: float
    retry_count: int
    max_retries: int
    retry_policy: RetryPolicy
    next_retry_at: float
    dlq_timestamp: float


class DeadLetterQueue:
    """Enhanced Dead Letter Queue with retry policies."""

    def __init__(
        self,
        redis_host: str = "redis",
        dlq_key: str = "dlq:failed_events",
        retry_key: str = "dlq:retry_queue",
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 300.0
    ):
        self.redis_host = redis_host
        self.dlq_key = dlq_key
        self.retry_key = retry_key
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._redis_client: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if not aioredis:
            raise RuntimeError("aioredis not available")
        if not self._redis_client:
            self._redis_client = aioredis.from_url(f"redis://{self.redis_host}")
        return self._redis_client

    async def add_failed_event(
        self,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Dict[str, Any],
        failure_reason: str,
        retry_policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF
    ) -> None:
        redis = await self._get_redis()
        dlq_entry = DLQEntry(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            metadata=metadata,
            failure_reason=failure_reason,
            failure_timestamp=time.time(),
            retry_count=0,
            max_retries=self.max_retries,
            retry_policy=retry_policy,
            next_retry_at=self._calculate_next_retry(0, retry_policy),
            dlq_timestamp=time.time()
        )
        await redis.hset(self.dlq_key, event_id, json.dumps(asdict(dlq_entry)))
        if dlq_entry.retry_count < dlq_entry.max_retries:
            await redis.zadd(self.retry_key, {event_id: dlq_entry.next_retry_at})
        logger.warning(f"Added failed event {event_id} to DLQ: {failure_reason}")

    def _calculate_next_retry(self, retry_count: int, policy: RetryPolicy) -> float:
        now = time.time()
        if policy == RetryPolicy.IMMEDIATE:
            return now
        elif policy == RetryPolicy.FIXED_DELAY:
            return now + self.base_delay
        elif policy == RetryPolicy.LINEAR_BACKOFF:
            delay = self.base_delay * (retry_count + 1)
            return now + min(delay, self.max_delay)
        elif policy == RetryPolicy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay * (2 ** retry_count)
            return now + min(delay, self.max_delay)
        else:
            return now + self.base_delay

    async def get_retryable_events(self, limit: int = 10) -> List[DLQEntry]:
        redis = await self._get_redis()
        now = time.time()
        event_ids = await redis.zrangebyscore(self.retry_key, 0, now, start=0, num=limit)
        events = []
        for event_id in event_ids:
            event_data = await redis.hget(self.dlq_key, event_id)
            if event_data:
                event_dict = json.loads(event_data)
                events.append(DLQEntry(**event_dict))
        return events

    async def retry_event(self, event_id: str, processor_func: Callable[[Dict[str, Any]], Any]) -> bool:
        redis = await self._get_redis()
        event_data = await redis.hget(self.dlq_key, event_id)
        if not event_data:
            return False
        event_dict = json.loads(event_data)
        dlq_entry = DLQEntry(**event_dict)
        try:
            await processor_func(dlq_entry.payload)
            await redis.hdel(self.dlq_key, event_id)
            await redis.zrem(self.retry_key, event_id)
            logger.info(f"Successfully retried event {event_id}")
            return True
        except Exception as e:
            dlq_entry.retry_count += 1
            if dlq_entry.retry_count < dlq_entry.max_retries:
                dlq_entry.next_retry_at = self._calculate_next_retry(
                    dlq_entry.retry_count, dlq_entry.retry_policy
                )
                await redis.hset(self.dlq_key, event_id, json.dumps(asdict(dlq_entry)))
                await redis.zadd(self.retry_key, {event_id: dlq_entry.next_retry_at})
                logger.warning(f"Retry {dlq_entry.retry_count} failed for event {event_id}: {e}")
            else:
                await redis.zrem(self.retry_key, event_id)
                logger.error(f"Event {event_id} exceeded max retries, moved to permanent DLQ")
            return False


# Saga Pattern
class SagaStepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"


@dataclass
class SagaStep:
    step_id: str
    service_name: str
    action: str
    payload: Dict[str, Any]
    compensation: str
    compensation_payload: Dict[str, Any]
    status: SagaStepStatus = SagaStepStatus.PENDING
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class SagaTransaction:
    saga_id: str
    correlation_id: str
    steps: List[SagaStep]
    status: str = "running"
    created_at: float = 0.0
    updated_at: float = 0.0
    error: Optional[str] = None


class SagaOrchestrator:
    """Orchestrates saga transactions across services."""

    def __init__(self, redis_host: str = "redis"):
        self.redis_host = redis_host
        self.saga_key = "saga:transactions"
        self.step_key = "saga:steps"
        self._redis_client: Optional[aioredis.Redis] = None
        self._service_clients = {}

    async def _get_redis(self) -> aioredis.Redis:
        if not aioredis:
            raise RuntimeError("aioredis not available")
        if not self._redis_client:
            self._redis_client = aioredis.from_url(f"redis://{self.redis_host}")
        return self._redis_client

    def set_service_client(self, service_name: str, client):
        self._service_clients[service_name] = client

    async def create_saga(self, correlation_id: str, steps: List[Dict[str, Any]]) -> str:
        saga_id = str(uuid.uuid4())
        now = time.time()
        saga_steps = []
        for i, step_data in enumerate(steps):
            step = SagaStep(
                step_id=f"{saga_id}:step_{i}",
                service_name=step_data["service_name"],
                action=step_data["action"],
                payload=step_data["payload"],
                compensation=step_data["compensation"],
                compensation_payload=step_data["compensation_payload"],
                max_retries=step_data.get("max_retries", 3)
            )
            saga_steps.append(step)
        saga = SagaTransaction(
            saga_id=saga_id,
            correlation_id=correlation_id,
            steps=saga_steps,
            created_at=now,
            updated_at=now
        )
        redis = await self._get_redis()
        await redis.hset(self.saga_key, saga_id, json.dumps(asdict(saga)))
        return saga_id

    async def get_saga_status(self, saga_id: str) -> Optional[Dict[str, Any]]:
        redis = await self._get_redis()
        saga_data = await redis.hget(self.saga_key, saga_id)
        if not saga_data:
            return None
        saga_dict = json.loads(saga_data)
        return saga_dict


# Event Replay
@dataclass
class ReplayableEvent:
    event_id: str
    event_type: str
    channel: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float
    correlation_id: Optional[str] = None
    source_service: Optional[str] = None
    replay_count: int = 0
    max_replays: int = 3


class EventReplayManager:
    """Manages event persistence and replay operations."""

    def __init__(
        self,
        redis_host: str = "redis",
        events_key: str = "events:persistent",
        max_events: int = 10000,
        retention_days: int = 30
    ):
        self.redis_host = redis_host
        self.events_key = events_key
        self.max_events = max_events
        self.retention_days = retention_days
        self._redis_client: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if not aioredis:
            raise RuntimeError("aioredis not available")
        if not self._redis_client:
            self._redis_client = aioredis.from_url(f"redis://{self.redis_host}")
        return self._redis_client

    async def persist_event(
        self,
        event_type: str,
        channel: str,
        payload: Dict[str, Any],
        metadata: Dict[str, Any],
        correlation_id: Optional[str] = None,
        source_service: Optional[str] = None
    ) -> str:
        event_id = str(uuid.uuid4())
        now = time.time()
        event = ReplayableEvent(
            event_id=event_id,
            event_type=event_type,
            channel=channel,
            payload=payload,
            metadata=metadata,
            timestamp=now,
            correlation_id=correlation_id,
            source_service=source_service
        )
        redis = await self._get_redis()
        await redis.hset(self.events_key, event_id, json.dumps(asdict(event)))
        return event_id

    async def replay_events(
        self,
        event_types: Optional[List[str]] = None,
        correlation_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[str]:
        redis = await self._get_redis()
        all_events = await redis.hgetall(self.events_key)
        events_to_replay = []
        for event_id, event_data in all_events.items():
            event_dict = json.loads(event_data)
            event = ReplayableEvent(**event_dict)
            if event_types and event.event_type not in event_types:
                continue
            if correlation_id and event.correlation_id != correlation_id:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            events_to_replay.append(event)
        events_to_replay.sort(key=lambda e: e.timestamp)
        events_to_replay = events_to_replay[:limit]
        replayed_ids = []
        for event in events_to_replay:
            # Simplified replay logic
            replayed_ids.append(event.event_id)
        logger.info(f"Replayed {len(replayed_ids)} events")
        return replayed_ids


class DLQProcessor:
    """Background processor for retrying failed events."""

    def __init__(self, dlq: DeadLetterQueue, processor_func: Callable):
        self.dlq = dlq
        self.processor_func = processor_func
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self, interval: float = 30.0):
        """Start the DLQ processor."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._process_loop(interval))
        logger.info("DLQ processor started")

    async def stop(self):
        """Stop the DLQ processor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DLQ processor stopped")

    async def _process_loop(self, interval: float):
        """Main processing loop for retrying events."""
        while self._running:
            try:
                events = await self.dlq.get_retryable_events(limit=5)
                for event in events:
                    await self.dlq.retry_event(event.event_id, self.processor_func)

                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in DLQ processor: {e}")
                await asyncio.sleep(interval)


# Saga Pattern for Doc Consistency Workflows
class DocConsistencySaga:
    """Saga patterns for documentation consistency workflows."""

    @staticmethod
    def create_ingestion_saga(correlation_id: str) -> List[Dict[str, Any]]:
        """Create saga for multi-source ingestion workflow."""
        return [
            {
                "service_name": "github-agent",
                "action": "POST /ingest",
                "payload": {"source": "github", "correlation_id": correlation_id},
                "compensation": "POST /ingest/rollback",
                "compensation_payload": {"source": "github", "correlation_id": correlation_id}
            },
            {
                "service_name": "jira-agent",
                "action": "POST /ingest",
                "payload": {"source": "jira", "correlation_id": correlation_id},
                "compensation": "POST /ingest/rollback",
                "compensation_payload": {"source": "jira", "correlation_id": correlation_id}
            },
            {
                "service_name": "confluence-agent",
                "action": "POST /ingest",
                "payload": {"source": "confluence", "correlation_id": correlation_id},
                "compensation": "POST /ingest/rollback",
                "compensation_payload": {"source": "confluence", "correlation_id": correlation_id}
            },
            {
                "service_name": "consistency-engine",
                "action": "POST /analyze",
                "payload": {"correlation_id": correlation_id},
                "compensation": "POST /analyze/rollback",
                "compensation_payload": {"correlation_id": correlation_id}
            }
        ]

    @staticmethod
    def create_notification_saga(correlation_id: str, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create saga for notification workflow."""
        return [
            {
                "service_name": "reporting",
                "action": "POST /reports/findings/notify-owners",
                "payload": {"findings": findings, "correlation_id": correlation_id},
                "compensation": "POST /reports/findings/notify-owners/rollback",
                "compensation_payload": {"findings": findings, "correlation_id": correlation_id}
            }
        ]
