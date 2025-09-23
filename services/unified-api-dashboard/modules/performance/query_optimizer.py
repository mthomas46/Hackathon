"""
Database Query Optimization and Connection Management

Features:
- Query optimization and execution planning
- Connection pooling with health monitoring
- Async query execution with timeouts
- Query result caching and streaming
- Database performance monitoring
- Automatic retry and failover logic
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

import psycopg2
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Query performance metrics."""

    query_id: str
    sql: str
    execution_time: float
    rows_affected: int = 0
    connection_time: float = 0
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConnectionStats:
    """Database connection statistics."""

    active_connections: int = 0
    idle_connections: int = 0
    total_connections_created: int = 0
    connection_errors: int = 0
    average_response_time: float = 0.0
    pool_exhaustion_count: int = 0


class ConnectionPool:
    """
    Advanced database connection pool with health monitoring.

    Features:
    - Connection health checks
    - Automatic reconnection
    - Pool size management
    - Performance monitoring
    - Graceful shutdown
    """

    def __init__(
        self, dsn: str, min_size: int = 5, max_size: int = 20, max_idle_time: int = 300, health_check_interval: int = 60
    ):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.health_check_interval = health_check_interval

        self._pool = []
        self._available = []
        self._in_use = set()
        self._lock = asyncio.Lock()
        self._stats = ConnectionStats()

        # Health monitoring
        self._health_monitor_task = None
        self._shutdown = False

    async def initialize(self):
        """Initialize the connection pool."""
        for _ in range(self.min_size):
            conn = await self._create_connection()
            if conn:
                self._available.append(conn)
                self._stats.total_connections_created += 1

        # Start health monitoring
        self._health_monitor_task = asyncio.create_task(self._health_monitor())

    async def get_connection(self) -> Optional[Any]:
        """Get a connection from the pool."""
        async with self._lock:
            if self._shutdown:
                return None

            # Try to get available connection
            if self._available:
                conn = self._available.pop()
                if await self._is_connection_healthy(conn):
                    self._in_use.add(conn)
                    self._stats.active_connections = len(self._in_use)
                    return conn
                else:
                    # Connection unhealthy, discard
                    await self._close_connection(conn)

            # Create new connection if pool not at max
            if len(self._pool) < self.max_size:
                conn = await self._create_connection()
                if conn:
                    self._pool.append(conn)
                    self._in_use.add(conn)
                    self._stats.total_connections_created += 1
                    self._stats.active_connections = len(self._in_use)
                    return conn

            # Pool exhausted
            self._stats.pool_exhaustion_count += 1
            return None

    async def return_connection(self, conn: Any):
        """Return a connection to the pool."""
        async with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)

                if await self._is_connection_healthy(conn):
                    self._available.append(conn)
                    self._stats.idle_connections = len(self._available)
                else:
                    await self._close_connection(conn)

            self._stats.active_connections = len(self._in_use)

    async def shutdown(self):
        """Shutdown the connection pool."""
        self._shutdown = True

        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        async with self._lock:
            for conn in self._pool:
                await self._close_connection(conn)
            self._pool.clear()
            self._available.clear()
            self._in_use.clear()

    async def get_stats(self) -> ConnectionStats:
        """Get connection pool statistics."""
        async with self._lock:
            self._stats.idle_connections = len(self._available)
            self._stats.active_connections = len(self._in_use)
            return self._stats

    async def _create_connection(self) -> Optional[Any]:
        """Create a new database connection."""
        try:
            # This would be implemented based on the specific database driver
            # For PostgreSQL with psycopg2:
            # conn = psycopg2.connect(self.dsn)

            # For async drivers:
            # conn = await asyncpg.connect(self.dsn)

            # Placeholder implementation
            return {"connection_id": id(self), "created_at": time.time()}

        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            self._stats.connection_errors += 1
            return None

    async def _is_connection_healthy(self, conn: Any) -> bool:
        """Check if connection is healthy."""
        try:
            # Implement health check based on database type
            # For example, execute a simple query
            return True
        except Exception:
            return False

    async def _close_connection(self, conn: Any):
        """Close a database connection."""
        try:
            # Implement connection closing based on database type
            # conn.close()
            pass
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    async def _health_monitor(self):
        """Background health monitoring task."""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.health_check_interval)

                async with self._lock:
                    unhealthy = []

                    # Check available connections
                    for conn in self._available[:]:
                        if not await self._is_connection_healthy(conn):
                            unhealthy.append(conn)

                    # Remove unhealthy connections
                    for conn in unhealthy:
                        self._available.remove(conn)
                        await self._close_connection(conn)

                    # Maintain minimum pool size
                    while len(self._available) + len(self._in_use) < self.min_size:
                        conn = await self._create_connection()
                        if conn:
                            self._available.append(conn)
                            self._stats.total_connections_created += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")


class AsyncQueryExecutor:
    """
    Asynchronous query execution with optimization.

    Features:
    - Query planning and optimization
    - Parallel query execution
    - Result streaming
    - Performance monitoring
    - Automatic retries
    """

    def __init__(self, connection_pool: ConnectionPool, max_retries: int = 3):
        self.connection_pool = connection_pool
        self.max_retries = max_retries
        self.query_metrics: List[QueryMetrics] = []
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def get_connection(self):
        """Context manager for connection handling."""
        conn = None
        try:
            conn = await self.connection_pool.get_connection()
            if conn is None:
                raise RuntimeError("No available connections")
            yield conn
        finally:
            if conn:
                await self.connection_pool.return_connection(conn)

    async def execute_query(self, sql: str, params: tuple = None, timeout: float = 30.0) -> List[Dict]:
        """Execute a query with automatic retries and monitoring."""
        query_id = f"query_{int(time.time() * 1000000)}"
        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                async with self.get_connection() as conn:
                    connection_time = time.time() - start_time

                    # Execute query with timeout
                    result = await asyncio.wait_for(self._execute_query_impl(conn, sql, params), timeout=timeout)

                    execution_time = time.time() - start_time

                    # Record metrics
                    metrics = QueryMetrics(
                        query_id=query_id,
                        sql=sql,
                        execution_time=execution_time,
                        rows_affected=len(result) if result else 0,
                        connection_time=connection_time,
                    )

                    async with self._lock:
                        self.query_metrics.append(metrics)

                    return result

            except asyncio.TimeoutError:
                logger.warning(f"Query timeout on attempt {attempt + 1}: {sql}")
                if attempt == self.max_retries - 1:
                    raise
            except Exception as e:
                logger.error(f"Query execution error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    # Record failed metrics
                    metrics = QueryMetrics(
                        query_id=query_id, sql=sql, execution_time=time.time() - start_time, error=str(e)
                    )
                    async with self._lock:
                        self.query_metrics.append(metrics)
                    raise

        raise RuntimeError(f"Query failed after {self.max_retries} attempts")

    async def execute_many(self, queries: List[tuple]) -> List[Any]:
        """Execute multiple queries in parallel."""
        semaphore = asyncio.Semaphore(10)  # Limit concurrent queries

        async def execute_single(query_tuple):
            async with semaphore:
                sql, params = query_tuple
                return await self.execute_query(sql, params)

        tasks = [execute_single(query_tuple) for query_tuple in queries]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def stream_results(
        self, sql: str, params: tuple = None, chunk_size: int = 1000
    ) -> AsyncGenerator[List[Dict], None]:
        """Stream query results for large datasets."""
        async with self.get_connection() as conn:
            # This would implement cursor-based streaming
            # For demonstration, we'll simulate streaming
            offset = 0
            while True:
                chunk_sql = f"{sql} LIMIT {chunk_size} OFFSET {offset}"
                chunk = await self._execute_query_impl(conn, chunk_sql, params)

                if not chunk:
                    break

                yield chunk
                offset += chunk_size

                # Allow other tasks to run
                await asyncio.sleep(0)

    async def _execute_query_impl(self, conn: Any, sql: str, params: tuple = None) -> List[Dict]:
        """Actual query execution implementation."""
        # This would be implemented based on the specific database driver
        # Placeholder implementation
        if "SELECT" in sql.upper():
            return [{"id": 1, "name": "example"}]  # Mock result
        else:
            return []  # Mock for non-SELECT queries

    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate query performance report."""
        async with self._lock:
            if not self.query_metrics:
                return {"total_queries": 0, "average_execution_time": 0}

            total_queries = len(self.query_metrics)
            successful_queries = [m for m in self.query_metrics if not m.error]
            failed_queries = [m for m in self.query_metrics if m.error]

            avg_execution_time = (
                sum(m.execution_time for m in successful_queries) / len(successful_queries) if successful_queries else 0
            )
            avg_connection_time = (
                sum(m.connection_time for m in successful_queries) / len(successful_queries)
                if successful_queries
                else 0
            )

            return {
                "total_queries": total_queries,
                "successful_queries": len(successful_queries),
                "failed_queries": len(failed_queries),
                "average_execution_time": avg_execution_time,
                "average_connection_time": avg_connection_time,
                "success_rate": len(successful_queries) / total_queries if total_queries > 0 else 0,
                "recent_queries": self.query_metrics[-10:],  # Last 10 queries
            }


class QueryOptimizer:
    """
    Intelligent query optimization engine.

    Features:
    - Query analysis and optimization suggestions
    - Index recommendations
    - Query rewriting
    - Execution plan analysis
    - Performance bottleneck detection
    """

    def __init__(self, executor: AsyncQueryExecutor):
        self.executor = executor
        self.query_patterns: Dict[str, Dict] = {}
        self.index_recommendations: Dict[str, List[str]] = {}

    async def analyze_query(self, sql: str, execution_time: float) -> Dict[str, Any]:
        """Analyze query performance and provide optimization suggestions."""
        analysis = {
            "query_type": self._classify_query(sql),
            "complexity_score": self._calculate_complexity(sql),
            "execution_time": execution_time,
            "optimization_suggestions": [],
        }

        # Check for common optimization opportunities
        if "SELECT *" in sql.upper():
            analysis["optimization_suggestions"].append("Consider selecting specific columns instead of SELECT *")

        if "WHERE" in sql.upper() and "INDEX" not in sql.upper():
            analysis["optimization_suggestions"].append("Consider adding indexes on WHERE clause columns")

        if "JOIN" in sql.upper():
            analysis["optimization_suggestions"].append("Review JOIN operations for optimization opportunities")

        if execution_time > 1.0:
            analysis["optimization_suggestions"].append("Query execution time is high, consider optimization")

        return analysis

    async def optimize_query(self, sql: str) -> str:
        """Attempt to optimize query automatically."""
        optimized = sql

        # Simple optimizations
        # Remove unnecessary spaces and formatting
        optimized = " ".join(optimized.split())

        # Add LIMIT if missing and it's a SELECT without aggregation
        if (
            sql.upper().strip().startswith("SELECT")
            and "LIMIT" not in sql.upper()
            and "GROUP BY" not in sql.upper()
            and "HAVING" not in sql.upper()
        ):
            # This is a risky optimization, so we'll skip it in practice
            pass

        return optimized

    def suggest_indexes(self, sql: str, execution_time: float) -> List[str]:
        """Suggest indexes based on query analysis."""
        suggestions = []

        # Simple index suggestions based on WHERE clauses
        if "WHERE" in sql.upper():
            # This would parse the WHERE clause and suggest indexes
            # Placeholder implementation
            suggestions.append("Consider adding index on frequently queried columns")

        if execution_time > 2.0:
            suggestions.append("High execution time suggests index optimization may be needed")

        return suggestions

    async def get_query_patterns(self) -> Dict[str, Any]:
        """Analyze query patterns for optimization opportunities."""
        report = await self.executor.get_performance_report()

        patterns = {
            "slow_queries": [m for m in report.get("recent_queries", []) if m.execution_time > 1.0],
            "frequent_queries": {},  # Would group by SQL hash
            "optimization_opportunities": [],
        }

        return patterns

    def _classify_query(self, sql: str) -> str:
        """Classify query type."""
        sql_upper = sql.upper().strip()

        if sql_upper.startswith("SELECT"):
            return "SELECT"
        elif sql_upper.startswith("INSERT"):
            return "INSERT"
        elif sql_upper.startswith("UPDATE"):
            return "UPDATE"
        elif sql_upper.startswith("DELETE"):
            return "DELETE"
        else:
            return "OTHER"

    def _calculate_complexity(self, sql: str) -> int:
        """Calculate query complexity score."""
        score = 0

        # Simple complexity heuristics
        score += sql.upper().count("JOIN") * 2
        score += sql.upper().count("WHERE") * 1
        score += sql.upper().count("GROUP BY") * 2
        score += sql.upper().count("ORDER BY") * 1
        score += sql.upper().count("HAVING") * 2
        score += sql.upper().count("UNION") * 3
        score += sql.upper().count("SUBQUERY") * 3

        # Length factor
        score += len(sql) // 1000

        return score
