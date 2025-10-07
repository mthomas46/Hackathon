"""Redis Pattern Performance Repository Implementation."""

import logging
import json
from typing import List, Optional
import redis.asyncio as redis

from services.mcp_performance_store.domain.entities.pattern_performance import PatternPerformance
from services.mcp_performance_store.domain.repositories.pattern_performance_repository import (
    PatternPerformanceRepository,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
)

logger = logging.getLogger(__name__)


class RedisPatternPerformanceRepository(PatternPerformanceRepository):
    """
    Redis implementation of PatternPerformanceRepository.
    
    Keys:
    - {prefix}:pattern:{pattern_name} -> JSON pattern performance
    - {prefix}:patterns:all -> Set of all pattern names
    - {prefix}:patterns:degrading -> Set of degrading pattern names
    """
    
    def __init__(self, redis_client: redis.Redis, key_prefix: str = "mcp-perf"):
        """Initialize repository."""
        self.redis = redis_client
        self.prefix = key_prefix
        logger.info(f"Redis Pattern Performance repository initialized (prefix: {self.prefix})")
    
    def _pattern_key(self, pattern_name: str) -> str:
        """Get Redis key for a pattern."""
        return f"{self.prefix}:pattern:{pattern_name}"
    
    def _all_key(self) -> str:
        """Get Redis key for all patterns set."""
        return f"{self.prefix}:patterns:all"
    
    def _degrading_key(self) -> str:
        """Get Redis key for degrading patterns set."""
        return f"{self.prefix}:patterns:degrading"
    
    async def save(self, performance: PatternPerformance) -> None:
        """Save pattern performance."""
        try:
            pattern_key = self._pattern_key(performance.pattern_name)
            
            # Check if already exists
            exists = await self.redis.exists(pattern_key)
            if exists:
                raise DuplicateEntityError(f"Pattern {performance.pattern_name} already exists")
            
            # Serialize
            data = json.dumps(performance.to_dict())
            
            # Save
            await self.redis.set(pattern_key, data)
            await self.redis.sadd(self._all_key(), performance.pattern_name)
            
            # Update degrading index if needed
            if performance.is_degrading():
                await self.redis.sadd(self._degrading_key(), performance.pattern_name)
            
            logger.info(f"Saved pattern performance: {performance.pattern_name}")
            
        except DuplicateEntityError:
            raise
        except Exception as e:
            logger.error(f"Failed to save pattern {performance.pattern_name}: {e}")
            raise RepositoryError(f"Failed to save pattern: {e}")
    
    async def get_by_pattern(self, pattern_name: str) -> Optional[PatternPerformance]:
        """Retrieve pattern performance."""
        try:
            pattern_key = self._pattern_key(pattern_name)
            data = await self.redis.get(pattern_key)
            
            if not data:
                return None
            
            perf_dict = json.loads(data)
            return PatternPerformance.from_dict(perf_dict)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize pattern {pattern_name}: {e}")
            raise RepositoryError(f"Failed to deserialize pattern: {e}")
        except Exception as e:
            logger.error(f"Failed to get pattern {pattern_name}: {e}")
            raise RepositoryError(f"Failed to get pattern: {e}")
    
    async def get_all(self) -> List[PatternPerformance]:
        """Retrieve all pattern performances."""
        try:
            pattern_names = await self.redis.smembers(self._all_key())
            
            if not pattern_names:
                return []
            
            patterns = []
            for name in pattern_names:
                name_str = name.decode('utf-8') if isinstance(name, bytes) else name
                pattern = await self.get_by_pattern(name_str)
                if pattern:
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to get all patterns: {e}")
            raise RepositoryError(f"Failed to get all patterns: {e}")
    
    async def get_top_performers(self, limit: int = 10) -> List[PatternPerformance]:
        """Get top performing patterns."""
        try:
            all_patterns = await self.get_all()
            # Sort by success rate descending
            sorted_patterns = sorted(all_patterns, key=lambda p: p.get_success_rate(), reverse=True)
            return sorted_patterns[:limit]
        except Exception as e:
            logger.error(f"Failed to get top performers: {e}")
            raise RepositoryError(f"Failed to get top performers: {e}")
    
    async def get_degrading_patterns(self) -> List[PatternPerformance]:
        """Get patterns with degrading performance."""
        try:
            degrading_names = await self.redis.smembers(self._degrading_key())
            
            if not degrading_names:
                return []
            
            patterns = []
            for name in degrading_names:
                name_str = name.decode('utf-8') if isinstance(name, bytes) else name
                pattern = await self.get_by_pattern(name_str)
                if pattern and pattern.is_degrading():
                    patterns.append(pattern)
                elif pattern and not pattern.is_degrading():
                    # Remove from degrading set if no longer degrading
                    await self.redis.srem(self._degrading_key(), name)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to get degrading patterns: {e}")
            raise RepositoryError(f"Failed to get degrading patterns: {e}")
    
    async def update(self, performance: PatternPerformance) -> None:
        """Update pattern performance."""
        try:
            pattern_key = self._pattern_key(performance.pattern_name)
            
            # Check if exists
            exists = await self.redis.exists(pattern_key)
            if not exists:
                raise EntityNotFoundError(f"Pattern {performance.pattern_name} not found")
            
            # Serialize
            data = json.dumps(performance.to_dict())
            
            # Update
            await self.redis.set(pattern_key, data)
            
            # Update degrading index
            if performance.is_degrading():
                await self.redis.sadd(self._degrading_key(), performance.pattern_name)
            else:
                await self.redis.srem(self._degrading_key(), performance.pattern_name)
            
            logger.info(f"Updated pattern performance: {performance.pattern_name}")
            
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update pattern {performance.pattern_name}: {e}")
            raise RepositoryError(f"Failed to update pattern: {e}")
    
    async def exists(self, pattern_name: str) -> bool:
        """Check if pattern exists."""
        try:
            return await self.redis.exists(self._pattern_key(pattern_name)) > 0
        except Exception as e:
            logger.error(f"Failed to check pattern existence {pattern_name}: {e}")
            raise RepositoryError(f"Failed to check existence: {e}")
    
    async def count(self) -> int:
        """Get total number of patterns."""
        try:
            return await self.redis.scard(self._all_key())
        except Exception as e:
            logger.error(f"Failed to count patterns: {e}")
            raise RepositoryError(f"Failed to count patterns: {e}")
    
    async def delete(self, pattern_name: str) -> None:
        """Delete pattern performance."""
        try:
            pattern_key = self._pattern_key(pattern_name)
            
            # Check if exists
            exists = await self.redis.exists(pattern_key)
            if not exists:
                raise EntityNotFoundError(f"Pattern {pattern_name} not found")
            
            # Delete
            await self.redis.delete(pattern_key)
            await self.redis.srem(self._all_key(), pattern_name)
            await self.redis.srem(self._degrading_key(), pattern_name)
            
            logger.info(f"Deleted pattern: {pattern_name}")
            
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete pattern {pattern_name}: {e}")
            raise RepositoryError(f"Failed to delete pattern: {e}")
