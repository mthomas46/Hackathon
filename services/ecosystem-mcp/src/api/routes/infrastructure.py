"""
Infrastructure health monitoring endpoint.

Provides detailed status of all infrastructure components with circuit breaker info.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Response, status

from ...utils.circuit_breaker import get_all_breakers
from ...storage import get_database
from ...storage.chromadb_client import get_chroma_client
from ...utils.redis_client import get_redis_client

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/infrastructure/health",
    summary="Infrastructure Health Check",
    description="Detailed health status of all infrastructure components",
    response_model=Dict[str, Any]
)
async def infrastructure_health(response: Response):
    """
    Get detailed health status of all infrastructure components.
    
    Returns:
        Health status including:
        - Database connection status
        - Redis connection status
        - ChromaDB status
        - Circuit breaker status for each component
        - Connection pool statistics
    """
    health_status = {
        "status": "healthy",
        "components": {},
        "circuit_breakers": {}
    }
    
    overall_healthy = True
    
    # Check Database
    try:
        db = get_database()
        db_healthy = await db.health_check()
        
        health_status["components"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "type": "postgresql",
            "pool_size": db.pool_size if hasattr(db, 'pool_size') else "unknown"
        }
        
        if not db_healthy:
            overall_healthy = False
    
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check Redis
    try:
        redis_wrapper = get_redis_client(); redis = redis_wrapper.client
        ping_response = await redis.ping()
        redis_healthy = ping_response == True or ping_response == b'PONG'
        
        # Get Redis info
        try:
            info = await redis.info("stats")
            health_status["components"]["redis"] = {
                "status": "healthy" if redis_healthy else "unhealthy",
                "type": "redis",
                "connected_clients": info.get("connected_clients", "unknown"),
                "total_commands_processed": info.get("total_commands_processed", "unknown")
            }
        except:
            health_status["components"]["redis"] = {
                "status": "healthy" if redis_healthy else "unhealthy",
                "type": "redis"
            }
        
        if not redis_healthy:
            overall_healthy = False
    
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check ChromaDB
    try:
        import traceback
        chroma = get_chroma_client()  # Returns ChromaDBClient wrapper
        logger.info(f"ChromaDB client type: {type(chroma)}")
        logger.info(f"ChromaDB has health_check: {hasattr(chroma, 'health_check')}")
        
        chroma_healthy = await chroma.health_check()
        logger.info(f"ChromaDB healthy: {chroma_healthy}")
        
        if not chroma_healthy:
            raise Exception("ChromaDB health check failed")
        
        vector_count = await chroma.count()
        logger.info(f"ChromaDB vector_count: {vector_count}")
        
        health_status["components"]["chromadb"] = {
            "status": "healthy",
            "type": "chromadb",
            "collection": chroma.collection_name,
            "vector_count": vector_count
        }
    
    except Exception as e:
        logger.error(f"ChromaDB health check error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        health_status["components"]["chromadb"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Get Circuit Breaker Status
    breakers = get_all_breakers()
    for name, breaker in breakers.items():
        stats = breaker.get_stats()
        health_status["circuit_breakers"][name] = stats
        
        # If any breaker is open, mark as degraded
        if stats["state"] == "open":
            overall_healthy = False
    
    # Set overall status
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"
    
    # Set HTTP status code
    if not overall_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return health_status


@router.get(
    "/infrastructure/circuit-breakers",
    summary="Circuit Breaker Status",
    description="Status of all circuit breakers"
)
async def circuit_breaker_status():
    """Get status of all circuit breakers."""
    breakers = get_all_breakers()
    
    return {
        "count": len(breakers),
        "breakers": {
            name: breaker.get_stats()
            for name, breaker in breakers.items()
        }
    }


@router.post(
    "/infrastructure/circuit-breakers/{name}/reset",
    summary="Reset Circuit Breaker",
    description="Manually reset a circuit breaker to CLOSED state"
)
async def reset_circuit_breaker(name: str):
    """Manually reset a circuit breaker."""
    breakers = get_all_breakers()
    
    if name not in breakers:
        return {
            "error": "not_found",
            "message": f"Circuit breaker '{name}' not found",
            "available_breakers": list(breakers.keys())
        }
    
    breaker = breakers[name]
    await breaker.reset()
    
    return {
        "message": f"Circuit breaker '{name}' reset to CLOSED",
        "stats": breaker.get_stats()
    }


@router.get(
    "/infrastructure/diagnostics",
    summary="Infrastructure Diagnostics",
    description="Detailed diagnostics for troubleshooting"
)
async def infrastructure_diagnostics():
    """
    Get detailed diagnostics for troubleshooting infrastructure issues.
    
    Includes:
    - Connection status
    - Recent errors
    - Performance metrics
    - Configuration validation
    """
    diagnostics = {
        "database": {},
        "redis": {},
        "chromadb": {},
        "circuit_breakers": {},
        "recommendations": []
    }
    
    # Database Diagnostics
    try:
        from ...config import settings
        from urllib.parse import urlparse
        
        settings = get_settings()
        parsed = urlparse(str(settings.database_url))
        
        db = get_database()
        db_healthy = await db.health_check()
        
        diagnostics["database"] = {
            "healthy": db_healthy,
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "database": parsed.path.lstrip('/') if parsed.path else "unknown",
            "username": parsed.username or "unknown",
            "pool_config": {
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow
            }
        }
        
        if not db_healthy:
            diagnostics["recommendations"].append({
                "component": "database",
                "issue": "Database connection unhealthy",
                "actions": [
                    "Check if PostgreSQL container is running: docker ps | grep postgres",
                    f"Check database exists: docker exec <container> psql -U {parsed.username} -l",
                    "Check connection settings in .env file"
                ]
            })
    
    except Exception as e:
        diagnostics["database"] = {
            "error": str(e),
            "healthy": False
        }
        diagnostics["recommendations"].append({
            "component": "database",
            "issue": f"Database error: {e}",
            "actions": [
                "Check DATABASE_URL environment variable",
                "Verify PostgreSQL is accessible"
            ]
        })
    
    # Redis Diagnostics
    try:
        redis_wrapper = get_redis_client(); redis = redis_wrapper.client
        info = await redis.info()
        
        diagnostics["redis"] = {
            "healthy": True,
            "version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", "unknown"),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0)
        }
    
    except Exception as e:
        diagnostics["redis"] = {
            "error": str(e),
            "healthy": False
        }
        diagnostics["recommendations"].append({
            "component": "redis",
            "issue": f"Redis error: {e}",
            "actions": [
                "Check if Redis container is running: docker ps | grep redis",
                "Check REDIS_URL environment variable",
                "Test connection: redis-cli ping"
            ]
        })
    
    # ChromaDB Diagnostics
    try:
        from ...config import settings
        
        chroma = get_chroma_client()  # Returns ChromaDBClient wrapper
        chroma_healthy = await chroma.health_check()
        
        if not chroma_healthy:
            raise Exception("ChromaDB health check failed")
        
        vector_count = await chroma.count()
        
        diagnostics["chromadb"] = {
            "healthy": True,
            "path": str(settings.chroma_path),
            "collection": chroma.collection_name,
            "total_vectors": vector_count
        }
        
        if vector_count == 0:
            diagnostics["recommendations"].append({
                "component": "chromadb",
                "issue": "No documents ingested",
                "actions": [
                    "Ingest documents using /api/v1/admin/ingest endpoint",
                    "Check ingestion logs for errors"
                ]
            })
    
    except Exception as e:
        diagnostics["chromadb"] = {
            "error": str(e),
            "healthy": False
        }
        diagnostics["recommendations"].append({
            "component": "chromadb",
            "issue": f"ChromaDB error: {e}",
            "actions": [
                "Check CHROMA_PATH is writable",
                "Verify ChromaDB data directory exists"
            ]
        })
    
    # Circuit Breaker Diagnostics
    breakers = get_all_breakers()
    open_breakers = []
    
    for name, breaker in breakers.items():
        stats = breaker.get_stats()
        diagnostics["circuit_breakers"][name] = stats
        
        if stats["state"] == "open":
            open_breakers.append(name)
            diagnostics["recommendations"].append({
                "component": "circuit_breaker",
                "issue": f"Circuit breaker '{name}' is OPEN",
                "actions": [
                    f"Breaker opened after {stats['total_failures']} failures",
                    f"Fix underlying {name} issue",
                    f"Wait {stats['config']['timeout']}s for automatic retry",
                    f"Or manually reset: POST /api/v1/infrastructure/circuit-breakers/{name}/reset"
                ]
            })
    
    if len(diagnostics["recommendations"]) == 0:
        diagnostics["recommendations"].append({
            "component": "all",
            "issue": "none",
            "actions": ["All systems operational ✅"]
        })
    
    return diagnostics

