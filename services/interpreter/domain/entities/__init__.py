"""Interpreter Domain Entities.

Core business entities for the interpreter service following Domain-Driven Design principles.
"""

from .query import UserQuery, QueryIntent, QueryResult
from .workflow import Workflow, WorkflowExecution, WorkflowStatus
from .document import Document, DocumentProvenance, OutputFormat
from .execution import ExecutionResult, ExecutionStatus

__all__ = [
    "UserQuery",
    "QueryIntent",
    "QueryResult",
    "Workflow",
    "WorkflowExecution",
    "WorkflowStatus",
    "Document",
    "DocumentProvenance",
    "OutputFormat",
    "ExecutionResult",
    "ExecutionStatus",
]
