"""Connection Pool Service for managing database and HTTP connection pools.

Provides enterprise-grade connection pooling with:
- Database connection pooling with automatic cleanup
- HTTP client connection pooling with keep-alive
- Connection health monitoring and automatic recovery
- Resource limits and connection lifecycle management
- Metrics and monitoring for connection usage
"""

import asyncio
import logging
import sqlite3
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar

import httpx
import psycopg2
import redis.asyncio as redis

logger = logging.getLogger(__name__)
T = TypeVar("T")


class ConnectionType(Enum):
    """Types of connections supported by the pool."""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    HTTP = "http"
    GENERIC = "generic"


class PoolState(Enum):
    """Connection pool states."""

    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class ConnectionConfig:
    """Configuration for a connection pool."""

    pool_type: ConnectionType
    host: str = "localhost"
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    max_connections: int = 10
    min_connections: int = 1
    max_idle_time: float = 300.0  # 5 minutes
    max_lifetime: float = 3600.0  # 1 hour
    connection_timeout: float = 30.0
    retry_attempts: int = 3
    health_check_interval: float = 60.0
    ssl_enabled: bool = False
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionWrapper:
    """Wrapper for individual connections with metadata."""

    connection: Any
    pool_name: str
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    is_healthy: bool = True

    def mark_used(self) -> None:
        """Mark connection as used."""
        self.last_used = time.time()
        self.use_count += 1

    def is_expired(self, max_idle_time: float, max_lifetime: float) -> bool:
        """Check if connection has expired."""
        current_time = time.time()
        return (
            current_time - self.last_used > max_idle_time
            or current_time - self.created_at > max_lifetime
        )

    async def close(self) -> None:
        """Close the connection."""
        try:
            if hasattr(self.connection, "close"):
                if asyncio.iscoroutinefunction(self.connection.close):
                    await self.connection.close()
                else:
                    self.connection.close()
        except Exception as e:
            logger.warning(f"Error closing connection in pool {self.pool_name}: {e}")


@dataclass
class PoolMetrics:
    """Metrics for connection pool monitoring."""

    total_connections_created: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    connections_destroyed: int = 0
    connection_timeouts: int = 0
    connection_errors: int = 0
    avg_connection_wait_time: float = 0.0
    pool_state: PoolState = PoolState.INITIALIZING


class ConnectionPool:
    """Generic connection pool with lifecycle management."""

    def __init__(self, name: str, config: ConnectionConfig):
        self.name = name
        self.config = config
        self.metrics = PoolMetrics()

        # Connection storage
        self._available_connections: List[ConnectionWrapper] = []
        self._in_use_connections: set = set()

        # Synchronization
        self._lock = threading.Lock()
        self._connection_semaphore = asyncio.Semaphore(config.max_connections)
        self._shutdown_event = asyncio.Event()

        # Health monitoring
        self._health_check_task: Optional[asyncio.Task] = None
        self._last_health_check = 0.0

    async def get_connection(self) -> ConnectionWrapper:
        """Get a connection from the pool."""
        if self._shutdown_event.is_set():
            raise RuntimeError(f"Connection pool {self.name} is shutting down")

        # Wait for available connection slot
        await self._connection_semaphore.acquire()

        try:
            async with asyncio.timeout(self.config.connection_timeout):
                return await self._acquire_connection()
        except asyncio.TimeoutError:
            self.metrics.connection_timeouts += 1
            self._connection_semaphore.release()
            raise RuntimeError(f"Connection timeout for pool {self.name}")

    async def _acquire_connection(self) -> ConnectionWrapper:
        """Acquire a connection, creating new one if necessary."""
        with self._lock:
            # Try to get existing connection
            while self._available_connections:
                wrapper = self._available_connections.pop()

                # Check if connection is still valid
                if await self._is_connection_valid(wrapper):
                    wrapper.mark_used()
                    self._in_use_connections.add(wrapper)
                    self._update_metrics()
                    return wrapper
                else:
                    # Connection is invalid, destroy it
                    await self._destroy_connection(wrapper)

            # No valid connections available, create new one
            wrapper = await self._create_connection()
            wrapper.mark_used()
            self._in_use_connections.add(wrapper)
            self._update_metrics()
            return wrapper

    async def return_connection(self, wrapper: ConnectionWrapper) -> None:
        """Return a connection to the pool."""
        with self._lock:
            if wrapper in self._in_use_connections:
                self._in_use_connections.remove(wrapper)

                # Check if connection should be destroyed
                if wrapper.is_expired(
                    self.config.max_idle_time, self.config.max_lifetime
                ):
                    await self._destroy_connection(wrapper)
                else:
                    self._available_connections.append(wrapper)

            self._connection_semaphore.release()
            self._update_metrics()

    async def _create_connection(self) -> ConnectionWrapper:
        """Create a new connection."""
        try:
            if self.config.pool_type == ConnectionType.SQLITE:
                conn = sqlite3.connect(
                    self.config.database or ":memory:",
                    timeout=self.config.connection_timeout,
                    **self.config.extra_params,
                )
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")

            elif self.config.pool_type == ConnectionType.POSTGRESQL:
                conn = psycopg2.connect(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.username,
                    password=self.config.password,
                    connect_timeout=int(self.config.connection_timeout),
                    sslmode="require" if self.config.ssl_enabled else "disable",
                    **self.config.extra_params,
                )

            elif self.config.pool_type == ConnectionType.REDIS:
                conn = redis.from_url(
                    f"redis://{self.config.host}:{self.config.port or 6379}",
                    max_connections=1,  # Each wrapper gets its own connection
                    retry_on_timeout=True,
                    socket_timeout=self.config.connection_timeout,
                    **self.config.extra_params,
                )

            elif self.config.pool_type == ConnectionType.HTTP:
                conn = httpx.AsyncClient(
                    limits=httpx.Limits(
                        max_keepalive_connections=self.config.max_connections,
                        max_connections=self.config.max_connections,
                    ),
                    timeout=httpx.Timeout(self.config.connection_timeout),
                    **self.config.extra_params,
                )

            else:
                raise ValueError(
                    f"Unsupported connection type: {self.config.pool_type}"
                )

            self.metrics.total_connections_created += 1
            wrapper = ConnectionWrapper(connection=conn, pool_name=self.name)

            logger.debug(f"Created new connection in pool {self.name}")
            return wrapper

        except Exception as e:
            self.metrics.connection_errors += 1
            logger.error(f"Failed to create connection in pool {self.name}: {e}")
            raise

    async def _is_connection_valid(self, wrapper: ConnectionWrapper) -> bool:
        """Check if a connection is still valid."""
        try:
            if self.config.pool_type == ConnectionType.SQLITE:
                wrapper.connection.execute("SELECT 1").fetchone()
                return True

            elif self.config.pool_type == ConnectionType.POSTGRESQL:
                with wrapper.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                return True

            elif self.config.pool_type == ConnectionType.REDIS:
                await wrapper.connection.ping()
                return True

            elif self.config.pool_type == ConnectionType.HTTP:
                # HTTP clients are generally self-managing
                return wrapper.connection.is_closed is False

            return True

        except Exception as e:
            logger.debug(f"Connection validation failed for pool {self.name}: {e}")
            wrapper.is_healthy = False
            return False

    async def _destroy_connection(self, wrapper: ConnectionWrapper) -> None:
        """Destroy a connection."""
        try:
            await wrapper.close()
            self.metrics.connections_destroyed += 1
            logger.debug(f"Destroyed connection in pool {self.name}")
        except Exception as e:
            logger.warning(f"Error destroying connection in pool {self.name}: {e}")

    def _update_metrics(self) -> None:
        """Update pool metrics."""
        with self._lock:
            self.metrics.active_connections = len(self._in_use_connections)
            self.metrics.idle_connections = len(self._available_connections)
            self.metrics.pool_state = self._determine_pool_state()

    def _determine_pool_state(self) -> PoolState:
        """Determine the current pool state."""
        total_connections = (
            self.metrics.active_connections + self.metrics.idle_connections
        )

        if total_connections == 0:
            return PoolState.INITIALIZING

        error_rate = self.metrics.connection_errors / max(
            1, self.metrics.total_connections_created
        )

        if error_rate > 0.5:
            return PoolState.UNHEALTHY
        elif error_rate > 0.2:
            return PoolState.DEGRADED
        else:
            return PoolState.HEALTHY

    async def start_health_monitoring(self) -> None:
        """Start background health monitoring."""
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(
                self._health_monitoring_loop()
            )
            logger.info(f"Started health monitoring for connection pool {self.name}")

    async def stop_health_monitoring(self) -> None:
        """Stop background health monitoring."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            logger.info(f"Stopped health monitoring for connection pool {self.name}")

    async def _health_monitoring_loop(self) -> None:
        """Background health monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                if (
                    current_time - self._last_health_check
                    >= self.config.health_check_interval
                ):
                    await self._perform_health_check()
                    self._last_health_check = current_time

                # Clean up expired connections
                await self._cleanup_expired_connections()

                await asyncio.sleep(self.config.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Error in health monitoring loop for pool {self.name}: {e}"
                )
                await asyncio.sleep(self.config.health_check_interval)

    async def _perform_health_check(self) -> None:
        """Perform health check on the pool."""
        # Simple health check - try to get and return a connection
        try:
            conn = await self.get_connection()
            await self.return_connection(conn)
            logger.debug(f"Health check passed for pool {self.name}")
        except Exception as e:
            logger.warning(f"Health check failed for pool {self.name}: {e}")

    async def _cleanup_expired_connections(self) -> None:
        """Clean up expired connections."""
        with self._lock:
            expired_connections = []
            for wrapper in self._available_connections[:]:  # Copy the list
                if wrapper.is_expired(
                    self.config.max_idle_time, self.config.max_lifetime
                ):
                    expired_connections.append(wrapper)
                    self._available_connections.remove(wrapper)

            # Destroy expired connections
            for wrapper in expired_connections:
                await self._destroy_connection(wrapper)

            if expired_connections:
                logger.debug(
                    f"Cleaned up {len(expired_connections)} expired connections in pool {self.name}"
                )

    async def shutdown(self) -> None:
        """Shutdown the connection pool."""
        logger.info(f"Shutting down connection pool {self.name}")

        self._shutdown_event.set()
        await self.stop_health_monitoring()

        # Close all connections
        with self._lock:
            all_connections = self._available_connections + list(
                self._in_use_connections
            )

        for wrapper in all_connections:
            await self._destroy_connection(wrapper)

        self._available_connections.clear()
        self._in_use_connections.clear()

        logger.info(f"Connection pool {self.name} shutdown complete")


class HTTPConnectionPool:
    """Specialized HTTP connection pool using httpx."""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = threading.Lock()

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            with self._lock:
                if self._client is None or self._client.is_closed:
                    self._client = httpx.AsyncClient(
                        limits=httpx.Limits(
                            max_keepalive_connections=self.config.max_connections,
                            max_connections=self.config.max_connections,
                        ),
                        timeout=httpx.Timeout(self.config.connection_timeout),
                        **self.config.extra_params,
                    )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


class ConnectionPoolService:
    """Centralized service for managing multiple connection pools."""

    def __init__(self):
        self._pools: Dict[str, ConnectionPool] = {}
        self._http_pools: Dict[str, HTTPConnectionPool] = {}
        self._lock = threading.Lock()

    def create_pool(self, name: str, config: ConnectionConfig) -> ConnectionPool:
        """Create a new connection pool."""
        with self._lock:
            if name in self._pools:
                raise ValueError(f"Connection pool {name} already exists")

            pool = ConnectionPool(name, config)
            self._pools[name] = pool

            # Start health monitoring
            asyncio.create_task(pool.start_health_monitoring())

            logger.info(f"Created connection pool: {name}")
            return pool

    def get_pool(self, name: str) -> ConnectionPool:
        """Get an existing connection pool."""
        if name not in self._pools:
            raise ValueError(f"Connection pool {name} does not exist")
        return self._pools[name]

    def create_http_pool(
        self, name: str, config: ConnectionConfig
    ) -> HTTPConnectionPool:
        """Create a new HTTP connection pool."""
        with self._lock:
            if name in self._http_pools:
                raise ValueError(f"HTTP connection pool {name} already exists")

            pool = HTTPConnectionPool(config)
            self._http_pools[name] = pool

            logger.info(f"Created HTTP connection pool: {name}")
            return pool

    def get_http_pool(self, name: str) -> HTTPConnectionPool:
        """Get an existing HTTP connection pool."""
        if name not in self._http_pools:
            raise ValueError(f"HTTP connection pool {name} does not exist")
        return self._http_pools[name]

    @asynccontextmanager
    async def get_connection(self, pool_name: str):
        """Context manager for getting a connection from a pool."""
        pool = self.get_pool(pool_name)
        connection = await pool.get_connection()
        try:
            yield connection
        finally:
            await pool.return_connection(connection)

    async def get_http_client(self, pool_name: str) -> httpx.AsyncClient:
        """Get an HTTP client from a pool."""
        pool = self.get_http_pool(pool_name)
        return await pool.get_client()

    def get_pool_metrics(self, pool_name: str) -> PoolMetrics:
        """Get metrics for a specific pool."""
        pool = self.get_pool(pool_name)
        return pool.metrics

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all pools."""
        metrics = {}

        for name, pool in self._pools.items():
            metrics[name] = {
                "pool_type": pool.config.pool_type.value,
                "state": pool.metrics.pool_state.value,
                "active_connections": pool.metrics.active_connections,
                "idle_connections": pool.metrics.idle_connections,
                "total_created": pool.metrics.total_connections_created,
                "total_destroyed": pool.metrics.connections_destroyed,
                "connection_errors": pool.metrics.connection_errors,
                "connection_timeouts": pool.metrics.connection_timeouts,
                "avg_wait_time": pool.metrics.avg_connection_wait_time,
            }

        return metrics

    async def shutdown_all(self) -> None:
        """Shutdown all connection pools."""
        logger.info("Shutting down all connection pools")

        # Shutdown regular pools
        shutdown_tasks = []
        for name, pool in self._pools.items():
            shutdown_tasks.append(pool.shutdown())

        # Shutdown HTTP pools
        for name, pool in self._http_pools.items():
            shutdown_tasks.append(pool.close())

        await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        logger.info("All connection pools shutdown complete")


# Global instance
_connection_pool_service: Optional[ConnectionPoolService] = None


def get_connection_pool_service() -> ConnectionPoolService:
    """Get the global connection pool service instance."""
    global _connection_pool_service
    if _connection_pool_service is None:
        _connection_pool_service = ConnectionPoolService()
    return _connection_pool_service


# Convenience functions
def create_database_pool(
    name: str,
    database_url: str,
    pool_type: ConnectionType = ConnectionType.SQLITE,
    max_connections: int = 10,
) -> ConnectionPool:
    """Convenience function to create a database connection pool."""
    # Parse database URL (simplified)
    if pool_type == ConnectionType.SQLITE:
        config = ConnectionConfig(
            pool_type=pool_type, database=database_url, max_connections=max_connections
        )
    else:
        # For other databases, you'd parse the URL properly
        config = ConnectionConfig(
            pool_type=pool_type,
            host="localhost",
            port=5432,
            database=database_url,
            max_connections=max_connections,
        )

    service = get_connection_pool_service()
    return service.create_pool(name, config)


def create_http_pool(
    name: str, base_url: str = "", max_connections: int = 20
) -> HTTPConnectionPool:
    """Convenience function to create an HTTP connection pool."""
    config = ConnectionConfig(
        pool_type=ConnectionType.HTTP,
        max_connections=max_connections,
        extra_params={"base_url": base_url} if base_url else {},
    )

    service = get_connection_pool_service()
    return service.create_http_pool(name, config)
