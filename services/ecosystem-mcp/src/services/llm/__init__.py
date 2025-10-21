"""
LLM Services (Week 3)

Enhanced model routing and LLM integration.
"""

from .enhanced_model_router import (
    EnhancedModelRouter,
    CodeDetector,
    TaskType,
    ModelType,
    get_enhanced_model_router
)
from .model_router_integration import (
    ModelRouterIntegration,
    get_model_router_integration,
    select_model_for_analysis,
    should_use_codellama
)

__all__ = [
    "EnhancedModelRouter",
    "CodeDetector",
    "TaskType",
    "ModelType",
    "get_enhanced_model_router",
    "ModelRouterIntegration",
    "get_model_router_integration",
    "select_model_for_analysis",
    "should_use_codellama",
]

