"""Redis Composition Repository Implementation - Infrastructure Layer.

Implements CompositionRepository interface using Redis as the persistence layer.
"""

import logging
import json
from typing import List, Optional
import redis.asyncio as redis

from services.mcp_composer.domain.entities.composition import Composition
from services.mcp_composer.domain.repositories.composition_repository import (
    CompositionRepository,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
)


logger = logging.getLogger(__name__)


class RedisCompositionRepository(CompositionRepository):
    """
    Redis implementation of CompositionRepository.
    
    Uses Redis hashes to store Composition entities with the following structure:
    - Key: mcp-composer:composition:{composition_id}
    - Value: JSON serialized Composition
    
    Additional indices:
    - mcp-composer:compositions:all -> Set of all composition_ids
    - mcp-composer:compositions:active -> Set of active composition_ids
    - mcp-composer:compositions:tag:{tag} -> Set of composition_ids with tag
    """
    
    def __init__(self, redis_client: redis.Redis, key_prefix: str = "mcp-composer"):
        """
        Initialize repository.
        
        Args:
            redis_client: Async Redis client
            key_prefix: Prefix for Redis keys
        """
        self.redis = redis_client
        self.prefix = key_prefix
        
        logger.info(f"Redis Composition repository initialized (prefix: {self.prefix})")
    
    def _composition_key(self, composition_id: str) -> str:
        """Get Redis key for a composition."""
        return f"{self.prefix}:composition:{composition_id}"
    
    def _all_key(self) -> str:
        """Get Redis key for all compositions set."""
        return f"{self.prefix}:compositions:all"
    
    def _active_key(self) -> str:
        """Get Redis key for active compositions set."""
        return f"{self.prefix}:compositions:active"
    
    def _tag_key(self, tag: str) -> str:
        """Get Redis key for tag index."""
        return f"{self.prefix}:compositions:tag:{tag}"
    
    async def save(self, composition: Composition) -> None:
        """Save a composition to Redis."""
        try:
            composition_id = composition.composition_id
            composition_key = self._composition_key(composition_id)
            
            # Check if already exists
            exists = await self.redis.exists(composition_key)
            if exists:
                raise DuplicateEntityError(f"Composition {composition_id} already exists")
            
            # Serialize composition
            composition_data = json.dumps(composition.to_dict())
            
            # Save composition data
            await self.redis.set(composition_key, composition_data)
            
            # Update indices
            await self.redis.sadd(self._all_key(), composition_id)
            
            if composition.is_active:
                await self.redis.sadd(self._active_key(), composition_id)
            
            # Update tag indices
            for tag in composition.tags:
                await self.redis.sadd(self._tag_key(tag), composition_id)
            
            logger.info(f"Saved composition: {composition_id}")
            
        except DuplicateEntityError:
            raise
        except Exception as e:
            logger.error(f"Failed to save composition {composition_id}: {e}")
            raise RepositoryError(f"Failed to save composition: {e}")
    
    async def get_by_id(self, composition_id: str) -> Optional[Composition]:
        """Retrieve a composition by ID."""
        try:
            composition_key = self._composition_key(composition_id)
            
            # Get composition data
            data = await self.redis.get(composition_key)
            
            if not data:
                return None
            
            # Deserialize
            composition_dict = json.loads(data)
            composition = Composition.from_dict(composition_dict)
            
            return composition
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize composition {composition_id}: {e}")
            raise RepositoryError(f"Failed to deserialize composition: {e}")
        except Exception as e:
            logger.error(f"Failed to get composition {composition_id}: {e}")
            raise RepositoryError(f"Failed to get composition: {e}")
    
    async def get_all(self) -> List[Composition]:
        """Retrieve all compositions."""
        try:
            # Get all composition IDs
            composition_ids = await self.redis.smembers(self._all_key())
            
            if not composition_ids:
                return []
            
            # Get all compositions
            compositions = []
            for comp_id in composition_ids:
                comp_id_str = comp_id.decode('utf-8') if isinstance(comp_id, bytes) else comp_id
                composition = await self.get_by_id(comp_id_str)
                if composition:
                    compositions.append(composition)
            
            return compositions
            
        except Exception as e:
            logger.error(f"Failed to get all compositions: {e}")
            raise RepositoryError(f"Failed to get all compositions: {e}")
    
    async def get_active(self) -> List[Composition]:
        """Retrieve all active compositions."""
        try:
            # Get active composition IDs
            composition_ids = await self.redis.smembers(self._active_key())
            
            if not composition_ids:
                return []
            
            # Get active compositions
            compositions = []
            for comp_id in composition_ids:
                comp_id_str = comp_id.decode('utf-8') if isinstance(comp_id, bytes) else comp_id
                composition = await self.get_by_id(comp_id_str)
                if composition and composition.is_active:
                    compositions.append(composition)
            
            return compositions
            
        except Exception as e:
            logger.error(f"Failed to get active compositions: {e}")
            raise RepositoryError(f"Failed to get active compositions: {e}")
    
    async def update(self, composition: Composition) -> None:
        """Update an existing composition."""
        try:
            composition_id = composition.composition_id
            composition_key = self._composition_key(composition_id)
            
            # Check if exists
            exists = await self.redis.exists(composition_key)
            if not exists:
                raise EntityNotFoundError(f"Composition {composition_id} not found")
            
            # Get old composition for index cleanup
            old_data = await self.redis.get(composition_key)
            old_composition = None
            if old_data:
                old_dict = json.loads(old_data)
                old_composition = Composition.from_dict(old_dict)
            
            # Serialize new composition
            composition_data = json.dumps(composition.to_dict())
            
            # Update composition data
            await self.redis.set(composition_key, composition_data)
            
            # Update active index
            if composition.is_active:
                await self.redis.sadd(self._active_key(), composition_id)
            else:
                await self.redis.srem(self._active_key(), composition_id)
            
            # Update tag indices
            if old_composition:
                # Remove old tags
                for tag in old_composition.tags:
                    await self.redis.srem(self._tag_key(tag), composition_id)
            
            # Add new tags
            for tag in composition.tags:
                await self.redis.sadd(self._tag_key(tag), composition_id)
            
            logger.info(f"Updated composition: {composition_id}")
            
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update composition {composition_id}: {e}")
            raise RepositoryError(f"Failed to update composition: {e}")
    
    async def delete(self, composition_id: str) -> None:
        """Delete a composition by ID."""
        try:
            composition_key = self._composition_key(composition_id)
            
            # Get composition for index cleanup
            composition = await self.get_by_id(composition_id)
            
            if not composition:
                raise EntityNotFoundError(f"Composition {composition_id} not found")
            
            # Delete composition data
            await self.redis.delete(composition_key)
            
            # Remove from indices
            await self.redis.srem(self._all_key(), composition_id)
            await self.redis.srem(self._active_key(), composition_id)
            
            # Remove from tag indices
            for tag in composition.tags:
                await self.redis.srem(self._tag_key(tag), composition_id)
            
            logger.info(f"Deleted composition: {composition_id}")
            
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete composition {composition_id}: {e}")
            raise RepositoryError(f"Failed to delete composition: {e}")
    
    async def exists(self, composition_id: str) -> bool:
        """Check if a composition exists."""
        try:
            composition_key = self._composition_key(composition_id)
            return await self.redis.exists(composition_key) > 0
        except Exception as e:
            logger.error(f"Failed to check composition existence {composition_id}: {e}")
            raise RepositoryError(f"Failed to check existence: {e}")
    
    async def count(self) -> int:
        """Get the total number of compositions."""
        try:
            return await self.redis.scard(self._all_key())
        except Exception as e:
            logger.error(f"Failed to count compositions: {e}")
            raise RepositoryError(f"Failed to count compositions: {e}")
    
    async def get_by_tag(self, tag: str) -> List[Composition]:
        """Retrieve compositions by tag."""
        try:
            # Get composition IDs with tag
            composition_ids = await self.redis.smembers(self._tag_key(tag))
            
            if not composition_ids:
                return []
            
            # Get compositions
            compositions = []
            for comp_id in composition_ids:
                comp_id_str = comp_id.decode('utf-8') if isinstance(comp_id, bytes) else comp_id
                composition = await self.get_by_id(comp_id_str)
                if composition and tag in composition.tags:
                    compositions.append(composition)
            
            return compositions
            
        except Exception as e:
            logger.error(f"Failed to get compositions by tag {tag}: {e}")
            raise RepositoryError(f"Failed to get compositions by tag: {e}")
