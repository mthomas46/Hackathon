"""
Safe Git Operations with Multiple Layers of Protection

Provides timeout-protected, fail-safe wrappers around git operations
to prevent job hangs from C-level code or unexpected errors.

Protections:
1. Timeout wrapper with signal-based interruption
2. Fallback mechanisms
3. Operation blacklist
4. Error recovery
5. Graceful degradation
"""

import asyncio
import functools
import logging
import signal
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar
from contextlib import contextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class GitOperationTimeout(Exception):
    """Raised when a git operation exceeds its timeout."""
    pass


class SafeGitOperations:
    """
    Provides timeout-protected git operations with multiple safety layers.
    
    Features:
    - Signal-based timeout (can interrupt C code)
    - Fallback mechanisms
    - Operation blacklist
    - Error counting and circuit breaking
    """
    
    def __init__(
        self,
        default_timeout: int = 30,
        max_consecutive_errors: int = 5,
        blacklist_threshold: int = 3
    ):
        """
        Initialize safe git operations.
        
        Args:
            default_timeout: Default timeout for git operations in seconds
            max_consecutive_errors: Max errors before circuit breaking
            blacklist_threshold: Errors before blacklisting an operation
        """
        self.default_timeout = default_timeout
        self.max_consecutive_errors = max_consecutive_errors
        self.blacklist_threshold = blacklist_threshold
        
        # Error tracking
        self.error_counts: Dict[str, int] = {}
        self.consecutive_errors = 0
        self.blacklisted_commits: set = set()
        
        # Statistics
        self.stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "timeout_operations": 0,
            "blacklisted_operations": 0
        }
    
    @contextmanager
    def timeout_context(self, seconds: int):
        """
        Context manager for timeout using signals.
        
        Can interrupt C-level code unlike asyncio.wait_for().
        
        Args:
            seconds: Timeout in seconds
        
        Raises:
            GitOperationTimeout: If operation exceeds timeout
        """
        def timeout_handler(signum, frame):
            raise GitOperationTimeout(f"Operation timed out after {seconds}s")
        
        # Set signal handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        
        try:
            yield
        finally:
            # Cancel alarm and restore old handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def is_blacklisted(self, commit_sha: str) -> bool:
        """Check if a commit is blacklisted."""
        return commit_sha in self.blacklisted_commits
    
    def blacklist_commit(self, commit_sha: str, reason: str):
        """Add a commit to the blacklist."""
        self.blacklisted_commits.add(commit_sha)
        logger.warning(
            f"🚫 Blacklisted commit {commit_sha[:8]}: {reason}"
        )
        self.stats["blacklisted_operations"] += 1
    
    def record_success(self, operation_name: str):
        """Record successful operation."""
        self.stats["total_operations"] += 1
        self.stats["successful_operations"] += 1
        self.consecutive_errors = 0
        
        # Decrease error count for this operation
        if operation_name in self.error_counts:
            self.error_counts[operation_name] = max(
                0, 
                self.error_counts[operation_name] - 1
            )
    
    def record_failure(
        self, 
        operation_name: str, 
        commit_sha: Optional[str] = None
    ) -> bool:
        """
        Record failed operation.
        
        Args:
            operation_name: Name of the operation that failed
            commit_sha: Optional commit SHA for blacklisting
        
        Returns:
            True if circuit breaker should trip (stop processing)
        """
        self.stats["total_operations"] += 1
        self.stats["failed_operations"] += 1
        self.consecutive_errors += 1
        
        # Track per-operation errors
        self.error_counts[operation_name] = \
            self.error_counts.get(operation_name, 0) + 1
        
        # Blacklist commit if too many errors
        if commit_sha and self.error_counts.get(operation_name, 0) >= self.blacklist_threshold:
            self.blacklist_commit(commit_sha, f"Repeated {operation_name} failures")
        
        # Check circuit breaker
        if self.consecutive_errors >= self.max_consecutive_errors:
            logger.error(
                f"🔴 Circuit breaker tripped: {self.consecutive_errors} "
                f"consecutive errors"
            )
            return True
        
        return False
    
    def record_timeout(self, operation_name: str):
        """Record timeout."""
        self.stats["total_operations"] += 1
        self.stats["timeout_operations"] += 1
    
    async def safe_git_operation(
        self,
        operation: Callable[[], T],
        operation_name: str,
        commit_sha: Optional[str] = None,
        timeout: Optional[int] = None,
        fallback_value: Optional[T] = None
    ) -> T:
        """
        Execute git operation with timeout and error protection.
        
        Args:
            operation: Function to execute
            operation_name: Name for logging/tracking
            commit_sha: Optional commit SHA for blacklisting
            timeout: Timeout in seconds (default: self.default_timeout)
            fallback_value: Value to return on failure
        
        Returns:
            Operation result or fallback_value
        
        Raises:
            GitOperationTimeout: If operation times out
        """
        timeout = timeout or self.default_timeout
        
        # Check blacklist
        if commit_sha and self.is_blacklisted(commit_sha):
            logger.debug(f"Skipping blacklisted commit {commit_sha[:8]}")
            return fallback_value
        
        start_time = time.time()
        
        try:
            # Execute with timeout protection
            result = await asyncio.wait_for(
                asyncio.to_thread(self._execute_with_signal_timeout, operation, timeout),
                timeout=timeout + 1  # Extra second for cleanup
            )
            
            elapsed = time.time() - start_time
            logger.debug(f"✅ {operation_name} completed in {elapsed:.2f}s")
            
            self.record_success(operation_name)
            return result
            
        except (asyncio.TimeoutError, GitOperationTimeout) as e:
            elapsed = time.time() - start_time
            logger.warning(
                f"⏱️  {operation_name} timed out after {elapsed:.1f}s "
                f"(limit: {timeout}s)"
            )
            
            self.record_timeout(operation_name)
            
            # Blacklist if this is a commit operation
            if commit_sha:
                self.blacklist_commit(commit_sha, "Timeout")
            
            if fallback_value is not None:
                return fallback_value
            raise
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"❌ {operation_name} failed after {elapsed:.1f}s: {e}"
            )
            
            # Record failure and check circuit breaker
            should_stop = self.record_failure(operation_name, commit_sha)
            
            if should_stop:
                raise Exception(
                    f"Circuit breaker tripped after {self.consecutive_errors} "
                    f"consecutive errors"
                )
            
            if fallback_value is not None:
                return fallback_value
            raise
    
    def _execute_with_signal_timeout(
        self, 
        operation: Callable[[], T], 
        timeout: int
    ) -> T:
        """
        Execute operation with signal-based timeout.
        
        This can interrupt C-level code unlike asyncio.wait_for().
        
        Args:
            operation: Function to execute
            timeout: Timeout in seconds
        
        Returns:
            Operation result
        
        Raises:
            GitOperationTimeout: If operation times out
        """
        with self.timeout_context(timeout):
            return operation()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get operation statistics."""
        total = self.stats["total_operations"]
        return {
            **self.stats,
            "success_rate": (
                self.stats["successful_operations"] / total * 100 
                if total > 0 else 0
            ),
            "error_counts": dict(self.error_counts),
            "blacklisted_commits": len(self.blacklisted_commits),
            "consecutive_errors": self.consecutive_errors
        }
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "timeout_operations": 0,
            "blacklisted_operations": 0
        }
        self.error_counts.clear()
        self.consecutive_errors = 0


# Global instance
_safe_git_ops = None


def get_safe_git_operations() -> SafeGitOperations:
    """Get or create global SafeGitOperations instance."""
    global _safe_git_ops
    if _safe_git_ops is None:
        _safe_git_ops = SafeGitOperations(
            default_timeout=30,  # 30 seconds default
            max_consecutive_errors=5,
            blacklist_threshold=3
        )
    return _safe_git_ops


def safe_git_operation(
    timeout: int = 30,
    fallback_value: Optional[Any] = None,
    operation_name: Optional[str] = None
):
    """
    Decorator for protecting git operations with timeout and error handling.
    
    Usage:
        @safe_git_operation(timeout=10, fallback_value=[])
        def get_files(commit_sha):
            # ... git operation ...
            return files
    
    Args:
        timeout: Timeout in seconds
        fallback_value: Value to return on failure
        operation_name: Name for logging (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            safe_ops = get_safe_git_operations()
            name = operation_name or func.__name__
            
            # Extract commit_sha if present in args/kwargs
            commit_sha = kwargs.get('commit_sha') or (
                args[1] if len(args) > 1 else None
            )
            
            return await safe_ops.safe_git_operation(
                operation=lambda: func(*args, **kwargs),
                operation_name=name,
                commit_sha=commit_sha,
                timeout=timeout,
                fallback_value=fallback_value
            )
        
        return wrapper
    return decorator

