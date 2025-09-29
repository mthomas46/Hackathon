"""Log collector commands for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class CollectLogCommand(BaseModel):
    """Command to collect a log entry."""
    service: str
    level: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None


class QueryLogsCommand(BaseModel):
    """Command to query logs."""
    service: Optional[str] = None
    level: Optional[str] = None
    limit: int = 50
    offset: int = 0


class ExportLogsCommand(BaseModel):
    """Command to export logs."""
    format: str = "json"
    filters: Optional[Dict[str, Any]] = None
