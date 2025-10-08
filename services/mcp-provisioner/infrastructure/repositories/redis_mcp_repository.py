"""Redis MCP Repository Implementation - Infrastructure Layer.

Implements MCPRepository interface using Redis as the persistence layer.
"""

import logging
import json
from typing import List, Optional
import redis.asyncio as redis

from services.mcp_provisioner.domain.entities.mcp_instance import MCPInstance
from services.mcp_provisioner.domain.value_objects.mcp_state import MCPState
from services.mcp_provisioner.domain.repositories.mcp_repository import (
    MCPRepository,
    RepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
)
from services.mcp_provisioner.infrastructure.config.settings import Settings


logger = logging.getLogger(__name__)


class RedisMCPRepository(MCPRepository):
    """
    Redis implementation of MCPRepository.
    
    Uses Redis hashes to store MCP instances with the following structure:
    - Key: {prefix}instance:{mcp_id}
    - Value: JSON serialized MCPInstance
    
    Additional indices:
    - {prefix}state:{state} -> Set of mcp_ids
    - {prefix}tier:{tier} -> Set of mcp_ids
    - {prefix}all -> Set of all mcp_ids
    """
    
    def __init__(self, redis_client: redis.Redis, settings: Settings):
        """
        Initialize repository.
        
        Args:
            redis_client: Async Redis client
            settings: Application settings
        """
        self.redis = redis_client
        self.settings = settings
        self.prefix = settings.redis_key_prefix
        
        logger.info(f"Redis MCP repository initialized (prefix: {self.prefix})")
    
    def _instance_key(self, mcp_id: str) -> str:
        """Get Redis key for an instance."""
        return f"{self.prefix}instance:{mcp_id}"
    
    def _state_key(self, state: MCPState) -> str:
        """Get Redis key for state index."""
        # MCPState has state.state.value, not state.value
        return f"{self.prefix}state:{state.state.value}"
    
    def _tier_key(self, tier: int) -> str:
        """Get Redis key for tier index."""
        return f"{self.prefix}tier:{tier}"
    
    def _all_key(self) -> str:
        """Get Redis key for all instances set."""
        return f"{self.prefix}all"
    
    async def save(self, instance: MCPInstance) -> None:
        """Save an MCP instance to Redis."""
        try:
            # Entity uses mcp_id, not id
            mcp_id = instance.mcp_id
            instance_key = self._instance_key(mcp_id)
            
            # Serialize instance
            instance_data = json.dumps(instance.to_dict())
            
            # Save instance data
            await self.redis.set(instance_key, instance_data)
            
            # Update indices
            await self.redis.sadd(self._all_key(), mcp_id)
            await self.redis.sadd(self._state_key(instance.state), mcp_id)
            
            # Update tier index - check both config and metadata
            tier = None
            if instance.config and hasattr(instance.config, 'tier'):
                tier = instance.config.tier
            elif hasattr(instance, 'metadata') and instance.metadata and "tier" in instance.metadata:
                tier = instance.metadata["tier"]
            
            if tier is not None:
                await self.redis.sadd(self._tier_key(tier), mcp_id)
            
            logger.debug(f"Saved MCP instance: {mcp_id}")
            
        except redis.RedisError as e:
            logger.error(f"Redis error saving instance: {e}")
            raise RepositoryError(f"Failed to save instance: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving instance: {e}", exc_info=True)
            raise RepositoryError(f"Failed to save instance: {e}")
    
    async def find_by_id(self, mcp_id: str) -> Optional[MCPInstance]:
        """Find an MCP instance by ID."""
        try:
            instance_key = self._instance_key(mcp_id)
            data = await self.redis.get(instance_key)
            
            if not data:
                return None
            
            # Deserialize
            instance_dict = json.loads(data)
            instance = MCPInstance.from_dict(instance_dict)
            
            logger.debug(f"Found MCP instance: {mcp_id}")
            return instance
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for instance {mcp_id}: {e}")
            raise RepositoryError(f"Invalid instance data: {e}")
        except redis.RedisError as e:
            logger.error(f"Redis error finding instance: {e}")
            raise RepositoryError(f"Failed to find instance: {e}")
        except Exception as e:
            logger.error(f"Unexpected error finding instance: {e}", exc_info=True)
            raise RepositoryError(f"Failed to find instance: {e}")
    
    async def find_all(self) -> List[MCPInstance]:
        """Find all MCP instances."""
        try:
            # Get all instance IDs
            mcp_ids = await self.redis.smembers(self._all_key())
            
            if not mcp_ids:
                return []
            
            # Fetch all instances
            instances = []
            for mcp_id in mcp_ids:
                instance = await self.find_by_id(mcp_id.decode() if isinstance(mcp_id, bytes) else mcp_id)
                if instance:
                    instances.append(instance)
            
            logger.debug(f"Found {len(instances)} MCP instances")
            return instances
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding all instances: {e}")
            raise RepositoryError(f"Failed to find all instances: {e}")
        except Exception as e:
            logger.error(f"Unexpected error finding all instances: {e}", exc_info=True)
            raise RepositoryError(f"Failed to find all instances: {e}")
    
    async def find_by_state(self, state: MCPState) -> List[MCPInstance]:
        """Find all MCP instances in a specific state."""
        try:
            # Get instance IDs for state
            mcp_ids = await self.redis.smembers(self._state_key(state))
            
            if not mcp_ids:
                return []
            
            # Fetch instances
            instances = []
            for mcp_id in mcp_ids:
                instance = await self.find_by_id(mcp_id.decode() if isinstance(mcp_id, bytes) else mcp_id)
                if instance and instance.state == state:  # Verify state
                    instances.append(instance)
            
            logger.debug(f"Found {len(instances)} instances in state {state.value}")
            return instances
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding instances by state: {e}")
            raise RepositoryError(f"Failed to find instances by state: {e}")
        except Exception as e:
            logger.error(f"Unexpected error finding instances by state: {e}", exc_info=True)
            raise RepositoryError(f"Failed to find instances by state: {e}")
    
    async def find_by_tier(self, tier: int) -> List[MCPInstance]:
        """Find all MCP instances for a specific tier."""
        try:
            # Get instance IDs for tier
            mcp_ids = await self.redis.smembers(self._tier_key(tier))
            
            if not mcp_ids:
                return []
            
            # Fetch instances
            instances = []
            for mcp_id in mcp_ids:
                instance = await self.find_by_id(mcp_id.decode() if isinstance(mcp_id, bytes) else mcp_id)
                if instance:
                    instances.append(instance)
            
            logger.debug(f"Found {len(instances)} instances for tier {tier}")
            return instances
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding instances by tier: {e}")
            raise RepositoryError(f"Failed to find instances by tier: {e}")
        except Exception as e:
            logger.error(f"Unexpected error finding instances by tier: {e}", exc_info=True)
            raise RepositoryError(f"Failed to find instances by tier: {e}")
    
    async def delete(self, mcp_id: str) -> bool:
        """Delete an MCP instance."""
        try:
            # Get instance first to remove from indices
            instance = await self.find_by_id(mcp_id)
            if not instance:
                return False
            
            # Delete from all indices
            await self.redis.srem(self._all_key(), mcp_id)
            await self.redis.srem(self._state_key(instance.state), mcp_id)
            
            if "tier" in instance.metadata:
                tier = instance.metadata["tier"]
                await self.redis.srem(self._tier_key(tier), mcp_id)
            
            # Delete instance data
            deleted_count = await self.redis.delete(self._instance_key(mcp_id))
            
            logger.debug(f"Deleted MCP instance: {mcp_id}")
            return deleted_count > 0
            
        except redis.RedisError as e:
            logger.error(f"Redis error deleting instance: {e}")
            raise RepositoryError(f"Failed to delete instance: {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting instance: {e}", exc_info=True)
            raise RepositoryError(f"Failed to delete instance: {e}")
    
    async def exists(self, mcp_id: str) -> bool:
        """Check if an MCP instance exists."""
        try:
            exists = await self.redis.exists(self._instance_key(mcp_id))
            return bool(exists)
        except redis.RedisError as e:
            logger.error(f"Redis error checking existence: {e}")
            raise RepositoryError(f"Failed to check existence: {e}")
    
    async def count(self) -> int:
        """Count total number of MCP instances."""
        try:
            count = await self.redis.scard(self._all_key())
            return count
        except redis.RedisError as e:
            logger.error(f"Redis error counting instances: {e}")
            raise RepositoryError(f"Failed to count instances: {e}")
    
    async def count_by_state(self, state: MCPState) -> int:
        """Count MCP instances in a specific state."""
        try:
            count = await self.redis.scard(self._state_key(state))
            return count
        except redis.RedisError as e:
            logger.error(f"Redis error counting by state: {e}")
            raise RepositoryError(f"Failed to count by state: {e}")

