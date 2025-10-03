"""
SQLAlchemy Database Models for Project Planning Service
========================================================

Persistent storage models for features, tasks, roadmaps, and related entities.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey,
    Boolean, JSON, Table, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


# ============================================================================
# ENUMERATIONS
# ============================================================================

class FeatureStatusDB(enum.Enum):
    """Feature status for database storage."""
    DRAFT = "draft"
    ANALYZED = "analyzed"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FeaturePriorityDB(enum.Enum):
    """Feature priority for database storage."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatusDB(enum.Enum):
    """Task status for database storage."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskTypeDB(enum.Enum):
    """Task type for database storage."""
    ANALYSIS = "analysis"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    REVIEW = "review"


class RoadmapStatusDB(enum.Enum):
    """Roadmap status for database storage."""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReleaseStatusDB(enum.Enum):
    """Release status for database storage."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    RELEASED = "released"
    CANCELLED = "cancelled"


# ============================================================================
# MODELS
# ============================================================================

class ProjectModel(Base):
    """Project model for high-level project organization."""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(String(50), default="active")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255))
    
    # Relationships
    features = relationship("FeatureModel", back_populates="project", cascade="all, delete-orphan")
    roadmaps = relationship("RoadmapModel", back_populates="project", cascade="all, delete-orphan")


class FeatureModel(Base):
    """Feature persistence model."""
    __tablename__ = "features"

    id = Column(String(36), primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Status and priority
    status = Column(SQLEnum(FeatureStatusDB), default=FeatureStatusDB.DRAFT, nullable=False)
    priority = Column(SQLEnum(FeaturePriorityDB), default=FeaturePriorityDB.MEDIUM, nullable=False)
    
    # Business context
    business_value = Column(Text)
    acceptance_criteria = Column(JSON)  # List of strings
    
    # Technical details
    estimated_effort = Column(Float)  # Story points
    technical_complexity = Column(String(50))
    dependencies = Column(JSON)  # List of feature IDs
    
    # AI analysis
    ai_analysis = Column(JSON)
    risk_assessment = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255))
    
    # Foreign keys
    project_id = Column(String(36), ForeignKey("projects.id"))
    roadmap_id = Column(String(36), ForeignKey("roadmaps.id"))
    parent_feature_id = Column(String(36), ForeignKey("features.id"))
    
    # Relationships
    project = relationship("ProjectModel", back_populates="features")
    roadmap = relationship("RoadmapModel", back_populates="features")
    parent_feature = relationship("FeatureModel", remote_side=[id], back_populates="child_features")
    child_features = relationship("FeatureModel", back_populates="parent_feature", cascade="all, delete-orphan")
    tasks = relationship("TaskModel", back_populates="feature", cascade="all, delete-orphan")


class TaskModel(Base):
    """Task persistence model."""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=False)
    task_type = Column(SQLEnum(TaskTypeDB), nullable=False)
    
    # Status and assignment
    status = Column(SQLEnum(TaskStatusDB), default=TaskStatusDB.TODO, nullable=False)
    assigned_to = Column(String(255), index=True)
    assigned_by = Column(String(255))
    
    # Estimation and tracking
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    story_points = Column(Float)
    
    # Scheduling
    planned_start = Column(DateTime)
    planned_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    
    # Relationships
    feature_id = Column(String(36), ForeignKey("features.id"), nullable=False)
    depends_on = Column(JSON)  # List of task IDs
    blocks = Column(JSON)  # List of task IDs
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=False)
    
    # Additional context
    tags = Column(JSON)  # List of strings
    attachments = Column(JSON)  # List of file URLs/IDs
    comments = Column(JSON)  # List of comment objects
    
    # Relationships
    feature = relationship("FeatureModel", back_populates="tasks")


class RoadmapModel(Base):
    """Roadmap persistence model."""
    __tablename__ = "roadmaps"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Status and timeline
    status = Column(SQLEnum(RoadmapStatusDB), default=RoadmapStatusDB.PLANNING, nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Configuration
    sprint_duration_days = Column(Integer, default=14)
    
    # Progress tracking
    total_story_points = Column(Float)
    completed_story_points = Column(Float, default=0.0)
    
    # Team capacity (JSON: user_id -> capacity hours/week)
    team_capacity = Column(JSON)
    
    # AI analysis
    ai_insights = Column(JSON)
    risk_assessment = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=False)
    
    # Foreign keys
    project_id = Column(String(36), ForeignKey("projects.id"))
    
    # Relationships
    project = relationship("ProjectModel", back_populates="roadmaps")
    features = relationship("FeatureModel", back_populates="roadmap")
    releases = relationship("ReleaseModel", back_populates="roadmap", cascade="all, delete-orphan")


class ReleaseModel(Base):
    """Release milestone persistence model."""
    __tablename__ = "releases"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(SQLEnum(ReleaseStatusDB), default=ReleaseStatusDB.PLANNED, nullable=False)
    
    # Timeline
    planned_release_date = Column(DateTime)
    actual_release_date = Column(DateTime)
    
    # Content (JSON: list of feature IDs)
    feature_ids = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Foreign keys
    roadmap_id = Column(String(36), ForeignKey("roadmaps.id"), nullable=False)
    
    # Relationships
    roadmap = relationship("RoadmapModel", back_populates="releases")


class TeamMemberModel(Base):
    """Team member capacity and skills model."""
    __tablename__ = "team_members"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    role = Column(String(100))
    
    # Capacity
    capacity_hours_per_week = Column(Float, default=40.0)
    is_active = Column(Boolean, default=True)
    
    # Skills (JSON: {skill_name: proficiency_level})
    skills = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PlanningSessionModel(Base):
    """Planning session for collaborative planning."""
    __tablename__ = "planning_sessions"

    id = Column(String(36), primary_key=True)
    roadmap_id = Column(String(36), ForeignKey("roadmaps.id"), nullable=False)
    
    # Session details
    session_type = Column(String(50))  # planning, grooming, retrospective
    status = Column(String(50))  # active, completed, cancelled
    
    # Participants (JSON: list of user IDs)
    participants = Column(JSON)
    
    # Session data
    notes = Column(Text)
    decisions = Column(JSON)  # List of decision objects
    action_items = Column(JSON)  # List of action items
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    created_by = Column(String(255), nullable=False)

