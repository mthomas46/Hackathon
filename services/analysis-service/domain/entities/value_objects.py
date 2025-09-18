"""Value objects for domain entities."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class AnalysisType(Enum):
    """Analysis type enumeration."""
    SEMANTIC_SIMILARITY = "semantic_similarity"
    SENTIMENT = "sentiment"
    CONTENT_QUALITY = "content_quality"
    TREND_ANALYSIS = "trend_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    MAINTENANCE_FORECAST = "maintenance_forecast"
    QUALITY_DEGRADATION = "quality_degradation"
    CHANGE_IMPACT = "change_impact"
    CROSS_REPOSITORY = "cross_repository"
    AUTOMATED_REMEDIATION = "automated_remediation"


class Confidence(Enum):
    """Confidence level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass(frozen=True)
class AnalysisConfiguration:
    """Value object for analysis configuration."""
    detectors: List[str]
    options: Dict[str, Any]
    priority: str = "normal"
    timeout_seconds: int = 300

    def __post_init__(self):
        if not self.detectors:
            raise ValueError("At least one detector must be specified")

        valid_priorities = ["low", "normal", "high", "critical"]
        if self.priority not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")

        if self.timeout_seconds < 10 or self.timeout_seconds > 3600:
            raise ValueError("Timeout must be between 10 and 3600 seconds")


@dataclass(frozen=True)
class Location:
    """Value object for finding location in document."""
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    start_column: Optional[int] = None
    end_column: Optional[int] = None
    path: Optional[str] = None

    def __post_init__(self):
        if self.start_line is not None and self.start_line < 1:
            raise ValueError("Start line must be positive")
        if self.end_line is not None and self.end_line < 1:
            raise ValueError("End line must be positive")
        if self.start_line and self.end_line and self.start_line > self.end_line:
            raise ValueError("Start line cannot be greater than end line")


@dataclass(frozen=True)
class Suggestion:
    """Value object for finding suggestions."""
    description: str
    action_type: str
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if not self.description or not isinstance(self.description, str):
            raise ValueError("Suggestion description must be a non-empty string")

        if not self.action_type or not isinstance(self.action_type, str):
            raise ValueError("Action type must be a non-empty string")

        valid_actions = ["fix", "review", "ignore", "escalate"]
        if self.action_type not in valid_actions:
            raise ValueError(f"Action type must be one of: {valid_actions}")


@dataclass(frozen=True)
class Metrics:
    """Value object for analysis metrics."""
    execution_time_seconds: float
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    accuracy_score: Optional[float] = None

    def __post_init__(self):
        if self.execution_time_seconds < 0:
            raise ValueError("Execution time cannot be negative")
        if self.memory_usage_mb is not None and self.memory_usage_mb < 0:
            raise ValueError("Memory usage cannot be negative")
        if self.cpu_usage_percent is not None and not 0 <= self.cpu_usage_percent <= 100:
            raise ValueError("CPU usage must be between 0 and 100")
        if self.accuracy_score is not None and not 0.0 <= self.accuracy_score <= 1.0:
            raise ValueError("Accuracy score must be between 0.0 and 1.0")
