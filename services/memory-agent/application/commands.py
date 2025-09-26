"""Memory agent commands for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class StoreMemoryCommand(BaseModel):
    """Command to store a memory item."""
    user_id: str
    memory_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class UpdateMemoryCommand(BaseModel):
    """Command to update a memory item."""
    memory_id: str
    content: str


class RetrieveMemoriesCommand(BaseModel):
    """Command to retrieve memories."""
    user_id: str
    memory_type: Optional[str] = None
    limit: int = 50


class DeleteMemoryCommand(BaseModel):
    """Command to delete a memory item."""
    memory_id: str


class GetMemoryStatsCommand(BaseModel):
    """Command to get memory statistics."""
    user_id: str
