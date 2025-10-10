"""
Route Module Exports.

This module exports all route routers for easy inclusion in the main FastAPI app.
Each router is organized by domain concern for maintainability and clarity.
"""

from .status_routes import router as status_router
from .findings_routes import router as findings_router
from .remediation_routes import router as remediation_router
from .workflow_routes import router as workflow_router
from .repository_routes import router as repository_router
from .pr_confidence_routes import router as pr_confidence_router
from .integration_routes import router as integration_router
from .report_routes import router as report_router
from .distributed_routes import router as distributed_router
from .analysis_routes import router as analysis_router

__all__ = [
    "status_router",
    "findings_router",
    "remediation_router",
    "workflow_router",
    "repository_router",
    "pr_confidence_router",
    "integration_router",
    "report_router",
    "distributed_router",
    "analysis_router",
]
