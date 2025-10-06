"""Redis implementation of MCP Registry Repository."""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import redis.asyncio as redis

from services.mcp_gateway.domain.entities.mcp_instance import MCPInstance
from services.mcp_gateway.domain.repositories.mcp_registry_repository import MCPRegistryRepository
from services.mcp_gateway.domain.value_objects.mcp_instance_status import MCPInstanceStatus
from services.mcp_gateway.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class RedisMCPRegistryRepository(MCPRegistryRepository):
    """
    Redis implementation of the MCP Registry Repository.
    
    Uses Redis for fast access to MCP instance registry with multiple indices
    for efficient querying.
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
    
    def _instance_key(self, instance_id: str) -> str:
        """Generate Redis key for an instance."""
        return f"{self.KEY_PREFIX}instance:{instance_id}"
    
    def _mcp_id_index_key(self, mcp_id: str) -> str:
        """Generate Redis key for MCP ID index."""
        return f"{self.KEY_PREFIX}index:mcp_id:{mcp_id}"
    
    def _status_index_key(self, status: MCPInstanceStatus) -> str:
        """Generate Redis key for status index."""
        return f"{self.KEY_PREFIX}index:status:{status.value}"
    
    def _tier_index_key(self, tier: int) -> str:
        """Generate Redis key for tier index."""
        return f"{self.KEY_PREFIX}index:tier:{tier}"
    
    def _all_instances_key(self) -> str:
        """Generate Redis key for all instances set."""
        return f"{self.KEY_PREFIX}index:all"
    
    async def register(self, instance: MCPInstance) -> None:
        """Register a new MCP instance."""
        try:
            instance_key = self._instance_key(instance.id)
            instance_data = json.dumps(instance.to_dict())
            
            # Store instance data
            await self.redis.set(instance_key, instance_data)
            
            # Add to indices
            await self._add_to_indices(instance)
            
            logger.info(
                f"Registered instance {instance.id} "
                f"(mcp_id={instance.mcp_id}, host={instance.host}:{instance.port})"
            )
            
        except redis.RedisError as e:
            logger.error(f"Redis error registering instance {instance.id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error registering instance {instance.id}: {e}", exc_info=True)
            raise
    
    async def deregister(self, instance_id: str) -> bool:
        """Deregister an MCP instance."""
        try:
            # Get instance first to remove from indices
            instance = await self.find_by_id(instance_id)
            if not instance:
                return False
            
            # Remove from indices
            await self._remove_from_indices(instance)
            
            # Delete instance data
            instance_key = self._instance_key(instance_id)
            await self.redis.delete(instance_key)
            
            logger.info(f"Deregistered instance {instance_id}")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis error deregistering instance {instance_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deregistering instance {instance_id}: {e}", exc_info=True)
            raise
    
    async def find_by_id(self, instance_id: str) -> Optional[MCPInstance]:
        """Find an instance by ID."""
        try:
            instance_key = self._instance_key(instance_id)
            data = await self.redis.get(instance_key)
            
            if not data:
                return None
            
            instance_dict = json.loads(data)
            return MCPInstance.from_dict(instance_dict)
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding instance {instance_id}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for instance {instance_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error finding instance {instance_id}: {e}", exc_info=True)
            raise
    
    async def find_by_mcp_id(self, mcp_id: str) -> List[MCPInstance]:
        """Find all instances for a specific MCP."""
        try:
            index_key = self._mcp_id_index_key(mcp_id)
            instance_ids = await self.redis.smembers(index_key)
            
            instances = []
            for instance_id_bytes in instance_ids:
                instance_id = instance_id_bytes.decode()
                instance = await self.find_by_id(instance_id)
                if instance:
                    instances.append(instance)
            
            return instances
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding instances for {mcp_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error finding instances for {mcp_id}: {e}", exc_info=True)
            raise
    
    async def find_available(
        self,
        mcp_id: Optional[str] = None,
        tier: Optional[int] = None
    ) -> List[MCPInstance]:
        """Find all available (routable) instances."""
        try:
            # Start with all instances
            if mcp_id:
                instances = await self.find_by_mcp_id(mcp_id)
            else:
                instances = await self.find_all()
            
            # Filter by tier if specified
            if tier is not None:
                instances = [inst for inst in instances if inst.tier == tier]
            
            # Filter to only available instances
            available = [
                inst for inst in instances
                if inst.is_available_for_routing()
            ]
            
            return available
            
        except Exception as e:
            logger.error(f"Error finding available instances: {e}", exc_info=True)
            raise
    
    async def find_by_status(self, status: MCPInstanceStatus) -> List[MCPInstance]:
        """Find instances by status."""
        try:
            index_key = self._status_index_key(status)
            instance_ids = await self.redis.smembers(index_key)
            
            instances = []
            for instance_id_bytes in instance_ids:
                instance_id = instance_id_bytes.decode()
                instance = await self.find_by_id(instance_id)
                if instance and instance.status == status:
                    instances.append(instance)
            
            return instances
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding instances by status {status}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error finding instances by status {status}: {e}", exc_info=True)
            raise
    
    async def update(self, instance: MCPInstance) -> None:
        """Update an existing instance."""
        try:
            # Remove from old indices
            old_instance = await self.find_by_id(instance.id)
            if old_instance:
                await self._remove_from_indices(old_instance)
            
            # Update instance data
            instance_key = self._instance_key(instance.id)
            instance_data = json.dumps(instance.to_dict())
            await self.redis.set(instance_key, instance_data)
            
            # Add to new indices
            await self._add_to_indices(instance)
            
            logger.debug(f"Updated instance {instance.id}")
            
        except redis.RedisError as e:
            logger.error(f"Redis error updating instance {instance.id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating instance {instance.id}: {e}", exc_info=True)
            raise
    
    async def find_all(self) -> List[MCPInstance]:
        """Get all registered instances."""
        try:
            all_key = self._all_instances_key()
            instance_ids = await self.redis.smembers(all_key)
            
            instances = []
            for instance_id_bytes in instance_ids:
                instance_id = instance_id_bytes.decode()
                instance = await self.find_by_id(instance_id)
                if instance:
                    instances.append(instance)
            
            return instances
            
        except redis.RedisError as e:
            logger.error(f"Redis error finding all instances: {e}")
            raise
        except Exception as e:
            logger.error(f"Error finding all instances: {e}", exc_info=True)
            raise
    
    async def count_by_mcp_id(self, mcp_id: str) -> int:
        """Count instances for a specific MCP."""
        try:
            index_key = self._mcp_id_index_key(mcp_id)
            count = await self.redis.scard(index_key)
            return count
            
        except redis.RedisError as e:
            logger.error(f"Redis error counting instances for {mcp_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error counting instances for {mcp_id}: {e}", exc_info=True)
            raise
    
    async def cleanup_stale_instances(self, max_age_seconds: int) -> int:
        """Remove instances that haven't been seen recently."""
        try:
            all_instances = await self.find_all()
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(seconds=max_age_seconds)
            
            removed_count = 0
            for instance in all_instances:
                if instance.last_seen_at < cutoff:
                    await self.deregister(instance.id)
                    removed_count += 1
                    logger.info(
                        f"Removed stale instance {instance.id} "
                        f"(last seen: {instance.last_seen_at.isoformat()})"
                    )
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up stale instances: {e}", exc_info=True)
            raise
    
    async def _add_to_indices(self, instance: MCPInstance) -> None:
        """Add instance to Redis indices."""
        pipeline = self.redis.pipeline()
        
        # Add to all instances set
        pipeline.sadd(self._all_instances_key(), instance.id)
        
        # Add to MCP ID index
        pipeline.sadd(self._mcp_id_index_key(instance.mcp_id), instance.id)
        
        # Add to status index
        pipeline.sadd(self._status_index_key(instance.status), instance.id)
        
        # Add to tier index
        pipeline.sadd(self._tier_index_key(instance.tier), instance.id)
        
        await pipeline.execute()
    
    async def _remove_from_indices(self, instance: MCPInstance) -> None:
        """Remove instance from Redis indices."""
        pipeline = self.redis.pipeline()
        
        # Remove from all instances set
        pipeline.srem(self._all_instances_key(), instance.id)
        
        # Remove from MCP ID index
        pipeline.srem(self._mcp_id_index_key(instance.mcp_id), instance.id)
        
        # Remove from status index
        pipeline.srem(self._status_index_key(instance.status), instance.id)
        
        # Remove from tier index
        pipeline.srem(self._tier_index_key(instance.tier), instance.id)
        
        await pipeline.execute()

