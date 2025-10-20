"""
Business logic services for Ecosystem MCP Service.
"""

# Conditional imports to avoid circular dependencies
try:
    from .model_router import ModelRouter, get_model_router
    __all__ = [
        "ModelRouter",
        "get_model_router",
    ]
except ImportError:
    # Allow discovery module to be imported standalone
    __all__ = []

