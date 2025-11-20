"""Add documentation_citations table

This migration creates the documentation_citations table for tracking
source documents used in generated documentation for transparency.

Revision ID: 017
Revises: 016
Create Date: 2025-11-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    """Create documentation_citations table."""
    
    op.create_table(
        'documentation_citations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('artifact_id', UUID(as_uuid=True), sa.ForeignKey('documentation_artifacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('section_name', sa.String(255)),
        sa.Column('relevance_score', sa.Float, nullable=False),
        
        sa.Column('excerpt', sa.Text),
        sa.Column('start_line', sa.Integer),
        sa.Column('end_line', sa.Integer),
        
        sa.Column('citation_text', sa.Text),
        sa.Column('citation_order', sa.Integer),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        
        sa.CheckConstraint('relevance_score >= 0 AND relevance_score <= 1', name='ck_relevance_score')
    )
    
    op.create_index('idx_citations_artifact', 'documentation_citations', ['artifact_id'])
    op.create_index('idx_citations_document', 'documentation_citations', ['document_id'])
    op.create_index('idx_citations_section', 'documentation_citations', ['artifact_id', 'section_name'])


def downgrade():
    """Drop documentation_citations table."""
    
    op.drop_index('idx_citations_section', table_name='documentation_citations')
    op.drop_index('idx_citations_document', table_name='documentation_citations')
    op.drop_index('idx_citations_artifact', table_name='documentation_citations')
    op.drop_table('documentation_citations')

