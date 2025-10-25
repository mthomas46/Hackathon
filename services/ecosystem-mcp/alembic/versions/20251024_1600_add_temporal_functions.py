"""Add temporal query functions

Revision ID: temporal_001
Revises: a1b2c3d4e5f6
Create Date: 2025-10-24 16:00:00.000000+00:00

This migration adds PostgreSQL functions for temporal document queries:
- get_all_documents_as_of(timestamp): Get documents as they existed at a point in time
- get_document_timeline(document_id): Get complete history of a document
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'temporal_001'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create temporal query functions."""
    
    # Function 1: Get all documents as of a specific date
    op.execute("""
    CREATE OR REPLACE FUNCTION get_all_documents_as_of(query_time TIMESTAMP WITH TIME ZONE)
    RETURNS TABLE (
        document_id UUID,
        version_id INTEGER,
        version_number INTEGER,
        content_hash VARCHAR(64),
        modified_at TIMESTAMP,
        created_by VARCHAR(255),
        title TEXT,
        source_path TEXT,
        content_size INTEGER
    ) AS $$
    BEGIN
        RETURN QUERY
        WITH latest_versions AS (
            SELECT 
                dv.document_id,
                dv.id AS version_id,
                dv.version_number,
                dv.content_hash,
                dv.commit_date AS modified_at,
                d.service_name AS created_by,
                d.file_path AS title,
                d.file_path AS source_path,
                LENGTH(dv.content) AS content_size,
                ROW_NUMBER() OVER (
                    PARTITION BY dv.document_id 
                    ORDER BY dv.commit_date DESC
                ) AS rn
            FROM document_versions dv
            INNER JOIN documents d ON d.id = dv.document_id
            WHERE dv.commit_date <= query_time
        )
        SELECT 
            lv.document_id,
            lv.version_id,
            lv.version_number,
            lv.content_hash,
            lv.modified_at,
            lv.created_by,
            lv.title,
            lv.source_path,
            lv.content_size
        FROM latest_versions lv
        WHERE lv.rn = 1
        ORDER BY lv.modified_at DESC;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)
    
    # Function 2: Get document timeline
    op.execute("""
    CREATE OR REPLACE FUNCTION get_document_timeline(doc_id UUID)
    RETURNS TABLE (
        version_id INTEGER,
        version_number INTEGER,
        event_timestamp TIMESTAMP,
        event_type VARCHAR(50),
        actor VARCHAR(255),
        content_hash VARCHAR(64),
        title TEXT,
        is_latest BOOLEAN
    ) AS $$
    BEGIN
        RETURN QUERY
        WITH numbered_versions AS (
            SELECT 
                dv.id AS version_id,
                dv.version_number,
                dv.commit_date AS event_timestamp,
                CASE 
                    WHEN dv.version_number = 1 THEN 'created'
                    ELSE 'updated'
                END AS event_type,
                d.service_name AS actor,
                dv.content_hash,
                d.file_path AS title,
                (ROW_NUMBER() OVER (ORDER BY dv.commit_date DESC) = 1) AS is_latest
            FROM document_versions dv
            INNER JOIN documents d ON d.id = dv.document_id
            WHERE dv.document_id = doc_id
        )
        SELECT 
            nv.version_id,
            nv.version_number,
            nv.event_timestamp,
            nv.event_type::VARCHAR(50),
            nv.actor,
            nv.content_hash,
            nv.title,
            nv.is_latest
        FROM numbered_versions nv
        ORDER BY nv.version_number ASC;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)
    
    # Add indexes for better performance
    op.create_index(
        'idx_document_versions_document_commit',
        'document_versions',
        ['document_id', 'commit_date'],
        unique=False
    )


def downgrade() -> None:
    """Drop temporal query functions."""
    op.execute("DROP FUNCTION IF EXISTS get_document_timeline(UUID);")
    op.execute("DROP FUNCTION IF EXISTS get_all_documents_as_of(TIMESTAMP WITH TIME ZONE);")
    op.drop_index('idx_document_versions_document_commit', table_name='document_versions')

