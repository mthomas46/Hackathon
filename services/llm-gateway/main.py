"""LLM Gateway Service - Unified Access to LLM Resources.

The LLM Gateway provides centralized, secure, and optimized access to all LLM providers
in the ecosystem. It acts as a service mesh for LLM operations while preserving
specialized service capabilities.

Endpoints:
- POST /query: Generic LLM query with provider routing
- POST /chat: Conversational LLM interactions
- POST /embeddings: Text embedding generation
- POST /stream: Streaming LLM responses
- GET /providers: Available LLM providers and status
- GET /metrics: LLM usage metrics and costs
- POST /cache/clear: Cache management
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, AsyncGenerator
import asyncio
import time
import json
import os
import httpx

# ============================================================================
# SIMPLIFIED SHARED UTILITIES - Core functionality without complex dependencies
# ============================================================================

def create_success_response(message: str, data: Any = None) -> Dict[str, Any]:
    """Create a standardized success response."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": time.time()
    }

def create_error_response(error: str, error_code: str = "INTERNAL_ERROR") -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "success": False,
        "error": error,
        "error_code": error_code,
        "timestamp": time.time()
    }

def fire_and_forget(event: str, details: Dict[str, Any] = None):
    """Simple logging function for fire-and-forget events."""
    print(f"[{time.time()}] {event}: {details or {}}")

def increment_counter(metric_name: str, tags: Dict[str, str] = None):
    """Simple counter increment for metrics."""
    print(f"[METRIC] Counter {metric_name} incremented with tags: {tags or {}}")

def record_histogram(metric_name: str, value: float, tags: Dict[str, str] = None):
    """Simple histogram recording for metrics."""
    print(f"[METRIC] Histogram {metric_name} = {value} with tags: {tags or {}}")

# ============================================================================
# LLM GATEWAY MODELS - Request/Response structures
# ============================================================================

class LLMQuery(BaseModel):
    prompt: str
    model: Optional[str] = "llama2"
    provider: Optional[str] = "ollama"
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False
    context: Optional[str] = None

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

class EmbeddingRequest(BaseModel):
    text: str
    model: Optional[str] = "all-minilm"
    provider: Optional[str] = "ollama"

class ProviderInfo(BaseModel):
    name: str
    status: str
    models: List[str]
    endpoint: str
    features: List[str] = []

class GatewayResponse(BaseModel):
    success: bool
    data: Any
    provider: str
    model: str
    processing_time: float
    tokens_used: Optional[int] = None
    cached: Optional[bool] = False

class MetricsResponse(BaseModel):
    total_requests: int
    requests_by_provider: Dict[str, int]
    average_response_time: float
    cache_hit_rate: float
    error_rate: float

class CacheRequest(BaseModel):
    key: Optional[str] = None
    clear_all: Optional[bool] = False

# ============================================================================
# SIMPLIFIED PROVIDER ROUTER - Core LLM routing functionality
# ============================================================================

class ProviderRouter:
    """Simplified provider routing for LLM requests."""
    
    def __init__(self):
        self.ollama_endpoint = os.getenv("OLLAMA_ENDPOINT", "http://ollama:11434")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.bedrock_endpoint = os.getenv("BEDROCK_ENDPOINT", "http://bedrock-proxy:5060")
        
    async def route_query(self, query: LLMQuery) -> GatewayResponse:
        """Route LLM query to appropriate provider."""
        start_time = time.time()
        
        if query.provider == "ollama":
            return await self._query_ollama(query, start_time)
        elif query.provider == "openai" and self.openai_api_key:
            return await self._query_openai(query, start_time)
        elif query.provider == "anthropic" and self.anthropic_api_key:
            return await self._query_anthropic(query, start_time)
        elif query.provider == "bedrock":
            return await self._query_bedrock(query, start_time)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported or unconfigured provider: {query.provider}"
            )
    
    async def _query_ollama(self, query: LLMQuery, start_time: float) -> GatewayResponse:
        """Query Ollama provider."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                ollama_request = {
                    "model": query.model,
                    "prompt": query.prompt,
                    "stream": False,
                    "options": {
                        "num_predict": query.max_tokens,
                        "temperature": query.temperature
                    }
                }
                
                response = await client.post(
                    f"{self.ollama_endpoint}/api/generate",
                    json=ollama_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    processing_time = time.time() - start_time
                    
                    return GatewayResponse(
                        success=True,
                        data=result,
                        provider="ollama",
                        model=query.model,
                        processing_time=processing_time,
                        tokens_used=len(result.get("response", "").split())
                    )
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ollama request failed: {response.text}"
                    )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error querying Ollama: {str(e)}"
            )
    
    async def _query_openai(self, query: LLMQuery, start_time: float) -> GatewayResponse:
        """Query OpenAI provider."""
        # Placeholder for OpenAI integration
        raise HTTPException(status_code=501, detail="OpenAI integration not implemented")
    
    async def _query_anthropic(self, query: LLMQuery, start_time: float) -> GatewayResponse:
        """Query Anthropic provider."""
        # Placeholder for Anthropic integration
        raise HTTPException(status_code=501, detail="Anthropic integration not implemented")
    
    async def _query_bedrock(self, query: LLMQuery, start_time: float) -> GatewayResponse:
        """Query AWS Bedrock provider."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                bedrock_request = {
                    "prompt": query.prompt,
                    "model": query.model,
                    "max_tokens": query.max_tokens,
                    "temperature": query.temperature
                }
                
                response = await client.post(
                    f"{self.bedrock_endpoint}/invoke",
                    json=bedrock_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    processing_time = time.time() - start_time
                    
                    return GatewayResponse(
                        success=True,
                        data=result,
                        provider="bedrock",
                        model=query.model,
                        processing_time=processing_time
                    )
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Bedrock request failed: {response.text}"
                    )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error querying Bedrock: {str(e)}"
            )
    
    async def get_providers(self) -> List[ProviderInfo]:
        """Get status of all configured providers."""
        providers = []
        
        # Check Ollama
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_endpoint}/api/tags")
                if response.status_code == 200:
                    models_data = response.json()
                    models = [model["name"] for model in models_data.get("models", [])]
                    providers.append(ProviderInfo(
                        name="ollama",
                        status="healthy",
                        models=models,
                        endpoint=self.ollama_endpoint,
                        features=["chat", "embeddings", "streaming"]
                    ))
                else:
                    providers.append(ProviderInfo(
                        name="ollama",
                        status="unhealthy",
                        models=[],
                        endpoint=self.ollama_endpoint,
                        features=[]
                    ))
        except Exception:
            providers.append(ProviderInfo(
                name="ollama",
                status="error",
                models=[],
                endpoint=self.ollama_endpoint,
                features=[]
            ))
        
        # Check other providers (simplified checks)
        if self.openai_api_key:
            providers.append(ProviderInfo(
                name="openai",
                status="configured",
                models=["gpt-3.5-turbo", "gpt-4"],
                endpoint="https://api.openai.com",
                features=["chat", "embeddings", "streaming"]
            ))
        
        if self.anthropic_api_key:
            providers.append(ProviderInfo(
                name="anthropic",
                status="configured",
                models=["claude-3-sonnet", "claude-3-haiku"],
                endpoint="https://api.anthropic.com",
                features=["chat"]
            ))
        
        # Check Bedrock
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.bedrock_endpoint}/health")
                if response.status_code == 200:
                    providers.append(ProviderInfo(
                        name="bedrock",
                        status="healthy",
                        models=["amazon.titan", "anthropic.claude"],
                        endpoint=self.bedrock_endpoint,
                        features=["chat"]
                    ))
                else:
                    providers.append(ProviderInfo(
                        name="bedrock",
                        status="unhealthy",
                        models=[],
                        endpoint=self.bedrock_endpoint,
                        features=[]
                    ))
        except Exception:
            providers.append(ProviderInfo(
                name="bedrock",
                status="error",
                models=[],
                endpoint=self.bedrock_endpoint,
                features=[]
            ))
        
        return providers

# Service configuration
SERVICE_NAME = "llm-gateway"
SERVICE_TITLE = "LLM Gateway"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5055

# Environment configuration
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://ollama:11434")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# ============================================================================
# APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title=SERVICE_TITLE,
    description="Unified LLM Gateway for secure, optimized access to all LLM providers including Ollama",
    version=SERVICE_VERSION,
    openapi_tags=[
        {"name": "queries", "description": "LLM query operations"},
        {"name": "chat", "description": "Conversational AI endpoints"},
        {"name": "providers", "description": "Provider management"},
        {"name": "cache", "description": "Cache management"},
        {"name": "metrics", "description": "Usage metrics and monitoring"},
        {"name": "health", "description": "Service health checks"}
    ]
)

# Initialize LLM Gateway components
provider_router = ProviderRouter()

# ============================================================================
# SIMPLIFIED METRICS AND CACHING
# ============================================================================

# Simple in-memory metrics
metrics_data = {
    "total_requests": 0,
    "requests_by_provider": {},
    "response_times": [],
    "cache_hits": 0,
    "cache_misses": 0,
    "errors": 0
}

def update_metrics(provider: str, response_time: float, cached: bool = False, error: bool = False):
    """Update simple metrics."""
    metrics_data["total_requests"] += 1
    metrics_data["requests_by_provider"][provider] = metrics_data["requests_by_provider"].get(provider, 0) + 1
    metrics_data["response_times"].append(response_time)
    if cached:
        metrics_data["cache_hits"] += 1
    else:
        metrics_data["cache_misses"] += 1
    if error:
        metrics_data["errors"] += 1

# ============================================================================
# HEALTH AND STATUS ENDPOINTS
# ============================================================================

@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": time.time(),
        "environment": ENVIRONMENT,
        "ollama_endpoint": OLLAMA_ENDPOINT,
        "providers_configured": len(await provider_router.get_providers())
    }

@app.get("/", tags=["health"])
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
            "embeddings": "/embeddings",
            "metrics": "/metrics",
            "cache": "/cache/clear"
        }
    }

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/providers", tags=["providers"])
async def get_providers():
    """Get available LLM providers and their status."""
    providers = await provider_router.get_providers()
    return {"providers": providers}

@app.post("/query", response_model=GatewayResponse, tags=["queries"])
async def query_llm(request: LLMQuery):
    """
    Submit a query to the LLM Gateway for processing by the specified provider.
    
    The gateway will route to the appropriate LLM provider and return structured response with metadata.
    """
    start_time = time.time()
    
    try:
        # Route to provider
        response = await provider_router.route_query(request)
        
        # Record metrics
        processing_time = time.time() - start_time
        update_metrics(request.provider, processing_time)
        increment_counter("successful_queries", {"provider": request.provider})
        record_histogram("query_duration", processing_time, {"provider": request.provider})
        
        return response
        
    except HTTPException:
        update_metrics(request.provider, time.time() - start_time, error=True)
        raise
    except Exception as e:
        update_metrics(request.provider, time.time() - start_time, error=True)
        increment_counter("query_errors", {"provider": request.provider})
        raise HTTPException(
            status_code=500,
            detail=f"Internal gateway error: {str(e)}"
        )

@app.post("/chat", response_model=GatewayResponse, tags=["chat"])
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
                        "temperature": request.temperature
                    }
                }
                
                response = await client.post(
                    f"{OLLAMA_ENDPOINT}/api/generate",
                    json=ollama_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    processing_time = time.time() - start_time
                    
                    update_metrics(request.provider, processing_time)
                    
                    return GatewayResponse(
                        success=True,
                        data={
                            "response": result.get("response", ""),
                            "model": request.model,
                            "done": result.get("done", True)
                        },
                        provider="ollama",
                        model=request.model,
                        processing_time=processing_time,
                        tokens_used=len(result.get("response", "").split())
                    )
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ollama chat failed: {response.text}"
                    )
                    
        except Exception as e:
            update_metrics(request.provider, time.time() - start_time, error=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error in chat with Ollama: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {request.provider}"
        )

@app.post("/stream", tags=["queries"])
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
                            "temperature": request.temperature
                        }
                    }
                    
                    async with client.stream(
                        "POST",
                        f"{OLLAMA_ENDPOINT}/api/generate",
                        json=ollama_request
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
            status_code=400,
            detail=f"Unsupported provider: {request.provider}"
        )

@app.post("/embeddings", tags=["queries"])
async def generate_embeddings(request: EmbeddingRequest):
    """Generate embeddings using the specified provider."""
    if request.provider == "ollama":
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                ollama_request = {
                    "model": request.model,
                    "prompt": request.text
                }
                
                response = await client.post(
                    f"{OLLAMA_ENDPOINT}/api/embeddings",
                    json=ollama_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "embeddings": result.get("embedding", []),
                        "model": request.model,
                        "provider": "ollama"
                    }
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ollama embeddings failed: {response.text}"
                    )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating embeddings: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {request.provider}"
        )

@app.get("/metrics", response_model=MetricsResponse, tags=["metrics"])
async def get_metrics():
    """Get usage metrics and statistics."""
    total_requests = metrics_data["total_requests"]
    response_times = metrics_data["response_times"]
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
    cache_total = metrics_data["cache_hits"] + metrics_data["cache_misses"]
    cache_hit_rate = metrics_data["cache_hits"] / cache_total if cache_total > 0 else 0.0
    error_rate = metrics_data["errors"] / total_requests if total_requests > 0 else 0.0
    
    return MetricsResponse(
        total_requests=total_requests,
        requests_by_provider=metrics_data["requests_by_provider"],
        average_response_time=avg_response_time,
        cache_hit_rate=cache_hit_rate,
        error_rate=error_rate
    )

@app.post("/cache/clear", tags=["cache"])
async def clear_cache(request: CacheRequest = None):
    """Clear cache entries."""
    if request and request.clear_all:
        # Clear all metrics (simple implementation)
        metrics_data["cache_hits"] = 0
        metrics_data["cache_misses"] = 0
        return {"message": "All cache cleared", "success": True}
    else:
        return {"message": "Cache clear requested", "success": True}

@app.get("/ollama/models", tags=["providers"])
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
                    detail="Failed to fetch Ollama models"
                )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching Ollama models: {str(e)}"
        )

if __name__ == "__main__":
    """Run the LLM Gateway service directly."""
    import uvicorn
    print(f"🚀 Starting {SERVICE_TITLE} Service...")
    print(f"🔗 Ollama endpoint: {OLLAMA_ENDPOINT}")
    print(f"🌐 Environment: {ENVIRONMENT}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )
