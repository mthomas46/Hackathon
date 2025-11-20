"""Add generation_transparency_log table

This migration creates the generation_transparency_log table for tracking
all actions during documentation generation for full audit trail.

Revision ID: 018
Revises: 017
Create Date: 2025-11-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade():
    """Create generation_transparency_log table."""
    
    op.create_table(
        'generation_transparency_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_id', UUID(as_uuid=True), sa.ForeignKey('documentation_runs.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('phase', sa.String(100), nullable=False),
        sa.Column('sequence_number', sa.Integer, nullable=False),
        
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_description', sa.Text, nullable=False),
        
        sa.Column('input_data', JSONB),
        sa.Column('output_data', JSONB),
        
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_ms', sa.Integer),
        
        sa.Column('status', sa.String(20), nullable=False, server_default='success'),
        sa.Column('error_message', sa.Text),
        
        sa.CheckConstraint("status IN ('success', 'failed', 'skipped')", name='ck_log_status')
    )
    
    op.create_index('idx_transparency_run', 'generation_transparency_log', ['run_id'])
    op.create_index('idx_transparency_phase', 'generation_transparency_log', ['run_id', 'phase'])
    op.create_index('idx_transparency_sequence', 'generation_transparency_log', ['run_id', 'sequence_number'])


def downgrade():
    """Drop generation_transparency_log table."""
    
    op.drop_index('idx_transparency_sequence', table_name='generation_transparency_log')
    op.drop_index('idx_transparency_phase', table_name='generation_transparency_log')
    op.drop_index('idx_transparency_run', table_name='generation_transparency_log')
    op.drop_table('generation_transparency_log')

