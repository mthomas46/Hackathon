"""Redis implementation of Query Cache Repository."""

import json
import logging
import hashlib
from typing import Optional

import redis.asyncio as redis

from services.mcp_interpreter.domain.entities.parsed_query import ParsedQuery
from services.mcp_interpreter.domain.repositories.query_cache_repository import QueryCacheRepository
from services.mcp_interpreter.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class RedisQueryCacheRepository(QueryCacheRepository):
    """
    Redis implementation of the Query Cache Repository.
    
    Uses Redis for fast caching of parsed queries.
    """
    
    def __init__(self, redis_client: redis.Redis, settings: Settings):
        """
        Initialize the repository.
        
        Args:
            redis_client: Async Redis client
            settings: Application settings
        """
        self.redis = redis_client
        self.settings = settings
        self.KEY_PREFIX = settings.redis_key_prefix
    
    def _query_text_key(self, query_text: str) -> str:
        """Generate Redis key for query text lookup."""
        # Hash the query text for consistent key length
        query_hash = hashlib.md5(query_text.encode()).hexdigest()
        return f"{self.KEY_PREFIX}query_text:{query_hash}"
    
    def _query_id_key(self, query_id: str) -> str:
        """Generate Redis key for query ID lookup."""
        return f"{self.KEY_PREFIX}query_id:{query_id}"
    
    def _all_queries_key(self) -> str:
        """Generate Redis key for all queries set."""
        return f"{self.KEY_PREFIX}all_queries"
    
    async def save(self, query: ParsedQuery, ttl_seconds: int = 3600) -> None:
        """Save a parsed query to cache."""
        try:
            # Serialize query
            query_data = json.dumps(query.to_dict())
            
            # Keys
            text_key = self._query_text_key(query.normalized_query)
            id_key = self._query_id_key(query.id)
            
            # Save with both keys (for dual lookup)
            pipeline = self.redis.pipeline()
            pipeline.set(text_key, query_data, ex=ttl_seconds)
            pipeline.set(id_key, query_data, ex=ttl_seconds)
            pipeline.sadd(self._all_queries_key(), query.id)
            await pipeline.execute()
            
            logger.debug(f"Cached query {query.id} for {ttl_seconds}s")
            
        except redis.RedisError as e:
            logger.error(f"Redis error caching query {query.id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error caching query {query.id}: {e}", exc_info=True)
            raise
    
    async def find_by_query_text(self, query_text: str) -> Optional[ParsedQuery]:
        """Find a cached parsed query by query text."""
        try:
            # Normalize for lookup
            normalized = query_text.strip().lower()
            text_key = self._query_text_key(normalized)
            
            data = await self.redis.get(text_key)
            if not data:
                return None
            
            query_dict = json.loads(data)
            return ParsedQuery.from_dict(query_dict)
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding query by text: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error finding query by text: {e}", exc_info=True)
            raise
    
    async def find_by_id(self, query_id: str) -> Optional[ParsedQuery]:
        """Find a cached parsed query by ID."""
        try:
            id_key = self._query_id_key(query_id)
            
            data = await self.redis.get(id_key)
            if not data:
                return None
            
            query_dict = json.loads(data)
            return ParsedQuery.from_dict(query_dict)
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding query {query_id}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for query {query_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error finding query {query_id}: {e}", exc_info=True)
            raise
    
    async def delete(self, query_id: str) -> bool:
        """Delete a cached query by ID."""
        try:
            # Get query first to find text key
            query = await self.find_by_id(query_id)
            if not query:
                return False
            
            # Delete both keys
            text_key = self._query_text_key(query.normalized_query)
            id_key = self._query_id_key(query_id)
            
            pipeline = self.redis.pipeline()
            pipeline.delete(text_key)
            pipeline.delete(id_key)
            pipeline.srem(self._all_queries_key(), query_id)
            await pipeline.execute()
            
            logger.debug(f"Deleted cached query {query_id}")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis error deleting query {query_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting query {query_id}: {e}", exc_info=True)
            raise
    
    async def clear_cache(self) -> int:
        """Clear all cached queries."""
        try:
            # Get all query IDs
            all_queries = await self.redis.smembers(self._all_queries_key())
            
            if not all_queries:
                return 0
            
            # Delete all queries
            deleted_count = 0
            for query_id_bytes in all_queries:
                query_id = query_id_bytes.decode()
                if await self.delete(query_id):
                    deleted_count += 1
            
            # Clear the set
            await self.redis.delete(self._all_queries_key())
            
            logger.info(f"Cleared {deleted_count} cached queries")
            return deleted_count
            
        except redis.RedisError as e:
            logger.error(f"Redis error clearing cache: {e}")
            raise
        except Exception as e:
            logger.error(f"Error clearing cache: {e}", exc_info=True)
            raise

