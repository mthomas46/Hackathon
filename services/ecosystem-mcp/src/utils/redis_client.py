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

from ..config import settings

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
    FAILED_STREAM = "failed_queue"  # Dead letter queue
    
    # Consumer group name
    CONSUMER_GROUP = "workers"
    
    # Max retries before moving to DLQ
    MAX_RETRIES = 3
    
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
        try:
            if not self._connected:
                await self.connect()
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
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

