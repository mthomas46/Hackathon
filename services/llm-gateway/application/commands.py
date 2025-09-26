"""LLM Gateway commands for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class ProcessLLMRequestCommand(BaseModel):
    """Command to process an LLM request."""
    request_id: str
    prompt: str
    model: str
    parameters: Optional[Dict[str, Any]] = None


class RegisterProviderCommand(BaseModel):
    """Command to register a new LLM provider."""
    provider_id: str
    name: str
    base_url: str
    api_key: str
    models: list
    rate_limits: Optional[Dict[str, int]] = None


class UpdateProviderStatusCommand(BaseModel):
    """Command to update provider status."""
    provider_id: str
    status: str


class CancelLLMRequestCommand(BaseModel):
    """Command to cancel an LLM request."""
    request_id: str


class RetryLLMRequestCommand(BaseModel):
    """Command to retry a failed LLM request."""
    request_id: str
