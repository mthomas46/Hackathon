**Date:** November 19, 2025  
**Status:** 🤖 **LLM AGENT EXECUTABLE** - Phased Implementation Guide  
**Purpose:** Step-by-step implementation with execution tracking and context preservation  

---

# Adaptive Documentation System: Agent-Executable Implementation Guide

## 🎯 Document Purpose

This document is designed to be:
- ✅ **Executable by LLM agents** - Clear, unambiguous steps
- ✅ **Resumable** - Can pause and resume across chat sessions
- ✅ **Self-tracking** - Built-in progress tracking
- ✅ **Self-verifying** - Validation after each step
- ✅ **Rollback-capable** - Can undo changes if needed

---

## 📊 Execution Tracking System

### **Tracking File Location**
```
/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/.implementation-state.yaml
```

### **State Structure**
```yaml
# Execution State
execution:
  started_at: "2025-11-19T18:00:00Z"
  last_updated: "2025-11-19T18:30:00Z"
  current_phase: 1
  current_task: "1.1"
  status: "in_progress"  # not_started, in_progress, paused, completed, failed
  
# Phase Tracking
phases:
  phase_1:
    name: "Database Schema & Models"
    status: "in_progress"
    started_at: "2025-11-19T18:00:00Z"
    completed_at: null
    tasks:
      task_1_1:
        name: "Create migration for documentation_templates table"
        status: "completed"
        completed_at: "2025-11-19T18:15:00Z"
        verification: "passed"
        rollback_available: true
      task_1_2:
        name: "Create migration for template_execution_history table"
        status: "in_progress"
        started_at: "2025-11-19T18:16:00Z"
        verification: null
        rollback_available: false
  
  phase_2:
    name: "Template System Implementation"
    status: "not_started"
    tasks: {}

# Context Preservation
context:
  repository_path: "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp"
  database_connection: "postgresql://localhost:5432/ecosystem_mcp"
  docker_compose_path: "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/docker-compose.yml"
  
  files_created: []
  files_modified: []
  
  database_migrations_applied: []
  
  errors_encountered: []
  
  notes: []

# Verification Results
verifications:
  - task: "1.1"
    timestamp: "2025-11-19T18:15:00Z"
    result: "passed"
    details: "Migration file created successfully"
  
# Rollback Points
rollback_points:
  - phase: 1
    task: "1.1"
    timestamp: "2025-11-19T18:15:00Z"
    description: "Before creating documentation_templates table"
    files_backup: []
    database_backup: null
```

---

## 🏗️ Implementation Phases

### **Phase 1: Database Schema & Models** (Week 1-2)
**Estimated Time:** 2 days  
**Prerequisites:** PostgreSQL running, SQLAlchemy installed  
**Rollback Risk:** 🟢 Low (migrations are reversible)

**Phase 2: Template System Core** (Week 3-4)
**Estimated Time:** 5 days  
**Prerequisites:** Phase 1 complete  
**Rollback Risk:** 🟡 Medium

**Phase 3: Adaptive Features** (Week 5-6)
**Estimated Time:** 10 days  
**Prerequisites:** Phase 1-2 complete  
**Rollback Risk:** 🟡 Medium

**Phase 4: Integration** (Week 7-8)
**Estimated Time:** 10 days  
**Prerequisites:** Phase 1-3 complete  
**Rollback Risk:** 🟡 Medium

**Phase 5: Dashboard UI** (Week 9-10)
**Estimated Time:** 5 days  
**Prerequisites:** Phase 1-4 complete  
**Rollback Risk:** 🟢 Low

**Phase 6: Testing & Polish** (Week 11-12)
**Estimated Time:** 10 days  
**Prerequisites:** All phases complete  
**Rollback Risk:** 🟢 Low

---

## 📋 PHASE 1: Database Schema & Models

### **Overview**
Create 5 new database tables and extend 3 existing JSONB fields.

### **Tasks**

---

#### **Task 1.1: Create Migration for `documentation_templates` Table**

**Objective:** Create database migration for storing user-supplied documentation templates

**Prerequisites:**
- ✅ PostgreSQL running
- ✅ Alembic installed
- ✅ Access to migrations directory

**Steps:**

1. **Navigate to migrations directory**
   ```bash
   cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/src/storage/migrations
   ```

2. **Create migration file**
   ```bash
   # File: 013_add_documentation_templates.py
   ```

3. **Migration Content**
   ```python
   """Add documentation_templates table

   Revision ID: 013
   Revises: 012
   Create Date: 2025-11-19

   """
   from alembic import op
   import sqlalchemy as sa
   from sqlalchemy.dialects.postgresql import UUID, JSONB

   # Revision identifiers
   revision = '013'
   down_revision = '012'
   branch_labels = None
   depends_on = None

   def upgrade():
       # Create documentation_templates table
       op.create_table(
           'documentation_templates',
           sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
           sa.Column('name', sa.String(255), nullable=False, unique=True),
           sa.Column('category', sa.String(100), nullable=False),
           sa.Column('version', sa.Integer, nullable=False, default=1),
           sa.Column('is_active', sa.Boolean, default=True),
           
           # Template structure
           sa.Column('structure', JSONB, nullable=False),
           sa.Column('description', sa.Text),
           sa.Column('target_framework', sa.String(100)),
           sa.Column('target_audience', sa.String(50)),
           sa.Column('render_options', JSONB),
           
           # Usage tracking
           sa.Column('usage_count', sa.Integer, default=0),
           sa.Column('last_used_at', sa.DateTime(timezone=True)),
           
           # Ownership
           sa.Column('created_by', sa.String(255)),
           sa.Column('is_system_template', sa.Boolean, default=False),
           sa.Column('is_public', sa.Boolean, default=False),
           
           # Timestamps
           sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
           sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
           
           sa.CheckConstraint(
               "category IN ('api_reference', 'runbook', 'architecture', 'component', 'user_guide', 'deployment', 'troubleshooting', 'security')",
               name='valid_category'
           )
       )
       
       # Create indexes
       op.create_index('idx_doc_templates_category', 'documentation_templates', ['category'])
       op.create_index('idx_doc_templates_active', 'documentation_templates', ['is_active'])
       op.create_index('idx_doc_templates_framework', 'documentation_templates', ['target_framework'])

   def downgrade():
       op.drop_index('idx_doc_templates_framework', table_name='documentation_templates')
       op.drop_index('idx_doc_templates_active', table_name='documentation_templates')
       op.drop_index('idx_doc_templates_category', table_name='documentation_templates')
       op.drop_table('documentation_templates')
   ```

**Verification Steps:**

1. **Check file created**
   ```bash
   ls -la /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/src/storage/migrations/013_add_documentation_templates.py
   ```
   **Expected:** File exists

2. **Validate Python syntax**
   ```bash
   python -m py_compile /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/src/storage/migrations/013_add_documentation_templates.py
   ```
   **Expected:** No errors

3. **Test migration (dry-run)**
   ```bash
   cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
   docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "\d documentation_templates" 2>&1 | grep "does not exist"
   ```
   **Expected:** Table doesn't exist yet (we haven't run migration)

**Rollback:**
```bash
# If needed, delete the migration file
rm /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/src/storage/migrations/013_add_documentation_templates.py
```

**Update State:**
```yaml
task_1_1:
  status: "completed"
  completed_at: "<timestamp>"
  verification: "passed"
  rollback_available: true
  files_created:
    - "src/storage/migrations/013_add_documentation_templates.py"
```

**Estimated Time:** 15 minutes

---

#### **Task 1.2: Create Migration for `template_execution_history` Table**

**Objective:** Create table to track template usage and quality

**Prerequisites:**
- ✅ Task 1.1 completed

**Steps:**

1. **Create migration file**
   ```bash
   # File: 014_add_template_execution_history.py
   ```

2. **Migration Content**
   ```python
   """Add template_execution_history table

   Revision ID: 014
   Revises: 013
   Create Date: 2025-11-19

   """
   from alembic import op
   import sqlalchemy as sa
   from sqlalchemy.dialects.postgresql import UUID, JSONB

   revision = '014'
   down_revision = '013'
   branch_labels = None
   depends_on = None

   def upgrade():
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
           
           sa.CheckConstraint('completeness_score IS NULL OR completeness_score BETWEEN 0 AND 1', name='valid_completeness'),
           sa.CheckConstraint('adherence_score IS NULL OR adherence_score BETWEEN 0 AND 1', name='valid_adherence'),
           sa.CheckConstraint('user_rating IS NULL OR user_rating BETWEEN 1 AND 5', name='valid_rating')
       )
       
       op.create_index('idx_template_exec_template', 'template_execution_history', ['template_id'])
       op.create_index('idx_template_exec_run', 'template_execution_history', ['run_id'])
       op.create_index('idx_template_exec_quality', 'template_execution_history', ['completeness_score', 'adherence_score'])

   def downgrade():
       op.drop_index('idx_template_exec_quality', table_name='template_execution_history')
       op.drop_index('idx_template_exec_run', table_name='template_execution_history')
       op.drop_index('idx_template_exec_template', table_name='template_execution_history')
       op.drop_table('template_execution_history')
   ```

**Verification:** Same as Task 1.1

**Estimated Time:** 15 minutes

---

#### **Task 1.3: Create Migration for `prompt_execution_history` Table**

**Objective:** Track prompt effectiveness for continuous improvement

**Migration Content:**
```python
"""Add prompt_execution_history table

Revision ID: 015
Revises: 014

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '015'
down_revision = '014'

def upgrade():
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
        
        sa.CheckConstraint('effectiveness_score IS NULL OR effectiveness_score BETWEEN 0 AND 1', name='valid_effectiveness'),
        sa.CheckConstraint('specificity_score IS NULL OR specificity_score BETWEEN 0 AND 1', name='valid_specificity')
    )
    
    op.create_index('idx_prompt_history_run', 'prompt_execution_history', ['run_id'])
    op.create_index('idx_prompt_history_effectiveness', 'prompt_execution_history', ['effectiveness_score'])
    op.create_index('idx_prompt_history_template', 'prompt_execution_history', ['prompt_template'])

def downgrade():
    op.drop_index('idx_prompt_history_template', table_name='prompt_execution_history')
    op.drop_index('idx_prompt_history_effectiveness', table_name='prompt_execution_history')
    op.drop_index('idx_prompt_history_run', table_name='prompt_execution_history')
    op.drop_table('prompt_execution_history')
```

**Estimated Time:** 15 minutes

---

#### **Task 1.4: Create Migration for `documentation_citations` Table**

**Objective:** Enable source tracing and transparency

**Migration Content:**
```python
"""Add documentation_citations table

Revision ID: 016
Revises: 015

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '016'
down_revision = '015'

def upgrade():
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
        
        sa.CheckConstraint('relevance_score BETWEEN 0 AND 1', name='valid_relevance')
    )
    
    op.create_index('idx_citations_artifact', 'documentation_citations', ['artifact_id'])
    op.create_index('idx_citations_document', 'documentation_citations', ['document_id'])
    op.create_index('idx_citations_section', 'documentation_citations', ['artifact_id', 'section_name'])

def downgrade():
    op.drop_index('idx_citations_section', table_name='documentation_citations')
    op.drop_index('idx_citations_document', table_name='documentation_citations')
    op.drop_index('idx_citations_artifact', table_name='documentation_citations')
    op.drop_table('documentation_citations')
```

**Estimated Time:** 15 minutes

---

#### **Task 1.5: Create Migration for `generation_transparency_log` Table**

**Objective:** Full audit trail of documentation generation

**Migration Content:**
```python
"""Add generation_transparency_log table

Revision ID: 017
Revises: 016

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '017'
down_revision = '016'

def upgrade():
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
        
        sa.Column('status', sa.String(20), nullable=False, default='success'),
        sa.Column('error_message', sa.Text),
        
        sa.CheckConstraint("status IN ('success', 'failed', 'skipped')", name='valid_status')
    )
    
    op.create_index('idx_transparency_run', 'generation_transparency_log', ['run_id'])
    op.create_index('idx_transparency_phase', 'generation_transparency_log', ['run_id', 'phase'])
    op.create_index('idx_transparency_sequence', 'generation_transparency_log', ['run_id', 'sequence_number'])

def downgrade():
    op.drop_index('idx_transparency_sequence', table_name='generation_transparency_log')
    op.drop_index('idx_transparency_phase', table_name='generation_transparency_log')
    op.drop_index('idx_transparency_run', table_name='generation_transparency_log')
    op.drop_table('generation_transparency_log')
```

**Estimated Time:** 15 minutes

---

#### **Task 1.6: Apply All Migrations**

**Objective:** Apply all 5 new migrations to database

**Prerequisites:**
- ✅ Tasks 1.1-1.5 completed
- ✅ PostgreSQL container running
- ✅ No syntax errors in migrations

**Steps:**

1. **Backup database (safety)**
   ```bash
   docker exec ecosystem-mcp-postgres pg_dump -U ecosystem -d ecosystem_mcp -F c -f /tmp/backup_before_migrations.dump
   ```

2. **Apply migrations**
   ```bash
   cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
   
   # Method 1: Using Alembic (if configured)
   alembic upgrade head
   
   # Method 2: Direct SQL execution
   for file in src/storage/migrations/01{3,4,5,6,7}_*.py; do
       python -c "
   import sys
   sys.path.insert(0, 'src')
   from storage.migrations.$(basename $file .py) import upgrade
   from storage.database import get_database
   db = get_database()
   upgrade()
   "
   done
   ```

3. **Verify tables created**
   ```bash
   docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "
   SELECT table_name FROM information_schema.tables 
   WHERE table_name IN (
       'documentation_templates',
       'template_execution_history',
       'prompt_execution_history',
       'documentation_citations',
       'generation_transparency_log'
   );"
   ```
   **Expected:** All 5 tables listed

4. **Verify indexes created**
   ```bash
   docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "
   SELECT indexname FROM pg_indexes 
   WHERE indexname LIKE 'idx_doc_templates_%' 
      OR indexname LIKE 'idx_template_exec_%'
      OR indexname LIKE 'idx_prompt_history_%'
      OR indexname LIKE 'idx_citations_%'
      OR indexname LIKE 'idx_transparency_%';"
   ```
   **Expected:** All indexes listed

**Verification Steps:**

1. **Check table schemas**
   ```bash
   docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "\d documentation_templates"
   ```
   **Expected:** Shows correct columns and constraints

2. **Test insert (rollback after)**
   ```bash
   docker exec ecosystem-mcp-postgres psql -U ecosystem -d ecosystem_mcp -c "
   BEGIN;
   INSERT INTO documentation_templates (name, category, structure) 
   VALUES ('test_template', 'api_reference', '{}');
   SELECT * FROM documentation_templates WHERE name = 'test_template';
   ROLLBACK;
   "
   ```
   **Expected:** Insert succeeds, rollback succeeds

**Rollback:**
```bash
# Rollback all migrations
alembic downgrade -1  # One at a time
# OR
alembic downgrade 012  # Back to revision 012

# Restore from backup if needed
docker exec -i ecosystem-mcp-postgres pg_restore -U ecosystem -d ecosystem_mcp -c /tmp/backup_before_migrations.dump
```

**Update State:**
```yaml
task_1_6:
  status: "completed"
  verification: "passed"
  database_migrations_applied:
    - "013_add_documentation_templates"
    - "014_add_template_execution_history"
    - "015_add_prompt_execution_history"
    - "016_add_documentation_citations"
    - "017_add_generation_transparency_log"
  rollback_available: true
  backup_location: "/tmp/backup_before_migrations.dump"
```

**Estimated Time:** 30 minutes

---

#### **Task 1.7: Create SQLAlchemy Models**

**Objective:** Create Python ORM models for new tables

**Steps:**

1. **Create models file**
   ```bash
   # File: src/storage/models_templates.py
   ```

2. **Model Content**
   ```python
   """
   SQLAlchemy Models for Documentation Templates
   
   New models for adaptive documentation generation.
   """
   
   from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, CheckConstraint
   from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
   from sqlalchemy.orm import relationship
   from datetime import datetime
   import uuid
   
   from .db_models import Base
   
   
   class DocumentationTemplateModel(Base):
       """User-supplied documentation templates."""
       __tablename__ = "documentation_templates"
       
       id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       name = Column(String(255), nullable=False, unique=True)
       category = Column(String(100), nullable=False)
       version = Column(Integer, nullable=False, default=1)
       is_active = Column(Boolean, default=True)
       
       structure = Column(JSONB, nullable=False)
       description = Column(Text)
       target_framework = Column(String(100))
       target_audience = Column(String(50))
       render_options = Column(JSONB)
       
       usage_count = Column(Integer, default=0)
       last_used_at = Column(DateTime(timezone=True))
       
       created_by = Column(String(255))
       is_system_template = Column(Boolean, default=False)
       is_public = Column(Boolean, default=False)
       
       created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
       updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
       
       # Relationships
       executions = relationship("TemplateExecutionHistoryModel", back_populates="template", cascade="all, delete-orphan")
       
       __table_args__ = (
           CheckConstraint(
               "category IN ('api_reference', 'runbook', 'architecture', 'component', 'user_guide', 'deployment', 'troubleshooting', 'security')",
               name="valid_category"
           ),
       )
   
   
   class TemplateExecutionHistoryModel(Base):
       """Track template usage and quality."""
       __tablename__ = "template_execution_history"
       
       id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       template_id = Column(PGUUID(as_uuid=True), ForeignKey("documentation_templates.id", ondelete="CASCADE"), nullable=False)
       run_id = Column(PGUUID(as_uuid=True), ForeignKey("documentation_runs.id", ondelete="CASCADE"), nullable=False)
       artifact_id = Column(PGUUID(as_uuid=True), ForeignKey("documentation_artifacts.id", ondelete="CASCADE"))
       
       section_name = Column(String(255))
       executed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
       
       completeness_score = Column(Float)
       adherence_score = Column(Float)
       user_rating = Column(Integer)
       
       validation_errors = Column(JSONB)
       rendering_errors = Column(JSONB)
       
       # Relationships
       template = relationship("DocumentationTemplateModel", back_populates="executions")
       
       __table_args__ = (
           CheckConstraint("completeness_score IS NULL OR completeness_score BETWEEN 0 AND 1", name="valid_completeness"),
           CheckConstraint("adherence_score IS NULL OR adherence_score BETWEEN 0 AND 1", name="valid_adherence"),
           CheckConstraint("user_rating IS NULL OR user_rating BETWEEN 1 AND 5", name="valid_rating"),
       )
   
   
   class PromptExecutionHistoryModel(Base):
       """Track prompt effectiveness."""
       __tablename__ = "prompt_execution_history"
       
       id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       run_id = Column(PGUUID(as_uuid=True), ForeignKey("documentation_runs.id", ondelete="CASCADE"), nullable=False)
       
       prompt_template = Column(String(255))
       prompt_used = Column(Text, nullable=False)
       context_provided = Column(JSONB)
       
       pass_number = Column(Integer)
       section_name = Column(String(100))
       executed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
       
       response_length = Column(Integer)
       tokens_used = Column(Integer)
       sources_used = Column(JSONB)
       
       effectiveness_score = Column(Float)
       specificity_score = Column(Float)
       code_examples_count = Column(Integer)
       
       findings = Column(JSONB)
       
       __table_args__ = (
           CheckConstraint("effectiveness_score IS NULL OR effectiveness_score BETWEEN 0 AND 1", name="valid_effectiveness"),
           CheckConstraint("specificity_score IS NULL OR specificity_score BETWEEN 0 AND 1", name="valid_specificity"),
       )
   
   
   class DocumentationCitationModel(Base):
       """Source citations for generated documentation."""
       __tablename__ = "documentation_citations"
       
       id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       artifact_id = Column(PGUUID(as_uuid=True), ForeignKey("documentation_artifacts.id", ondelete="CASCADE"), nullable=False)
       document_id = Column(PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
       
       section_name = Column(String(255))
       relevance_score = Column(Float, nullable=False)
       
       excerpt = Column(Text)
       start_line = Column(Integer)
       end_line = Column(Integer)
       
       citation_text = Column(Text)
       citation_order = Column(Integer)
       
       created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
       
       __table_args__ = (
           CheckConstraint("relevance_score BETWEEN 0 AND 1", name="valid_relevance"),
       )
   
   
   class GenerationTransparencyLogModel(Base):
       """Audit trail for documentation generation."""
       __tablename__ = "generation_transparency_log"
       
       id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       run_id = Column(PGUUID(as_uuid=True), ForeignKey("documentation_runs.id", ondelete="CASCADE"), nullable=False)
       
       phase = Column(String(100), nullable=False)
       sequence_number = Column(Integer, nullable=False)
       
       action_type = Column(String(50), nullable=False)
       action_description = Column(Text, nullable=False)
       
       input_data = Column(JSONB)
       output_data = Column(JSONB)
       
       started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
       completed_at = Column(DateTime(timezone=True))
       duration_ms = Column(Integer)
       
       status = Column(String(20), nullable=False, default='success')
       error_message = Column(Text)
       
       __table_args__ = (
           CheckConstraint("status IN ('success', 'failed', 'skipped')", name="valid_status"),
       )
   ```

**Verification:**
```bash
python -m py_compile src/storage/models_templates.py
python -c "from src.storage.models_templates import *; print('Models imported successfully')"
```

**Estimated Time:** 30 minutes

---

#### **Phase 1 Completion Checklist**

**Before marking Phase 1 complete, verify:**

- [ ] All 5 migration files created
- [ ] All migrations applied successfully
- [ ] All 5 tables exist in database
- [ ] All indexes created
- [ ] SQLAlchemy models created
- [ ] Models can be imported without errors
- [ ] Test insert/select works for each table
- [ ] Backup created before migrations
- [ ] State file updated with all tasks

**Phase 1 Duration:** 2 hours 15 minutes

---

## 🔄 Session Management

### **Starting a New Session**

1. **Load state file**
   ```bash
   cat .implementation-state.yaml
   ```

2. **Identify current task**
   ```yaml
   current_phase: 1
   current_task: "1.6"
   status: "in_progress"
   ```

3. **Resume from current task**

### **Ending a Session**

1. **Update state file**
   ```yaml
   status: "paused"
   last_updated: "<current_timestamp>"
   notes:
     - "Paused after completing task 1.6"
     - "Next: Start task 1.7"
   ```

2. **Commit progress**
   ```bash
   git add .implementation-state.yaml
   git commit -m "Implementation progress: Completed Phase 1 Task 1.6"
   ```

### **Error Handling**

If error occurs:

1. **Log error**
   ```yaml
   errors_encountered:
     - task: "1.6"
       timestamp: "<timestamp>"
       error: "Migration failed: syntax error"
       resolution: "Fixed syntax, retried successfully"
   ```

2. **Attempt rollback if needed**
3. **Fix issue**
4. **Retry task**
5. **Update state**

---

## 📊 Progress Tracking Commands

### **View Current Status**
```bash
yq eval '.execution.status' .implementation-state.yaml
yq eval '.execution.current_phase' .implementation-state.yaml
yq eval '.execution.current_task' .implementation-state.yaml
```

### **View Phase Summary**
```bash
yq eval '.phases.phase_1' .implementation-state.yaml
```

### **View Task Status**
```bash
yq eval '.phases.phase_1.tasks.task_1_6' .implementation-state.yaml
```

### **View Errors**
```bash
yq eval '.context.errors_encountered' .implementation-state.yaml
```

---

## 🧪 Testing Framework

### **Unit Tests for Phase 1**

**Test File:** `tests/test_phase1_models.py`

```python
"""
Unit tests for Phase 1: Database models
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.storage.models_templates import (
    DocumentationTemplateModel,
    TemplateExecutionHistoryModel,
    PromptExecutionHistoryModel,
    DocumentationCitationModel,
    GenerationTransparencyLogModel
)


@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("postgresql://ecosystem:password@localhost:5432/ecosystem_mcp_test")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


def test_create_documentation_template(db_session):
    """Test creating a documentation template."""
    template = DocumentationTemplateModel(
        name="test_api_template",
        category="api_reference",
        structure={
            "sections": [
                {"name": "Overview", "order": 1, "required": True}
            ]
        },
        created_by="test_user"
    )
    
    db_session.add(template)
    db_session.commit()
    
    assert template.id is not None
    assert template.name == "test_api_template"
    assert template.category == "api_reference"
    assert template.is_active is True


def test_template_category_constraint(db_session):
    """Test category constraint validation."""
    template = DocumentationTemplateModel(
        name="test_invalid_category",
        category="invalid_category",
        structure={}
    )
    
    db_session.add(template)
    
    with pytest.raises(Exception):  # Constraint violation
        db_session.commit()


def test_template_execution_history(db_session):
    """Test template execution tracking."""
    # Create template first
    template = DocumentationTemplateModel(
        name="test_template",
        category="api_reference",
        structure={}
    )
    db_session.add(template)
    db_session.flush()
    
    # Create execution history
    execution = TemplateExecutionHistoryModel(
        template_id=template.id,
        run_id="00000000-0000-0000-0000-000000000001",  # Dummy UUID
        section_name="Overview",
        adherence_score=0.95
    )
    
    db_session.add(execution)
    db_session.commit()
    
    assert execution.id is not None
    assert execution.template_id == template.id
    assert execution.adherence_score == 0.95


# Add more tests for each model...
```

**Run Tests:**
```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
pytest tests/test_phase1_models.py -v
```

---

## 📝 Implementation Notes for LLM Agent

### **Agent Capabilities Required**

1. ✅ **File Creation** - Create Python files, YAML files
2. ✅ **Database Operations** - Run SQL via psql
3. ✅ **Command Execution** - Run bash commands
4. ✅ **State Management** - Read/write YAML state file
5. ✅ **Error Handling** - Catch errors, log, retry
6. ✅ **Verification** - Run test commands, check output
7. ✅ **Context Preservation** - Maintain state across sessions

### **Agent Decision Points**

**At each task:**
1. Read current state
2. Verify prerequisites met
3. Execute task steps
4. Run verification
5. Update state
6. Continue or pause

**On error:**
1. Log error details
2. Attempt automatic fix if possible
3. Otherwise, mark task as "blocked"
4. Request human intervention

### **Agent Autonomy Levels**

- **Level 1 (Autonomous):** Tasks 1.1-1.5 (file creation)
- **Level 2 (Semi-Autonomous):** Task 1.6 (apply migrations - verify first)
- **Level 3 (Supervised):** Later phases (require approval)

---

## 🚀 Ready to Begin

This document is now ready for LLM agent execution.

**Next Steps:**
1. Create state file (`.implementation-state.yaml`)
2. Begin Phase 1, Task 1.1
3. Track progress in state file
4. Verify each task before proceeding
5. Continue to Phase 2 after Phase 1 complete

**Estimated Total Time:**
- Phase 1: 2-3 days
- Phases 2-6: 10-12 weeks
- Total: ~12 weeks

---

**Document Status:** ✅ **READY FOR EXECUTION**  
**Agent-Executable:** ✅ **YES**  
**Resumable:** ✅ **YES**  
**Self-Verifying:** ✅ **YES**

