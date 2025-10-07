"""Redis Event Repository Implementation."""

import json
import logging
from typing import List, Optional
from datetime import datetime
import redis.asyncio as aioredis

from ...domain.entities.document_event import DocumentEvent
from ...domain.value_objects.event_status import EventStatus
from ...domain.repositories.event_repository import EventRepository

logger = logging.getLogger(__name__)


class RedisEventRepository(EventRepository):
    """
    Redis implementation of event repository.
    
    Stores events in Redis with multiple indices for querying.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize repository.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        logger.info(f"Connecting to Redis: {self.redis_url}")
        self._redis = await aioredis.from_url(self.redis_url, decode_responses=True)
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
    
    def _get_event_key(self, event_id: str) -> str:
        """Get Redis key for event."""
        return f"event:{event_id}"
    
    def _get_status_index_key(self, status: EventStatus) -> str:
        """Get Redis key for status index."""
        return f"events:status:{status.value}"
    
    def _get_document_index_key(self, document_id: str) -> str:
        """Get Redis key for document index."""
        return f"events:document:{document_id}"
    
    async def save(self, event: DocumentEvent) -> None:
        """Save event."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        event_key = self._get_event_key(event.event_id)
        event_data = json.dumps(event.to_dict())
        
        # Save event
        await self._redis.set(event_key, event_data)
        
        # Add to status index
        status_key = self._get_status_index_key(event.status)
        await self._redis.sadd(status_key, event.event_id)
        
        # Add to document index
        doc_key = self._get_document_index_key(event.document_id)
        await self._redis.sadd(doc_key, event.event_id)
        
        logger.debug(f"Saved event {event.event_id}")
    
    async def get_by_id(self, event_id: str) -> Optional[DocumentEvent]:
        """Get event by ID."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        event_key = self._get_event_key(event_id)
        event_data = await self._redis.get(event_key)
        
        if not event_data:
            return None
        
        data = json.loads(event_data)
        return DocumentEvent.from_dict(data)
    
    async def get_by_document_id(self, document_id: str) -> List[DocumentEvent]:
        """Get all events for a document."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        doc_key = self._get_document_index_key(document_id)
        event_ids = await self._redis.smembers(doc_key)
        
        events = []
        for event_id in event_ids:
            event = await self.get_by_id(event_id)
            if event:
                events.append(event)
        
        return events
    
    async def get_by_status(
        self,
        status: EventStatus,
        limit: int = 100
    ) -> List[DocumentEvent]:
        """Get events by status."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        status_key = self._get_status_index_key(status)
        event_ids = await self._redis.srandmember(status_key, limit)
        
        if not event_ids:
            return []
        
        # Handle single result
        if isinstance(event_ids, str):
            event_ids = [event_ids]
        
        events = []
        for event_id in event_ids:
            event = await self.get_by_id(event_id)
            if event:
                events.append(event)
        
        return events
    
    async def get_by_correlation_id(self, correlation_id: str) -> List[DocumentEvent]:
        """Get events by correlation ID."""
        # Note: This requires scanning all events - not efficient at scale
        # In production, would add correlation_id index
        logger.warning("get_by_correlation_id requires full scan - use sparingly")
        return []
    
    async def get_failed_events(
        self,
        can_retry: bool = True,
        limit: int = 100
    ) -> List[DocumentEvent]:
        """Get failed events."""
        events = await self.get_by_status(EventStatus.FAILED, limit)
        
        if can_retry:
            events = [e for e in events if e.can_retry()]
        
        return events
    
    async def get_events_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[DocumentEvent]:
        """Get events within time range."""
        # Note: This requires scanning - not efficient at scale
        # In production, would use sorted set with timestamp scores
        logger.warning("get_events_by_time_range requires full scan - use sparingly")
        return []
    
    async def update(self, event: DocumentEvent) -> None:
        """Update event."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        # Get old event to update indices
        old_event = await self.get_by_id(event.event_id)
        
        if old_event and old_event.status != event.status:
            # Remove from old status index
            old_status_key = self._get_status_index_key(old_event.status)
            await self._redis.srem(old_status_key, event.event_id)
        
        # Save updated event (this will add to new status index)
        await self.save(event)
        
        logger.debug(f"Updated event {event.event_id}")
    
    async def delete(self, event_id: str) -> bool:
        """Delete event."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        # Get event to update indices
        event = await self.get_by_id(event_id)
        if not event:
            return False
        
        # Remove from indices
        status_key = self._get_status_index_key(event.status)
        await self._redis.srem(status_key, event_id)
        
        doc_key = self._get_document_index_key(event.document_id)
        await self._redis.srem(doc_key, event_id)
        
        # Delete event
        event_key = self._get_event_key(event_id)
        await self._redis.delete(event_key)
        
        logger.debug(f"Deleted event {event_id}")
        return True
    
    async def count_by_status(self, status: EventStatus) -> int:
        """Count events by status."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        status_key = self._get_status_index_key(status)
        return await self._redis.scard(status_key)

