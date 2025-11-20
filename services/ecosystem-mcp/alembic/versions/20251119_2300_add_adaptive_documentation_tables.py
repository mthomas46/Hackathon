"""Add adaptive documentation tables

Revision ID: adaptive_doc_001
Revises: temporal_001
Create Date: 2025-11-19 23:00:00.000000+00:00

This migration adds 5 new tables for adaptive documentation generation:
- documentation_templates: User-supplied and system templates
- template_execution_history: Template usage and quality tracking
- prompt_execution_history: Prompt effectiveness tracking
- documentation_citations: Source attribution for transparency
- generation_transparency_log: Full audit trail of generation process
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision: str = 'adaptive_doc_001'
down_revision: Union[str, None] = 'temporal_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create adaptive documentation tables."""
    
    # 1. Create documentation_templates table
    op.create_table(
        'documentation_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        
        # Template structure
        sa.Column('structure', JSONB, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('target_framework', sa.String(100)),
        sa.Column('target_audience', sa.String(50)),
        sa.Column('render_options', JSONB),
        
        # Usage tracking
        sa.Column('usage_count', sa.Integer, server_default='0'),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
        
        # Ownership
        sa.Column('created_by', sa.String(255)),
        sa.Column('is_system_template', sa.Boolean, server_default='false'),
        sa.Column('is_public', sa.Boolean, server_default='false'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        
        sa.CheckConstraint(
            "category IN ('api_reference', 'runbook', 'architecture', 'component', 'user_guide', 'deployment', 'troubleshooting', 'security')",
            name='ck_doc_template_category'
        )
    )
    
    op.create_index('idx_doc_templates_category', 'documentation_templates', ['category'])
    op.create_index('idx_doc_templates_active', 'documentation_templates', ['is_active'])
    op.create_index('idx_doc_templates_framework', 'documentation_templates', ['target_framework'])
    op.create_index('idx_doc_templates_name', 'documentation_templates', ['name'])
    
    # 2. Create template_execution_history table
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
    
    # 3. Create prompt_execution_history table
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
    
    # 4. Create documentation_citations table
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
    
    # 5. Create generation_transparency_log table
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


def downgrade() -> None:
    """Drop adaptive documentation tables."""
    
    # Drop in reverse order due to foreign key constraints
    op.drop_index('idx_transparency_sequence', table_name='generation_transparency_log')
    op.drop_index('idx_transparency_phase', table_name='generation_transparency_log')
    op.drop_index('idx_transparency_run', table_name='generation_transparency_log')
    op.drop_table('generation_transparency_log')
    
    op.drop_index('idx_citations_section', table_name='documentation_citations')
    op.drop_index('idx_citations_document', table_name='documentation_citations')
    op.drop_index('idx_citations_artifact', table_name='documentation_citations')
    op.drop_table('documentation_citations')
    
    op.drop_index('idx_prompt_history_template', table_name='prompt_execution_history')
    op.drop_index('idx_prompt_history_effectiveness', table_name='prompt_execution_history')
    op.drop_index('idx_prompt_history_run', table_name='prompt_execution_history')
    op.drop_table('prompt_execution_history')
    
    op.drop_index('idx_template_exec_quality', table_name='template_execution_history')
    op.drop_index('idx_template_exec_run', table_name='template_execution_history')
    op.drop_index('idx_template_exec_template', table_name='template_execution_history')
    op.drop_table('template_execution_history')
    
    op.drop_index('idx_doc_templates_name', table_name='documentation_templates')
    op.drop_index('idx_doc_templates_framework', table_name='documentation_templates')
    op.drop_index('idx_doc_templates_active', table_name='documentation_templates')
    op.drop_index('idx_doc_templates_category', table_name='documentation_templates')
    op.drop_table('documentation_templates')

