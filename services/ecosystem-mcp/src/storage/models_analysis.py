"""
SQLAlchemy ORM models for analysis tables (Phase 3).
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


class RepositoryContextModel(Base):
    """Repository-level context metadata."""
    
    __tablename__ = "repository_contexts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    repo_id = Column(String(500), unique=True, nullable=False, index=True)
    repo_name = Column(String(500))
    
    # Technology Stack
    languages = Column(JSON)  # {"python": 120, "javascript": 45}
    frameworks = Column(JSON)  # {"fastapi": ["src/api/app.py"], "react": [...]}
    databases = Column(JSON)  # ["postgresql", "redis"]
    tools = Column(JSON)  # ["docker", "kubernetes"]
    deployment_platforms = Column(JSON)  # ["aws", "vercel"]
    
    # Architecture
    architecture_type = Column(String(50), index=True)  # "microservices", "mvc", etc.
    architecture_confidence = Column(Float)
    service_count = Column(Integer, default=1)
    component_count = Column(Integer)
    layers = Column(JSON)  # ["api", "business", "data"]
    
    # API Summary
    endpoint_count = Column(Integer, default=0)
    endpoints = Column(JSON)  # [{"path": "/api/v1/users", "method": "GET"}]
    has_rest_api = Column(Boolean, default=False)
    has_graphql = Column(Boolean, default=False)
    has_websocket = Column(Boolean, default=False)
    
    # Code Metrics
    total_files = Column(Integer)
    total_lines = Column(Integer)
    code_files = Column(Integer)
    test_files = Column(Integer)
    doc_files = Column(Integer)
    modularity_score = Column(Float)
    
    # Entry Points
    entry_points = Column(JSON)  # ["src/main.py", "app.py"]
    main_flows = Column(JSON)
    
    # AI Summary
    brief_description = Column(Text)
    key_features = Column(JSON)
    technical_highlights = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    services = relationship(
        "DetectedServiceModel",
        back_populates="repository",
        cascade="all, delete-orphan"
    )
    analysis_results = relationship(
        "AnalysisResultModel",
        back_populates="repository",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<RepositoryContext(repo_id={self.repo_id}, arch={self.architecture_type})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "repo_id": self.repo_id,
            "repo_name": self.repo_name,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "databases": self.databases,
            "tools": self.tools,
            "deployment_platforms": self.deployment_platforms,
            "architecture_type": self.architecture_type,
            "architecture_confidence": self.architecture_confidence,
            "service_count": self.service_count,
            "component_count": self.component_count,
            "layers": self.layers,
            "endpoint_count": self.endpoint_count,
            "endpoints": self.endpoints,
            "has_rest_api": self.has_rest_api,
            "has_graphql": self.has_graphql,
            "has_websocket": self.has_websocket,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "code_files": self.code_files,
            "test_files": self.test_files,
            "doc_files": self.doc_files,
            "modularity_score": self.modularity_score,
            "entry_points": self.entry_points,
            "main_flows": self.main_flows,
            "brief_description": self.brief_description,
            "key_features": self.key_features,
            "technical_highlights": self.technical_highlights,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DetectedServiceModel(Base):
    """Detected microservice or service boundary."""
    
    __tablename__ = "detected_services"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    repo_id = Column(String(500), ForeignKey("repository_contexts.repo_id", ondelete="CASCADE"), nullable=False, index=True)
    service_name = Column(String(200), nullable=False, index=True)
    root_path = Column(String(500))
    
    # Service Details
    file_count = Column(Integer)
    entry_point = Column(String(500))
    internal_dependencies = Column(JSON)  # ["auth-service", "payment-service"]
    external_dependencies = Column(JSON)  # ["fastapi", "sqlalchemy"]
    
    # Technology
    languages = Column(JSON)  # ["python", "javascript"]
    frameworks = Column(JSON)  # ["fastapi", "react"]
    databases = Column(JSON)  # ["postgresql", "redis"]
    
    # API
    has_api = Column(Boolean, default=False, index=True)
    endpoints = Column(JSON)  # ["/api/v1/users", "/api/v1/posts"]
    
    # Deployment
    has_dockerfile = Column(Boolean, default=False)
    has_k8s_config = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("RepositoryContextModel", back_populates="services")
    
    def __repr__(self) -> str:
        return f"<DetectedService(name={self.service_name}, repo={self.repo_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "repo_id": self.repo_id,
            "service_name": self.service_name,
            "root_path": self.root_path,
            "file_count": self.file_count,
            "entry_point": self.entry_point,
            "internal_dependencies": self.internal_dependencies,
            "external_dependencies": self.external_dependencies,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "databases": self.databases,
            "has_api": self.has_api,
            "endpoints": self.endpoints,
            "has_dockerfile": self.has_dockerfile,
            "has_k8s_config": self.has_k8s_config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AnalysisResultModel(Base):
    """Complete analysis result for a processing plan."""
    
    __tablename__ = "analysis_results"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(String(500), nullable=False, index=True)
    repo_id = Column(String(500), ForeignKey("repository_contexts.repo_id", ondelete="CASCADE"), nullable=False, index=True)
    repo_path = Column(Text)
    
    # Analysis Status
    analysis_complete = Column(Boolean, default=False, index=True)
    errors = Column(JSON)  # ["Dependency analysis: timeout"]
    
    # Dependency Analysis
    has_dependency_graph = Column(Boolean, default=False)
    total_nodes = Column(Integer)
    total_edges = Column(Integer)
    circular_dependencies = Column(JSON)
    topological_order = Column(JSON)
    
    # Technology Stack
    primary_language = Column(String(100))
    total_languages = Column(Integer)
    total_frameworks = Column(Integer)
    total_databases = Column(Integer)
    
    # Architecture
    primary_architecture = Column(String(50))
    architecture_confidence = Column(Float)
    secondary_architectures = Column(JSON)
    detected_layers = Column(JSON)
    
    # Services
    total_services = Column(Integer, default=1)
    is_microservices = Column(Boolean, default=False)
    service_dependencies = Column(JSON)
    
    # Summary Metrics
    total_files = Column(Integer)
    modularity_score = Column(Float)
    
    # Full Report (JSONB for flexibility)
    dependency_graph = Column(JSON)
    technology_stack = Column(JSON)
    architecture_analysis = Column(JSON)
    service_map = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("RepositoryContextModel", back_populates="analysis_results")
    
    def __repr__(self) -> str:
        return f"<AnalysisResult(plan_id={self.plan_id}, complete={self.analysis_complete})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "plan_id": self.plan_id,
            "repo_id": self.repo_id,
            "repo_path": self.repo_path,
            "analysis_complete": self.analysis_complete,
            "errors": self.errors,
            "has_dependency_graph": self.has_dependency_graph,
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "circular_dependencies": self.circular_dependencies,
            "topological_order": self.topological_order,
            "primary_language": self.primary_language,
            "total_languages": self.total_languages,
            "total_frameworks": self.total_frameworks,
            "total_databases": self.total_databases,
            "primary_architecture": self.primary_architecture,
            "architecture_confidence": self.architecture_confidence,
            "secondary_architectures": self.secondary_architectures,
            "detected_layers": self.detected_layers,
            "total_services": self.total_services,
            "is_microservices": self.is_microservices,
            "service_dependencies": self.service_dependencies,
            "total_files": self.total_files,
            "modularity_score": self.modularity_score,
            "dependency_graph": self.dependency_graph,
            "technology_stack": self.technology_stack,
            "architecture_analysis": self.architecture_analysis,
            "service_map": self.service_map,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

