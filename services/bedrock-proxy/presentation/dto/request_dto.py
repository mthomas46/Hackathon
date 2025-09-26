"""Request Data Transfer Objects for presentation layer."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class InvokeRequestDTO(BaseModel):
    """Data Transfer Object for invoke requests."""

    model: Optional[str] = Field(None, description="AI model identifier")
    region: Optional[str] = Field(None, description="AWS region for model deployment")
    prompt: Optional[str] = Field(None, description="Input prompt for AI processing")
    template: Optional[str] = Field(None, description="Response template to use")
    format: Optional[str] = Field("md", description="Output format")
    title: Optional[str] = Field(None, description="Custom title for the response")

    class Config:
        """Pydantic configuration."""
        json_encoders = {}
        validate_assignment = True
