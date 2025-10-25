"""
Migration 010: Add Temporal Columns to Documents

Adds temporal metadata columns to support time-travel RAG queries:
- git_date: Timestamp of the git commit (for temporal filtering)
- git_author: Author of the commit
- git_author_email: Author's email
- git_commit_message: Commit message

These columns enable:
- Temporal RAG queries ("as of" date filtering)
- Evolution tracking
- Period comparison
- Timeline analysis

NOTE: Columns are nullable because existing documents don't have this data.
Re-ingestion will populate them for enriched/git_history modes.
"""

import logging
import asyncpg

logger = logging.getLogger(__name__)


async def upgrade(connection: asyncpg.Connection) -> None:
    """
    Upgrade database schema to add temporal columns to documents table.
    
    Steps:
    1. Add temporal columns (nullable)
    2. Create indexes for query performance
    3. Log completion
    """
    logger.info("🚀 Starting migration 010: Add temporal columns to documents")
    
    # Step 1: Add temporal columns
    logger.info("  📝 Step 1/3: Adding temporal columns to documents table...")
    await connection.execute("""
        ALTER TABLE documents
        ADD COLUMN IF NOT EXISTS git_date TIMESTAMP,
        ADD COLUMN IF NOT EXISTS git_author VARCHAR(255),
        ADD COLUMN IF NOT EXISTS git_author_email VARCHAR(255),
        ADD COLUMN IF NOT EXISTS git_commit_message TEXT;
    """)
    logger.info("  ✅ Temporal columns added")
    
    # Step 2: Create indexes for performance
    logger.info("  📝 Step 2/3: Creating indexes...")
    
    # Index on git_date for temporal filtering
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_git_date 
        ON documents(git_date);
    """)
    
    # Composite index for service+date queries (most common pattern)
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_git_date_service 
        ON documents(git_date, service_name);
    """)
    
    # Index on git_author for author-based queries
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_git_author 
        ON documents(git_author);
    """)
    
    logger.info("  ✅ Indexes created")
    
    # Step 3: Log statistics
    logger.info("  📝 Step 3/3: Gathering statistics...")
    
    total_docs = await connection.fetchval("SELECT COUNT(*) FROM documents")
    docs_with_commit = await connection.fetchval(
        "SELECT COUNT(*) FROM documents WHERE git_commit_sha IS NOT NULL"
    )
    
    logger.info(f"  📊 Total documents: {total_docs}")
    logger.info(f"  📊 Documents with git_commit_sha: {docs_with_commit}")
    logger.info(f"  📊 Documents that will get temporal data on re-ingest: {docs_with_commit}")
    
    logger.info("✅ Migration 010 complete: Temporal columns added successfully")
    logger.info("")
    logger.info("⚠️  IMPORTANT: Existing documents have NULL temporal fields")
    logger.info("   To populate temporal data:")
    logger.info("   1. Run enriched ingestion on repositories")
    logger.info("   2. Or use script to backfill from git_commits table")


async def downgrade(connection: asyncpg.Connection) -> None:
    """
    Downgrade: Remove temporal columns from documents table.
    
    ⚠️ WARNING: This will delete temporal data!
    """
    logger.info("🔄 Rolling back migration 010: Removing temporal columns")
    
    # Drop indexes first
    await connection.execute("""
        DROP INDEX IF EXISTS idx_documents_git_date;
        DROP INDEX IF EXISTS idx_documents_git_date_service;
        DROP INDEX IF EXISTS idx_documents_git_author;
    """)
    
    # Drop columns
    await connection.execute("""
        ALTER TABLE documents
        DROP COLUMN IF EXISTS git_date,
        DROP COLUMN IF EXISTS git_author,
        DROP COLUMN IF EXISTS git_author_email,
        DROP COLUMN IF EXISTS git_commit_message;
    """)
    
    logger.info("✅ Migration 010 rolled back successfully")

