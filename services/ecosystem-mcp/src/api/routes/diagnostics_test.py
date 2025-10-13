"""Diagnostic testing endpoints to isolate issues."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
from decimal import Decimal
import time
from typing import Dict, Any
import json

from ...storage.database import get_database
from ...storage.redis_client import get_redis_client
from ...storage.chromadb_client import get_chroma_client
from ...config import settings

router = APIRouter()


def _type_analyzer(obj, path="root"):
    """Recursively analyze types in nested structures."""
    issues = []
    
    if isinstance(obj, Decimal):
        issues.append(f"{path}: Decimal({obj})")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            issues.extend(_type_analyzer(value, f"{path}.{key}"))
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            issues.extend(_type_analyzer(item, f"{path}[{i}]"))
    elif not isinstance(obj, (str, int, float, bool, type(None))):
        issues.append(f"{path}: {type(obj).__name__}")
    
    return issues


@router.get(
    "/diagnostics/test-monitor-parts",
    summary="Test individual monitoring components",
    description="Test each service monitoring separately to identify issues"
)
async def test_monitor_parts():
    """Test each monitoring component separately."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Test PostgreSQL
    try:
        pg_start = time.time()
        db = get_database()
        async with db.session() as session:
            from sqlalchemy import text
            
            result = await session.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
            ))
            connections = result.scalar()
            
            result = await session.execute(text(
                "SELECT pg_database_size(current_database())"
            ))
            db_size = result.scalar()
            
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
        
        pg_latency = (time.time() - pg_start) * 1000
        
        pg_data = {
            "status": "healthy",
            "latency_ms": pg_latency,
            "connections": connections,
            "database_size_bytes": db_size,
            "cache_stats": cache_stats
        }
        
        # Analyze types
        type_issues = _type_analyzer(pg_data, "postgresql")
        
        results["tests"]["postgresql"] = {
            "success": True,
            "data": str(pg_data),  # Convert to string to avoid serialization
            "type_issues": type_issues,
            "raw_types": {
                "connections_type": type(connections).__name__,
                "db_size_type": type(db_size).__name__,
                "cache_stats_type": type(cache_stats).__name__,
                "cache_stats_0_type": type(cache_stats[0]).__name__ if cache_stats else "N/A",
                "cache_stats_1_type": type(cache_stats[1]).__name__ if cache_stats else "N/A",
            }
        }
    except Exception as e:
        results["tests"]["postgresql"] = {
            "success": False,
            "error": str(e)
        }
    
    # Test Redis
    try:
        redis_start = time.time()
        redis_wrapper = get_redis_client()
        redis = redis_wrapper.client
        info = await redis.info()
        redis_latency = (time.time() - redis_start) * 1000
        
        redis_data = {
            "status": "healthy",
            "latency_ms": redis_latency,
            "connected_clients": info.get("connected_clients", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
        }
        
        type_issues = _type_analyzer(redis_data, "redis")
        
        results["tests"]["redis"] = {
            "success": True,
            "data": str(redis_data),
            "type_issues": type_issues,
            "raw_types": {
                "connected_clients_type": type(info.get("connected_clients")).__name__,
                "keyspace_hits_type": type(info.get("keyspace_hits")).__name__,
            }
        }
    except Exception as e:
        results["tests"]["redis"] = {
            "success": False,
            "error": str(e)
        }
    
    # Test ChromaDB
    try:
        chroma_start = time.time()
        chroma = await get_chroma_client()
        collections = await chroma.list_collections()
        chroma_latency = (time.time() - chroma_start) * 1000
        
        total_vectors = 0
        for collection in collections:
            count = await collection.count()
            total_vectors += count
        
        chroma_data = {
            "status": "healthy",
            "latency_ms": chroma_latency,
            "collections": len(collections),
            "total_vectors": total_vectors
        }
        
        type_issues = _type_analyzer(chroma_data, "chromadb")
        
        results["tests"]["chromadb"] = {
            "success": True,
            "data": str(chroma_data),
            "type_issues": type_issues,
            "raw_types": {
                "collections_type": type(len(collections)).__name__,
                "total_vectors_type": type(total_vectors).__name__,
            }
        }
    except Exception as e:
        results["tests"]["chromadb"] = {
            "success": False,
            "error": str(e)
        }
    
    return JSONResponse(content=results)


@router.get(
    "/diagnostics/test-serialization",
    summary="Test JSON serialization",
    description="Test serialization of different data types"
)
async def test_serialization():
    """Test serialization of various types."""
    from decimal import Decimal
    
    test_data = {
        "string": "test",
        "int": 123,
        "float": 123.45,
        "bool": True,
        "none": None,
        "list": [1, 2, 3],
        "dict": {"key": "value"},
    }
    
    # Try to serialize
    results = {
        "basic_types": "OK",
        "issues": []
    }
    
    try:
        json.dumps(test_data)
        results["basic_types_test"] = "PASS"
    except Exception as e:
        results["basic_types_test"] = f"FAIL: {str(e)}"
    
    # Test Decimal
    try:
        decimal_data = {"decimal": Decimal("123.45")}
        json.dumps(decimal_data)
        results["decimal_test"] = "PASS"
    except Exception as e:
        results["decimal_test"] = f"FAIL: {str(e)} - Decimal is not JSON serializable"
        results["issues"].append("Decimal type detected")
    
    # Test conversion
    try:
        decimal_data = {"decimal": float(Decimal("123.45"))}
        json.dumps(decimal_data)
        results["decimal_converted_test"] = "PASS - Conversion works"
    except Exception as e:
        results["decimal_converted_test"] = f"FAIL: {str(e)}"
    
    return JSONResponse(content=results)

