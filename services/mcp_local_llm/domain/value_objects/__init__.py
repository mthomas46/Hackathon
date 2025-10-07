"""Domain value objects for MCP Local LLM Service."""

from .generation_params import GenerationParams
from .model_config import ModelConfig

__all__ = [
    "GenerationParams",
    "ModelConfig",
]

