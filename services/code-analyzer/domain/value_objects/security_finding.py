"""Security finding value object."""

from dataclasses import dataclass

from domain.value_objects.severity import Severity
from domain.exceptions import InvalidValueError


@dataclass(frozen=True)
class SecurityFinding:
    """Security vulnerability found in code."""
    
    severity: Severity
    vulnerability_type: str
    line_number: int
    description: str
    recommendation: str
    
    def __post_init__(self):
        """Validate security finding."""
        if self.line_number <= 0:
            raise InvalidValueError("Line number must be positive")
        
        if not self.recommendation or not self.recommendation.strip():
            raise InvalidValueError("Security finding must have a recommendation")

