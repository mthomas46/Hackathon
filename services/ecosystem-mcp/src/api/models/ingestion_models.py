"""
API models for ingestion requests and responses.

Supports both snapshot and git_history modes.
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class IngestionMode(str, Enum):
    """
    Ingestion processing mode.
    
    - SNAPSHOT: Fast mode, processes current files only (5-15 min for 5K files)
    - GIT_HISTORY: Complete mode, processes full Git commit history (2-4 hours for 5K files)
    """
    SNAPSHOT = "snapshot"
    GIT_HISTORY = "git_history"


class IngestRequest(BaseModel):
    """
    Request to start an ingestion job.
    
    Example (Snapshot mode - fast):
    ```json
    {
        "repo_path": "/app",
        "mode": "snapshot",
        "include_patterns": ["*.py", "*.md"],
        "exclude_patterns": ["test_*"]
    }
    ```
    
    Example (Git history mode - complete):
    ```json
    {
        "repo_path": "/app",
        "mode": "git_history"
    }
    ```
    """
    repo_path: str = Field(
        ...,
        description="Path to repository or directory to ingest",
        example="/app"
    )
    
    mode: IngestionMode = Field(
        default=IngestionMode.GIT_HISTORY,
        description=(
            "Processing mode:\n"
            "- 'snapshot': Fast (5-15 min for 5K files), current state only\n"
            "- 'git_history': Complete (2-4 hours for 5K files), full history"
        )
    )
    
    include_patterns: Optional[List[str]] = Field(
        default=None,
        description="File patterns to include (e.g., ['*.py', '*.md'])",
        example=["*.py", "*.md", "*.js"]
    )
    
    exclude_patterns: Optional[List[str]] = Field(
        default=None,
        description="File patterns to exclude (e.g., ['test_*', '*_test.py'])",
        example=["test_*", "*_test.py", "*.pyc"]
    )
    
    # Git history mode options
    max_commits: Optional[int] = Field(
        default=None,
        description="Max commits to process (git_history mode only)",
        ge=1,
        example=100
    )
    
    branch: Optional[str] = Field(
        default="main",
        description="Git branch to process (git_history mode only)",
        example="main"
    )

    class Config:
        use_enum_values = True


class IngestionJobResponse(BaseModel):
    """Response containing ingestion job details."""
    
    id: str = Field(..., description="Job ID")
    mode: str = Field(..., description="Processing mode")
    status: str = Field(..., description="Job status")
    repo_path: str = Field(..., description="Repository path")
    started_at: datetime = Field(..., description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    
    # Progress stats
    processed_documents: int = Field(0, description="Documents processed")
    failed_documents: int = Field(0, description="Documents failed")
    skipped_documents: int = Field(0, description="Documents skipped (duplicates)")
    total_documents: Optional[int] = Field(None, description="Total documents to process")
    
    # Additional info
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        from_attributes = True


class IngestionStatsResponse(BaseModel):
    """Ingestion statistics by mode."""
    
    total_jobs: int = Field(..., description="Total jobs")
    snapshot_jobs: int = Field(..., description="Snapshot mode jobs")
    git_history_jobs: int = Field(..., description="Git history mode jobs")
    
    avg_snapshot_duration_seconds: Optional[float] = Field(
        None,
        description="Average duration for snapshot mode"
    )
    avg_git_history_duration_seconds: Optional[float] = Field(
        None,
        description="Average duration for git_history mode"
    )
    
    speedup_factor: Optional[float] = Field(
        None,
        description="Speedup of snapshot vs git_history mode"
    )


class ModeComparisonResponse(BaseModel):
    """Comparison between snapshot and git_history modes."""
    
    snapshot_mode: dict = Field(
        ...,
        description="Snapshot mode characteristics",
        example={
            "speed": "5-15 minutes for 5,000 files",
            "use_case": "Initial setup, periodic updates, non-Git repos",
            "includes_history": False,
            "speedup": "10-100× faster"
        }
    )
    
    git_history_mode: dict = Field(
        ...,
        description="Git history mode characteristics",
        example={
            "speed": "2-4 hours for 5,000 files",
            "use_case": "Complete versioning, historical context",
            "includes_history": True,
            "speedup": "1×  (baseline)"
        }
    )

