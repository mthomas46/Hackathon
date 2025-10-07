"""Stream Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.log_stream import LogStream


class StreamRepository(ABC):
    """Abstract repository for LogStream entities."""
    
    @abstractmethod
    async def add(self, stream: LogStream) -> None:
        """Add log stream."""
        pass
    
    @abstractmethod
    async def get_by_id(self, stream_id: str) -> Optional[LogStream]:
        """Get stream by ID."""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[LogStream]:
        """Get stream by name."""
        pass
    
    @abstractmethod
    async def update(self, stream: LogStream) -> None:
        """Update stream."""
        pass
    
    @abstractmethod
    async def delete(self, stream_id: str) -> None:
        """Delete stream."""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[LogStream]:
        """List all streams."""
        pass
    
    @abstractmethod
    async def list_by_service(self, service: str) -> List[LogStream]:
        """List streams by service."""
        pass
    
    @abstractmethod
    async def list_active(self) -> List[LogStream]:
        """List active streams."""
        pass

