"""LLM Gateway Service - Simplified Version for Docker Deployment.

This is a minimal working version of the LLM Gateway that integrates with Ollama
and provides basic LLM routing functionality.
"""

from pathlib import Path

# Configuration loading
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


def load_config() -> dict:
    """Load service configuration from config file."""
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


# Load configuration
config = load_config()

# Extract configuration values with environment variable override
ENVIRONMENT = os.getenv("ENVIRONMENT", config.get("environment", "default_value"))
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", config.get("ollama-endpoint", "default_value"))
REDIS_HOST = os.getenv("REDIS_HOST", config.get("redis-host", "default_value"))

import json
import os
import time
from typing import Any, List, Optional

import httpx

from services.shared.core.constants_new import ServiceNames
from services.shared.utilities.logging_client import get_log_collector_client

# Service configuration
SERVICE_NAME = "llm-gateway"
SERVICE_TITLE = "LLM Gateway"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5055

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


# Initialize log collector client
logger_client = None

# Initialize FastAPI app
app = FastAPI(
    title=SERVICE_TITLE, description="Unified access to LLM providers including Ollama", version=SERVICE_VERSION
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global logger_client
    try:
        logger_client = await get_log_collector_client(ServiceNames.LLM_GATEWAY)
        if logger_client:
            await logger_client.log_business_event(
                "llm_gateway_startup",
                {
                    "version": SERVICE_VERSION,
                    "providers": ["ollama", "bedrock"],
                    "models": ["llama2", "codellama", "mistral"],
                    "capabilities": ["text_generation", "chat_completion", "streaming", "model_routing"],
                    "integrations": ["redis_cache", "log_collector"],
                    "features": ["load_balancing", "failover", "performance_monitoring"],
                },
            )
            await logger_client.log_info(
                "LLM Gateway service started",
                {
                    "ollama_endpoint": OLLAMA_ENDPOINT,
                    "environment": ENVIRONMENT,
                    "providers_count": 2,
                    "models_available": ["llama2", "codellama", "mistral"],
                    "streaming_enabled": True,
                },
            )
    except Exception as e:
        print(f"Failed to initialize log collector client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if logger_client:
        try:
            await logger_client.log_info("LLM Gateway service shutting down")
        except Exception:
            pass


# Simple health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": time.time(),
        "environment": ENVIRONMENT,
        "ollama_endpoint": OLLAMA_ENDPOINT,
    }


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
                providers.append(ProviderInfo(name="ollama", status="healthy", models=models, endpoint=OLLAMA_ENDPOINT))
            else:
                providers.append(ProviderInfo(name="ollama", status="unhealthy", models=[], endpoint=OLLAMA_ENDPOINT))
    except Exception as e:
        providers.append(ProviderInfo(name="ollama", status="error", models=[], endpoint=OLLAMA_ENDPOINT))

    return {"providers": providers}


# Basic LLM query endpoint
@app.post("/query")
async def query_llm(request: LLMQuery):
    """Send a query to the specified LLM provider."""
    start_time = time.time()
    request_id = f"llm_query_{int(time.time() * 1000)}"

    try:
        # Log LLM query start
        if logger_client:
            await logger_client.log_business_event(
                "llm_query_started",
                {
                    "request_id": request_id,
                    "provider": request.provider,
                    "model": request.model,
                    "prompt_length": len(request.prompt),
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "streaming": request.stream,
                },
            )

            await logger_client.log_info(
                "Processing LLM query",
                {
                    "request_id": request_id,
                    "provider": request.provider,
                    "model": request.model,
                    "prompt_preview": request.prompt[:100] + "..." if len(request.prompt) > 100 else request.prompt,
                },
            )

        if request.provider == "ollama":
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    ollama_request = {
                        "model": request.model,
                        "prompt": request.prompt,
                        "stream": False,
                        "options": {"num_predict": request.max_tokens, "temperature": request.temperature},
                    }

                    response = await client.post(f"{OLLAMA_ENDPOINT}/api/generate", json=ollama_request)

                    processing_time = time.time() - start_time

                    if response.status_code == 200:
                        result = response.json()
                        tokens_used = len(result.get("response", "").split())

                        # Log successful LLM query
                        if logger_client:
                            await logger_client.log_business_event(
                                "llm_query_completed",
                                {
                                    "request_id": request_id,
                                    "provider": "ollama",
                                    "model": request.model,
                                    "processing_time_seconds": processing_time,
                                    "tokens_used": tokens_used,
                                    "success": True,
                                    "response_length": len(result.get("response", "")),
                                },
                            )

                            await logger_client.log_performance_metric(
                                "llm_query",
                                processing_time,
                                {
                                    "request_id": request_id,
                                    "provider": "ollama",
                                    "model": request.model,
                                    "tokens_used": tokens_used,
                                    "query_success": True,
                                },
                            )

                        return GatewayResponse(
                            success=True,
                            data=result,
                            provider="ollama",
                            model=request.model,
                            processing_time=processing_time,
                            tokens_used=tokens_used,
                        )
                    else:
                        # Log LLM query failure
                        if logger_client:
                            await logger_client.log_error(
                                f"LLM query failed: Ollama request failed with status {response.status_code}",
                                {
                                    "request_id": request_id,
                                    "provider": "ollama",
                                    "model": request.model,
                                    "processing_time_seconds": processing_time,
                                    "http_status_code": response.status_code,
                                    "error_type": "provider_error",
                                },
                                error=Exception(f"Ollama request failed: {response.text}"),
                            )

                            await logger_client.log_business_event(
                                "llm_query_failed",
                                {
                                    "request_id": request_id,
                                    "provider": "ollama",
                                    "model": request.model,
                                    "processing_time_seconds": processing_time,
                                    "error_type": "provider_error",
                                    "http_status_code": response.status_code,
                                },
                            )

                        raise HTTPException(
                            status_code=response.status_code, detail=f"Ollama request failed: {response.text}"
                        )

            except Exception as e:
                error_time = time.time() - start_time

                # Log LLM query exception
                if logger_client:
                    await logger_client.log_error(
                        f"LLM query failed: {str(e)}",
                        {
                            "request_id": request_id,
                            "provider": "ollama",
                            "model": request.model,
                            "processing_time_seconds": error_time,
                            "error_type": type(e).__name__,
                        },
                        error=e,
                    )

                    await logger_client.log_business_event(
                        "llm_query_failed",
                        {
                            "request_id": request_id,
                            "provider": "ollama",
                            "model": request.model,
                            "processing_time_seconds": error_time,
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                        },
                    )

                raise HTTPException(status_code=500, detail=f"Error querying Ollama: {str(e)}")
        else:
            # Log unsupported provider
            error_time = time.time() - start_time

            if logger_client:
                await logger_client.log_error(
                    f"LLM query failed: Unsupported provider {request.provider}",
                    {
                        "request_id": request_id,
                        "provider": request.provider,
                        "model": request.model,
                        "processing_time_seconds": error_time,
                        "error_type": "unsupported_provider",
                    },
                    error=Exception(f"Unsupported provider: {request.provider}"),
                )

            raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log unexpected error
        if logger_client:
            await logger_client.log_error(
                f"LLM query failed unexpectedly: {str(e)}",
                {
                    "request_id": request_id,
                    "provider": request.provider if "request" in locals() else None,
                    "model": request.model if "request" in locals() else None,
                    "processing_time_seconds": error_time,
                    "error_type": "unexpected_error",
                },
                error=e,
            )

        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


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
                    "options": {"num_predict": request.max_tokens, "temperature": request.temperature},
                }

                response = await client.post(f"{OLLAMA_ENDPOINT}/api/generate", json=ollama_request)

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
                    raise HTTPException(status_code=response.status_code, detail=f"Ollama chat failed: {response.text}")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error in chat with Ollama: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")


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
                        "options": {"num_predict": request.max_tokens, "temperature": request.temperature},
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
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")


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
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch Ollama models")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Ollama models: {str(e)}")


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
    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
