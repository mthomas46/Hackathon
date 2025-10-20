"""
Database Models for Discovery System

SQLAlchemy models for processing plans, sub-jobs, and file classifications.
"""

from sqlalchemy import Column, String, Integer, Float, Text, Boolean, BigInteger, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base


class ProcessingPlanModel(Base):
    """Processing plan for repository ingestion."""
    __tablename__ = "processing_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_path = Column(Text, nullable=False)
    total_files = Column(Integer, nullable=False, default=0)
    total_size_mb = Column(Float, nullable=False, default=0.0)
    estimated_time_minutes = Column(Float, nullable=False, default=0.0)
    max_parallelization = Column(Integer, nullable=False, default=1)
    processing_order = Column(JSONB, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sub_jobs = relationship("SubJobModel", back_populates="plan", cascade="all, delete-orphan")
    file_classifications = relationship("FileClassificationModel", back_populates="plan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ProcessingPlan(id={self.id}, repo={self.repo_path}, files={self.total_files}, status={self.status})>"


class SubJobModel(Base):
    """Sub-job within a processing plan."""
    __tablename__ = "sub_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("processing_plans.id", ondelete="CASCADE"), nullable=False)
    sub_job_id = Column(String(255), nullable=False)
    sub_job_name = Column(String(255), nullable=False)
    file_count = Column(Integer, nullable=False, default=0)
    priority = Column(Integer, nullable=False, default=0)
    estimated_time_minutes = Column(Float, nullable=False, default=0.0)
    dependencies = Column(JSONB, default=list)
    status = Column(String(50), default="pending")
    processed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    skipped_files = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    plan = relationship("ProcessingPlanModel", back_populates="sub_jobs")
    
    def __repr__(self):
        return f"<SubJob(id={self.sub_job_id}, name={self.sub_job_name}, status={self.status}, files={self.processed_files}/{self.file_count})>"


class FileClassificationModel(Base):
    """File classification within a processing plan."""
    __tablename__ = "file_classifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("processing_plans.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(Text, nullable=False)
    relative_path = Column(Text, nullable=False)
    size_bytes = Column(BigInteger, nullable=False, default=0)
    extension = Column(String(50), nullable=True)
    language = Column(String(100), nullable=True)
    is_code = Column(Boolean, default=False)
    is_test = Column(Boolean, default=False)
    is_doc = Column(Boolean, default=False)
    is_config = Column(Boolean, default=False)
    importance_level = Column(String(50), nullable=False)
    importance_score = Column(Float, nullable=False, default=0.5)
    priority = Column(Integer, nullable=False, default=1000)
    sub_job_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    plan = relationship("ProcessingPlanModel", back_populates="file_classifications")
    
    def __repr__(self):
        return f"<FileClassification(file={self.relative_path}, level={self.importance_level}, score={self.importance_score})>"

