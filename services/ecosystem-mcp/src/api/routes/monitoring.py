"""
Monitoring API endpoints for system health and metadata consistency.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query as QueryParam
from pydantic import BaseModel, Field

from ...services.monitoring.metadata_consistency import (
    get_metadata_consistency_monitor,
    ConsistencyReport,
    MetadataMismatch
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ConsistencyReportResponse(BaseModel):
    """Response model for consistency report."""
    success: bool
    report: dict
    message: Optional[str] = None


@router.get("/metadata/consistency")
async def check_metadata_consistency(
    sample_size: int = QueryParam(
        100,
        ge=10,
        le=1000,
        description="Number of documents to sample for detailed checks"
    ),
    check_all: bool = QueryParam(
        False,
        description="Check all documents (slower but comprehensive)"
    )
):
    """
    Check metadata consistency between PostgreSQL and ChromaDB.
    
    Returns health status, coverage statistics, and recommendations.
    
    **Health Status:**
    - `healthy`: All systems nominal
    - `warning`: Inconsistencies detected, action recommended
    - `critical`: Severe issues, immediate action required
    
    **Use Cases:**
    - Monitor Temporal RAG health
    - Detect metadata drift
    - Validate ingestion pipeline
    - Pre-deployment checks
    """
    try:
        logger.info(f"🔍 Running consistency check (sample_size={sample_size}, check_all={check_all})")
        
        monitor = get_metadata_consistency_monitor()
        report = await monitor.check_consistency(
            sample_size=sample_size,
            check_all=check_all
        )
        
        # Format response
        response_data = {
            "timestamp": report.timestamp.isoformat(),
            "health_status": report.health_status,
            "metrics": {
                "total_postgresql": report.total_postgresql,
                "total_chromadb": report.total_chromadb,
                "matched": report.matched,
                "postgresql_only": report.postgresql_only,
                "chromadb_only": report.chromadb_only,
                "metadata_mismatches": len(report.metadata_mismatches)
            },
            "coverage": {
                "postgresql": f"{report.coverage_postgresql:.1%}",
                "chromadb": f"{report.coverage_chromadb:.1%}",
                "postgresql_raw": report.coverage_postgresql,
                "chromadb_raw": report.coverage_chromadb
            },
            "recommendations": report.recommendations,
            "details": {
                "mismatches": [
                    {
                        "document_id": m.document_id,
                        "field": m.field,
                        "postgresql_value": str(m.postgresql_value),
                        "chromadb_value": str(m.chromadb_value),
                        "severity": m.severity
                    }
                    for m in report.metadata_mismatches[:10]  # First 10
                ],
                "total_mismatches": len(report.metadata_mismatches)
            }
        }
        
        # Log result
        logger.info(
            f"✅ Consistency check complete: {report.health_status.upper()} | "
            f"Coverage: PG={report.coverage_postgresql:.1%}, Chroma={report.coverage_chromadb:.1%}"
        )
        
        return ConsistencyReportResponse(
            success=True,
            report=response_data,
            message=f"Consistency check complete: {report.health_status}"
        )
        
    except Exception as e:
        logger.error(f"❌ Consistency check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Consistency check failed: {str(e)}"
        )


@router.get("/metadata/consistency/health")
async def get_consistency_health():
    """
    Quick health check for metadata consistency.
    
    Returns only the health status without detailed analysis.
    Useful for monitoring dashboards and alerts.
    """
    try:
        monitor = get_metadata_consistency_monitor()
        report = await monitor.check_consistency(sample_size=50)
        
        return {
            "success": True,
            "health_status": report.health_status,
            "coverage_chromadb": report.coverage_chromadb,
            "recommendations_count": len(report.recommendations),
            "timestamp": report.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )

