"""
Utility modules for Ecosystem MCP Service.
"""

from .logging import setup_logging, get_logger
from .redis_client import RedisClient, get_redis_client

# Placeholder functions for lifecycle management
async def init_redis():
    """Initialize Redis connection."""
    redis = get_redis_client()
    await redis.connect()

async def close_redis():
    """Close Redis connection."""
    redis = get_redis_client()
    await redis.close()

__all__ = [
    "setup_logging",
    "get_logger",
    "RedisClient",
    "get_redis_client",
    "init_redis",
    "close_redis",
]

