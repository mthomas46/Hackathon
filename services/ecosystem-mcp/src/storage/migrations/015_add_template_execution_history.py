"""Add template_execution_history table

This migration creates the template_execution_history table for tracking
template usage, quality metrics, and validation results.

Revision ID: 015
Revises: 014
Create Date: 2025-11-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade():
    """Create template_execution_history table."""
    
    op.create_table(
        'template_execution_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('template_id', UUID(as_uuid=True), sa.ForeignKey('documentation_templates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('run_id', UUID(as_uuid=True), sa.ForeignKey('documentation_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('artifact_id', UUID(as_uuid=True), sa.ForeignKey('documentation_artifacts.id', ondelete='CASCADE')),
        
        sa.Column('section_name', sa.String(255)),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        
        sa.Column('completeness_score', sa.Float),
        sa.Column('adherence_score', sa.Float),
        sa.Column('user_rating', sa.Integer),
        
        sa.Column('validation_errors', JSONB),
        sa.Column('rendering_errors', JSONB),
        
        sa.CheckConstraint('completeness_score IS NULL OR (completeness_score >= 0 AND completeness_score <= 1)', name='ck_completeness_score'),
        sa.CheckConstraint('adherence_score IS NULL OR (adherence_score >= 0 AND adherence_score <= 1)', name='ck_adherence_score'),
        sa.CheckConstraint('user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5)', name='ck_user_rating')
    )
    
    op.create_index('idx_template_exec_template', 'template_execution_history', ['template_id'])
    op.create_index('idx_template_exec_run', 'template_execution_history', ['run_id'])
    op.create_index('idx_template_exec_quality', 'template_execution_history', ['completeness_score', 'adherence_score'])


def downgrade():
    """Drop template_execution_history table."""
    
    op.drop_index('idx_template_exec_quality', table_name='template_execution_history')
    op.drop_index('idx_template_exec_run', table_name='template_execution_history')
    op.drop_index('idx_template_exec_template', table_name='template_execution_history')
    op.drop_table('template_execution_history')

