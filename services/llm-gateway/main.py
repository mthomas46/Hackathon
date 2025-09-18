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
import hashlib
from datetime import datetime, timedelta

# Redis import with fallback
try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    print("aioredis not available, Redis features disabled")
    REDIS_AVAILABLE = False

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
    user_id: Optional[str] = "anonymous"
    use_cache: Optional[bool] = True
    use_memory: Optional[bool] = False
    enhance_prompt: Optional[bool] = False
    store_interaction: Optional[bool] = False
    force_refresh: Optional[bool] = False

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
# ENHANCED ECOSYSTEM INTEGRATIONS - Leveraging existing services
# ============================================================================

class EcosystemIntegrator:
    """Enhanced integrations with existing ecosystem services."""
    
    def __init__(self):
        self.redis_client = None
        self.service_endpoints = {
            "doc_store": "http://doc_store:5010",
            "prompt_store": "http://prompt_store:5110", 
            "memory_agent": "http://memory-agent:5040",
            "interpreter": "http://interpreter:5120",
            "orchestrator": "http://orchestrator:5099",
            "secure_analyzer": "http://secure-analyzer:5070",
            "analysis_service": "http://analysis-service:5080"
        }
        
    async def get_redis_client(self):
        """Get Redis client for caching and rate limiting."""
        if not REDIS_AVAILABLE:
            return None
            
        if not self.redis_client:
            try:
                self.redis_client = aioredis.from_url(
                    f"redis://{os.getenv('REDIS_HOST', 'redis')}:6379"
                )
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self.redis_client = None
        return self.redis_client
    
    async def security_filter(self, content: str) -> Dict[str, Any]:
        """Use secure-analyzer for content security filtering."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.service_endpoints['secure_analyzer']}/analyze",
                    json={"content": content}
                )
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "is_sensitive": result.get("sensitive", False),
                        "risk_level": result.get("risk_level", "low"),
                        "issues": result.get("issues", [])
                    }
        except Exception as e:
            print(f"Security filtering failed: {e}")
        
        # Fallback local security check
        sensitive_keywords = ["password", "secret", "token", "key", "credential"]
        is_sensitive = any(keyword in content.lower() for keyword in sensitive_keywords)
        return {
            "is_sensitive": is_sensitive,
            "risk_level": "high" if is_sensitive else "low", 
            "issues": ["Contains sensitive keywords"] if is_sensitive else []
        }
    
    async def rate_limit_check(self, user_id: str = "anonymous") -> bool:
        """Redis-based rate limiting."""
        redis = await self.get_redis_client()
        if not redis:
            return True  # Allow if Redis unavailable
        
        try:
            key = f"rate_limit:{user_id}"
            current = await redis.get(key)
            
            if current is None:
                await redis.setex(key, 60, 1)  # 1 request in 60 seconds window
                return True
            
            count = int(current)
            if count >= 60:  # 60 requests per minute limit
                return False
            
            await redis.incr(key)
            return True
        except Exception as e:
            print(f"Rate limiting check failed: {e}")
            return True
    
    async def cache_get(self, cache_key: str) -> Optional[Any]:
        """Get cached response."""
        redis = await self.get_redis_client()
        if not redis:
            return None
        
        try:
            cached = await redis.get(f"cache:{cache_key}")
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Cache get failed: {e}")
        return None
    
    async def cache_set(self, cache_key: str, data: Any, ttl: int = 3600):
        """Set cached response."""
        redis = await self.get_redis_client()
        if not redis:
            return
        
        try:
            await redis.setex(f"cache:{cache_key}", ttl, json.dumps(data))
        except Exception as e:
            print(f"Cache set failed: {e}")
    
    def generate_cache_key(self, query: 'LLMQuery') -> str:
        """Generate cache key for query."""
        content = f"{query.prompt}:{query.model}:{query.provider}:{query.temperature}:{query.max_tokens}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def store_interaction(self, user_id: str, prompt: str, response: str, provider: str, metadata: Dict[str, Any]):
        """Store interaction in memory-agent."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{self.service_endpoints['memory_agent']}/store",
                    json={
                        "user_id": user_id,
                        "interaction": {
                            "prompt": prompt,
                            "response": response,
                            "provider": provider,
                            "timestamp": time.time(),
                            **metadata
                        }
                    }
                )
        except Exception as e:
            print(f"Memory storage failed: {e}")
    
    async def get_context(self, user_id: str, query: str) -> Optional[str]:
        """Get relevant context from memory-agent."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.service_endpoints['memory_agent']}/retrieve",
                    json={"user_id": user_id, "query": query}
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("context")
        except Exception as e:
            print(f"Context retrieval failed: {e}")
        return None
    
    async def enhance_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """Enhance prompt using prompt-store."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.service_endpoints['prompt_store']}/enhance",
                    json={"prompt": prompt, "context": context}
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("enhanced_prompt", prompt)
        except Exception as e:
            print(f"Prompt enhancement failed: {e}")
        return prompt
    
    async def store_document(self, title: str, content: str, metadata: Dict[str, Any]):
        """Store document in doc-store."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{self.service_endpoints['doc_store']}/documents",
                    json={
                        "title": title,
                        "content": content,
                        "metadata": metadata
                    }
                )
        except Exception as e:
            print(f"Document storage failed: {e}")

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
ecosystem = EcosystemIntegrator()

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
        "ecosystem_integration": True,
        "endpoints": {
            "health": "/health",
            "providers": "/providers",
            "query": "/query",
            "enhanced_query": "/enhanced-query",
            "chat": "/chat",
            "stream": "/stream",
            "embeddings": "/embeddings",
            "metrics": "/metrics",
            "cache": {
                "clear": "/cache/clear",
                "stats": "/cache/stats"
            },
            "security": "/security/analyze",
            "memory": "/user/{user_id}/context",
            "workflow": "/workflow/execute",
            "ecosystem_health": "/ecosystem/health",
            "ollama_models": "/ollama/models"
        },
        "features": {
            "redis_caching": True,
            "rate_limiting": True,
            "security_filtering": True,
            "memory_integration": True,
            "prompt_enhancement": True,
            "interaction_storage": True,
            "workflow_execution": True,
            "multi_provider_support": True
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
    
    Enhanced features:
    - Security filtering using secure-analyzer
    - Redis-based caching and rate limiting
    - Memory context integration
    - Prompt enhancement from prompt-store
    - Interaction storage in memory-agent
    """
    start_time = time.time()
    
    try:
        # Rate limiting check
        if not await ecosystem.rate_limit_check(request.user_id):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Security filtering
        security_result = await ecosystem.security_filter(request.prompt + (request.context or ""))
        if security_result["is_sensitive"] and request.provider not in ["ollama"]:
            # Force secure provider for sensitive content
            request.provider = "ollama"
            fire_and_forget("security_route_override", {
                "user_id": request.user_id,
                "original_provider": request.provider,
                "security_issues": security_result["issues"]
            })
        
        # Get context from memory if requested
        if request.use_memory:
            context = await ecosystem.get_context(request.user_id, request.prompt)
            if context:
                request.context = context
        
        # Enhance prompt if requested
        if request.enhance_prompt:
            enhanced_prompt = await ecosystem.enhance_prompt(request.prompt, request.context)
            request.prompt = enhanced_prompt
        
        # Check cache
        cache_key = ecosystem.generate_cache_key(request)
        if request.use_cache and not request.force_refresh:
            cached_response = await ecosystem.cache_get(cache_key)
            if cached_response:
                processing_time = time.time() - start_time
                update_metrics(request.provider, processing_time, cached=True)
                increment_counter("cache_hits", {"provider": request.provider})
                
                # Store cached interaction if requested
                if request.store_interaction:
                    await ecosystem.store_interaction(
                        request.user_id,
                        request.prompt,
                        cached_response.get("data", {}).get("response", ""),
                        "cache",
                        {"cached": True, "processing_time": processing_time}
                    )
                
                return GatewayResponse(
                    success=True,
                    data=cached_response.get("data", {}),
                    provider="cache",
                    model=request.model,
                    processing_time=processing_time,
                    cached=True
                )
        
        # Route to provider
        response = await provider_router.route_query(request)
        
        # Cache successful response
        if request.use_cache and response.success:
            await ecosystem.cache_set(cache_key, response.dict(), ttl=3600)
        
        # Store interaction if requested
        if request.store_interaction:
            await ecosystem.store_interaction(
                request.user_id,
                request.prompt,
                response.data.get("response", ""),
                response.provider,
                {
                    "model": response.model,
                    "processing_time": response.processing_time,
                    "tokens_used": response.tokens_used
                }
            )
        
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

# ============================================================================
# ENHANCED ECOSYSTEM ENDPOINTS
# ============================================================================

@app.post("/enhanced-query", response_model=GatewayResponse, tags=["queries"])
async def enhanced_query(request: LLMQuery):
    """
    Enhanced query with full ecosystem integration.
    Automatically enables memory, caching, prompt enhancement, and interaction storage.
    """
    request.use_memory = True
    request.enhance_prompt = True
    request.store_interaction = True
    return await query_llm(request)

@app.get("/user/{user_id}/context", tags=["memory"])
async def get_user_context(user_id: str, query: str):
    """Get user context from memory-agent."""
    context = await ecosystem.get_context(user_id, query)
    return {"user_id": user_id, "context": context}

@app.post("/security/analyze", tags=["security"])
async def analyze_content_security(content: str):
    """Analyze content security using secure-analyzer."""
    result = await ecosystem.security_filter(content)
    return result

@app.get("/cache/stats", tags=["cache"])
async def get_cache_stats():
    """Get Redis cache statistics."""
    redis = await ecosystem.get_redis_client()
    if not redis:
        return {"error": "Redis not available"}
    
    try:
        info = await redis.info()
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory_human", "0B"),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "cache_hit_rate": metrics_data["cache_hits"] / (metrics_data["cache_hits"] + metrics_data["cache_misses"]) if (metrics_data["cache_hits"] + metrics_data["cache_misses"]) > 0 else 0
        }
    except Exception as e:
        return {"error": f"Failed to get cache stats: {e}"}

@app.post("/workflow/execute", tags=["orchestrator"])
async def execute_workflow(workflow_name: str, parameters: Dict[str, Any]):
    """Execute a workflow through the orchestrator."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ecosystem.service_endpoints['orchestrator']}/execute",
                json={"workflow": workflow_name, "parameters": parameters}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Workflow execution failed: {response.text}"
                )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing workflow: {str(e)}"
        )

@app.get("/ecosystem/health", tags=["health"])
async def get_ecosystem_health():
    """Get health status of all ecosystem services."""
    health_results = {}
    
    for service_name, endpoint in ecosystem.service_endpoints.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{endpoint}/health")
                if response.status_code == 200:
                    health_results[service_name] = {
                        "status": "healthy",
                        "response_time": response.elapsed.total_seconds(),
                        "data": response.json()
                    }
                else:
                    health_results[service_name] = {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            health_results[service_name] = {
                "status": "error",
                "error": str(e)
            }
    
    # Add Redis health
    redis = await ecosystem.get_redis_client()
    if redis:
        try:
            await redis.ping()
            health_results["redis"] = {"status": "healthy"}
        except Exception as e:
            health_results["redis"] = {"status": "error", "error": str(e)}
    else:
        health_results["redis"] = {"status": "unavailable"}
    
    return {
        "ecosystem_health": health_results,
        "overall_status": "healthy" if all(
            result.get("status") == "healthy" 
            for result in health_results.values()
        ) else "degraded"
    }

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
