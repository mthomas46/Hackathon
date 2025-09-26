"""Log service domain service for DDD compliance."""

from typing import List, Optional
from ..entities.log_entry import LogEntry, LogLevel
from ..repositories.log_repository import LogRepository


class LogService:
    """Domain service for log operations."""

    def __init__(self, repository: LogRepository):
        self._repository = repository

    async def collect_log(self, service: str, level: str, message: str, **kwargs) -> LogEntry:
        """Create and save a new log entry."""
        log_entry = LogEntry(
            id=f"{service}_{int(__import__('time').time() * 1000000)}",
            service=service,
            level=LogLevel[level.upper()],
            message=message,
            **kwargs
        )
        await self._repository.save(log_entry)
        return log_entry

    async def get_logs_by_service(self, service: str, limit: int = 50) -> List[LogEntry]:
        """Get logs for a specific service."""
        return await self._repository.find_by_service(service, limit)

    async def search_logs(self, query: str, limit: int = 50) -> List[LogEntry]:
        """Search logs by query."""
        return await self._repository.search_logs(query, limit)
