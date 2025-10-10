"""
ExpertQuery value object.

Represents a query for finding experts, including search criteria
and filtering parameters.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)  # Immutable value object
class ExpertQuery:
    """
    Represents a query for finding experts.
    
    This value object encapsulates all the parameters needed to search
    for and match experts, including role, topics, services, and limits.
    
    Attributes:
        query_text: Natural language query text
        role: Specific role to match (optional)
        topics: List of topics to match (optional)
        services: List of services to match (optional)
        tags: List of tags to match (optional)
        limit: Maximum number of results to return
        min_score: Minimum relevance score threshold
        sme_only: If True, only return Subject Matter Experts
        min_documents: Minimum document count for SME filtering
    """
    
    query_text: str
    role: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    limit: int = 10
    min_score: float = 0.0
    sme_only: bool = False
    min_documents: int = 10
    
    def __post_init__(self):
        """Validate query after initialization."""
        # Validate query text
        if not self.query_text or not self.query_text.strip():
            raise ValueError("query_text cannot be empty")
        
        # Validate limit
        if self.limit < 1:
            raise ValueError(f"limit must be at least 1, got {self.limit}")
        if self.limit > 100:
            raise ValueError(f"limit must not exceed 100, got {self.limit}")
        
        # Validate min_score
        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError(f"min_score must be between 0.0 and 1.0, got {self.min_score}")
        
        # Validate min_documents
        if self.min_documents < 0:
            raise ValueError(f"min_documents must be non-negative, got {self.min_documents}")
    
    def has_role_filter(self) -> bool:
        """Check if query has a role filter."""
        return self.role is not None and len(self.role.strip()) > 0
    
    def has_topic_filters(self) -> bool:
        """Check if query has topic filters."""
        return len(self.topics) > 0
    
    def has_service_filters(self) -> bool:
        """Check if query has service filters."""
        return len(self.services) > 0
    
    def has_tag_filters(self) -> bool:
        """Check if query has tag filters."""
        return len(self.tags) > 0
    
    def has_any_filters(self) -> bool:
        """Check if query has any filters applied."""
        return (
            self.has_role_filter() or
            self.has_topic_filters() or
            self.has_service_filters() or
            self.has_tag_filters()
        )
    
    def is_sme_query(self) -> bool:
        """Check if this is a query for Subject Matter Experts only."""
        return self.sme_only
    
    def get_normalized_query_text(self) -> str:
        """
        Get normalized query text for matching.
        
        Returns:
            Lowercase, stripped query text
        """
        return self.query_text.lower().strip()
    
    def get_keywords(self) -> List[str]:
        """
        Extract keywords from query text.
        
        Returns:
            List of keywords from the query
        """
        # Simple keyword extraction (split on whitespace)
        # Could be enhanced with stop-word filtering
        keywords = self.get_normalized_query_text().split()
        return [k for k in keywords if len(k) > 2]  # Filter out very short words
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for logging/serialization.
        
        Returns:
            Dictionary representation of the query
        """
        return {
            "query_text": self.query_text,
            "role": self.role,
            "topics": self.topics,
            "services": self.services,
            "tags": self.tags,
            "limit": self.limit,
            "min_score": self.min_score,
            "sme_only": self.sme_only,
            "min_documents": self.min_documents,
        }
    
    def __str__(self) -> str:
        """String representation of query."""
        filters = []
        if self.has_role_filter():
            filters.append(f"role={self.role}")
        if self.has_topic_filters():
            filters.append(f"topics={len(self.topics)}")
        if self.has_service_filters():
            filters.append(f"services={len(self.services)}")
        if self.sme_only:
            filters.append("SME_ONLY")
        
        filter_str = f" [{', '.join(filters)}]" if filters else ""
        return f"ExpertQuery('{self.query_text}'{filter_str}, limit={self.limit})"
    
    def __repr__(self) -> str:
        """Detailed representation of query."""
        return (
            f"ExpertQuery(query_text='{self.query_text}', "
            f"role={self.role}, topics={self.topics}, "
            f"services={self.services}, limit={self.limit}, "
            f"min_score={self.min_score}, sme_only={self.sme_only})"
        )

