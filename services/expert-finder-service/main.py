"""
Expert Finder Service - Main Application Entry Point

Refactored DDD architecture with clean separation of concerns.

Architecture:
- domain/: Business logic (entities, value objects, domain services)
- application/: Use cases (orchestration)
- infrastructure/: External integrations (repositories, config)
- presentation/: API routes (request/response handling)
- utils/: Shared utilities (validators, transformers, constants)

Reduced from 1,286 lines (monolithic) to ~90 lines (focused app setup).
MANDATORY refactoring from Phase 2.8 (CRITICAL - split large file).
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import configuration
from infrastructure.config.settings import get_settings

# Import routes
from presentation.routes.standard_routes import router as standard_router
from presentation.routes.expert_routes import router as expert_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="Expert Finder Service",
    description="""
    ## Intelligent User Discovery & Subject Matter Expert Identification
    
    Smart, relevance-based expert matching using multi-factor scoring:
    - Role Matching (30% weight)
    - Topic/Interest Matching (40% weight) - Strongest signal
    - Service Contributions (20% weight)
    - Document Authorship (10% weight)
    
    **Architecture**: Domain-Driven Design (DDD) with clean layers
    **Dependencies**: user-store (required), doc-store, external-service-store (optional)
    
    **Refactored**: October 2025 - Reduced from 1,286 lines to modular DDD structure
    """,
    version=settings.service_version,
    contact={"name": "Hackathon Team"},
    license_info={"name": "MIT"},
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Register routes
app.include_router(standard_router)  # Standard endpoints (health, about-me, etc.)
app.include_router(expert_router)    # Business endpoints (find-experts, etc.)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info(f"=== Starting {settings.service_name} v{settings.service_version} ===")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Port: {settings.service_port}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Dependencies:")
    logger.info(f"  - user-store: {settings.user_store_url} (required)")
    logger.info(f"  - doc-store: {settings.doc_store_url} (optional)")
    logger.info(f"  - external-service-store: {settings.service_store_url} (optional)")
    logger.info(f"Scoring weights: role={settings.role_weight}, topic={settings.topic_weight}, "
                f"service={settings.service_weight}, document={settings.document_weight}")
    logger.info("=== Service ready ===")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information."""
    logger.info(f"=== Shutting down {settings.service_name} ===")


# Main entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=settings.debug
    )
