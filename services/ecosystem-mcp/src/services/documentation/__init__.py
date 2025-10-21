"""
Documentation Generation Services (Phase 4)

Multi-pass documentation generation for codebases.
"""

from .doc_orchestrator import (
    DocumentationOrchestrator,
    DocumentationSet,
    PassResult,
    PassType,
    DocStatus,
    DocConfig,
    get_doc_orchestrator
)

__all__ = [
    "DocumentationOrchestrator",
    "DocumentationSet",
    "PassResult",
    "PassType",
    "DocStatus",
    "DocConfig",
    "get_doc_orchestrator",
]

