from __future__ import annotations

from typing import Any, Dict, Optional
import os

_CONFIG_CACHE: Dict[str, Any] = {}


def load_yaml_config(default_path: str) -> Dict[str, Any]:
    """Load a YAML file and return a dict. Returns {} on any error.

    Keep intentionally simple to avoid adding new runtime deps beyond PyYAML
    which is already present in the project for other components.
    """
    try:
        import yaml  # type: ignore
        with open(default_path, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _load_app_config() -> Dict[str, Any]:
    """Load a global app config once (config.yml or config/app.yaml) if present."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE:
        return _CONFIG_CACHE

    # Check for unified config.yml first, then fall back to config/app.yaml
    config_paths = [
        os.environ.get("APP_CONFIG_PATH"),  # Explicit override
        "config.yml",                       # Unified config at project root
        "config/app.yaml"                   # Legacy config location
    ]

    for cfg_path in config_paths:
        if cfg_path and os.path.exists(cfg_path):
            _CONFIG_CACHE = load_yaml_config(cfg_path) or {}
            if _CONFIG_CACHE:  # Only use if we successfully loaded something
                break

    return _CONFIG_CACHE


def get_config_value(key: str,
                     default: Any = None,
                     section: Optional[str] = None,
                     env_key: Optional[str] = None) -> Any:
    """Return a configuration value with precedence: env > app.yaml section > app.yaml root > default.

    Args:
        key: config key to look up
        default: default value if not found
        section: optional config section (e.g., "redis" or "services")
        env_key: optional environment var name (defaults to key)
    """
    # 1) Environment variable takes precedence
    env_name = env_key or key
    if env_name in os.environ:
        return os.environ.get(env_name, default)

    # 2) Config file lookup
    cfg = _load_app_config()
    if section and isinstance(cfg.get(section), dict):
        if key in cfg[section]:
            return cfg[section][key]

    if key in cfg:
        return cfg[key]

    # 3) Default
    return default


