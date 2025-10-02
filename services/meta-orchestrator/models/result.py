"""Operation result models"""

from typing import Any, Optional
from pydantic import BaseModel


class OperationResult(BaseModel):
    """Result of a Docker operation"""
    success: bool
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
