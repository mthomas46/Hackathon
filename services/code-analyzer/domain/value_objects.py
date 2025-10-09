"""Value objects for code-analyzer domain."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List

from domain.exceptions import UnsupportedLanguageError, InvalidValueError


class Language(Enum):
    """Supported programming languages."""
    
    PYTHON = auto()
    JAVASCRIPT = auto()
    TYPESCRIPT = auto()
    JAVA = auto()
    GO = auto()
    RUST = auto()
    
    @property
    def extensions(self) -> List[str]:
        """Get file extensions for this language."""
        extensions_map = {
            Language.PYTHON: ['.py', '.pyw'],
            Language.JAVASCRIPT: ['.js', '.mjs'],
            Language.TYPESCRIPT: ['.ts'],
            Language.JAVA: ['.java'],
            Language.GO: ['.go'],
            Language.RUST: ['.rs']
        }
        return extensions_map.get(self, [])
    
    @classmethod
    def from_extension(cls, extension: str) -> 'Language':
        """Detect language from file extension."""
        for language in cls:
            if extension in language.extensions:
                return language
        raise UnsupportedLanguageError(f"Unsupported file extension: {extension}")


class AnalysisStatus(Enum):
    """Status of code analysis."""
    
    PENDING = auto()
    ANALYZING = auto()
    COMPLETED = auto()
    FAILED = auto()
    
    def can_transition_to(self, target: 'AnalysisStatus') -> bool:
        """Check if transition to target status is valid."""
        valid_transitions = {
            AnalysisStatus.PENDING: [AnalysisStatus.ANALYZING, AnalysisStatus.FAILED],
            AnalysisStatus.ANALYZING: [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED],
            AnalysisStatus.COMPLETED: [],  # Terminal state
            AnalysisStatus.FAILED: []  # Terminal state
        }
        return target in valid_transitions.get(self, [])


class Severity(Enum):
    """Severity levels for issues and findings."""
    
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1
    WARNING = 3  # Alias for MEDIUM
    
    def __lt__(self, other):
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value < other.value
    
    def __le__(self, other):
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value <= other.value
    
    def __gt__(self, other):
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value > other.value
    
    def __ge__(self, other):
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value >= other.value


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

