"""
Retry Handler for Documentation Generation

Handles retry logic for failed sections with:
- Exponential backoff
- Maximum retry attempts
- Circuit breaker pattern
- Graceful degradation
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class RetryHandler:
    """
    Handles retry logic for failed documentation generation sections.
    
    Features:
    - Exponential backoff
    - Maximum retry attempts
    - Circuit breaker for RAG service
    - Graceful degradation
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        circuit_failure_threshold: int = 5,
        circuit_recovery_timeout: int = 60
    ):
        """
        Initialize retry handler.
        
        Args:
            max_retries: Maximum retry attempts per section
            initial_delay: Initial retry delay in seconds
            max_delay: Maximum retry delay in seconds
            backoff_factor: Exponential backoff multiplier
            circuit_failure_threshold: Failures before opening circuit
            circuit_recovery_timeout: Seconds before testing recovery
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        
        # Circuit breaker state
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.circuit_failure_threshold = circuit_failure_threshold
        self.circuit_recovery_timeout = circuit_recovery_timeout
        self.circuit_opened_at: Optional[datetime] = None
        
        # Retry statistics
        self.retry_stats = {
            "total_attempts": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "circuit_openings": 0
        }
        
        logger.info(
            f"RetryHandler initialized: max_retries={max_retries}, "
            f"circuit_threshold={circuit_failure_threshold}"
        )
    
    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[Any]],
        operation_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Async function to execute
            operation_name: Name for logging
            context: Additional context for logging
        
        Returns:
            Result dict with success status and data/error
        """
        context = context or {}
        attempt = 0
        last_error = None
        
        while attempt <= self.max_retries:
            # Check circuit breaker
            if not self._should_attempt():
                logger.warning(
                    f"Circuit breaker OPEN for {operation_name}, "
                    f"skipping attempt {attempt}"
                )
                return {
                    "success": False,
                    "error": "Circuit breaker open",
                    "circuit_state": self.circuit_state.value,
                    "attempts": attempt
                }
            
            try:
                self.retry_stats["total_attempts"] += 1
                
                logger.info(
                    f"Executing {operation_name} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                
                # Execute operation
                result = await operation()
                
                # Success! Reset circuit breaker
                self._record_success()
                
                if attempt > 0:
                    self.retry_stats["successful_retries"] += 1
                    logger.info(
                        f"✅ {operation_name} succeeded on retry "
                        f"(attempt {attempt + 1})"
                    )
                
                return {
                    "success": True,
                    "data": result,
                    "attempts": attempt + 1
                }
            
            except Exception as e:
                last_error = e
                attempt += 1
                
                # Record failure
                self._record_failure()
                
                logger.warning(
                    f"❌ {operation_name} failed "
                    f"(attempt {attempt}/{self.max_retries + 1}): {e}"
                )
                
                # If we have retries left, wait and try again
                if attempt <= self.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    # Out of retries
                    self.retry_stats["failed_retries"] += 1
                    logger.error(
                        f"❌ {operation_name} failed after "
                        f"{self.max_retries + 1} attempts"
                    )
        
        # All retries exhausted
        return {
            "success": False,
            "error": str(last_error),
            "error_type": type(last_error).__name__,
            "attempts": attempt,
            "circuit_state": self.circuit_state.value
        }
    
    def _should_attempt(self) -> bool:
        """Check if we should attempt operation based on circuit state."""
        if self.circuit_state == CircuitState.CLOSED:
            return True
        
        if self.circuit_state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.circuit_opened_at:
                elapsed = (datetime.utcnow() - self.circuit_opened_at).total_seconds()
                if elapsed >= self.circuit_recovery_timeout:
                    # Try half-open state
                    self.circuit_state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker: OPEN → HALF_OPEN (testing recovery)")
                    return True
            return False
        
        # HALF_OPEN: Allow one attempt to test
        return True
    
    def _record_success(self):
        """Record successful operation."""
        if self.circuit_state == CircuitState.HALF_OPEN:
            # Recovery successful, close circuit
            self.circuit_state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info("Circuit breaker: HALF_OPEN → CLOSED (recovered)")
        elif self.circuit_state == CircuitState.CLOSED:
            # Reduce failure count on success
            self.failure_count = max(0, self.failure_count - 1)
    
    def _record_failure(self):
        """Record failed operation and update circuit breaker."""
        self.failure_count += 1
        
        if self.circuit_state == CircuitState.HALF_OPEN:
            # Failed during testing, reopen circuit
            self.circuit_state = CircuitState.OPEN
            self.circuit_opened_at = datetime.utcnow()
            self.retry_stats["circuit_openings"] += 1
            logger.warning(
                "Circuit breaker: HALF_OPEN → OPEN (recovery failed)"
            )
        elif self.circuit_state == CircuitState.CLOSED:
            # Check if we should open circuit
            if self.failure_count >= self.circuit_failure_threshold:
                self.circuit_state = CircuitState.OPEN
                self.circuit_opened_at = datetime.utcnow()
                self.retry_stats["circuit_openings"] += 1
                logger.error(
                    f"Circuit breaker: CLOSED → OPEN "
                    f"({self.failure_count} consecutive failures)"
                )
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        return min(delay, self.max_delay)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry statistics."""
        return {
            **self.retry_stats,
            "circuit_state": self.circuit_state.value,
            "failure_count": self.failure_count,
            "success_rate": (
                self.retry_stats["successful_retries"] /
                max(self.retry_stats["total_attempts"], 1)
            )
        }
    
    def reset_circuit(self):
        """Manually reset circuit breaker (admin function)."""
        logger.info(f"Circuit breaker manually reset from {self.circuit_state.value}")
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.circuit_opened_at = None


class GracefulDegradationHandler:
    """
    Handles graceful degradation when sections fail to generate.
    
    Provides fallback content for failed sections to ensure
    documentation is still useful even with partial failures.
    """
    
    def __init__(self):
        """Initialize graceful degradation handler."""
        logger.info("GracefulDegradationHandler initialized")
    
    def generate_fallback_content(
        self,
        section_name: str,
        error: str,
        template_def: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate fallback content for a failed section.
        
        Args:
            section_name: Section that failed
            error: Error message
            template_def: Template definition for this section
        
        Returns:
            Fallback content in markdown
        """
        lines = [
            f"## {section_name}",
            "",
            "⚠️ **Generation Error**",
            "",
            f"This section could not be automatically generated due to a technical issue:",
            f"> {error}",
            "",
            "**What you can do:**",
            "- Review the source code manually",
            "- Retry documentation generation",
            "- Contact support if the issue persists",
            ""
        ]
        
        # Add template guidance if available
        if template_def:
            description = template_def.get("description", "")
            if description:
                lines.extend([
                    "**Expected Content:**",
                    f"{description}",
                    ""
                ])
            
            prompt = template_def.get("prompt_template", "")
            if prompt:
                lines.extend([
                    "<details>",
                    "<summary>What should be documented here?</summary>",
                    "",
                    f"{prompt[:500]}...",
                    "",
                    "</details>",
                    ""
                ])
        
        return "\n".join(lines)
    
    def should_degrade(
        self,
        failed_sections: List[str],
        total_sections: int,
        threshold: float = 0.5
    ) -> bool:
        """
        Determine if we should accept partial documentation.
        
        Args:
            failed_sections: List of failed section names
            total_sections: Total number of sections
            threshold: Minimum success rate (default 50%)
        
        Returns:
            True if partial documentation is acceptable
        """
        success_rate = 1 - (len(failed_sections) / total_sections)
        
        should_accept = success_rate >= threshold
        
        logger.info(
            f"Degradation check: {len(failed_sections)}/{total_sections} failed, "
            f"success_rate={success_rate:.1%}, "
            f"threshold={threshold:.1%}, "
            f"accept={'YES' if should_accept else 'NO'}"
        )
        
        return should_accept


# Singleton instances
_retry_handler: Optional[RetryHandler] = None
_degradation_handler: Optional[GracefulDegradationHandler] = None


def get_retry_handler() -> RetryHandler:
    """Get or create singleton retry handler."""
    global _retry_handler
    if _retry_handler is None:
        _retry_handler = RetryHandler()
    return _retry_handler


def get_degradation_handler() -> GracefulDegradationHandler:
    """Get or create singleton degradation handler."""
    global _degradation_handler
    if _degradation_handler is None:
        _degradation_handler = GracefulDegradationHandler()
    return _degradation_handler

