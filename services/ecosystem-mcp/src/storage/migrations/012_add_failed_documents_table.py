"""
Database Migration 012: Add Failed Documents Table

Creates the failed_documents table to persistently track document processing failures
and retry metadata for the retry infrastructure.

Features:
- Tracks job_id, file_path, error details
- Stores retry count and next retry time
- Records error classification
- Tracks dead letter queue status
- Indexes for performance
- Supports rollback

Created: 2025-10-26
Phase: 1.4 (Retry Infrastructure)
"""

import logging
import asyncpg

logger = logging.getLogger(__name__)


async def upgrade(connection: asyncpg.Connection) -> None:
    """
    Create failed_documents table for retry infrastructure.
    
    This table tracks all document processing failures, enabling:
    - Persistent retry queue
    - Error analytics
    - Dead letter queue tracking
    - Retry history and audit trail
    """
    logger.info("🚀 Starting migration 012: Add failed_documents table")
    
    # Create failed_documents table
    logger.info("  📝 Creating failed_documents table...")
    await connection.execute("""
        CREATE TABLE IF NOT EXISTS failed_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            
            -- Job and document identification
            job_id UUID NOT NULL REFERENCES ingestion_jobs(id) ON DELETE CASCADE,
            file_path TEXT NOT NULL,
            content_hash VARCHAR(64),  -- SHA256 hash if available
            
            -- Service context
            service_name VARCHAR(255) NOT NULL,
            mode VARCHAR(50) NOT NULL,
            repo_path TEXT NOT NULL,
            
            -- Error information
            error_type VARCHAR(50) NOT NULL,  -- From ErrorType enum
            error_message TEXT NOT NULL,
            error_stack_trace TEXT,
            
            -- Retry metadata
            retry_count INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL DEFAULT 5,
            next_retry_at TIMESTAMP,
            last_retry_at TIMESTAMP,
            
            -- Status tracking
            status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, retrying, dead_letter, recovered
            in_dead_letter_queue BOOLEAN NOT NULL DEFAULT FALSE,
            recovered_at TIMESTAMP,
            
            -- Timestamps
            failed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            moved_to_dlq_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Additional context (JSON)
            retry_context JSONB,
            error_metadata JSONB
        );
    """)
    
    # Create indexes for performance
    logger.info("  📝 Creating indexes for failed_documents table...")
    
    # Index for finding documents to retry
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_failed_documents_retry_lookup 
        ON failed_documents (status, next_retry_at)
        WHERE in_dead_letter_queue = FALSE;
    """)
    
    # Index for job-based queries
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_failed_documents_job_id 
        ON failed_documents (job_id);
    """)
    
    # Index for error type analytics
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_failed_documents_error_type 
        ON failed_documents (error_type);
    """)
    
    # Index for retry count (find documents near max retries)
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_failed_documents_retry_count 
        ON failed_documents (retry_count, status);
    """)
    
    # Index for dead letter queue
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_failed_documents_dlq 
        ON failed_documents (in_dead_letter_queue, moved_to_dlq_at)
        WHERE in_dead_letter_queue = TRUE;
    """)
    
    # Index for file_path lookups
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_failed_documents_file_path 
        ON failed_documents (file_path);
    """)
    
    # Create function to auto-update updated_at timestamp
    logger.info("  📝 Creating auto-update trigger for updated_at...")
    await connection.execute("""
        CREATE OR REPLACE FUNCTION update_failed_documents_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger
    await connection.execute("""
        CREATE TRIGGER trigger_update_failed_documents_updated_at
        BEFORE UPDATE ON failed_documents
        FOR EACH ROW
        EXECUTE FUNCTION update_failed_documents_updated_at();
    """)
    
    logger.info("✅ Migration 012 complete: failed_documents table created with 6 indexes and trigger")


async def downgrade(connection: asyncpg.Connection) -> None:
    """
    Remove failed_documents table and associated objects.
    
    WARNING: This will permanently delete all failure tracking data.
    """
    logger.info("🔙 Starting downgrade 012: Remove failed_documents table")
    
    # Drop trigger first
    logger.info("  📝 Dropping trigger...")
    await connection.execute("""
        DROP TRIGGER IF EXISTS trigger_update_failed_documents_updated_at 
        ON failed_documents;
    """)
    
    # Drop function
    logger.info("  📝 Dropping function...")
    await connection.execute("""
        DROP FUNCTION IF EXISTS update_failed_documents_updated_at();
    """)
    
    # Drop indexes (will be dropped automatically with table, but explicit for clarity)
    logger.info("  📝 Dropping indexes...")
    await connection.execute("""
        DROP INDEX IF EXISTS idx_failed_documents_retry_lookup;
        DROP INDEX IF EXISTS idx_failed_documents_job_id;
        DROP INDEX IF EXISTS idx_failed_documents_error_type;
        DROP INDEX IF EXISTS idx_failed_documents_retry_count;
        DROP INDEX IF EXISTS idx_failed_documents_dlq;
        DROP INDEX IF EXISTS idx_failed_documents_file_path;
    """)
    
    # Drop table
    logger.info("  📝 Dropping failed_documents table...")
    await connection.execute("""
        DROP TABLE IF EXISTS failed_documents CASCADE;
    """)
    
    logger.info("✅ Downgrade 012 complete: failed_documents table removed")

