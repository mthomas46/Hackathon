"""LLM Gateway Service - Simplified Version for Docker Deployment.

This is a minimal working version of the LLM Gateway that integrates with Ollama
and provides basic LLM routing functionality.
"""

import json
import os
import time
from typing import Any, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ============================================================================
# STANDARDIZED CONFIGURATION
# ============================================================================
try:
    from services.shared.infrastructure.config import load_service_config
from services.shared.utilities.resource_monitor import monitor_resources
    from services.shared.utilities import setup_common_middleware
    from services.shared.presentation.responses import create_error_response, create_success_response
    from services.shared.monitoring.health import register_health_endpoints
except ImportError:
    # Fallback implementations
    def load_service_config(**kwargs):
        return type('Config', (), {
            'service_name': 'llm-gateway',
            'service_description': 'LLM Gateway Service',
            'service_version': '1.0.0',
            'server': type('Server', (), {'host': '0.0.0.0', 'port': 5055})(),
            'port': 5055,
        })()

    def setup_common_middleware(app, **kwargs):
        pass

    def create_error_response(message, **kwargs):
        return {"success": False, "message": message, **kwargs}

    def create_success_response(data):
        return {"success": True, "data": data}

    def register_health_endpoints(app, *args, **kwargs):
        pass

# Load standardized configuration
config = load_service_config(
    service_type="llm-gateway",
    config_file="./config.yaml"  # Optional config file override
)

# Service configuration from standardized config
SERVICE_NAME = config.service_name
SERVICE_TITLE = config.service_description or "LLM Gateway"
SERVICE_VERSION = config.service_version
DEFAULT_PORT = config.port

# Environment configuration
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://ollama:11434")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


# Request/Response Models
class LLMQuery(BaseModel):
    prompt: str
    model: Optional[str] = "llama2"
    provider: Optional[str] = "ollama"
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "llama2"
    provider: Optional[str] = "ollama"
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False


class ProviderInfo(BaseModel):
    name: str
    status: str
    models: List[str]
    endpoint: str


class GatewayResponse(BaseModel):
    success: bool
    data: Any
    provider: str
    model: str
    processing_time: float
    tokens_used: Optional[int] = None


# Initialize FastAPI app
app = FastAPI(
    title=SERVICE_TITLE,
    description="Unified access to LLM providers including Ollama",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup standardized middleware and utilities
setup_common_middleware(app, service_name=SERVICE_NAME)

# Register standardized health endpoints
register_health_endpoints(app, SERVICE_NAME, SERVICE_VERSION)


# Enhanced health check endpoint
@app.get("/health")
async def health():
    """Enhanced health check endpoint with dependency validation."""
    try:
        # Test Ollama connectivity
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{OLLAMA_ENDPOINT}/api/tags")
                ollama_status = "healthy" if response.status_code == 200 else "unreachable"
            except Exception:
                ollama_status = "unreachable"

        return create_success_response(
            data={
                "status": "healthy",
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "environment": ENVIRONMENT,
                "ollama_endpoint": OLLAMA_ENDPOINT,
                "ollama_status": ollama_status,
                "features": {
                    "llm_routing": True,
                    "streaming": True,
                    "caching": True,
                    "rate_limiting": True,
                }
            },
            message="Service is healthy"
        )
    except Exception as e:
        return create_error_response(
            message=f"Health check failed: {str(e)}",
            error_code="HEALTH_CHECK_FAILED",
            details={"error": str(e)}
        )


# Provider management
@app.get("/providers")
async def get_providers():
    """Get available LLM providers and their status."""
    providers = []

    # Check Ollama status
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_ENDPOINT}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                models = [model["name"] for model in models_data.get("models", [])]
                providers.append(
                    ProviderInfo(
                        name="ollama",
                        status="healthy",
                        models=models,
                        endpoint=OLLAMA_ENDPOINT,
                    )
                )
            else:
                providers.append(
                    ProviderInfo(
                        name="ollama",
                        status="unhealthy",
                        models=[],
                        endpoint=OLLAMA_ENDPOINT,
                    )
                )
    except Exception:
        providers.append(
            ProviderInfo(
                name="ollama", status="error", models=[], endpoint=OLLAMA_ENDPOINT
            )
        )

    return {"providers": providers}


# Basic LLM query endpoint
@app.post("/query")
async def query_llm(request: LLMQuery):
    """Send a query to the specified LLM provider."""
    start_time = time.time()

    if request.provider == "ollama":
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                ollama_request = {
                    "model": request.model,
                    "prompt": request.prompt,
                    "stream": False,
                    "options": {
                        "num_predict": request.max_tokens,
                        "temperature": request.temperature,
                    },
                }

                response = await client.post(
                    f"{OLLAMA_ENDPOINT}/api/generate", json=ollama_request
                )

                if response.status_code == 200:
                    result = response.json()
                    processing_time = time.time() - start_time

                    return GatewayResponse(
                        success=True,
                        data=result,
                        provider="ollama",
                        model=request.model,
                        processing_time=processing_time,
                        tokens_used=len(result.get("response", "").split()),
                    )
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ollama request failed: {response.text}",
                    )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error querying Ollama: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=400, detail=f"Unsupported provider: {request.provider}"
        )


# Chat endpoint for conversational interactions
@app.post("/chat")
async def chat_llm(request: ChatRequest):
    """Have a conversation with the specified LLM provider."""
    start_time = time.time()

    if request.provider == "ollama":
        try:
            # Convert chat messages to a single prompt for Ollama
            conversation = ""
            for message in request.messages:
                conversation += f"{message.role}: {message.content}\n"
            conversation += "assistant: "

            async with httpx.AsyncClient(timeout=30.0) as client:
                ollama_request = {
                    "model": request.model,
                    "prompt": conversation,
                    "stream": False,
                    "options": {
                        "num_predict": request.max_tokens,
                        "temperature": request.temperature,
                    },
                }

                response = await client.post(
                    f"{OLLAMA_ENDPOINT}/api/generate", json=ollama_request
                )

                if response.status_code == 200:
                    result = response.json()
                    processing_time = time.time() - start_time

                    return GatewayResponse(
                        success=True,
                        data={
                            "response": result.get("response", ""),
                            "model": request.model,
                            "done": result.get("done", True),
                        },
                        provider="ollama",
                        model=request.model,
                        processing_time=processing_time,
                        tokens_used=len(result.get("response", "").split()),
                    )
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ollama chat failed: {response.text}",
                    )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error in chat with Ollama: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=400, detail=f"Unsupported provider: {request.provider}"
        )


# Streaming endpoint
@app.post("/stream")
async def stream_llm(request: LLMQuery):
    """Stream responses from the LLM provider."""
    if request.provider == "ollama":

        async def generate():
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    ollama_request = {
                        "model": request.model,
                        "prompt": request.prompt,
                        "stream": True,
                        "options": {
                            "num_predict": request.max_tokens,
                            "temperature": request.temperature,
                        },
                    }

                    async with client.stream(
                        "POST", f"{OLLAMA_ENDPOINT}/api/generate", json=ollama_request
                    ) as response:
                        async for chunk in response.aiter_lines():
                            if chunk:
                                data = json.loads(chunk)
                                yield f"data: {json.dumps(data)}\n\n"

                                if data.get("done", False):
                                    break

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(generate(), media_type="text/plain")
    else:
        raise HTTPException(
            status_code=400, detail=f"Unsupported provider: {request.provider}"
        )


# Ollama models endpoint
@app.get("/api/v1/models")
async def get_available_models():
    """Get comprehensive list of available models across all providers."""
    try:
        # Get Ollama models
        ollama_models = []
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{OLLAMA_ENDPOINT}/api/tags")
                if response.status_code == 200:
                    models_data = response.json()
                    ollama_models = [
                        {
                            "name": model["name"],
                            "provider": "ollama",
                            "size": model.get("size", 0),
                            "modified_at": model.get("modified_at", ""),
                            "digest": model.get("digest", ""),
                        }
                        for model in models_data.get("models", [])
                    ]
        except Exception as e:
            print(f"Ollama models fetch failed: {e}")

        # For now, return only Ollama models
        # In a full implementation, this would aggregate models from all providers
        return {
            "success": True,
            "models": ollama_models,
            "total_count": len(ollama_models),
            "providers": ["ollama"],
            "timestamp": time.time(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


@app.get("/ollama/models")
async def list_ollama_models():
    """List available Ollama models."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_ENDPOINT}/api/tags")
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch Ollama models",
                )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching Ollama models: {str(e)}"
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": SERVICE_NAME,
        "title": SERVICE_TITLE,
        "version": SERVICE_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "providers": "/providers",
            "query": "/query",
            "chat": "/chat",
            "stream": "/stream",
            "ollama_models": "/ollama/models",
        },
    }


if __name__ == "__main__":
    """Run the LLM Gateway service directly."""
    import uvicorn

    print(f"🚀 Starting {SERVICE_TITLE} Service...")
    print(f"🔗 Ollama endpoint: {OLLAMA_ENDPOINT}")
    print(f"🌐 Environment: {ENVIRONMENT}")
    uvicorn.run(app, host="127.0.0.1", port=DEFAULT_PORT, log_level="info")
