"""
Timeline models for Ecosystem MCP Service.

Represents timelines, time periods, and document placements for temporal document analysis.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class TemporalConfidence(str, Enum):
    """
    Temporal confidence levels.
    
    Based on the proportion of documents with git_history vs snapshot ingestion mode:
    - HIGH: 90%+ documents have git_history with commit dates
    - MEDIUM: 50-90% documents have git_history
    - LOW: 1-50% documents have git_history
    - NONE: 0% documents have git_history (all snapshot mode)
    """
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class PeriodStrategy(str, Enum):
    """Timeline period generation strategies."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ADAPTIVE = "adaptive"  # Based on major commits/releases


class PlacementSource(str, Enum):
    """Source used for document placement in timeline."""
    GIT_COMMIT = "git_commit"
    CREATED_AT = "created_at"
    MANUAL = "manual"


class ConfidenceMetadata(BaseModel):
    """
    Detailed confidence metadata for a timeline.
    
    Provides insight into why a particular confidence level was assigned
    and what capabilities are available.
    """
    total_documents: int = Field(ge=0, description="Total documents considered")
    git_history_documents: int = Field(ge=0, description="Documents with git_history mode")
    snapshot_documents: int = Field(ge=0, description="Documents with snapshot mode")
    git_percentage: float = Field(ge=0.0, le=100.0, description="Percentage with git_history")
    
    # Capability flags
    can_show_evolution: bool = Field(description="Can track document evolution over time")
    can_detect_drift: bool = Field(description="Can detect API/schema drift")
    can_show_timeline: bool = Field(description="Can show document timeline")
    can_compare_periods: bool = Field(description="Can compare between periods")
    
    # Fallback strategy
    fallback_strategy: str = Field(description="Strategy when confidence is low")
    
    # Warnings
    warnings: List[str] = Field(default_factory=list, description="Confidence warnings")
    
    # Timestamp
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class TimelineMetadata(BaseModel):
    """Extended metadata for timelines."""
    total_commits: Optional[int] = Field(default=None, ge=0)
    total_documents: Optional[int] = Field(default=None, ge=0)
    primary_authors: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class Timeline(BaseModel):
    """
    Timeline model.
    
    Represents a temporal timeline for a repository/service with discrete time periods.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique timeline identifier")
    name: str = Field(min_length=1, max_length=255, description="Timeline name")
    description: Optional[str] = Field(default=None, description="Timeline description")
    service_name: str = Field(min_length=1, max_length=255, description="Associated service")
    repo_path: str = Field(min_length=1, description="Repository path")
    
    # Timeline range
    start_date: datetime = Field(description="Timeline start date")
    end_date: datetime = Field(description="Timeline end date")
    
    # Confidence
    confidence_level: TemporalConfidence = Field(description="Confidence level for temporal operations")
    confidence_metadata: ConfidenceMetadata = Field(description="Detailed confidence information")
    
    # Period strategy
    period_strategy: PeriodStrategy = Field(
        default=PeriodStrategy.ADAPTIVE,
        description="Strategy for generating time periods"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    # Metadata
    metadata: TimelineMetadata = Field(default_factory=TimelineMetadata)
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: datetime, info) -> datetime:
        """Ensure end_date is after start_date."""
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "name": "ecosystem-mcp Timeline 2025",
                "description": "Complete timeline for ecosystem-mcp service",
                "service_name": "ecosystem-mcp",
                "repo_path": "/path/to/ecosystem-mcp",
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-12-31T23:59:59Z",
                "confidence_level": "HIGH",
                "period_strategy": "adaptive"
            }
        }


class TimelineCreate(BaseModel):
    """Model for creating a new timeline."""
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    service_name: str = Field(min_length=1, max_length=255)
    repo_path: str = Field(min_length=1)
    start_date: datetime
    end_date: datetime
    period_strategy: PeriodStrategy = PeriodStrategy.ADAPTIVE
    created_by: Optional[str] = None
    metadata: TimelineMetadata = Field(default_factory=TimelineMetadata)
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: datetime, info) -> datetime:
        """Ensure end_date is after start_date."""
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v


class TimelineUpdate(BaseModel):
    """Model for updating a timeline (partial updates)."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    end_date: Optional[datetime] = None
    period_strategy: Optional[PeriodStrategy] = None
    metadata: Optional[TimelineMetadata] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PeriodMetadata(BaseModel):
    """Extended metadata for time periods."""
    major_commits: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class TimePeriod(BaseModel):
    """
    Time period model.
    
    Represents a discrete time period within a timeline with associated documents.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique period identifier")
    timeline_id: UUID = Field(description="Parent timeline ID")
    name: str = Field(min_length=1, max_length=255, description="Period name (e.g., 'Q1 2025')")
    description: Optional[str] = Field(default=None, description="Period description")
    
    # Period range
    start_date: datetime = Field(description="Period start date")
    end_date: datetime = Field(description="Period end date")
    
    # Ordering
    sequence_number: int = Field(ge=1, description="Order within timeline")
    
    # Statistics
    document_count: int = Field(default=0, ge=0, description="Number of documents in period")
    commit_count: int = Field(default=0, ge=0, description="Number of commits in period")
    
    # Metadata
    metadata: PeriodMetadata = Field(default_factory=PeriodMetadata)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: datetime, info) -> datetime:
        """Ensure end_date is after start_date."""
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "timeline_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Q1 2025",
                "description": "First quarter of 2025",
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-03-31T23:59:59Z",
                "sequence_number": 1,
                "document_count": 42,
                "commit_count": 156
            }
        }


class TimePeriodCreate(BaseModel):
    """Model for creating a time period."""
    timeline_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    sequence_number: int = Field(ge=1)
    metadata: PeriodMetadata = Field(default_factory=PeriodMetadata)


class PlacementMetadata(BaseModel):
    """Extended metadata for document placements."""
    commit_message: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class DocumentPlacement(BaseModel):
    """
    Document placement model.
    
    Links a document to a specific time period within a timeline.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique placement identifier")
    period_id: UUID = Field(description="Time period ID")
    document_id: UUID = Field(description="Document ID")
    
    # Placement details
    placement_date: datetime = Field(description="Date used for placement decision")
    placement_source: PlacementSource = Field(description="Source of placement date")
    
    # Git information
    git_commit_sha: Optional[str] = Field(
        default=None,
        min_length=40,
        max_length=40,
        description="Git commit SHA if applicable"
    )
    
    # Relevance
    relevance_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="How relevant this document is to the period"
    )
    
    # Metadata
    metadata: PlacementMetadata = Field(default_factory=PlacementMetadata)
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "period_id": "123e4567-e89b-12d3-a456-426614174000",
                "document_id": "987e6543-e21b-12d3-a456-426614174000",
                "placement_date": "2025-01-15T10:30:00Z",
                "placement_source": "git_commit",
                "git_commit_sha": "a" * 40,
                "relevance_score": 1.0
            }
        }


class DocumentPlacementCreate(BaseModel):
    """Model for creating a document placement."""
    period_id: UUID
    document_id: UUID
    placement_date: datetime
    placement_source: PlacementSource
    git_commit_sha: Optional[str] = Field(default=None, min_length=40, max_length=40)
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: PlacementMetadata = Field(default_factory=PlacementMetadata)


# Response models for API endpoints

class TimelineListResponse(BaseModel):
    """Response for listing timelines."""
    timelines: List[Timeline]
    total: int
    page: int
    page_size: int


class TimePeriodListResponse(BaseModel):
    """Response for listing time periods."""
    periods: List[TimePeriod]
    total: int
    timeline_id: UUID


class DocumentPlacementListResponse(BaseModel):
    """Response for listing document placements."""
    placements: List[DocumentPlacement]
    total: int
    period_id: UUID


class TimelineWithPeriodsResponse(BaseModel):
    """Response with timeline and its periods."""
    timeline: Timeline
    periods: List[TimePeriod]
    total_periods: int


class PeriodWithDocumentsResponse(BaseModel):
    """Response with period and its documents."""
    period: TimePeriod
    placements: List[DocumentPlacement]
    total_documents: int

