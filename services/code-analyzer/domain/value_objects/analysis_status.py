"""Analysis status value object."""

from enum import Enum
from typing import Optional, List


class AnalysisStatus(Enum):
    """Enumeration of analysis processing statuses."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    EXTRACTING_ENDPOINTS = "extracting_endpoints"
    CHECKING_SECURITY = "checking_security"
    VALIDATING_STYLE = "validating_style"
    CALCULATING_METRICS = "calculating_metrics"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"

    @classmethod
    def from_string(cls, value: str) -> Optional['AnalysisStatus']:
        """Create analysis status from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def get_display_name(self) -> str:
        """Get human-readable display name."""
        display_names = {
            "pending": "Pending Analysis",
            "analyzing": "Analyzing Code",
            "extracting_endpoints": "Extracting Endpoints",
            "checking_security": "Checking Security",
            "validating_style": "Validating Style",
            "calculating_metrics": "Calculating Metrics",
            "completed": "Analysis Completed",
            "failed": "Analysis Failed",
            "partial_success": "Partial Success",
        }
        return display_names.get(self.value, self.value.title())

    def is_terminal(self) -> bool:
        """Check if this is a terminal status (analysis complete)."""
        return self in [self.COMPLETED, self.FAILED, self.PARTIAL_SUCCESS]

    def is_success(self) -> bool:
        """Check if this status represents successful completion."""
        return self in [self.COMPLETED, self.PARTIAL_SUCCESS]

    def is_processing(self) -> bool:
        """Check if this status indicates analysis is in progress."""
        return self in [
            self.ANALYZING,
            self.EXTRACTING_ENDPOINTS,
            self.CHECKING_SECURITY,
            self.VALIDATING_STYLE,
            self.CALCULATING_METRICS
        ]

    @classmethod
    def get_processing_statuses(cls) -> List['AnalysisStatus']:
        """Get all processing statuses."""
        return [status for status in cls if status.is_processing()]

    @classmethod
    def get_terminal_statuses(cls) -> List['AnalysisStatus']:
        """Get all terminal statuses."""
        return [status for status in cls if status.is_terminal()]

    def can_transition_to(self, new_status: 'AnalysisStatus') -> bool:
        """Check if transition to new status is allowed."""
        # Define valid transitions (supports both simple and complex workflows)
        valid_transitions = {
            self.PENDING: [self.ANALYZING, self.FAILED],
            self.ANALYZING: [self.EXTRACTING_ENDPOINTS, self.COMPLETED, self.FAILED],  # Allow direct completion
            self.EXTRACTING_ENDPOINTS: [self.CHECKING_SECURITY, self.FAILED],
            self.CHECKING_SECURITY: [self.VALIDATING_STYLE, self.FAILED],
            self.VALIDATING_STYLE: [self.CALCULATING_METRICS, self.FAILED],
            self.CALCULATING_METRICS: [self.COMPLETED, self.PARTIAL_SUCCESS, self.FAILED],
            self.COMPLETED: [],  # Terminal
            self.FAILED: [],     # Terminal
            self.PARTIAL_SUCCESS: [],  # Terminal
        }

        return new_status in valid_transitions.get(self, [])
