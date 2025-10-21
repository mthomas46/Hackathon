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
from .architecture_generator import ArchitectureGenerator
from .component_generator import ComponentGenerator
from .api_generator import APIReferenceGenerator
from .examples_generator import ExamplesGenerator
from .synthesis_generator import SynthesisGenerator

__all__ = [
    "DocumentationOrchestrator",
    "DocumentationSet",
    "PassResult",
    "PassType",
    "DocStatus",
    "DocConfig",
    "get_doc_orchestrator",
    "ArchitectureGenerator",
    "ComponentGenerator",
    "APIReferenceGenerator",
    "ExamplesGenerator",
    "SynthesisGenerator",
]

