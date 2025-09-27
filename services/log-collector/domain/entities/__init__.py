"""Domain entities for log collector service."""

from .log_entry import LogEntry
from .log_statistics import LogStatistics

__all__ = [
    "LogEntry",
    "LogStatistics",
]
