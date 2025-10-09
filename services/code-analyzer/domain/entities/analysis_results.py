"""AnalysisResults entity."""

from dataclasses import dataclass
from typing import List, Optional

from domain.value_objects import ComplexityMetrics, StyleIssue, SecurityFinding


@dataclass
class CodeStructure:
    """Represents a code structure (function, class, etc.)."""
    
    type: str  # 'function', 'class', 'method', etc.
    name: str
    line_start: int
    line_end: int
    complexity: Optional[int] = None
    docstring: Optional[str] = None


@dataclass
class AnalysisResults:
    """Results of code analysis."""
    
    structures: List[CodeStructure]
    complexity_metrics: dict
    security_findings: List[SecurityFinding] = None
    style_issues: List[StyleIssue] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.security_findings is None:
            self.security_findings = []
        if self.style_issues is None:
            self.style_issues = []
    
    @property
    def complexity(self) -> Optional[ComplexityMetrics]:
        """Get complexity metrics as ComplexityMetrics object."""
        if not self.complexity_metrics:
            return None
        
        return ComplexityMetrics(
            cyclomatic_complexity=self.complexity_metrics.get('cyclomatic_complexity', 0),
            cognitive_complexity=self.complexity_metrics.get('cognitive_complexity', 0),
            maintainability_index=self.complexity_metrics.get('maintainability_index', 0.0),
            lines_of_code=self.complexity_metrics.get('lines_of_code', 0),
            comment_ratio=self.complexity_metrics.get('comment_ratio', 0.0)
        )

