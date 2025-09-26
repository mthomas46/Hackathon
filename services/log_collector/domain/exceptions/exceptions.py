"""Domain exceptions for log collector."""

class LogCollectorException(Exception):
    """Base exception for log collector domain errors."""
    pass


class LogNotFoundException(LogCollectorException):
    """Exception when log entry is not found."""
    pass
