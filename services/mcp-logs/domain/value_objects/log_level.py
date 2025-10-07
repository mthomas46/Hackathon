"""LogLevel Value Object."""

from enum import Enum


class LogLevel(Enum):
    """Log level enumeration."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    def get_numeric_value(self) -> int:
        """Get numeric value for comparison."""
        values = {
            LogLevel.DEBUG: 10,
            LogLevel.INFO: 20,
            LogLevel.WARNING: 30,
            LogLevel.ERROR: 40,
            LogLevel.CRITICAL: 50,
        }
        return values.get(self, 0)
    
    def is_severe(self) -> bool:
        """Check if log level is severe (ERROR or CRITICAL)."""
        return self in (LogLevel.ERROR, LogLevel.CRITICAL)

