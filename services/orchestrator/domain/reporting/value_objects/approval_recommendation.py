"""Approval Recommendation Value Object"""

from enum import Enum


class ApprovalRecommendation(Enum):
    """Enumeration of approval recommendations."""

    APPROVE = "approve"                    # Ready for approval
    APPROVE_WITH_CONDITIONS = "approve_with_conditions"  # Approve with specific requirements
    REVIEW_REQUIRED = "review_required"    # Requires additional review
    REJECT = "reject"                     # Should not be approved
    ESCALATE = "escalate"                 # Requires higher-level review

    @property
    def description(self) -> str:
        """Get a human-readable description."""
        descriptions = {
            ApprovalRecommendation.APPROVE: "Ready for approval - meets all requirements",
            ApprovalRecommendation.APPROVE_WITH_CONDITIONS: "Can be approved with specific conditions met",
            ApprovalRecommendation.REVIEW_REQUIRED: "Requires additional review before approval",
            ApprovalRecommendation.REJECT: "Should not be approved due to critical issues",
            ApprovalRecommendation.ESCALATE: "Requires review by senior stakeholders"
        }
        return descriptions[self]

    @property
    def priority(self) -> int:
        """Get priority level (higher number = more urgent)."""
        priorities = {
            ApprovalRecommendation.REJECT: 5,
            ApprovalRecommendation.ESCALATE: 4,
            ApprovalRecommendation.REVIEW_REQUIRED: 3,
            ApprovalRecommendation.APPROVE_WITH_CONDITIONS: 2,
            ApprovalRecommendation.APPROVE: 1
        }
        return priorities[self]

    @property
    def requires_action(self) -> bool:
        """Check if this recommendation requires immediate action."""
        return self in (
            ApprovalRecommendation.REJECT,
            ApprovalRecommendation.ESCALATE,
            ApprovalRecommendation.REVIEW_REQUIRED
        )

    def __str__(self) -> str:
        return self.value.replace('_', ' ').title()
