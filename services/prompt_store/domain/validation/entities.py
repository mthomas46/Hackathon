"""Validation domain entities for testing and bias detection."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from ...core.entities import BaseEntity


@dataclass
class PromptTestingResult(BaseEntity):
    """Results from automated prompt testing."""
    prompt_id: str
    version: int
    test_suite_id: str
    test_case_id: str
    test_name: str
    passed: bool
    execution_time_ms: float
    output_quality_score: float
    expected_output_similarity: float  # How close to expected result
    error_message: Optional[str] = None
    test_metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = field(default=None)
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())

    def __post_init__(self):
        """Initialize BaseEntity fields."""
        BaseEntity.__init__(self)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "test_suite_id": self.test_suite_id,
            "test_case_id": self.test_case_id,
            "test_name": self.test_name,
            "passed": self.passed,
            "execution_time_ms": self.execution_time_ms,
            "output_quality_score": self.output_quality_score,
            "expected_output_similarity": self.expected_output_similarity,
            "error_message": self.error_message,
            "test_metadata": self.test_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTestingResult':
        """Create entity from dictionary representation."""
        entity = cls(
            prompt_id=data["prompt_id"],
            version=data["version"],
            test_suite_id=data["test_suite_id"],
            test_case_id=data["test_case_id"],
            test_name=data["test_name"],
            passed=data["passed"],
            execution_time_ms=data["execution_time_ms"],
            output_quality_score=data["output_quality_score"],
            expected_output_similarity=data["expected_output_similarity"],
            error_message=data.get("error_message"),
            test_metadata=data.get("test_metadata", {})
        )
        entity.id = data.get("id")
        if "created_at" in data:
            entity.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "updated_at" in data and data["updated_at"]:
            entity.updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        return entity


@dataclass
class BiasDetectionResult(BaseEntity):
    """Results from bias detection analysis."""
    prompt_id: str
    version: int
    bias_type: str  # "gender", "racial", "cultural", etc.
    severity_score: float  # 0.0 to 1.0
    detected_phrases: List[str]
    suggested_alternatives: List[str]
    confidence_score: float
    analysis_method: str  # "pattern_matching", "llm_analysis", "statistical"
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    id: Optional[str] = field(default=None)
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())

    def __post_init__(self):
        """Initialize BaseEntity fields."""
        BaseEntity.__init__(self)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "bias_type": self.bias_type,
            "severity_score": self.severity_score,
            "detected_phrases": self.detected_phrases,
            "suggested_alternatives": self.suggested_alternatives,
            "confidence_score": self.confidence_score,
            "analysis_method": self.analysis_method,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BiasDetectionResult':
        """Create entity from dictionary representation."""
        entity = cls(
            prompt_id=data["prompt_id"],
            version=data["version"],
            bias_type=data["bias_type"],
            severity_score=data["severity_score"],
            detected_phrases=data["detected_phrases"],
            suggested_alternatives=data["suggested_alternatives"],
            confidence_score=data["confidence_score"],
            analysis_method=data["analysis_method"],
            resolved=data.get("resolved", False)
        )
        entity.id = data.get("id")
        if "resolved_at" in data and data["resolved_at"]:
            entity.resolved_at = datetime.fromisoformat(data["resolved_at"].replace('Z', '+00:00'))
        if "created_at" in data:
            entity.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "updated_at" in data and data["updated_at"]:
            entity.updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        return entity


@dataclass
class ValidationReport(BaseEntity):
    """Comprehensive validation report for a prompt."""
    prompt_id: str
    version: int
    linting_results: Dict[str, Any]
    bias_detection_results: List[Dict[str, Any]]
    testing_results: List[Dict[str, Any]]
    overall_score: float  # 0.0 to 1.0
    issues_count: int
    recommendations: List[str]
    id: Optional[str] = field(default=None)
    created_at: datetime = field(default_factory=lambda: datetime.now())
    updated_at: datetime = field(default_factory=lambda: datetime.now())

    def __post_init__(self):
        """Initialize BaseEntity fields."""
        BaseEntity.__init__(self)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "linting_results": self.linting_results,
            "bias_detection_results": self.bias_detection_results,
            "testing_results": self.testing_results,
            "overall_score": self.overall_score,
            "issues_count": self.issues_count,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationReport':
        """Create entity from dictionary representation."""
        entity = cls(
            prompt_id=data["prompt_id"],
            version=data["version"],
            linting_results=data["linting_results"],
            bias_detection_results=data["bias_detection_results"],
            testing_results=data["testing_results"],
            overall_score=data["overall_score"],
            issues_count=data["issues_count"],
            recommendations=data["recommendations"]
        )
        entity.id = data.get("id")
        if "created_at" in data:
            entity.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "updated_at" in data and data["updated_at"]:
            entity.updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        return entity
