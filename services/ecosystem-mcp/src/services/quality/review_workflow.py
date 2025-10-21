"""
Review Workflow Manager

Manages review queue and workflow for low-confidence documentation.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """Review status types."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


@dataclass
class ReviewItem:
    """Item queued for review."""
    id: str
    artifact_id: str
    artifact_title: str
    confidence_score: float
    priority: str
    status: ReviewStatus
    issues: List[str]
    recommendations: List[str]
    created_at: datetime
    assigned_to: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'artifact_id': self.artifact_id,
            'artifact_title': self.artifact_title,
            'confidence_score': self.confidence_score,
            'priority': self.priority,
            'status': self.status.value,
            'issues': self.issues,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat(),
            'assigned_to': self.assigned_to,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewer_notes': self.reviewer_notes
        }


class ReviewWorkflowManager:
    """
    Manages review workflow for documentation.
    
    Features:
    - Review queue management
    - Priority-based sorting
    - Status tracking
    - Feedback collection
    - Metrics tracking
    """
    
    def __init__(self):
        # In-memory queue (will be backed by database)
        self.review_queue: Dict[str, ReviewItem] = {}
        
        # Priority ordering
        self.priority_order = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3
        }
        
        logger.info("ReviewWorkflowManager initialized")
    
    async def queue_for_review(
        self,
        artifact_id: str,
        artifact_title: str,
        confidence_score: float,
        priority: str,
        issues: List[str],
        recommendations: List[str]
    ) -> ReviewItem:
        """
        Queue an artifact for review.
        
        Args:
            artifact_id: Artifact identifier
            artifact_title: Artifact title
            confidence_score: Overall confidence score
            priority: Review priority (critical, high, medium, low)
            issues: List of identified issues
            recommendations: List of recommendations
        
        Returns:
            Created review item
        """
        review_id = str(uuid.uuid4())
        
        review_item = ReviewItem(
            id=review_id,
            artifact_id=artifact_id,
            artifact_title=artifact_title,
            confidence_score=confidence_score,
            priority=priority,
            status=ReviewStatus.PENDING,
            issues=issues,
            recommendations=recommendations,
            created_at=datetime.now()
        )
        
        self.review_queue[review_id] = review_item
        
        logger.info(
            f"📋 Queued for review: {artifact_title} "
            f"(confidence: {confidence_score:.2f}, priority: {priority})"
        )
        
        return review_item
    
    async def get_review_queue(
        self,
        status: Optional[ReviewStatus] = None,
        priority: Optional[str] = None,
        limit: int = 100
    ) -> List[ReviewItem]:
        """
        Get review queue with optional filtering.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            limit: Maximum items to return
        
        Returns:
            List of review items, sorted by priority
        """
        items = list(self.review_queue.values())
        
        # Apply filters
        if status:
            items = [i for i in items if i.status == status]
        
        if priority:
            items = [i for i in items if i.priority == priority]
        
        # Sort by priority (critical first) then by confidence (lowest first)
        items.sort(
            key=lambda x: (
                self.priority_order.get(x.priority, 999),
                x.confidence_score
            )
        )
        
        return items[:limit]
    
    async def assign_review(
        self,
        review_id: str,
        reviewer: str
    ) -> Optional[ReviewItem]:
        """
        Assign a review to a reviewer.
        
        Args:
            review_id: Review item ID
            reviewer: Reviewer identifier
        
        Returns:
            Updated review item or None if not found
        """
        if review_id not in self.review_queue:
            logger.warning(f"Review item not found: {review_id}")
            return None
        
        item = self.review_queue[review_id]
        item.assigned_to = reviewer
        item.status = ReviewStatus.IN_REVIEW
        
        logger.info(f"👤 Assigned review {review_id} to {reviewer}")
        
        return item
    
    async def complete_review(
        self,
        review_id: str,
        status: ReviewStatus,
        reviewer_notes: Optional[str] = None
    ) -> Optional[ReviewItem]:
        """
        Complete a review.
        
        Args:
            review_id: Review item ID
            status: Final status (approved/rejected/needs_revision)
            reviewer_notes: Optional reviewer notes
        
        Returns:
            Updated review item or None if not found
        """
        if review_id not in self.review_queue:
            logger.warning(f"Review item not found: {review_id}")
            return None
        
        item = self.review_queue[review_id]
        item.status = status
        item.reviewed_at = datetime.now()
        item.reviewer_notes = reviewer_notes
        
        logger.info(
            f"✅ Review completed: {review_id} "
            f"(status: {status.value})"
        )
        
        return item
    
    async def get_review_metrics(self) -> Dict:
        """
        Get review workflow metrics.
        
        Returns:
            Dictionary of metrics
        """
        items = list(self.review_queue.values())
        
        if not items:
            return {
                'total_items': 0,
                'pending': 0,
                'in_review': 0,
                'completed': 0,
                'average_confidence': 0.0,
                'by_priority': {}
            }
        
        # Count by status
        status_counts = {}
        for status in ReviewStatus:
            status_counts[status.value] = sum(
                1 for i in items if i.status == status
            )
        
        # Count by priority
        priority_counts = {}
        for priority in ['critical', 'high', 'medium', 'low']:
            priority_counts[priority] = sum(
                1 for i in items if i.priority == priority
            )
        
        # Calculate average confidence
        avg_confidence = sum(i.confidence_score for i in items) / len(items)
        
        # Calculate completion rate
        completed = sum(
            1 for i in items 
            if i.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]
        )
        completion_rate = completed / len(items) if items else 0.0
        
        return {
            'total_items': len(items),
            'pending': status_counts.get('pending', 0),
            'in_review': status_counts.get('in_review', 0),
            'completed': completed,
            'completion_rate': completion_rate,
            'average_confidence': avg_confidence,
            'by_priority': priority_counts,
            'by_status': status_counts
        }
    
    async def get_next_review_item(
        self,
        reviewer: Optional[str] = None
    ) -> Optional[ReviewItem]:
        """
        Get next item for review (highest priority, lowest confidence).
        
        Args:
            reviewer: Optional reviewer to assign to
        
        Returns:
            Next review item or None if queue is empty
        """
        pending_items = await self.get_review_queue(
            status=ReviewStatus.PENDING,
            limit=1
        )
        
        if not pending_items:
            return None
        
        item = pending_items[0]
        
        if reviewer:
            await self.assign_review(item.id, reviewer)
        
        return item
    
    async def remove_from_queue(self, review_id: str) -> bool:
        """
        Remove item from review queue.
        
        Args:
            review_id: Review item ID
        
        Returns:
            True if removed, False if not found
        """
        if review_id in self.review_queue:
            del self.review_queue[review_id]
            logger.info(f"🗑️  Removed from queue: {review_id}")
            return True
        return False


# Singleton instance
_review_workflow_manager: Optional[ReviewWorkflowManager] = None


def get_review_workflow_manager() -> ReviewWorkflowManager:
    """Get or create singleton review workflow manager."""
    global _review_workflow_manager
    if _review_workflow_manager is None:
        _review_workflow_manager = ReviewWorkflowManager()
    return _review_workflow_manager

