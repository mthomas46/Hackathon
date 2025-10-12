"""Initial schema complete

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2025-10-12 00:00:00.000000+00:00

This migration creates all tables for the ecosystem-mcp service:
- documents: Core document storage with versioning
- document_versions: Historical versions of documents
- embeddings: Embedding metadata (vectors in ChromaDB)
- git_commits: Git commit metadata cache
- ingestion_jobs: Job tracking for ingestion pipeline
- model_requests: AI model request tracking for cost/monitoring

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for ecosystem-mcp service."""
    
    # Create git_commits table first (referenced by documents)
    op.create_table(
        'git_commits',
        sa.Column('sha', sa.String(length=40), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=False),
        sa.Column('author_email', sa.String(length=255), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('commit_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('sha'),
        sa.Index('idx_commits_date', 'date'),
        sa.Index('idx_commits_author', 'author'),
    )
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('original_format', sa.String(length=50), nullable=False),
        sa.Column('original_content', sa.Text(), nullable=False),
        sa.Column('normalized_content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('git_commit_sha', sa.String(length=40), nullable=True),
        sa.Column('is_latest', sa.Boolean(), nullable=False),
        sa.Column('embedding_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('doc_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(['git_commit_sha'], ['git_commits.sha'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_path', 'git_commit_sha', name='uq_document_file_commit'),
        sa.Index('idx_documents_service_latest', 'service_name', 'is_latest'),
        sa.Index('idx_documents_content_hash', 'content_hash'),
    )
    
    # Create embeddings table
    op.create_table(
        'embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chroma_id', sa.String(length=255), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('dimensions', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Float(), nullable=False),
        sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chroma_id'),
        sa.CheckConstraint('dimensions > 0', name='ck_dimensions_positive'),
        sa.CheckConstraint('token_count >= 0', name='ck_token_count_nonnegative'),
        sa.CheckConstraint('cost_usd >= 0.0', name='ck_cost_nonnegative'),
        sa.Index('idx_embeddings_document', 'document_id'),
        sa.Index('idx_embeddings_model', 'model'),
        sa.Index('idx_embeddings_chroma_id', 'chroma_id'),
    )
    
    # Add foreign key from documents to embeddings
    # (This creates a circular reference which is OK in PostgreSQL)
    op.create_foreign_key(
        'fk_documents_embedding_id',
        'documents',
        'embeddings',
        ['embedding_id'],
        ['id']
    )
    
    # Create document_versions table
    op.create_table(
        'document_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_hash', sa.String(length=64), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_hash'),
        sa.Index('idx_document_versions_document', 'document_id'),
    )
    
    # Create ingestion_jobs table
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mode', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('processed_documents', sa.Integer(), nullable=False),
        sa.Column('total_documents', sa.Integer(), nullable=True),
        sa.Column('failed_documents', sa.Integer(), nullable=False),
        sa.Column('repo_path', sa.Text(), nullable=True),
        sa.Column('embeddings_generated', sa.Integer(), nullable=False),
        sa.Column('total_cost_usd', sa.Float(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('job_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('processed_documents >= 0', name='ck_processed_nonnegative'),
        sa.CheckConstraint('failed_documents >= 0', name='ck_failed_nonnegative'),
        sa.CheckConstraint('embeddings_generated >= 0', name='ck_embeddings_nonnegative'),
        sa.CheckConstraint('total_cost_usd >= 0.0', name='ck_cost_nonnegative'),
        sa.Index('idx_jobs_status_started', 'status', 'started_at'),
        sa.Index('idx_jobs_mode', 'mode'),
    )
    
    # Create model_requests table
    op.create_table(
        'model_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Float(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('input_tokens >= 0', name='ck_input_tokens_nonnegative'),
        sa.CheckConstraint('output_tokens >= 0', name='ck_output_tokens_nonnegative'),
        sa.CheckConstraint('cost_usd >= 0.0', name='ck_cost_nonnegative'),
        sa.CheckConstraint('latency_ms >= 0', name='ck_latency_nonnegative'),
        sa.Index('idx_requests_timestamp', 'timestamp'),
        sa.Index('idx_requests_model_timestamp', 'model', 'timestamp'),
        sa.Index('idx_requests_task_type', 'task_type'),
        sa.Index('idx_requests_success', 'success'),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('model_requests')
    op.drop_table('ingestion_jobs')
    op.drop_table('document_versions')
    
    # Drop foreign key from documents to embeddings first
    op.drop_constraint('fk_documents_embedding_id', 'documents', type_='foreignkey')
    
    op.drop_table('embeddings')
    op.drop_table('documents')
    op.drop_table('git_commits')

