"""
Migration 009: Add Timeline Analysis Tables

Adds support for timeline-based document analysis:
- Timelines: Temporal organization of documents for a repository/service
- Time Periods: Discrete time periods within a timeline (e.g., Q1 2025, Oct 2025)
- Document Placements: Links documents to specific time periods
- Confidence tracking: Tracks temporal confidence based on ingestion mode

Features:
- Support for both git_history and snapshot ingestion modes
- Confidence-based operations (HIGH/MEDIUM/LOW/NONE)
- Multiple period generation strategies (monthly, quarterly, adaptive)
- Full JSONB metadata for flexibility
"""

import logging
from typing import Optional
import asyncpg

logger = logging.getLogger(__name__)


async def upgrade(connection: asyncpg.Connection) -> None:
    """
    Upgrade database schema to add timeline analysis tables.
    
    Creates:
    1. timelines table
    2. time_periods table
    3. document_placements table
    4. Indexes for performance
    5. Foreign key constraints
    """
    logger.info("🚀 Starting migration 009: Add timeline analysis tables")
    
    # Step 1: Create timelines table
    logger.info("  📝 Step 1/6: Creating timelines table...")
    await connection.execute("""
        CREATE TABLE IF NOT EXISTS timelines (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            service_name VARCHAR(255) NOT NULL,
            repo_path TEXT NOT NULL,
            
            -- Timeline range
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP NOT NULL,
            
            -- Confidence tracking
            confidence_level VARCHAR(20) NOT NULL,
            confidence_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            
            -- Period generation strategy
            period_strategy VARCHAR(50) NOT NULL DEFAULT 'adaptive',
            
            -- Timestamps
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            created_by VARCHAR(255),
            
            -- Metadata
            timeline_metadata JSONB DEFAULT '{}'::jsonb,
            
            -- Constraints
            CONSTRAINT ck_timeline_date_range CHECK (start_date <= end_date),
            CONSTRAINT ck_confidence_level CHECK (
                confidence_level IN ('HIGH', 'MEDIUM', 'LOW', 'NONE')
            )
        );
    """)
    logger.info("  ✅ Timelines table created")
    
    # Step 2: Create time_periods table
    logger.info("  📝 Step 2/6: Creating time_periods table...")
    await connection.execute("""
        CREATE TABLE IF NOT EXISTS time_periods (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            timeline_id UUID NOT NULL REFERENCES timelines(id) ON DELETE CASCADE,
            
            -- Period identification
            name VARCHAR(255) NOT NULL,
            description TEXT,
            
            -- Period range
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP NOT NULL,
            
            -- Ordering
            sequence_number INTEGER NOT NULL,
            
            -- Statistics
            document_count INTEGER NOT NULL DEFAULT 0,
            commit_count INTEGER NOT NULL DEFAULT 0,
            
            -- Metadata
            period_metadata JSONB DEFAULT '{}'::jsonb,
            
            -- Timestamps
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            
            -- Constraints
            CONSTRAINT ck_period_date_range CHECK (start_date <= end_date),
            CONSTRAINT ck_sequence_positive CHECK (sequence_number >= 1),
            CONSTRAINT ck_document_count_nonnegative CHECK (document_count >= 0),
            CONSTRAINT ck_commit_count_nonnegative CHECK (commit_count >= 0),
            CONSTRAINT uq_period_timeline_sequence UNIQUE (timeline_id, sequence_number)
        );
    """)
    logger.info("  ✅ Time periods table created")
    
    # Step 3: Create document_placements table
    logger.info("  📝 Step 3/6: Creating document_placements table...")
    await connection.execute("""
        CREATE TABLE IF NOT EXISTS document_placements (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            period_id UUID NOT NULL REFERENCES time_periods(id) ON DELETE CASCADE,
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            
            -- Placement details
            placement_date TIMESTAMP NOT NULL,
            placement_source VARCHAR(50) NOT NULL,
            
            -- Git information (optional)
            git_commit_sha VARCHAR(40) REFERENCES git_commits(sha) ON DELETE SET NULL,
            
            -- Relevance
            relevance_score FLOAT NOT NULL DEFAULT 1.0,
            
            -- Metadata
            placement_metadata JSONB DEFAULT '{}'::jsonb,
            
            -- Timestamp
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            
            -- Constraints
            CONSTRAINT ck_relevance_range CHECK (
                relevance_score >= 0.0 AND relevance_score <= 1.0
            ),
            CONSTRAINT ck_placement_source CHECK (
                placement_source IN ('git_commit', 'created_at', 'manual')
            ),
            CONSTRAINT uq_placement_period_document UNIQUE (period_id, document_id)
        );
    """)
    logger.info("  ✅ Document placements table created")
    
    # Step 4: Create indexes for timelines
    logger.info("  📝 Step 4/6: Creating indexes for timelines...")
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_timelines_service 
        ON timelines(service_name);
        
        CREATE INDEX IF NOT EXISTS idx_timelines_confidence 
        ON timelines(confidence_level);
        
        CREATE INDEX IF NOT EXISTS idx_timelines_dates 
        ON timelines(start_date, end_date);
        
        CREATE INDEX IF NOT EXISTS idx_timelines_created 
        ON timelines(created_at);
    """)
    logger.info("  ✅ Timeline indexes created")
    
    # Step 5: Create indexes for time_periods
    logger.info("  📝 Step 5/6: Creating indexes for time_periods...")
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_periods_timeline 
        ON time_periods(timeline_id);
        
        CREATE INDEX IF NOT EXISTS idx_periods_dates 
        ON time_periods(start_date, end_date);
        
        CREATE INDEX IF NOT EXISTS idx_periods_sequence 
        ON time_periods(timeline_id, sequence_number);
    """)
    logger.info("  ✅ Time period indexes created")
    
    # Step 6: Create indexes for document_placements
    logger.info("  📝 Step 6/6: Creating indexes for document_placements...")
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_placements_period 
        ON document_placements(period_id);
        
        CREATE INDEX IF NOT EXISTS idx_placements_document 
        ON document_placements(document_id);
        
        CREATE INDEX IF NOT EXISTS idx_placements_date 
        ON document_placements(placement_date);
        
        CREATE INDEX IF NOT EXISTS idx_placements_commit 
        ON document_placements(git_commit_sha);
    """)
    logger.info("  ✅ Document placement indexes created")
    
    # Validation
    logger.info("  📝 Validating migration...")
    
    # Check all tables exist
    tables = await connection.fetch("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('timelines', 'time_periods', 'document_placements');
    """)
    assert len(tables) == 3, "Not all tables were created"
    logger.info("  ✅ All tables created successfully")
    
    # Check all indexes exist
    indexes = await connection.fetch("""
        SELECT indexname FROM pg_indexes
        WHERE schemaname = 'public'
        AND indexname LIKE 'idx_timelines_%'
        OR indexname LIKE 'idx_periods_%'
        OR indexname LIKE 'idx_placements_%';
    """)
    assert len(indexes) >= 11, f"Expected at least 11 indexes, found {len(indexes)}"
    logger.info(f"  ✅ All indexes created successfully ({len(indexes)} total)")
    
    logger.info(
        "✅ Migration 009 complete! "
        "Timeline analysis tables created and ready for use."
    )


async def downgrade(connection: asyncpg.Connection) -> None:
    """
    Downgrade database schema (remove timeline analysis tables).
    
    WARNING: This will:
    - Remove all timeline data
    - Remove all time period data  
    - Remove all document placement data
    - Drop all related indexes
    """
    logger.info("🔄 Starting migration 009 downgrade...")
    
    # Step 1: Drop indexes first
    logger.info("  📝 Step 1/4: Dropping indexes...")
    await connection.execute("""
        DROP INDEX IF EXISTS idx_timelines_service;
        DROP INDEX IF EXISTS idx_timelines_confidence;
        DROP INDEX IF EXISTS idx_timelines_dates;
        DROP INDEX IF EXISTS idx_timelines_created;
        
        DROP INDEX IF EXISTS idx_periods_timeline;
        DROP INDEX IF EXISTS idx_periods_dates;
        DROP INDEX IF EXISTS idx_periods_sequence;
        
        DROP INDEX IF EXISTS idx_placements_period;
        DROP INDEX IF EXISTS idx_placements_document;
        DROP INDEX IF EXISTS idx_placements_date;
        DROP INDEX IF EXISTS idx_placements_commit;
    """)
    logger.info("  ✅ Indexes dropped")
    
    # Step 2: Drop document_placements table (has foreign keys to time_periods and documents)
    logger.info("  📝 Step 2/4: Dropping document_placements table...")
    dropped_placements = await connection.fetchval("""
        SELECT COUNT(*) FROM document_placements;
    """)
    await connection.execute("""
        DROP TABLE IF EXISTS document_placements CASCADE;
    """)
    logger.info(f"  ✅ Dropped document_placements table ({dropped_placements} records)")
    
    # Step 3: Drop time_periods table (has foreign keys to timelines)
    logger.info("  📝 Step 3/4: Dropping time_periods table...")
    dropped_periods = await connection.fetchval("""
        SELECT COUNT(*) FROM time_periods;
    """)
    await connection.execute("""
        DROP TABLE IF EXISTS time_periods CASCADE;
    """)
    logger.info(f"  ✅ Dropped time_periods table ({dropped_periods} records)")
    
    # Step 4: Drop timelines table
    logger.info("  📝 Step 4/4: Dropping timelines table...")
    dropped_timelines = await connection.fetchval("""
        SELECT COUNT(*) FROM timelines;
    """)
    await connection.execute("""
        DROP TABLE IF EXISTS timelines CASCADE;
    """)
    logger.info(f"  ✅ Dropped timelines table ({dropped_timelines} records)")
    
    logger.info("✅ Migration 009 downgrade complete!")


# Migration metadata
__migration__ = {
    "version": 9,
    "description": "Add timeline analysis tables for temporal document organization",
    "requires": [8],  # Depends on snapshot mode migration
    "breaking": False,  # Backward compatible (additive only)
}

