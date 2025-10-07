"""Log Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..entities.log_entry import LogEntry
from ..value_objects.search_query import SearchQuery


class LogRepository(ABC):
    """Abstract repository for LogEntry entities."""
    
    @abstractmethod
    async def add(self, log: LogEntry) -> None:
        """Add log entry."""
        pass
    
    @abstractmethod
    async def get_by_id(self, entry_id: str) -> Optional[LogEntry]:
        """Get log by ID."""
        pass
    
    @abstractmethod
    async def search(self, query: SearchQuery) -> List[LogEntry]:
        """Search logs."""
        pass
    
    @abstractmethod
    async def get_by_service(
        self, service: str, limit: int = 100
    ) -> List[LogEntry]:
        """Get logs by service."""
        pass
    
    @abstractmethod
    async def get_by_level(
        self, level: str, limit: int = 100
    ) -> List[LogEntry]:
        """Get logs by level."""
        pass
    
    @abstractmethod
    async def get_by_time_range(
        self, start: datetime, end: datetime
    ) -> List[LogEntry]:
        """Get logs by time range."""
        pass
    
    @abstractmethod
    async def count_by_service(self, service: str) -> int:
        """Count logs by service."""
        pass
    
    @abstractmethod
    async def delete_old_logs(self, before: datetime) -> int:
        """Delete logs older than timestamp."""
        pass

