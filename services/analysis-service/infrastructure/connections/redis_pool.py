"""Redis Connection Pool - Redis connection pooling for caching and messaging."""

import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .connection_pool import ConnectionPool, ConnectionPoolConfig, PooledConnection


class RedisConnectionPool(ConnectionPool):
    """Redis connection pool implementation."""

    def __init__(
        self,
        config: ConnectionPoolConfig,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        socket_timeout: Optional[float] = None,
        socket_connect_timeout: Optional[float] = None,
        socket_keepalive: bool = True,
        socket_keepalive_options: Optional[Dict[int, Union[int, bytes]]] = None,
        health_check_interval: int = 30,
        **kwargs
    ):
        """Initialize Redis connection pool."""
        super().__init__(config)
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.socket_keepalive = socket_keepalive
        self.socket_keepalive_options = socket_keepalive_options or {}
        self.health_check_interval = health_check_interval
        self.redis_kwargs = kwargs

        # Import redis here to make it optional
        try:
            import redis.asyncio as aioredis
            self.aioredis = aioredis
        except ImportError:
            try:
                import redis
                self.aioredis = redis
            except ImportError:
                raise ImportError("redis or redis-py is required for Redis connection pooling")

    async def create_connection(self) -> Any:
        """Create Redis connection."""
        return self.aioredis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            socket_timeout=self.socket_timeout,
            socket_connect_timeout=self.socket_connect_timeout,
            socket_keepalive=self.socket_keepalive,
            socket_keepalive_options=self.socket_keepalive_options,
            **self.redis_kwargs
        )

    async def validate_connection(self, connection: Any) -> bool:
        """Validate Redis connection."""
        try:
            # Simple ping to test connection
            return await connection.ping()
        except Exception:
            return False

    async def close_connection(self, connection: Any) -> None:
        """Close Redis connection."""
        try:
            await connection.close()
        except Exception:
            pass  # Ignore errors during cleanup

    async def execute_command(self, command: str, *args, **kwargs) -> Any:
        """Execute Redis command using pooled connection."""
        async with self.acquire() as pooled_conn:
            redis_conn = pooled_conn.connection

            # Get the command method
            command_method = getattr(redis_conn, command.lower())
            return await command_method(*args, **kwargs)

    # Convenience methods for common Redis operations
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        return await self.execute_command('GET', key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set value in Redis."""
        return await self.execute_command('SET', key, value, ex=ex)

    async def delete(self, *keys: str) -> int:
        """Delete keys from Redis."""
        return await self.execute_command('DELETE', *keys)

    async def exists(self, *keys: str) -> int:
        """Check if keys exist in Redis."""
        return await self.execute_command('EXISTS', *keys)

    async def expire(self, key: str, time: int) -> bool:
        """Set key expiration."""
        return await self.execute_command('EXPIRE', key, time)

    async def ttl(self, key: str) -> int:
        """Get key time-to-live."""
        return await self.execute_command('TTL', key)

    async def incr(self, key: str) -> int:
        """Increment key value."""
        return await self.execute_command('INCR', key)

    async def decr(self, key: str) -> int:
        """Decrement key value."""
        return await self.execute_command('DECR', key)

    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field value."""
        return await self.execute_command('HGET', key, field)

    async def hset(self, key: str, field: str, value: Any) -> bool:
        """Set hash field value."""
        return await self.execute_command('HSET', key, field, value)

    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields."""
        return await self.execute_command('HGETALL', key)

    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to list left."""
        return await self.execute_command('LPUSH', key, *values)

    async def rpush(self, key: str, *values: Any) -> int:
        """Push values to list right."""
        return await self.execute_command('RPUSH', key, *values)

    async def lpop(self, key: str) -> Optional[str]:
        """Pop value from list left."""
        return await self.execute_command('LPOP', key)

    async def rpop(self, key: str) -> Optional[str]:
        """Pop value from list right."""
        return await self.execute_command('RPOP', key)

    async def blpop(self, keys: List[str], timeout: int = 0) -> Optional[List[str]]:
        """Blocking left pop from list."""
        return await self.execute_command('BLPOP', keys, timeout)

    async def brpop(self, keys: List[str], timeout: int = 0) -> Optional[List[str]]:
        """Blocking right pop from list."""
        return await self.execute_command('BRPOP', keys, timeout)

    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel."""
        return await self.execute_command('PUBLISH', channel, message)

    async def subscribe(self, *channels: str) -> Any:
        """Subscribe to channels."""
        return await self.execute_command('SUBSCRIBE', *channels)

    async def psubscribe(self, *patterns: str) -> Any:
        """Subscribe to channel patterns."""
        return await self.execute_command('PSUBSCRIBE', *patterns)

    async def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        """Add members to sorted set."""
        return await self.execute_command('ZADD', key, mapping)

    async def zrange(self, key: str, start: int, end: int, withscores: bool = False) -> List[str]:
        """Get range from sorted set."""
        return await self.execute_command('ZRANGE', key, start, end, withscores=withscores)

    async def zrem(self, key: str, *members: str) -> int:
        """Remove members from sorted set."""
        return await self.execute_command('ZREM', key, *members)

    async def sadd(self, key: str, *members: str) -> int:
        """Add members to set."""
        return await self.execute_command('SADD', key, *members)

    async def srem(self, key: str, *members: str) -> int:
        """Remove members from set."""
        return await self.execute_command('SREM', key, *members)

    async def smembers(self, key: str) -> set:
        """Get all set members."""
        return await self.execute_command('SMEMBERS', key)


class RedisClusterConnectionPool(ConnectionPool):
    """Redis Cluster connection pool implementation."""

    def __init__(
        self,
        config: ConnectionPoolConfig,
        startup_nodes: List[Dict[str, Union[str, int]]],
        password: Optional[str] = None,
        **kwargs
    ):
        """Initialize Redis Cluster connection pool."""
        super().__init__(config)
        self.startup_nodes = startup_nodes
        self.password = password
        self.cluster_kwargs = kwargs

        # Import redis cluster here to make it optional
        try:
            from rediscluster import RedisCluster
            self.RedisCluster = RedisCluster
        except ImportError:
            try:
                from redis.cluster import RedisCluster
                self.RedisCluster = RedisCluster
            except ImportError:
                raise ImportError("redis-py-cluster is required for Redis Cluster connection pooling")

    async def create_connection(self) -> Any:
        """Create Redis Cluster connection."""
        # Redis Cluster connections are synchronous
        loop = asyncio.get_event_loop()

        def _create_cluster():
            return self.RedisCluster(
                startup_nodes=self.startup_nodes,
                password=self.password,
                **self.cluster_kwargs
            )

        return await loop.run_in_executor(None, _create_cluster)

    async def validate_connection(self, connection: Any) -> bool:
        """Validate Redis Cluster connection."""
        loop = asyncio.get_event_loop()

        def _validate():
            try:
                return connection.ping()
            except Exception:
                return False

        return await loop.run_in_executor(None, _validate)

    async def close_connection(self, connection: Any) -> None:
        """Close Redis Cluster connection."""
        loop = asyncio.get_event_loop()

        def _close():
            try:
                connection.close()
            except Exception:
                pass  # Ignore errors during cleanup

        await loop.run_in_executor(None, _close)

    async def execute_command(self, command: str, *args, **kwargs) -> Any:
        """Execute Redis Cluster command using pooled connection."""
        async with self.acquire() as pooled_conn:
            cluster_conn = pooled_conn.connection
            loop = asyncio.get_event_loop()

            def _execute():
                # Get the command method
                command_method = getattr(cluster_conn, command.lower())
                return command_method(*args, **kwargs)

            return await loop.run_in_executor(None, _execute)


class RedisSentinelConnectionPool(ConnectionPool):
    """Redis Sentinel connection pool implementation."""

    def __init__(
        self,
        config: ConnectionPoolConfig,
        sentinels: List[Dict[str, Union[str, int]]],
        service_name: str,
        password: Optional[str] = None,
        **kwargs
    ):
        """Initialize Redis Sentinel connection pool."""
        super().__init__(config)
        self.sentinels = sentinels
        self.service_name = service_name
        self.password = password
        self.sentinel_kwargs = kwargs

        # Import redis sentinel here to make it optional
        try:
            from redis.sentinel import Sentinel
            self.Sentinel = Sentinel
        except ImportError:
            raise ImportError("redis-py is required for Redis Sentinel connection pooling")

    async def create_connection(self) -> Any:
        """Create Redis Sentinel connection."""
        sentinel = self.Sentinel(
            [(s['host'], s['port']) for s in self.sentinels],
            password=self.password,
            **self.sentinel_kwargs
        )

        # Get master connection
        return sentinel.master_for(self.service_name)

    async def validate_connection(self, connection: Any) -> bool:
        """Validate Redis Sentinel connection."""
        try:
            return await connection.ping()
        except Exception:
            return False

    async def close_connection(self, connection: Any) -> None:
        """Close Redis Sentinel connection."""
        try:
            await connection.close()
        except Exception:
            pass  # Ignore errors during cleanup

    async def execute_command(self, command: str, *args, **kwargs) -> Any:
        """Execute Redis Sentinel command using pooled connection."""
        async with self.acquire() as pooled_conn:
            redis_conn = pooled_conn.connection

            # Get the command method
            command_method = getattr(redis_conn, command.lower())
            return await command_method(*args, **kwargs)


class RedisPoolFactory:
    """Factory for creating Redis connection pools."""

    @staticmethod
    def create_single_node_pool(
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 20,
        **kwargs
    ) -> RedisConnectionPool:
        """Create single Redis node connection pool."""
        config = ConnectionPoolConfig(
            min_size=1,
            max_size=max_connections,
            acquire_timeout=30.0
        )

        return RedisConnectionPool(
            config=config,
            host=host,
            port=port,
            db=db,
            password=password,
            **kwargs
        )

    @staticmethod
    def create_cluster_pool(
        startup_nodes: List[Dict[str, Union[str, int]]],
        password: Optional[str] = None,
        max_connections: int = 20,
        **kwargs
    ) -> RedisClusterConnectionPool:
        """Create Redis Cluster connection pool."""
        config = ConnectionPoolConfig(
            min_size=1,
            max_size=max_connections,
            acquire_timeout=30.0
        )

        return RedisClusterConnectionPool(
            config=config,
            startup_nodes=startup_nodes,
            password=password,
            **kwargs
        )

    @staticmethod
    def create_sentinel_pool(
        sentinels: List[Dict[str, Union[str, int]]],
        service_name: str,
        password: Optional[str] = None,
        max_connections: int = 20,
        **kwargs
    ) -> RedisSentinelConnectionPool:
        """Create Redis Sentinel connection pool."""
        config = ConnectionPoolConfig(
            min_size=1,
            max_size=max_connections,
            acquire_timeout=30.0
        )

        return RedisSentinelConnectionPool(
            config=config,
            sentinels=sentinels,
            service_name=service_name,
            password=password,
            **kwargs
        )

    @staticmethod
    def create_pool_from_url(
        redis_url: str,
        max_connections: int = 20
    ) -> RedisConnectionPool:
        """Create Redis pool from connection URL."""
        # Parse Redis URL (redis://[:password@]host[:port][/db])
        if redis_url.startswith('redis://'):
            url = redis_url.replace('redis://', '')

            # Parse auth and host/port
            if '@' in url:
                auth, rest = url.split('@', 1)
                password = auth
            else:
                password = None
                rest = url

            # Parse host, port, db
            if '/' in rest:
                host_port, db_part = rest.split('/', 1)
                db = int(db_part) if db_part else 0
            else:
                host_port = rest
                db = 0

            if ':' in host_port:
                host, port = host_port.split(':', 1)
                port = int(port)
            else:
                host = host_port
                port = 6379

            return RedisPoolFactory.create_single_node_pool(
                host=host,
                port=port,
                db=db,
                password=password,
                max_connections=max_connections
            )

        elif redis_url.startswith('redis-cluster://'):
            # For cluster URLs, we'd need more complex parsing
            # This is a simplified implementation
            raise NotImplementedError("Redis Cluster URL parsing not implemented")

        else:
            raise ValueError(f"Unsupported Redis URL scheme: {redis_url}")
