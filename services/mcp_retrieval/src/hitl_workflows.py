"""
Human-in-the-Loop (HITL) Workflows for MCP System.

Implements approval queues and human review workflows for:
- High-stakes decisions
- Low-confidence predictions
- Policy violations
- Manual review requests
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid
import logging
import time
from threading import Lock

logger = logging.getLogger(__name__)


# ============================================================================
# Enumerations
# ============================================================================

class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DecisionType(Enum):
    """Type of decision requiring approval."""
    HIGH_STAKES = "high_stakes"  # Critical operations
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # Low confidence
    POLICY_VIOLATION = "policy_violation"  # Policy checks
    MANUAL_REVIEW = "manual_review"  # Explicit manual review


class ReviewAction(Enum):
    """Action taken during review."""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    ESCALATE = "escalate"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ApprovalRequest:
    """An approval request in the queue."""
    request_id: str
    decision_type: DecisionType
    content: Dict[str, Any]
    status: ApprovalStatus
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer: Optional[str] = None
    review_comment: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize audit trail."""
        if not self.audit_trail:
            self.audit_trail.append({
                "timestamp": self.created_at,
                "action": "created",
                "status": self.status.value,
            })


# ============================================================================
# Approval Queue
# ============================================================================

class ApprovalQueue:
    """
    Manage approval requests with queue operations.
    
    Supports:
    - Adding/retrieving requests
    - Reviewing and approving/rejecting
    - Filtering and sorting
    - Audit trail tracking
    - Statistics
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize approval queue.
        
        Args:
            max_size: Maximum number of requests in queue
        """
        self.max_size = max_size
        self._requests: Dict[str, ApprovalRequest] = {}
        self._lock = Lock()
        
        logger.info(f"ApprovalQueue initialized with max_size={max_size}")
    
    def create_request(
        self,
        decision_type: DecisionType,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ApprovalRequest:
        """
        Create a new approval request.
        
        Args:
            decision_type: Type of decision
            content: Request content
            metadata: Additional metadata
        
        Returns:
            New ApprovalRequest instance
        """
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        request = ApprovalRequest(
            request_id=request_id,
            decision_type=decision_type,
            content=content,
            status=ApprovalStatus.PENDING,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        logger.info(f"Created approval request: {request_id}")
        return request
    
    def add_request(self, request: ApprovalRequest) -> bool:
        """
        Add request to queue.
        
        Args:
            request: Approval request to add
        
        Returns:
            True if added successfully, False if queue full
        """
        with self._lock:
            if len(self._requests) >= self.max_size:
                logger.warning(f"Queue full ({self.max_size} requests), cannot add request")
                return False
            
            self._requests[request.request_id] = request
            logger.info(f"Added request to queue: {request.request_id}")
            return True
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """
        Get request by ID.
        
        Args:
            request_id: Request ID
        
        Returns:
            ApprovalRequest if found, None otherwise
        """
        with self._lock:
            return self._requests.get(request_id)
    
    def get_pending_requests(self, sort_by: Optional[str] = None) -> List[ApprovalRequest]:
        """
        Get all pending requests.
        
        Args:
            sort_by: Optional field to sort by ("priority", "created_at")
        
        Returns:
            List of pending requests
        """
        with self._lock:
            pending = [
                r for r in self._requests.values()
                if r.status == ApprovalStatus.PENDING
            ]
            
            # Sort if requested
            if sort_by == "priority":
                priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                pending.sort(
                    key=lambda r: priority_order.get(
                        r.metadata.get("priority", "low"), 3
                    )
                )
            elif sort_by == "created_at":
                pending.sort(key=lambda r: r.created_at)
            
            return pending
    
    def review_request(
        self,
        request_id: str,
        action: ReviewAction,
        reviewer: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Review and approve/reject a request.
        
        Args:
            request_id: Request ID to review
            action: Review action (approve, reject, etc.)
            reviewer: Reviewer identifier
            comment: Optional review comment
        
        Returns:
            True if reviewed successfully, False otherwise
        """
        with self._lock:
            request = self._requests.get(request_id)
            
            if not request:
                logger.warning(f"Request not found: {request_id}")
                return False
            
            # Can only review pending requests
            if request.status != ApprovalStatus.PENDING:
                logger.warning(f"Request {request_id} already reviewed (status: {request.status})")
                return False
            
            # Update status based on action
            if action == ReviewAction.APPROVE:
                request.status = ApprovalStatus.APPROVED
            elif action == ReviewAction.REJECT:
                request.status = ApprovalStatus.REJECTED
            # For REQUEST_CHANGES and ESCALATE, keep pending for now
            
            # Update request
            request.reviewed_at = datetime.now()
            request.reviewer = reviewer
            request.review_comment = comment
            
            # Add to audit trail
            request.audit_trail.append({
                "timestamp": request.reviewed_at,
                "action": "review",
                "review_action": action.value,
                "reviewer": reviewer,
                "comment": comment,
                "new_status": request.status.value,
            })
            
            logger.info(f"Reviewed request {request_id}: {action.value} by {reviewer}")
            return True
    
    def cancel_request(self, request_id: str) -> bool:
        """
        Cancel a pending request.
        
        Args:
            request_id: Request ID to cancel
        
        Returns:
            True if cancelled, False if not pending or not found
        """
        with self._lock:
            request = self._requests.get(request_id)
            
            if not request:
                return False
            
            # Can only cancel pending requests
            if request.status != ApprovalStatus.PENDING:
                return False
            
            request.status = ApprovalStatus.CANCELLED
            request.audit_trail.append({
                "timestamp": datetime.now(),
                "action": "cancelled",
                "new_status": ApprovalStatus.CANCELLED.value,
            })
            
            logger.info(f"Cancelled request: {request_id}")
            return True
    
    def filter_requests(
        self,
        status: Optional[ApprovalStatus] = None,
        decision_type: Optional[DecisionType] = None
    ) -> List[ApprovalRequest]:
        """
        Filter requests by criteria.
        
        Args:
            status: Filter by status
            decision_type: Filter by decision type
        
        Returns:
            Filtered list of requests
        """
        with self._lock:
            results = list(self._requests.values())
            
            if status:
                results = [r for r in results if r.status == status]
            
            if decision_type:
                results = [r for r in results if r.decision_type == decision_type]
            
            return results
    
    def get_audit_trail(self, request_id: str) -> List[Dict[str, Any]]:
        """
        Get audit trail for a request.
        
        Args:
            request_id: Request ID
        
        Returns:
            List of audit trail entries
        """
        with self._lock:
            request = self._requests.get(request_id)
            if request:
                return request.audit_trail.copy()
            return []
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            stats = {
                "total_requests": len(self._requests),
                "pending": 0,
                "approved": 0,
                "rejected": 0,
                "cancelled": 0,
            }
            
            for request in self._requests.values():
                stats[request.status.value] += 1
            
            return stats


# ============================================================================
# HITL Workflow
# ============================================================================

class HITLWorkflow:
    """
    Human-in-the-Loop workflow orchestrator.
    
    Manages:
    - Approval requirement decisions
    - Submission to approval queue
    - Waiting for approvals
    - Auto-approval for low-risk decisions
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.8,
        auto_approve_low_risk: bool = True
    ):
        """
        Initialize HITL workflow.
        
        Args:
            confidence_threshold: Minimum confidence for auto-approval
            auto_approve_low_risk: Whether to auto-approve low-risk decisions
        """
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError(f"Confidence threshold must be 0-1, got {confidence_threshold}")
        
        self.confidence_threshold = confidence_threshold
        self.auto_approve_low_risk = auto_approve_low_risk
        self.approval_queue = ApprovalQueue()
        
        logger.info(
            f"HITLWorkflow initialized: threshold={confidence_threshold}, "
            f"auto_approve={auto_approve_low_risk}"
        )
    
    def requires_approval(
        self,
        decision_type: DecisionType,
        confidence: float,
        content: Dict[str, Any]
    ) -> bool:
        """
        Determine if a decision requires human approval.
        
        Args:
            decision_type: Type of decision
            confidence: Confidence score (0-1)
            content: Decision content
        
        Returns:
            True if approval required, False otherwise
        """
        # Validate confidence
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {confidence}")
        
        # High-stakes decisions always require approval
        if decision_type == DecisionType.HIGH_STAKES:
            logger.info("High-stakes decision requires approval")
            return True
        
        # Policy violations always require approval
        if decision_type == DecisionType.POLICY_VIOLATION:
            logger.info("Policy violation requires approval")
            return True
        
        # Manual review explicitly requested
        if decision_type == DecisionType.MANUAL_REVIEW:
            logger.info("Manual review requested")
            return True
        
        # Confidence threshold check
        if decision_type == DecisionType.CONFIDENCE_THRESHOLD:
            if confidence < self.confidence_threshold:
                logger.info(
                    f"Low confidence ({confidence:.2f} < {self.confidence_threshold}) "
                    f"requires approval"
                )
                return True
            elif self.auto_approve_low_risk:
                logger.info(f"High confidence ({confidence:.2f}), auto-approving")
                return False
        
        return False
    
    def submit_for_approval(
        self,
        decision_type: DecisionType,
        content: Dict[str, Any],
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ApprovalRequest:
        """
        Submit a decision for approval.
        
        Args:
            decision_type: Type of decision
            content: Decision content
            confidence: Optional confidence score
            metadata: Additional metadata
        
        Returns:
            ApprovalRequest instance
        """
        # Create request
        request = self.approval_queue.create_request(
            decision_type=decision_type,
            content=content,
            metadata=metadata or {}
        )
        
        # Add confidence if provided
        if confidence is not None:
            request.metadata["confidence"] = confidence
        
        # Add to queue
        self.approval_queue.add_request(request)
        
        logger.info(f"Submitted for approval: {request.request_id}")
        return request
    
    def wait_for_approval(
        self,
        request_id: str,
        timeout_seconds: float = 30.0
    ) -> Optional[ApprovalRequest]:
        """
        Wait for a request to be approved (with timeout).
        
        Args:
            request_id: Request ID to wait for
            timeout_seconds: Maximum time to wait
        
        Returns:
            ApprovalRequest if approved/rejected, None if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            request = self.approval_queue.get_request(request_id)
            
            if not request:
                logger.warning(f"Request not found: {request_id}")
                return None
            
            if request.status != ApprovalStatus.PENDING:
                logger.info(f"Request {request_id} reviewed: {request.status.value}")
                return request
            
            # Sleep briefly before checking again
            time.sleep(0.1)
        
        logger.warning(f"Timeout waiting for approval: {request_id}")
        return self.approval_queue.get_request(request_id)
    
    def process_decision(
        self,
        decision_type: DecisionType,
        content: Dict[str, Any],
        confidence: float = 1.0,
        wait_for_approval: bool = False,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """
        Process a decision with automatic approval handling.
        
        Args:
            decision_type: Type of decision
            content: Decision content
            confidence: Confidence score
            wait_for_approval: Whether to wait for manual approval
            timeout_seconds: Timeout for waiting
        
        Returns:
            Dictionary with processing result
        """
        # Check if approval required
        requires_approval = self.requires_approval(
            decision_type=decision_type,
            confidence=confidence,
            content=content
        )
        
        if not requires_approval:
            # Auto-approve
            return {
                "approved": True,
                "auto_approved": True,
                "confidence": confidence,
                "decision_type": decision_type.value,
            }
        
        # Submit for approval
        request = self.submit_for_approval(
            decision_type=decision_type,
            content=content,
            confidence=confidence
        )
        
        if wait_for_approval:
            # Wait for human review
            result = self.wait_for_approval(request.request_id, timeout_seconds)
            
            if result and result.status == ApprovalStatus.APPROVED:
                return {
                    "approved": True,
                    "auto_approved": False,
                    "request_id": request.request_id,
                    "reviewer": result.reviewer,
                    "reviewed_at": result.reviewed_at,
                }
            else:
                return {
                    "approved": False,
                    "requires_approval": True,
                    "request_id": request.request_id,
                    "status": result.status.value if result else "pending",
                }
        else:
            # Don't wait, just queue
            return {
                "approved": False,
                "requires_approval": True,
                "request_id": request.request_id,
                "status": "pending",
            }


# ============================================================================
# Helper Functions
# ============================================================================

def create_approval_request(
    decision_type: DecisionType,
    content: Dict[str, Any],
    priority: str = "medium"
) -> ApprovalRequest:
    """
    Helper to create an approval request.
    
    Args:
        decision_type: Type of decision
        content: Request content
        priority: Priority level (low/medium/high/critical)
    
    Returns:
        ApprovalRequest instance
    """
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    return ApprovalRequest(
        request_id=request_id,
        decision_type=decision_type,
        content=content,
        status=ApprovalStatus.PENDING,
        created_at=datetime.now(),
        metadata={"priority": priority}
    )

