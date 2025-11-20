"""Add documentation_templates table

This migration creates the documentation_templates table for storing
user-supplied and system documentation templates.

Revision ID: 014
Revises: 013
Create Date: 2025-11-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# Revision identifiers
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    """Create documentation_templates table."""
    
    # Create documentation_templates table
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
    
    # Create indexes
    op.create_index('idx_doc_templates_category', 'documentation_templates', ['category'])
    op.create_index('idx_doc_templates_active', 'documentation_templates', ['is_active'])
    op.create_index('idx_doc_templates_framework', 'documentation_templates', ['target_framework'])
    op.create_index('idx_doc_templates_name', 'documentation_templates', ['name'])


def downgrade():
    """Drop documentation_templates table."""
    
    op.drop_index('idx_doc_templates_name', table_name='documentation_templates')
    op.drop_index('idx_doc_templates_framework', table_name='documentation_templates')
    op.drop_index('idx_doc_templates_active', table_name='documentation_templates')
    op.drop_index('idx_doc_templates_category', table_name='documentation_templates')
    op.drop_table('documentation_templates')

