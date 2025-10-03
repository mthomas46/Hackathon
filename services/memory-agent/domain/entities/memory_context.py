"""
Memory Context - Phase 3 Day 1
Enhanced context storage for workflow results and artifact linking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum


class WorkflowType(Enum):
    """Types of workflows tracked in memory."""
    ORCHESTRATION = "orchestration"
    WORKFLOW_A = "workflow_a"  # Feature Decomposition
    WORKFLOW_B = "workflow_b"  # Historical Context
    WORKFLOW_C = "workflow_c"  # Timeline Analysis
    WORKFLOW_D = "workflow_d"  # Skills Matching
    INTERPRETER = "interpreter"
    CUSTOM = "custom"


@dataclass
class ArtifactLink:
    """Links workflow results to external artifacts."""
    
    artifact_id: str
    artifact_type: str  # "document", "prompt", "user", "code", "report"
    source_service: str  # "doc-store", "prompt-store", "user-store", etc.
    artifact_url: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "source_service": self.source_service,
            "artifact_url": self.artifact_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArtifactLink":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return cls(
            artifact_id=data["artifact_id"],
            artifact_type=data["artifact_type"],
            source_service=data["source_service"],
            artifact_url=data["artifact_url"],
            created_at=created_at or datetime.utcnow(),
            metadata=data.get("metadata", {})
        )


@dataclass
class WorkflowResult:
    """Stores complete workflow execution result."""
    
    result_id: str
    workflow_id: str
    workflow_type: WorkflowType
    
    # Result data
    result_data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    
    # Artifacts
    artifacts: List[ArtifactLink] = field(default_factory=list)
    
    # Performance metrics
    duration_ms: float = 0.0
    services_called: List[str] = field(default_factory=list)
    
    # Timestamps
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_artifact(self, artifact: ArtifactLink) -> None:
        """Add an artifact link to this result."""
        self.artifacts.append(artifact)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "result_id": self.result_id,
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type.value if isinstance(self.workflow_type, WorkflowType) else self.workflow_type,
            "result_data": self.result_data,
            "success": self.success,
            "error_message": self.error_message,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "duration_ms": self.duration_ms,
            "services_called": self.services_called,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowResult":
        """Create from dictionary."""
        workflow_type = data.get("workflow_type")
        if isinstance(workflow_type, str):
            workflow_type = WorkflowType(workflow_type)
        
        started_at = data.get("started_at")
        if started_at and isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        
        completed_at = data.get("completed_at")
        if completed_at and isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
        
        artifacts = [
            ArtifactLink.from_dict(a) for a in data.get("artifacts", [])
        ]
        
        return cls(
            result_id=data["result_id"],
            workflow_id=data["workflow_id"],
            workflow_type=workflow_type,
            result_data=data.get("result_data", {}),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            artifacts=artifacts,
            duration_ms=data.get("duration_ms", 0.0),
            services_called=data.get("services_called", []),
            started_at=started_at or datetime.utcnow(),
            completed_at=completed_at or datetime.utcnow()
        )


@dataclass
class MemoryContext:
    """
    Enhanced memory context with artifact linking.
    
    This is the central data structure for Phase 3, storing:
    - Workflow execution results
    - Links to external artifacts (documents, prompts, users)
    - Context data for workflow coordination
    - Version history
    - TTL management
    """
    
    context_id: str
    workflow_id: str
    parent_workflow_id: Optional[str]
    workflow_type: WorkflowType
    
    # Core data
    context_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Artifact links (NEW for Phase 3)
    linked_documents: List[str] = field(default_factory=list)  # Doc Store IDs
    linked_prompts: List[str] = field(default_factory=list)    # Prompt Store IDs
    linked_users: List[str] = field(default_factory=list)      # User Store IDs
    linked_artifacts: List[ArtifactLink] = field(default_factory=list)
    
    # Workflow results (NEW for Phase 3)
    workflow_results: Dict[str, WorkflowResult] = field(default_factory=dict)
    
    # Versioning
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # TTL management
    ttl_seconds: int = 86400  # 24 hours default
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize expires_at based on ttl_seconds."""
        if self.expires_at is None and self.ttl_seconds:
            self.expires_at = self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def add_workflow_result(self, result: WorkflowResult) -> None:
        """Add a workflow result to this context."""
        self.workflow_results[result.workflow_id] = result
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def add_artifact_link(self, artifact: ArtifactLink) -> None:
        """Add an artifact link."""
        self.linked_artifacts.append(artifact)
        self.updated_at = datetime.utcnow()
        self.version += 1
    
    def link_document(self, document_id: str) -> None:
        """Link a Doc Store document."""
        if document_id not in self.linked_documents:
            self.linked_documents.append(document_id)
            self.updated_at = datetime.utcnow()
            self.version += 1
    
    def link_prompt(self, prompt_id: str) -> None:
        """Link a Prompt Store prompt."""
        if prompt_id not in self.linked_prompts:
            self.linked_prompts.append(prompt_id)
            self.updated_at = datetime.utcnow()
            self.version += 1
    
    def link_user(self, user_id: str) -> None:
        """Link a User Store user."""
        if user_id not in self.linked_users:
            self.linked_users.append(user_id)
            self.updated_at = datetime.utcnow()
            self.version += 1
    
    def is_expired(self) -> bool:
        """Check if context has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def extend_ttl(self, additional_seconds: int) -> None:
        """Extend the TTL of this context."""
        if self.expires_at:
            self.expires_at += timedelta(seconds=additional_seconds)
        self.updated_at = datetime.utcnow()
    
    def get_all_artifacts(self) -> List[ArtifactLink]:
        """Get all artifact links including those in workflow results."""
        all_artifacts = list(self.linked_artifacts)
        
        for result in self.workflow_results.values():
            all_artifacts.extend(result.artifacts)
        
        return all_artifacts
    
    def get_workflow_result(self, workflow_id: str) -> Optional[WorkflowResult]:
        """Get a specific workflow result."""
        return self.workflow_results.get(workflow_id)
    
    def get_successful_workflows(self) -> List[WorkflowResult]:
        """Get all successful workflow results."""
        return [r for r in self.workflow_results.values() if r.success]
    
    def get_failed_workflows(self) -> List[WorkflowResult]:
        """Get all failed workflow results."""
        return [r for r in self.workflow_results.values() if not r.success]
    
    @property
    def total_workflows(self) -> int:
        """Total number of workflows tracked."""
        return len(self.workflow_results)
    
    @property
    def successful_workflows(self) -> int:
        """Number of successful workflows."""
        return len(self.get_successful_workflows())
    
    @property
    def failed_workflows(self) -> int:
        """Number of failed workflows."""
        return len(self.get_failed_workflows())
    
    @property
    def success_rate(self) -> float:
        """Calculate workflow success rate."""
        if self.total_workflows == 0:
            return 0.0
        return self.successful_workflows / self.total_workflows
    
    @property
    def age_seconds(self) -> float:
        """Get age of context in seconds."""
        return (datetime.utcnow() - self.created_at).total_seconds()
    
    @property
    def time_until_expiry_seconds(self) -> Optional[float]:
        """Get time until expiry in seconds."""
        if self.expires_at is None:
            return None
        return (self.expires_at - datetime.utcnow()).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "context_id": self.context_id,
            "workflow_id": self.workflow_id,
            "parent_workflow_id": self.parent_workflow_id,
            "workflow_type": self.workflow_type.value if isinstance(self.workflow_type, WorkflowType) else self.workflow_type,
            "context_data": self.context_data,
            "metadata": self.metadata,
            "linked_documents": self.linked_documents,
            "linked_prompts": self.linked_prompts,
            "linked_users": self.linked_users,
            "linked_artifacts": [a.to_dict() for a in self.linked_artifacts],
            "workflow_results": {
                wid: result.to_dict() for wid, result in self.workflow_results.items()
            },
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "ttl_seconds": self.ttl_seconds,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryContext":
        """Create from dictionary."""
        workflow_type = data.get("workflow_type")
        if isinstance(workflow_type, str):
            workflow_type = WorkflowType(workflow_type)
        
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        expires_at = data.get("expires_at")
        if expires_at and isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        
        linked_artifacts = [
            ArtifactLink.from_dict(a) for a in data.get("linked_artifacts", [])
        ]
        
        workflow_results = {
            wid: WorkflowResult.from_dict(result_dict)
            for wid, result_dict in data.get("workflow_results", {}).items()
        }
        
        return cls(
            context_id=data["context_id"],
            workflow_id=data["workflow_id"],
            parent_workflow_id=data.get("parent_workflow_id"),
            workflow_type=workflow_type,
            context_data=data.get("context_data", {}),
            metadata=data.get("metadata", {}),
            linked_documents=data.get("linked_documents", []),
            linked_prompts=data.get("linked_prompts", []),
            linked_users=data.get("linked_users", []),
            linked_artifacts=linked_artifacts,
            workflow_results=workflow_results,
            version=data.get("version", 1),
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
            ttl_seconds=data.get("ttl_seconds", 86400),
            expires_at=expires_at
        )

