"""
Comprehensive diagnostics and connection testing endpoints.

Provides API for testing all service connections, health checks, and monitoring.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ...storage import get_database
from ...storage.chromadb_client import get_chroma_client
from ...utils.redis_client import get_redis_client
from ...config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class ServiceStatus(BaseModel):
    """Model for service status."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy", "unknown"
    latency_ms: Optional[float] = None
    message: str
    details: Dict[str, Any] = {}
    timestamp: str


class ConnectionTestResult(BaseModel):
    """Model for connection test results."""
    service: str
    success: bool
    latency_ms: float
    message: str
    details: Dict[str, Any] = {}


@router.get(
    "/diagnostics/health",
    summary="Comprehensive health check",
    description="Check health of all services with detailed diagnostics"
)
async def comprehensive_health_check():
    """
    Perform comprehensive health check on all services.
    
    Returns:
        Health status of all services with latency and diagnostic info.
    """
    start_time = time.time()
    results = []
    
    # PostgreSQL health check
    pg_result = await _test_postgresql()
    results.append(pg_result)
    
    # Redis health check
    redis_result = await _test_redis()
    results.append(redis_result)
    
    # ChromaDB health check
    chroma_result = await _test_chromadb()
    results.append(chroma_result)
    
    # Ollama health check
    ollama_result = await _test_ollama()
    results.append(ollama_result)
    
    # Filesystem health check
    fs_result = await _test_filesystem()
    results.append(fs_result)
    
    # Determine overall status
    healthy_count = sum(1 for r in results if r["status"] == "healthy")
    degraded_count = sum(1 for r in results if r["status"] == "degraded")
    unhealthy_count = sum(1 for r in results if r["status"] == "unhealthy")
    
    if unhealthy_count > 0:
        overall_status = "unhealthy"
    elif degraded_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    total_time = (time.time() - start_time) * 1000
    
    return JSONResponse(content={
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "total_checks": len(results),
        "healthy": healthy_count,
        "degraded": degraded_count,
        "unhealthy": unhealthy_count,
        "total_latency_ms": total_time,
        "services": results
    })


@router.post(
    "/diagnostics/test-connection",
    summary="Test specific service connection",
    description="Test connection to a specific service"
)
async def test_service_connection(service: str):
    """
    Test connection to a specific service.
    
    Args:
        service: Service name (postgresql, redis, chromadb, ollama, filesystem)
    
    Returns:
        Connection test result with latency and details.
    """
    service = service.lower()
    
    if service == "postgresql":
        result = await _test_postgresql()
    elif service == "redis":
        result = await _test_redis()
    elif service == "chromadb":
        result = await _test_chromadb()
    elif service == "ollama":
        result = await _test_ollama()
    elif service == "filesystem":
        result = await _test_filesystem()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")
    
    return JSONResponse(content=result)


def _safe_float(value) -> float:
    """Safely convert any numeric type to float."""
    from decimal import Decimal
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value) -> int:
    """Safely convert any numeric type to int."""
    from decimal import Decimal
    if value is None:
        return 0
    if isinstance(value, Decimal):
        return int(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


@router.get(
    "/diagnostics/monitor",
    summary="Real-time monitoring data",
    description="Get real-time monitoring metrics for all services"
)
async def get_monitoring_data():
    """
    Get real-time monitoring data for all services.
    
    Returns:
        Monitoring metrics including response times, error rates, and resource usage.
    """
    monitoring_data = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "system": {}
    }
    
    # PostgreSQL monitoring
    try:
        pg_start = time.time()
        db = get_database()
        async with db.session() as session:
            from sqlalchemy import text
            
            # Connection count
            result = await session.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
            ))
            connections = result.scalar()
            
            # Database size
            result = await session.execute(text(
                "SELECT pg_database_size(current_database())"
            ))
            db_size = result.scalar()
            
            # Cache hit ratio
            result = await session.execute(text(
                """
                SELECT 
                    sum(blks_hit) as hits,
                    sum(blks_read) as reads
                FROM pg_stat_database
                WHERE datname = current_database()
                """
            ))
            cache_stats = result.fetchone()
            hits = _safe_float(cache_stats[0])
            reads = _safe_float(cache_stats[1])
            total = hits + reads
            cache_hit_ratio = _safe_float((hits / total * 100) if total > 0 else 0)
        
        pg_latency = _safe_float((time.time() - pg_start) * 1000)
        
        monitoring_data["services"]["postgresql"] = {
            "status": "healthy",
            "latency_ms": pg_latency,
            "connections": _safe_int(connections),
            "database_size_bytes": _safe_int(db_size),
            "cache_hit_ratio": cache_hit_ratio
        }
    except Exception as e:
        monitoring_data["services"]["postgresql"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Redis monitoring
    try:
        redis_start = time.time()
        redis_wrapper = get_redis_client()
        redis = redis_wrapper.client if redis_wrapper and redis_wrapper.client else None
        if not redis:
            raise Exception("Redis client not available")
        info = await redis.info()
        redis_latency = _safe_float((time.time() - redis_start) * 1000)
        
        monitoring_data["services"]["redis"] = {
            "status": "healthy",
            "latency_ms": redis_latency,
            "connected_clients": _safe_int(info.get("connected_clients", 0)),
            "used_memory": str(info.get("used_memory_human", "unknown")),
            "ops_per_sec": _safe_int(info.get("instantaneous_ops_per_sec", 0)),
            "keyspace_hits": _safe_int(info.get("keyspace_hits", 0)),
            "keyspace_misses": _safe_int(info.get("keyspace_misses", 0))
        }
    except Exception as e:
        monitoring_data["services"]["redis"] = {
            "status": "error",
            "error": str(e)
        }
    
    # ChromaDB monitoring
    try:
        chroma_start = time.time()
        chroma = get_chroma_client()  # Returns ChromaDBClient wrapper
        
        # Use health_check and count methods from the wrapper
        healthy = await chroma.health_check()
        if not healthy:
            raise Exception("ChromaDB health check failed")
        
        vector_count = await chroma.count()
        chroma_latency = _safe_float((time.time() - chroma_start) * 1000)
        
        monitoring_data["services"]["chromadb"] = {
            "status": "healthy",
            "latency_ms": chroma_latency,
            "collection": chroma.collection_name,
            "total_vectors": _safe_int(vector_count)
        }
    except Exception as e:
        monitoring_data["services"]["chromadb"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Ollama monitoring
    try:
        import httpx
        ollama_start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
        ollama_latency = _safe_float((time.time() - ollama_start) * 1000)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            monitoring_data["services"]["ollama"] = {
                "status": "healthy",
                "latency_ms": ollama_latency,
                "models": _safe_int(len(models)),
                "model_names": [m.get("name") for m in models]
            }
        else:
            monitoring_data["services"]["ollama"] = {
                "status": "degraded",
                "latency_ms": ollama_latency,
                "message": f"HTTP {response.status_code}"
            }
    except Exception as e:
        monitoring_data["services"]["ollama"] = {
            "status": "error",
            "error": str(e)
        }
    
    # System resource monitoring
    try:
        import psutil
        
        monitoring_data["system"] = {
            "cpu_percent": _safe_float(psutil.cpu_percent(interval=0.1)),
            "memory_percent": _safe_float(psutil.virtual_memory().percent),
            "disk_percent": _safe_float(psutil.disk_usage('/').percent),
            "process_count": _safe_int(len(psutil.pids()))
        }
    except Exception as e:
        monitoring_data["system"] = {"error": str(e)}
    
    # All data is now guaranteed to be JSON-serializable (converted via _safe_float/_safe_int)
    # Manually serialize to JSON and return as Response to avoid FastAPI serialization issues
    import json
    from fastapi.responses import Response
    
    json_content = json.dumps(monitoring_data, indent=2)
    return Response(
        content=json_content,
        media_type="application/json",
        status_code=200
    )


# Helper functions for testing individual services

async def _test_postgresql() -> Dict[str, Any]:
    """Test PostgreSQL connection."""
    start_time = time.time()
    
    try:
        db = get_database()
        async with db.session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        
        latency = (time.time() - start_time) * 1000
        
        return {
            "name": "PostgreSQL",
            "status": "healthy",
            "latency_ms": latency,
            "message": "Connection successful",
            "details": {
                "response_time": f"{latency:.2f}ms"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return {
            "name": "PostgreSQL",
            "status": "unhealthy",
            "latency_ms": latency,
            "message": f"Connection failed: {str(e)}",
            "details": {"error": str(e)},
            "timestamp": datetime.now().isoformat()
        }


async def _test_redis() -> Dict[str, Any]:
    """Test Redis connection."""
    start_time = time.time()
    
    try:
        redis_wrapper = get_redis_client(); redis = redis_wrapper.client
        await redis.ping()
        
        latency = (time.time() - start_time) * 1000
        
        return {
            "name": "Redis",
            "status": "healthy",
            "latency_ms": latency,
            "message": "Connection successful",
            "details": {
                "response_time": f"{latency:.2f}ms"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return {
            "name": "Redis",
            "status": "unhealthy",
            "latency_ms": latency,
            "message": f"Connection failed: {str(e)}",
            "details": {"error": str(e)},
            "timestamp": datetime.now().isoformat()
        }


async def _test_chromadb() -> Dict[str, Any]:
    """Test ChromaDB connection."""
    start_time = time.time()
    
    try:
        chroma = get_chroma_client()  # Not async, returns wrapper
        healthy = await chroma.health_check()
        
        if not healthy:
            raise Exception("ChromaDB health check failed")
        
        vector_count = await chroma.count()
        latency = (time.time() - start_time) * 1000
        
        return {
            "name": "ChromaDB",
            "status": "healthy",
            "latency_ms": latency,
            "message": f"Connection successful ({vector_count} vectors)",
            "details": {
                "response_time": f"{latency:.2f}ms",
                "vector_count": vector_count,
                "collection": chroma.collection_name
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return {
            "name": "ChromaDB",
            "status": "unhealthy",
            "latency_ms": latency,
            "message": f"Connection failed: {str(e)}",
            "details": {"error": str(e)},
            "timestamp": datetime.now().isoformat()
        }


async def _test_ollama() -> Dict[str, Any]:
    """Test Ollama connection."""
    start_time = time.time()
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
        
        latency = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "name": "Ollama",
                "status": "healthy",
                "latency_ms": latency,
                "message": f"Connection successful ({len(models)} models)",
                "details": {
                    "response_time": f"{latency:.2f}ms",
                    "models": len(models)
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "name": "Ollama",
                "status": "degraded",
                "latency_ms": latency,
                "message": f"HTTP {response.status_code}",
                "details": {"status_code": response.status_code},
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return {
            "name": "Ollama",
            "status": "unhealthy",
            "latency_ms": latency,
            "message": f"Connection failed: {str(e)}",
            "details": {"error": str(e)},
            "timestamp": datetime.now().isoformat()
        }


async def _test_filesystem() -> Dict[str, Any]:
    """Test filesystem access."""
    start_time = time.time()
    
    try:
        from pathlib import Path
        
        # Test chroma path
        chroma_path = Path(settings.chroma_path)
        chroma_readable = chroma_path.exists() and chroma_path.is_dir()
        chroma_writable = False
        
        if chroma_readable:
            try:
                test_file = chroma_path / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                chroma_writable = True
            except:
                pass
        
        latency = (time.time() - start_time) * 1000
        
        if chroma_readable and chroma_writable:
            status = "healthy"
            message = "Filesystem access OK"
        elif chroma_readable:
            status = "degraded"
            message = "Read-only access"
        else:
            status = "unhealthy"
            message = "No access"
        
        return {
            "name": "Filesystem",
            "status": status,
            "latency_ms": latency,
            "message": message,
            "details": {
                "chroma_path": str(chroma_path),
                "readable": chroma_readable,
                "writable": chroma_writable
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        return {
            "name": "Filesystem",
            "status": "unhealthy",
            "latency_ms": latency,
            "message": f"Check failed: {str(e)}",
            "details": {"error": str(e)},
            "timestamp": datetime.now().isoformat()
        }

