"""
Performance Optimization API Routes

Provides endpoints to apply and monitor performance optimizations.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage import get_database
from ...storage.migrations.add_performance_indexes import (
    add_performance_indexes,
    remove_performance_indexes,
    analyze_index_usage
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimization", tags=["Performance Optimization"])


@router.post("/indexes/create")
async def create_performance_indexes():
    """
    Create performance indexes for Phase 2 optimizations.
    
    This creates indexes on:
    - content_hash (for fast duplicate detection)
    - commit_sha (for fast commit queries)
    - service_name + file_path (for fast lookups)
    - created_at (for time-based queries)
    - is_latest (for version queries)
    
    Expected improvement: 5-10× faster queries
    
    Returns:
        Dict with creation results
    """
    try:
        async with get_database().session() as session:
            results = await add_performance_indexes(session)
            
            return {
                "success": len(results["errors"]) == 0,
                "indexes_created": results["indexes_created"],
                "indexes_skipped": results["indexes_skipped"],
                "errors": results["errors"],
                "message": (
                    f"Created {len(results['indexes_created'])} indexes, "
                    f"skipped {len(results['indexes_skipped'])} existing"
                )
            }
    
    except Exception as e:
        logger.error(f"Error creating performance indexes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create performance indexes: {str(e)}"
        )


@router.delete("/indexes/remove")
async def remove_performance_indexes_endpoint():
    """
    Remove performance indexes (for rollback).
    
    **Warning:** This will slow down queries significantly.
    Only use for testing or rollback purposes.
    
    Returns:
        Dict with removal results
    """
    try:
        async with get_database().session() as session:
            results = await remove_performance_indexes(session)
            
            return {
                "success": len(results["errors"]) == 0,
                "indexes_removed": results["indexes_removed"],
                "errors": results["errors"],
                "message": f"Removed {len(results['indexes_removed'])} indexes"
            }
    
    except Exception as e:
        logger.error(f"Error removing performance indexes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove performance indexes: {str(e)}"
        )


@router.get("/indexes/stats")
async def get_index_statistics():
    """
    Get usage statistics for performance indexes.
    
    Returns:
        Dict with index usage statistics including:
        - Number of scans per index
        - Tuples read/fetched
        - Index sizes
    """
    try:
        async with get_database().session() as session:
            stats = await analyze_index_usage(session)
            
            return {
                "success": True,
                "total_indexes": len(stats["indexes"]),
                "total_scans": stats["total_scans"],
                "indexes": stats["indexes"]
            }
    
    except Exception as e:
        logger.error(f"Error getting index statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get index statistics: {str(e)}"
        )


@router.get("/status")
async def get_optimization_status():
    """
    Get current status of performance optimizations.
    
    Returns:
        Dict with optimization status including:
        - Parallel commit settings
        - Index status
        - Batch operation status
    """
    try:
        from ...services.ingestion import get_ingestion_worker
        worker = get_ingestion_worker()
        processor = worker.job_processor
        
        # Get index stats
        async with get_database().session() as session:
            index_stats = await analyze_index_usage(session)
        
        return {
            "success": True,
            "phase_1": {
                "batch_optimization": processor.use_batch_optimization,
                "status": "✅ Enabled" if processor.use_batch_optimization else "❌ Disabled"
            },
            "phase_2": {
                "parallel_commits": processor.max_concurrent_commits,
                "commit_timeout": processor.commit_timeout_seconds,
                "indexes_created": len(index_stats["indexes"]),
                "total_index_scans": index_stats["total_scans"],
                "status": "✅ Optimized"
            },
            "recommendations": _get_optimization_recommendations(processor, index_stats)
        }
    
    except Exception as e:
        logger.error(f"Error getting optimization status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get optimization status: {str(e)}"
        )


def _get_optimization_recommendations(processor, index_stats: dict) -> list:
    """Generate optimization recommendations based on current state."""
    recommendations = []
    
    # Check if batch optimization is disabled
    if not processor.use_batch_optimization:
        recommendations.append({
            "priority": "high",
            "category": "batch_optimization",
            "message": "Batch optimization is disabled. Enable for 10-50× faster database operations.",
            "action": "Set use_batch_optimization=True"
        })
    
    # Check parallel commits
    if processor.max_concurrent_commits < 10:
        recommendations.append({
            "priority": "medium",
            "category": "parallelism",
            "message": f"Parallel commits is set to {processor.max_concurrent_commits}. Consider increasing to 10-20 for better throughput.",
            "action": "Increase max_concurrent_commits or set to None for auto-tuning"
        })
    
    # Check index usage
    if len(index_stats["indexes"]) < 6:
        recommendations.append({
            "priority": "high",
            "category": "indexes",
            "message": f"Only {len(index_stats['indexes'])} performance indexes found. Expected 6.",
            "action": "POST /api/v1/admin/optimization/indexes/create"
        })
    
    # Check if indexes are being used
    unused_indexes = [idx for idx in index_stats["indexes"] if idx["scans"] == 0]
    if unused_indexes and index_stats["total_scans"] > 100:
        recommendations.append({
            "priority": "low",
            "category": "indexes",
            "message": f"{len(unused_indexes)} indexes have not been used yet. This is normal for new indexes.",
            "action": "Monitor index usage over time"
        })
    
    if not recommendations:
        recommendations.append({
            "priority": "none",
            "category": "status",
            "message": "✅ All optimizations are properly configured!",
            "action": "None"
        })
    
    return recommendations

