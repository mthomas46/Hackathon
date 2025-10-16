"""
Database Update Monitor

Tracks and alerts on failed database updates.
Provides metrics for monitoring dashboards and automatic retries.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class UpdateFailure:
    """Represents a single database update failure."""
    timestamp: datetime
    operation: str
    table: str
    error: str
    job_id: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "table": self.table,
            "error": self.error,
            "job_id": self.job_id,
            "retry_count": self.retry_count
        }


class DatabaseUpdateMonitor:
    """
    Monitors database update operations and tracks failures.
    
    Features:
    - Track failures per hour/minute
    - Alert on high failure rates
    - Provide metrics for dashboards
    - Automatic retry with exponential backoff
    """
    
    def __init__(
        self,
        alert_threshold: int = 10,
        alert_window_minutes: int = 60,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0
    ):
        """
        Initialize the monitor.
        
        Args:
            alert_threshold: Number of failures before alerting
            alert_window_minutes: Time window for counting failures
            max_retries: Maximum retry attempts per operation
            initial_retry_delay: Initial delay for exponential backoff (seconds)
        """
        self.alert_threshold = alert_threshold
        self.alert_window_minutes = alert_window_minutes
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        
        # Thread-safe deque for storing recent failures
        self._failures: deque = deque(maxlen=1000)
        self._lock = asyncio.Lock()
        
        # Alert state
        self._alert_active = False
        self._last_alert_time: Optional[datetime] = None
        self._alert_cooldown_minutes = 15
        
        logger.info(
            f"DatabaseUpdateMonitor initialized: "
            f"threshold={alert_threshold}, window={alert_window_minutes}min"
        )
    
    async def record_failure(
        self,
        operation: str,
        table: str,
        error: Exception,
        job_id: Optional[str] = None
    ) -> None:
        """
        Record a database update failure.
        
        Args:
            operation: Type of operation (update, insert, delete)
            table: Table name
            error: Exception that occurred
            job_id: Optional job ID for context
        """
        async with self._lock:
            failure = UpdateFailure(
                timestamp=datetime.utcnow(),
                operation=operation,
                table=table,
                error=str(error),
                job_id=job_id
            )
            self._failures.append(failure)
            
            logger.error(
                f"Database update failed: {operation} on {table} - {error}",
                extra={
                    "operation": operation,
                    "table": table,
                    "job_id": job_id
                }
            )
            
            # Check if we should alert
            await self._check_alert_threshold()
    
    async def _check_alert_threshold(self) -> None:
        """Check if failure rate exceeds threshold and alert if needed."""
        # Count failures in the alert window
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.alert_window_minutes)
        recent_failures = [
            f for f in self._failures
            if f.timestamp > cutoff_time
        ]
        
        failure_count = len(recent_failures)
        
        if failure_count >= self.alert_threshold:
            # Check if we're in alert cooldown
            if self._last_alert_time:
                cooldown_cutoff = datetime.utcnow() - timedelta(
                    minutes=self._alert_cooldown_minutes
                )
                if self._last_alert_time > cooldown_cutoff:
                    # Still in cooldown, don't alert again
                    return
            
            # Trigger alert
            await self._trigger_alert(failure_count, recent_failures)
    
    async def _trigger_alert(
        self,
        failure_count: int,
        recent_failures: List[UpdateFailure]
    ) -> None:
        """
        Trigger alert for high failure rate.
        
        Args:
            failure_count: Number of failures in window
            recent_failures: List of recent failure objects
        """
        self._alert_active = True
        self._last_alert_time = datetime.utcnow()
        
        # Group failures by table and operation
        by_table = {}
        by_operation = {}
        
        for failure in recent_failures:
            by_table[failure.table] = by_table.get(failure.table, 0) + 1
            by_operation[failure.operation] = by_operation.get(failure.operation, 0) + 1
        
        alert_message = (
            f"🚨 DATABASE UPDATE ALERT 🚨\n"
            f"Failure rate: {failure_count} failures in {self.alert_window_minutes} minutes\n"
            f"Threshold: {self.alert_threshold} failures\n"
            f"By table: {by_table}\n"
            f"By operation: {by_operation}\n"
            f"Action: Investigate database health, check connections, review logs"
        )
        
        logger.critical(alert_message)
        
        # In production, this could also:
        # - Send email/Slack notification
        # - Create PagerDuty incident
        # - Post to monitoring dashboard
        # - Trigger automatic remediation
    
    async def clear_alert(self) -> None:
        """Clear active alert state."""
        async with self._lock:
            if self._alert_active:
                self._alert_active = False
                logger.info("✅ Database update alert cleared")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics for monitoring dashboards.
        
        Returns:
            Dict with failure counts, rates, and statistics
        """
        async with self._lock:
            now = datetime.utcnow()
            
            # Calculate metrics for different time windows
            windows = {
                "last_minute": 1,
                "last_5_minutes": 5,
                "last_15_minutes": 15,
                "last_hour": 60
            }
            
            metrics = {
                "alert_active": self._alert_active,
                "alert_threshold": self.alert_threshold,
                "total_tracked_failures": len(self._failures)
            }
            
            for window_name, minutes in windows.items():
                cutoff = now - timedelta(minutes=minutes)
                failures_in_window = [
                    f for f in self._failures
                    if f.timestamp > cutoff
                ]
                
                metrics[f"{window_name}_count"] = len(failures_in_window)
                metrics[f"{window_name}_rate"] = len(failures_in_window) / minutes
            
            # Get most common failures
            if self._failures:
                # Group by table
                by_table = {}
                by_operation = {}
                by_error_type = {}
                
                for failure in self._failures:
                    by_table[failure.table] = by_table.get(failure.table, 0) + 1
                    by_operation[failure.operation] = by_operation.get(failure.operation, 0) + 1
                    
                    # Extract error type (first word of error message)
                    error_type = failure.error.split(":")[0] if ":" in failure.error else failure.error[:50]
                    by_error_type[error_type] = by_error_type.get(error_type, 0) + 1
                
                # Sort and get top 5
                metrics["top_failing_tables"] = dict(
                    sorted(by_table.items(), key=lambda x: x[1], reverse=True)[:5]
                )
                metrics["top_failing_operations"] = dict(
                    sorted(by_operation.items(), key=lambda x: x[1], reverse=True)[:5]
                )
                metrics["top_error_types"] = dict(
                    sorted(by_error_type.items(), key=lambda x: x[1], reverse=True)[:5]
                )
            else:
                metrics["top_failing_tables"] = {}
                metrics["top_failing_operations"] = {}
                metrics["top_error_types"] = {}
            
            return metrics
    
    async def get_recent_failures(
        self,
        limit: int = 50,
        minutes: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent failures for detailed inspection.
        
        Args:
            limit: Maximum number of failures to return
            minutes: Optional time window in minutes
        
        Returns:
            List of failure dictionaries
        """
        async with self._lock:
            failures = list(self._failures)
            
            # Filter by time window if specified
            if minutes:
                cutoff = datetime.utcnow() - timedelta(minutes=minutes)
                failures = [f for f in failures if f.timestamp > cutoff]
            
            # Sort by timestamp (newest first) and limit
            failures.sort(key=lambda f: f.timestamp, reverse=True)
            failures = failures[:limit]
            
            return [f.to_dict() for f in failures]
    
    async def retry_with_backoff(
        self,
        operation_func,
        operation_name: str,
        table_name: str,
        job_id: Optional[str] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute operation with automatic retry and exponential backoff.
        
        Args:
            operation_func: Async function to execute
            operation_name: Name for logging (update, insert, delete)
            table_name: Table name for tracking
            job_id: Optional job ID for context
            *args, **kwargs: Arguments to pass to operation_func
        
        Returns:
            Result of operation_func
        
        Raises:
            Exception: If all retries exhausted
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                result = await operation_func(*args, **kwargs)
                
                # Success! Log if this was a retry
                if attempt > 0:
                    logger.info(
                        f"✅ Database operation succeeded after {attempt} retries: "
                        f"{operation_name} on {table_name}"
                    )
                
                return result
            
            except Exception as e:
                last_error = e
                
                # Record the failure
                await self.record_failure(
                    operation=operation_name,
                    table=table_name,
                    error=e,
                    job_id=job_id
                )
                
                # If we have retries left, wait and retry
                if attempt < self.max_retries:
                    delay = self.initial_retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Database operation failed (attempt {attempt + 1}/{self.max_retries + 1}): "
                        f"{operation_name} on {table_name} - {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    logger.error(
                        f"❌ Database operation failed after {self.max_retries + 1} attempts: "
                        f"{operation_name} on {table_name} - {e}"
                    )
        
        # All retries exhausted, raise the last error
        raise last_error


# Global singleton instance
_monitor: Optional[DatabaseUpdateMonitor] = None


def get_monitor() -> DatabaseUpdateMonitor:
    """Get the global database update monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = DatabaseUpdateMonitor()
    return _monitor


async def record_update_failure(
    operation: str,
    table: str,
    error: Exception,
    job_id: Optional[str] = None
) -> None:
    """
    Convenience function to record a failure.
    
    Args:
        operation: Type of operation (update, insert, delete)
        table: Table name
        error: Exception that occurred
        job_id: Optional job ID for context
    """
    monitor = get_monitor()
    await monitor.record_failure(operation, table, error, job_id)


async def get_update_metrics() -> Dict[str, Any]:
    """
    Convenience function to get metrics.
    
    Returns:
        Current metrics dictionary
    """
    monitor = get_monitor()
    return await monitor.get_metrics()


async def get_recent_update_failures(
    limit: int = 50,
    minutes: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to get recent failures.
    
    Args:
        limit: Maximum number of failures to return
        minutes: Optional time window in minutes
    
    Returns:
        List of failure dictionaries
    """
    monitor = get_monitor()
    return await monitor.get_recent_failures(limit, minutes)

