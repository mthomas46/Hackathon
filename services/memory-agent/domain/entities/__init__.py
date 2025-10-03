"""Domain entities for memory agent."""

from .memory_item import MemoryItem, MemoryType
from .memory_session import MemorySession
from .memory_context import (
    MemoryContext,
    WorkflowResult,
    ArtifactLink,
    WorkflowType
)

__all__ = [
    # Original entities
    "MemoryItem",
    "MemoryType",
    "MemorySession",
    # Phase 3 enhanced entities
    "MemoryContext",
    "WorkflowResult",
    "ArtifactLink",
    "WorkflowType"
]

