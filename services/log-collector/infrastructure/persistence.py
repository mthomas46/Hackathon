"""Log repository implementation."""

from typing import List, Optional
from ..domain.repositories.log_repository import LogRepository as BaseLogRepository
from ..domain.entities.log_entry import LogEntry


class LogRepository(BaseLogRepository):
    """Concrete implementation of log repository."""

    def __init__(self):
        self._logs = []  # In-memory storage for now

    async def save(self, log_entry: LogEntry) -> None:
        """Save a log entry."""
        self._logs.append(log_entry)

    async def find_by_id(self, log_id: str) -> Optional[LogEntry]:
        """Find log by ID."""
        for log in self._logs:
            if log.id == log_id:
                return log
        return None

    async def find_logs(self, query) -> List[LogEntry]:
        """Find logs based on query."""
        # Simple filtering implementation
        results = self._logs

        if hasattr(query, 'service') and query.service:
            results = [log for log in results if log.service == query.service]

        # Apply limit
        limit = getattr(query, 'limit', 50)
        return results[-limit:] if results else []

    async def find_by_service(self, service: str, limit: int = 50) -> List[LogEntry]:
        """Find logs by service."""
        results = [log for log in self._logs if log.service == service]
        return results[-limit:] if results else []

    async def find_by_level(self, level, limit: int = 50) -> List[LogEntry]:
        """Find logs by level."""
        results = [log for log in self._logs if log.level == level]
        return results[-limit:] if results else []

    async def search_logs(self, query: str, limit: int = 50) -> List[LogEntry]:
        """Search logs by query."""
        results = [log for log in self._logs if query.lower() in log.message.lower()]
        return results[-limit:] if results else []

    async def find_all(self) -> List[LogEntry]:
        """Find all logs."""
        return self._logs.copy()
