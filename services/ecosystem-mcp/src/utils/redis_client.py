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
from src.config.registry import get_registry

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client with Streams support.
    
    Provides:
    - Connection pooling (reuses TCP connections) ⚡ NEW
    - Producer: Add messages to streams
    - Consumer: Read messages from streams
    - Consumer groups for parallel processing
    - Retry logic with dead letter queue
    - Persistent queues (survives restarts)
    
    ✅ PHASE 2: Migrated to use configuration registry
    Stream names and consumer groups now loaded from service_registry.yaml
    """
    
    # ⚡ QUICK WIN 1.2: Class-level connection pool (shared across all instances)
    _connection_pool: Optional[redis.ConnectionPool] = None
    _pool_lock = asyncio.Lock()
    
    def __init__(self, redis_url: str | None = None):
        """
        Initialize Redis client.
        
        Args:
            redis_url: Redis connection string (uses settings if None)
        """
        # Load configuration from registry
        registry = get_registry()
        
        # Stream names from registry (was hardcoded)
        self.INGESTION_STREAM = registry.redis.streams.ingestion.name
        self.EMBEDDING_STREAM = registry.redis.streams.embedding.name
        self.RETRY_STREAM = registry.redis.streams.retry.name
        self.FAILED_STREAM = registry.redis.streams.dead_letter.name
        
        # Consumer group name from registry (was hardcoded)
        # ✅ This prevents today's consumer group mismatch issue!
        self.CONSUMER_GROUP = registry.redis.streams.ingestion.consumer_group
        
        # Retry configuration from registry (was hardcoded)
        self.MAX_RETRIES = registry.redis.retry.max_retries
        self.RETRY_BACKOFF_BASE = registry.redis.retry.backoff_base
        
        # Connection settings
        self.redis_url = redis_url or settings.redis_url
        self.client: Optional[redis.Redis] = None
        self._connected = False
        
        # ⚡ Max connections from settings (already exists!)
        self.max_connections = settings.redis_max_connections
        
        logger.info(f"✅ Redis client initialized from registry: {self._safe_url()}")
        logger.info(f"   📊 Connection pool: max={self.max_connections} connections")
        logger.debug(f"   Consumer group: {self.CONSUMER_GROUP}")
        logger.debug(f"   Ingestion stream: {self.INGESTION_STREAM}")
    
    def _safe_url(self) -> str:
        """Return Redis URL with password redacted."""
        url = self.redis_url
        if "@" in url and ":" in url.split("@")[0]:
            protocol, rest = url.split("://", 1)
            credentials, host = rest.split("@", 1)
            user, _ = credentials.split(":", 1)
            return f"{protocol}://{user}:***@{host}"
        return url
    
    async def _get_or_create_pool(self) -> redis.ConnectionPool:
        """
        Get or create Redis connection pool (singleton).
        
        ⚡ Connection pool is shared across all RedisClient instances.
        This dramatically reduces TCP handshake overhead.
        
        Returns:
            Redis connection pool
        """
        if RedisClient._connection_pool is None:
            async with RedisClient._pool_lock:
                # Double-check after acquiring lock
                if RedisClient._connection_pool is None:
                    logger.info(f"🔧 Creating Redis connection pool (max={self.max_connections})")
                    
                    RedisClient._connection_pool = redis.ConnectionPool.from_url(
                        self.redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                        max_connections=self.max_connections,
                        socket_keepalive=True,
                        socket_timeout=5.0,
                        retry_on_timeout=True,
                        health_check_interval=30  # Check health every 30s
                    )
                    
                    logger.info("✅ Redis connection pool created")
        
        return RedisClient._connection_pool
    
    async def connect(self) -> None:
        """Connect to Redis using connection pool."""
        if self._connected:
            return
        
        # ⚡ Use connection pool instead of direct connection
        pool = await self._get_or_create_pool()
        self.client = redis.Redis(connection_pool=pool)
        
        # Create consumer groups for all streams
        await self._ensure_consumer_groups()
        
        self._connected = True
        logger.info("Redis connected (using connection pool)")
    
    async def close(self) -> None:
        """Close Redis connection (but keep pool alive for reuse)."""
        if self.client:
            await self.client.close()
            self._connected = False
        logger.info("Redis connection closed (pool remains active)")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.
        
        Returns:
            Pool stats including active connections
        """
        if RedisClient._connection_pool is None:
            return {"status": "not_initialized"}
        
        pool = RedisClient._connection_pool
        return {
            "max_connections": self.max_connections,
            "in_use_connections": len(pool._in_use_connections) if hasattr(pool, '_in_use_connections') else "unknown",
            "available_connections": len(pool._available_connections) if hasattr(pool, '_available_connections') else "unknown",
            "status": "active"
        }
    
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
    
    async def ensure_consumer_group_exists(self, stream_name: str) -> bool:
        """
        Explicitly check and ensure consumer group exists for a stream.
        
        This is useful for auto-recovery after manual stream deletion.
        
        Args:
            stream_name: Name of the stream to check
        
        Returns:
            True if group exists or was created, False on error
        """
        try:
            # First, check if the group exists
            try:
                groups = await self.client.xinfo_groups(stream_name)
                for group in groups:
                    group_name = group.get(b"name", group.get("name"))
                    if group_name == self.CONSUMER_GROUP or group_name == self.CONSUMER_GROUP.encode():
                        logger.debug(f"✅ Consumer group '{self.CONSUMER_GROUP}' exists for {stream_name}")
                        return True
            except ResponseError as e:
                if "no such key" in str(e).lower():
                    # Stream doesn't exist yet, will be created
                    logger.info(f"Stream {stream_name} doesn't exist yet, will be created")
                else:
                    raise
            
            # Group doesn't exist, create it
            logger.warning(f"⚠️  Consumer group '{self.CONSUMER_GROUP}' missing for {stream_name}, creating...")
            await self.client.xgroup_create(
                stream_name,
                self.CONSUMER_GROUP,
                id="0",
                mkstream=True
            )
            logger.info(f"✅ Created consumer group '{self.CONSUMER_GROUP}' for {stream_name}")
            return True
            
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Group was created by another process, that's fine
                logger.info(f"✅ Consumer group '{self.CONSUMER_GROUP}' exists for {stream_name}")
                return True
            else:
                logger.error(f"❌ Failed to ensure consumer group for {stream_name}: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking consumer group for {stream_name}: {e}")
            return False
    
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
        
        Tries two strategies:
        1. Read new undelivered messages with XREADGROUP + ">"
        2. Claim pending messages from dead consumers with XAUTOCLAIM
        
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
        
        # Strategy 1: Try to read new undelivered messages
        messages = await self.client.xreadgroup(
            groupname=self.CONSUMER_GROUP,
            consumername=consumer_name,
            streams={stream: ">"},  # ">" reads new undelivered messages
            count=count,
            block=block
        )
        
        # Strategy 2: If no new messages, try to claim pending ones from dead consumers
        if not messages:
            logger.debug(f"No new messages, attempting to claim pending messages...")
            try:
                # XAUTOCLAIM returns: (next_id, [(message_id, data), ...], deleted_ids)
                claimed = await self.client.xautoclaim(
                    name=stream,
                    groupname=self.CONSUMER_GROUP,
                    consumername=consumer_name,
                    min_idle_time=5000,  # Claim messages idle for 5+ seconds
                    start_id="0-0",
                    count=count
                )
                
                if claimed and len(claimed) >= 2 and claimed[1]:
                    # claimed[1] is the list of (message_id, data) tuples
                    logger.info(f"✅ Claimed {len(claimed[1])} pending messages from dead consumers")
                    messages = [(stream, claimed[1])]
            except Exception as e:
                logger.warning(f"Failed to claim pending messages: {e}")
        
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

