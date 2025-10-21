"""
Migration 002: Add Discovery and Sub-Job Tables

Adds tables for:
- processing_plans: Repository processing plans
- sub_jobs: Individual sub-jobs within a plan
- file_classifications: File importance classifications
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


async def upgrade(session: AsyncSession):
    """Apply the database schema upgrade."""
    logger.info("Applying migration: 002_add_discovery_and_sub_jobs")
    
    # Create processing_plans table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS processing_plans (
            id UUID PRIMARY KEY,
            repo_path TEXT NOT NULL,
            total_files INTEGER NOT NULL DEFAULT 0,
            total_size_mb FLOAT NOT NULL DEFAULT 0,
            estimated_time_minutes FLOAT NOT NULL DEFAULT 0,
            max_parallelization INTEGER NOT NULL DEFAULT 1,
            processing_order JSONB,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'pending'
        );
    """))
    logger.info("  ✅ Created processing_plans table")
    
    # Create sub_jobs table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS sub_jobs (
            id UUID PRIMARY KEY,
            plan_id UUID NOT NULL REFERENCES processing_plans(id) ON DELETE CASCADE,
            sub_job_id VARCHAR(255) NOT NULL,
            sub_job_name VARCHAR(255) NOT NULL,
            file_count INTEGER NOT NULL DEFAULT 0,
            priority INTEGER NOT NULL DEFAULT 0,
            estimated_time_minutes FLOAT NOT NULL DEFAULT 0,
            dependencies JSONB DEFAULT '[]',
            status VARCHAR(50) DEFAULT 'pending',
            processed_files INTEGER DEFAULT 0,
            failed_files INTEGER DEFAULT 0,
            skipped_files INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP WITHOUT TIME ZONE,
            completed_at TIMESTAMP WITHOUT TIME ZONE,
            UNIQUE(plan_id, sub_job_id)
        );
    """))
    logger.info("  ✅ Created sub_jobs table")
    
    # Create file_classifications table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS file_classifications (
            id UUID PRIMARY KEY,
            plan_id UUID NOT NULL REFERENCES processing_plans(id) ON DELETE CASCADE,
            file_path TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            size_bytes BIGINT NOT NULL DEFAULT 0,
            extension VARCHAR(50),
            language VARCHAR(100),
            is_code BOOLEAN DEFAULT FALSE,
            is_test BOOLEAN DEFAULT FALSE,
            is_doc BOOLEAN DEFAULT FALSE,
            is_config BOOLEAN DEFAULT FALSE,
            importance_level VARCHAR(50) NOT NULL,
            importance_score FLOAT NOT NULL DEFAULT 0.5,
            priority INTEGER NOT NULL DEFAULT 1000,
            sub_job_id VARCHAR(255),
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(plan_id, file_path)
        );
    """))
    logger.info("  ✅ Created file_classifications table")
    
    # Create indexes for performance (one at a time for asyncpg)
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_sub_jobs_plan_id ON sub_jobs (plan_id)",
        "CREATE INDEX IF NOT EXISTS idx_sub_jobs_status ON sub_jobs (status)",
        "CREATE INDEX IF NOT EXISTS idx_sub_jobs_priority ON sub_jobs (priority)",
        "CREATE INDEX IF NOT EXISTS idx_file_classifications_plan_id ON file_classifications (plan_id)",
        "CREATE INDEX IF NOT EXISTS idx_file_classifications_importance ON file_classifications (importance_level)",
        "CREATE INDEX IF NOT EXISTS idx_file_classifications_priority ON file_classifications (priority)",
        "CREATE INDEX IF NOT EXISTS idx_processing_plans_status ON processing_plans (status)",
        "CREATE INDEX IF NOT EXISTS idx_processing_plans_created_at ON processing_plans (created_at)"
    ]
    for index_sql in indexes:
        await session.execute(text(index_sql))
    logger.info("  ✅ Created performance indexes")
    
    await session.commit()
    logger.info("✅ Migration 002 completed successfully")


async def downgrade(session: AsyncSession):
    """Revert the database schema upgrade."""
    logger.info("Reverting migration: 002_add_discovery_and_sub_jobs")
    
    # Drop indexes first (one at a time for asyncpg)
    indexes = [
        "DROP INDEX IF EXISTS idx_sub_jobs_plan_id",
        "DROP INDEX IF EXISTS idx_sub_jobs_status",
        "DROP INDEX IF EXISTS idx_sub_jobs_priority",
        "DROP INDEX IF EXISTS idx_file_classifications_plan_id",
        "DROP INDEX IF EXISTS idx_file_classifications_importance",
        "DROP INDEX IF EXISTS idx_file_classifications_priority",
        "DROP INDEX IF EXISTS idx_processing_plans_status",
        "DROP INDEX IF EXISTS idx_processing_plans_created_at"
    ]
    for index_sql in indexes:
        await session.execute(text(index_sql))
    logger.info("  ✅ Dropped performance indexes")
    
    # Drop tables (in reverse order due to foreign keys)
    await session.execute(text("DROP TABLE IF EXISTS file_classifications;"))
    logger.info("  ✅ Dropped file_classifications table")
    
    await session.execute(text("DROP TABLE IF EXISTS sub_jobs;"))
    logger.info("  ✅ Dropped sub_jobs table")
    
    await session.execute(text("DROP TABLE IF EXISTS processing_plans;"))
    logger.info("  ✅ Dropped processing_plans table")
    
    await session.commit()
    logger.info("✅ Migration 002 reverted successfully")


# Migration metadata
MIGRATION_ID = "002_add_discovery_and_sub_jobs"
MIGRATION_NAME = "Add Discovery and Sub-Job Tables"
MIGRATION_DESCRIPTION = "Creates tables for repository processing plans, sub-jobs, and file classifications"

