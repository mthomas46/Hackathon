"""
ExpertMatch value object.

Represents the result of matching an expert to a query,
including the overall score and individual component scores.
"""

from dataclasses import dataclass
from typing import Optional

from domain.entities.expert import Expert


@dataclass(frozen=True)  # Immutable value object
class ExpertMatch:
    """
    Represents a matched expert with relevance scores.
    
    This value object encapsulates the result of matching an expert
    to a query, including the overall relevance score and breakdown
    of individual scoring components.
    
    Attributes:
        expert: The matched expert
        overall_score: Overall relevance score (0.0 to 1.0)
        role_score: Score for role matching (0.0 to 1.0)
        topic_score: Score for topic matching (0.0 to 1.0)
        service_score: Score for service matching (0.0 to 1.0)
        document_score: Score for document matching (0.0 to 1.0)
        explanation: Human-readable explanation of the match
    """
    
    expert: Expert
    overall_score: float
    role_score: float = 0.0
    topic_score: float = 0.0
    service_score: float = 0.0
    document_score: float = 0.0
    explanation: str = ""
    
    def __post_init__(self):
        """Validate scores after initialization."""
        # Validate score ranges
        for score_name in ['overall_score', 'role_score', 'topic_score', 'service_score', 'document_score']:
            score = getattr(self, score_name)
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"{score_name} must be between 0.0 and 1.0, got {score}")
    
    def is_excellent_match(self, threshold: float = 0.8) -> bool:
        """
        Check if this is an excellent match.
        
        Args:
            threshold: Minimum score for excellent match (default 0.8)
            
        Returns:
            True if overall_score >= threshold
        """
        return self.overall_score >= threshold
    
    def is_good_match(self, threshold: float = 0.6) -> bool:
        """
        Check if this is a good match.
        
        Args:
            threshold: Minimum score for good match (default 0.6)
            
        Returns:
            True if overall_score >= threshold
        """
        return self.overall_score >= threshold
    
    def is_fair_match(self, threshold: float = 0.4) -> bool:
        """
        Check if this is a fair match.
        
        Args:
            threshold: Minimum score for fair match (default 0.4)
            
        Returns:
            True if overall_score >= threshold
        """
        return self.overall_score >= threshold
    
    def match_quality(self) -> str:
        """
        Get match quality label.
        
        Returns:
            "excellent", "good", "fair", or "poor"
        """
        if self.is_excellent_match():
            return "excellent"
        elif self.is_good_match():
            return "good"
        elif self.is_fair_match():
            return "fair"
        else:
            return "poor"
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the match
        """
        return {
            "expert": {
                "user_id": self.expert.user_id,
                "name": self.expert.name,
                "role": self.expert.role,
                "seniority": self.expert.seniority,
                "topics": self.expert.topics,
                "tags": self.expert.tags,
                "services": self.expert.services,
                "document_count": self.expert.document_count,
                "service_count": self.expert.service_count,
            },
            "scores": {
                "overall": round(self.overall_score, 3),
                "role": round(self.role_score, 3),
                "topic": round(self.topic_score, 3),
                "service": round(self.service_score, 3),
                "document": round(self.document_score, 3),
            },
            "match_quality": self.match_quality(),
            "explanation": self.explanation
        }
    
    def __str__(self) -> str:
        """String representation of match."""
        return (
            f"ExpertMatch(expert={self.expert.name}, "
            f"score={self.overall_score:.2f}, "
            f"quality={self.match_quality()})"
        )
    
    def __repr__(self) -> str:
        """Detailed representation of match."""
        return (
            f"ExpertMatch(expert={self.expert.user_id}, "
            f"overall={self.overall_score:.3f}, "
            f"role={self.role_score:.3f}, "
            f"topic={self.topic_score:.3f}, "
            f"service={self.service_score:.3f}, "
            f"document={self.document_score:.3f})"
        )

