"""Domain entities for code analyzer service."""

from .analysis_result import AnalysisResult
from .code_entity import CodeEntity
from .security_issue import SecurityIssue

__all__ = [
    "AnalysisResult",
    "CodeEntity",
    "SecurityIssue",
]
