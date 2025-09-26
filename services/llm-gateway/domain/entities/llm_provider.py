"""LLM Provider domain entity for DDD compliance."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ProviderStatus(Enum):
    """Status of LLM provider."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


@dataclass
class LLMProvider:
    """Domain entity representing an LLM provider."""

    id: str
    name: str
    base_url: str
    api_key: str
    models: List[str]
    status: ProviderStatus = ProviderStatus.ACTIVE
    rate_limits: Dict[str, int] = None  # requests_per_minute, tokens_per_minute, etc.
    capabilities: List[str] = None  # streaming, function_calling, etc.
    metadata: Dict[str, str] = None

    def __post_init__(self):
        if self.rate_limits is None:
            self.rate_limits = {}
        if self.capabilities is None:
            self.capabilities = []
        if self.metadata is None:
            self.metadata = {}

    def is_model_supported(self, model: str) -> bool:
        """Check if provider supports a specific model."""
        return model in self.models

    def has_capability(self, capability: str) -> bool:
        """Check if provider has a specific capability."""
        return capability in self.capabilities

    def update_status(self, status: ProviderStatus) -> None:
        """Update provider status."""
        self.status = status

    def add_model(self, model: str) -> None:
        """Add a supported model."""
        if model not in self.models:
            self.models.append(model)

    def remove_model(self, model: str) -> None:
        """Remove a supported model."""
        if model in self.models:
            self.models.remove(model)
