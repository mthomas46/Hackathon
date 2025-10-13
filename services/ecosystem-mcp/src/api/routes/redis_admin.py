"""
Redis administration and exploration endpoints.

Provides API for viewing and managing Redis data.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


class RedisKeyValue(BaseModel):
    """Model for Redis key-value operations."""
    key: str = Field(..., description="Redis key")
    value: Optional[str] = Field(None, description="Value to set")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")


class RedisSearchRequest(BaseModel):
    """Model for Redis key search."""
    pattern: str = Field(default="*", description="Search pattern (e.g., 'cache:*')")
    count: int = Field(default=100, ge=1, le=1000, description="Maximum keys to return")


@router.get(
    "/redis/info",
    summary="Get Redis server info",
    description="Get detailed Redis server information and statistics"
)
async def get_redis_info():
    """
    Get Redis server information.
    
    Returns:
        Redis server info including memory usage, stats, and configuration.
    """
    try:
        redis_wrapper = get_redis_client(); redis = redis_wrapper.client
        
        # Get various info sections
        info = await redis.info()
        
        # Parse key metrics
        memory_info = {
            "used_memory": info.get("used_memory", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "used_memory_peak": info.get("used_memory_peak", 0),
            "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
            "maxmemory": info.get("maxmemory", 0),
            "maxmemory_human": info.get("maxmemory_human", "unlimited"),
            "maxmemory_policy": info.get("maxmemory_policy", "noeviction"),
        }
        
        stats = {
            "total_connections_received": info.get("total_connections_received", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
            "total_net_input_bytes": info.get("total_net_input_bytes", 0),
            "total_net_output_bytes": info.get("total_net_output_bytes", 0),
            "rejected_connections": info.get("rejected_connections", 0),
            "expired_keys": info.get("expired_keys", 0),
            "evicted_keys": info.get("evicted_keys", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
        }
        
        # Calculate hit rate
        total_requests = stats["keyspace_hits"] + stats["keyspace_misses"]
        hit_rate = (stats["keyspace_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        server = {
            "redis_version": info.get("redis_version", "unknown"),
            "redis_mode": info.get("redis_mode", "standalone"),
            "os": info.get("os", "unknown"),
            "arch_bits": info.get("arch_bits", 0),
            "process_id": info.get("process_id", 0),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            "uptime_in_days": info.get("uptime_in_days", 0),
        }
        
        clients = {
            "connected_clients": info.get("connected_clients", 0),
            "blocked_clients": info.get("blocked_clients", 0),
            "tracking_clients": info.get("tracking_clients", 0),
        }
        
        # Get keyspace info
        keyspace = {}
        for key, value in info.items():
            if key.startswith("db"):
                keyspace[key] = value
        
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "memory": memory_info,
            "stats": stats,
            "hit_rate": hit_rate,
            "server": server,
            "clients": clients,
            "keyspace": keyspace,
            "full_info": info
        })
    
    except Exception as e:
        logger.error(f"Error getting Redis info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Redis info: {str(e)}"
        )


@router.post(
    "/redis/keys",
    summary="Search Redis keys",
    description="Search for Redis keys matching a pattern"
)
async def search_redis_keys(request: RedisSearchRequest):
    """
    Search for Redis keys matching a pattern.
    
    Args:
        request: Search parameters (pattern and count)
    
    Returns:
        List of matching keys with their types and TTLs.
    """
    try:
        redis_wrapper = get_redis_client(); redis = redis_wrapper.client
        
        # Use SCAN for better performance
        keys = []
        cursor = 0
        
        while len(keys) < request.count:
            cursor, batch = await redis.scan(
                cursor=cursor,
                match=request.pattern,
                count=100
            )
            
            for key in batch:
                if len(keys) >= request.count:
                    break
                
                # Get key type and TTL
                key_type = await redis.type(key)
                ttl = await redis.ttl(key)
                
                # Get size estimate
                size = 0
                if key_type == "string":
                    size = await redis.strlen(key)
                elif key_type == "list":
                    size = await redis.llen(key)
                elif key_type == "set":
                    size = await redis.scard(key)
                elif key_type == "zset":
                    size = await redis.zcard(key)
                elif key_type == "hash":
                    size = await redis.hlen(key)
                
                keys.append({
                    "key": key.decode() if isinstance(key, bytes) else key,
                    "type": key_type.decode() if isinstance(key_type, bytes) else key_type,
                    "ttl": ttl,
                    "size": size
                })
            
            if cursor == 0:
                break
        
        return JSONResponse(content={
            "pattern": request.pattern,
            "total": len(keys),
            "keys": keys
        })
    
    except Exception as e:
        logger.error(f"Error searching Redis keys: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search Redis keys: {str(e)}"
        )


@router.get(
    "/redis/key/{key:path}",
    summary="Get Redis key value",
    description="Get value of a specific Redis key"
)
async def get_redis_key(key: str):
    """
    Get value of a Redis key.
    
    Args:
        key: Redis key name
    
    Returns:
        Key value, type, and metadata.
    """
    try:
        redis_wrapper = get_redis_client(); redis = redis_wrapper.client
        
        # Check if key exists
        exists = await redis.exists(key)
        if not exists:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
        
        # Get key type
        key_type = await redis.type(key)
        key_type_str = key_type.decode() if isinstance(key_type, bytes) else key_type
        
        # Get TTL
        ttl = await redis.ttl(key)
        
        # Get value based on type
        value = None
        if key_type_str == "string":
            raw_value = await redis.get(key)
            value = raw_value.decode() if isinstance(raw_value, bytes) else raw_value
        
        elif key_type_str == "list":
            raw_list = await redis.lrange(key, 0, -1)
            value = [v.decode() if isinstance(v, bytes) else v for v in raw_list]
        
        elif key_type_str == "set":
            raw_set = await redis.smembers(key)
            value = [v.decode() if isinstance(v, bytes) else v for v in raw_set]
        
        elif key_type_str == "zset":
            raw_zset = await redis.zrange(key, 0, -1, withscores=True)
            value = [(v.decode() if isinstance(v, bytes) else v, score) for v, score in raw_zset]
        
        elif key_type_str == "hash":
            raw_hash = await redis.hgetall(key)
            value = {
                k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
                for k, v in raw_hash.items()
            }
        
        return JSONResponse(content={
            "key": key,
            "type": key_type_str,
            "ttl": ttl,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Redis key: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Redis key: {str(e)}"
        )


@router.delete(
    "/redis/key/{key:path}",
    summary="Delete Redis key",
    description="Delete a specific Redis key"
)
async def delete_redis_key(key: str):
    """
    Delete a Redis key.
    
    Args:
        key: Redis key name
    
    Returns:
        Success status and deleted key name.
    """
    try:
        redis_wrapper = get_redis_client(); redis = redis_wrapper.client
        
        # Delete the key
        deleted = await redis.delete(key)
        
        if deleted == 0:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Key '{key}' deleted successfully",
            "key": key,
            "timestamp": datetime.now().isoformat()
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Redis key: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete Redis key: {str(e)}"
        )


@router.post(
    "/redis/key",
    summary="Set Redis key value",
    description="Set value for a Redis key"
)
async def set_redis_key(key_value: RedisKeyValue):
    """
    Set value for a Redis key.
    
    Args:
        key_value: Key name, value, and optional TTL
    
    Returns:
        Success status and key details.
    """
    try:
        redis_wrapper = get_redis_client(); redis = redis_wrapper.client
        
        if key_value.value is None:
            raise HTTPException(status_code=400, detail="Value is required")
        
        # Set the key
        if key_value.ttl:
            await redis.setex(key_value.key, key_value.ttl, key_value.value)
        else:
            await redis.set(key_value.key, key_value.value)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Key '{key_value.key}' set successfully",
            "key": key_value.key,
            "ttl": key_value.ttl,
            "timestamp": datetime.now().isoformat()
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting Redis key: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set Redis key: {str(e)}"
        )


@router.post(
    "/redis/flush",
    summary="Flush Redis database",
    description="WARNING: Deletes all keys in the current database"
)
async def flush_redis_db(
    confirm: bool = Query(..., description="Must be true to confirm flush")
):
    """
    Flush all keys from the current Redis database.
    
    WARNING: This is a destructive operation!
    
    Args:
        confirm: Must be true to proceed
    
    Returns:
        Success status with count of deleted keys.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to flush database"
        )
    
    try:
        redis_wrapper = get_redis_client(); redis = redis_wrapper.client
        
        # Get key count before flush
        info = await redis.info()
        db_keys = 0
        for key, value in info.items():
            if key.startswith("db"):
                # Parse "keys=123,expires=45" format
                for part in value.split(","):
                    if part.startswith("keys="):
                        db_keys += int(part.split("=")[1])
        
        # Flush the database
        await redis.flushdb()
        
        logger.warning(f"Redis database flushed - {db_keys} keys deleted")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Redis database flushed successfully",
            "keys_deleted": db_keys,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error flushing Redis database: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to flush Redis database: {str(e)}"
        )


@router.get(
    "/redis/memory",
    summary="Get Redis memory analysis",
    description="Analyze Redis memory usage by key patterns"
)
async def get_redis_memory_analysis():
    """
    Analyze Redis memory usage.
    
    Returns:
        Memory usage breakdown and analysis.
    """
    try:
        redis_wrapper = get_redis_client(); redis = redis_wrapper.client
        
        # Get memory stats
        info = await redis.info("memory")
        
        # Sample keys to analyze patterns
        patterns = {}
        cursor = 0
        sample_size = 0
        max_samples = 1000
        
        while sample_size < max_samples:
            cursor, keys = await redis.scan(cursor=cursor, count=100)
            
            for key in keys:
                if sample_size >= max_samples:
                    break
                
                # Get memory usage for key
                try:
                    memory = await redis.memory_usage(key)
                    if memory:
                        # Extract pattern (e.g., "cache:*", "session:*")
                        key_str = key.decode() if isinstance(key, bytes) else key
                        pattern = key_str.split(":")[0] if ":" in key_str else "other"
                        
                        if pattern not in patterns:
                            patterns[pattern] = {"count": 0, "memory": 0}
                        
                        patterns[pattern]["count"] += 1
                        patterns[pattern]["memory"] += memory
                        
                        sample_size += 1
                except:
                    pass  # Skip keys that don't support MEMORY USAGE
            
            if cursor == 0:
                break
        
        # Sort by memory usage
        sorted_patterns = sorted(
            patterns.items(),
            key=lambda x: x[1]["memory"],
            reverse=True
        )
        
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "total_memory": info.get("used_memory", 0),
            "total_memory_human": info.get("used_memory_human", "0B"),
            "peak_memory": info.get("used_memory_peak", 0),
            "peak_memory_human": info.get("used_memory_peak_human", "0B"),
            "fragmentation_ratio": info.get("mem_fragmentation_ratio", 0),
            "sampled_keys": sample_size,
            "patterns": [
                {
                    "pattern": pattern,
                    "count": data["count"],
                    "memory_bytes": data["memory"],
                    "avg_size_bytes": data["memory"] // data["count"] if data["count"] > 0 else 0
                }
                for pattern, data in sorted_patterns
            ]
        })
    
    except Exception as e:
        logger.error(f"Error analyzing Redis memory: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze Redis memory: {str(e)}"
        )

