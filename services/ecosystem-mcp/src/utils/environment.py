"""
Environment validation utilities.

Ensures application runs only in allowed environments.
"""

from enum import Enum
from typing import List


class Environment(Enum):
    """Allowed environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


ALLOWED_ENVIRONMENTS = [env.value for env in Environment]


def validate_environment(environment: str) -> bool:
    """
    Validate that environment is allowed.
    
    Args:
        environment: Environment name
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If environment is not allowed
    
    Example:
        >>> validate_environment("production")  # OK
        >>> validate_environment("invalid")  # Raises ValueError
    """
    #  Note: Using ValueError instead of ValidationError here to avoid circular import
    # when this is called during Settings model validation
    if environment.lower() not in ALLOWED_ENVIRONMENTS:
        raise ValueError(
            f"Invalid environment: '{environment}'. "
            f"Allowed: {', '.join(ALLOWED_ENVIRONMENTS)}"
        )
    return True


def get_environment_config(environment: str) -> dict:
    """
    Get configuration for specific environment.
    
    Args:
        environment: Environment name
    
    Returns:
        Environment-specific configuration
    """
    validate_environment(environment)
    
    configs = {
        Environment.DEVELOPMENT.value: {
            "debug": True,
            "log_level": "DEBUG",
            "json_logs": False,
            "preflight_mode": "lenient",
        },
        Environment.STAGING.value: {
            "debug": False,
            "log_level": "INFO",
            "json_logs": True,
            "preflight_mode": "strict",
        },
        Environment.PRODUCTION.value: {
            "debug": False,
            "log_level": "WARNING",
            "json_logs": True,
            "preflight_mode": "strict",
        },
        Environment.TEST.value: {
            "debug": True,
            "log_level": "DEBUG",
            "json_logs": False,
            "preflight_mode": "lenient",
        },
    }
    
    return configs.get(environment.lower(), configs[Environment.DEVELOPMENT.value])

