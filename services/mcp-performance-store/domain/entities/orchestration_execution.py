"""Orchestration Execution Entity - Domain Layer."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4

from services.mcp_performance_store.domain.value_objects.execution_status import ExecutionStatus


@dataclass
class OrchestrationExecution:
    """
    Represents a single execution of an MCP orchestration.
    
    Tracks the complete lifecycle of executing a query through the MCP ecosystem,
    including which MCPs were involved, patterns used, timings, and results.
    """
    
    # Identity
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    
    # Request info
    query: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    # MCP composition
    composition_id: Optional[str] = None
    mcp_ids: List[str] = field(default_factory=list)
    
    # Pattern usage
    pattern_name: Optional[str] = None
    pattern_config: Dict[str, Any] = field(default_factory=dict)
    
    # Timing metrics (milliseconds)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_duration_ms: float = 0.0
    
    # Breakdown timings
    interpretation_ms: float = 0.0
    retrieval_ms: float = 0.0
    pattern_execution_ms: float = 0.0
    composition_ms: float = 0.0
    
    # Status
    status: ExecutionStatus = ExecutionStatus.PENDING
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    # Results
    confidence: float = 0.0
    num_sources: int = 0
    response_length: int = 0
    
    # Metadata
    service: str = "mcp-orchestrator"  # Which service initiated this
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def mark_started(self) -> None:
        """Mark execution as started."""
        self.status = ExecutionStatus.RUNNING
        self.start_time = datetime.now()
    
    def mark_completed(
        self,
        confidence: float,
        num_sources: int,
        response_length: int
    ) -> None:
        """Mark execution as completed successfully."""
        self.status = ExecutionStatus.SUCCESS
        self.end_time = datetime.now()
        self.confidence = confidence
        self.num_sources = num_sources
        self.response_length = response_length
        self._calculate_duration()
    
    def mark_failed(self, error_message: str, error_type: str = "unknown") -> None:
        """Mark execution as failed."""
        self.status = ExecutionStatus.FAILED
        self.end_time = datetime.now()
        self.error_message = error_message
        self.error_type = error_type
        self._calculate_duration()
    
    def mark_timeout(self) -> None:
        """Mark execution as timed out."""
        self.status = ExecutionStatus.TIMEOUT
        self.end_time = datetime.now()
        self.error_message = "Execution timed out"
        self.error_type = "timeout"
        self._calculate_duration()
    
    def mark_cancelled(self) -> None:
        """Mark execution as cancelled."""
        self.status = ExecutionStatus.CANCELLED
        self.end_time = datetime.now()
        self._calculate_duration()
    
    def _calculate_duration(self) -> None:
        """Calculate total duration."""
        if self.end_time:
            delta = self.end_time - self.start_time
            self.total_duration_ms = delta.total_seconds() * 1000
    
    def get_duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.total_duration_ms / 1000.0
    
    def was_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.SUCCESS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "query": self.query,
            "context": self.context,
            "composition_id": self.composition_id,
            "mcp_ids": self.mcp_ids,
            "pattern_name": self.pattern_name,
            "pattern_config": self.pattern_config,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": self.total_duration_ms,
            "interpretation_ms": self.interpretation_ms,
            "retrieval_ms": self.retrieval_ms,
            "pattern_execution_ms": self.pattern_execution_ms,
            "composition_ms": self.composition_ms,
            "status": self.status.value,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "confidence": self.confidence,
            "num_sources": self.num_sources,
            "response_length": self.response_length,
            "service": self.service,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrchestrationExecution":
        """Create from dictionary."""
        return cls(
            execution_id=data["execution_id"],
            query=data["query"],
            context=data.get("context", {}),
            composition_id=data.get("composition_id"),
            mcp_ids=data.get("mcp_ids", []),
            pattern_name=data.get("pattern_name"),
            pattern_config=data.get("pattern_config", {}),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            total_duration_ms=data.get("total_duration_ms", 0.0),
            interpretation_ms=data.get("interpretation_ms", 0.0),
            retrieval_ms=data.get("retrieval_ms", 0.0),
            pattern_execution_ms=data.get("pattern_execution_ms", 0.0),
            composition_ms=data.get("composition_ms", 0.0),
            status=ExecutionStatus(data["status"]),
            error_message=data.get("error_message"),
            error_type=data.get("error_type"),
            confidence=data.get("confidence", 0.0),
            num_sources=data.get("num_sources", 0),
            response_length=data.get("response_length", 0),
            service=data.get("service", "mcp-orchestrator"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )