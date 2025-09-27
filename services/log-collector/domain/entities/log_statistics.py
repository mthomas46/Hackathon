"""Log statistics domain entity."""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class LogStatistics:
    """Domain entity representing log statistics.

    Aggregates log data for analysis and monitoring.
    """

    service_name: str = ""
    time_window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    time_window_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=1))

    # Count statistics
    total_logs: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    debug_count: int = 0

    # Performance metrics
    average_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = 0.0

    # Error analysis
    top_errors: Dict[str, int] = field(default_factory=dict)
    error_rate: float = 0.0

    # Resource usage
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # Custom metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate statistics after initialization."""
        if self.time_window_start >= self.time_window_end:
            raise ValueError("Time window start must be before end")

    @property
    def duration_seconds(self) -> float:
        """Get the duration of this statistics window in seconds."""
        return (self.time_window_end - self.time_window_start).total_seconds()

    @property
    def logs_per_second(self) -> float:
        """Calculate logs per second rate."""
        if self.duration_seconds == 0:
            return 0.0
        return self.total_logs / self.duration_seconds

    @property
    def error_percentage(self) -> float:
        """Calculate error percentage."""
        if self.total_logs == 0:
            return 0.0
        return (self.error_count / self.total_logs) * 100.0

    def add_log_entry(self, level: str, response_time: float = 0.0) -> None:
        """Add a log entry to the statistics."""
        self.total_logs += 1

        # Update level counts
        if level == "ERROR":
            self.error_count += 1
        elif level == "WARNING":
            self.warning_count += 1
        elif level == "INFO":
            self.info_count += 1
        elif level == "DEBUG":
            self.debug_count += 1

        # Update response time metrics
        if response_time > 0:
            self.average_response_time = (
                (self.average_response_time * (self.total_logs - 1)) + response_time
            ) / self.total_logs
            self.max_response_time = max(self.max_response_time, response_time)
            if self.min_response_time == 0 or response_time < self.min_response_time:
                self.min_response_time = response_time

        # Update error rate
        self.error_rate = self.error_percentage

    def record_error(self, error_message: str) -> None:
        """Record an error occurrence."""
        if error_message in self.top_errors:
            self.top_errors[error_message] += 1
        else:
            self.top_errors[error_message] = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "service_name": self.service_name,
            "time_window_start": self.time_window_start.isoformat(),
            "time_window_end": self.time_window_end.isoformat(),
            "total_logs": self.total_logs,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "debug_count": self.debug_count,
            "average_response_time": self.average_response_time,
            "max_response_time": self.max_response_time,
            "min_response_time": self.min_response_time,
            "top_errors": self.top_errors,
            "error_rate": self.error_rate,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "custom_metrics": self.custom_metrics,
        }
