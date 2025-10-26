"""
Redis client for Ecosystem MCP Service.

Provides Redis Streams for ingestion queue with consumer groups,
retry logic, and dead letter queue.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import redis.asyncio as redis
from redis.exceptions import ResponseError

from src.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client with Streams support.
    
    Provides:
    - Producer: Add messages to streams
    - Consumer: Read messages from streams
    - Consumer groups for parallel processing
    - Retry logic with dead letter queue
    - Persistent queues (survives restarts)
    """
    
    # Stream names
    INGESTION_STREAM = "ingestion_queue"
    EMBEDDING_STREAM = "embedding_queue"
    RETRY_STREAM = "retry_queue"  # 🆕 Transient failures with retry logic
    FAILED_STREAM = "failed_queue"  # Dead letter queue (permanent failures)
    
    # Consumer group name
    CONSUMER_GROUP = "workers"
    
    # Retry configuration
    MAX_RETRIES = 5  # 🆕 Increased from 3 to 5
    RETRY_BACKOFF_BASE = 2  # 🆕 Exponential base (2^n minutes)
    
    def __init__(self, redis_url: str | None = None):
        """
        Initialize Redis client.
        
        Args:
            redis_url: Redis connection string (uses settings if None)
        """
        self.redis_url = redis_url or settings.redis_url
        self.client: Optional[redis.Redis] = None
        self._connected = False
        
        logger.info(f"Redis client initialized: {self._safe_url()}")
    
    def _safe_url(self) -> str:
        """Return Redis URL with password redacted."""
        url = self.redis_url
        if "@" in url and ":" in url.split("@")[0]:
            protocol, rest = url.split("://", 1)
            credentials, host = rest.split("@", 1)
            user, _ = credentials.split(":", 1)
            return f"{protocol}://{user}:***@{host}"
        return url
    
    async def connect(self) -> None:
        """Connect to Redis."""
        if self._connected:
            return
        
        self.client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_max_connections
        )
        
        # Create consumer groups for all streams
        await self._ensure_consumer_groups()
        
        self._connected = True
        logger.info("Redis connected")
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            self._connected = False
        logger.info("Redis connection closed")
    
    async def _ensure_consumer_groups(self) -> None:
        """
        Ensure consumer groups exist for all streams.
        
        Creates groups if they don't exist.
        """
        streams = [
            self.INGESTION_STREAM,
            self.EMBEDDING_STREAM,
            self.RETRY_STREAM,  # 🆕 Retry queue
            self.FAILED_STREAM
        ]
        
        for stream in streams:
            try:
                await self.client.xgroup_create(
                    stream,
                    self.CONSUMER_GROUP,
                    id="0",
                    mkstream=True
                )
                logger.info(f"Created consumer group for {stream}")
            except ResponseError as e:
                if "BUSYGROUP" in str(e):
                    # Group already exists
                    pass
                else:
                    raise
    
    async def add_to_stream(
        self,
        stream: str,
        data: Dict[str, Any],
        max_len: int = 10000
    ) -> str:
        """
        Add message to stream.
        
        Args:
            stream: Stream name
            data: Message data (will be JSON serialized)
            max_len: Maximum stream length (oldest messages dropped)
        
        Returns:
            Message ID
        """
        if not self._connected:
            await self.connect()
        
        # Serialize data
        serialized = {
            k: json.dumps(v) if not isinstance(v, str) else v
            for k, v in data.items()
        }
        
        # Add timestamp
        serialized["_timestamp"] = datetime.utcnow().isoformat()
        
        # Add to stream with max length
        message_id = await self.client.xadd(
            stream,
            serialized,
            maxlen=max_len,
            approximate=True
        )
        
        return message_id
    
    async def read_from_stream(
        self,
        stream: str,
        consumer_name: str,
        count: int = 1,
        block: int = 1000
    ) -> List[tuple[str, Dict[str, Any]]]:
        """
        Read messages from stream using consumer group.
        
        Args:
            stream: Stream name
            consumer_name: Unique consumer name
            count: Number of messages to read
            block: Block time in milliseconds (0 = non-blocking)
        
        Returns:
            List of (message_id, data) tuples
        """
        if not self._connected:
            await self.connect()
        
        # Read from stream
        messages = await self.client.xreadgroup(
            groupname=self.CONSUMER_GROUP,
            consumername=consumer_name,
            streams={stream: ">"},
            count=count,
            block=block
        )
        
        if not messages:
            return []
        
        # Parse messages
        parsed = []
        for stream_name, message_list in messages:
            for message_id, data in message_list:
                # Deserialize data
                deserialized = {}
                for k, v in data.items():
                    if k.startswith("_"):
                        deserialized[k] = v
                        continue
                    
                    try:
                        deserialized[k] = json.loads(v)
                    except (json.JSONDecodeError, TypeError):
                        deserialized[k] = v
                
                parsed.append((message_id, deserialized))
        
        return parsed
    
    async def ack_message(
        self,
        stream: str,
        message_id: str
    ) -> None:
        """
        Acknowledge message processing.
        
        Args:
            stream: Stream name
            message_id: Message ID to acknowledge
        """
        if not self._connected:
            await self.connect()
        
        await self.client.xack(stream, self.CONSUMER_GROUP, message_id)
    
    async def move_to_dlq(
        self,
        original_stream: str,
        message_id: str,
        data: Dict[str, Any],
        error: str
    ) -> None:
        """
        Move failed message to dead letter queue.
        
        Args:
            original_stream: Original stream name
            message_id: Original message ID
            data: Message data
            error: Error message
        """
        # Add metadata
        dlq_data = {
            **data,
            "_original_stream": original_stream,
            "_original_id": message_id,
            "_error": error,
            "_failed_at": datetime.utcnow().isoformat()
        }
        
        # Add to DLQ
        await self.add_to_stream(self.FAILED_STREAM, dlq_data)
        
        # Acknowledge original message
        await self.ack_message(original_stream, message_id)
        
        logger.warning(
            f"Moved message {message_id} to DLQ: {error}"
        )
    
    async def get_stream_length(self, stream: str) -> int:
        """
        Get number of messages in stream.
        
        Args:
            stream: Stream name
        
        Returns:
            Number of messages
        """
        if not self._connected:
            await self.connect()
        
        return await self.client.xlen(stream)
    
    async def get_pending_count(
        self,
        stream: str
    ) -> int:
        """
        Get number of pending (unacknowledged) messages.
        
        Args:
            stream: Stream name
        
        Returns:
            Number of pending messages
        """
        if not self._connected:
            await self.connect()
        
        pending = await self.client.xpending(stream, self.CONSUMER_GROUP)
        return pending["pending"]
    
    async def health_check(self) -> bool:
        """
        Check if Redis is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        from .retry import retry_health_check
        
        @retry_health_check
        async def _check():
            if not self._connected:
                await self.connect()
            await self.client.ping()
            return True
        
        try:
            return await _check()
        except Exception as e:
            logger.error(f"Redis health check failed after retries: {e}")
            return False
    
    async def clear_stream(self, stream: str) -> None:
        """
        Clear all messages from stream.
        
        ⚠️ DANGER: This will delete all data!
        """
        if not self._connected:
            await self.connect()
        
        await self.client.xtrim(stream, maxlen=0, approximate=False)
        logger.warning(f"Cleared stream: {stream}")
    
    # Cache operations (for response caching)
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Value if exists, None otherwise
        """
        if not self._connected:
            await self.connect()
        
        return await self.client.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to store
            ex: Expiration time in seconds (None = no expiration)
        """
        if not self._connected:
            await self.connect()
        
        await self.client.set(key, value, ex=ex)
    
    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys.
        
        Args:
            *keys: Keys to delete
        
        Returns:
            Number of keys deleted
        """
        if not self._connected:
            await self.connect()
        
        return await self.client.delete(*keys)
    
    async def keys(self, pattern: str) -> List[str]:
        """
        Find keys matching pattern.
        
        Args:
            pattern: Pattern to match (e.g., "cache:*")
        
        Returns:
            List of matching keys
        
        Note:
            For production use with large datasets, use SCAN instead.
        """
        if not self._connected:
            await self.connect()
        
        return await self.client.keys(pattern)
    
    # ============================================================================
    # 🆕 PHASE 1: Retry Infrastructure Methods
    # ============================================================================
    
    async def enqueue_failed_document(
        self,
        job_id: str,
        document_info: Dict[str, Any],
        error_type: str,
        error_message: str,
        retry_count: int = 0
    ) -> str:
        """
        Enqueue failed document for retry.
        
        Args:
            job_id: Parent job ID
            document_info: Document details (file_path, mode, etc.)
            error_type: Classified error type
            error_message: Full error message
            retry_count: Current retry count
        
        Returns:
            Message ID
        """
        from datetime import datetime, timedelta
        
        # Calculate next retry time with exponential backoff
        backoff_minutes = self.RETRY_BACKOFF_BASE ** retry_count
        next_retry_at = datetime.utcnow() + timedelta(minutes=backoff_minutes)
        
        data = {
            "job_id": job_id,
            "document_info": json.dumps(document_info),
            "error_type": error_type,
            "error_message": error_message,
            "retry_count": str(retry_count),
            "failed_at": datetime.utcnow().isoformat(),
            "next_retry_at": next_retry_at.isoformat()
        }
        
        message_id = await self.add_to_stream(
            self.RETRY_STREAM,
            data,
            max_len=50000  # Higher limit for retry queue
        )
        
        logger.info(
            f"📝 Enqueued document for retry: {document_info.get('file_path', 'unknown')} "
            f"(retry {retry_count + 1}/{self.MAX_RETRIES}, "
            f"next attempt in {backoff_minutes}min)"
        )
        
        return message_id
    
    async def move_to_dead_letter(
        self,
        job_id: str,
        document_info: Dict[str, Any],
        error_type: str,
        error_message: str,
        retry_count: int
    ) -> str:
        """
        Move document to dead letter queue (permanent failure).
        
        Args:
            job_id: Parent job ID
            document_info: Document details
            error_type: Classified error type
            error_message: Full error message
            retry_count: Number of retries attempted
        
        Returns:
            Message ID
        """
        from datetime import datetime
        
        data = {
            "job_id": job_id,
            "document_info": json.dumps(document_info),
            "error_type": error_type,
            "error_message": error_message,
            "retry_count": str(retry_count),
            "failed_at": datetime.utcnow().isoformat(),
            "moved_to_dlq_at": datetime.utcnow().isoformat()
        }
        
        message_id = await self.add_to_stream(
            self.FAILED_STREAM,
            data,
            max_len=100000  # Keep dead letters longer
        )
        
        logger.warning(
            f"💀 Moved to dead letter queue: {document_info.get('file_path', 'unknown')} "
            f"after {retry_count} retries (error: {error_type})"
        )
        
        return message_id


# Global Redis instance
_redis_client: RedisClient | None = None


def get_redis_client() -> RedisClient:
    """
    Get global Redis instance.
    
    Creates instance on first call.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


async def init_redis():
    """Initialize Redis on application startup."""
    redis_client = get_redis_client()
    await redis_client.connect()
    healthy = await redis_client.health_check()
    if not healthy:
        from .exceptions import StorageError
        raise StorageError("Redis is not accessible")
    logger.info("Redis initialized successfully")


async def close_redis():
    """Close Redis on application shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
    logger.info("Redis closed")

