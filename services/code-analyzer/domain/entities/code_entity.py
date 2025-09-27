"""Code entity domain entity."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class CodeEntity:
    """Domain entity representing a code entity (class, function, etc.).

    Encapsulates metadata and analysis results for individual code entities
    extracted during code analysis.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = ""  # function, class, method, variable, etc.
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    content: str = ""

    # Analysis results
    complexity_score: int = 0
    parameters_count: int = 0
    return_type: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    docstring_present: bool = False
    test_coverage: Optional[float] = None

    # Quality metrics
    maintainability_index: Optional[float] = None
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0

    # Metadata
    language: str = ""
    framework: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate code entity after initialization."""
        if not self.name.strip():
            raise ValueError("Entity name cannot be empty")
        if not self.file_path.strip():
            raise ValueError("File path cannot be empty")
        if self.line_start < 0 or self.line_end < 0:
            raise ValueError("Line numbers cannot be negative")
        if self.line_start > self.line_end:
            raise ValueError("Start line cannot be greater than end line")

        # Ensure valid entity types
        valid_types = ["function", "class", "method", "variable", "constant", "interface", "enum"]
        if self.type.lower() not in valid_types:
            raise ValueError(f"Invalid entity type: {self.type}")

    @property
    def lines_of_code(self) -> int:
        """Calculate lines of code for this entity."""
        return self.line_end - self.line_start + 1

    @property
    def is_complex(self) -> bool:
        """Check if entity has high complexity."""
        return self.cyclomatic_complexity > 10 or self.cognitive_complexity > 15

    @property
    def has_good_coverage(self) -> bool:
        """Check if entity has good test coverage."""
        return self.test_coverage is not None and self.test_coverage >= 80.0

    @property
    def is_well_documented(self) -> bool:
        """Check if entity is well documented."""
        return self.docstring_present and len(self.content.split('\n')) > 5

    @property
    def quality_score(self) -> float:
        """Calculate overall quality score for this entity."""
        score = 100.0

        # Deduct for complexity
        if self.is_complex:
            score -= 20

        # Deduct for missing documentation
        if not self.docstring_present:
            score -= 15

        # Deduct for poor test coverage
        if self.test_coverage is not None and self.test_coverage < 60:
            score -= 10

        # Deduct for high parameter count
        if self.parameters_count > 5:
            score -= 5

        return max(0.0, score)

    def add_dependency(self, dependency: str) -> None:
        """Add a dependency to this entity."""
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)

    def add_tag(self, tag: str) -> None:
        """Add a tag to this entity."""
        if tag not in self.tags:
            self.tags.append(tag)

    def update_complexity(self, cyclomatic: int, cognitive: int) -> None:
        """Update complexity metrics."""
        self.cyclomatic_complexity = cyclomatic
        self.cognitive_complexity = cognitive

    def update_quality_metrics(self, maintainability: float, coverage: float) -> None:
        """Update quality metrics."""
        self.maintainability_index = maintainability
        self.test_coverage = coverage

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "content": self.content,
            "complexity_score": self.complexity_score,
            "parameters_count": self.parameters_count,
            "return_type": self.return_type,
            "dependencies": self.dependencies,
            "docstring_present": self.docstring_present,
            "test_coverage": self.test_coverage,
            "maintainability_index": self.maintainability_index,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "language": self.language,
            "framework": self.framework,
            "tags": self.tags,
            "analyzed_at": self.analyzed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeEntity':
        """Create CodeEntity from dictionary."""
        # Handle datetime conversion
        if isinstance(data.get("analyzed_at"), str):
            data["analyzed_at"] = datetime.fromisoformat(data["analyzed_at"].replace('Z', '+00:00'))

        return cls(**data)
