"""
Partial Success Utilities (Phase 10 - Day 3 - Task 3.1)

Provides utilities for handling partial success scenarios where some operations
succeed and others fail, ensuring the overall job doesn't fail completely.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FailureStage(Enum):
    """Stage at which a failure occurred."""
    FILE_READ = "file_read"
    PARSING = "parsing"
    NORMALIZATION = "normalization"
    EMBEDDING = "embedding"
    STORAGE = "storage"
    UNKNOWN = "unknown"


@dataclass
class FailureDetail:
    """Detailed information about a failure."""
    file_path: str
    stage: FailureStage
    error_message: str
    error_type: str
    timestamp: Optional[str] = None
    retry_attempted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "stage": self.stage.value,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "timestamp": self.timestamp,
            "retry_attempted": self.retry_attempted
        }


@dataclass
class PartialSuccessResult:
    """
    Result of an operation with partial success support.
    
    Tracks both successful and failed operations, allowing the overall
    job to succeed even if some individual operations fail.
    """
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    failures: List[FailureDetail] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.total == 0:
            return 1.0
        return self.succeeded / self.total
    
    @property
    def is_complete_success(self) -> bool:
        """Check if all operations succeeded."""
        return self.failed == 0 and self.succeeded > 0
    
    @property
    def is_partial_success(self) -> bool:
        """Check if some operations succeeded but some failed."""
        return self.succeeded > 0 and self.failed > 0
    
    @property
    def is_complete_failure(self) -> bool:
        """Check if all operations failed."""
        return self.succeeded == 0 and self.failed > 0
    
    @property
    def overall_success(self) -> bool:
        """
        Determine if result should be considered a success.
        
        A result is successful if:
        - At least one operation succeeded, AND
        - Success rate is above threshold (default 50%)
        """
        if self.total == 0:
            return False
        
        threshold = self.metadata.get("success_threshold", 0.5)
        return self.succeeded > 0 and self.success_rate >= threshold
    
    def add_success(self):
        """Record a successful operation."""
        self.total += 1
        self.succeeded += 1
    
    def add_failure(
        self,
        file_path: str,
        stage: FailureStage,
        error: Exception,
        retry_attempted: bool = False
    ):
        """Record a failed operation."""
        self.total += 1
        self.failed += 1
        
        failure = FailureDetail(
            file_path=file_path,
            stage=stage,
            error_message=str(error),
            error_type=type(error).__name__,
            retry_attempted=retry_attempted
        )
        self.failures.append(failure)
    
    def add_skip(self):
        """Record a skipped operation."""
        self.total += 1
        self.skipped += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": self.success_rate,
            "is_complete_success": self.is_complete_success,
            "is_partial_success": self.is_partial_success,
            "is_complete_failure": self.is_complete_failure,
            "overall_success": self.overall_success,
            "failures": [f.to_dict() for f in self.failures],
            "metadata": self.metadata
        }
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        if self.is_complete_success:
            return f"✅ Complete success: {self.succeeded}/{self.total} operations"
        elif self.is_partial_success:
            return f"⚠️  Partial success: {self.succeeded}/{self.total} operations ({self.success_rate:.1%})"
        elif self.is_complete_failure:
            return f"❌ Complete failure: 0/{self.total} operations succeeded"
        elif self.total == 0:
            return "📭 No operations performed"
        else:
            return f"📊 {self.succeeded}/{self.total} operations"
    
    def log_summary(self, logger_instance: logging.Logger = logger):
        """Log a summary of the result."""
        summary = self.get_summary()
        
        if self.is_complete_success:
            logger_instance.info(summary)
        elif self.is_partial_success:
            logger_instance.warning(summary)
            logger_instance.warning(f"   Failed operations: {self.failed}")
            # Log first few failures
            for failure in self.failures[:3]:
                logger_instance.warning(
                    f"   - {failure.file_path}: {failure.stage.value} - {failure.error_type}"
                )
            if len(self.failures) > 3:
                logger_instance.warning(f"   ... and {len(self.failures) - 3} more")
        elif self.is_complete_failure:
            logger_instance.error(summary)
        else:
            logger_instance.info(summary)


def merge_partial_results(results: List[PartialSuccessResult]) -> PartialSuccessResult:
    """
    Merge multiple partial success results into one.
    
    Useful for aggregating results from parallel operations.
    
    Args:
        results: List of partial success results
    
    Returns:
        Merged result
    """
    merged = PartialSuccessResult()
    
    for result in results:
        merged.total += result.total
        merged.succeeded += result.succeeded
        merged.failed += result.failed
        merged.skipped += result.skipped
        merged.failures.extend(result.failures)
        
        # Merge metadata (later results override earlier)
        merged.metadata.update(result.metadata)
    
    return merged


def should_continue_on_failure(
    result: PartialSuccessResult,
    max_failure_rate: float = 0.5,
    max_consecutive_failures: int = 10
) -> bool:
    """
    Determine if processing should continue given current failures.
    
    Args:
        result: Current partial success result
        max_failure_rate: Maximum acceptable failure rate (0.0 to 1.0)
        max_consecutive_failures: Maximum consecutive failures before stopping
    
    Returns:
        True if processing should continue, False if should stop
    """
    # If no operations yet, continue
    if result.total == 0:
        return True
    
    # Check failure rate
    failure_rate = result.failed / result.total
    if failure_rate >= max_failure_rate:
        logger.warning(
            f"⚠️  High failure rate: {failure_rate:.1%} "
            f"(threshold: {max_failure_rate:.1%})"
        )
        return False
    
    # Check consecutive failures (would need to track separately)
    # For now, just check if recent failures are all failures
    recent_failures = result.failures[-max_consecutive_failures:]
    if len(recent_failures) >= max_consecutive_failures:
        logger.error(
            f"❌ Too many consecutive failures: {len(recent_failures)} "
            f"(threshold: {max_consecutive_failures})"
        )
        return False
    
    return True


__all__ = [
    "FailureStage",
    "FailureDetail",
    "PartialSuccessResult",
    "merge_partial_results",
    "should_continue_on_failure",
]

