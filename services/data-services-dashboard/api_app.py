"""
FastAPI Application for Data Services Dashboard.

This is the standalone REST API that runs on port 8080.
It provides standard endpoints for ecosystem integration.

Run: uvicorn api_app:app --host 0.0.0.0 --port 8080
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import config
from api.router import api_router

# Create FastAPI app
app = FastAPI(
    title="Data Services Dashboard API",
    description="""
    REST API for the Data Services Dashboard.
    
    Provides standard endpoints for ecosystem monitoring and integration:
    - `/health` - Service health check
    - `/about-me` - Service metadata and capabilities
    - `/endpoints` - List of all API endpoints
    - `/provider-consumer` - Service relationship matrix
    - `/openapi.json` - OpenAPI specification
    
    The Streamlit UI runs on port 8501, this API runs on port 8080.
    """,
    version=config.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include API router with all standard endpoints
app.include_router(api_router, tags=["Standard Endpoints"])

# Root endpoint
@app.get("/", summary="API Root")
async def root():
    """
    API root endpoint. Redirects to documentation.
    """
    return {
        "service": config.service_name,
        "version": config.service_version,
        "api_version": "v1",
        "description": "Data Services Dashboard REST API",
        "documentation": f"http://localhost:{config.api_port}/docs",
        "streamlit_ui": f"http://localhost:{config.ui_port}",
        "endpoints": {
            "health": f"http://localhost:{config.api_port}/health",
            "about_me": f"http://localhost:{config.api_port}/about-me",
            "endpoints_list": f"http://localhost:{config.api_port}/endpoints",
            "provider_consumer": f"http://localhost:{config.api_port}/provider-consumer",
            "openapi": f"http://localhost:{config.api_port}/openapi.json"
        }
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup event."""
    print(f"🚀 FastAPI started on port {config.api_port}")
    print(f"📖 API Docs: http://localhost:{config.api_port}/docs")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown event."""
    print(f"🛑 FastAPI shutting down")

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.api_port,
        log_level="info"
    )

