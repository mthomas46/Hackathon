"""
SQLAlchemy Models for Documentation Templates

New models for adaptive documentation generation system.
Includes templates, execution tracking, prompt history, citations, and transparency logging.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .db_models import Base


class DocumentationTemplateModel(Base):
    """
    User-supplied and system documentation templates.
    
    Stores template structure, validation rules, and usage statistics.
    """
    __tablename__ = "documentation_templates"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template identification
    name = Column(String(255), nullable=False, unique=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True, index=True)
    
    # Template structure (JSONB for flexibility)
    structure = Column(JSONB, nullable=False)
    description = Column(Text)
    target_framework = Column(String(100), index=True)
    target_audience = Column(String(50))
    render_options = Column(JSONB)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    
    # Ownership
    created_by = Column(String(255))
    is_system_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship(
        "TemplateExecutionHistoryModel",
        back_populates="template",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "category IN ('api_reference', 'runbook', 'architecture', 'component', 'user_guide', 'deployment', 'troubleshooting', 'security')",
            name="ck_doc_template_category"
        ),
    )
    
    def __repr__(self):
        return f"<DocumentationTemplate(id={self.id}, name={self.name}, category={self.category})>"
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "category": self.category,
            "version": self.version,
            "is_active": self.is_active,
            "structure": self.structure,
            "description": self.description,
            "target_framework": self.target_framework,
            "target_audience": self.target_audience,
            "render_options": self.render_options,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "is_system_template": self.is_system_template,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class TemplateExecutionHistoryModel(Base):
    """
    Track template usage and quality.
    
    Stores metrics about how well templates perform, validation results,
    and user ratings for continuous improvement.
    """
    __tablename__ = "template_execution_history"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    template_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("documentation_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    run_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("documentation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    artifact_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("documentation_artifacts.id", ondelete="CASCADE")
    )
    
    # Execution details
    section_name = Column(String(255))
    executed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Quality metrics
    completeness_score = Column(Float)
    adherence_score = Column(Float, index=True)
    user_rating = Column(Integer)
    
    # Issues encountered
    validation_errors = Column(JSONB)
    rendering_errors = Column(JSONB)
    
    # Relationships
    template = relationship("DocumentationTemplateModel", back_populates="executions")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "completeness_score IS NULL OR (completeness_score >= 0 AND completeness_score <= 1)",
            name="ck_completeness_score"
        ),
        CheckConstraint(
            "adherence_score IS NULL OR (adherence_score >= 0 AND adherence_score <= 1)",
            name="ck_adherence_score"
        ),
        CheckConstraint(
            "user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5)",
            name="ck_user_rating"
        ),
    )
    
    def __repr__(self):
        return f"<TemplateExecutionHistory(id={self.id}, template_id={self.template_id}, adherence={self.adherence_score})>"


class PromptExecutionHistoryModel(Base):
    """
    Track prompt effectiveness.
    
    Stores prompts used, their results, and effectiveness metrics for
    continuous prompt evolution and improvement.
    """
    __tablename__ = "prompt_execution_history"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    run_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("documentation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Prompt details
    prompt_template = Column(String(255), index=True)
    prompt_used = Column(Text, nullable=False)
    context_provided = Column(JSONB)
    
    # Execution context
    pass_number = Column(Integer)
    section_name = Column(String(100))
    executed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Response metrics
    response_length = Column(Integer)
    tokens_used = Column(Integer)
    sources_used = Column(JSONB)
    
    # Effectiveness metrics
    effectiveness_score = Column(Float, index=True)
    specificity_score = Column(Float)
    code_examples_count = Column(Integer)
    
    # Extracted findings for next pass
    findings = Column(JSONB)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "effectiveness_score IS NULL OR (effectiveness_score >= 0 AND effectiveness_score <= 1)",
            name="ck_effectiveness_score"
        ),
        CheckConstraint(
            "specificity_score IS NULL OR (specificity_score >= 0 AND specificity_score <= 1)",
            name="ck_specificity_score"
        ),
    )
    
    def __repr__(self):
        return f"<PromptExecutionHistory(id={self.id}, effectiveness={self.effectiveness_score})>"


class DocumentationCitationModel(Base):
    """
    Source citations for generated documentation.
    
    Links generated documentation artifacts to their source documents
    for full transparency and traceability.
    """
    __tablename__ = "documentation_citations"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    artifact_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("documentation_artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    document_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Citation details
    section_name = Column(String(255), index=True)
    relevance_score = Column(Float, nullable=False)
    
    # Excerpt information
    excerpt = Column(Text)
    start_line = Column(Integer)
    end_line = Column(Integer)
    
    # Formatted citation
    citation_text = Column(Text)
    citation_order = Column(Integer)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "relevance_score >= 0 AND relevance_score <= 1",
            name="ck_relevance_score"
        ),
    )
    
    def __repr__(self):
        return f"<DocumentationCitation(id={self.id}, artifact_id={self.artifact_id}, relevance={self.relevance_score})>"


class GenerationTransparencyLogModel(Base):
    """
    Audit trail for documentation generation.
    
    Logs every action during documentation generation for complete
    transparency and debugging capabilities.
    """
    __tablename__ = "generation_transparency_log"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    run_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("documentation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Phase/step information
    phase = Column(String(100), nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False, index=True)
    
    # Action details
    action_type = Column(String(50), nullable=False)
    action_description = Column(Text, nullable=False)
    
    # Input/output data
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    
    # Status
    status = Column(String(20), nullable=False, default='success')
    error_message = Column(Text)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed', 'skipped')",
            name="ck_log_status"
        ),
    )
    
    def __repr__(self):
        return f"<GenerationTransparencyLog(id={self.id}, phase={self.phase}, status={self.status})>"

