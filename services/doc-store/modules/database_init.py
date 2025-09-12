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

        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash)",
            "CREATE INDEX IF NOT EXISTS idx_analyses_document_id ON analyses(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_analyses_prompt_hash ON analyses(prompt_hash)",
            "CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_style_examples_language ON style_examples(language)"
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
