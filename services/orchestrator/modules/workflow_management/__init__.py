#!/usr/bin/env python3
"""
Workflow Management Module

Provides comprehensive workflow management capabilities for the orchestrator service.
Supports creation, execution, monitoring, and management of complex workflows.
"""

from .models import (
    WorkflowDefinition, WorkflowExecution, WorkflowParameter, WorkflowAction,
    WorkflowStatus, WorkflowExecutionStatus, ActionType, ParameterType,
    WORKFLOW_TEMPLATES, create_workflow_from_template
)

from .repository import WorkflowRepository

from .service import WorkflowManagementService

from .api import router as workflow_api_router

__all__ = [
    # Models
    "WorkflowDefinition",
    "WorkflowExecution",
    "WorkflowParameter",
    "WorkflowAction",
    "WorkflowStatus",
    "WorkflowExecutionStatus",
    "ActionType",
    "ParameterType",
    "WORKFLOW_TEMPLATES",
    "create_workflow_from_template",

    # Repository
    "WorkflowRepository",

    # Service
    "WorkflowManagementService",

    # API
    "workflow_api_router"
]


# Global instances for easy access
_workflow_service = None

def get_workflow_service() -> WorkflowManagementService:
    """Get the global workflow management service instance."""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowManagementService()
    return _workflow_service

def initialize_workflow_management():
    """Initialize the workflow management module."""
    print("🔧 Initializing Workflow Management Module...")

    # Get service instance to initialize it
    service = get_workflow_service()

    print("✅ Workflow Management Module initialized")
    print("   • Workflow definitions: Supported")
    print("   • Parameter validation: Enabled")
    print("   • Action execution: Ready")
    print("   • Dependency management: Active")
    print("   • Execution monitoring: Enabled")

    return service
