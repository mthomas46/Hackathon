"""Style issue value object."""

from dataclasses import dataclass

from domain.value_objects.severity import Severity
from domain.exceptions import InvalidValueError


@dataclass(frozen=True)
class StyleIssue:
    """Style issue found in code."""
    
    severity: Severity
    line_number: int
    message: str
    rule_id: str
    
    def __post_init__(self):
        """Validate style issue."""
        if self.line_number <= 0:
            raise InvalidValueError("Line number must be positive")

