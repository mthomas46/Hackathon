"""
SQLAlchemy ORM models for documentation tables (Phase 4).
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text,
    ForeignKey, DateTime, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .db_models import Base


class DocumentationRunModel(Base):
    """Documentation generation run."""
    
    __tablename__ = "documentation_runs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(String(500), index=True)
    repo_id = Column(String(500), ForeignKey("repository_contexts.repo_id", ondelete="CASCADE"), index=True)
    
    # Run configuration
    passes_completed = Column(Integer, default=0)
    total_passes = Column(Integer, default=5)
    current_pass = Column(String(50))
    config = Column(JSON)  # DocConfig serialized
    
    # Status
    status = Column(String(20), nullable=False, index=True)  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Metrics
    total_artifacts = Column(Integer, default=0)
    total_words = Column(Integer, default=0)
    overall_quality_score = Column(Float)
    
    # Output
    output_path = Column(Text)
    output_formats = Column(JSON)  # ['markdown', 'html', 'json']
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    artifacts = relationship(
        "DocumentationArtifactModel",
        back_populates="run",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<DocumentationRun(id={self.id}, status={self.status}, artifacts={self.total_artifacts})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "plan_id": self.plan_id,
            "repo_id": self.repo_id,
            "passes_completed": self.passes_completed,
            "total_passes": self.total_passes,
            "current_pass": self.current_pass,
            "config": self.config,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_artifacts": self.total_artifacts,
            "total_words": self.total_words,
            "overall_quality_score": self.overall_quality_score,
            "output_path": self.output_path,
            "output_formats": self.output_formats,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DocumentationArtifactModel(Base):
    """Generated documentation artifact."""
    
    __tablename__ = "documentation_artifacts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("documentation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Artifact info
    artifact_type = Column(String(50), nullable=False, index=True)  # 'architecture', 'component', 'api', 'examples', 'synthesis'
    pass_number = Column(Integer, nullable=False)
    pass_type = Column(String(50), nullable=False, index=True)  # 'architecture', 'component', etc.
    component_name = Column(String(200), index=True)  # For component-specific docs
    
    # Content
    title = Column(String(500))
    content = Column(Text)
    format = Column(String(20), default='markdown')  # 'markdown', 'json', 'yaml', 'html'
    
    # Metadata
    word_count = Column(Integer, default=0)
    quality_score = Column(Float)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    run = relationship("DocumentationRunModel", back_populates="artifacts")
    
    def __repr__(self) -> str:
        return f"<DocumentationArtifact(id={self.id}, type={self.artifact_type}, title={self.title})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "run_id": str(self.run_id),
            "artifact_type": self.artifact_type,
            "pass_number": self.pass_number,
            "pass_type": self.pass_type,
            "component_name": self.component_name,
            "title": self.title,
            "content": self.content,
            "format": self.format,
            "word_count": self.word_count,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

