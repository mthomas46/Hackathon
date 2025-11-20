"""
Documentation Generation Services

Provides adaptive, template-based documentation generation with
multi-pass refinement and complete transparency.
"""

# Legacy documentation system (existing)
from .doc_orchestrator import (
    get_doc_orchestrator,
    DocConfig,
    PassType,
    DocStatus,
    DocumentationSet
)

# New adaptive documentation system (Phase 4)
from .adaptive_orchestrator import (
    AdaptiveDocumentationOrchestrator,
    get_adaptive_orchestrator
)

# Documentation worker (Solution #1)
from .documentation_worker import (
    DocumentationWorker,
    get_documentation_worker,
    start_documentation_worker
)

__all__ = [
    # Legacy exports
    "get_doc_orchestrator",
    "DocConfig",
    "PassType",
    "DocStatus",
    "DocumentationSet",
    # New adaptive exports
    "AdaptiveDocumentationOrchestrator",
    "get_adaptive_orchestrator",
    # Worker exports
    "DocumentationWorker",
    "get_documentation_worker",
    "start_documentation_worker",
]
