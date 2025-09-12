"""Policy enforcement for secure analyzer service."""

import os
from typing import List, Dict, Any, Optional


class PolicyEnforcer:
    """Enforces security policies for provider selection."""

    def __init__(self):
        self._secure_only_models = self._load_secure_models()
        self._all_providers = self._load_all_providers()

    def get_allowed_models(self, sensitive: bool) -> List[str]:
        """Get allowed models based on content sensitivity."""
        if sensitive:
            return self._secure_only_models.copy()
        return self._all_providers.copy()

    def filter_providers(
        self,
        providers: Optional[List[Dict[str, Any]]],
        sensitive: bool,
        override_policy: bool = False
    ) -> List[Dict[str, Any]]:
        """Filter providers based on security policy."""

        if sensitive and not override_policy:
            # Filter to secure providers only
            secure_names = set(self._secure_only_models)
            filtered = [
                p for p in (providers or [])
                if str(p.get("name", "")).lower() in secure_names
            ]

            # If no secure providers specified, default to bedrock then ollama
            if not filtered:
                filtered = [{"name": "bedrock"}, {"name": "ollama"}]

            return filtered

        # No policy enforcement needed
        return providers or [{"name": "ollama"}]

    def get_policy_suggestion(self, sensitive: bool) -> str:
        """Get policy suggestion message."""
        if sensitive:
            secure_models = ", ".join(self._secure_only_models)
            return f"Sensitive content detected. Recommend secure models: {secure_models}"
        return "No sensitive content detected. All models allowed."

    def _load_secure_models(self) -> List[str]:
        """Load secure-only models from environment."""
        models = os.environ.get("SECURE_ONLY_MODELS", "bedrock,ollama").split(",")
        return [m.strip() for m in models if m.strip()]

    def _load_all_providers(self) -> List[str]:
        """Load all available providers from environment."""
        providers = os.environ.get("ALL_PROVIDERS", "bedrock,ollama,openai,anthropic,grok").split(",")
        return [p.strip() for p in providers if p.strip()]


# Global policy enforcer instance
policy_enforcer = PolicyEnforcer()
