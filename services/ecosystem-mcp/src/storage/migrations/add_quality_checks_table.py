"""
Database Migration: Add Quality Checks Tables

Creates tables for storing quality validation results, confidence scores,
and review workflow data.
"""

from sqlalchemy import text


def upgrade(conn):
    """Create quality checks tables."""
    
    # Create quality_checks table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS quality_checks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id UUID REFERENCES documentation_runs(id) ON DELETE CASCADE,
            artifact_id UUID REFERENCES documentation_artifacts(id) ON DELETE CASCADE,
            
            -- Completeness scores
            completeness_score FLOAT NOT NULL,
            missing_sections JSONB DEFAULT '[]',
            incomplete_sections JSONB DEFAULT '[]',
            placeholder_count INTEGER DEFAULT 0,
            broken_links JSONB DEFAULT '[]',
            formatting_issues JSONB DEFAULT '[]',
            section_word_counts JSONB DEFAULT '{}',
            has_code_examples BOOLEAN DEFAULT FALSE,
            
            -- Accuracy scores
            accuracy_score FLOAT NOT NULL,
            code_example_issues JSONB DEFAULT '[]',
            api_mismatches JSONB DEFAULT '[]',
            type_errors JSONB DEFAULT '[]',
            factual_errors JSONB DEFAULT '[]',
            accuracy_warnings JSONB DEFAULT '[]',
            validated_examples INTEGER DEFAULT 0,
            total_examples INTEGER DEFAULT 0,
            
            -- Confidence scores
            overall_confidence FLOAT NOT NULL,
            completeness_confidence FLOAT NOT NULL,
            accuracy_confidence FLOAT NOT NULL,
            source_quality_confidence FLOAT NOT NULL,
            confidence_breakdown JSONB DEFAULT '{}',
            
            -- Review workflow
            requires_review BOOLEAN DEFAULT FALSE,
            review_priority VARCHAR(20),  -- critical, high, medium, low
            review_status VARCHAR(20),    -- pending, in_review, approved, rejected, needs_revision
            assigned_to VARCHAR(200),
            reviewed_at TIMESTAMP,
            reviewer_notes TEXT,
            
            -- Recommendations
            recommendations JSONB DEFAULT '[]',
            
            -- Metadata
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """))
    
    # Create indexes for performance
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_quality_checks_run_id 
        ON quality_checks(run_id);
    """))
    
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_quality_checks_artifact_id 
        ON quality_checks(artifact_id);
    """))
    
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_quality_checks_review_status 
        ON quality_checks(requires_review, review_status);
    """))
    
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_quality_checks_confidence 
        ON quality_checks(overall_confidence);
    """))
    
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_quality_checks_priority 
        ON quality_checks(review_priority);
    """))
    
    # Create quality_reports table for aggregated reports
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS quality_reports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id UUID REFERENCES documentation_runs(id) ON DELETE CASCADE,
            
            -- Summary metrics
            total_artifacts INTEGER NOT NULL,
            average_completeness FLOAT NOT NULL,
            average_accuracy FLOAT NOT NULL,
            average_confidence FLOAT NOT NULL,
            
            -- Detailed breakdowns
            completeness_breakdown JSONB DEFAULT '{}',
            accuracy_breakdown JSONB DEFAULT '{}',
            confidence_breakdown JSONB DEFAULT '{}',
            
            -- Issue summary
            total_issues INTEGER DEFAULT 0,
            critical_issues INTEGER DEFAULT 0,
            issues_by_type JSONB DEFAULT '{}',
            
            -- Review requirements
            artifacts_requiring_review INTEGER DEFAULT 0,
            review_priority_breakdown JSONB DEFAULT '{}',
            
            -- Recommendations
            top_recommendations JSONB DEFAULT '[]',
            
            -- Trends
            quality_trend VARCHAR(20),  -- improving, declining, stable
            
            -- Metadata
            generated_at TIMESTAMP DEFAULT NOW()
        );
    """))
    
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_quality_reports_run_id 
        ON quality_reports(run_id);
    """))
    
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_quality_reports_generated_at 
        ON quality_reports(generated_at);
    """))
    
    print("✅ Created quality_checks and quality_reports tables")
    print("✅ Created 7 indexes for performance")


def downgrade(conn):
    """Drop quality checks tables."""
    
    # Drop indexes
    conn.execute(text("DROP INDEX IF EXISTS idx_quality_reports_generated_at;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_quality_reports_run_id;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_quality_checks_priority;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_quality_checks_confidence;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_quality_checks_review_status;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_quality_checks_artifact_id;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_quality_checks_run_id;"))
    
    # Drop tables
    conn.execute(text("DROP TABLE IF EXISTS quality_reports;"))
    conn.execute(text("DROP TABLE IF EXISTS quality_checks;"))
    
    print("✅ Dropped quality_checks and quality_reports tables")

