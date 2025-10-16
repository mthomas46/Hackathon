"""
Git Error Handler

Handles git repository errors with proper logging and recovery strategies.
"""

import logging
from typing import Optional, Dict, Any
from git.exc import GitError, BadName, BadObject
import traceback

logger = logging.getLogger(__name__)


class GitCorruptionError(Exception):
    """Raised when git repository corruption is detected."""
    pass


class GitErrorHandler:
    """
    Centralized error handling for git operations.
    
    Provides:
    - Error classification
    - Recovery strategies
    - Detailed logging
    - Metrics tracking
    """
    
    def __init__(self):
        self.error_counts = {
            "corruption": 0,
            "bad_object": 0,
            "bad_name": 0,
            "timeout": 0,
            "unknown": 0
        }
    
    def classify_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify and log a git error.
        
        Args:
            error: The exception that occurred
            context: Additional context (commit_sha, file_path, etc.)
            
        Returns:
            Dict with error classification and suggested action
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Classify error
        if "index out of range" in error_msg.lower():
            category = "corruption"
            self.error_counts["corruption"] += 1
            recoverable = False
            action = "skip_commit"
            severity = "ERROR"
            
            logger.error(
                f"🔴 Git corruption detected in commit {context.get('commit_sha', 'unknown')[:8]}: {error_msg}",
                extra={
                    "error_type": "git_corruption",
                    "commit_sha": context.get('commit_sha'),
                    "file_path": context.get('file_path'),
                    "operation": context.get('operation'),
                    "traceback": traceback.format_exc()
                }
            )
            
        elif isinstance(error, BadObject) or "bad object" in error_msg.lower():
            category = "bad_object"
            self.error_counts["bad_object"] += 1
            recoverable = False
            action = "skip_commit"
            severity = "ERROR"
            
            logger.error(
                f"🔴 Bad git object in commit {context.get('commit_sha', 'unknown')[:8]}: {error_msg}"
            )
            
        elif isinstance(error, BadName) or "bad name" in error_msg.lower():
            category = "bad_name"
            self.error_counts["bad_name"] += 1
            recoverable = True
            action = "retry"
            severity = "WARNING"
            
            logger.warning(
                f"⚠️  Bad git name in commit {context.get('commit_sha', 'unknown')[:8]}: {error_msg}"
            )
            
        elif "timeout" in error_msg.lower():
            category = "timeout"
            self.error_counts["timeout"] += 1
            recoverable = True
            action = "retry"
            severity = "WARNING"
            
            logger.warning(
                f"⚠️  Git operation timeout in commit {context.get('commit_sha', 'unknown')[:8]}"
            )
            
        else:
            category = "unknown"
            self.error_counts["unknown"] += 1
            recoverable = False
            action = "skip_commit"
            severity = "ERROR"
            
            logger.error(
                f"🔴 Unknown git error in commit {context.get('commit_sha', 'unknown')[:8]}: {error_type} - {error_msg}",
                extra={
                    "error_type": error_type,
                    "commit_sha": context.get('commit_sha'),
                    "traceback": traceback.format_exc()
                }
            )
        
        return {
            "category": category,
            "error_type": error_type,
            "error_message": error_msg,
            "recoverable": recoverable,
            "suggested_action": action,
            "severity": severity,
            "context": context
        }
    
    def should_skip_commit(self, error_classification: Dict[str, Any]) -> bool:
        """
        Determine if a commit should be skipped based on error classification.
        
        Args:
            error_classification: Result from classify_error()
            
        Returns:
            True if commit should be skipped, False otherwise
        """
        return error_classification["suggested_action"] == "skip_commit"
    
    def should_retry(self, error_classification: Dict[str, Any]) -> bool:
        """
        Determine if operation should be retried.
        
        Args:
            error_classification: Result from classify_error()
            
        Returns:
            True if operation should be retried, False otherwise
        """
        return error_classification["suggested_action"] == "retry"
    
    def get_error_summary(self) -> Dict[str, int]:
        """
        Get summary of all errors encountered.
        
        Returns:
            Dict with error counts by category
        """
        return self.error_counts.copy()
    
    def log_error_summary(self):
        """Log summary of all errors encountered."""
        total_errors = sum(self.error_counts.values())
        
        if total_errors == 0:
            logger.info("✅ No git errors encountered")
            return
        
        logger.warning(
            f"⚠️  Git Error Summary: {total_errors} total errors",
            extra=self.error_counts
        )
        
        for category, count in self.error_counts.items():
            if count > 0:
                logger.warning(f"   • {category}: {count}")


# Singleton instance
_git_error_handler: Optional[GitErrorHandler] = None


def get_git_error_handler() -> GitErrorHandler:
    """Get singleton git error handler instance."""
    global _git_error_handler
    if _git_error_handler is None:
        _git_error_handler = GitErrorHandler()
    return _git_error_handler

