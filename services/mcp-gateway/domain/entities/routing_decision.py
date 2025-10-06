"""Routing Decision Entity - Domain Layer."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid

from services.mcp_gateway.domain.value_objects.routing_strategy import RoutingStrategy


@dataclass
class RoutingDecision:
    """
    Represents a routing decision made by the Gateway.
    
    Captures which MCP instance was selected and why,
    for observability and debugging.
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Request details
    request_id: str = ""  # Original request ID
    mcp_type: str = ""  # Requested MCP type (e.g., "client-acme")
    
    # Routing decision
    selected_instance_id: Optional[str] = None
    selected_instance_url: Optional[str] = None
    strategy_used: RoutingStrategy = RoutingStrategy.ROUND_ROBIN
    
    # Decision metadata
    available_instances: int = 0
    considered_instances: list[str] = field(default_factory=list)
    excluded_instances: Dict[str, str] = field(default_factory=dict)  # instance_id -> reason
    
    # Decision factors
    decision_factors: Dict[str, Any] = field(default_factory=dict)
    selection_score: float = 0.0
    
    # Timestamps
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Result (updated after request completes)
    success: Optional[bool] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate the routing decision."""
        if not self.request_id:
            raise ValueError("RoutingDecision must have a request_id")
        if not self.mcp_type:
            raise ValueError("RoutingDecision must have an mcp_type")
    
    def mark_success(self, response_time_ms: float) -> None:
        """
        Mark the routing decision as successful.
        
        Args:
            response_time_ms: Request duration in milliseconds
        """
        self.success = True
        self.response_time_ms = response_time_ms
    
    def mark_failure(self, error_message: str) -> None:
        """
        Mark the routing decision as failed.
        
        Args:
            error_message: Error description
        """
        self.success = False
        self.error_message = error_message
    
    def add_excluded_instance(self, instance_id: str, reason: str) -> None:
        """
        Add an instance that was excluded from routing.
        
        Args:
            instance_id: Instance ID
            reason: Reason for exclusion
        """
        self.excluded_instances[instance_id] = reason
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "request_id": self.request_id,
            "mcp_type": self.mcp_type,
            "selected_instance_id": self.selected_instance_id,
            "selected_instance_url": self.selected_instance_url,
            "strategy_used": self.strategy_used.value,
            "available_instances": self.available_instances,
            "considered_instances": self.considered_instances,
            "excluded_instances": self.excluded_instances,
            "decision_factors": self.decision_factors,
            "selection_score": self.selection_score,
            "decided_at": self.decided_at.isoformat(),
            "success": self.success,
            "response_time_ms": self.response_time_ms,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoutingDecision":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            request_id=data["request_id"],
            mcp_type=data["mcp_type"],
            selected_instance_id=data.get("selected_instance_id"),
            selected_instance_url=data.get("selected_instance_url"),
            strategy_used=RoutingStrategy(data.get("strategy_used", "round_robin")),
            available_instances=data.get("available_instances", 0),
            considered_instances=data.get("considered_instances", []),
            excluded_instances=data.get("excluded_instances", {}),
            decision_factors=data.get("decision_factors", {}),
            selection_score=data.get("selection_score", 0.0),
            decided_at=datetime.fromisoformat(data["decided_at"]),
            success=data.get("success"),
            response_time_ms=data.get("response_time_ms"),
            error_message=data.get("error_message"),
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"RoutingDecision(request_id={self.request_id}, "
            f"selected={self.selected_instance_id}, "
            f"strategy={self.strategy_used}, success={self.success})"
        )

