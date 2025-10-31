"""
Document Cleanup API Endpoints

Provides endpoints for cleaning up low-value documents and embeddings
using intelligent filtering rules.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...utils.document_cleanup import (
    DocumentCleanupService,
    cleanup_low_value_documents,
    cleanup_old_versions_only,
    get_cleanup_recommendations
)
from ...utils.intelligent_file_filter import FilePriority

logger = logging.getLogger(__name__)

router = APIRouter()


class CleanupRequest(BaseModel):
    """Request for document cleanup."""
    dry_run: bool = Field(True, description="If true, only preview what would be deleted")
    include_latest: bool = Field(False, description="If true, can delete latest versions")
    categories_to_remove: Optional[List[str]] = Field(None, description="Specific categories to remove")
    min_priority: Optional[str] = Field("LOW", description="Minimum priority to keep (CRITICAL, HIGH, MEDIUM, LOW)")


class CategoryCleanupRequest(BaseModel):
    """Request for category-specific cleanup."""
    categories: List[str] = Field(..., description="Categories to remove (e.g., temporary, configuration)")
    dry_run: bool = Field(True, description="Preview mode")


class OldVersionCleanupRequest(BaseModel):
    """Request for old version cleanup."""
    dry_run: bool = Field(True, description="Preview mode")
    older_than_days: Optional[int] = Field(None, description="Only delete versions older than N days")


@router.get("/cleanup/report")
async def get_cleanup_report():
    """
    Get a report of what can be cleaned up.
    
    Returns recommendations for cleanup actions.
    
    Example:
    ```bash
    curl http://localhost:8000/api/v1/documents/cleanup/report | jq
    ```
    """
    try:
        logger.info("📊 Generating cleanup report...")
        report = await get_cleanup_recommendations()
        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/analyze")
async def analyze_documents(
    include_latest: bool = False,
    min_priority: str = "LOW"
):
    """
    Analyze documents and identify cleanup candidates.
    
    Args:
        include_latest: Analyze latest versions too
        min_priority: Minimum priority to keep (CRITICAL, HIGH, MEDIUM, LOW)
    
    Returns:
        Analysis results with statistics
    
    Example:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/documents/cleanup/analyze?min_priority=MEDIUM" | jq
    ```
    """
    try:
        logger.info(f"🔍 Analyzing documents (include_latest={include_latest}, min_priority={min_priority})")
        
        # Convert string to FilePriority
        try:
            priority = FilePriority[min_priority]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority: {min_priority}. Must be one of: CRITICAL, HIGH, MEDIUM, LOW, SKIP"
            )
        
        service = DocumentCleanupService()
        analysis = await service.analyze_documents(
            include_latest=include_latest,
            min_priority=priority
        )
        
        return {
            "success": True,
            "analysis": analysis
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/execute")
async def cleanup_documents(request: CleanupRequest):
    """
    Execute document cleanup.
    
    **IMPORTANT:** Always run with dry_run=true first!
    
    Args:
        request: Cleanup configuration
    
    Returns:
        Cleanup results
    
    Example (DRY RUN):
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/cleanup/execute \
      -H 'Content-Type: application/json' \
      -d '{"dry_run": true, "min_priority": "MEDIUM"}' | jq
    ```
    
    Example (ACTUAL DELETE):
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/cleanup/execute \
      -H 'Content-Type: application/json' \
      -d '{"dry_run": false, "min_priority": "LOW"}' | jq
    ```
    """
    try:
        if not request.dry_run:
            logger.warning("⚠️  EXECUTING ACTUAL CLEANUP - Documents will be deleted!")
        
        # Convert string to FilePriority if provided
        priority = None
        if request.min_priority:
            try:
                priority = FilePriority[request.min_priority]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid priority: {request.min_priority}"
                )
        
        service = DocumentCleanupService()
        result = await service.cleanup_documents(
            dry_run=request.dry_run,
            include_latest=request.include_latest,
            categories_to_remove=request.categories_to_remove,
            min_priority=priority
        )
        
        return {
            "success": True,
            "result": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/by-category")
async def cleanup_by_category(request: CategoryCleanupRequest):
    """
    Clean up documents in specific categories.
    
    Common categories:
    - temporary: Logs, temp files
    - configuration: Config files, .env, .ini
    - build_artifact: Build outputs, compiled files
    - test: Test files
    - data: Data files
    
    Example (DRY RUN):
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/cleanup/by-category \
      -H 'Content-Type: application/json' \
      -d '{"categories": ["temporary", "configuration"], "dry_run": true}' | jq
    ```
    
    Example (ACTUAL DELETE):
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/cleanup/by-category \
      -H 'Content-Type: application/json' \
      -d '{"categories": ["temporary"], "dry_run": false}' | jq
    ```
    """
    try:
        if not request.dry_run:
            logger.warning(f"⚠️  Deleting documents in categories: {request.categories}")
        
        service = DocumentCleanupService()
        result = await service.cleanup_by_category(
            categories=request.categories,
            dry_run=request.dry_run
        )
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Category cleanup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/old-versions")
async def cleanup_old_versions(request: OldVersionCleanupRequest):
    """
    Clean up old document versions (keep only latest).
    
    This is safe to run as it only removes non-latest versions.
    
    Example (DRY RUN):
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/cleanup/old-versions \
      -H 'Content-Type: application/json' \
      -d '{"dry_run": true}' | jq
    ```
    
    Example (DELETE old versions older than 90 days):
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/cleanup/old-versions \
      -H 'Content-Type: application/json' \
      -d '{"dry_run": false, "older_than_days": 90}' | jq
    ```
    """
    try:
        if not request.dry_run:
            logger.warning("⚠️  Deleting old document versions")
        
        service = DocumentCleanupService()
        result = await service.cleanup_old_versions(
            dry_run=request.dry_run,
            older_than_days=request.older_than_days
        )
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Old version cleanup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/low-value")
async def cleanup_low_value(dry_run: bool = True):
    """
    Quick cleanup of low-value documents (logs, configs, build artifacts).
    
    This removes documents with SKIP priority according to intelligent filtering rules.
    
    Example (DRY RUN):
    ```bash
    curl -X POST "http://localhost:8000/api/v1/documents/cleanup/low-value?dry_run=true" | jq
    ```
    
    Example (ACTUAL DELETE):
    ```bash
    curl -X POST "http://localhost:8000/api/v1/documents/cleanup/low-value?dry_run=false" | jq
    ```
    """
    try:
        if not dry_run:
            logger.warning("⚠️  Deleting low-value documents")
        
        result = await cleanup_low_value_documents(dry_run=dry_run)
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Low-value cleanup failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

