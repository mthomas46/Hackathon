"""
SQLAlchemy Models for Quality Checks

ORM models for quality validation, scoring, and review workflow.
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .database import Base


class QualityCheckModel(Base):
    """Quality check result for a documentation artifact."""
    
    __tablename__ = "quality_checks"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    run_id = Column(UUID(as_uuid=True), ForeignKey('documentation_runs.id', ondelete='CASCADE'), nullable=False)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey('documentation_artifacts.id', ondelete='CASCADE'), nullable=False)
    
    # Completeness metrics
    completeness_score = Column(Float, nullable=False)
    missing_sections = Column(JSONB, default=list)
    incomplete_sections = Column(JSONB, default=list)
    placeholder_count = Column(Integer, default=0)
    broken_links = Column(JSONB, default=list)
    formatting_issues = Column(JSONB, default=list)
    section_word_counts = Column(JSONB, default=dict)
    has_code_examples = Column(Boolean, default=False)
    
    # Accuracy metrics
    accuracy_score = Column(Float, nullable=False)
    code_example_issues = Column(JSONB, default=list)
    api_mismatches = Column(JSONB, default=list)
    type_errors = Column(JSONB, default=list)
    factual_errors = Column(JSONB, default=list)
    accuracy_warnings = Column(JSONB, default=list)
    validated_examples = Column(Integer, default=0)
    total_examples = Column(Integer, default=0)
    
    # Confidence metrics
    overall_confidence = Column(Float, nullable=False)
    completeness_confidence = Column(Float, nullable=False)
    accuracy_confidence = Column(Float, nullable=False)
    source_quality_confidence = Column(Float, nullable=False)
    confidence_breakdown = Column(JSONB, default=dict)
    
    # Review workflow
    requires_review = Column(Boolean, default=False)
    review_priority = Column(String(20))  # critical, high, medium, low
    review_status = Column(String(20))    # pending, in_review, approved, rejected, needs_revision
    assigned_to = Column(String(200))
    reviewed_at = Column(DateTime(timezone=True))
    reviewer_notes = Column(Text)
    
    # Recommendations
    recommendations = Column(JSONB, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    run = relationship("DocumentationRunModel", back_populates="quality_checks")
    artifact = relationship("DocumentationArtifactModel", back_populates="quality_check")
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'run_id': str(self.run_id),
            'artifact_id': str(self.artifact_id),
            'completeness_score': self.completeness_score,
            'accuracy_score': self.accuracy_score,
            'overall_confidence': self.overall_confidence,
            'requires_review': self.requires_review,
            'review_priority': self.review_priority,
            'review_status': self.review_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class QualityReportModel(Base):
    """Aggregated quality report for a documentation run."""
    
    __tablename__ = "quality_reports"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    run_id = Column(UUID(as_uuid=True), ForeignKey('documentation_runs.id', ondelete='CASCADE'), nullable=False)
    
    # Summary metrics
    total_artifacts = Column(Integer, nullable=False)
    average_completeness = Column(Float, nullable=False)
    average_accuracy = Column(Float, nullable=False)
    average_confidence = Column(Float, nullable=False)
    
    # Detailed breakdowns
    completeness_breakdown = Column(JSONB, default=dict)
    accuracy_breakdown = Column(JSONB, default=dict)
    confidence_breakdown = Column(JSONB, default=dict)
    
    # Issue summary
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    issues_by_type = Column(JSONB, default=dict)
    
    # Review requirements
    artifacts_requiring_review = Column(Integer, default=0)
    review_priority_breakdown = Column(JSONB, default=dict)
    
    # Recommendations
    top_recommendations = Column(JSONB, default=list)
    
    # Trends
    quality_trend = Column(String(20))  # improving, declining, stable
    
    # Timestamp
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    run = relationship("DocumentationRunModel", back_populates="quality_report")
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'run_id': str(self.run_id),
            'total_artifacts': self.total_artifacts,
            'average_completeness': self.average_completeness,
            'average_accuracy': self.average_accuracy,
            'average_confidence': self.average_confidence,
            'total_issues': self.total_issues,
            'critical_issues': self.critical_issues,
            'artifacts_requiring_review': self.artifacts_requiring_review,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }

