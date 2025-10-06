"""Parse Query Request DTO."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ParseQueryRequest:
    """
    DTO for parsing a natural language query.
    """
    
    # Required
    query: str  # Natural language query text
    
    # Optional context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Dict[str, Any] = None
    
    # Processing options
    use_cache: bool = True  # Whether to use cached results
    force_reparse: bool = False  # Force reparsing even if cached
    include_alternatives: bool = False  # Include alternative interpretations
    
    def __post_init__(self):
        """Validate the request."""
        if not self.query or not self.query.strip():
            raise ValueError("query is required and cannot be empty")
        
        if self.context is None:
            self.context = {}
        
        # Clean up query
        self.query = self.query.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "context": self.context,
            "use_cache": self.use_cache,
            "force_reparse": self.force_reparse,
            "include_alternatives": self.include_alternatives,
        }

