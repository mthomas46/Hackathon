"""Log repository interface for DDD compliance."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.log_entry import LogEntry, LogLevel


class LogRepository(ABC):
    """Abstract repository for log operations."""

    @abstractmethod
    async def save(self, log_entry: LogEntry) -> None:
        """Save a log entry."""
        pass

    @abstractmethod
    async def find_by_id(self, log_id: str) -> Optional[LogEntry]:
        """Find log entry by ID."""
        pass

    @abstractmethod
    async def find_by_service(self, service: str, limit: int = 50) -> List[LogEntry]:
        """Find logs by service."""
        pass

    @abstractmethod
    async def find_by_level(self, level: LogLevel, limit: int = 50) -> List[LogEntry]:
        """Find logs by level."""
        pass

    @abstractmethod
    async def search_logs(self, query: str, limit: int = 50) -> List[LogEntry]:
        """Search logs by query."""
        pass
