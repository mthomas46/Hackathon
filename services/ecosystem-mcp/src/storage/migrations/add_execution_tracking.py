"""
Database Migration: Execution Tracking Tables

Adds tables for tracking sub-job execution metrics and performance.
"""

import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


async def upgrade(session):
    """
    Create execution tracking tables.
    
    Tables:
    - execution_metrics: Track execution performance metrics
    - sub_job_metrics: Track individual sub-job metrics
    """
    logger.info("Creating execution tracking tables...")
    
    # Create execution_metrics table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS execution_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plan_id UUID NOT NULL REFERENCES processing_plans(id) ON DELETE CASCADE,
            
            -- Timing metrics
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration_seconds FLOAT,
            
            -- File metrics
            total_files INTEGER NOT NULL DEFAULT 0,
            files_processed INTEGER NOT NULL DEFAULT 0,
            files_failed INTEGER NOT NULL DEFAULT 0,
            files_skipped INTEGER NOT NULL DEFAULT 0,
            
            -- Sub-job metrics
            total_sub_jobs INTEGER NOT NULL DEFAULT 0,
            sub_jobs_completed INTEGER NOT NULL DEFAULT 0,
            sub_jobs_failed INTEGER NOT NULL DEFAULT 0,
            max_concurrent INTEGER NOT NULL DEFAULT 5,
            
            -- Performance metrics
            avg_processing_time_per_file FLOAT,
            avg_processing_time_per_sub_job FLOAT,
            peak_memory_mb FLOAT,
            peak_cpu_percent FLOAT,
            
            -- Throughput metrics
            files_per_second FLOAT,
            sub_jobs_per_minute FLOAT,
            
            -- Status
            status VARCHAR(50) NOT NULL DEFAULT 'running',
            error_message TEXT,
            
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """))
    
    # Create sub_job_metrics table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS sub_job_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            sub_job_id UUID NOT NULL REFERENCES sub_jobs(id) ON DELETE CASCADE,
            execution_metrics_id UUID REFERENCES execution_metrics(id) ON DELETE CASCADE,
            
            -- Timing
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration_seconds FLOAT,
            queue_time_seconds FLOAT,
            
            -- Processing metrics
            files_processed INTEGER NOT NULL DEFAULT 0,
            files_failed INTEGER NOT NULL DEFAULT 0,
            files_skipped INTEGER NOT NULL DEFAULT 0,
            
            -- Embedding metrics
            embeddings_generated INTEGER NOT NULL DEFAULT 0,
            embedding_time_seconds FLOAT,
            avg_embedding_time_per_file FLOAT,
            
            -- Resource metrics
            memory_used_mb FLOAT,
            cpu_percent FLOAT,
            
            -- Performance
            processing_rate FLOAT,
            
            -- Status
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            error_message TEXT,
            retry_count INTEGER NOT NULL DEFAULT 0,
            
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """))
    
    # Create indexes for execution_metrics
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_execution_metrics_plan_id ON execution_metrics(plan_id)",
        "CREATE INDEX IF NOT EXISTS idx_execution_metrics_status ON execution_metrics(status)",
        "CREATE INDEX IF NOT EXISTS idx_execution_metrics_start_time ON execution_metrics(start_time DESC)",
        "CREATE INDEX IF NOT EXISTS idx_execution_metrics_duration ON execution_metrics(duration_seconds)"
    ]
    
    for index_sql in indexes:
        await session.execute(text(index_sql))
    
    # Create indexes for sub_job_metrics
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_sub_job_metrics_sub_job_id ON sub_job_metrics(sub_job_id)",
        "CREATE INDEX IF NOT EXISTS idx_sub_job_metrics_execution_id ON sub_job_metrics(execution_metrics_id)",
        "CREATE INDEX IF NOT EXISTS idx_sub_job_metrics_status ON sub_job_metrics(status)",
        "CREATE INDEX IF NOT EXISTS idx_sub_job_metrics_duration ON sub_job_metrics(duration_seconds)"
    ]
    
    for index_sql in indexes:
        await session.execute(text(index_sql))
    
    await session.commit()
    
    logger.info("✅ Execution tracking tables created successfully")


async def downgrade(session):
    """Drop execution tracking tables."""
    logger.info("Dropping execution tracking tables...")
    
    # Drop indexes first
    indexes = [
        "DROP INDEX IF EXISTS idx_sub_job_metrics_duration",
        "DROP INDEX IF EXISTS idx_sub_job_metrics_status",
        "DROP INDEX IF EXISTS idx_sub_job_metrics_execution_id",
        "DROP INDEX IF EXISTS idx_sub_job_metrics_sub_job_id",
        "DROP INDEX IF EXISTS idx_execution_metrics_duration",
        "DROP INDEX IF EXISTS idx_execution_metrics_start_time",
        "DROP INDEX IF EXISTS idx_execution_metrics_status",
        "DROP INDEX IF EXISTS idx_execution_metrics_plan_id"
    ]
    
    for index_sql in indexes:
        await session.execute(text(index_sql))
    
    # Drop tables
    await session.execute(text("DROP TABLE IF EXISTS sub_job_metrics CASCADE"))
    await session.execute(text("DROP TABLE IF EXISTS execution_metrics CASCADE"))
    
    await session.commit()
    
    logger.info("✅ Execution tracking tables dropped successfully")

