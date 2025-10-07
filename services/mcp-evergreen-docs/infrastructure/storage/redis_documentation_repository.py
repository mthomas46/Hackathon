"""Redis Documentation Repository Implementation."""

from typing import List, Optional
import json
import redis.asyncio as redis

from ...domain.entities.documentation import Documentation
from ...domain.repositories.documentation_repository import DocumentationRepository


class RedisDocumentationRepository(DocumentationRepository):
    """Redis implementation of DocumentationRepository."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize repository."""
        self.redis = redis_client
        self.prefix = "evergreen:doc:"
        self.index_key = "evergreen:docs:all"
    
    async def add(self, doc: Documentation) -> None:
        """Add documentation."""
        key = f"{self.prefix}{doc.doc_id}"
        await self.redis.set(key, json.dumps(doc.to_dict()))
        await self.redis.sadd(self.index_key, doc.doc_id)
    
    async def get_by_id(self, doc_id: str) -> Optional[Documentation]:
        """Get documentation by ID."""
        key = f"{self.prefix}{doc_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return self._from_dict(json.loads(data))
    
    async def update(self, doc: Documentation) -> None:
        """Update documentation."""
        await self.add(doc)
    
    async def delete(self, doc_id: str) -> None:
        """Delete documentation."""
        key = f"{self.prefix}{doc_id}"
        await self.redis.delete(key)
        await self.redis.srem(self.index_key, doc_id)
    
    async def list_all(self) -> List[Documentation]:
        """List all documentation."""
        doc_ids = await self.redis.smembers(self.index_key)
        docs = []
        for doc_id in doc_ids:
            doc = await self.get_by_id(doc_id.decode() if isinstance(doc_id, bytes) else doc_id)
            if doc:
                docs.append(doc)
        return docs
    
    async def find_by_path(self, file_path: str) -> Optional[Documentation]:
        """Find documentation by file path."""
        docs = await self.list_all()
        for doc in docs:
            if doc.file_path == file_path:
                return doc
        return None
    
    async def find_by_source(self, source_type: str, source_repo: str) -> List[Documentation]:
        """Find documentation by source."""
        docs = await self.list_all()
        return [
            doc for doc in docs
            if doc.source_type == source_type and doc.source_repo == source_repo
        ]
    
    async def find_outdated(self) -> List[Documentation]:
        """Find outdated documentation."""
        docs = await self.list_all()
        return [doc for doc in docs if doc.needs_update]
    
    async def find_by_tags(self, tags: List[str]) -> List[Documentation]:
        """Find documentation by tags."""
        docs = await self.list_all()
        return [
            doc for doc in docs
            if any(tag in doc.tags for tag in tags)
        ]
    
    def _from_dict(self, data: dict) -> Documentation:
        """Convert dict to Documentation entity."""
        from datetime import datetime
        
        # Convert ISO strings back to datetime
        for field in ("created_at", "updated_at", "generated_at", "last_synced_at", "validation_timestamp"):
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        return Documentation(**data)

