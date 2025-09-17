"""Database schema definitions for Doc Store service.

Contains all table creation statements and indexes.
"""
from .connection import get_doc_store_connection, return_doc_store_connection


def create_documents_table() -> str:
    """Create documents table schema."""
    return """
        CREATE TABLE IF NOT EXISTS documents (
          id TEXT PRIMARY KEY,
          content TEXT NOT NULL,
          content_hash TEXT,
          metadata TEXT,
          correlation_id TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT
        )
    """


def create_analyses_table() -> str:
    """Create analyses table schema."""
    return """
        CREATE TABLE IF NOT EXISTS analyses (
          id TEXT PRIMARY KEY,
          document_id TEXT NOT NULL,
          analyzer TEXT,
          model TEXT,
          prompt_hash TEXT,
          result TEXT NOT NULL,
          score REAL,
          metadata TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """


def create_ensembles_table() -> str:
    """Create ensembles table schema."""
    return """
        CREATE TABLE IF NOT EXISTS ensembles (
          id TEXT PRIMARY KEY,
          document_id TEXT NOT NULL,
          config TEXT,
          results TEXT,
          analysis TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """


def create_style_examples_table() -> str:
    """Create style examples table schema."""
    return """
        CREATE TABLE IF NOT EXISTS style_examples (
          id TEXT PRIMARY KEY,
          language TEXT NOT NULL,
          pattern TEXT NOT NULL,
          example TEXT NOT NULL,
          explanation TEXT,
          created_at TEXT NOT NULL
        )
    """


def create_document_versions_table() -> str:
    """Create document versions table schema."""
    return """
        CREATE TABLE IF NOT EXISTS document_versions (
          id TEXT PRIMARY KEY,
          document_id TEXT NOT NULL,
          version_number INTEGER NOT NULL,
          content TEXT,
          content_hash TEXT,
          metadata TEXT,
          change_summary TEXT,
          created_by TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """


def create_document_relationships_table() -> str:
    """Create document relationships table schema."""
    return """
        CREATE TABLE IF NOT EXISTS document_relationships (
          id TEXT PRIMARY KEY,
          source_document_id TEXT NOT NULL,
          target_document_id TEXT NOT NULL,
          relationship_type TEXT NOT NULL,
          strength REAL DEFAULT 1.0,
          metadata TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY(source_document_id) REFERENCES documents(id) ON DELETE CASCADE,
          FOREIGN KEY(target_document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """


def create_document_tags_table() -> str:
    """Create document tags table schema."""
    return """
        CREATE TABLE IF NOT EXISTS document_tags (
          id TEXT PRIMARY KEY,
          document_id TEXT NOT NULL,
          tag TEXT NOT NULL,
          confidence REAL DEFAULT 1.0,
          created_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """


def create_semantic_metadata_table() -> str:
    """Create semantic metadata table schema."""
    return """
        CREATE TABLE IF NOT EXISTS semantic_metadata (
          id TEXT PRIMARY KEY,
          document_id TEXT NOT NULL,
          entity_type TEXT,
          entity_value TEXT,
          confidence REAL,
          metadata TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """


def create_tag_taxonomy_table() -> str:
    """Create tag taxonomy table schema."""
    return """
        CREATE TABLE IF NOT EXISTS tag_taxonomy (
          id TEXT PRIMARY KEY,
          tag TEXT UNIQUE NOT NULL,
          parent_tag TEXT,
          description TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY(parent_tag) REFERENCES tag_taxonomy(tag) ON DELETE CASCADE
        )
    """


def create_lifecycle_policies_table() -> str:
    """Create lifecycle policies table schema."""
    return """
        CREATE TABLE IF NOT EXISTS lifecycle_policies (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          description TEXT,
          conditions TEXT NOT NULL,
          actions TEXT NOT NULL,
          priority INTEGER DEFAULT 0,
          enabled INTEGER DEFAULT 1,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
    """


def create_document_lifecycle_table() -> str:
    """Create document lifecycle table schema."""
    return """
        CREATE TABLE IF NOT EXISTS document_lifecycle (
          id TEXT PRIMARY KEY,
          document_id TEXT UNIQUE NOT NULL,
          current_phase TEXT DEFAULT 'active',
          retention_period_days INTEGER,
          archival_date TEXT,
          deletion_date TEXT,
          last_reviewed TEXT,
          compliance_status TEXT DEFAULT 'compliant',
          applied_policies TEXT,
          metadata TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """


def create_lifecycle_events_table() -> str:
    """Create lifecycle events table schema."""
    return """
        CREATE TABLE IF NOT EXISTS lifecycle_events (
          id TEXT PRIMARY KEY,
          document_id TEXT NOT NULL,
          event_type TEXT NOT NULL,
          policy_id TEXT,
          old_phase TEXT,
          new_phase TEXT,
          details TEXT,
          performed_by TEXT DEFAULT 'system',
          created_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """


def create_webhooks_table() -> str:
    """Create webhooks table schema."""
    return """
        CREATE TABLE IF NOT EXISTS webhooks (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          url TEXT NOT NULL,
          secret TEXT,
          headers TEXT,
          events TEXT NOT NULL,
          is_active INTEGER DEFAULT 1,
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
          event_id TEXT NOT NULL,
          payload TEXT NOT NULL,
          status TEXT DEFAULT 'pending',
          response_code INTEGER,
          error_message TEXT,
          attempt_count INTEGER DEFAULT 0,
          delivered_at TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY(webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE
        )
    """


def create_notification_events_table() -> str:
    """Create notification events table schema."""
    return """
        CREATE TABLE IF NOT EXISTS notification_events (
          id TEXT PRIMARY KEY,
          event_type TEXT NOT NULL,
          entity_type TEXT,
          entity_id TEXT,
          user_id TEXT,
          data TEXT,
          created_at TEXT NOT NULL
        )
    """


def create_bulk_operations_table() -> str:
    """Create bulk operations table schema."""
    return """
        CREATE TABLE IF NOT EXISTS bulk_operations (
          operation_id TEXT PRIMARY KEY,
          operation_type TEXT NOT NULL,
          status TEXT DEFAULT 'pending',
          total_items INTEGER DEFAULT 0,
          processed_items INTEGER DEFAULT 0,
          successful_items INTEGER DEFAULT 0,
          failed_items INTEGER DEFAULT 0,
          errors TEXT,
          results TEXT,
          metadata TEXT,
          created_at TEXT NOT NULL,
          completed_at TEXT
        )
    """


def get_all_table_schemas() -> list[str]:
    """Get all table creation schemas."""
    return [
        create_documents_table(),
        create_analyses_table(),
        create_ensembles_table(),
        create_style_examples_table(),
        create_document_versions_table(),
        create_document_relationships_table(),
        create_document_tags_table(),
        create_semantic_metadata_table(),
        create_tag_taxonomy_table(),
        create_lifecycle_policies_table(),
        create_document_lifecycle_table(),
        create_lifecycle_events_table(),
        create_webhooks_table(),
        create_webhook_deliveries_table(),
        create_notification_events_table(),
        create_bulk_operations_table(),
    ]


def create_indexes() -> list[str]:
    """Get all index creation statements."""
    return [
        "CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash)",
        "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_documents_correlation_id ON documents(correlation_id)",
        "CREATE INDEX IF NOT EXISTS idx_analyses_document_id ON analyses(document_id)",
        "CREATE INDEX IF NOT EXISTS idx_analyses_analyzer ON analyses(analyzer)",
        "CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_ensembles_document_id ON ensembles(document_id)",
        "CREATE INDEX IF NOT EXISTS idx_style_examples_language ON style_examples(language)",
        "CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON document_versions(document_id)",
        "CREATE INDEX IF NOT EXISTS idx_document_versions_version_number ON document_versions(version_number)",
        "CREATE INDEX IF NOT EXISTS idx_document_relationships_source ON document_relationships(source_document_id)",
        "CREATE INDEX IF NOT EXISTS idx_document_relationships_target ON document_relationships(target_document_id)",
        "CREATE INDEX IF NOT EXISTS idx_document_relationships_type ON document_relationships(relationship_type)",
        "CREATE INDEX IF NOT EXISTS idx_document_tags_document_id ON document_tags(document_id)",
        "CREATE INDEX IF NOT EXISTS idx_document_tags_tag ON document_tags(tag)",
        "CREATE INDEX IF NOT EXISTS idx_semantic_metadata_document_id ON semantic_metadata(document_id)",
        "CREATE INDEX IF NOT EXISTS idx_semantic_metadata_entity_type ON semantic_metadata(entity_type)",
        "CREATE INDEX IF NOT EXISTS idx_tag_taxonomy_parent ON tag_taxonomy(parent_tag)",
        "CREATE INDEX IF NOT EXISTS idx_lifecycle_policies_enabled ON lifecycle_policies(enabled)",
        "CREATE INDEX IF NOT EXISTS idx_document_lifecycle_document_id ON document_lifecycle(document_id)",
        "CREATE INDEX IF NOT EXISTS idx_document_lifecycle_current_phase ON document_lifecycle(current_phase)",
        "CREATE INDEX IF NOT EXISTS idx_document_lifecycle_archival_date ON document_lifecycle(archival_date)",
        "CREATE INDEX IF NOT EXISTS idx_document_lifecycle_deletion_date ON document_lifecycle(deletion_date)",
        "CREATE INDEX IF NOT EXISTS idx_lifecycle_events_document_id ON lifecycle_events(document_id)",
        "CREATE INDEX IF NOT EXISTS idx_lifecycle_events_event_type ON lifecycle_events(event_type)",
        "CREATE INDEX IF NOT EXISTS idx_webhooks_is_active ON webhooks(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id)",
        "CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_status ON webhook_deliveries(status)",
        "CREATE INDEX IF NOT EXISTS idx_notification_events_event_type ON notification_events(event_type)",
        "CREATE INDEX IF NOT EXISTS idx_notification_events_entity_type ON notification_events(entity_type)",
        "CREATE INDEX IF NOT EXISTS idx_bulk_operations_status ON bulk_operations(status)",
        "CREATE INDEX IF NOT EXISTS idx_bulk_operations_created_at ON bulk_operations(created_at)",
    ]


def init_database() -> None:
    """Initialize database tables and indexes."""
    conn = get_doc_store_connection()
    try:
        # Create tables
        for schema in get_all_table_schemas():
            conn.execute(schema)

        # Create indexes
        for index_sql in create_indexes():
            conn.execute(index_sql)

        # Enable FTS on documents table
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                content, content='documents', content_rowid='rowid'
            )
        """)

        # Create FTS triggers
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_fts_insert AFTER INSERT ON documents
            BEGIN
                INSERT INTO documents_fts(rowid, content) VALUES (new.rowid, new.content);
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_fts_delete AFTER DELETE ON documents
            BEGIN
                DELETE FROM documents_fts WHERE rowid = old.rowid;
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_fts_update AFTER UPDATE ON documents
            BEGIN
                UPDATE documents_fts SET content = new.content WHERE rowid = new.rowid;
            END
        """)

        conn.commit()

    finally:
        return_doc_store_connection(conn)
