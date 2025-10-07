"""SQLAlchemy models for MCP Store."""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class PackageModel(Base):
    """SQLAlchemy model for MCP Package."""
    
    __tablename__ = "packages"
    
    # Identity
    package_id = Column(String(36), primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    
    # Metadata
    description = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    author_email = Column(String(255))
    homepage_url = Column(String(500))
    repository_url = Column(String(500))
    documentation_url = Column(String(500))
    license = Column(String(50), default="MIT")
    
    # Status
    status = Column(String(20), nullable=False, index=True)
    
    # Version info
    latest_version = Column(String(50))
    
    # Classification (stored as JSON arrays)
    tags = Column(JSON, default=list)
    categories = Column(JSON, default=list)
    
    # Statistics
    total_downloads = Column(Integer, default=0, index=True)
    download_count_30d = Column(Integer, default=0)
    star_count = Column(Integer, default=0, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime)
    
    # Access control
    owner_id = Column(String(36), nullable=False, index=True)
    is_public = Column(Boolean, default=True, index=True)
    allowed_users = Column(JSON, default=list)
    
    # Content metadata
    embedding_count = Column(Integer, default=0)
    document_count = Column(Integer, default=0)
    entity_count = Column(Integer, default=0)
    relationship_count = Column(Integer, default=0)
    
    # Additional metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    versions = relationship("VersionModel", back_populates="package", cascade="all, delete-orphan")
    
    # Indexes for search (SQLite compatible)
    __table_args__ = (
        Index('idx_package_name', 'name'),
        Index('idx_package_display_name', 'display_name'),
    )


class VersionModel(Base):
    """SQLAlchemy model for MCP Version."""
    
    __tablename__ = "versions"
    
    # Identity
    version = Column(String(50), primary_key=True)
    package_id = Column(String(36), ForeignKey("packages.package_id", ondelete="CASCADE"), primary_key=True)
    
    # Storage
    storage_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA-256
    
    # Metadata
    changelog = Column(Text, default="")
    release_notes = Column(Text, default="")
    
    # Flags
    is_prerelease = Column(Boolean, default=False)
    is_yanked = Column(Boolean, default=False, index=True)
    yank_reason = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    published_at = Column(DateTime)
    yanked_at = Column(DateTime)
    
    # Statistics
    download_count = Column(Integer, default=0)
    
    # Dependencies (stored as JSON)
    dependencies = Column(JSON, default=dict)
    
    # Platform requirements
    min_python_version = Column(String(20))
    max_python_version = Column(String(20))
    
    # Additional metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    package = relationship("PackageModel", back_populates="versions")
    
    # Indexes
    __table_args__ = (
        Index('idx_version_package', 'package_id', 'version'),
        Index('idx_version_created', 'created_at'),
    )
