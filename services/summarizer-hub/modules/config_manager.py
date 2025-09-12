"""Configuration management for Summarizer Hub.

Handles loading hub configuration and merging provider configs.
"""
from typing import Dict, Any, Optional
from services.shared.config import load_yaml_config, get_config_value


class ConfigManager:
    """Manages hub configuration and provider merging."""

    @staticmethod
    def load_hub_config() -> Dict[str, Any]:
        """Load hub configuration from YAML file."""
        path = get_config_value("SH_CONFIG", "services/summarizer-hub/config.yaml", section="summarizer_hub", env_key="SH_CONFIG")
        return load_yaml_config(path)

    @staticmethod
    def merge_provider_from_config(provider_config, cfg: Dict[str, Any]):
        """Merge provider configuration with hub config.

        Finds provider by name in config and fills missing fields.
        """
        from ..main import ProviderConfig  # Import here to avoid circular imports

        providers = (cfg.get("providers") or [])
        for entry in providers:
            if str(entry.get("name")).lower() == provider_config.name.lower():
                return ProviderConfig(
                    name=provider_config.name,
                    model=provider_config.model or entry.get("model"),
                    endpoint=provider_config.endpoint or entry.get("endpoint"),
                    api_key=provider_config.api_key or entry.get("api_key"),
                    region=provider_config.region or entry.get("region"),
                    profile=provider_config.profile or entry.get("profile"),
                )
        return provider_config


# Create singleton instance
config_manager = ConfigManager()
