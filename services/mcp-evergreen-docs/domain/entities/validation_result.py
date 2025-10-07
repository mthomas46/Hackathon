"""ValidationResult Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4


@dataclass
class ValidationResult:
    """
    Validation result entity.
    
    Represents the result of validating documentation content.
    """
    
    # Identity
    result_id: str = field(default_factory=lambda: str(uuid4()))
    doc_id: str = ""
    
    # Validation status
    valid: bool = False
    score: float = 0.0  # 0.0 - 1.0
    
    # Issues
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Checks performed
    checks_performed: List[str] = field(default_factory=list)
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    
    # Metrics
    content_length: int = 0
    word_count: int = 0
    heading_count: int = 0
    link_count: int = 0
    broken_links: int = 0
    
    # Timing
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_seconds: Optional[float] = None
    
    # Validator info
    validator_version: str = "1.0.0"
    validation_rules: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate result."""
        if not self.result_id:
            self.result_id = str(uuid4())
        if not self.doc_id:
            raise ValueError("Document ID is required")
    
    def add_error(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        rule: Optional[str] = None,
    ) -> None:
        """
        Add validation error.
        
        Args:
            message: Error message
            line: Line number
            column: Column number
            rule: Validation rule that failed
        """
        error = {
            "message": message,
            "severity": "error",
            "line": line,
            "column": column,
            "rule": rule,
        }
        self.errors.append(error)
        self.valid = False
    
    def add_warning(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        rule: Optional[str] = None,
    ) -> None:
        """
        Add validation warning.
        
        Args:
            message: Warning message
            line: Line number
            column: Column number
            rule: Validation rule
        """
        warning = {
            "message": message,
            "severity": "warning",
            "line": line,
            "column": column,
            "rule": rule,
        }
        self.warnings.append(warning)
    
    def add_suggestion(
        self,
        message: str,
        line: Optional[int] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """
        Add improvement suggestion.
        
        Args:
            message: Suggestion message
            line: Line number
            suggestion: Suggested fix
        """
        sug = {
            "message": message,
            "severity": "info",
            "line": line,
            "suggestion": suggestion,
        }
        self.suggestions.append(sug)
    
    def mark_check_passed(self, check: str) -> None:
        """
        Mark validation check as passed.
        
        Args:
            check: Check name
        """
        if check not in self.checks_performed:
            self.checks_performed.append(check)
        if check not in self.checks_passed:
            self.checks_passed.append(check)
    
    def mark_check_failed(self, check: str) -> None:
        """
        Mark validation check as failed.
        
        Args:
            check: Check name
        """
        if check not in self.checks_performed:
            self.checks_performed.append(check)
        if check not in self.checks_failed:
            self.checks_failed.append(check)
        self.valid = False
    
    def calculate_score(self) -> float:
        """
        Calculate validation score.
        
        Returns:
            Score between 0.0 and 1.0
        """
        if not self.checks_performed:
            self.score = 0.0
            return self.score
        
        # Base score on checks passed
        passed_ratio = len(self.checks_passed) / len(self.checks_performed)
        
        # Apply penalties
        error_penalty = min(0.5, len(self.errors) * 0.1)
        warning_penalty = min(0.2, len(self.warnings) * 0.02)
        
        self.score = max(0.0, passed_ratio - error_penalty - warning_penalty)
        return self.score
    
    def is_valid(self) -> bool:
        """
        Check if validation passed.
        
        Returns:
            True if no errors, False otherwise
        """
        return self.valid and len(self.errors) == 0
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get validation summary.
        
        Returns:
            Summary dictionary
        """
        return {
            "valid": self.is_valid(),
            "score": self.score,
            "total_checks": len(self.checks_performed),
            "checks_passed": len(self.checks_passed),
            "checks_failed": len(self.checks_failed),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "suggestion_count": len(self.suggestions),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result_id": self.result_id,
            "doc_id": self.doc_id,
            "valid": self.valid,
            "score": self.score,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "checks_performed": self.checks_performed,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "content_length": self.content_length,
            "word_count": self.word_count,
            "heading_count": self.heading_count,
            "link_count": self.link_count,
            "broken_links": self.broken_links,
            "validated_at": self.validated_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "validator_version": self.validator_version,
            "validation_rules": self.validation_rules,
            "metadata": self.metadata,
            "summary": self.get_summary(),
        }

