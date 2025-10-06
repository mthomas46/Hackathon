"""Create Workflow Request DTO."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class CreateWorkflowRequest:
    """
    DTO for creating a new workflow.
    
    Can be created from a parsed query (from MCP Interpreter)
    or with custom parameters.
    """
    
    # Required
    original_query: str
    
    # From MCP Interpreter (optional)
    parsed_query_id: Optional[str] = None
    query_intent: Optional[str] = None
    query_complexity: Optional[int] = None
    required_tiers: Optional[List[int]] = None
    
    # User context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Execution preferences
    execution_strategy: Optional[str] = None  # Auto-select if not provided
    patterns_to_apply: Optional[List[str]] = None  # Auto-select if not provided
    max_duration_seconds: Optional[int] = None
    max_cost: Optional[float] = None
    requires_approval: bool = False
    
    # MCP selection filters
    client_ids: Optional[List[str]] = None
    project_ids: Optional[List[str]] = None
    team_ids: Optional[List[str]] = None
    
    # Additional context
    context: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Validate and initialize."""
        if not self.original_query or not self.original_query.strip():
            raise ValueError("original_query is required and cannot be empty")
        
        if self.context is None:
            self.context = {}
        
        if self.metadata is None:
            self.metadata = {}
        
        # Clean up query
        self.original_query = self.original_query.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_query": self.original_query,
            "parsed_query_id": self.parsed_query_id,
            "query_intent": self.query_intent,
            "query_complexity": self.query_complexity,
            "required_tiers": self.required_tiers,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "execution_strategy": self.execution_strategy,
            "patterns_to_apply": self.patterns_to_apply,
            "max_duration_seconds": self.max_duration_seconds,
            "max_cost": self.max_cost,
            "requires_approval": self.requires_approval,
            "client_ids": self.client_ids,
            "project_ids": self.project_ids,
            "team_ids": self.team_ids,
            "context": self.context,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_parsed_query(
        cls,
        parsed_query: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> "CreateWorkflowRequest":
        """
        Create from MCP Interpreter parsed query.
        
        Args:
            parsed_query: Parsed query data from interpreter
            user_id: Optional user ID
            session_id: Optional session ID
            **kwargs: Additional parameters
        
        Returns:
            CreateWorkflowRequest instance
        """
        return cls(
            original_query=parsed_query["original_query"],
            parsed_query_id=parsed_query["query_id"],
            query_intent=parsed_query["intent"],
            query_complexity=parsed_query.get("estimated_complexity", 5),
            required_tiers=parsed_query.get("required_tiers", []),
            user_id=user_id,
            session_id=session_id,
            **kwargs
        )

