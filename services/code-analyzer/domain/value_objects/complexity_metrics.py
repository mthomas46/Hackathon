"""Complexity metrics value object."""

from dataclasses import dataclass

from domain.exceptions import InvalidValueError


@dataclass(frozen=True)
class ComplexityMetrics:
    """Complexity metrics for code analysis."""
    
    cyclomatic_complexity: int
    cognitive_complexity: int
    maintainability_index: float
    lines_of_code: int
    comment_ratio: float
    
    def __post_init__(self):
        """Validate complexity metrics."""
        if self.cyclomatic_complexity < 0:
            raise InvalidValueError("Cyclomatic complexity cannot be negative")
        
        if self.cognitive_complexity < 0:
            raise InvalidValueError("Cognitive complexity cannot be negative")
        
        if not (0 <= self.maintainability_index <= 100):
            raise InvalidValueError("Maintainability index must be between 0 and 100")
        
        if self.lines_of_code < 0:
            raise InvalidValueError("Lines of code cannot be negative")
        
        if not (0.0 <= self.comment_ratio <= 1.0):
            raise InvalidValueError("Comment ratio must be between 0.0 and 1.0")

