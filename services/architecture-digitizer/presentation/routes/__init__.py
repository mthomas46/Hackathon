"""Route modules for architecture-digitizer service."""

from .normalization_routes import router as normalization_router, init_normalization_routes
from .systems_routes import router as systems_router
from .standard_routes import router as standard_router, init_standard_routes

__all__ = [
    "normalization_router",
    "systems_router",
    "standard_router",
    "init_normalization_routes",
    "init_standard_routes",
]

