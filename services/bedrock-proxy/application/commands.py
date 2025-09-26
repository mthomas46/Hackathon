"""Bedrock proxy commands for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class ProcessBedrockRequestCommand(BaseModel):
    """Command to process a Bedrock AI request."""
    request_id: str
    model: str
    prompt: str
    parameters: Optional[Dict[str, Any]] = None


class ValidateBedrockRequestCommand(BaseModel):
    """Command to validate a Bedrock request."""
    request_id: str
    content: Dict[str, Any]


class TransformBedrockResponseCommand(BaseModel):
    """Command to transform a Bedrock response."""
    request_id: str
    raw_response: Dict[str, Any]
    transformation_rules: Optional[Dict[str, Any]] = None
