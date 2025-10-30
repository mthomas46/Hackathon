"""
SQLAlchemy database models for Ecosystem MCP Service.

These mirror the Pydantic models but are optimized for database storage.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer,
    String, Text, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class DocumentModel(Base):
    """
    Document table model.
    
    Stores documents with full metadata and optional git linkage.
    Supports both 'snapshot' and 'git_history' ingestion modes.
    """
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    service_name = Column(String(255), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    original_format = Column(String(50), nullable=False)
    original_content = Column(Text, nullable=False)
    normalized_content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    
    # Phase 8: Snapshot mode support
    ingestion_mode = Column(String(20), nullable=False, default='git_history', index=True)
    version = Column(Integer, nullable=False, default=1)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Now nullable for snapshot mode
    git_commit_sha = Column(String(40), ForeignKey("git_commits.sha"), nullable=True, index=True)
    
    # Temporal metadata columns (Phase 1: Temporal RAG)
    git_date = Column(DateTime, nullable=True)
    git_author = Column(String(255), nullable=True)
    git_author_email = Column(String(255), nullable=True)
    git_commit_message = Column(Text, nullable=True)
    
    # Metadata schema version (Fix #6: Metadata completeness tracking)
    metadata_version = Column(Integer, nullable=True, default=1)
    
    is_latest = Column(Boolean, nullable=False, default=True, index=True)
    embedding_id = Column(UUID(as_uuid=True), ForeignKey("embeddings.id"))
    doc_metadata = Column(JSONB, nullable=False, default=dict)
    
    # Document quality score (0-100, for RAG weighting)
    quality_score = Column(Float, nullable=True, index=True)
    quality_grade = Column(String(1), nullable=True)  # S, A, B, C, D, F
    score_breakdown = Column(JSONB, nullable=True)  # Detailed scoring breakdown
    
    # Relationships
    commit = relationship("GitCommitModel", back_populates="documents")
    embedding = relationship("EmbeddingModel", back_populates="document", uselist=False, foreign_keys="[EmbeddingModel.document_id]")
    versions = relationship("DocumentVersionModel", back_populates="document", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        # Updated constraint for snapshot mode (uses content_hash instead of git_commit_sha)
        UniqueConstraint("file_path", "content_hash", name="uq_document_file_hash"),
        Index("idx_documents_service_latest", "service_name", "is_latest"),
        Index("idx_documents_content_hash", "content_hash"),
        Index("idx_documents_mode", "ingestion_mode"),
        Index("idx_documents_mode_latest", "ingestion_mode", "is_latest"),
        Index("idx_documents_version", "version"),
    )


class DocumentVersionModel(Base):
    """
    Document version table model.
    
    Stores historical versions of documents.
    """
    __tablename__ = "document_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    git_commit_sha = Column(String(40), ForeignKey("git_commits.sha"), nullable=False)
    commit_message = Column(Text, nullable=False)
    commit_date = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    embedding_id = Column(UUID(as_uuid=True), ForeignKey("embeddings.id"))
    
    # Relationships
    document = relationship("DocumentModel", back_populates="versions")
    commit = relationship("GitCommitModel")
    embedding = relationship("EmbeddingModel")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_version_document_number"),
        Index("idx_versions_document_version", "document_id", "version_number"),
        CheckConstraint("version_number >= 1", name="ck_version_positive"),
    )


class EmbeddingModel(Base):
    """
    Embedding table model.
    
    Stores embedding metadata (vectors in ChromaDB).
    """
    __tablename__ = "embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    chroma_id = Column(String(255), nullable=False, unique=True, index=True)
    model = Column(String(100), nullable=False, index=True)
    dimensions = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    token_count = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    extra_metadata = Column(JSONB)
    
    # Relationships
    document = relationship("DocumentModel", back_populates="embedding", foreign_keys=[document_id])
    
    # Constraints
    __table_args__ = (
        CheckConstraint("dimensions > 0", name="ck_dimensions_positive"),
        CheckConstraint("token_count >= 0", name="ck_token_count_nonnegative"),
        CheckConstraint("cost_usd >= 0.0", name="ck_cost_nonnegative"),
        Index("idx_embeddings_document", "document_id"),
        Index("idx_embeddings_model", "model"),
    )


class GitCommitModel(Base):
    """
    Git commit table model.
    
    Caches git commit metadata.
    """
    __tablename__ = "git_commits"
    
    sha = Column(String(40), primary_key=True)
    author = Column(String(255), nullable=False)
    author_email = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    message = Column(Text, nullable=False)
    commit_metadata = Column(JSONB)
    
    # Relationships
    documents = relationship("DocumentModel", back_populates="commit")
    
    # Indexes
    __table_args__ = (
        Index("idx_commits_date", "date"),
        Index("idx_commits_author", "author"),
    )


class IngestionJobModel(Base):
    """
    Ingestion job table model.
    
    Tracks ingestion job progress and results.
    """
    __tablename__ = "ingestion_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    mode = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    processed_documents = Column(Integer, nullable=False, default=0)
    total_documents = Column(Integer)
    failed_documents = Column(Integer, nullable=False, default=0)
    skipped_documents = Column(Integer, nullable=False, default=0)  # Duplicates, not errors
    repo_path = Column(Text)
    embeddings_generated = Column(Integer, nullable=False, default=0)
    total_cost_usd = Column(Float, nullable=False, default=0.0)
    error_message = Column(Text)
    job_metadata = Column(JSONB, default=dict)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("processed_documents >= 0", name="ck_processed_nonnegative"),
        CheckConstraint("failed_documents >= 0", name="ck_failed_nonnegative"),
        CheckConstraint("embeddings_generated >= 0", name="ck_embeddings_nonnegative"),
        CheckConstraint("total_cost_usd >= 0.0", name="ck_cost_nonnegative"),
        Index("idx_jobs_status_started", "status", "started_at"),
    )


class ModelRequestModel(Base):
    """
    Model request table model.
    
    Tracks all AI model requests for monitoring and cost control.
    """
    __tablename__ = "model_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    model = Column(String(100), nullable=False, index=True)
    task_type = Column(String(100), nullable=False, index=True)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)
    latency_ms = Column(Integer, nullable=False, default=0)
    success = Column(Boolean, nullable=False, default=True, index=True)
    error_message = Column(Text)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    
    # Constraints
    __table_args__ = (
        CheckConstraint("input_tokens >= 0", name="ck_input_tokens_nonnegative"),
        CheckConstraint("output_tokens >= 0", name="ck_output_tokens_nonnegative"),
        CheckConstraint("cost_usd >= 0.0", name="ck_cost_nonnegative"),
        CheckConstraint("latency_ms >= 0", name="ck_latency_nonnegative"),
        Index("idx_requests_timestamp", "timestamp"),
        Index("idx_requests_model_timestamp", "model", "timestamp"),
        Index("idx_requests_task_type", "task_type"),
    )


# ==========================================
# Timeline Analysis Models (Phase 1)
# ==========================================

class TimelineModel(Base):
    """
    Timeline table model.
    
    Represents a timeline for a specific repository/service with temporal periods.
    Supports confidence-based operation based on ingestion mode distribution.
    """
    __tablename__ = "timelines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    service_name = Column(String(255), nullable=False, index=True)
    repo_path = Column(Text, nullable=False)
    
    # Timeline range
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    
    # Confidence tracking
    confidence_level = Column(String(20), nullable=False, index=True)  # HIGH, MEDIUM, LOW, NONE
    confidence_metadata = Column(JSONB, nullable=False, default=dict)  # Detailed confidence info
    
    # Period generation strategy
    period_strategy = Column(String(50), nullable=False, default='adaptive')  # monthly, quarterly, adaptive
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    
    # Metadata
    timeline_metadata = Column(JSONB, default=dict)
    
    # Relationships
    periods = relationship("TimePeriodModel", back_populates="timeline", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("start_date <= end_date", name="ck_timeline_date_range"),
        CheckConstraint("confidence_level IN ('HIGH', 'MEDIUM', 'LOW', 'NONE')", name="ck_confidence_level"),
        Index("idx_timelines_service", "service_name"),
        Index("idx_timelines_confidence", "confidence_level"),
        Index("idx_timelines_dates", "start_date", "end_date"),
        Index("idx_timelines_created", "created_at"),
    )


class TimePeriodModel(Base):
    """
    Time period table model.
    
    Represents a discrete time period within a timeline (e.g., Q1 2025, Oct 2025).
    Contains documents placed in this period based on commit dates or creation dates.
    """
    __tablename__ = "time_periods"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timeline_id = Column(UUID(as_uuid=True), ForeignKey("timelines.id"), nullable=False, index=True)
    
    # Period identification
    name = Column(String(255), nullable=False)  # e.g., "Q1 2025", "Oct 2025", "Major Release v2.0"
    description = Column(Text)
    
    # Period range
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    
    # Ordering
    sequence_number = Column(Integer, nullable=False)  # Order within timeline
    
    # Statistics
    document_count = Column(Integer, nullable=False, default=0)
    commit_count = Column(Integer, nullable=False, default=0)
    
    # Metadata
    period_metadata = Column(JSONB, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    timeline = relationship("TimelineModel", back_populates="periods")
    document_placements = relationship("DocumentPlacementModel", back_populates="period", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("start_date <= end_date", name="ck_period_date_range"),
        CheckConstraint("sequence_number >= 1", name="ck_sequence_positive"),
        CheckConstraint("document_count >= 0", name="ck_document_count_nonnegative"),
        CheckConstraint("commit_count >= 0", name="ck_commit_count_nonnegative"),
        UniqueConstraint("timeline_id", "sequence_number", name="uq_period_timeline_sequence"),
        Index("idx_periods_timeline", "timeline_id"),
        Index("idx_periods_dates", "start_date", "end_date"),
        Index("idx_periods_sequence", "timeline_id", "sequence_number"),
    )


class DocumentPlacementModel(Base):
    """
    Document placement table model.
    
    Links documents to specific time periods within a timeline.
    Supports both git_history mode (based on commit dates) and snapshot mode (based on created_at).
    """
    __tablename__ = "document_placements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    period_id = Column(UUID(as_uuid=True), ForeignKey("time_periods.id"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    
    # Placement details
    placement_date = Column(DateTime, nullable=False, index=True)  # Date used for placement
    placement_source = Column(String(50), nullable=False)  # 'git_commit', 'created_at', 'manual'
    
    # Git information (if applicable)
    git_commit_sha = Column(String(40), ForeignKey("git_commits.sha"), nullable=True, index=True)
    
    # Relevance and confidence
    relevance_score = Column(Float, default=1.0)  # How relevant is this doc to the period
    
    # Metadata
    placement_metadata = Column(JSONB, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    period = relationship("TimePeriodModel", back_populates="document_placements")
    document = relationship("DocumentModel")
    commit = relationship("GitCommitModel")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("relevance_score >= 0.0 AND relevance_score <= 1.0", name="ck_relevance_range"),
        CheckConstraint("placement_source IN ('git_commit', 'created_at', 'manual')", name="ck_placement_source"),
        UniqueConstraint("period_id", "document_id", name="uq_placement_period_document"),
        Index("idx_placements_period", "period_id"),
        Index("idx_placements_document", "document_id"),
        Index("idx_placements_date", "placement_date"),
        Index("idx_placements_commit", "git_commit_sha"),
    )

