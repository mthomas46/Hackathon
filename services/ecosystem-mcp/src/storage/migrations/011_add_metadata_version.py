"""
Migration 011: Add metadata_version column to documents table

This enables metadata-aware duplicate detection:
- Tracks metadata schema version
- Allows re-processing when new metadata fields are added
- Prevents skipping documents with incomplete metadata

Author: AI Assistant
Date: 2025-10-25
"""

import logging
import asyncpg

logger = logging.getLogger(__name__)

async def upgrade(connection: asyncpg.Connection) -> None:
    """Add metadata_version column."""
    logger.info("🚀 Starting migration 011: Add metadata_version column")
    
    # Add metadata_version column
    logger.info("  📝 Adding metadata_version column...")
    await connection.execute("""
        ALTER TABLE documents
        ADD COLUMN IF NOT EXISTS metadata_version INTEGER DEFAULT 1;
    """)
    
    # Backfill existing documents with version 1
    logger.info("  📝 Backfilling existing documents with version 1...")
    result = await connection.execute("""
        UPDATE documents
        SET metadata_version = 1
        WHERE metadata_version IS NULL;
    """)
    logger.info(f"  ✅ Updated {result} documents")
    
    # Create index for performance
    logger.info("  📝 Creating index on metadata_version...")
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_metadata_version 
        ON documents (metadata_version);
    """)
    
    logger.info("✅ Migration 011 complete: metadata_version column added")

async def downgrade(connection: asyncpg.Connection) -> None:
    """Remove metadata_version column."""
    logger.info("🔙 Starting downgrade 011: Remove metadata_version column")
    
    # Drop index
    logger.info("  📝 Dropping index on metadata_version...")
    await connection.execute("""
        DROP INDEX IF EXISTS idx_documents_metadata_version;
    """)
    
    # Remove column
    logger.info("  📝 Removing metadata_version column...")
    await connection.execute("""
        ALTER TABLE documents
        DROP COLUMN IF EXISTS metadata_version;
    """)
    
    logger.info("✅ Downgrade 011 complete: metadata_version column removed")

