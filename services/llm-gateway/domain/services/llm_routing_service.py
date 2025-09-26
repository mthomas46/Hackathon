"""LLM Routing domain service for DDD compliance."""

from typing import List, Optional, Dict, Any
from ..entities.llm_provider import LLMProvider
from ..entities.llm_request import LLMRequest
from ..repositories.llm_provider_repository import LLMProviderRepository


class LLMRoutingService:
    """Domain service for routing LLM requests to appropriate providers."""

    def __init__(self, provider_repository: LLMProviderRepository):
        self._provider_repository = provider_repository

    async def route_request(self, request: LLMRequest) -> Optional[LLMProvider]:
        """Route an LLM request to the best available provider."""
        # Find providers that support the requested model
        providers = await self._provider_repository.find_supporting_model(request.model)

        if not providers:
            return None

        # Filter to active providers only
        active_providers = [p for p in providers if p.status.name == "ACTIVE"]

        if not active_providers:
            return None

        # For now, return the first active provider
        # In a real implementation, this could include load balancing,
        # cost optimization, latency considerations, etc.
        return active_providers[0]

    async def get_available_models(self) -> List[str]:
        """Get all available models across all active providers."""
        providers = await self._provider_repository.find_active()
        models = set()

        for provider in providers:
            models.update(provider.models)

        return sorted(list(models))

    async def validate_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Validate an LLM request."""
        issues = []

        if not request.prompt or not request.prompt.strip():
            issues.append("Prompt cannot be empty")

        if not request.model:
            issues.append("Model must be specified")

        # Check if model is supported by any active provider
        providers = await self._provider_repository.find_supporting_model(request.model)
        active_providers = [p for p in providers if p.status.name == "ACTIVE"]

        if not active_providers:
            issues.append(f"Model '{request.model}' is not supported by any active provider")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
