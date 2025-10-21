"""
Database migration: Add analysis tables for Phase 3

Creates tables for:
- repository_contexts (repository-level analysis metadata)
- detected_services (microservices/service boundaries)
- analysis_results (complete analysis reports)
"""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def upgrade(session: AsyncSession) -> None:
    """
    Create analysis tables.
    
    Tables:
    - repository_contexts: Repository-level context metadata
    - detected_services: Detected microservices/services
    - analysis_results: Complete analysis reports
    """
    logger.info("Creating analysis tables...")
    
    # 1. Repository Contexts Table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS repository_contexts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            repo_id VARCHAR(500) UNIQUE NOT NULL,
            repo_name VARCHAR(500),
            
            -- Technology Stack
            languages JSONB,
            frameworks JSONB,
            databases JSONB,
            tools JSONB,
            deployment_platforms JSONB,
            
            -- Architecture
            architecture_type VARCHAR(50),
            architecture_confidence FLOAT,
            service_count INTEGER DEFAULT 1,
            component_count INTEGER,
            layers JSONB,
            
            -- API Summary
            endpoint_count INTEGER DEFAULT 0,
            endpoints JSONB,
            has_rest_api BOOLEAN DEFAULT FALSE,
            has_graphql BOOLEAN DEFAULT FALSE,
            has_websocket BOOLEAN DEFAULT FALSE,
            
            -- Code Metrics
            total_files INTEGER,
            total_lines INTEGER,
            code_files INTEGER,
            test_files INTEGER,
            doc_files INTEGER,
            modularity_score FLOAT,
            
            -- Entry Points
            entry_points JSONB,
            main_flows JSONB,
            
            -- AI Summary
            brief_description TEXT,
            key_features JSONB,
            technical_highlights JSONB,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """))
    logger.info("  ✅ Created repository_contexts table")
    
    # 2. Detected Services Table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS detected_services (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            repo_id VARCHAR(500) NOT NULL,
            service_name VARCHAR(200) NOT NULL,
            root_path VARCHAR(500),
            
            -- Service Details
            file_count INTEGER,
            entry_point VARCHAR(500),
            internal_dependencies JSONB,
            external_dependencies JSONB,
            
            -- Technology
            languages JSONB,
            frameworks JSONB,
            databases JSONB,
            
            -- API
            has_api BOOLEAN DEFAULT FALSE,
            endpoints JSONB,
            
            -- Deployment
            has_dockerfile BOOLEAN DEFAULT FALSE,
            has_k8s_config BOOLEAN DEFAULT FALSE,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Foreign key
            FOREIGN KEY (repo_id) REFERENCES repository_contexts(repo_id) ON DELETE CASCADE
        )
    """))
    logger.info("  ✅ Created detected_services table")
    
    # 3. Analysis Results Table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plan_id VARCHAR(500) NOT NULL,
            repo_id VARCHAR(500) NOT NULL,
            repo_path TEXT,
            
            -- Analysis Status
            analysis_complete BOOLEAN DEFAULT FALSE,
            errors JSONB,
            
            -- Dependency Analysis
            has_dependency_graph BOOLEAN DEFAULT FALSE,
            total_nodes INTEGER,
            total_edges INTEGER,
            circular_dependencies JSONB,
            topological_order JSONB,
            
            -- Technology Stack
            primary_language VARCHAR(100),
            total_languages INTEGER,
            total_frameworks INTEGER,
            total_databases INTEGER,
            
            -- Architecture
            primary_architecture VARCHAR(50),
            architecture_confidence FLOAT,
            secondary_architectures JSONB,
            detected_layers JSONB,
            
            -- Services
            total_services INTEGER DEFAULT 1,
            is_microservices BOOLEAN DEFAULT FALSE,
            service_dependencies JSONB,
            
            -- Summary Metrics
            total_files INTEGER,
            modularity_score FLOAT,
            
            -- Full Report (JSONB for flexibility)
            dependency_graph JSONB,
            technology_stack JSONB,
            architecture_analysis JSONB,
            service_map JSONB,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Foreign keys
            FOREIGN KEY (repo_id) REFERENCES repository_contexts(repo_id) ON DELETE CASCADE
        )
    """))
    logger.info("  ✅ Created analysis_results table")
    
    # Create indexes for performance
    indexes = [
        # Repository Contexts
        "CREATE INDEX IF NOT EXISTS idx_repo_contexts_repo_id ON repository_contexts(repo_id)",
        "CREATE INDEX IF NOT EXISTS idx_repo_contexts_architecture ON repository_contexts(architecture_type)",
        "CREATE INDEX IF NOT EXISTS idx_repo_contexts_created ON repository_contexts(created_at DESC)",
        
        # Detected Services
        "CREATE INDEX IF NOT EXISTS idx_detected_services_repo ON detected_services(repo_id)",
        "CREATE INDEX IF NOT EXISTS idx_detected_services_name ON detected_services(service_name)",
        "CREATE INDEX IF NOT EXISTS idx_detected_services_has_api ON detected_services(has_api) WHERE has_api = TRUE",
        
        # Analysis Results
        "CREATE INDEX IF NOT EXISTS idx_analysis_results_plan ON analysis_results(plan_id)",
        "CREATE INDEX IF NOT EXISTS idx_analysis_results_repo ON analysis_results(repo_id)",
        "CREATE INDEX IF NOT EXISTS idx_analysis_results_complete ON analysis_results(analysis_complete)",
        "CREATE INDEX IF NOT EXISTS idx_analysis_results_created ON analysis_results(created_at DESC)",
    ]
    
    for index_sql in indexes:
        await session.execute(text(index_sql))
    
    logger.info("  ✅ Created performance indexes")
    
    await session.commit()
    logger.info("✅ Analysis tables migration complete")


async def downgrade(session: AsyncSession) -> None:
    """Drop analysis tables."""
    logger.info("Dropping analysis tables...")
    
    # Drop tables in reverse order (respecting foreign keys)
    await session.execute(text("DROP TABLE IF EXISTS analysis_results CASCADE"))
    logger.info("  ✅ Dropped analysis_results table")
    
    await session.execute(text("DROP TABLE IF EXISTS detected_services CASCADE"))
    logger.info("  ✅ Dropped detected_services table")
    
    await session.execute(text("DROP TABLE IF EXISTS repository_contexts CASCADE"))
    logger.info("  ✅ Dropped repository_contexts table")
    
    await session.commit()
    logger.info("✅ Analysis tables rollback complete")

