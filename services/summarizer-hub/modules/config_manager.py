"""Configuration management for Summarizer Hub.

Handles loading hub configuration from YAML files and merging provider
configurations with defaults for consistent service operation.
"""
from typing import Dict, Any, Optional
from services.shared.config import load_yaml_config, get_config_value


class ConfigManager:
    """Manages hub configuration loading and provider configuration merging.

    Provides centralized configuration management for the summarizer hub,
    allowing provider settings to be defined globally and merged with
    request-specific overrides.
    """

    @staticmethod
    def load_hub_config() -> Dict[str, Any]:
        """Load hub configuration from YAML configuration file.

        Returns the complete hub configuration dictionary containing
        provider defaults and other service-wide settings.

        Returns:
            Dictionary containing hub configuration, or empty dict if loading fails
        """
        config_path = get_config_value(
            "SH_CONFIG",
            "services/summarizer-hub/config.yaml",
            section="summarizer_hub",
            env_key="SH_CONFIG"
        )
        return load_yaml_config(config_path)

    @staticmethod
    def merge_provider_from_config(provider_config, hub_config: Dict[str, Any]):
        """Merge provider configuration with hub-wide defaults.

        Finds the provider by name in the hub configuration and fills in
        any missing fields from the global defaults. Request-specific
        values take precedence over hub defaults.

        Args:
            provider_config: The provider configuration from the request
            hub_config: The complete hub configuration dictionary

        Returns:
            Merged ProviderConfig object with defaults applied
        """
        from ..main import ProviderConfig  # Import here to avoid circular imports

        # Get providers list from hub config
        hub_providers = hub_config.get("providers") or []

        # Find matching provider by name (case-insensitive)
        for hub_provider_entry in hub_providers:
            if str(hub_provider_entry.get("name", "")).lower() == provider_config.name.lower():
                # Merge configurations, with request values taking precedence
                return ProviderConfig(
                    name=provider_config.name,
                    model=provider_config.model or hub_provider_entry.get("model"),
                    endpoint=provider_config.endpoint or hub_provider_entry.get("endpoint"),
                    api_key=provider_config.api_key or hub_provider_entry.get("api_key"),
                    region=provider_config.region or hub_provider_entry.get("region"),
                    profile=provider_config.profile or hub_provider_entry.get("profile"),
                )

        # Return original config if no hub defaults found
        return provider_config


# Create singleton instance
config_manager = ConfigManager()
