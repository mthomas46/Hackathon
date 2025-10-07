"""Search Application Service."""

from typing import List

from ...domain.entities.log_entry import LogEntry
from ...domain.repositories.log_repository import LogRepository
from ...domain.value_objects.search_query import SearchQuery


class SearchService:
    """Application service for log search."""
    
    def __init__(self, log_repo: LogRepository):
        """Initialize search service."""
        self.log_repo = log_repo
    
    async def search_logs(
        self,
        query_string: str,
        service: str = None,
        level: str = None,
        limit: int = 100,
        **kwargs,
    ) -> List[dict]:
        """Search logs."""
        query = SearchQuery(
            query_string=query_string,
            service=service,
            level=level,
            limit=limit,
            **kwargs,
        )
        
        logs = await self.log_repo.search(query)
        return [log.to_dict() for log in logs]
    
    async def search_errors(
        self,
        query_string: str = "*",
        service: str = None,
        limit: int = 100,
    ) -> List[dict]:
        """Search error logs."""
        query = SearchQuery(
            query_string=query_string,
            service=service,
            level="ERROR",
            limit=limit,
        )
        
        logs = await self.log_repo.search(query)
        return [log.to_dict() for log in logs]

