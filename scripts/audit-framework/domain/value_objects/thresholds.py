"""
ThresholdConfig Value Object

Immutable value object representing audit scoring thresholds
and configuration parameters with validation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass(frozen=True)
class ThresholdConfig:
    """Immutable value object representing audit scoring thresholds.

    Contains all threshold values and configuration parameters used
    throughout the audit process with business rules for validation.
    """

    # Overall scoring thresholds
    excellent_score: float = 90.0
    good_score: float = 80.0
    passing_score: float = 70.0
    critical_score: float = 50.0

    # Dimension-specific thresholds
    dimensions: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'architecture': {
            'min_score': 60.0,
            'target_score': 80.0,
            'ddd_compliance_required': 70.0,
            'rest_compliance_required': 75.0,
            'layer_separation_required': 70.0,
            'routes_score_required': 8.0
        },
        'code_quality': {
            'min_score': 65.0,
            'target_score': 85.0,
            'complexity_max': 10,
            'test_coverage_required': 70.0,
            'linting_score_required': 7.0
        },
        'performance': {
            'min_score': 70.0,
            'target_score': 85.0,
            'memory_threshold_mb': 500,
            'cpu_threshold_percent': 80,
            'response_time_max_ms': 1000
        },
        'maintainability': {
            'min_score': 65.0,
            'target_score': 80.0,
            'docstring_coverage_required': 80.0,
            'max_file_size_lines': 1000,
            'dead_code_tolerance_percent': 5.0
        }
    })

    # Critical issue thresholds
    critical_issues: Dict[str, int] = field(default_factory=lambda: {
        'max_critical_issues': 2,
        'max_high_priority_issues': 5,
        'max_medium_priority_issues': 10
    })

    # File and module limits
    file_limits: Dict[str, int] = field(default_factory=lambda: {
        'max_lines_per_file': 1000,
        'max_functions_per_file': 20,
        'max_classes_per_file': 10,
        'max_imports_per_file': 20
    })

    # Analysis timeouts and limits
    analysis_limits: Dict[str, Any] = field(default_factory=lambda: {
        'max_analysis_time_seconds': 300,
        'max_files_to_analyze': 100,
        'max_memory_usage_mb': 1024,
        'timeout_per_file_seconds': 30
    })

    def __post_init__(self):
        """Apply business rules and validations."""
        self._validate_score_ranges()
        self._validate_dimension_thresholds()

    def _validate_score_ranges(self) -> None:
        """Validate that score thresholds are in logical order."""
        scores = [self.critical_score, self.passing_score, self.good_score, self.excellent_score]
        if not all(scores[i] <= scores[i+1] for i in range(len(scores)-1)):
            raise ValueError("Score thresholds must be in ascending order")

        for score in scores:
            if not (0.0 <= score <= 100.0):
                raise ValueError("All score thresholds must be between 0.0 and 100.0")

    def _validate_dimension_thresholds(self) -> None:
        """Validate dimension-specific thresholds."""
        for dimension, config in self.dimensions.items():
            min_score = config.get('min_score', 0)
            target_score = config.get('target_score', 100)

            if min_score > target_score:
                raise ValueError(f"Dimension {dimension}: min_score cannot be greater than target_score")

    def get_dimension_threshold(self, dimension: str, key: str, default: Any = None) -> Any:
        """Get a threshold value for a specific dimension."""
        dimension_config = self.dimensions.get(dimension, {})
        return dimension_config.get(key, default)

    def get_file_limit(self, limit_name: str, default: Any = None) -> Any:
        """Get a file limit value."""
        return self.file_limits.get(limit_name, default)

    def get_analysis_limit(self, limit_name: str, default: Any = None) -> Any:
        """Get an analysis limit value."""
        return self.analysis_limits.get(limit_name, default)

    def is_score_passing(self, score: float, dimension: str = None) -> bool:
        """Check if a score is passing for the given dimension or overall."""
        threshold = self.passing_score
        if dimension:
            threshold = self.get_dimension_threshold(dimension, 'min_score', self.passing_score)
        return score >= threshold

    def is_score_excellent(self, score: float) -> bool:
        """Check if a score is excellent."""
        return score >= self.excellent_score

    def get_score_grade(self, score: float) -> str:
        """Get a letter grade for a score."""
        if score >= self.excellent_score:
            return "A"
        elif score >= self.good_score:
            return "B"
        elif score >= self.passing_score:
            return "C"
        elif score >= self.critical_score:
            return "D"
        else:
            return "F"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "excellent_score": self.excellent_score,
            "good_score": self.good_score,
            "passing_score": self.passing_score,
            "critical_score": self.critical_score,
            "dimensions": self.dimensions,
            "critical_issues": self.critical_issues,
            "file_limits": self.file_limits,
            "analysis_limits": self.analysis_limits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThresholdConfig':
        """Create ThresholdConfig from dictionary."""
        return cls(
            excellent_score=data.get("excellent_score", 90.0),
            good_score=data.get("good_score", 80.0),
            passing_score=data.get("passing_score", 70.0),
            critical_score=data.get("critical_score", 50.0),
            dimensions=data.get("dimensions", {}),
            critical_issues=data.get("critical_issues", {}),
            file_limits=data.get("file_limits", {}),
            analysis_limits=data.get("analysis_limits", {}),
        )
