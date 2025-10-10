"""Routes for expert-finder-service"""

from .expert_routes import router as expert_router
from .standard_routes import router as standard_router

__all__ = ["expert_router", "standard_router"]

