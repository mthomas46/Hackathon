"""Redis Execution Repository Implementation."""

import logging
import json
from typing import List, Optional
from datetime import datetime
import redis.asyncio as redis

from services.mcp_performance_store.domain.entities.orchestration_execution import OrchestrationExecution
from services.mcp_performance_store.domain.value_objects.execution_status import ExecutionStatus
from services.mcp_performance_store.domain.repositories.execution_repository import (
    ExecutionRepository,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
)

logger = logging.getLogger(__name__)


class RedisExecutionRepository(ExecutionRepository):
    """
    Redis implementation of ExecutionRepository.
    
    Keys:
    - {prefix}:execution:{execution_id} -> JSON execution
    - {prefix}:executions:all -> Sorted set (score=timestamp, member=execution_id)
    - {prefix}:executions:status:{status} -> Set of execution_ids
    - {prefix}:executions:pattern:{pattern} -> Sorted set (score=timestamp)
    - {prefix}:executions:composition:{comp_id} -> Sorted set (score=timestamp)
    """
    
    def __init__(self, redis_client: redis.Redis, key_prefix: str = "mcp-perf"):
        """Initialize repository."""
        self.redis = redis_client
        self.prefix = key_prefix
        logger.info(f"Redis Execution repository initialized (prefix: {self.prefix})")
    
    def _execution_key(self, execution_id: str) -> str:
        """Get Redis key for an execution."""
        return f"{self.prefix}:execution:{execution_id}"
    
    def _all_key(self) -> str:
        """Get Redis key for all executions sorted set."""
        return f"{self.prefix}:executions:all"
    
    def _status_key(self, status: ExecutionStatus) -> str:
        """Get Redis key for status set."""
        return f"{self.prefix}:executions:status:{status.value}"
    
    def _pattern_key(self, pattern_name: str) -> str:
        """Get Redis key for pattern sorted set."""
        return f"{self.prefix}:executions:pattern:{pattern_name}"
    
    def _composition_key(self, composition_id: str) -> str:
        """Get Redis key for composition sorted set."""
        return f"{self.prefix}:executions:composition:{composition_id}"
    
    async def save(self, execution: OrchestrationExecution) -> None:
        """Save an execution."""
        try:
            exec_key = self._execution_key(execution.execution_id)
            
            # Check if already exists
            exists = await self.redis.exists(exec_key)
            if exists:
                raise DuplicateEntityError(f"Execution {execution.execution_id} already exists")
            
            # Serialize
            data = json.dumps(execution.to_dict())
            
            # Save
            await self.redis.set(exec_key, data)
            
            # Add to indices
            timestamp = execution.start_time.timestamp() if execution.start_time else datetime.now().timestamp()
            
            # All executions sorted set
            await self.redis.zadd(self._all_key(), {execution.execution_id: timestamp})
            
            # Status index
            await self.redis.sadd(self._status_key(execution.status), execution.execution_id)
            
            # Pattern index (if pattern exists)
            if execution.pattern_name:
                await self.redis.zadd(
                    self._pattern_key(execution.pattern_name),
                    {execution.execution_id: timestamp}
                )
            
            # Composition index (if composition exists)
            if execution.composition_id:
                await self.redis.zadd(
                    self._composition_key(execution.composition_id),
                    {execution.execution_id: timestamp}
                )
            
            logger.info(f"Saved execution: {execution.execution_id}")
            
        except DuplicateEntityError:
            raise
        except Exception as e:
            logger.error(f"Failed to save execution {execution.execution_id}: {e}")
            raise RepositoryError(f"Failed to save execution: {e}")
    
    async def get_by_id(self, execution_id: str) -> Optional[OrchestrationExecution]:
        """Retrieve an execution by ID."""
        try:
            exec_key = self._execution_key(execution_id)
            data = await self.redis.get(exec_key)
            
            if not data:
                return None
            
            exec_dict = json.loads(data)
            return OrchestrationExecution.from_dict(exec_dict)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize execution {execution_id}: {e}")
            raise RepositoryError(f"Failed to deserialize execution: {e}")
        except Exception as e:
            logger.error(f"Failed to get execution {execution_id}: {e}")
            raise RepositoryError(f"Failed to get execution: {e}")
    
    async def get_by_pattern(
        self,
        pattern_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrchestrationExecution]:
        """Retrieve executions for a pattern."""
        try:
            pattern_key = self._pattern_key(pattern_name)
            
            # Get execution IDs from sorted set (newest first)
            execution_ids = await self.redis.zrevrange(
                pattern_key,
                offset,
                offset + limit - 1
            )
            
            if not execution_ids:
                return []
            
            executions = []
            for exec_id in execution_ids:
                exec_id_str = exec_id.decode('utf-8') if isinstance(exec_id, bytes) else exec_id
                execution = await self.get_by_id(exec_id_str)
                if execution:
                    executions.append(execution)
            
            return executions
            
        except Exception as e:
            logger.error(f"Failed to get executions for pattern {pattern_name}: {e}")
            raise RepositoryError(f"Failed to get executions by pattern: {e}")
    
    async def get_by_status(
        self,
        status: ExecutionStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrchestrationExecution]:
        """Retrieve executions by status."""
        try:
            status_key = self._status_key(status)
            
            # Get execution IDs from set
            execution_ids = await self.redis.smembers(status_key)
            
            if not execution_ids:
                return []
            
            # Convert to list and handle offset/limit
            execution_ids_list = list(execution_ids)[offset:offset + limit]
            
            executions = []
            for exec_id in execution_ids_list:
                exec_id_str = exec_id.decode('utf-8') if isinstance(exec_id, bytes) else exec_id
                execution = await self.get_by_id(exec_id_str)
                if execution:
                    executions.append(execution)
            
            # Sort by timestamp (newest first)
            executions.sort(key=lambda e: e.start_time or datetime.min, reverse=True)
            
            return executions
            
        except Exception as e:
            logger.error(f"Failed to get executions by status {status}: {e}")
            raise RepositoryError(f"Failed to get executions by status: {e}")
    
    async def get_by_date_range(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000
    ) -> List[OrchestrationExecution]:
        """Retrieve executions within a date range."""
        try:
            # Use sorted set with timestamp scores
            start_score = start.timestamp()
            end_score = end.timestamp()
            
            execution_ids = await self.redis.zrangebyscore(
                self._all_key(),
                start_score,
                end_score,
                start=0,
                num=limit
            )
            
            if not execution_ids:
                return []
            
            executions = []
            for exec_id in execution_ids:
                exec_id_str = exec_id.decode('utf-8') if isinstance(exec_id, bytes) else exec_id
                execution = await self.get_by_id(exec_id_str)
                if execution:
                    executions.append(execution)
            
            return executions
            
        except Exception as e:
            logger.error(f"Failed to get executions by date range: {e}")
            raise RepositoryError(f"Failed to get executions by date range: {e}")
    
    async def get_recent(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrchestrationExecution]:
        """Retrieve most recent executions."""
        try:
            # Get execution IDs from sorted set (newest first)
            execution_ids = await self.redis.zrevrange(
                self._all_key(),
                offset,
                offset + limit - 1
            )
            
            if not execution_ids:
                return []
            
            executions = []
            for exec_id in execution_ids:
                exec_id_str = exec_id.decode('utf-8') if isinstance(exec_id, bytes) else exec_id
                execution = await self.get_by_id(exec_id_str)
                if execution:
                    executions.append(execution)
            
            return executions
            
        except Exception as e:
            logger.error(f"Failed to get recent executions: {e}")
            raise RepositoryError(f"Failed to get recent executions: {e}")
    
    async def get_by_composition(
        self,
        composition_id: str,
        limit: int = 100
    ) -> List[OrchestrationExecution]:
        """Retrieve executions for a composition."""
        try:
            comp_key = self._composition_key(composition_id)
            
            # Get execution IDs from sorted set (newest first)
            execution_ids = await self.redis.zrevrange(comp_key, 0, limit - 1)
            
            if not execution_ids:
                return []
            
            executions = []
            for exec_id in execution_ids:
                exec_id_str = exec_id.decode('utf-8') if isinstance(exec_id, bytes) else exec_id
                execution = await self.get_by_id(exec_id_str)
                if execution:
                    executions.append(execution)
            
            return executions
            
        except Exception as e:
            logger.error(f"Failed to get executions for composition {composition_id}: {e}")
            raise RepositoryError(f"Failed to get executions by composition: {e}")
    
    async def count(self) -> int:
        """Get total number of executions."""
        try:
            return await self.redis.zcard(self._all_key())
        except Exception as e:
            logger.error(f"Failed to count executions: {e}")
            raise RepositoryError(f"Failed to count executions: {e}")
    
    async def count_by_status(self, status: ExecutionStatus) -> int:
        """Get count of executions by status."""
        try:
            return await self.redis.scard(self._status_key(status))
        except Exception as e:
            logger.error(f"Failed to count executions by status {status}: {e}")
            raise RepositoryError(f"Failed to count by status: {e}")
    
    async def count_by_pattern(self, pattern_name: str) -> int:
        """Get count of executions for a pattern."""
        try:
            return await self.redis.zcard(self._pattern_key(pattern_name))
        except Exception as e:
            logger.error(f"Failed to count executions for pattern {pattern_name}: {e}")
            raise RepositoryError(f"Failed to count by pattern: {e}")
    
    async def delete(self, execution_id: str) -> None:
        """Delete an execution."""
        try:
            # Get execution first to remove from indices
            execution = await self.get_by_id(execution_id)
            if not execution:
                raise EntityNotFoundError(f"Execution {execution_id} not found")
            
            exec_key = self._execution_key(execution_id)
            
            # Delete from main key
            await self.redis.delete(exec_key)
            
            # Remove from indices
            await self.redis.zrem(self._all_key(), execution_id)
            await self.redis.srem(self._status_key(execution.status), execution_id)
            
            if execution.pattern_name:
                await self.redis.zrem(self._pattern_key(execution.pattern_name), execution_id)
            
            if execution.composition_id:
                await self.redis.zrem(self._composition_key(execution.composition_id), execution_id)
            
            logger.info(f"Deleted execution: {execution_id}")
            
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete execution {execution_id}: {e}")
            raise RepositoryError(f"Failed to delete execution: {e}")
