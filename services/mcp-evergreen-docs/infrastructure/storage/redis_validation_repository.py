"""Redis Validation Repository Implementation."""

from typing import List, Optional
import json
import redis.asyncio as redis

from ...domain.entities.validation_result import ValidationResult
from ...domain.repositories.validation_repository import ValidationRepository


class RedisValidationRepository(ValidationRepository):
    """Redis implementation of ValidationRepository."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize repository."""
        self.redis = redis_client
        self.prefix = "evergreen:validation:"
        self.index_key = "evergreen:validations:all"
        self.doc_index_prefix = "evergreen:validations:doc:"
    
    async def add(self, result: ValidationResult) -> None:
        """Add validation result."""
        key = f"{self.prefix}{result.result_id}"
        await self.redis.set(key, json.dumps(result.to_dict()))
        await self.redis.sadd(self.index_key, result.result_id)
        
        # Add to document-specific index
        doc_key = f"{self.doc_index_prefix}{result.doc_id}"
        await self.redis.zadd(
            doc_key,
            {result.result_id: result.validated_at.timestamp()},
        )
    
    async def get_by_id(self, result_id: str) -> Optional[ValidationResult]:
        """Get validation result by ID."""
        key = f"{self.prefix}{result_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return self._from_dict(json.loads(data))
    
    async def get_latest_by_doc(self, doc_id: str) -> Optional[ValidationResult]:
        """Get latest validation result for document."""
        doc_key = f"{self.doc_index_prefix}{doc_id}"
        
        # Get most recent (highest score/timestamp)
        result_ids = await self.redis.zrevrange(doc_key, 0, 0)
        if not result_ids:
            return None
        
        result_id = result_ids[0].decode() if isinstance(result_ids[0], bytes) else result_ids[0]
        return await self.get_by_id(result_id)
    
    async def list_by_doc(self, doc_id: str) -> List[ValidationResult]:
        """List all validation results for document."""
        doc_key = f"{self.doc_index_prefix}{doc_id}"
        
        # Get all results, most recent first
        result_ids = await self.redis.zrevrange(doc_key, 0, -1)
        results = []
        for result_id in result_ids:
            rid = result_id.decode() if isinstance(result_id, bytes) else result_id
            result = await self.get_by_id(rid)
            if result:
                results.append(result)
        return results
    
    async def delete(self, result_id: str) -> None:
        """Delete validation result."""
        # Get result to find doc_id
        result = await self.get_by_id(result_id)
        if result:
            doc_key = f"{self.doc_index_prefix}{result.doc_id}"
            await self.redis.zrem(doc_key, result_id)
        
        key = f"{self.prefix}{result_id}"
        await self.redis.delete(key)
        await self.redis.srem(self.index_key, result_id)
    
    async def find_invalid_docs(self) -> List[str]:
        """Find document IDs with invalid validation results."""
        result_ids = await self.redis.smembers(self.index_key)
        invalid_doc_ids = set()
        
        for result_id in result_ids:
            rid = result_id.decode() if isinstance(result_id, bytes) else result_id
            result = await self.get_by_id(rid)
            if result and not result.is_valid():
                invalid_doc_ids.add(result.doc_id)
        
        return list(invalid_doc_ids)
    
    def _from_dict(self, data: dict) -> ValidationResult:
        """Convert dict to ValidationResult entity."""
        from datetime import datetime
        
        # Remove summary field (it's computed)
        data.pop("summary", None)
        
        # Convert ISO strings back to datetime
        if data.get("validated_at"):
            data["validated_at"] = datetime.fromisoformat(data["validated_at"])
        
        return ValidationResult(**data)

