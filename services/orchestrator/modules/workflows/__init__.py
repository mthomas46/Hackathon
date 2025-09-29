"""LangGraph workflows for Orchestrator service.

This module contains predefined LangGraph workflows that leverage
the existing service ecosystem for common documentation tasks.
"""

from .document_analysis import create_document_analysis_workflow

# Additional workflows can be added as they are implemented
# from .code_documentation import create_code_documentation_workflow
# from .quality_assurance import create_quality_assurance_workflow

__all__ = [
    'create_document_analysis_workflow'
    # Additional workflows will be added here as implemented
]
