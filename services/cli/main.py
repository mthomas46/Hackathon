"""CLI Service - Domain-Driven Design Implementation

A FastAPI-based CLI service that provides command execution and session management
using Domain-Driven Design principles.
"""

import os
import sys
import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for proper imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from services.shared.infrastructure.config import load_service_config
    from services.shared.infrastructure.utilities.middleware import setup_common_middleware
    from services.shared.presentation.api.responses import create_error_response, create_success_response
    from services.shared.monitoring.health import register_health_endpoints
except ImportError:
    # Fallback implementations
    def load_service_config(**kwargs):
        return type('Config', (), {
            'service_name': 'cli',
            'service_description': 'CLI Service',
            'service_version': '1.0.0',
        })()

    def setup_common_middleware(app, **kwargs):
        pass

    def create_error_response(message, **kwargs):
        return {"success": False, "message": message, **kwargs}

    def create_success_response(data):
        return {"success": True, "data": data}

    def register_health_endpoints(app, *args, **kwargs):
        pass

# Simplified imports - bypass complex dependencies for now
try:
    from domain.services.cli_command_service import CLICommandService
    from domain.services.cli_session_service import CLISessionService
    from application.use_cases.execute_command_use_case import ExecuteCommandUseCase
    from application.use_cases.create_session_use_case import CreateSessionUseCase
    from application.use_cases.manage_session_use_case import ManageSessionUseCase
    from presentation.routes.commands import router as commands_router
    from presentation.routes.sessions import router as sessions_router
except ImportError:
    # Create stub implementations
    class CLICommandService:
        def __init__(self): pass

    class CLISessionService:
        def __init__(self): pass

    class ExecuteCommandUseCase:
        def __init__(self, *args): pass

    class CreateSessionUseCase:
        def __init__(self, *args): pass

    class ManageSessionUseCase:
        def __init__(self, *args): pass

    # Create stub routers
    from fastapi import APIRouter
    commands_router = APIRouter(prefix="/api/v1/commands")
    sessions_router = APIRouter(prefix="/api/v1/sessions")

    @commands_router.get("/")
    async def list_commands():
        return {"commands": ["help", "status", "analyze"], "status": "stub"}

    @sessions_router.get("/")
    async def list_sessions():
        return {"sessions": [], "status": "stub"}


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Configure default environment variables for service URLs
def configure_service_urls():
    """Configure default service URLs as environment variables if not set."""
    defaults = {
        # Core Services
        "ANALYSIS_SERVICE_URL": "http://localhost:5020",
        "PROMPT_STORE_URL": "http://localhost:5110",
        "MEMORY_AGENT_URL": "http://localhost:5040",
        "SOURCE_AGENT_URL": "http://localhost:5000",
        "DOC_STORE_URL": "http://localhost:5010",
        "GITHUB_AGENT_URL": "http://localhost:5072",
        "INTERPRETER_URL": "http://localhost:5120",
        "SECURE_ANALYZER_URL": "http://localhost:5070",

        # Supporting Services
        "LOG_COLLECTOR_URL": "http://localhost:5050",
        "NOTIFICATION_SERVICE_URL": "http://localhost:5060",
        "ORCHESTRATOR_URL": "http://localhost:5000",
        "SUMMARIZER_HUB_URL": "http://localhost:5030",
        "CODE_ANALYZER_URL": "http://localhost:5090",
        "BEDROCK_PROXY_URL": "http://localhost:5055",
        "ARCHITECTURE_DIGITIZER_URL": "http://localhost:5100",
        "LLM_GATEWAY_URL": "http://localhost:5055",

        # External Services
        "OLLAMA_ENDPOINT": "http://localhost:11434",
        "REDIS_URL": "redis://localhost:6379",
        "DATABASE_URL": "sqlite:///./cli.db",

        # CLI Service Configuration
        "CLI_SERVICE_API_HOST": "127.0.0.1",
        "CLI_SERVICE_API_PORT": "5130",
        "CLI_DEBUG_MODE": "false",
        "CLI_LOG_LEVEL": "INFO",
    }

    # Set defaults only if not already set
    for key, default_value in defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value
            logger.debug(f"Set default {key}={default_value}")


# Configure service URLs before application startup
configure_service_urls()

# Service configuration - hardcoded for now due to config issues
SERVICE_NAME = "cli"
SERVICE_TITLE = "CLI Service"
SERVICE_VERSION = "1.0.0"
DEFAULT_API_PORT = int(os.environ.get("SERVICE_API_PORT", "5130"))

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
        title=SERVICE_TITLE,
        description="A Domain-Driven Design CLI service for command execution and session management",
        version=SERVICE_VERSION,
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
        "services.cli.main:app",
        host="0.0.0.0",
        port=DEFAULT_API_PORT,
        reload=True,
        log_level="info"
    )
