"""Connection Pool Manager - Centralized management of multiple connection pools."""

import asyncio
import threading
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
from dataclasses import dataclass

from .connection_pool import ConnectionPool, ConnectionPoolConfig, PooledConnection


@dataclass
class PoolMetrics:
    """Metrics for connection pool performance."""
    pool_name: str
    created_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    pending_acquires: int = 0
    total_acquires: int = 0
    total_releases: int = 0
    failed_acquires: int = 0
    connection_errors: int = 0
    average_acquire_time: float = 0.0
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"


class ConnectionPoolManager:
    """Centralized manager for multiple connection pools."""

    def __init__(self):
        """Initialize connection pool manager."""
        self.pools: Dict[str, ConnectionPool] = {}
        self.metrics: Dict[str, PoolMetrics] = {}
        self._lock = asyncio.Lock()
        self._running = False
        self._monitoring_task: Optional[asyncio.Task] = None

        # Global metrics
        self._total_pools = 0
        self._healthy_pools = 0
        self._unhealthy_pools = 0

    async def register_pool(
        self,
        name: str,
        pool: ConnectionPool,
        enable_monitoring: bool = True
    ) -> None:
        """Register a connection pool."""
        async with self._lock:
            if name in self.pools:
                raise ValueError(f"Pool {name} already registered")

            self.pools[name] = pool
            self.metrics[name] = PoolMetrics(pool_name=name)
            self._total_pools += 1

            # Start the pool if not already started
            if not pool._closed:
                await pool.start()

            print(f"Registered connection pool: {name}")

    async def unregister_pool(self, name: str) -> bool:
        """Unregister a connection pool."""
        async with self._lock:
            if name not in self.pools:
                return False

            pool = self.pools[name]

            # Stop the pool
            try:
                await pool.stop()
            except Exception as e:
                print(f"Error stopping pool {name}: {e}")

            # Remove from registry
            del self.pools[name]
            del self.metrics[name]
            self._total_pools -= 1

            print(f"Unregistered connection pool: {name}")
            return True

    def get_pool(self, name: str) -> Optional[ConnectionPool]:
        """Get a registered connection pool."""
        return self.pools.get(name)

    def list_pools(self) -> List[str]:
        """List all registered pool names."""
        return list(self.pools.keys())

    async def start_all_pools(self) -> None:
        """Start all registered connection pools."""
        async with self._lock:
            for name, pool in self.pools.items():
                try:
                    if pool._closed:
                        await pool.start()
                        print(f"Started pool: {name}")
                except Exception as e:
                    print(f"Error starting pool {name}: {e}")

            self._running = True

            # Start monitoring if enabled
            if any(pool.config.enable_metrics for pool in self.pools.values()):
                self._monitoring_task = asyncio.create_task(self._monitor_pools())

    async def stop_all_pools(self) -> None:
        """Stop all registered connection pools."""
        async with self._lock:
            self._running = False

            # Cancel monitoring task
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass

            # Stop all pools
            stop_tasks = []
            for name, pool in self.pools.items():
                stop_tasks.append(self._safe_stop_pool(name, pool))

            if stop_tasks:
                await asyncio.gather(*stop_tasks, return_exceptions=True)

    async def _safe_stop_pool(self, name: str, pool: ConnectionPool) -> None:
        """Safely stop a connection pool."""
        try:
            await pool.stop()
            print(f"Stopped pool: {name}")
        except Exception as e:
            print(f"Error stopping pool {name}: {e}")

    async def _monitor_pools(self) -> None:
        """Monitor all connection pools."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds

                async with self._lock:
                    healthy_count = 0
                    unhealthy_count = 0

                    for name, pool in self.pools.items():
                        try:
                            # Update pool metrics
                            stats = pool.get_stats()
                            metrics = self.metrics[name]

                            metrics.created_connections = stats.get('created_count', 0)
                            metrics.active_connections = stats.get('in_use_count', 0)
                            metrics.idle_connections = stats.get('available_count', 0)
                            metrics.total_acquires = stats.get('acquired_count', 0)
                            metrics.total_releases = stats.get('released_count', 0)
                            metrics.failed_acquires = stats.get('failed_count', 0)

                            # Perform health check
                            health = await pool.health_check()
                            metrics.last_health_check = datetime.utcnow()
                            metrics.health_status = health.get('status', 'unknown')

                            if metrics.health_status == 'healthy':
                                healthy_count += 1
                            else:
                                unhealthy_count += 1

                        except Exception as e:
                            print(f"Error monitoring pool {name}: {e}")
                            unhealthy_count += 1

                    self._healthy_pools = healthy_count
                    self._unhealthy_pools = unhealthy_count

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in pool monitoring: {e}")

    def get_pool_metrics(self, name: str) -> Optional[PoolMetrics]:
        """Get metrics for a specific pool."""
        return self.metrics.get(name)

    def get_all_metrics(self) -> Dict[str, PoolMetrics]:
        """Get metrics for all pools."""
        return self.metrics.copy()

    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global connection pool metrics."""
        total_active = sum(m.active_connections for m in self.metrics.values())
        total_idle = sum(m.idle_connections for m in self.metrics.values())
        total_created = sum(m.created_connections for m in self.metrics.values())
        total_acquires = sum(m.total_acquires for m in self.metrics.values())
        total_releases = sum(m.total_releases for m in self.metrics.values())
        total_failed = sum(m.failed_acquires for m in self.metrics.values())

        return {
            'total_pools': self._total_pools,
            'healthy_pools': self._healthy_pools,
            'unhealthy_pools': self._unhealthy_pools,
            'total_active_connections': total_active,
            'total_idle_connections': total_idle,
            'total_created_connections': total_created,
            'total_acquires': total_acquires,
            'total_releases': total_releases,
            'total_failed_acquires': total_failed,
            'pool_utilization_rate': total_active / max(1, total_active + total_idle),
            'acquire_success_rate': total_acquires / max(1, total_acquires + total_failed)
        }

    async def health_check_all_pools(self) -> Dict[str, Any]:
        """Perform health check on all pools."""
        results = {}

        async with self._lock:
            for name, pool in self.pools.items():
                try:
                    health = await pool.health_check()
                    results[name] = health
                except Exception as e:
                    results[name] = {
                        'status': 'error',
                        'error': str(e)
                    }

        # Add global health summary
        healthy_count = sum(1 for r in results.values() if r.get('status') == 'healthy')
        total_count = len(results)

        overall_status = 'healthy' if healthy_count == total_count else 'degraded'
        if healthy_count == 0:
            overall_status = 'unhealthy'

        results['_summary'] = {
            'overall_status': overall_status,
            'total_pools': total_count,
            'healthy_pools': healthy_count,
            'unhealthy_pools': total_count - healthy_count,
            'timestamp': datetime.utcnow().isoformat()
        }

        return results

    async def acquire_connection(self, pool_name: str):
        """Acquire a connection from a specific pool."""
        pool = self.get_pool(pool_name)
        if not pool:
            raise ValueError(f"Pool {pool_name} not found")

        return pool.acquire()

    async def execute_with_pool(
        self,
        pool_name: str,
        operation: callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation using a connection from specified pool."""
        async with self.acquire_connection(pool_name) as connection:
            return await operation(connection, *args, **kwargs)

    def create_pool_config(
        self,
        min_size: int = 1,
        max_size: int = 10,
        max_idle_time: int = 300,
        max_lifetime: int = 3600,
        acquire_timeout: float = 30.0,
        enable_metrics: bool = True,
        enable_health_checks: bool = True
    ) -> ConnectionPoolConfig:
        """Create a standardized pool configuration."""
        return ConnectionPoolConfig(
            min_size=min_size,
            max_size=max_size,
            max_idle_time=max_idle_time,
            max_lifetime=max_lifetime,
            acquire_timeout=acquire_timeout,
            enable_metrics=enable_metrics,
            enable_health_checks=enable_health_checks
        )


# Global pool manager instance
pool_manager = ConnectionPoolManager()


class PoolManagerService:
    """Service for managing connection pools with lifecycle management."""

    def __init__(self, pool_manager: ConnectionPoolManager):
        """Initialize pool manager service."""
        self.pool_manager = pool_manager
        self._started = False

    async def start(self) -> None:
        """Start the pool manager service."""
        if not self._started:
            await self.pool_manager.start_all_pools()
            self._started = True
            print("Connection Pool Manager Service started")

    async def stop(self) -> None:
        """Stop the pool manager service."""
        if self._started:
            await self.pool_manager.stop_all_pools()
            self._started = False
            print("Connection Pool Manager Service stopped")

    async def register_database_pool(
        self,
        name: str,
        database_url: str,
        pool_config: Optional[ConnectionPoolConfig] = None
    ) -> None:
        """Register a database connection pool."""
        from .database_pool import DatabasePoolFactory

        if pool_config is None:
            pool_config = self.pool_manager.create_pool_config()

        pool = DatabasePoolFactory.create_pool_from_url(database_url, pool_config)
        await self.pool_manager.register_pool(name, pool)

    async def register_http_pool(
        self,
        name: str,
        base_url: str,
        pool_config: Optional[ConnectionPoolConfig] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """Register an HTTP connection pool."""
        from .http_pool import HTTPPoolFactory

        if pool_config is None:
            pool_config = self.pool_manager.create_pool_config()

        pool = HTTPPoolFactory.create_advanced_pool(
            base_url=base_url,
            max_connections=pool_config.max_size,
            headers=headers
        )
        await self.pool_manager.register_pool(name, pool)

    async def register_redis_pool(
        self,
        name: str,
        redis_url: str,
        pool_config: Optional[ConnectionPoolConfig] = None
    ) -> None:
        """Register a Redis connection pool."""
        from .redis_pool import RedisPoolFactory

        if pool_config is None:
            pool_config = self.pool_manager.create_pool_config()

        pool = RedisPoolFactory.create_pool_from_url(
            redis_url,
            max_connections=pool_config.max_size
        )
        await self.pool_manager.register_pool(name, pool)

    async def get_service_status(self) -> Dict[str, Any]:
        """Get service status and metrics."""
        return {
            'service_started': self._started,
            'pool_manager_metrics': self.pool_manager.get_global_metrics(),
            'registered_pools': self.pool_manager.list_pools(),
            'pool_health': await self.pool_manager.health_check_all_pools()
        }


# Global pool manager service instance
pool_manager_service = PoolManagerService(pool_manager)
