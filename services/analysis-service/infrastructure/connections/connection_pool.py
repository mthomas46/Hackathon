"""Connection Pool - Core connection pooling abstractions and interfaces."""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Generic, TypeVar, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from contextlib import asynccontextmanager


class ConnectionState(Enum):
    """Connection state enumeration."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    VALIDATING = "validating"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"


class PoolExhaustionPolicy(Enum):
    """Pool exhaustion handling policies."""
    BLOCK = "block"  # Block until connection available
    GROW = "grow"    # Grow pool beyond max size
    FAIL = "fail"    # Fail with exception
    WAIT = "wait"    # Wait with timeout


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pools."""
    min_size: int = 1
    max_size: int = 10
    max_idle_time: int = 300  # seconds
    max_lifetime: int = 3600  # seconds
    acquire_timeout: float = 30.0  # seconds
    validation_timeout: float = 5.0  # seconds
    retry_attempts: int = 3
    retry_delay: float = 0.1  # seconds
    health_check_interval: int = 60  # seconds
    exhaustion_policy: PoolExhaustionPolicy = PoolExhaustionPolicy.BLOCK
    enable_metrics: bool = True
    enable_health_checks: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.min_size < 0:
            raise ValueError("min_size cannot be negative")
        if self.max_size < self.min_size:
            raise ValueError("max_size must be >= min_size")
        if self.acquire_timeout <= 0:
            raise ValueError("acquire_timeout must be positive")
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts cannot be negative")


T = TypeVar('T')


@dataclass
class PooledConnection(Generic[T]):
    """Wrapper for pooled connections."""
    connection: T
    pool: 'ConnectionPool[T]'
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: datetime = field(default_factory=datetime.utcnow)
    state: ConnectionState = ConnectionState.AVAILABLE
    usage_count: int = 0
    error_count: int = 0

    def __post_init__(self):
        """Initialize pooled connection."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_used_at is None:
            self.last_used_at = self.created_at

    @property
    def age(self) -> float:
        """Get connection age in seconds."""
        return (datetime.utcnow() - self.created_at).total_seconds()

    @property
    def idle_time(self) -> float:
        """Get idle time in seconds."""
        return (datetime.utcnow() - self.last_used_at).total_seconds()

    @property
    def is_expired(self) -> bool:
        """Check if connection is expired."""
        return self.age > self.pool.config.max_lifetime

    @property
    def is_idle_expired(self) -> bool:
        """Check if connection is idle expired."""
        return self.idle_time > self.pool.config.max_idle_time

    def mark_used(self) -> None:
        """Mark connection as used."""
        self.last_used_at = datetime.utcnow()
        self.usage_count += 1

    def mark_error(self) -> None:
        """Mark connection error."""
        self.error_count += 1

    async def validate(self) -> bool:
        """Validate connection health."""
        if not hasattr(self.pool, 'validate_connection'):
            return True

        try:
            return await self.pool.validate_connection(self.connection)
        except Exception:
            self.mark_error()
            return False

    async def close(self) -> None:
        """Close the connection."""
        self.state = ConnectionState.CLOSING
        try:
            if hasattr(self.pool, 'close_connection'):
                await self.pool.close_connection(self.connection)
            self.state = ConnectionState.CLOSED
        except Exception:
            self.state = ConnectionState.ERROR
            raise


class ConnectionPool(ABC, Generic[T]):
    """Abstract base class for connection pools."""

    def __init__(self, config: ConnectionPoolConfig):
        """Initialize connection pool."""
        self.config = config
        self._connections: List[PooledConnection[T]] = []
        self._available: asyncio.Queue[PooledConnection[T]] = asyncio.Queue()
        self._in_use: set = set()
        self._lock = asyncio.Lock()
        self._closed = False

        # Statistics
        self._created_count = 0
        self._destroyed_count = 0
        self._acquired_count = 0
        self._released_count = 0
        self._failed_count = 0

        # Health check task
        self._health_check_task: Optional[asyncio.Task] = None

    @abstractmethod
    async def create_connection(self) -> T:
        """Create a new connection."""
        pass

    @abstractmethod
    async def validate_connection(self, connection: T) -> bool:
        """Validate connection health."""
        pass

    @abstractmethod
    async def close_connection(self, connection: T) -> None:
        """Close a connection."""
        pass

    async def start(self) -> None:
        """Start the connection pool."""
        async with self._lock:
            if self._closed:
                raise RuntimeError("Pool is closed")

            # Create minimum connections
            for _ in range(self.config.min_size):
                await self._create_connection()

            # Start health check task
            if self.config.enable_health_checks:
                self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def stop(self) -> None:
        """Stop the connection pool."""
        async with self._lock:
            self._closed = True

            # Cancel health check task
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            # Close all connections
            close_tasks = []
            for conn in self._connections:
                close_tasks.append(conn.close())

            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)

            self._connections.clear()
            self._in_use.clear()

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if self._closed:
            raise RuntimeError("Pool is closed")

        connection = await self._acquire_connection()
        try:
            yield connection
        finally:
            await self._release_connection(connection)

    async def _acquire_connection(self) -> PooledConnection[T]:
        """Acquire a connection from the pool."""
        start_time = time.time()

        while True:
            if self._closed:
                raise RuntimeError("Pool is closed")

            # Try to get available connection
            try:
                pooled_conn = self._available.get_nowait()
            except asyncio.QueueEmpty:
                # No available connections, create new one if possible
                if len(self._connections) < self.config.max_size:
                    pooled_conn = await self._create_connection()
                elif self.config.exhaustion_policy == PoolExhaustionPolicy.FAIL:
                    raise RuntimeError("Connection pool exhausted")
                elif self.config.exhaustion_policy == PoolExhaustionPolicy.GROW:
                    pooled_conn = await self._create_connection()
                else:
                    # Wait for available connection
                    try:
                        pooled_conn = await asyncio.wait_for(
                            self._available.get(),
                            timeout=self.config.acquire_timeout
                        )
                    except asyncio.TimeoutError:
                        raise RuntimeError("Connection acquire timeout")

            # Validate connection
            if not await pooled_conn.validate():
                # Connection is invalid, destroy and try again
                await self._destroy_connection(pooled_conn)
                continue

            # Mark as in use
            pooled_conn.state = ConnectionState.IN_USE
            pooled_conn.mark_used()
            self._in_use.add(pooled_conn)
            self._acquired_count += 1

            return pooled_conn

    async def _release_connection(self, pooled_conn: PooledConnection[T]) -> None:
        """Release a connection back to the pool."""
        if pooled_conn in self._in_use:
            self._in_use.remove(pooled_conn)

        # Check if connection should be destroyed
        if (pooled_conn.is_expired or
            pooled_conn.is_idle_expired or
            pooled_conn.error_count > 3):
            await self._destroy_connection(pooled_conn)
            return

        # Return to available pool
        pooled_conn.state = ConnectionState.AVAILABLE
        await self._available.put(pooled_conn)
        self._released_count += 1

    async def _create_connection(self) -> PooledConnection[T]:
        """Create a new pooled connection."""
        connection = await self.create_connection()
        pooled_conn = PooledConnection(connection=connection, pool=self)
        self._connections.append(pooled_conn)
        self._created_count += 1
        return pooled_conn

    async def _destroy_connection(self, pooled_conn: PooledConnection[T]) -> None:
        """Destroy a pooled connection."""
        if pooled_conn in self._connections:
            self._connections.remove(pooled_conn)

        if pooled_conn in self._in_use:
            self._in_use.remove(pooled_conn)

        try:
            await pooled_conn.close()
        except Exception:
            pass  # Ignore errors during cleanup

        self._destroyed_count += 1

    async def _health_check_loop(self) -> None:
        """Periodic health check loop."""
        while not self._closed:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Health check error: {e}")

    async def _perform_health_check(self) -> None:
        """Perform health check on connections."""
        async with self._lock:
            # Check available connections
            available_connections = list(self._available._queue)  # Access private queue

            for pooled_conn in available_connections:
                if not await pooled_conn.validate():
                    # Remove invalid connection
                    try:
                        self._available._queue.remove(pooled_conn)  # Remove from queue
                        await self._destroy_connection(pooled_conn)
                    except (ValueError, AttributeError):
                        pass  # Connection not in queue or queue access failed

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            'pool_size': len(self._connections),
            'available_count': self._available.qsize(),
            'in_use_count': len(self._in_use),
            'created_count': self._created_count,
            'destroyed_count': self._destroyed_count,
            'acquired_count': self._acquired_count,
            'released_count': self._released_count,
            'failed_count': self._failed_count,
            'closed': self._closed,
            'config': {
                'min_size': self.config.min_size,
                'max_size': self.config.max_size,
                'max_idle_time': self.config.max_idle_time,
                'max_lifetime': self.config.max_lifetime
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform pool health check."""
        stats = self.get_stats()

        # Test creating a new connection
        connection_test_passed = False
        try:
            test_conn = await self._create_connection()
            connection_test_passed = await test_conn.validate()
            await self._destroy_connection(test_conn)
        except Exception:
            connection_test_passed = False

        return {
            'healthy': not self._closed and connection_test_passed,
            'status': 'healthy' if (not self._closed and connection_test_passed) else 'unhealthy',
            'pool_stats': stats,
            'connection_test_passed': connection_test_passed,
            'timestamp': datetime.utcnow().isoformat()
        }
