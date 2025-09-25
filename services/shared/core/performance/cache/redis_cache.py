import logging
from ....infrastructure.utilities.error_handling import CacheException


class RedisCache(CacheBackend):
    """Redis cache implementation."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: Optional[int] = None,
        key_prefix: str = "cache:",
    ) -> None:
        """Initialize Redis cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            default_ttl: Default TTL in seconds
            key_prefix: Key prefix for namespacing
        """
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._default_ttl = default_ttl
        self._key_prefix = key_prefix
        self._redis = None
        self._lock = threading.RLock()

        # Initialize Redis connection
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                decode_responses=False,  # Keep as bytes for pickle
            )
        except ImportError:
            # Redis not available
            pass

    def _make_key(self, key: str) -> str:
        """Make prefixed cache key."""
        return f"{self._key_prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self._redis:
            return None

        try:
            cache_key = self._make_key(key)
            value_bytes = await self._redis.get(cache_key)
            if value_bytes:
                return pickle.loads(
                    value_bytes
                )  # nosec: Controlled data from Redis cache
        except Exception as e:
            # Cache miss or connection error - log and return None
            logger = logging.getLogger(__name__)
            logger.debug(f"Cache get failed for key {key}: {e}")
            pass  # Cache miss or error

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in Redis cache."""
        if not self._redis:
            return

        try:
            cache_key = self._make_key(key)
            value_bytes = pickle.dumps(
                value
            )  # nosec: Serializing controlled application data
            ttl_seconds = ttl or self._default_ttl

            if ttl_seconds:
                await self._redis.setex(cache_key, ttl_seconds, value_bytes)
            else:
                await self._redis.set(cache_key, value_bytes)
        except Exception:
            pass  # Ignore cache errors

    async def delete(self, key: str) -> None:
        """Delete value from Redis cache."""
        if not self._redis:
            return

        try:
            cache_key = self._make_key(key)
            await self._redis.delete(cache_key)
        except Exception:
            pass  # Ignore cache errors

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        if not self._redis:
            return False

        try:
            cache_key = self._make_key(key)
            return await self._redis.exists(cache_key) > 0
        except Exception:
            return False

    async def clear(self) -> None:
        """Clear all Redis cache entries with our prefix."""
        if not self._redis:
            return

        try:
            # Find all keys with our prefix
            pattern = f"{self._key_prefix}*"
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
        except Exception:
            pass  # Ignore cache errors

    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self._redis:
            return {"error": "Redis not available"}

        try:
            info = await self._redis.info()
            return {
                "redis_connected": True,
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "key_prefix": self._key_prefix,
                "default_ttl": self._default_ttl,
            }
        except Exception as e:
            return {"error": str(e)}


