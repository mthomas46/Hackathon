"""
Feedback System for MCP - Continuous Improvement.

Collects user feedback, ratings, and improvement suggestions for:
- Retrieval quality
- Pruning effectiveness
- Approval decisions
- Overall system performance
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# Enumerations
# ============================================================================

class FeedbackType(Enum):
    """Type of feedback."""
    RETRIEVAL_QUALITY = "retrieval_quality"
    PRUNING_QUALITY = "pruning_quality"
    APPROVAL_DECISION = "approval_decision"
    SYSTEM_PERFORMANCE = "system_performance"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"


class Rating(Enum):
    """Feedback rating (1-5 stars)."""
    ONE_STAR = 1
    TWO_STARS = 2
    THREE_STARS = 3
    FOUR_STARS = 4
    FIVE_STARS = 5


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class FeedbackEntry:
    """A single feedback entry."""
    feedback_id: str
    feedback_type: FeedbackType
    rating: Rating
    comment: Optional[str]
    context: Dict[str, Any]
    user_id: Optional[str]
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackStats:
    """Feedback statistics."""
    total_feedback: int
    average_rating: float
    rating_distribution: Dict[int, int]
    by_type: Dict[str, int]
    recent_feedback: List[FeedbackEntry]


# ============================================================================
# Feedback Store (In-Memory)
# ============================================================================

class FeedbackStore:
    """
    In-memory feedback storage.
    
    In production, replace with Redis or database.
    """
    
    def __init__(self, max_entries: int = 10000):
        """Initialize feedback store."""
        self.max_entries = max_entries
        self._feedback: Dict[str, FeedbackEntry] = {}
        logger.info(f"FeedbackStore initialized (max_entries={max_entries})")
    
    def add_feedback(self, entry: FeedbackEntry) -> bool:
        """Add feedback entry."""
        if len(self._feedback) >= self.max_entries:
            # Remove oldest entries
            oldest = sorted(self._feedback.values(), key=lambda x: x.created_at)[:100]
            for old in oldest:
                del self._feedback[old.feedback_id]
        
        self._feedback[entry.feedback_id] = entry
        return True
    
    def get_feedback(self, feedback_id: str) -> Optional[FeedbackEntry]:
        """Get feedback by ID."""
        return self._feedback.get(feedback_id)
    
    def get_all_feedback(self) -> List[FeedbackEntry]:
        """Get all feedback entries."""
        return list(self._feedback.values())
    
    def get_by_type(self, feedback_type: FeedbackType) -> List[FeedbackEntry]:
        """Get feedback by type."""
        return [f for f in self._feedback.values() if f.feedback_type == feedback_type]
    
    def get_statistics(self) -> FeedbackStats:
        """Calculate feedback statistics."""
        entries = list(self._feedback.values())
        
        if not entries:
            return FeedbackStats(
                total_feedback=0,
                average_rating=0.0,
                rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                by_type={},
                recent_feedback=[]
            )
        
        # Calculate average rating
        ratings = [e.rating.value for e in entries]
        avg_rating = sum(ratings) / len(ratings)
        
        # Rating distribution
        rating_dist = defaultdict(int)
        for r in ratings:
            rating_dist[r] += 1
        
        # By type
        by_type = defaultdict(int)
        for e in entries:
            by_type[e.feedback_type.value] += 1
        
        # Recent feedback
        recent = sorted(entries, key=lambda x: x.created_at, reverse=True)[:10]
        
        return FeedbackStats(
            total_feedback=len(entries),
            average_rating=avg_rating,
            rating_distribution=dict(rating_dist),
            by_type=dict(by_type),
            recent_feedback=recent
        )


# ============================================================================
# Feedback System
# ============================================================================

class FeedbackSystem:
    """
    Main feedback system for collecting and analyzing user feedback.
    """
    
    def __init__(self, store: Optional[FeedbackStore] = None):
        """Initialize feedback system."""
        self.store = store or FeedbackStore()
        logger.info("FeedbackSystem initialized")
    
    def submit_feedback(
        self,
        feedback_type: FeedbackType,
        rating: Rating,
        comment: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FeedbackEntry:
        """
        Submit feedback.
        
        Args:
            feedback_type: Type of feedback
            rating: Rating (1-5)
            comment: Optional comment
            context: Context information
            user_id: Optional user identifier
            metadata: Additional metadata
        
        Returns:
            FeedbackEntry instance
        """
        feedback_id = f"fb_{uuid.uuid4().hex[:12]}"
        
        entry = FeedbackEntry(
            feedback_id=feedback_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment,
            context=context or {},
            user_id=user_id,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        self.store.add_feedback(entry)
        logger.info(f"Feedback submitted: {feedback_id} ({feedback_type.value}, {rating.value}⭐)")
        
        return entry
    
    def get_feedback(self, feedback_id: str) -> Optional[FeedbackEntry]:
        """Get feedback by ID."""
        return self.store.get_feedback(feedback_id)
    
    def get_statistics(self) -> FeedbackStats:
        """Get feedback statistics."""
        return self.store.get_statistics()
    
    def get_by_type(self, feedback_type: FeedbackType) -> List[FeedbackEntry]:
        """Get feedback by type."""
        return self.store.get_by_type(feedback_type)
    
    def analyze_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze feedback trends over time.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Trend analysis dictionary
        """
        entries = self.store.get_all_feedback()
        cutoff = datetime.now() - timedelta(days=days)
        recent = [e for e in entries if e.created_at >= cutoff]
        
        if not recent:
            return {"trend": "no_data", "entries": 0}
        
        # Calculate average rating over time
        ratings = [e.rating.value for e in recent]
        avg_rating = sum(ratings) / len(ratings)
        
        # Identify trending issues
        low_ratings = [e for e in recent if e.rating.value <= 2]
        
        return {
            "period_days": days,
            "total_entries": len(recent),
            "average_rating": avg_rating,
            "low_ratings_count": len(low_ratings),
            "trend": "positive" if avg_rating >= 4 else "neutral" if avg_rating >= 3 else "negative"
        }
    
    def get_improvement_suggestions(self, min_rating: int = 3) -> List[FeedbackEntry]:
        """
        Get feedback entries with improvement suggestions.
        
        Args:
            min_rating: Minimum rating to filter by
        
        Returns:
            List of feedback entries with suggestions
        """
        all_feedback = self.store.get_all_feedback()
        return [
            f for f in all_feedback
            if f.rating.value <= min_rating and f.comment
        ]


# ============================================================================
# Helper Functions
# ============================================================================

def create_feedback(
    feedback_type: FeedbackType,
    rating: int,
    comment: str = None,
    **kwargs
) -> FeedbackEntry:
    """Helper to create feedback entry."""
    return FeedbackEntry(
        feedback_id=f"fb_{uuid.uuid4().hex[:12]}",
        feedback_type=feedback_type,
        rating=Rating(rating),
        comment=comment,
        context=kwargs.get("context", {}),
        user_id=kwargs.get("user_id"),
        created_at=datetime.now(),
        metadata=kwargs.get("metadata", {})
    )


# Make timedelta available for analysis
from datetime import timedelta

