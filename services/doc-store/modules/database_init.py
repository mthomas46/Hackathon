"""Database initialization for Doc Store service.

Contains database schema creation and initialization logic.
"""
import sqlite3
import os
from typing import Optional

from .shared_utils import get_doc_store_connection


def init_database() -> None:
    """Initialize database tables and indexes."""
    conn = get_doc_store_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
              id TEXT PRIMARY KEY,
              content TEXT,
              content_hash TEXT,
              metadata TEXT,
              created_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
              id TEXT PRIMARY KEY,
              document_id TEXT,
              analyzer TEXT,
              model TEXT,
              prompt_hash TEXT,
              result TEXT,
              score REAL,
              metadata TEXT,
              created_at TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ensembles (
              id TEXT PRIMARY KEY,
              document_id TEXT,
              config TEXT,
              results TEXT,
              analysis TEXT,
              created_at TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS style_examples (
              id TEXT PRIMARY KEY,
              document_id TEXT,
              language TEXT,
              title TEXT,
              tags TEXT,
              created_at TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_versions (
              id TEXT PRIMARY KEY,
              document_id TEXT,
              version_number INTEGER,
              content TEXT,
              content_hash TEXT,
              metadata TEXT,
              change_summary TEXT,
              changed_by TEXT,
              created_at TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_relationships (
              id TEXT PRIMARY KEY,
              source_document_id TEXT,
              target_document_id TEXT,
              relationship_type TEXT,
              strength REAL DEFAULT 1.0,
              metadata TEXT,
              created_at TEXT,
              updated_at TEXT,
              FOREIGN KEY(source_document_id) REFERENCES documents(id),
              FOREIGN KEY(target_document_id) REFERENCES documents(id),
              UNIQUE(source_document_id, target_document_id, relationship_type)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_tags (
              id TEXT PRIMARY KEY,
              document_id TEXT,
              tag TEXT,
              category TEXT,
              confidence REAL DEFAULT 1.0,
              metadata TEXT,
              created_at TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id),
              UNIQUE(document_id, tag, category)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS semantic_metadata (
              id TEXT PRIMARY KEY,
              document_id TEXT,
              entity_type TEXT,
              entity_value TEXT,
              confidence REAL,
              start_offset INTEGER,
              end_offset INTEGER,
              metadata TEXT,
              created_at TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id),
              UNIQUE(document_id, entity_type, entity_value, start_offset, end_offset)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tag_taxonomy (
              id TEXT PRIMARY KEY,
              tag TEXT UNIQUE,
              category TEXT,
              description TEXT,
              parent_tag TEXT,
              synonyms TEXT,
              created_at TEXT,
              updated_at TEXT,
              FOREIGN KEY(parent_tag) REFERENCES tag_taxonomy(tag)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS lifecycle_policies (
              id TEXT PRIMARY KEY,
              name TEXT UNIQUE,
              description TEXT,
              conditions TEXT,
              actions TEXT,
              priority INTEGER DEFAULT 0,
              enabled BOOLEAN DEFAULT 1,
              created_at TEXT,
              updated_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_lifecycle (
              id TEXT PRIMARY KEY,
              document_id TEXT,
              current_phase TEXT DEFAULT 'active',
              retention_period_days INTEGER,
              archival_date TEXT,
              deletion_date TEXT,
              last_reviewed TEXT,
              compliance_status TEXT DEFAULT 'compliant',
              applied_policies TEXT,
              metadata TEXT,
              created_at TEXT,
              updated_at TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS lifecycle_events (
              id TEXT PRIMARY KEY,
              document_id TEXT,
              event_type TEXT,
              policy_id TEXT,
              old_phase TEXT,
              new_phase TEXT,
              details TEXT,
              performed_by TEXT,
              created_at TEXT,
              FOREIGN KEY(document_id) REFERENCES documents(id),
              FOREIGN KEY(policy_id) REFERENCES lifecycle_policies(id)
            )
        """)

        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash)",
            "CREATE INDEX IF NOT EXISTS idx_analyses_document_id ON analyses(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_analyses_prompt_hash ON analyses(prompt_hash)",
            "CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_style_examples_language ON style_examples(language)",
            "CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON document_versions(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_document_versions_version_number ON document_versions(version_number)",
            "CREATE INDEX IF NOT EXISTS idx_document_versions_created_at ON document_versions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_relationships_source ON document_relationships(source_document_id)",
            "CREATE INDEX IF NOT EXISTS idx_relationships_target ON document_relationships(target_document_id)",
            "CREATE INDEX IF NOT EXISTS idx_relationships_type ON document_relationships(relationship_type)",
            "CREATE INDEX IF NOT EXISTS idx_relationships_strength ON document_relationships(strength)",
            "CREATE INDEX IF NOT EXISTS idx_document_tags_document_id ON document_tags(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_document_tags_tag ON document_tags(tag)",
            "CREATE INDEX IF NOT EXISTS idx_document_tags_category ON document_tags(category)",
            "CREATE INDEX IF NOT EXISTS idx_semantic_metadata_document_id ON semantic_metadata(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_semantic_metadata_entity_type ON semantic_metadata(entity_type)",
            "CREATE INDEX IF NOT EXISTS idx_tag_taxonomy_tag ON tag_taxonomy(tag)",
            "CREATE INDEX IF NOT EXISTS idx_tag_taxonomy_category ON tag_taxonomy(category)",
            "CREATE INDEX IF NOT EXISTS idx_tag_taxonomy_parent ON tag_taxonomy(parent_tag)",
            "CREATE INDEX IF NOT EXISTS idx_lifecycle_policies_name ON lifecycle_policies(name)",
            "CREATE INDEX IF NOT EXISTS idx_lifecycle_policies_enabled ON lifecycle_policies(enabled)",
            "CREATE INDEX IF NOT EXISTS idx_document_lifecycle_document_id ON document_lifecycle(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_document_lifecycle_phase ON document_lifecycle(current_phase)",
            "CREATE INDEX IF NOT EXISTS idx_document_lifecycle_deletion_date ON document_lifecycle(deletion_date)",
            "CREATE INDEX IF NOT EXISTS idx_lifecycle_events_document_id ON lifecycle_events(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_lifecycle_events_type ON lifecycle_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_lifecycle_events_created_at ON lifecycle_events(created_at)"
        ]

        for index in indexes:
            conn.execute(index)

        # Optional FTS for search (best-effort)
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                  id UNINDEXED,
                  title,
                  content,
                  tags
                )
            """)
        except Exception:
            pass

        conn.commit()
    finally:
        conn.close()
