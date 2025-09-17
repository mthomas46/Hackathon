"""DDD Schema Migration Script

Creates comprehensive database schema migrations for the new Domain-Driven Design
architecture, including all entities, relationships, and performance optimizations.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add the service directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "analysis-service"))

from infrastructure.migrations.migration_templates import MigrationTemplateGenerator
from infrastructure.migrations.sqlite_migration_manager import SQLiteMigrationManager


class DDDSchemaMigrationGenerator:
    """Generates comprehensive DDD schema migrations."""

    def __init__(self, output_dir: str = "migrations/ddd_schema"):
        """Initialize migration generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template_generator = MigrationTemplateGenerator()

    def generate_all_migrations(self) -> List[str]:
        """Generate all DDD schema migrations."""
        migrations_created = []

        print("🚀 Generating DDD Schema Migrations")
        print("=" * 50)

        # Migration 1: Create core domain tables
        migrations_created.append(self._create_core_domain_tables_migration())

        # Migration 2: Create analysis and findings tables
        migrations_created.append(self._create_analysis_tables_migration())

        # Migration 3: Create repository management tables
        migrations_created.append(self._create_repository_tables_migration())

        # Migration 4: Create distributed processing tables
        migrations_created.append(self._create_distributed_processing_tables_migration())

        # Migration 5: Create workflow and event tables
        migrations_created.append(self._create_workflow_event_tables_migration())

        # Migration 6: Create audit and metadata tables
        migrations_created.append(self._create_audit_metadata_tables_migration())

        # Migration 7: Create performance optimization indexes
        migrations_created.append(self._create_performance_indexes_migration())

        # Migration 8: Create data migration triggers
        migrations_created.append(self._create_data_migration_triggers_migration())

        print(f"\n✅ Generated {len(migrations_created)} migration files:")
        for migration in migrations_created:
            print(f"   📄 {migration}")

        return migrations_created

    def _create_core_domain_tables_migration(self) -> str:
        """Create migration for core domain tables (Document, Analysis, Finding)."""

        migration_id = "001_create_core_domain_tables"
        name = "Create Core Domain Tables"

        migration_code = f'''"""Migration: {migration_id} - {name}"""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from infrastructure.migrations.migration import Migration, MigrationResult, MigrationStatus


class Migration001CreateCoreDomainTables(Migration):
    """Create core domain tables for DDD architecture."""

    @property
    def migration_id(self) -> str:
        return "{migration_id}"

    @property
    def name(self) -> str:
        return "{name}"

    @property
    def description(self) -> str:
        return "Create core domain tables: documents, analyses, findings"

    @property
    def dependencies(self) -> List[str]:
        return []

    def up(self, context: Any) -> MigrationResult:
        """Execute migration up."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Create documents table with enhanced DDD structure
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

            # Create analyses table
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

            # Create findings table
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

            # Create document versions table for audit trail
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_versions (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    content_snapshot TEXT,  -- JSON snapshot
                    changes_summary TEXT,
                    changed_by TEXT,
                    changed_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    UNIQUE(document_id, version)
                )
            """)

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Core domain tables created successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to create core domain tables: {{str(e)}}",
                execution_time=0.0
            )

    def down(self, context: Any) -> MigrationResult:
        """Execute migration down."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Drop tables in reverse order
            cursor.execute("DROP TABLE IF EXISTS document_versions")
            cursor.execute("DROP TABLE IF EXISTS findings")
            cursor.execute("DROP TABLE IF EXISTS analyses")
            cursor.execute("DROP TABLE IF EXISTS documents")

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Core domain tables dropped successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to drop core domain tables: {{str(e)}}",
                execution_time=0.0
            )'''

        # Write migration file
        output_path = self.output_dir / f"{migration_id}.py"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_code)

        return str(output_path)

    def _create_analysis_tables_migration(self) -> str:
        """Create migration for analysis-specific tables."""

        migration_id = "002_create_analysis_tables"
        name = "Create Analysis Tables"

        migration_code = f'''"""Migration: {migration_id} - {name}"""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from infrastructure.migrations.migration import Migration, MigrationResult, MigrationStatus


class Migration002CreateAnalysisTables(Migration):
    """Create analysis-specific tables for advanced analysis features."""

    @property
    def migration_id(self) -> str:
        return "{migration_id}"

    @property
    def name(self) -> str:
        return "{name}"

    @property
    def description(self) -> str:
        return "Create tables for semantic analysis, sentiment analysis, and quality metrics"

    @property
    def dependencies(self) -> List[str]:
        return ["001_create_core_domain_tables"]

    def up(self, context: Any) -> MigrationResult:
        """Execute migration up."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Create semantic analysis results table
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

            # Create sentiment analysis results table
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

            # Create quality metrics table
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

            # Create risk assessments table
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

            # Create maintenance forecasts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_forecasts (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    analysis_id TEXT NOT NULL,
                    predicted_maintenance_date TEXT,
                    maintenance_priority TEXT NOT NULL,
                    maintenance_type TEXT,
                    forecast_accuracy REAL,
                    forecast_factors TEXT,  -- JSON forecast factors
                    maintenance_schedule TEXT,  -- JSON schedule
                    created_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE,
                    CONSTRAINT chk_maintenance_priority CHECK (maintenance_priority IN ('minimal', 'low', 'medium', 'high', 'critical'))
                )
            """)

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Analysis tables created successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to create analysis tables: {{str(e)}}",
                execution_time=0.0
            )

    def down(self, context: Any) -> MigrationResult:
        """Execute migration down."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Drop tables in reverse order
            cursor.execute("DROP TABLE IF EXISTS maintenance_forecasts")
            cursor.execute("DROP TABLE IF EXISTS risk_assessments")
            cursor.execute("DROP TABLE IF EXISTS quality_metrics")
            cursor.execute("DROP TABLE IF EXISTS sentiment_analysis_results")
            cursor.execute("DROP TABLE IF EXISTS semantic_analysis_results")

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Analysis tables dropped successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to drop analysis tables: {{str(e)}}",
                execution_time=0.0
            )'''

        # Write migration file
        output_path = self.output_dir / f"{migration_id}.py"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_code)

        return str(output_path)

    def _create_repository_tables_migration(self) -> str:
        """Create migration for repository management tables."""

        migration_id = "003_create_repository_tables"
        name = "Create Repository Tables"

        migration_code = f'''"""Migration: {migration_id} - {name}"""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from infrastructure.migrations.migration import Migration, MigrationResult, MigrationStatus


class Migration003CreateRepositoryTables(Migration):
    """Create repository management tables for cross-repository analysis."""

    @property
    def migration_id(self) -> str:
        return "{migration_id}"

    @property
    def name(self) -> str:
        return "{name}"

    @property
    def description(self) -> str:
        return "Create tables for repository management and cross-repository analysis"

    @property
    def dependencies(self) -> List[str]:
        return ["001_create_core_domain_tables"]

    def up(self, context: Any) -> MigrationResult:
        """Execute migration up."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Create repositories table
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

            # Create repository sync logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repository_sync_logs (
                    id TEXT PRIMARY KEY,
                    repository_id TEXT NOT NULL,
                    sync_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_seconds REAL,
                    files_processed INTEGER DEFAULT 0,
                    documents_created INTEGER DEFAULT 0,
                    documents_updated INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    error_details TEXT,  -- JSON error details
                    created_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE,
                    CONSTRAINT chk_sync_log_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
                )
            """)

            # Create repository connectivity tests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repository_connectivity_tests (
                    id TEXT PRIMARY KEY,
                    repository_id TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_time_ms REAL,
                    error_message TEXT,
                    tested_at TEXT NOT NULL,
                    next_test_at TEXT,
                    metadata TEXT,  -- JSON metadata
                    FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE,
                    CONSTRAINT chk_connectivity_status CHECK (status IN ('success', 'failed', 'timeout', 'auth_error'))
                )
            """)

            # Create cross-repository analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cross_repository_analysis (
                    id TEXT PRIMARY KEY,
                    analysis_name TEXT NOT NULL,
                    repository_ids TEXT NOT NULL,  -- JSON array
                    analysis_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    consistency_score REAL,
                    duplicate_documents TEXT,  -- JSON duplicates found
                    missing_documentation TEXT,  -- JSON missing docs
                    standardization_issues TEXT,  -- JSON issues
                    recommendations TEXT,  -- JSON recommendations
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    CONSTRAINT chk_cross_repo_status CHECK (status IN ('pending', 'running', 'completed', 'failed'))
                )
            """)

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Repository tables created successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to create repository tables: {{str(e)}}",
                execution_time=0.0
            )

    def down(self, context: Any) -> MigrationResult:
        """Execute migration down."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Drop tables in reverse order
            cursor.execute("DROP TABLE IF EXISTS cross_repository_analysis")
            cursor.execute("DROP TABLE IF EXISTS repository_connectivity_tests")
            cursor.execute("DROP TABLE IF EXISTS repository_sync_logs")
            cursor.execute("DROP TABLE IF EXISTS repositories")

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Repository tables dropped successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to drop repository tables: {{str(e)}}",
                execution_time=0.0
            )'''

        # Write migration file
        output_path = self.output_dir / f"{migration_id}.py"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_code)

        return str(output_path)

    def _create_distributed_processing_tables_migration(self) -> str:
        """Create migration for distributed processing tables."""

        migration_id = "004_create_distributed_processing_tables"
        name = "Create Distributed Processing Tables"

        migration_code = f'''"""Migration: {migration_id} - {name}"""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from infrastructure.migrations.migration import Migration, MigrationResult, MigrationStatus


class Migration004CreateDistributedProcessingTables(Migration):
    """Create tables for distributed processing and task management."""

    @property
    def migration_id(self) -> str:
        return "{migration_id}"

    @property
    def name(self) -> str:
        return "{name}"

    @property
    def description(self) -> str:
        return "Create tables for distributed task processing and worker management"

    @property
    def dependencies(self) -> List[str]:
        return ["001_create_core_domain_tables"]

    def up(self, context: Any) -> MigrationResult:
        """Execute migration up."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Create workers table
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

            # Create distributed tasks table
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

            # Create task queues table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_queues (
                    id TEXT PRIMARY KEY,
                    queue_name TEXT NOT NULL,
                    task_count INTEGER DEFAULT 0,
                    processing_rate REAL,  -- tasks per second
                    average_wait_time REAL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    UNIQUE(queue_name)
                )
            """)

            # Create worker performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS worker_performance_metrics (
                    id TEXT PRIMARY KEY,
                    worker_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL,
                    recorded_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE
                )
            """)

            # Create task dependencies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    depends_on_task_id TEXT NOT NULL,
                    dependency_type TEXT DEFAULT 'completion',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES distributed_tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY (depends_on_task_id) REFERENCES distributed_tasks(id) ON DELETE CASCADE,
                    UNIQUE(task_id, depends_on_task_id)
                )
            """)

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Distributed processing tables created successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to create distributed processing tables: {{str(e)}}",
                execution_time=0.0
            )

    def down(self, context: Any) -> MigrationResult:
        """Execute migration down."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Drop tables in reverse order
            cursor.execute("DROP TABLE IF EXISTS task_dependencies")
            cursor.execute("DROP TABLE IF EXISTS worker_performance_metrics")
            cursor.execute("DROP TABLE IF EXISTS task_queues")
            cursor.execute("DROP TABLE IF EXISTS distributed_tasks")
            cursor.execute("DROP TABLE IF EXISTS workers")

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Distributed processing tables dropped successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to drop distributed processing tables: {{str(e)}}",
                execution_time=0.0
            )'''

        # Write migration file
        output_path = self.output_dir / f"{migration_id}.py"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_code)

        return str(output_path)

    def _create_workflow_event_tables_migration(self) -> str:
        """Create migration for workflow and event tables."""

        migration_id = "005_create_workflow_event_tables"
        name = "Create Workflow Event Tables"

        migration_code = f'''"""Migration: {migration_id} - {name}"""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from infrastructure.migrations.migration import Migration, MigrationResult, MigrationStatus


class Migration005CreateWorkflowEventTables(Migration):
    """Create tables for workflow management and event processing."""

    @property
    def migration_id(self) -> str:
        return "{migration_id}"

    @property
    def name(self) -> str:
        return "{name}"

    @property
    def description(self) -> str:
        return "Create tables for workflow management and event-driven processing"

    @property
    def dependencies(self) -> List[str]:
        return ["001_create_core_domain_tables"]

    def up(self, context: Any) -> MigrationResult:
        """Execute migration up."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Create workflows table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    workflow_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    trigger_conditions TEXT,  -- JSON trigger conditions
                    steps TEXT NOT NULL,  -- JSON workflow steps
                    created_by TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_executed_at TEXT,
                    execution_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 1.0,
                    metadata TEXT,  -- JSON metadata
                    CONSTRAINT chk_workflow_status CHECK (status IN ('active', 'inactive', 'deprecated')),
                    CONSTRAINT chk_workflow_type CHECK (workflow_type IN ('pr_analysis', 'commit_analysis', 'scheduled', 'manual'))
                )
            """)

            # Create workflow executions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    trigger_event TEXT,  -- JSON trigger event
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_seconds REAL,
                    steps_completed INTEGER DEFAULT 0,
                    steps_failed INTEGER DEFAULT 0,
                    error_message TEXT,
                    results TEXT,  -- JSON execution results
                    created_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
                    UNIQUE(workflow_id, execution_id),
                    CONSTRAINT chk_execution_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
                )
            """)

            # Create events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    event_source TEXT NOT NULL,
                    event_data TEXT NOT NULL,  -- JSON event data
                    correlation_id TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    processed_at TEXT,
                    processing_attempts INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    metadata TEXT  -- JSON metadata
                )
            """)

            # Create webhooks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS webhooks (
                    id TEXT PRIMARY KEY,
                    repository_id TEXT,
                    webhook_url TEXT NOT NULL,
                    webhook_secret TEXT,
                    events TEXT NOT NULL,  -- JSON array of events
                    is_active BOOLEAN DEFAULT TRUE,
                    last_delivery_at TEXT,
                    delivery_attempts INTEGER DEFAULT 0,
                    delivery_failures INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE
                )
            """)

            # Create webhook deliveries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS webhook_deliveries (
                    id TEXT PRIMARY KEY,
                    webhook_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,  -- JSON payload
                    response_status INTEGER,
                    response_body TEXT,
                    delivered_at TEXT,
                    processing_time_ms REAL,
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE
                )
            """)

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Workflow and event tables created successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to create workflow and event tables: {{str(e)}}",
                execution_time=0.0
            )

    def down(self, context: Any) -> MigrationResult:
        """Execute migration down."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Drop tables in reverse order
            cursor.execute("DROP TABLE IF EXISTS webhook_deliveries")
            cursor.execute("DROP TABLE IF EXISTS webhooks")
            cursor.execute("DROP TABLE IF EXISTS events")
            cursor.execute("DROP TABLE IF EXISTS workflow_executions")
            cursor.execute("DROP TABLE IF EXISTS workflows")

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Workflow and event tables dropped successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to drop workflow and event tables: {{str(e)}}",
                execution_time=0.0
            )'''

        # Write migration file
        output_path = self.output_dir / f"{migration_id}.py"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_code)

        return str(output_path)

    def _create_audit_metadata_tables_migration(self) -> str:
        """Create migration for audit and metadata tables."""

        migration_id = "006_create_audit_metadata_tables"
        name = "Create Audit Metadata Tables"

        migration_code = f'''"""Migration: {migration_id} - {name}"""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from infrastructure.migrations.migration import Migration, MigrationResult, MigrationStatus


class Migration006CreateAuditMetadataTables(Migration):
    """Create audit trail and metadata tables for compliance and tracking."""

    @property
    def migration_id(self) -> str:
        return "{migration_id}"

    @property
    def name(self) -> str:
        return "{name}"

    @property
    def description(self) -> str:
        return "Create audit trails and metadata tables for compliance and tracking"

    @property
    def dependencies(self) -> List[str]:
        return ["001_create_core_domain_tables"]

    def up(self, context: Any) -> MigrationResult:
        """Execute migration up."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Create audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_values TEXT,  -- JSON old values
                    new_values TEXT,  -- JSON new values
                    user_id TEXT,
                    user_name TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    correlation_id TEXT,
                    session_id TEXT,
                    created_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    CONSTRAINT chk_audit_action CHECK (action IN ('create', 'update', 'delete', 'view', 'export'))
                )
            """)

            # Create user sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    user_name TEXT,
                    session_token TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    started_at TEXT NOT NULL,
                    last_activity_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    metadata TEXT,  -- JSON metadata
                    UNIQUE(session_token)
                )
            """)

            # Create system configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_configuration (
                    id TEXT PRIMARY KEY,
                    config_key TEXT NOT NULL,
                    config_value TEXT NOT NULL,  -- JSON value
                    config_type TEXT NOT NULL,
                    is_encrypted BOOLEAN DEFAULT FALSE,
                    description TEXT,
                    created_by TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    UNIQUE(config_key),
                    CONSTRAINT chk_config_type CHECK (config_type IN ('string', 'number', 'boolean', 'json', 'encrypted'))
                )
            """)

            # Create data retention policies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_retention_policies (
                    id TEXT PRIMARY KEY,
                    policy_name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    retention_period_days INTEGER NOT NULL,
                    retention_action TEXT NOT NULL DEFAULT 'delete',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON metadata
                    UNIQUE(policy_name, entity_type),
                    CONSTRAINT chk_retention_action CHECK (retention_action IN ('delete', 'archive', 'anonymize'))
                )
            """)

            # Create backup history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_history (
                    id TEXT PRIMARY KEY,
                    backup_type TEXT NOT NULL,
                    backup_path TEXT,
                    backup_size_bytes INTEGER,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_seconds REAL,
                    error_message TEXT,
                    created_by TEXT,
                    metadata TEXT,  -- JSON metadata
                    CONSTRAINT chk_backup_status CHECK (status IN ('running', 'completed', 'failed')),
                    CONSTRAINT chk_backup_type CHECK (backup_type IN ('full', 'incremental', 'configuration'))
                )
            """)

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Audit and metadata tables created successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to create audit and metadata tables: {{str(e)}}",
                execution_time=0.0
            )

    def down(self, context: Any) -> MigrationResult:
        """Execute migration down."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Drop tables in reverse order
            cursor.execute("DROP TABLE IF EXISTS backup_history")
            cursor.execute("DROP TABLE IF EXISTS data_retention_policies")
            cursor.execute("DROP TABLE IF EXISTS system_configuration")
            cursor.execute("DROP TABLE IF EXISTS user_sessions")
            cursor.execute("DROP TABLE IF EXISTS audit_log")

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Audit and metadata tables dropped successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to drop audit and metadata tables: {{str(e)}}",
                execution_time=0.0
            )'''

        # Write migration file
        output_path = self.output_dir / f"{migration_id}.py"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_code)

        return str(output_path)

    def _create_performance_indexes_migration(self) -> str:
        """Create migration for performance optimization indexes."""

        migration_id = "007_create_performance_indexes"
        name = "Create Performance Indexes"

        migration_code = f'''"""Migration: {migration_id} - {name}"""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from infrastructure.migrations.migration import Migration, MigrationResult, MigrationStatus


class Migration007CreatePerformanceIndexes(Migration):
    """Create performance optimization indexes for the DDD schema."""

    @property
    def migration_id(self) -> str:
        return "{migration_id}"

    @property
    def name(self) -> str:
        return "{name}"

    @property
    def description(self) -> str:
        return "Create performance indexes for optimal query performance"

    @property
    def dependencies(self) -> List[str]:
        return ["001_create_core_domain_tables", "002_create_analysis_tables",
                "003_create_repository_tables", "004_create_distributed_processing_tables",
                "005_create_workflow_event_tables", "006_create_audit_metadata_tables"]

    def up(self, context: Any) -> MigrationResult:
        """Execute migration up."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Documents table indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_author ON documents(author_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_repository ON documents(repository_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_updated ON documents(updated_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_quality ON documents(quality_score)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_author_repo ON documents(author_id, repository_id)")

            # Analyses table indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_document ON analyses(document_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_type ON analyses(analysis_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_worker ON analyses(worker_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_priority_status ON analyses(priority, status)")

            # Findings table indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_analysis ON findings(analysis_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_document ON findings(document_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_type ON findings(finding_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_created ON findings(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_severity_status ON findings(severity, status)")

            # Repository tables indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_repositories_type ON repositories(repository_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_repositories_owner ON repositories(owner)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_repositories_synced ON repositories(last_synced_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_repositories_private ON repositories(is_private)")

            # Distributed processing indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workers_status ON workers(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workers_capabilities ON workers(capabilities)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_distributed_tasks_status ON distributed_tasks(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_distributed_tasks_type ON distributed_tasks(task_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_distributed_tasks_worker ON distributed_tasks(assigned_worker_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_distributed_tasks_priority ON distributed_tasks(priority)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_distributed_tasks_created ON distributed_tasks(created_at)")

            # Workflow indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflows_type ON workflows(workflow_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow ON workflow_executions(workflow_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status)")

            # Event indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_source ON events(event_source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_processed ON events(processed)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)")

            # Audit and metadata indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active)")

            # Composite indexes for common queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_repo_status_updated ON documents(repository_id, status, updated_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_doc_status_created ON analyses(document_id, status, created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_analysis_severity ON findings(analysis_id, severity)")

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Performance indexes created successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to create performance indexes: {{str(e)}}",
                execution_time=0.0
            )

    def down(self, context: Any) -> MigrationResult:
        """Execute migration down."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Drop all indexes (SQLite doesn't have a simple way to drop all at once)
            indexes_to_drop = [
                "idx_documents_author", "idx_documents_repository", "idx_documents_status",
                "idx_documents_updated", "idx_documents_quality", "idx_documents_created",
                "idx_documents_author_repo", "idx_analyses_document", "idx_analyses_status",
                "idx_analyses_type", "idx_analyses_created", "idx_analyses_worker",
                "idx_analyses_priority_status", "idx_findings_analysis", "idx_findings_document",
                "idx_findings_severity", "idx_findings_status", "idx_findings_type",
                "idx_findings_created", "idx_findings_severity_status", "idx_repositories_type",
                "idx_repositories_owner", "idx_repositories_synced", "idx_repositories_private",
                "idx_workers_status", "idx_workers_capabilities", "idx_distributed_tasks_status",
                "idx_distributed_tasks_type", "idx_distributed_tasks_worker", "idx_distributed_tasks_priority",
                "idx_distributed_tasks_created", "idx_workflows_type", "idx_workflows_status",
                "idx_workflow_executions_workflow", "idx_workflow_executions_status",
                "idx_events_type", "idx_events_source", "idx_events_processed", "idx_events_created",
                "idx_audit_log_entity", "idx_audit_log_action", "idx_audit_log_created",
                "idx_user_sessions_token", "idx_user_sessions_active",
                "idx_documents_repo_status_updated", "idx_analyses_doc_status_created",
                "idx_findings_analysis_severity"
            ]

            for index_name in indexes_to_drop:
                try:
                    cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                except:
                    pass  # Ignore errors for indexes that don't exist

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Performance indexes dropped successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to drop performance indexes: {{str(e)}}",
                execution_time=0.0
            )'''

        # Write migration file
        output_path = self.output_dir / f"{migration_id}.py"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_code)

        return str(output_path)

    def _create_data_migration_triggers_migration(self) -> str:
        """Create migration for data migration triggers."""

        migration_id = "008_create_data_migration_triggers"
        name = "Create Data Migration Triggers"

        migration_code = f'''"""Migration: {migration_id} - {name}"""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from infrastructure.migrations.migration import Migration, MigrationResult, MigrationStatus


class Migration008CreateDataMigrationTriggers(Migration):
    """Create triggers for data consistency and audit trails."""

    @property
    def migration_id(self) -> str:
        return "{migration_id}"

    @property
    def name(self) -> str:
        return "{name}"

    @property
    def description(self) -> str:
        return "Create database triggers for data consistency and audit trails"

    @property
    def dependencies(self) -> List[str]:
        return ["001_create_core_domain_tables", "006_create_audit_metadata_tables"]

    def up(self, context: Any) -> MigrationResult:
        """Execute migration up."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Create audit trigger for documents table
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS audit_documents_insert
                AFTER INSERT ON documents
                BEGIN
                    INSERT INTO audit_log (
                        id, entity_type, entity_id, action, new_values,
                        created_at, metadata
                    ) VALUES (
                        lower(hex(randomblob(16))),
                        'document',
                        NEW.id,
                        'create',
                        json_object(
                            'title', NEW.title,
                            'author_id', NEW.author_id,
                            'repository_id', NEW.repository_id,
                            'version', NEW.version,
                            'created_at', NEW.created_at
                        ),
                        datetime('now'),
                        json_object('trigger', 'audit_documents_insert')
                    );
                END
            """)

            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS audit_documents_update
                AFTER UPDATE ON documents
                BEGIN
                    INSERT INTO audit_log (
                        id, entity_type, entity_id, action, old_values, new_values,
                        created_at, metadata
                    ) VALUES (
                        lower(hex(randomblob(16))),
                        'document',
                        NEW.id,
                        'update',
                        json_object(
                            'title', OLD.title,
                            'content', OLD.content_text,
                            'version', OLD.version,
                            'updated_at', OLD.updated_at
                        ),
                        json_object(
                            'title', NEW.title,
                            'content', NEW.content_text,
                            'version', NEW.version,
                            'updated_at', NEW.updated_at
                        ),
                        datetime('now'),
                        json_object('trigger', 'audit_documents_update')
                    );
                END
            """)

            # Create trigger to update document analysis count
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_document_analysis_count
                AFTER INSERT ON analyses
                BEGIN
                    UPDATE documents
                    SET analysis_count = analysis_count + 1,
                        last_analyzed_at = datetime('now'),
                        updated_at = datetime('now')
                    WHERE id = NEW.document_id;
                END
            """)

            # Create trigger to update worker statistics
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_worker_stats_completed
                AFTER UPDATE ON distributed_tasks
                WHEN NEW.status = 'completed' AND OLD.status != 'completed'
                BEGIN
                    UPDATE workers
                    SET tasks_completed = tasks_completed + 1,
                        last_seen_at = datetime('now')
                    WHERE id = NEW.assigned_worker_id;
                END
            """)

            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_worker_stats_failed
                AFTER UPDATE ON distributed_tasks
                WHEN NEW.status = 'failed' AND OLD.status != 'failed'
                BEGIN
                    UPDATE workers
                    SET tasks_failed = tasks_failed + 1,
                        last_seen_at = datetime('now')
                    WHERE id = NEW.assigned_worker_id;
                END
            """)

            # Create trigger to automatically update timestamps
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_documents_timestamp
                AFTER UPDATE ON documents
                BEGIN
                    UPDATE documents
                    SET updated_at = datetime('now')
                    WHERE id = NEW.id;
                END
            """)

            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_analyses_timestamp
                AFTER UPDATE ON analyses
                BEGIN
                    UPDATE analyses
                    SET updated_at = datetime('now')
                    WHERE id = NEW.id;
                END
            """)

            # Create trigger to validate data consistency
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS validate_document_quality_score
                BEFORE UPDATE ON documents
                WHEN NEW.quality_score IS NOT NULL
                BEGIN
                    SELECT CASE
                        WHEN NEW.quality_score < 0.0 OR NEW.quality_score > 1.0 THEN
                            RAISE(ABORT, 'Quality score must be between 0.0 and 1.0')
                    END;
                END
            """)

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Data migration triggers created successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to create data migration triggers: {{str(e)}}",
                execution_time=0.0
            )

    def down(self, context: Any) -> MigrationResult:
        """Execute migration down."""
        try:
            conn = context.get('connection')
            cursor = conn.cursor()

            # Drop all triggers
            triggers_to_drop = [
                "audit_documents_insert",
                "audit_documents_update",
                "update_document_analysis_count",
                "update_worker_stats_completed",
                "update_worker_stats_failed",
                "update_documents_timestamp",
                "update_analyses_timestamp",
                "validate_document_quality_score"
            ]

            for trigger_name in triggers_to_drop:
                try:
                    cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
                except:
                    pass  # Ignore errors for triggers that don't exist

            conn.commit()

            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.SUCCESS,
                message="Data migration triggers dropped successfully",
                execution_time=0.0
            )

        except Exception as e:
            return MigrationResult(
                migration_id=self.migration_id,
                status=MigrationStatus.FAILED,
                message=f"Failed to drop data migration triggers: {{str(e)}}",
                execution_time=0.0
            )'''

        # Write migration file
        output_path = self.output_dir / f"{migration_id}.py"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(migration_code)

        return str(output_path)


def main():
    """Main migration generation function."""
    import argparse

    parser = argparse.ArgumentParser(description="DDD Schema Migration Generator")
    parser.add_argument("--output", default="migrations/ddd_schema",
                       help="Output directory for migration files")

    args = parser.parse_args()

    print("🏗️  DDD Schema Migration Generator")
    print("=" * 50)

    generator = DDDSchemaMigrationGenerator(args.output)
    migrations = generator.generate_all_migrations()

    print(f"\n✅ Successfully generated {len(migrations)} comprehensive DDD schema migrations!")
    print("\n📋 Migration Summary:")
    print("   1. Core Domain Tables (documents, analyses, findings)")
    print("   2. Analysis Tables (semantic, sentiment, quality, risk)")
    print("   3. Repository Tables (management, sync, connectivity)")
    print("   4. Distributed Processing (workers, tasks, queues)")
    print("   5. Workflow & Events (automations, webhooks)")
    print("   6. Audit & Metadata (compliance, tracking)")
    print("   7. Performance Indexes (optimization)")
    print("   8. Data Migration Triggers (consistency)")

    print("\n🚀 Next Steps:")
    print("   1. Review generated migration files")
    print("   2. Test migrations in development environment")
    print("   3. Create data migration scripts for existing data")
    print("   4. Update application configuration")
    print("   5. Deploy migrations to staging/production")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
