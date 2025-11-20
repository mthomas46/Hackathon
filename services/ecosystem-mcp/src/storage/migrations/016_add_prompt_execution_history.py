"""Add prompt_execution_history table

This migration creates the prompt_execution_history table for tracking
prompt effectiveness, findings, and continuous improvement metrics.

Revision ID: 016
Revises: 015
Create Date: 2025-11-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    """Create prompt_execution_history table."""
    
    op.create_table(
        'prompt_execution_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_id', UUID(as_uuid=True), sa.ForeignKey('documentation_runs.id', ondelete='CASCADE'), nullable=False),
        
        sa.Column('prompt_template', sa.String(255)),
        sa.Column('prompt_used', sa.Text, nullable=False),
        sa.Column('context_provided', JSONB),
        
        sa.Column('pass_number', sa.Integer),
        sa.Column('section_name', sa.String(100)),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        
        sa.Column('response_length', sa.Integer),
        sa.Column('tokens_used', sa.Integer),
        sa.Column('sources_used', JSONB),
        
        sa.Column('effectiveness_score', sa.Float),
        sa.Column('specificity_score', sa.Float),
        sa.Column('code_examples_count', sa.Integer),
        
        sa.Column('findings', JSONB),
        
        sa.CheckConstraint('effectiveness_score IS NULL OR (effectiveness_score >= 0 AND effectiveness_score <= 1)', name='ck_effectiveness_score'),
        sa.CheckConstraint('specificity_score IS NULL OR (specificity_score >= 0 AND specificity_score <= 1)', name='ck_specificity_score')
    )
    
    op.create_index('idx_prompt_history_run', 'prompt_execution_history', ['run_id'])
    op.create_index('idx_prompt_history_effectiveness', 'prompt_execution_history', ['effectiveness_score'])
    op.create_index('idx_prompt_history_template', 'prompt_execution_history', ['prompt_template'])


def downgrade():
    """Drop prompt_execution_history table."""
    
    op.drop_index('idx_prompt_history_template', table_name='prompt_execution_history')
    op.drop_index('idx_prompt_history_effectiveness', table_name='prompt_execution_history')
    op.drop_index('idx_prompt_history_run', table_name='prompt_execution_history')
    op.drop_table('prompt_execution_history')

