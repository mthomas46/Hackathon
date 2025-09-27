"""Analysis result domain entity."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class AnalysisResult:
    """Domain entity representing the result of code analysis.

    Encapsulates the complete analysis output including metadata,
    findings, security issues, and performance metrics.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str = ""
    title: str = ""
    content: str = ""
    source_refs: List[Dict[str, Any]] = field(default_factory=list)
    repo: Optional[str] = None
    path: Optional[str] = None
    correlation_id: Optional[str] = None
    analysis_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Analysis results
    endpoints_found: List[Dict[str, Any]] = field(default_factory=list)
    security_issues: List[Dict[str, Any]] = field(default_factory=list)
    style_violations: List[Dict[str, Any]] = field(default_factory=list)
    complexity_metrics: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0

    # Processing metadata
    processing_time_seconds: float = 0.0
    lines_analyzed: int = 0
    files_processed: int = 0
    analysis_version: str = "1.0"

    def __post_init__(self):
        """Validate analysis result after initialization."""
        if not self.source_type.strip():
            raise ValueError("Source type cannot be empty")
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if self.quality_score < 0.0 or self.quality_score > 100.0:
            raise ValueError("Quality score must be between 0.0 and 100.0")

        # Ensure valid source types
        valid_sources = ["github", "gitlab", "bitbucket", "local", "filesystem"]
        if self.source_type.lower() not in valid_sources:
            raise ValueError(f"Invalid source type: {self.source_type}")

    @property
    def has_security_issues(self) -> bool:
        """Check if analysis found security issues."""
        return len(self.security_issues) > 0

    @property
    def has_style_violations(self) -> bool:
        """Check if analysis found style violations."""
        return len(self.style_violations) > 0

    @property
    def critical_issues_count(self) -> int:
        """Count critical security issues."""
        return len([issue for issue in self.security_issues
                   if issue.get("severity", "").upper() == "CRITICAL"])

    @property
    def high_issues_count(self) -> int:
        """Count high-severity security issues."""
        return len([issue for issue in self.security_issues
                   if issue.get("severity", "").upper() == "HIGH"])

    @property
    def analysis_age_seconds(self) -> float:
        """Get age of this analysis in seconds."""
        return (datetime.now(timezone.utc) - self.analysis_timestamp).total_seconds()

    @property
    def is_recent(self) -> bool:
        """Check if analysis is recent (within last hour)."""
        return self.analysis_age_seconds < 3600

    def add_security_issue(self, issue: Dict[str, Any]) -> None:
        """Add a security issue to the analysis."""
        if not isinstance(issue, dict):
            raise ValueError("Security issue must be a dictionary")

        required_fields = ["type", "severity", "description"]
        for field in required_fields:
            if field not in issue:
                raise ValueError(f"Security issue missing required field: {field}")

        self.security_issues.append(issue)

    def add_style_violation(self, violation: Dict[str, Any]) -> None:
        """Add a style violation to the analysis."""
        if not isinstance(violation, dict):
            raise ValueError("Style violation must be a dictionary")

        self.style_violations.append(violation)

    def add_endpoint(self, endpoint: Dict[str, Any]) -> None:
        """Add a discovered endpoint to the analysis."""
        if not isinstance(endpoint, dict):
            raise ValueError("Endpoint must be a dictionary")

        self.endpoints_found.append(endpoint)

    def update_complexity_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update complexity metrics."""
        self.complexity_metrics.update(metrics)

    def set_processing_metadata(self, processing_time: float, lines: int, files: int) -> None:
        """Set processing metadata."""
        self.processing_time_seconds = processing_time
        self.lines_analyzed = lines
        self.files_processed = files

    def calculate_quality_score(self) -> float:
        """Calculate overall quality score based on analysis results."""
        # Base score starts at 100
        score = 100.0

        # Deduct points for security issues
        critical_penalty = self.critical_issues_count * 20  # 20 points per critical issue
        high_penalty = self.high_issues_count * 10          # 10 points per high issue
        medium_penalty = len([i for i in self.security_issues
                             if i.get("severity", "").upper() == "MEDIUM"]) * 5

        # Deduct points for style violations
        style_penalty = len(self.style_violations) * 2      # 2 points per violation

        # Deduct points for complexity issues
        complexity_penalty = 0
        if self.complexity_metrics.get("cyclomatic_complexity", 0) > 15:
            complexity_penalty += 10
        if self.complexity_metrics.get("cognitive_complexity", 0) > 20:
            complexity_penalty += 10

        total_penalty = critical_penalty + high_penalty + medium_penalty + style_penalty + complexity_penalty

        # Ensure score doesn't go below 0
        self.quality_score = max(0.0, score - total_penalty)
        return self.quality_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_type": self.source_type,
            "title": self.title,
            "content": self.content,
            "source_refs": self.source_refs,
            "repo": self.repo,
            "path": self.path,
            "correlation_id": self.correlation_id,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "endpoints_found": self.endpoints_found,
            "security_issues": self.security_issues,
            "style_violations": self.style_violations,
            "complexity_metrics": self.complexity_metrics,
            "quality_score": self.quality_score,
            "processing_time_seconds": self.processing_time_seconds,
            "lines_analyzed": self.lines_analyzed,
            "files_processed": self.files_processed,
            "analysis_version": self.analysis_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create AnalysisResult from dictionary."""
        # Handle datetime conversion
        if isinstance(data.get("analysis_timestamp"), str):
            data["analysis_timestamp"] = datetime.fromisoformat(data["analysis_timestamp"].replace('Z', '+00:00'))

        return cls(**data)
