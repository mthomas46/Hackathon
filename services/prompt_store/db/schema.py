"""Database schema definitions for Prompt Store service.

Contains all table creation statements and indexes.
"""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from ..db.connection import get_prompt_store_connection, return_prompt_store_connection


def create_prompts_table() -> str:
    """Create prompts table schema."""
    return """
        CREATE TABLE IF NOT EXISTS prompts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            content TEXT NOT NULL,
            variables TEXT,  -- JSON array
            tags TEXT,  -- JSON array
            is_active BOOLEAN DEFAULT 1,
            is_template BOOLEAN DEFAULT 0,
            lifecycle_status TEXT DEFAULT 'draft',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            parent_id TEXT,
            performance_score REAL DEFAULT 0.0,
            usage_count INTEGER DEFAULT 0
        )
    """


def create_prompt_versions_table() -> str:
    """Create prompt versions table schema."""
    return """
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id TEXT PRIMARY KEY,
            prompt_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            content TEXT NOT NULL,
            variables TEXT,  -- JSON array
            change_summary TEXT,
            change_type TEXT DEFAULT 'update',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
        )
    """


def create_ab_tests_table() -> str:
    """Create A/B tests table schema."""
    return """
        CREATE TABLE IF NOT EXISTS ab_tests (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            prompt_a_id TEXT NOT NULL,
            prompt_b_id TEXT NOT NULL,
            test_metric TEXT DEFAULT 'response_quality',
            is_active BOOLEAN DEFAULT 1,
            traffic_split REAL DEFAULT 0.5,
            start_date TEXT NOT NULL,
            end_date TEXT,
            target_audience TEXT,  -- JSON object
            created_by TEXT NOT NULL,
            winner TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(prompt_a_id) REFERENCES prompts(id) ON DELETE CASCADE,
            FOREIGN KEY(prompt_b_id) REFERENCES prompts(id) ON DELETE CASCADE
        )
    """


def create_ab_test_results_table() -> str:
    """Create A/B test results table schema."""
    return """
        CREATE TABLE IF NOT EXISTS ab_test_results (
            id TEXT PRIMARY KEY,
            test_id TEXT NOT NULL,
            prompt_id TEXT NOT NULL,
            metric_value REAL NOT NULL,
            sample_size INTEGER NOT NULL,
            confidence_level REAL DEFAULT 0.0,
            statistical_significance BOOLEAN DEFAULT 0,
            recorded_at TEXT NOT NULL,
            FOREIGN KEY(test_id) REFERENCES ab_tests(id) ON DELETE CASCADE,
            FOREIGN KEY(prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
        )
    """


def create_prompt_usage_table() -> str:
    """Create prompt usage table schema."""
    return """
        CREATE TABLE IF NOT EXISTS prompt_usage (
            id TEXT PRIMARY KEY,
            prompt_id TEXT NOT NULL,
            session_id TEXT,
            user_id TEXT,
            service_name TEXT NOT NULL,
            operation TEXT DEFAULT 'generate',
            input_tokens INTEGER,
            output_tokens INTEGER,
            response_time_ms REAL,
            success BOOLEAN DEFAULT 1,
            error_message TEXT,
            metadata TEXT,  -- JSON object
            created_at TEXT NOT NULL,
            FOREIGN KEY(prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
        )
    """


def create_prompt_relationships_table() -> str:
    """Create prompt relationships table schema."""
    return """
        CREATE TABLE IF NOT EXISTS prompt_relationships (
            id TEXT PRIMARY KEY,
            source_prompt_id TEXT NOT NULL,
            target_prompt_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            strength REAL DEFAULT 1.0,
            metadata TEXT,  -- JSON object
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(source_prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
            FOREIGN KEY(target_prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
            UNIQUE(source_prompt_id, target_prompt_id, relationship_type)
        )
    """


def create_bulk_operations_table() -> str:
    """Create bulk operations table schema."""
    return """
        CREATE TABLE IF NOT EXISTS bulk_operations (
            id TEXT PRIMARY KEY,
            operation_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            total_items INTEGER DEFAULT 0,
            processed_items INTEGER DEFAULT 0,
            successful_items INTEGER DEFAULT 0,
            failed_items INTEGER DEFAULT 0,
            errors TEXT,  -- JSON array
            metadata TEXT,  -- JSON object
            results TEXT,  -- JSON array
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            completed_at TEXT
        )
    """


def create_webhooks_table() -> str:
    """Create webhooks table schema."""
    return """
        CREATE TABLE IF NOT EXISTS webhooks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            events TEXT NOT NULL,  -- JSON array
            secret TEXT,
            is_active BOOLEAN DEFAULT 1,
            retry_count INTEGER DEFAULT 3,
            timeout_seconds INTEGER DEFAULT 30,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """


def create_webhook_deliveries_table() -> str:
    """Create webhook deliveries table schema."""
    return """
        CREATE TABLE IF NOT EXISTS webhook_deliveries (
            id TEXT PRIMARY KEY,
            webhook_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT NOT NULL,  -- JSON object
            status TEXT DEFAULT 'pending',
            response_code INTEGER,
            response_body TEXT,
            error_message TEXT,
            attempt_count INTEGER DEFAULT 1,
            delivered_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE
        )
    """


def create_notifications_table() -> str:
    """Create notifications table schema."""
    return """
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            event_data TEXT NOT NULL,  -- JSON object
            recipient_type TEXT DEFAULT 'webhook',  -- webhook, email, etc.
            recipient_id TEXT,
            status TEXT DEFAULT 'pending',
            sent_at TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL
        )
    """


def get_all_table_schemas() -> List[str]:
    """Get all table creation schemas."""
    return [
        create_prompts_table(),
        create_prompt_versions_table(),
        create_ab_tests_table(),
        create_ab_test_results_table(),
        create_prompt_usage_table(),
        create_prompt_relationships_table(),
        create_bulk_operations_table(),
        create_webhooks_table(),
        create_webhook_deliveries_table(),
        create_notifications_table(),
    ]


def create_indexes() -> List[str]:
    """Create database indexes for performance."""
    return [
        # Prompts indexes
        "CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category)",
        "CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts(tags)",
        "CREATE INDEX IF NOT EXISTS idx_prompts_active ON prompts(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_prompts_lifecycle ON prompts(lifecycle_status)",
        "CREATE INDEX IF NOT EXISTS idx_prompts_performance ON prompts(performance_score)",
        "CREATE INDEX IF NOT EXISTS idx_prompts_usage ON prompts(usage_count)",
        "CREATE INDEX IF NOT EXISTS idx_prompts_created_by ON prompts(created_by)",

        # Prompt versions indexes
        "CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt_id ON prompt_versions(prompt_id)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_versions_version ON prompt_versions(prompt_id, version)",

        # A/B tests indexes
        "CREATE INDEX IF NOT EXISTS idx_ab_tests_active ON ab_tests(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_ab_tests_prompts ON ab_tests(prompt_a_id, prompt_b_id)",
        "CREATE INDEX IF NOT EXISTS idx_ab_tests_dates ON ab_tests(start_date, end_date)",

        # A/B test results indexes
        "CREATE INDEX IF NOT EXISTS idx_ab_test_results_test ON ab_test_results(test_id)",
        "CREATE INDEX IF NOT EXISTS idx_ab_test_results_prompt ON ab_test_results(prompt_id)",
        "CREATE INDEX IF NOT EXISTS idx_ab_test_results_recorded ON ab_test_results(recorded_at)",

        # Prompt usage indexes
        "CREATE INDEX IF NOT EXISTS idx_prompt_usage_prompt ON prompt_usage(prompt_id)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_usage_session ON prompt_usage(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_usage_user ON prompt_usage(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_usage_service ON prompt_usage(service_name)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_usage_created ON prompt_usage(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_usage_success ON prompt_usage(success)",

        # Prompt relationships indexes
        "CREATE INDEX IF NOT EXISTS idx_prompt_relationships_source ON prompt_relationships(source_prompt_id)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_relationships_target ON prompt_relationships(target_prompt_id)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_relationships_type ON prompt_relationships(relationship_type)",
        "CREATE INDEX IF NOT EXISTS idx_prompt_relationships_strength ON prompt_relationships(strength)",

        # Bulk operations indexes
        "CREATE INDEX IF NOT EXISTS idx_bulk_operations_status ON bulk_operations(status)",
        "CREATE INDEX IF NOT EXISTS idx_bulk_operations_type ON bulk_operations(operation_type)",
        "CREATE INDEX IF NOT EXISTS idx_bulk_operations_created ON bulk_operations(created_at)",

        # Webhooks indexes
        "CREATE INDEX IF NOT EXISTS idx_webhooks_active ON webhooks(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_webhooks_events ON webhooks(events)",

        # Webhook deliveries indexes
        "CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook ON webhook_deliveries(webhook_id)",
        "CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_status ON webhook_deliveries(status)",
        "CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_created ON webhook_deliveries(created_at)",

        # Notifications indexes
        "CREATE INDEX IF NOT EXISTS idx_notifications_event_type ON notifications(event_type)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)",
    ]


def init_database() -> None:
    """Initialize database tables and indexes."""
    conn = get_prompt_store_connection()
    try:
        # Create tables
        for schema in get_all_table_schemas():
            conn.execute(schema)

        # Create indexes
        for index_sql in create_indexes():
            conn.execute(index_sql)

        # Enable FTS on prompts table for content search
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS prompts_fts USING fts5(
                name, category, description, content, tags, content='prompts', content_rowid='rowid'
            )
        """)

        # Create FTS triggers
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS prompts_fts_insert AFTER INSERT ON prompts
            BEGIN
                INSERT INTO prompts_fts(rowid, name, category, description, content, tags)
                VALUES (new.rowid, new.name, new.category, new.description, new.content, new.tags);
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS prompts_fts_delete AFTER DELETE ON prompts
            BEGIN
                DELETE FROM prompts_fts WHERE rowid = old.rowid;
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS prompts_fts_update AFTER UPDATE ON prompts
            BEGIN
                UPDATE prompts_fts SET
                    name = new.name,
                    category = new.category,
                    description = new.description,
                    content = new.content,
                    tags = new.tags
                WHERE rowid = new.rowid;
            END
        """)

        conn.commit()
        print("✅ Prompt Store database initialized successfully")

    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to initialize database: {e}")
        raise
    finally:
        return_prompt_store_connection(conn)
