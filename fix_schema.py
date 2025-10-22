#!/usr/bin/env python
"""Quick fix for missing ingestion_mode column."""

import asyncio
import logging
from sqlalchemy import text
import sys
sys.path.insert(0, '/app')

from src.storage import get_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_schema():
    """Add missing ingestion_mode column."""
    logger.info("🔧 Adding missing ingestion_mode column...")
    
    db = get_database()
    async with db.session() as session:
        try:
            # Add column
            await session.execute(text(
                "ALTER TABLE documents " 
                "ADD COLUMN IF NOT EXISTS ingestion_mode VARCHAR(20) NOT NULL DEFAULT 'git_history'"
            ))
            await session.commit()
            logger.info("✅ Added ingestion_mode column")
            
            # Create index
            await session.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_documents_mode ON documents(ingestion_mode)"
            ))
            await session.commit()
            logger.info("✅ Created index on ingestion_mode")
            
            # Verify
            result = await session.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='documents' AND column_name='ingestion_mode'"
            ))
            if result.rowcount > 0:
                logger.info("✅ Column exists and is accessible")
            else:
                logger.error("❌ Column not found after creation")
                
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(fix_schema())

