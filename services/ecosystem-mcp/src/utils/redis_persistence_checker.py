"""
Redis Persistence Verification

Verifies that Redis is configured for persistence (AOF/RDB) to prevent
message loss on container restarts.
"""

import logging
from typing import Dict, Any

from .redis_client import get_redis_client

logger = logging.getLogger(__name__)


async def verify_redis_persistence() -> Dict[str, Any]:
    """
    Verify Redis persistence configuration.
    
    Checks:
    - appendonly (AOF) enabled
    - AOF status active
    - RDB save configuration
    
    Returns:
        Dict with verification results
    """
    result = {
        "aof_enabled": False,
        "aof_active": False,
        "rdb_enabled": False,
        "warnings": [],
        "recommendations": []
    }
    
    try:
        redis = get_redis_client()
        
        # Check AOF configuration
        config = await redis.client.config_get("appendonly")
        aof_enabled = config.get("appendonly") == "yes"
        result["aof_enabled"] = aof_enabled
        
        if not aof_enabled:
            warning = "Redis appendonly (AOF) not enabled! Messages will be lost on restart!"
            result["warnings"].append(warning)
            logger.error(f"❌ {warning}")
            
            result["recommendations"].append(
                "Enable AOF in redis.conf: appendonly yes"
            )
            result["recommendations"].append(
                "Or set in docker-compose: command: redis-server --appendonly yes"
            )
        else:
            logger.info("✅ Redis appendonly (AOF) enabled")
        
        # Check AOF status from persistence info
        info = await redis.client.info("persistence")
        aof_enabled_runtime = info.get("aof_enabled", 0)
        result["aof_active"] = aof_enabled_runtime == 1
        
        if aof_enabled_runtime == 0:
            warning = "Redis AOF not active at runtime!"
            result["warnings"].append(warning)
            logger.error(f"❌ {warning}")
        else:
            logger.info("✅ Redis AOF active")
            
            # Show AOF file info
            aof_current_size = info.get("aof_current_size", 0)
            aof_base_size = info.get("aof_base_size", 0)
            logger.info(f"   AOF file size: {aof_current_size} bytes (base: {aof_base_size})")
        
        # Check RDB configuration
        save_config = await redis.client.config_get("save")
        rdb_save = save_config.get("save", "")
        result["rdb_enabled"] = bool(rdb_save and rdb_save != "")
        
        if result["rdb_enabled"]:
            logger.info(f"✅ Redis RDB snapshots enabled: {rdb_save}")
            
            # Show RDB info
            rdb_last_save = info.get("rdb_last_save_time", 0)
            rdb_changes = info.get("rdb_changes_since_last_save", 0)
            logger.info(f"   Last RDB save: {rdb_last_save}, Changes since: {rdb_changes}")
        else:
            logger.warning("⚠️  Redis RDB snapshots disabled (AOF recommended)")
        
        # Overall status
        if result["aof_enabled"] and result["aof_active"]:
            logger.info("✅ Redis persistence verified: AOF enabled and active")
        elif result["rdb_enabled"]:
            logger.warning("⚠️  Redis using RDB only (AOF recommended for job queue)")
        else:
            logger.error("❌ CRITICAL: Redis has NO persistence! Data will be lost on restart!")
            result["recommendations"].append(
                "URGENT: Enable persistence to prevent job loss!"
            )
    
    except Exception as e:
        error_msg = f"Failed to verify Redis persistence: {e}"
        logger.error(error_msg, exc_info=True)
        result["warnings"].append(error_msg)
    
    return result

