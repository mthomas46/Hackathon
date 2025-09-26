"""Workflow type value object."""

from enum import Enum


class WorkflowType(Enum):
    """Enumeration of possible workflow types."""

    # Document analysis workflows
    DOCUMENT_ANALYSIS = "document_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    DOCUMENT_VALIDATION = "document_validation"

    # PR and code analysis workflows
    PR_CONFIDENCE_ANALYSIS = "pr_confidence_analysis"
    CODE_REVIEW = "code_review"
    CODE_QUALITY_CHECK = "code_quality_check"

    # Testing and integration workflows
    END_TO_END_TEST = "end_to_end_test"
    INTEGRATION_TEST = "integration_test"
    PERFORMANCE_TEST = "performance_test"

    # Service orchestration workflows
    SERVICE_DEPLOYMENT = "service_deployment"
    SERVICE_HEALTH_CHECK = "service_health_check"
    SERVICE_COORDINATION = "service_coordination"

    # Generic workflows
    CUSTOM = "custom"
    AUTOMATED = "automated"
    MANUAL = "manual"

    def is_analysis_workflow(self) -> bool:
        """Check if this is a document/code analysis workflow."""
        return self in [
            WorkflowType.DOCUMENT_ANALYSIS,
            WorkflowType.DOCUMENT_PROCESSING,
            WorkflowType.DOCUMENT_VALIDATION,
            WorkflowType.PR_CONFIDENCE_ANALYSIS,
            WorkflowType.CODE_REVIEW,
            WorkflowType.CODE_QUALITY_CHECK
        ]

    def is_testing_workflow(self) -> bool:
        """Check if this is a testing workflow."""
        return self in [
            WorkflowType.END_TO_END_TEST,
            WorkflowType.INTEGRATION_TEST,
            WorkflowType.PERFORMANCE_TEST
        ]

    def is_service_workflow(self) -> bool:
        """Check if this is a service orchestration workflow."""
        return self in [
            WorkflowType.SERVICE_DEPLOYMENT,
            WorkflowType.SERVICE_HEALTH_CHECK,
            WorkflowType.SERVICE_COORDINATION
        ]

    def requires_approval(self) -> bool:
        """Check if this workflow type requires manual approval."""
        return self in [
            WorkflowType.SERVICE_DEPLOYMENT,
            WorkflowType.MANUAL
        ]
