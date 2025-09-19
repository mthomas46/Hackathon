"""Logging Infrastructure - Reuse Shared Logging Service.

This module provides logging infrastructure for the project-simulation service
by reusing the shared logging components from services/shared/.
"""

from typing import Optional
import sys
from pathlib import Path

# Import from shared infrastructure
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))
try:
    from core.logging.logger import LoggerService, get_logger, with_correlation_id, generate_correlation_id
except ImportError:
    # Fallback for testing - create simple implementations
    class LoggerService:
        def __init__(self, name="project-simulation", level="INFO", enable_json=True, enable_console=True):
            pass
        def debug(self, message, **kwargs): pass
        def info(self, message, **kwargs): pass
        def warning(self, message, **kwargs): pass
        def error(self, message, **kwargs): pass
        def critical(self, message, **kwargs): pass

    def get_logger(name=None):
        return LoggerService()

    def with_correlation_id(correlation_id=None):
        return lambda func: func

    def generate_correlation_id():
        import uuid
        return str(uuid.uuid4())


class SimulationLogger:
    """Logger adapter for project-simulation service."""

    def __init__(self):
        """Initialize simulation logger."""
        self._logger = LoggerService(
            name="project-simulation",
            level="INFO",
            enable_json=True,
            enable_console=True
        )

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._logger.critical(message, **kwargs)

    def log_simulation_event(self, event_type: str, simulation_id: str, **kwargs):
        """Log simulation-specific event."""
        self._logger.log_business_event(
            event_type=event_type,
            simulation_id=simulation_id,
            **kwargs
        )

    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics."""
        self._logger.log_performance(operation, duration, **kwargs)

    def create_child_logger(self, child_name: str) -> 'SimulationLogger':
        """Create a child logger."""
        child_logger = SimulationLogger()
        child_logger._logger = self._logger.create_child_logger(child_name)
        return child_logger


# Global logger instance
_simulation_logger: Optional[SimulationLogger] = None


def get_simulation_logger() -> SimulationLogger:
    """Get the global simulation logger instance."""
    global _simulation_logger
    if _simulation_logger is None:
        _simulation_logger = SimulationLogger()
    return _simulation_logger


# Re-export shared logging utilities for convenience
__all__ = [
    'SimulationLogger',
    'get_simulation_logger',
    'with_correlation_id',
    'generate_correlation_id'
]
