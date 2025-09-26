"""Response Data Transfer Objects for presentation layer."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class InvokeResponseDTO(BaseModel):
    """Data Transfer Object for invoke responses."""

    success: bool = Field(..., description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data payload")

    class Config:
        """Pydantic configuration."""
        json_encoders = {}
        validate_assignment = True
