"""
Redis-based Performance Repository Implementation.

Provides fast caching and real-time access to performance data.
TimescaleDB is used for long-term storage and complex analytics.
"""
import json
import redis.asyncio as redis
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from services.mcp_performance_store.domain.entities import (
    OrchestrationExecution,
    PatternPerformance
)
from services.mcp_performance_store.domain.repositories import PerformanceRepository
from services.mcp_performance_store.infrastructure.config import Settings


class RedisPerformanceRepository(PerformanceRepository):
    """
    Redis-based implementation of PerformanceRepository.
    
    Provides caching layer for fast access to recent executions
    and pattern performance metrics.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize Redis repository.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._redis_client: Optional[redis.Redis] = None
        
        # Key prefixes
        self.EXECUTION_PREFIX = "perf:execution:"
        self.PATTERN_PREFIX = "perf:pattern:"
        self.EXECUTION_LIST_PREFIX = "perf:executions:"
        self.STATS_PREFIX = "perf:stats:"
    
    async def connect(self):
        """Establish Redis connection."""
        if self._redis_client is None:
            self._redis_client = await redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=False,
                max_connections=self.settings.redis_pool_size
            )
            self.logger.info("Redis connection established")
    
    async def disconnect(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
            self.logger.info("Redis connection closed")
    
    @property
    def redis(self) -> redis.Redis:
        """Get Redis client."""
        if self._redis_client is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._redis_client
    
    # Orchestration Execution Methods
    
    async def save_execution(self, execution: OrchestrationExecution) -> str:
        """
        Save an orchestration execution to Redis cache.
        
        Args:
            execution: The execution to save
        
        Returns:
            The execution_id
        """
        key = f"{self.EXECUTION_PREFIX}{execution.execution_id}"
        
        # Serialize execution
        data = json.dumps(execution.to_dict(), default=str)
        
        # Store with TTL based on settings
        ttl = self.settings.cache_ttl_seconds
        await self.redis.setex(key, ttl, data)
        
        # Add to sorted set for time-based queries (score = timestamp)
        list_key = f"{self.EXECUTION_LIST_PREFIX}{execution.mcp_id}"
        timestamp = execution.timestamp.timestamp()
        await self.redis.zadd(list_key, {execution.execution_id: timestamp})
        await self.redis.expire(list_key, ttl)
        
        # Index by pattern
        pattern_list_key = f"{self.EXECUTION_LIST_PREFIX}pattern:{execution.pattern_used}"
        await self.redis.zadd(pattern_list_key, {execution.execution_id: timestamp})
        await self.redis.expire(pattern_list_key, ttl)
        
        self.logger.info(f"Saved execution {execution.execution_id} to Redis cache")
        return execution.execution_id
    
    async def get_execution(self, execution_id: str) -> Optional[OrchestrationExecution]:
        """
        Retrieve an execution by ID from Redis cache.
        
        Args:
            execution_id: ID of the execution
        
        Returns:
            The execution, or None if not found in cache
        """
        key = f"{self.EXECUTION_PREFIX}{execution_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        execution_dict = json.loads(data)
        return OrchestrationExecution(**execution_dict)
    
    async def list_executions(
        self,
        mcp_id: Optional[str] = None,
        pattern_used: Optional[str] = None,
        success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrchestrationExecution]:
        """
        List executions from Redis cache with filters.
        
        Note: This is a simplified implementation. Full filtering
        should use TimescaleDB for complex queries.
        
        Args:
            mcp_id: Filter by MCP ID
            pattern_used: Filter by pattern
            success: Filter by success status
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            offset: Offset for pagination
        
        Returns:
            List of matching executions from cache
        """
        # Determine which index to use
        if pattern_used:
            list_key = f"{self.EXECUTION_LIST_PREFIX}pattern:{pattern_used}"
        elif mcp_id:
            list_key = f"{self.EXECUTION_LIST_PREFIX}{mcp_id}"
        else:
            # No index available, return empty
            # Full scan would be expensive, delegate to TimescaleDB
            return []
        
        # Get execution IDs from sorted set
        start_score = start_time.timestamp() if start_time else "-inf"
        end_score = end_time.timestamp() if end_time else "+inf"
        
        execution_ids = await self.redis.zrangebyscore(
            list_key,
            start_score,
            end_score,
            start=offset,
            num=limit
        )
        
        if not execution_ids:
            return []
        
        # Fetch executions
        executions = []
        for exec_id in execution_ids:
            if isinstance(exec_id, bytes):
                exec_id = exec_id.decode('utf-8')
            execution = await self.get_execution(exec_id)
            if execution:
                # Apply additional filters
                if success is not None and execution.success != success:
                    continue
                executions.append(execution)
        
        return executions
    
    async def count_executions(
        self,
        mcp_id: Optional[str] = None,
        pattern_used: Optional[str] = None,
        success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        Count executions in Redis cache.
        
        Note: For accurate counts, use TimescaleDB.
        """
        executions = await self.list_executions(
            mcp_id=mcp_id,
            pattern_used=pattern_used,
            success=success,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        return len(executions)
    
    async def delete_execution(self, execution_id: str) -> bool:
        """
        Delete an execution from Redis cache.
        
        Args:
            execution_id: ID of the execution to delete
        
        Returns:
            True if deleted, False if not found
        """
        key = f"{self.EXECUTION_PREFIX}{execution_id}"
        result = await self.redis.delete(key)
        return result > 0
    
    # Pattern Performance Methods
    
    async def save_pattern_performance(self, performance: PatternPerformance) -> str:
        """
        Save pattern performance metrics to Redis.
        
        Args:
            performance: The pattern performance to save
        
        Returns:
            The pattern_id
        """
        key = f"{self.PATTERN_PREFIX}{performance.pattern_id}"
        
        # Serialize performance
        data = json.dumps(performance.to_dict(), default=str)
        
        # Store with longer TTL for aggregated data
        ttl = self.settings.cache_ttl_seconds * 10  # 10x longer
        await self.redis.setex(key, ttl, data)
        
        # Also store by name for lookup
        name_key = f"{self.PATTERN_PREFIX}name:{performance.pattern_name}:{performance.version}"
        await self.redis.setex(name_key, ttl, performance.pattern_id)
        
        self.logger.info(f"Saved pattern performance {performance.pattern_id} to Redis")
        return performance.pattern_id
    
    async def get_pattern_performance(self, pattern_id: str) -> Optional[PatternPerformance]:
        """
        Retrieve pattern performance by ID from Redis.
        
        Args:
            pattern_id: ID of the pattern
        
        Returns:
            The pattern performance, or None if not found
        """
        key = f"{self.PATTERN_PREFIX}{pattern_id}"
        data = await self.redis.get(key)
        
        if not data:
            return None
        
        performance_dict = json.loads(data)
        return PatternPerformance(**performance_dict)
    
    async def get_pattern_performance_by_name(
        self,
        pattern_name: str,
        version: Optional[str] = None
    ) -> Optional[PatternPerformance]:
        """
        Retrieve pattern performance by name and version.
        
        Args:
            pattern_name: Name of the pattern
            version: Version of the pattern (optional)
        
        Returns:
            The pattern performance, or None if not found
        """
        # If version not provided, use "latest"
        version = version or "latest"
        name_key = f"{self.PATTERN_PREFIX}name:{pattern_name}:{version}"
        
        pattern_id = await self.redis.get(name_key)
        if not pattern_id:
            return None
        
        if isinstance(pattern_id, bytes):
            pattern_id = pattern_id.decode('utf-8')
        
        return await self.get_pattern_performance(pattern_id)
    
    async def list_pattern_performances(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[PatternPerformance]:
        """
        List all pattern performances from Redis.
        
        Note: This scans keys, which can be expensive.
        For production, use TimescaleDB.
        """
        pattern = f"{self.PATTERN_PREFIX}*"
        cursor = 0
        performances = []
        count = 0
        
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            
            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                
                # Skip name lookup keys
                if ":name:" in key:
                    continue
                
                if count < offset:
                    count += 1
                    continue
                
                if len(performances) >= limit:
                    return performances
                
                data = await self.redis.get(key)
                if data:
                    perf_dict = json.loads(data)
                    performances.append(PatternPerformance(**perf_dict))
                    count += 1
            
            if cursor == 0:
                break
        
        return performances
    
    async def delete_pattern_performance(self, pattern_id: str) -> bool:
        """
        Delete pattern performance from Redis.
        
        Args:
            pattern_id: ID of the pattern
        
        Returns:
            True if deleted, False if not found
        """
        key = f"{self.PATTERN_PREFIX}{pattern_id}"
        result = await self.redis.delete(key)
        return result > 0
    
    # Analytics Methods (Simplified - Full implementation in TimescaleDB)
    
    async def get_execution_stats_by_pattern(
        self,
        pattern_used: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get cached statistics for a pattern.
        
        For real-time calculations, use TimescaleDB.
        """
        stats_key = f"{self.STATS_PREFIX}pattern:{pattern_used}"
        data = await self.redis.get(stats_key)
        
        if data:
            return json.loads(data)
        
        return {
            "pattern": pattern_used,
            "cached": False,
            "message": "Statistics not in cache. Query TimescaleDB for full analytics."
        }
    
    async def get_execution_stats_by_mcp(
        self,
        mcp_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get cached statistics for an MCP."""
        stats_key = f"{self.STATS_PREFIX}mcp:{mcp_id}"
        data = await self.redis.get(stats_key)
        
        if data:
            return json.loads(data)
        
        return {
            "mcp_id": mcp_id,
            "cached": False,
            "message": "Statistics not in cache. Query TimescaleDB for full analytics."
        }
    
    async def get_latency_percentiles(
        self,
        pattern_used: Optional[str] = None,
        mcp_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Get cached latency percentiles.
        
        For real-time calculations, use TimescaleDB.
        """
        return {
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "cached": False,
            "message": "Use TimescaleDB for percentile calculations"
        }
    
    async def detect_anomalies(
        self,
        pattern_used: Optional[str] = None,
        threshold_factor: float = 2.0
    ) -> List[OrchestrationExecution]:
        """
        Detect anomalies from cached data.
        
        For comprehensive anomaly detection, use TimescaleDB.
        """
        return []
    
    async def get_trend_data(
        self,
        pattern_used: str,
        time_window_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Get cached trend data.
        
        For real-time trend analysis, use TimescaleDB.
        """
        return []
    
    async def cache_stats(self, key: str, stats: Dict[str, Any], ttl: int = None):
        """
        Cache statistics for fast retrieval.
        
        Args:
            key: Cache key
            stats: Statistics to cache
            ttl: Time to live in seconds
        """
        if ttl is None:
            ttl = self.settings.cache_ttl_seconds
        
        data = json.dumps(stats, default=str)
        await self.redis.setex(key, ttl, data)
        self.logger.debug(f"Cached stats: {key}")
