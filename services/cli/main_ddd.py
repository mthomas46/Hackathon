"""CLI Service - Domain-Driven Design Implementation

A FastAPI-based CLI service that provides command execution and session management
using Domain-Driven Design principles.
"""

import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domain.services.cli_command_service import CLICommandService
from domain.services.cli_session_service import CLISessionService
from application.use_cases.execute_command_use_case import ExecuteCommandUseCase
from application.use_cases.create_session_use_case import CreateSessionUseCase
from application.use_cases.manage_session_use_case import ManageSessionUseCase
from presentation.routes.commands import router as commands_router
from presentation.routes.sessions import router as sessions_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting CLI Service with DDD architecture")

    # Initialize domain services
    command_service = CLICommandService()
    session_service = CLISessionService()

    # Initialize application services
    app.state.execute_command_use_case = ExecuteCommandUseCase(
        command_service, session_service
    )
    app.state.create_session_use_case = CreateSessionUseCase(session_service)
    app.state.manage_session_use_case = ManageSessionUseCase(session_service)

    logger.info("CLI Service initialized successfully")
    yield

    # Shutdown
    logger.info("Shutting down CLI Service")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CLI Service",
        description="A Domain-Driven Design CLI service for command execution and session management",
        version="1.0.0",
        lifespan=lifespan
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(commands_router)
    app.include_router(sessions_router)

    # Health check endpoint
    @app.get("/health", summary="Health check", tags=["Health"])
    async def health_check():
        """Check service health."""
        return {
            "status": "healthy",
            "service": "cli-service",
            "architecture": "ddd",
            "version": "1.0.0"
        }

    # Root endpoint
    @app.get("/", summary="Service information", tags=["Info"])
    async def root():
        """Get service information."""
        return {
            "service": "CLI Service",
            "description": "Domain-Driven Design CLI service",
            "version": "1.0.0",
            "architecture": "DDD (Domain-Driven Design)",
            "layers": ["domain", "application", "infrastructure", "presentation"],
            "endpoints": {
                "commands": "/commands",
                "sessions": "/sessions",
                "health": "/health"
            }
        }

    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "services.cli.main_ddd:app",
        host="0.0.0.0",
        port=8008,  # CLI service port
        reload=True,
        log_level="info"
    )
