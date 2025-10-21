"""
Database migration: Add documentation tables for Phase 4

Creates tables for:
- documentation_runs (documentation generation runs)
- documentation_artifacts (generated documentation pieces)
"""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def upgrade(session: AsyncSession) -> None:
    """
    Create documentation tables.
    
    Tables:
    - documentation_runs: Track documentation generation runs
    - documentation_artifacts: Store generated documentation
    """
    logger.info("Creating documentation tables...")
    
    # 1. Documentation Runs Table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS documentation_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plan_id VARCHAR(500),
            repo_id VARCHAR(500),
            
            -- Run configuration
            passes_completed INTEGER DEFAULT 0,
            total_passes INTEGER DEFAULT 5,
            current_pass VARCHAR(50),
            config JSONB,
            
            -- Status
            status VARCHAR(20) NOT NULL,
            started_at TIMESTAMP NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMP,
            
            -- Metrics
            total_artifacts INTEGER DEFAULT 0,
            total_words INTEGER DEFAULT 0,
            overall_quality_score FLOAT,
            
            -- Output
            output_path TEXT,
            output_formats JSONB,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Foreign keys
            FOREIGN KEY (repo_id) REFERENCES repository_contexts(repo_id) ON DELETE CASCADE
        )
    """))
    logger.info("  ✅ Created documentation_runs table")
    
    # 2. Documentation Artifacts Table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS documentation_artifacts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id UUID NOT NULL,
            
            -- Artifact info
            artifact_type VARCHAR(50) NOT NULL,
            pass_number INTEGER NOT NULL,
            pass_type VARCHAR(50) NOT NULL,
            component_name VARCHAR(200),
            
            -- Content
            title VARCHAR(500),
            content TEXT,
            format VARCHAR(20) DEFAULT 'markdown',
            
            -- Metadata
            word_count INTEGER DEFAULT 0,
            quality_score FLOAT,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT NOW(),
            
            -- Foreign key
            FOREIGN KEY (run_id) REFERENCES documentation_runs(id) ON DELETE CASCADE
        )
    """))
    logger.info("  ✅ Created documentation_artifacts table")
    
    # Create indexes for performance
    indexes = [
        # Documentation Runs
        "CREATE INDEX IF NOT EXISTS idx_doc_runs_plan ON documentation_runs(plan_id)",
        "CREATE INDEX IF NOT EXISTS idx_doc_runs_repo ON documentation_runs(repo_id)",
        "CREATE INDEX IF NOT EXISTS idx_doc_runs_status ON documentation_runs(status)",
        "CREATE INDEX IF NOT EXISTS idx_doc_runs_created ON documentation_runs(created_at DESC)",
        
        # Documentation Artifacts
        "CREATE INDEX IF NOT EXISTS idx_doc_artifacts_run ON documentation_artifacts(run_id)",
        "CREATE INDEX IF NOT EXISTS idx_doc_artifacts_type ON documentation_artifacts(artifact_type)",
        "CREATE INDEX IF NOT EXISTS idx_doc_artifacts_pass ON documentation_artifacts(pass_type)",
        "CREATE INDEX IF NOT EXISTS idx_doc_artifacts_component ON documentation_artifacts(component_name)",
    ]
    
    for index_sql in indexes:
        await session.execute(text(index_sql))
    
    logger.info("  ✅ Created performance indexes")
    
    await session.commit()
    logger.info("✅ Documentation tables migration complete")


async def downgrade(session: AsyncSession) -> None:
    """Drop documentation tables."""
    logger.info("Dropping documentation tables...")
    
    # Drop tables in reverse order (respecting foreign keys)
    await session.execute(text("DROP TABLE IF EXISTS documentation_artifacts CASCADE"))
    logger.info("  ✅ Dropped documentation_artifacts table")
    
    await session.execute(text("DROP TABLE IF EXISTS documentation_runs CASCADE"))
    logger.info("  ✅ Dropped documentation_runs table")
    
    await session.commit()
    logger.info("✅ Documentation tables rollback complete")

