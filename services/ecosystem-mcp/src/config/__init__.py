"""
Configuration registry module.

Provides centralized configuration management through a single source of truth.

Note: This module (src/config/) shadows the settings file (src/config.py).
We re-export settings here to maintain backward compatibility.
"""

from .registry import get_registry, RegistryLoader, ServiceRegistry

# Import settings from parent config.py
# We use exec to load it directly to avoid import path conflicts
import sys
from pathlib import Path

_config_file = Path(__file__).parent.parent / "config.py"
_config_globals = {
    '__file__': str(_config_file),
    '__name__': 'src.config',
    '__package__': 'src',
}
with open(_config_file) as f:
    exec(f.read(), _config_globals)

settings = _config_globals['settings']

__all__ = [
    "get_registry",
    "RegistryLoader", 
    "ServiceRegistry",
    "settings",
]

