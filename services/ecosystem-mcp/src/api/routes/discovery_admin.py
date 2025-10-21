"""
Discovery Admin Routes

Admin endpoints for discovery system management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ...storage import get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/discovery/admin", tags=["Discovery Admin"])


@router.post(
    "/migrate",
    summary="Run discovery database migration",
    description="Creates tables for processing plans, sub-jobs, and file classifications"
)
async def run_migration(db: AsyncSession = Depends(get_database)):
    """
    Run discovery database migration.
    
    Creates:
    - processing_plans table
    - sub_jobs table
    - file_classifications table
    - Performance indexes
    """
    try:
        logger.info("🔄 Running discovery migration...")
        
        # Lazy import to avoid circular dependency
        from ...storage.migrations import add_discovery_tables
        
        async with db.session() as session:
            await add_discovery_tables.upgrade(session)
        
        logger.info("✅ Discovery migration complete")
        
        return {
            "success": True,
            "message": "Discovery migration completed successfully",
            "tables_created": [
                "processing_plans",
                "sub_jobs",
                "file_classifications"
            ],
            "indexes_created": 8
        }
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@router.post(
    "/rollback",
    summary="Rollback discovery database migration",
    description="Drops all discovery tables and indexes"
)
async def rollback_migration(db: AsyncSession = Depends(get_database)):
    """
    Rollback discovery database migration.
    
    Drops:
    - processing_plans table
    - sub_jobs table
    - file_classifications table
    - All indexes
    """
    try:
        logger.info("🔄 Rolling back discovery migration...")
        
        # Lazy import to avoid circular dependency
        from ...storage.migrations import add_discovery_tables
        
        async with db.session() as session:
            await add_discovery_tables.downgrade(session)
        
        logger.info("✅ Discovery migration rollback complete")
        
        return {
            "success": True,
            "message": "Discovery migration rolled back successfully",
            "tables_dropped": [
                "processing_plans",
                "sub_jobs",
                "file_classifications"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {str(e)}"
        )


@router.post(
    "/migrate-execution",
    summary="Run execution tracking migration",
    description="Creates tables for execution metrics and sub-job metrics"
)
async def run_execution_migration(db: AsyncSession = Depends(get_database)):
    """
    Run execution tracking database migration.
    
    Creates:
    - execution_metrics table
    - sub_job_metrics table
    - Performance indexes
    """
    try:
        logger.info("🔄 Running execution tracking migration...")
        
        # Lazy import to avoid circular dependency
        from ...storage.migrations import add_execution_tracking
        
        async with db.session() as session:
            await add_execution_tracking.upgrade(session)
        
        logger.info("✅ Execution tracking migration complete")
        
        return {
            "success": True,
            "message": "Execution tracking migration completed successfully",
            "tables_created": [
                "execution_metrics",
                "sub_job_metrics"
            ],
            "indexes_created": 8
        }
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@router.post(
    "/rollback-execution",
    summary="Rollback execution tracking migration",
    description="Drops all execution tracking tables and indexes"
)
async def rollback_execution_migration(db: AsyncSession = Depends(get_database)):
    """
    Rollback execution tracking database migration.
    
    Drops:
    - execution_metrics table
    - sub_job_metrics table
    - All indexes
    """
    try:
        logger.info("🔄 Rolling back execution tracking migration...")
        
        # Lazy import to avoid circular dependency
        from ...storage.migrations import add_execution_tracking
        
        async with db.session() as session:
            await add_execution_tracking.downgrade(session)
        
        logger.info("✅ Execution tracking migration rollback complete")
        
        return {
            "success": True,
            "message": "Execution tracking migration rolled back successfully",
            "tables_dropped": [
                "execution_metrics",
                "sub_job_metrics"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {str(e)}"
        )


@router.post(
    "/migrate-documentation",
    summary="Run documentation database migration",
    description="Creates tables for documentation runs and artifacts (Phase 4)"
)
async def run_documentation_migration(db: AsyncSession = Depends(get_database)):
    """
    Run documentation database migration.
    
    Creates:
    - documentation_runs table
    - documentation_artifacts table
    - Performance indexes
    """
    try:
        logger.info("🔄 Running documentation migration...")
        
        # Lazy import to avoid circular dependency
        from ...storage.migrations import add_documentation_tables
        
        async with db.session() as session:
            await add_documentation_tables.upgrade(session)
        
        logger.info("✅ Documentation migration complete")
        
        return {
            "success": True,
            "message": "Documentation migration completed successfully",
            "tables_created": [
                "documentation_runs",
                "documentation_artifacts"
            ],
            "indexes_created": 8
        }
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@router.post(
    "/rollback-documentation",
    summary="Rollback documentation database migration",
    description="Drops all documentation tables and indexes"
)
async def rollback_documentation_migration(db: AsyncSession = Depends(get_database)):
    """
    Rollback documentation database migration.
    
    Drops:
    - documentation_runs table
    - documentation_artifacts table
    - All indexes
    """
    try:
        logger.info("🔄 Rolling back documentation migration...")
        
        # Lazy import to avoid circular dependency
        from ...storage.migrations import add_documentation_tables
        
        async with db.session() as session:
            await add_documentation_tables.downgrade(session)
        
        logger.info("✅ Documentation migration rollback complete")
        
        return {
            "success": True,
            "message": "Documentation migration rolled back successfully",
            "tables_dropped": [
                "documentation_runs",
                "documentation_artifacts"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {str(e)}"
        )
