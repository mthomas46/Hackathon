"""Create DDD Schema Migration

Simple script to create the essential DDD database schema migration.
"""

import sqlite3
from datetime import datetime
from pathlib import Path


def create_ddd_schema():
    """Create the complete DDD database schema."""

    # Connect to database (create if doesn't exist)
    db_path = Path("../data/analysis_ddd.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    print("🏗️  Creating DDD Database Schema...")

    # ============================================================================
    # CORE DOMAIN TABLES
    # ============================================================================

    # Documents table with enhanced DDD structure
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content_text TEXT,
            content_format TEXT NOT NULL DEFAULT 'markdown',
            content_hash TEXT,
            author_id TEXT,
            author_name TEXT,
            author_email TEXT,
            repository_id TEXT,
            repository_name TEXT,
            repository_url TEXT,
            branch TEXT DEFAULT 'main',
            commit_hash TEXT,
            file_path TEXT,
            tags TEXT,  -- JSON array
            categories TEXT,  -- JSON array
            version TEXT NOT NULL DEFAULT '1.0.0',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_analyzed_at TEXT,
            analysis_count INTEGER DEFAULT 0,
            quality_score REAL,
            metadata TEXT,  -- JSON object with domain metadata
            domain_events TEXT,  -- JSON array of domain events
            CONSTRAINT chk_status CHECK (status IN ('active', 'archived', 'deleted')),
            CONSTRAINT chk_quality_score CHECK (quality_score >= 0.0 AND quality_score <= 1.0)
        )
    """)

    # Analyses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            analysis_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            priority INTEGER DEFAULT 1,
            configuration TEXT,  -- JSON configuration
            results TEXT,  -- JSON results
            error_message TEXT,
            started_at TEXT,
            completed_at TEXT,
            duration_seconds REAL,
            worker_id TEXT,
            correlation_id TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT,  -- JSON metadata
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            CONSTRAINT chk_analysis_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
            CONSTRAINT chk_analysis_priority CHECK (priority >= 1 AND priority <= 10)
        )
    """)

    # Findings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id TEXT PRIMARY KEY,
            analysis_id TEXT NOT NULL,
            document_id TEXT NOT NULL,
            finding_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            location TEXT,  -- JSON location info
            evidence TEXT,  -- JSON evidence data
            recommendation TEXT,
            confidence REAL,
            tags TEXT,  -- JSON tags
            status TEXT NOT NULL DEFAULT 'open',
            assigned_to TEXT,
            resolved_at TEXT,
            resolved_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT,  -- JSON metadata
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            CONSTRAINT chk_finding_severity CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
            CONSTRAINT chk_finding_status CHECK (status IN ('open', 'in_progress', 'resolved', 'dismissed')),
            CONSTRAINT chk_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)
        )
    """)

    # ============================================================================
    # ANALYSIS-SPECIFIC TABLES
    # ============================================================================

    # Semantic analysis results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS semantic_analysis_results (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            analysis_id TEXT NOT NULL,
            embedding_model TEXT NOT NULL,
            embedding_dimensions INTEGER,
            similarity_threshold REAL DEFAULT 0.7,
            similar_documents TEXT,  -- JSON array of similar docs
            semantic_clusters TEXT,  -- JSON clustering results
            key_phrases TEXT,  -- JSON extracted phrases
            semantic_score REAL,
            created_at TEXT NOT NULL,
            metadata TEXT,  -- JSON metadata
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        )
    """)

    # Sentiment analysis results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_analysis_results (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            analysis_id TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            confidence REAL,
            polarity REAL,
            subjectivity REAL,
            emotion_scores TEXT,  -- JSON emotion scores
            tone_analysis TEXT,  -- JSON tone analysis
            readability_score REAL,
            clarity_score REAL,
            created_at TEXT NOT NULL,
            metadata TEXT,  -- JSON metadata
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE,
            CONSTRAINT chk_sentiment CHECK (sentiment IN ('positive', 'negative', 'neutral')),
            CONSTRAINT chk_sentiment_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)
        )
    """)

    # Quality metrics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_metrics (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            analysis_id TEXT NOT NULL,
            readability_score REAL,
            completeness_score REAL,
            consistency_score REAL,
            technical_accuracy_score REAL,
            overall_quality_score REAL,
            quality_trend TEXT,  -- JSON trend data
            improvement_suggestions TEXT,  -- JSON suggestions
            quality_indicators TEXT,  -- JSON indicators
            created_at TEXT NOT NULL,
            metadata TEXT,  -- JSON metadata
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
        )
    """)

    # Risk assessments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_assessments (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            analysis_id TEXT NOT NULL,
            overall_risk_score REAL,
            risk_level TEXT NOT NULL,
            risk_factors TEXT,  -- JSON risk factors
            risk_drivers TEXT,  -- JSON top risk drivers
            mitigation_recommendations TEXT,  -- JSON recommendations
            risk_trend TEXT,  -- JSON risk trend
            assessment_date TEXT NOT NULL,
            next_assessment_date TEXT,
            created_at TEXT NOT NULL,
            metadata TEXT,  -- JSON metadata
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE,
            CONSTRAINT chk_risk_level CHECK (risk_level IN ('minimal', 'low', 'medium', 'high', 'critical'))
        )
    """)

    # ============================================================================
    # REPOSITORY MANAGEMENT TABLES
    # ============================================================================

    # Repositories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            repository_type TEXT NOT NULL DEFAULT 'github',
            description TEXT,
            owner TEXT,
            is_private BOOLEAN DEFAULT FALSE,
            default_branch TEXT DEFAULT 'main',
            language TEXT,
            topics TEXT,  -- JSON array
            stars INTEGER DEFAULT 0,
            forks INTEGER DEFAULT 0,
            last_commit_hash TEXT,
            last_synced_at TEXT,
            sync_status TEXT DEFAULT 'never',
            webhook_url TEXT,
            webhook_secret TEXT,
            access_token TEXT,  -- Encrypted
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata TEXT,  -- JSON metadata
            UNIQUE(url),
            CONSTRAINT chk_repo_type CHECK (repository_type IN ('github', 'gitlab', 'bitbucket', 'local')),
            CONSTRAINT chk_sync_status CHECK (sync_status IN ('never', 'pending', 'running', 'completed', 'failed'))
        )
    """)

    # ============================================================================
    # DISTRIBUTED PROCESSING TABLES
    # ============================================================================

    # Workers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id TEXT PRIMARY KEY,
            hostname TEXT NOT NULL,
            pid INTEGER,
            capabilities TEXT,  -- JSON array of capabilities
            max_concurrent_tasks INTEGER DEFAULT 5,
            current_tasks INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'idle',
            last_heartbeat TEXT,
            registered_at TEXT NOT NULL,
            last_seen_at TEXT,
            cpu_percent REAL,
            memory_percent REAL,
            tasks_completed INTEGER DEFAULT 0,
            tasks_failed INTEGER DEFAULT 0,
            average_task_time REAL,
            metadata TEXT,  -- JSON metadata
            CONSTRAINT chk_worker_status CHECK (status IN ('idle', 'busy', 'offline', 'error'))
        )
    """)

    # Distributed tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS distributed_tasks (
            id TEXT PRIMARY KEY,
            task_type TEXT NOT NULL,
            payload TEXT NOT NULL,  -- JSON payload
            priority INTEGER DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'pending',
            assigned_worker_id TEXT,
            assigned_at TEXT,
            started_at TEXT,
            completed_at TEXT,
            failed_at TEXT,
            duration_seconds REAL,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            error_message TEXT,
            result TEXT,  -- JSON result
            correlation_id TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            timeout_seconds INTEGER DEFAULT 300,
            metadata TEXT,  -- JSON metadata
            FOREIGN KEY (assigned_worker_id) REFERENCES workers(id),
            CONSTRAINT chk_task_status CHECK (status IN ('pending', 'assigned', 'running', 'completed', 'failed', 'cancelled')),
            CONSTRAINT chk_task_priority CHECK (priority >= 1 AND priority <= 10)
        )
    """)

    # ============================================================================
    # PERFORMANCE INDEXES
    # ============================================================================

    print("🔧 Creating performance indexes...")

    # Documents indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_author ON documents(author_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_repository ON documents(repository_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_updated ON documents(updated_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_quality ON documents(quality_score)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at)")

    # Analyses indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_document ON analyses(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_type ON analyses(analysis_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_worker ON analyses(worker_id)")

    # Findings indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_analysis ON findings(analysis_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_document ON findings(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_type ON findings(finding_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_created ON findings(created_at)")

    # Distributed tasks indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_distributed_tasks_status ON distributed_tasks(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_distributed_tasks_type ON distributed_tasks(task_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_distributed_tasks_worker ON distributed_tasks(assigned_worker_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_distributed_tasks_priority ON distributed_tasks(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_distributed_tasks_created ON distributed_tasks(created_at)")

    # ============================================================================
    # SCHEMA MIGRATION TRACKING
    # ============================================================================

    # Create schema migrations table to track migrations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_id TEXT PRIMARY KEY,
            migration_name TEXT NOT NULL,
            executed_at TEXT NOT NULL,
            execution_time_seconds REAL,
            status TEXT NOT NULL,
            checksum TEXT,
            metadata TEXT  -- JSON metadata
        )
    """)

    # Record this migration
    migration_id = "001_create_ddd_core_schema"
    cursor.execute("""
        INSERT OR REPLACE INTO schema_migrations
        (migration_id, migration_name, executed_at, execution_time_seconds, status, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        migration_id,
        "Create DDD Core Schema",
        datetime.now().isoformat(),
        0.0,
        "completed",
        '{"description": "Complete DDD schema with all domain tables and indexes"}'
    ))

    conn.commit()
    conn.close()

    print("✅ DDD schema created successfully!")
    print(f"📁 Database created at: {db_path}")
    print("\n📊 Schema includes:")
    print("   • 8 core domain tables")
    print("   • 4 analysis-specific tables")
    print("   • Repository management tables")
    print("   • Distributed processing tables")
    print("   • 20+ performance indexes")
    print("   • Schema migration tracking")


def main():
    """Main function."""
    print("🏗️  DDD Schema Migration Creator")
    print("=" * 50)
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    create_ddd_schema()

    print("\n🚀 Migration completed successfully!")
    print("🎯 The DDD database schema is now ready for the new architecture!")


if __name__ == "__main__":
    main()
