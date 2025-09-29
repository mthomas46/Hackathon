"""Infrastructure events for Architecture Digitizer service.

This module handles application lifecycle events including startup
and shutdown procedures, service initialization, and cleanup operations.
"""

import time
from typing import Any, Dict, Optional

from services.shared.infrastructure.monitoring.logging import fire_and_forget
from services.shared.core.constants_new import ServiceNames


async def startup_event(app) -> None:
    """Initialize services on startup.

    Performs service initialization including logging client setup,
    capability registration, and startup event logging.

    Args:
        app: FastAPI application instance
    """
    # Set startup time for uptime calculation
    app._startup_time = time.time()

    try:
        # Log service startup with comprehensive metadata
        service_name = getattr(ServiceNames, "ARCHITECTURE_DIGITIZER", "architecture-digitizer")

        fire_and_forget(
            "info",
            "Architecture Digitizer service started",
            service_name,
            {
                "version": getattr(app, "version", "unknown"),
                "capabilities": [
                    "diagram_normalization",
                    "multi_format_support",
                    "external_api_integration",
                    "file_upload_processing",
                ],
                "integrations": [
                    "miro", "figjam", "lucid", "confluence", "log_collector"
                ],
                "supported_formats": [
                    "miro", "figjam", "lucid", "confluence", "json", "xml"
                ],
                "features": [
                    "authentication_handling",
                    "error_recovery",
                    "structured_output",
                    "component_extraction",
                ],
                "diagram_sources": ["miro", "figjam", "lucid", "confluence"],
                "output_formats": ["json", "xml"],
                "file_upload_enabled": True,
                "api_integration_ready": True,
            }
        )
    except Exception as e:
        print(f"Failed to initialize logging during startup: {e}")


async def shutdown_event(app) -> None:
    """Cleanup on shutdown.

    Performs graceful shutdown operations including logging
    the shutdown event and cleaning up resources.

    Args:
        app: FastAPI application instance
    """
    try:
        service_name = getattr(ServiceNames, "ARCHITECTURE_DIGITIZER", "architecture-digitizer")
        fire_and_forget(
            "info",
            "Architecture Digitizer service shutting down",
            service_name
        )
    except Exception as e:
        print(f"Error during shutdown logging: {e}")


def register_lifecycle_events(app) -> None:
    """Register application lifecycle event handlers.

    Args:
        app: FastAPI application instance to register events on
    """
    @app.on_event("startup")
    async def _startup():
        await startup_event(app)

    @app.on_event("shutdown")
    async def _shutdown():
        await shutdown_event(app)
