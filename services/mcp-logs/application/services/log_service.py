"""Log Management Application Service."""

from typing import Optional

from ...domain.entities.log_entry import LogEntry
from ...domain.repositories.log_repository import LogRepository


class LogService:
    """Application service for log management."""
    
    def __init__(self, log_repo: LogRepository):
        """Initialize log service."""
        self.log_repo = log_repo
    
    async def ingest_log(
        self,
        message: str,
        level: str,
        service: str,
        source: str = "",
        **kwargs,
    ) -> LogEntry:
        """Ingest log entry."""
        log = LogEntry(
            message=message,
            level=level,
            service=service,
            source=source,
            **kwargs,
        )
        
        await self.log_repo.add(log)
        return log
    
    async def get_log(self, entry_id: str) -> Optional[LogEntry]:
        """Get log by ID."""
        return await self.log_repo.get_by_id(entry_id)
    
    async def get_service_logs(self, service: str, limit: int = 100) -> list:
        """Get logs for service."""
        logs = await self.log_repo.get_by_service(service, limit)
        return [log.to_dict() for log in logs]
    
    async def get_error_logs(self, limit: int = 100) -> list:
        """Get error logs."""
        logs = await self.log_repo.get_by_level("ERROR", limit)
        return [log.to_dict() for log in logs]

