"""Provider management for Summarizer Hub.

Handles provider registry and orchestration.
"""
from typing import Dict, Any, Callable, Optional
from .provider_implementations import provider_implementations


class ProviderManager:
    """Manages provider implementations and orchestration."""

    def __init__(self):
        self.provider_implementations: Dict[str, Callable] = {
            "ollama": provider_implementations.summarize_with_ollama,
            "openai": provider_implementations.summarize_with_openai,
            "anthropic": provider_implementations.summarize_with_anthropic,
            "grok": provider_implementations.summarize_with_grok,
            "bedrock": provider_implementations.summarize_with_bedrock,
        }

    async def summarize_with_provider(self, provider_name: str, provider_config, prompt: Optional[str], text: str) -> str:
        """Summarize using a specific provider."""
        impl = self.provider_implementations.get(provider_name.lower())
        if impl is None:
            # Fallback: echo with tag
            content = (prompt + "\n\n" if prompt else "") + text
            return f"[{provider_name}]\n" + content
        output = await impl(provider_config, prompt, text)
        return output or f"[{provider_name}]\n" + ((prompt + "\n\n") if prompt else "") + text


# Create singleton instance
provider_manager = ProviderManager()
