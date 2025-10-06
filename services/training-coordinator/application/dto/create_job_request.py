"""Create Job Request DTO."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from services.training_coordinator.domain.value_objects.job_priority import JobPriority
from services.training_coordinator.domain.value_objects.data_source import DataSource


@dataclass
class CreateJobRequest:
    """Request to create a new training job."""
    
    mcp_id: str
    name: str
    description: str
    data_sources: List[DataSource]
    source_config: Dict[str, Any] = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    max_documents: Optional[int] = None
    max_duration_seconds: Optional[int] = None
    created_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate request."""
        if not self.mcp_id:
            raise ValueError("MCP ID is required")
        if not self.name:
            raise ValueError("Name is required")
        if not self.data_sources:
            raise ValueError("At least one data source required")

