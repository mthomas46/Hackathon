"""Redis MCP Context Repository Implementation - Infrastructure Layer.

Implements MCPContextRepository using Redis as the persistence layer.
"""

import logging
import json
from typing import List, Optional
from datetime import datetime
import redis.asyncio as redis

from services.mcp_infrastructure.domain.entities.mcp_context import MCPContext
from services.mcp_infrastructure.domain.value_objects.mcp_context_type import MCPContextType
from services.mcp_infrastructure.domain.repositories.mcp_context_repository import (
    MCPContextRepository,
    RepositoryError,
    EntityNotFoundError,
)
from services.mcp_infrastructure.infrastructure.config.settings import Settings


logger = logging.getLogger(__name__)


class RedisMCPContextRepository(MCPContextRepository):
    """
    Redis implementation of MCPContextRepository.
    
    Key Structure:
    - mcp:infra:context:{id} -> Hash: Context data
    - mcp:infra:index:mcp:{mcp_id} -> Set: Context IDs for MCP
    - mcp:infra:index:type:{type} -> Set: Context IDs by type
    - mcp:infra:index:tag:{tag} -> Set: Context IDs by tag
    - mcp:infra:index:all -> Set: All context IDs
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
        self.prefix = settings.redis_key_prefix
        logger.info(f"Redis MCP Context repository initialized (prefix: {self.prefix})")
    
    def _context_key(self, context_id: str) -> str:
        """Get Redis key for a context."""
        return f"{self.prefix}context:{context_id}"
    
    def _mcp_index_key(self, mcp_id: str) -> str:
        """Get Redis key for MCP index."""
        return f"{self.prefix}index:mcp:{mcp_id}"
    
    def _type_index_key(self, context_type: MCPContextType) -> str:
        """Get Redis key for type index."""
        return f"{self.prefix}index:type:{context_type.value}"
    
    def _tag_index_key(self, tag: str) -> str:
        """Get Redis key for tag index."""
        return f"{self.prefix}index:tag:{tag}"
    
    def _all_index_key(self) -> str:
        """Get Redis key for all contexts index."""
        return f"{self.prefix}index:all"
    
    async def save(self, context: MCPContext) -> None:
        """
        Save an MCP context to Redis.
        
        Stores the context data and updates all relevant indices.
        Sets TTL if specified.
        """
        try:
            context_id = context.id
            context_key = self._context_key(context_id)
            
            # Serialize context
            context_data = json.dumps(context.to_dict())
            
            # Save context data
            await self.redis.set(context_key, context_data)
            
            # Set TTL if specified
            if context.ttl > 0:
                await self.redis.expire(context_key, context.ttl)
            
            # Update indices
            await self.redis.sadd(self._all_index_key(), context_id)
            await self.redis.sadd(self._mcp_index_key(context.mcp_id), context_id)
            await self.redis.sadd(self._type_index_key(context.context_type), context_id)
            
            # Update tag indices
            for tag in context.tags:
                await self.redis.sadd(self._tag_index_key(tag), context_id)
            
            logger.debug(f"Saved context: {context_id} for MCP: {context.mcp_id}")
            
        except redis.RedisError as e:
            logger.error(f"Redis error saving context: {e}")
            raise RepositoryError(f"Failed to save context: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving context: {e}", exc_info=True)
            raise RepositoryError(f"Failed to save context: {e}")
    
    async def find_by_id(self, context_id: str) -> Optional[MCPContext]:
        """Find a context by its ID."""
        try:
            context_key = self._context_key(context_id)
            data = await self.redis.get(context_key)
            
            if not data:
                return None
            
            # Deserialize
            context_dict = json.loads(data)
            context = MCPContext.from_dict(context_dict)
            
            logger.debug(f"Found context: {context_id}")
            return context
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for context {context_id}: {e}")
            raise RepositoryError(f"Invalid context data: {e}")
        except redis.RedisError as e:
            logger.error(f"Redis error finding context: {e}")
            raise RepositoryError(f"Failed to find context: {e}")
        except Exception as e:
            logger.error(f"Unexpected error finding context: {e}", exc_info=True)
            raise RepositoryError(f"Failed to find context: {e}")
    
    async def find_by_mcp_id(
        self,
        mcp_id: str,
        context_type: Optional[MCPContextType] = None
    ) -> List[MCPContext]:
        """Find all contexts for an MCP instance."""
        try:
            # Get context IDs for this MCP
            context_ids = await self.redis.smembers(self._mcp_index_key(mcp_id))
            
            if not context_ids:
                return []
            
            # Fetch all contexts
            contexts = []
            for context_id in context_ids:
                context_id_str = context_id.decode() if isinstance(context_id, bytes) else context_id
                context = await self.find_by_id(context_id_str)
                
                if context:
                    # Apply type filter if specified
                    if context_type is None or context.context_type == context_type:
                        contexts.append(context)
            
            logger.debug(f"Found {len(contexts)} contexts for MCP: {mcp_id}")
            return contexts
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding contexts by MCP ID: {e}")
            raise RepositoryError(f"Failed to find contexts: {e}")
        except Exception as e:
            logger.error(f"Unexpected error finding contexts by MCP ID: {e}", exc_info=True)
            raise RepositoryError(f"Failed to find contexts: {e}")
    
    async def find_by_type(self, context_type: MCPContextType) -> List[MCPContext]:
        """Find all contexts of a specific type."""
        try:
            # Get context IDs for this type
            context_ids = await self.redis.smembers(self._type_index_key(context_type))
            
            if not context_ids:
                return []
            
            # Fetch all contexts
            contexts = []
            for context_id in context_ids:
                context_id_str = context_id.decode() if isinstance(context_id, bytes) else context_id
                context = await self.find_by_id(context_id_str)
                
                if context:
                    contexts.append(context)
            
            logger.debug(f"Found {len(contexts)} contexts of type: {context_type.value}")
            return contexts
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding contexts by type: {e}")
            raise RepositoryError(f"Failed to find contexts: {e}")
        except Exception as e:
            logger.error(f"Unexpected error finding contexts by type: {e}", exc_info=True)
            raise RepositoryError(f"Failed to find contexts: {e}")
    
    async def find_by_tags(self, tags: List[str]) -> List[MCPContext]:
        """Find contexts by tags (OR search)."""
        try:
            # Get union of all tag sets (OR search)
            if not tags:
                return []
            
            tag_keys = [self._tag_index_key(tag) for tag in tags]
            context_ids = await self.redis.sunion(*tag_keys)
            
            if not context_ids:
                return []
            
            # Fetch all contexts
            contexts = []
            for context_id in context_ids:
                context_id_str = context_id.decode() if isinstance(context_id, bytes) else context_id
                context = await self.find_by_id(context_id_str)
                
                if context:
                    contexts.append(context)
            
            logger.debug(f"Found {len(contexts)} contexts with tags: {tags}")
            return contexts
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding contexts by tags: {e}")
            raise RepositoryError(f"Failed to find contexts: {e}")
        except Exception as e:
            logger.error(f"Unexpected error finding contexts by tags: {e}", exc_info=True)
            raise RepositoryError(f"Failed to find contexts: {e}")
    
    async def delete(self, context_id: str) -> bool:
        """Delete a context."""
        try:
            # Get context first to remove from indices
            context = await self.find_by_id(context_id)
            if not context:
                return False
            
            # Delete from all indices
            await self.redis.srem(self._all_index_key(), context_id)
            await self.redis.srem(self._mcp_index_key(context.mcp_id), context_id)
            await self.redis.srem(self._type_index_key(context.context_type), context_id)
            
            # Delete from tag indices
            for tag in context.tags:
                await self.redis.srem(self._tag_index_key(tag), context_id)
            
            # Delete context data
            deleted_count = await self.redis.delete(self._context_key(context_id))
            
            logger.debug(f"Deleted context: {context_id}")
            return deleted_count > 0
            
        except redis.RedisError as e:
            logger.error(f"Redis error deleting context: {e}")
            raise RepositoryError(f"Failed to delete context: {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting context: {e}", exc_info=True)
            raise RepositoryError(f"Failed to delete context: {e}")
    
    async def delete_by_mcp_id(self, mcp_id: str) -> int:
        """Delete all contexts for an MCP instance."""
        try:
            # Get all context IDs for this MCP
            context_ids = await self.redis.smembers(self._mcp_index_key(mcp_id))
            
            if not context_ids:
                return 0
            
            # Delete each context
            deleted_count = 0
            for context_id in context_ids:
                context_id_str = context_id.decode() if isinstance(context_id, bytes) else context_id
                if await self.delete(context_id_str):
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} contexts for MCP: {mcp_id}")
            return deleted_count
            
        except redis.RedisError as e:
            logger.error(f"Redis error deleting contexts by MCP ID: {e}")
            raise RepositoryError(f"Failed to delete contexts: {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting contexts by MCP ID: {e}", exc_info=True)
            raise RepositoryError(f"Failed to delete contexts: {e}")
    
    async def delete_expired(self) -> int:
        """Delete all expired contexts."""
        try:
            # Get all context IDs
            context_ids = await self.redis.smembers(self._all_index_key())
            
            if not context_ids:
                return 0
            
            # Check each context for expiration
            deleted_count = 0
            for context_id in context_ids:
                context_id_str = context_id.decode() if isinstance(context_id, bytes) else context_id
                context = await self.find_by_id(context_id_str)
                
                if context and context.is_expired():
                    if await self.delete(context_id_str):
                        deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} expired contexts")
            return deleted_count
            
        except redis.RedisError as e:
            logger.error(f"Redis error deleting expired contexts: {e}")
            raise RepositoryError(f"Failed to delete expired contexts: {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting expired contexts: {e}", exc_info=True)
            raise RepositoryError(f"Failed to delete expired contexts: {e}")
    
    async def count(self) -> int:
        """Get total number of contexts."""
        try:
            count = await self.redis.scard(self._all_index_key())
            return count
        except redis.RedisError as e:
            logger.error(f"Redis error counting contexts: {e}")
            raise RepositoryError(f"Failed to count contexts: {e}")
    
    async def count_by_type(self, context_type: MCPContextType) -> int:
        """Get count of contexts by type."""
        try:
            count = await self.redis.scard(self._type_index_key(context_type))
            return count
        except redis.RedisError as e:
            logger.error(f"Redis error counting by type: {e}")
            raise RepositoryError(f"Failed to count by type: {e}")
    
    async def count_total(self) -> int:
        """Get total number of contexts."""
        return await self.count()
    
    async def delete_by_id(self, context_id: str) -> None:
        """Delete a context by ID, raises error if not found."""
        deleted = await self.delete(context_id)
        if not deleted:
            raise EntityNotFoundError(f"Context not found: {context_id}")
    
    async def find_all(self, limit: Optional[int] = None) -> List[MCPContext]:
        """Get all contexts with optional limit."""
        try:
            # Get all context IDs
            context_ids = await self.redis.smembers(self._all_index_key())
            
            if not context_ids:
                return []
            
            # Fetch all contexts
            contexts = []
            for i, context_id in enumerate(context_ids):
                if limit and i >= limit:
                    break
                
                context_id_str = context_id.decode() if isinstance(context_id, bytes) else context_id
                context = await self.find_by_id(context_id_str)
                
                if context:
                    contexts.append(context)
            
            logger.debug(f"Found {len(contexts)} contexts (limit={limit})")
            return contexts
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding all contexts: {e}")
            raise RepositoryError(f"Failed to find all contexts: {e}")
        except Exception as e:
            logger.error(f"Unexpected error finding all contexts: {e}", exc_info=True)
            raise RepositoryError(f"Failed to find all contexts: {e}")
    
    async def search_by_tags(
        self, tags: List[str], mcp_id: Optional[str] = None
    ) -> List[MCPContext]:
        """Search for contexts with specific tags, optionally filtered by MCP ID."""
        contexts = await self.find_by_tags(tags)
        
        # Apply MCP ID filter if specified
        if mcp_id:
            contexts = [ctx for ctx in contexts if ctx.mcp_id == mcp_id]
        
        return contexts

