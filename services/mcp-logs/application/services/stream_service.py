"""Stream Management Application Service."""

from typing import List, Optional

from ...domain.entities.log_stream import LogStream
from ...domain.repositories.stream_repository import StreamRepository


class StreamService:
    """Application service for stream management."""
    
    def __init__(self, stream_repo: StreamRepository):
        """Initialize stream service."""
        self.stream_repo = stream_repo
    
    async def create_stream(
        self,
        name: str,
        service: str,
        environment: str = "production",
        **kwargs,
    ) -> LogStream:
        """Create log stream."""
        stream = LogStream(
            name=name,
            service=service,
            environment=environment,
            **kwargs,
        )
        
        await self.stream_repo.add(stream)
        return stream
    
    async def get_stream(self, stream_id: str) -> Optional[LogStream]:
        """Get stream by ID."""
        return await self.stream_repo.get_by_id(stream_id)
    
    async def start_stream(self, stream_id: str) -> LogStream:
        """Start stream."""
        stream = await self.stream_repo.get_by_id(stream_id)
        if not stream:
            raise ValueError(f"Stream not found: {stream_id}")
        
        stream.start()
        await self.stream_repo.update(stream)
        return stream
    
    async def pause_stream(self, stream_id: str) -> LogStream:
        """Pause stream."""
        stream = await self.stream_repo.get_by_id(stream_id)
        if not stream:
            raise ValueError(f"Stream not found: {stream_id}")
        
        stream.pause()
        await self.stream_repo.update(stream)
        return stream
    
    async def list_streams(self) -> List[LogStream]:
        """List all streams."""
        return await self.stream_repo.list_all()

