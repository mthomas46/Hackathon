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
    
    Stores documents with full metadata and git linkage.
    """
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    service_name = Column(String(255), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    original_format = Column(String(50), nullable=False)
    original_content = Column(Text, nullable=False)
    normalized_content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    git_commit_sha = Column(String(40), ForeignKey("git_commits.sha"), index=True)
    is_latest = Column(Boolean, nullable=False, default=True, index=True)
    embedding_id = Column(UUID(as_uuid=True), ForeignKey("embeddings.id"))
    doc_metadata = Column(JSONB, nullable=False, default=dict)
    
    # Relationships
    commit = relationship("GitCommitModel", back_populates="documents")
    embedding = relationship("EmbeddingModel", back_populates="document", uselist=False, foreign_keys="[EmbeddingModel.document_id]")
    versions = relationship("DocumentVersionModel", back_populates="document", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("file_path", "git_commit_sha", name="uq_document_file_commit"),
        Index("idx_documents_service_latest", "service_name", "is_latest"),
        Index("idx_documents_content_hash", "content_hash"),
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
        CheckConstraint("documents_processed >= 0", name="ck_processed_nonnegative"),
        CheckConstraint("documents_failed >= 0", name="ck_failed_nonnegative"),
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

