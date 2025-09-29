"""Dead Letter Queue - Handles failed events and retry logic."""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .event_bus import DomainEvent, EventEnvelope


@dataclass
class DeadLetterEntry:
    """Entry in the dead letter queue."""

    event: DomainEvent
    envelope: EventEnvelope
    error_message: str
    error_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    max_retries: int = 3
    next_retry_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize entry."""
        if self.metadata is None:
            self.metadata = {}

    def should_retry(self) -> bool:
        """Check if this entry should be retried."""
        if self.retry_count >= self.max_retries:
            return False

        if self.next_retry_time and datetime.utcnow() < self.next_retry_time:
            return False

        return True

    def increment_retry(self, delay_seconds: int = 60) -> None:
        """Increment retry count and set next retry time."""
        self.retry_count += 1
        self.next_retry_time = datetime.utcnow() + timedelta(seconds=delay_seconds)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'event': self.event.to_dict(),
            'envelope': {
                'topic': self.envelope.topic,
                'partition_key': self.envelope.partition_key,
                'headers': self.envelope.headers,
                'retry_count': self.envelope.retry_count,
                'max_retries': self.envelope.max_retries
            },
            'error_message': self.error_message,
            'error_type': self.error_type,
            'timestamp': self.timestamp.isoformat(),
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'next_retry_time': self.next_retry_time.isoformat() if self.next_retry_time else None,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeadLetterEntry':
        """Create from dictionary."""
        # Reconstruct event
        event_data = data['event']
        event = DomainEvent.from_dict(event_data)

        # Reconstruct envelope
        envelope_data = data['envelope']
        envelope = EventEnvelope(
            event=event,
            topic=envelope_data['topic'],
            partition_key=envelope_data.get('partition_key'),
            headers=envelope_data.get('headers', {}),
            retry_count=envelope_data.get('retry_count', 0),
            max_retries=envelope_data.get('max_retries', 3)
        )

        # Handle timestamp
        timestamp = datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.utcnow()

        # Handle next retry time
        next_retry_time = None
        if data.get('next_retry_time'):
            next_retry_time = datetime.fromisoformat(data['next_retry_time'])

        return cls(
            event=event,
            envelope=envelope,
            error_message=data['error_message'],
            error_type=data['error_type'],
            timestamp=timestamp,
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            next_retry_time=next_retry_time,
            metadata=data.get('metadata', {})
        )


class DeadLetterQueue(ABC):
    """Abstract base class for dead letter queues."""

    @abstractmethod
    async def add_event(
        self,
        event: DomainEvent,
        error_message: str,
        envelope: Optional[EventEnvelope] = None,
        error_type: Optional[str] = None
    ) -> None:
        """Add event to dead letter queue."""
        pass

    @abstractmethod
    async def get_pending_events(self, limit: int = 100) -> List[DeadLetterEntry]:
        """Get events pending retry."""
        pass

    @abstractmethod
    async def mark_retry_successful(self, event_id: str) -> bool:
        """Mark retry as successful and remove from queue."""
        pass

    @abstractmethod
    async def mark_retry_failed(self, event_id: str, error_message: str) -> bool:
        """Mark retry as failed and update entry."""
        pass

    @abstractmethod
    async def get_failed_events(self, limit: int = 100) -> List[DeadLetterEntry]:
        """Get permanently failed events."""
        pass

    @abstractmethod
    async def purge_old_events(self, days_old: int = 30) -> int:
        """Purge events older than specified days."""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        pass


class InMemoryDeadLetterQueue(DeadLetterQueue):
    """In-memory dead letter queue for testing and development."""

    def __init__(self, max_size: int = 10000):
        """Initialize in-memory dead letter queue."""
        self.entries: List[DeadLetterEntry] = []
        self.max_size = max_size

    async def add_event(
        self,
        event: DomainEvent,
        error_message: str,
        envelope: Optional[EventEnvelope] = None,
        error_type: Optional[str] = None
    ) -> None:
        """Add event to queue."""
        if envelope is None:
            envelope = EventEnvelope(event=event, topic="unknown")

        entry = DeadLetterEntry(
            event=event,
            envelope=envelope,
            error_message=error_message,
            error_type=error_type or "UnknownError"
        )

        self.entries.append(entry)

        # Maintain max size
        if len(self.entries) > self.max_size:
            # Remove oldest entries
            self.entries = self.entries[-self.max_size:]

    async def get_pending_events(self, limit: int = 100) -> List[DeadLetterEntry]:
        """Get events pending retry."""
        current_time = datetime.utcnow()
        pending = [
            entry for entry in self.entries
            if entry.should_retry() and
            (entry.next_retry_time is None or entry.next_retry_time <= current_time)
        ]

        return pending[:limit]

    async def mark_retry_successful(self, event_id: str) -> bool:
        """Mark retry as successful."""
        for i, entry in enumerate(self.entries):
            if entry.event.event_id == event_id:
                del self.entries[i]
                return True
        return False

    async def mark_retry_failed(self, event_id: str, error_message: str) -> bool:
        """Mark retry as failed."""
        for entry in self.entries:
            if entry.event.event_id == event_id:
                entry.increment_retry()
                entry.error_message = error_message
                entry.metadata['last_retry'] = datetime.utcnow().isoformat()
                return True
        return False

    async def get_failed_events(self, limit: int = 100) -> List[DeadLetterEntry]:
        """Get permanently failed events."""
        failed = [
            entry for entry in self.entries
            if entry.retry_count >= entry.max_retries
        ]

        return failed[:limit]

    async def purge_old_events(self, days_old: int = 30) -> int:
        """Purge events older than specified days."""
        cutoff_time = datetime.utcnow() - timedelta(days=days_old)
        original_count = len(self.entries)

        self.entries = [
            entry for entry in self.entries
            if entry.timestamp > cutoff_time
        ]

        purged_count = original_count - len(self.entries)
        return purged_count

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        current_time = datetime.utcnow()
        pending_count = len([
            entry for entry in self.entries
            if entry.should_retry() and
            (entry.next_retry_time is None or entry.next_retry_time <= current_time)
        ])

        failed_count = len([
            entry for entry in self.entries
            if entry.retry_count >= entry.max_retries
        ])

        retrying_count = len([
            entry for entry in self.entries
            if entry.retry_count > 0 and entry.retry_count < entry.max_retries
        ])

        return {
            'total_entries': len(self.entries),
            'pending_retry': pending_count,
            'permanently_failed': failed_count,
            'currently_retrying': retrying_count,
            'max_size': self.max_size,
            'utilization': len(self.entries) / self.max_size if self.max_size > 0 else 0
        }


class RedisDeadLetterQueue(DeadLetterQueue):
    """Redis-based dead letter queue for production."""

    def __init__(
        self,
        redis_client=None,
        queue_key: str = "dead_letter_queue",
        failed_key: str = "failed_events",
        max_size: int = 10000
    ):
        """Initialize Redis dead letter queue."""
        self.redis = redis_client
        self.queue_key = queue_key
        self.failed_key = failed_key
        self.max_size = max_size

    async def add_event(
        self,
        event: DomainEvent,
        error_message: str,
        envelope: Optional[EventEnvelope] = None,
        error_type: Optional[str] = None
    ) -> None:
        """Add event to Redis queue."""
        if not self.redis:
            raise RuntimeError("Redis client not configured")

        if envelope is None:
            envelope = EventEnvelope(event=event, topic="unknown")

        entry = DeadLetterEntry(
            event=event,
            envelope=envelope,
            error_message=error_message,
            error_type=error_type or "UnknownError"
        )

        # Add to queue
        entry_data = json.dumps(entry.to_dict())
        await self.redis.lpush(self.queue_key, entry_data)

        # Maintain max size
        await self.redis.ltrim(self.queue_key, 0, self.max_size - 1)

    async def get_pending_events(self, limit: int = 100) -> List[DeadLetterEntry]:
        """Get events pending retry from Redis."""
        if not self.redis:
            return []

        # Get entries from queue
        entries_data = await self.redis.lrange(self.queue_key, 0, limit - 1)

        entries = []
        current_time = datetime.utcnow()

        for entry_data in entries_data:
            try:
                entry_dict = json.loads(entry_data)
                entry = DeadLetterEntry.from_dict(entry_dict)

                if entry.should_retry():
                    entries.append(entry)
                else:
                    # Move to failed queue if max retries exceeded
                    await self._move_to_failed_queue(entry)

            except Exception as e:
                print(f"Error parsing dead letter entry: {e}")
                continue

        return entries

    async def mark_retry_successful(self, event_id: str) -> bool:
        """Mark retry as successful."""
        if not self.redis:
            return False

        # Remove from queue
        entries_data = await self.redis.lrange(self.queue_key, 0, -1)

        for i, entry_data in enumerate(entries_data):
            try:
                entry_dict = json.loads(entry_data)
                if entry_dict['event']['event_id'] == event_id:
                    await self.redis.lrem(self.queue_key, 1, entry_data)
                    return True
            except Exception:
                continue

        return False

    async def mark_retry_failed(self, event_id: str, error_message: str) -> bool:
        """Mark retry as failed."""
        if not self.redis:
            return False

        # Find and update entry
        entries_data = await self.redis.lrange(self.queue_key, 0, -1)

        for entry_data in entries_data:
            try:
                entry_dict = json.loads(entry_data)
                if entry_dict['event']['event_id'] == event_id:
                    entry = DeadLetterEntry.from_dict(entry_dict)
                    entry.increment_retry()
                    entry.error_message = error_message
                    entry.metadata['last_retry'] = datetime.utcnow().isoformat()

                    # If max retries exceeded, move to failed queue
                    if entry.retry_count >= entry.max_retries:
                        await self._move_to_failed_queue(entry)
                        await self.redis.lrem(self.queue_key, 1, entry_data)
                    else:
                        # Update entry in queue
                        updated_data = json.dumps(entry.to_dict())
                        await self.redis.lset(self.queue_key, entries_data.index(entry_data), updated_data)

                    return True
            except Exception:
                continue

        return False

    async def get_failed_events(self, limit: int = 100) -> List[DeadLetterEntry]:
        """Get permanently failed events from Redis."""
        if not self.redis:
            return []

        # Get failed entries
        failed_data = await self.redis.lrange(self.failed_key, 0, limit - 1)

        entries = []
        for entry_data in failed_data:
            try:
                entry_dict = json.loads(entry_data)
                entry = DeadLetterEntry.from_dict(entry_dict)
                entries.append(entry)
            except Exception as e:
                print(f"Error parsing failed entry: {e}")
                continue

        return entries

    async def purge_old_events(self, days_old: int = 30) -> int:
        """Purge events older than specified days."""
        if not self.redis:
            return 0

        cutoff_time = datetime.utcnow() - timedelta(days=days_old)
        total_purged = 0

        # Purge from main queue
        entries_data = await self.redis.lrange(self.queue_key, 0, -1)
        remaining_entries = []

        for entry_data in entries_data:
            try:
                entry_dict = json.loads(entry_data)
                entry_timestamp = datetime.fromisoformat(entry_dict['timestamp'])

                if entry_timestamp > cutoff_time:
                    remaining_entries.append(entry_data)
                else:
                    total_purged += 1
            except Exception:
                # Keep malformed entries
                remaining_entries.append(entry_data)

        # Update queue with remaining entries
        if remaining_entries:
            await self.redis.delete(self.queue_key)
            await self.redis.rpush(self.queue_key, *remaining_entries)

        # Also purge from failed queue
        failed_data = await self.redis.lrange(self.failed_key, 0, -1)
        remaining_failed = []

        for entry_data in failed_data:
            try:
                entry_dict = json.loads(entry_data)
                entry_timestamp = datetime.fromisoformat(entry_dict['timestamp'])

                if entry_timestamp > cutoff_time:
                    remaining_failed.append(entry_data)
                else:
                    total_purged += 1
            except Exception:
                remaining_failed.append(entry_data)

        if remaining_failed:
            await self.redis.delete(self.failed_key)
            await self.redis.rpush(self.failed_key, *remaining_failed)

        return total_purged

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics from Redis."""
        if not self.redis:
            return {
                'total_entries': 0,
                'pending_retry': 0,
                'permanently_failed': 0,
                'error': 'Redis client not configured'
            }

        try:
            queue_length = await self.redis.llen(self.queue_key)
            failed_length = await self.redis.llen(self.failed_key)

            # Get some entries to analyze
            entries_data = await self.redis.lrange(self.queue_key, 0, 100)
            current_time = datetime.utcnow()

            pending_count = 0
            retrying_count = 0

            for entry_data in entries_data:
                try:
                    entry_dict = json.loads(entry_data)
                    retry_count = entry_dict.get('retry_count', 0)
                    max_retries = entry_dict.get('max_retries', 3)

                    if retry_count > 0:
                        retrying_count += 1

                    if retry_count < max_retries:
                        next_retry = entry_dict.get('next_retry_time')
                        if not next_retry or datetime.fromisoformat(next_retry) <= current_time:
                            pending_count += 1

                except Exception:
                    continue

            return {
                'total_entries': queue_length,
                'pending_retry': min(pending_count, queue_length),  # Estimate based on sample
                'permanently_failed': failed_length,
                'currently_retrying': min(retrying_count, queue_length),
                'max_size': self.max_size,
                'queue_utilization': queue_length / self.max_size if self.max_size > 0 else 0
            }

        except Exception as e:
            return {
                'total_entries': 0,
                'error': str(e)
            }

    async def _move_to_failed_queue(self, entry: DeadLetterEntry) -> None:
        """Move entry to failed events queue."""
        if not self.redis:
            return

        entry_data = json.dumps(entry.to_dict())
        await self.redis.lpush(self.failed_key, entry_data)

        # Maintain max size for failed queue too
        await self.redis.ltrim(self.failed_key, 0, self.max_size - 1)


class DeadLetterQueueProcessor:
    """Processor for handling dead letter queue retries."""

    def __init__(
        self,
        dead_letter_queue: DeadLetterQueue,
        event_bus=None,
        retry_interval: int = 60,
        batch_size: int = 10
    ):
        """Initialize dead letter queue processor."""
        self.dead_letter_queue = dead_letter_queue
        self.event_bus = event_bus
        self.retry_interval = retry_interval
        self.batch_size = batch_size
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start processing dead letter queue."""
        self._running = True
        self._processing_task = asyncio.create_task(self._process_queue())

    async def stop(self) -> None:
        """Stop processing dead letter queue."""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

    async def _process_queue(self) -> None:
        """Process dead letter queue periodically."""
        while self._running:
            try:
                # Get pending events
                pending_events = await self.dead_letter_queue.get_pending_events(self.batch_size)

                if not pending_events:
                    await asyncio.sleep(self.retry_interval)
                    continue

                # Retry events
                for entry in pending_events:
                    try:
                        # Republish event
                        await self.event_bus.publish(entry.envelope)

                        # Mark as successful
                        await self.dead_letter_queue.mark_retry_successful(entry.event.event_id)

                        print(f"Successfully retried event {entry.event.event_id}")

                    except Exception as e:
                        # Mark as failed
                        await self.dead_letter_queue.mark_retry_failed(
                            entry.event.event_id,
                            str(e)
                        )
                        print(f"Retry failed for event {entry.event.event_id}: {e}")

                # Wait before next batch
                await asyncio.sleep(self.retry_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing dead letter queue: {e}")
                await asyncio.sleep(self.retry_interval)
