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
async def query_llm(request: LLMQuery, req: Request):
    """Execute a generic LLM query with intelligent provider routing and full ecosystem integration.

    Features:
    - Automatic provider selection based on content and requirements
    - Security-aware routing for sensitive content
    - Response caching for repeated queries
    - Rate limiting and cost optimization
    - Comprehensive metrics collection
    - Full ecosystem integration (interpreter, memory, prompts, etc.)
    """
    start_time = time.time()

    try:
        # Extract client information
        client_ip = req.client.host if req.client else "unknown"
        user_id = request.user_id or "anonymous"
        correlation_id = req.headers.get("X-Correlation-ID", f"gw-{int(time.time())}")

        # Rate limiting check
        if not await rate_limiter.check_rate_limit(user_id):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # Security filtering
        security_result = await security_filter.analyze_content(request.prompt + (request.context or ""))
        if security_result.is_sensitive and request.provider not in ["ollama", "bedrock"]:
            # Force secure provider for sensitive content
            request.provider = "ollama"  # Default to local Ollama for security

        # Cache check
        cache_key = cache_manager.generate_cache_key(request)
        cached_response = await cache_manager.get_cached_response(cache_key)
        if cached_response and not request.force_refresh:
            # Return cached response
            response_time = time.time() - start_time
            await metrics_collector.record_request("cache_hit", request.provider, response_time, 0)

            # Store interaction in memory agent
            await service_integrations.integrate_with_memory_agent(
                "store_interaction",
                user_id=user_id,
                prompt=request.prompt,
                response=cached_response,
                provider="cache",
                tokens_used=0,
                processing_time=response_time
            )

            return GatewayResponse(
                response=cached_response,
                provider="cache",
                tokens_used=0,
                processing_time=response_time,
                cached=True,
                correlation_id=correlation_id
            )

        # Enhanced processing with service integrations
        if req.headers.get("X-Use-Enhanced-Processing", "false").lower() == "true":
            enhanced_response = await service_integrations.enhanced_llm_processing(request)
            return enhanced_response

        # Standard provider routing and execution
        provider_response = await provider_router.route_and_execute(request)

        # Cache successful responses
        if provider_response.success and len(provider_response.response) > 100:
            await cache_manager.cache_response(cache_key, provider_response.response, ttl=3600)

        # Store interaction in memory agent
        await service_integrations.integrate_with_memory_agent(
            "store_interaction",
            user_id=user_id,
            prompt=request.prompt,
            response=provider_response.response,
            provider=provider_response.provider,
            tokens_used=provider_response.tokens_used,
            processing_time=time.time() - start_time
        )

        # Store in document store if requested
        if req.headers.get("X-Store-Interaction", "false").lower() == "true":
            await service_integrations.integrate_with_doc_store(
                "store",
                title=f"LLM Query: {request.prompt[:50]}...",
                content=f"Prompt: {request.prompt}\n\nResponse: {provider_response.response}",
                provider=provider_response.provider,
                tokens_used=provider_response.tokens_used,
                processing_time=time.time() - start_time
            )

        # Metrics collection
        response_time = time.time() - start_time
        await metrics_collector.record_request(
            "llm_query",
            provider_response.provider,
            response_time,
            provider_response.tokens_used,
            cost=provider_response.cost
        )

        # Logging
        fire_and_forget(
            "llm_gateway_query_completed",
            f"LLM query completed: {request.provider} -> {len(provider_response.response)} chars",
            ServiceNames.LLM_GATEWAY,
            {
                "correlation_id": correlation_id,
                "user_id": user_id,
                "provider": provider_response.provider,
                "tokens_used": provider_response.tokens_used,
                "processing_time": response_time,
                "cached": False,
                "enhanced_processing": False
            }
        )

        return GatewayResponse(
            response=provider_response.response,
            provider=provider_response.provider,
            tokens_used=provider_response.tokens_used,
            processing_time=response_time,
            cost=provider_response.cost,
            correlation_id=correlation_id
        )

    except Exception as e:
        response_time = time.time() - start_time
        await metrics_collector.record_error("llm_query", str(e), response_time)

        return create_error_response(
            f"LLM query failed: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={
                "processing_time": response_time,
                "correlation_id": req.headers.get("X-Correlation-ID")
            }
        )


@app.post("/chat", response_model=GatewayResponse)
async def chat_with_llm(request: LLMQuery, req: Request):
    """Conversational LLM interaction with conversation memory.

    Supports multi-turn conversations with context preservation and
    intelligent conversation flow management.
    """
    # Implementation similar to /query but with conversation context
    # For now, delegate to the query endpoint
    return await query_llm(request, req)


@app.post("/embeddings")
async def generate_embeddings(request: EmbeddingRequest, req: Request):
    """Generate embeddings for text using available embedding models."""
    try:
        # Use provider router to get embeddings
        embeddings = await provider_router.generate_embeddings(
            request.text,
            request.model or "text-embedding-ada-002",
            request.provider or "openai"
        )

        await metrics_collector.record_request("embeddings", request.provider, 0.1, 0)

        return create_success_response(
            "Embeddings generated successfully",
            {
                "embeddings": embeddings,
                "model": request.model,
                "provider": request.provider,
                "dimensions": len(embeddings) if isinstance(embeddings, list) else 0
            }
        )

    except Exception as e:
        return create_error_response(
            f"Embedding generation failed: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.post("/stream")
async def stream_llm_response(request: LLMQuery, req: Request):
    """Stream LLM responses for real-time interaction."""
    async def generate_stream():
        try:
            async for chunk in provider_router.stream_response(request):
                yield f"data: {json.dumps(chunk)}\n\n"

            # Final completion marker
            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@app.get("/providers")
async def list_providers():
    """List available LLM providers and their current status."""
    try:
        providers = await provider_router.get_available_providers()

        return create_success_response(
            "Providers retrieved successfully",
            {"providers": providers}
        )

    except Exception as e:
        return create_error_response(
            f"Failed to retrieve providers: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get LLM usage metrics and performance statistics."""
    try:
        metrics = await metrics_collector.get_metrics_summary()

        return MetricsResponse(
            total_requests=metrics.get("total_requests", 0),
            requests_by_provider=metrics.get("requests_by_provider", {}),
            total_tokens_used=metrics.get("total_tokens_used", 0),
            total_cost=metrics.get("total_cost", 0.0),
            average_response_time=metrics.get("average_response_time", 0.0),
            cache_hit_rate=metrics.get("cache_hit_rate", 0.0),
            error_rate=metrics.get("error_rate", 0.0),
            uptime_percentage=metrics.get("uptime_percentage", 100.0)
        )

    except Exception as e:
        return create_error_response(
            f"Failed to retrieve metrics: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.post("/cache/clear")
async def clear_cache(request: CacheRequest):
    """Clear LLM response cache."""
    try:
        if request.pattern:
            cleared_count = await cache_manager.clear_pattern(request.pattern)
        else:
            cleared_count = await cache_manager.clear_all()

        return create_success_response(
            f"Cache cleared successfully: {cleared_count} entries removed",
            {"entries_cleared": cleared_count}
        )

    except Exception as e:
        return create_error_response(
            f"Cache clear failed: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check including LLM provider status and service integrations."""
    try:
        # Basic service health
        health_status = {
            "service": "healthy",
            "version": SERVICE_VERSION,
            "uptime": "unknown"  # Could be enhanced with actual uptime tracking
        }

        # Provider health checks
        provider_health = await provider_router.check_provider_health()

        # Cache health
        cache_health = await cache_manager.get_health_status()

        # Rate limiter status
        rate_limiter_status = await rate_limiter.get_status()

        # Service integration health
        service_health = await service_integrations.get_service_health_status()

        detailed_health = {
            **health_status,
            "providers": provider_health,
            "cache": cache_health,
            "rate_limiter": rate_limiter_status,
            "service_integrations": service_health,
            "timestamp": time.time()
        }

        return create_success_response(
            "Detailed health check completed",
            detailed_health
        )

    except Exception as e:
        return create_error_response(
            f"Detailed health check failed: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


# ============================================================================
# ENHANCED ECOSYSTEM INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/enhanced-query")
async def enhanced_query(request: LLMQuery, req: Request):
    """Enhanced LLM query with full ecosystem integration.

    This endpoint leverages:
    - Interpreter service for query understanding
    - Prompt Store for optimized prompts
    - Memory Agent for conversation context
    - Secure Analyzer for security analysis
    - Document Store for context retrieval
    """
    start_time = time.time()

    try:
        user_id = request.user_id or "anonymous"
        correlation_id = req.headers.get("X-Correlation-ID", f"enhanced-{int(time.time())}")

        # Use enhanced processing
        enhanced_response = await service_integrations.enhanced_llm_processing(request)

        response_time = time.time() - start_time

        # Record metrics
        await metrics_collector.record_request(
            "enhanced_query",
            enhanced_response.provider,
            response_time,
            enhanced_response.tokens_used or 0,
            cost=enhanced_response.cost
        )

        fire_and_forget(
            "llm_gateway_enhanced_query_completed",
            f"Enhanced query completed with full ecosystem integration",
            ServiceNames.LLM_GATEWAY,
            {
                "correlation_id": correlation_id,
                "user_id": user_id,
                "processing_time": response_time,
                "services_used": ["interpreter", "prompt_store", "memory_agent", "secure_analyzer"]
            }
        )

        return enhanced_response

    except Exception as e:
        response_time = time.time() - start_time
        await metrics_collector.record_error("enhanced_query", str(e), response_time)

        return create_error_response(
            f"Enhanced query failed: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.post("/workflow-query")
async def workflow_query(request: LLMQuery, req: Request):
    """Execute LLM query as part of a larger workflow.

    Integrates with Orchestrator service to execute complex multi-step workflows
    that involve multiple services and LLM interactions.
    """
    try:
        user_id = request.user_id or "anonymous"
        workflow_type = req.headers.get("X-Workflow-Type", "llm_processing")

        # Execute workflow through orchestrator
        workflow_result = await service_integrations.integrate_with_orchestrator(
            "execute_workflow",
            workflow_type=workflow_type,
            parameters={
                "llm_query": request.dict(),
                "user_id": user_id,
                "correlation_id": req.headers.get("X-Correlation-ID")
            }
        )

        return create_success_response(
            "Workflow executed successfully",
            workflow_result
        )

    except Exception as e:
        return create_error_response(
            f"Workflow execution failed: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.post("/contextual-query")
async def contextual_query(request: LLMQuery, req: Request):
    """Execute LLM query with rich contextual information.

    Retrieves relevant context from:
    - Memory Agent (conversation history)
    - Document Store (relevant documents)
    - Prompt Store (optimized prompts)
    """
    start_time = time.time()

    try:
        user_id = request.user_id or "anonymous"

        # Get conversation context
        conversation_context = await service_integrations.integrate_with_memory_agent(
            "retrieve_context",
            user_id=user_id
        )

        # Search for relevant documents
        if request.context and "search_terms" in request.context:
            doc_results = await service_integrations.integrate_with_doc_store(
                "search",
                query=request.context["search_terms"]
            )
        else:
            doc_results = {"documents": []}

        # Get optimized prompt
        optimized_prompt = await service_integrations.integrate_with_prompt_store(
            "get_optimized",
            task_type=request.context.get("task_type", "general") if request.context else "general",
            context=request.context
        )

        # Enhance query with context
        enhanced_prompt = f"""
{optimized_prompt.get('content', request.prompt)}

Additional Context:
- Conversation History: {conversation_context.get('summary', 'None available')}
- Relevant Documents: {len(doc_results.get('documents', []))} found
- User Context: {request.context or 'None provided'}

Original Query: {request.prompt}
        """.strip()

        enhanced_request = LLMQuery(
            prompt=enhanced_prompt,
            provider=request.provider,
            model=request.model,
            context={
                **(request.context or {}),
                "conversation_context": conversation_context,
                "document_context": doc_results,
                "optimized_prompt": optimized_prompt
            },
            user_id=user_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        # Execute enhanced query
        return await query_llm(enhanced_request, req)

    except Exception as e:
        response_time = time.time() - start_time
        await metrics_collector.record_error("contextual_query", str(e), response_time)

        return create_error_response(
            f"Contextual query failed: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.get("/services/status")
async def get_services_status():
    """Get comprehensive status of all integrated services."""
    try:
        service_health = await service_integrations.get_service_health_status()

        return create_success_response(
            "Service status retrieved successfully",
            service_health
        )

    except Exception as e:
        return create_error_response(
            f"Failed to get service status: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.post("/integrations/{service_name}/{operation}")
async def service_integration_endpoint(service_name: str, operation: str, data: Dict[str, Any], req: Request):
    """Generic endpoint for service integrations.

    Allows direct access to integrated services through the LLM Gateway.
    """
    try:
        integration_method = f"integrate_with_{service_name}"

        if not hasattr(service_integrations, integration_method):
            return create_error_response(
                f"Integration with {service_name} not available",
                error_code=ErrorCodes.NOT_FOUND
            )

        integration_func = getattr(service_integrations, integration_method)
        result = await integration_func(operation, **data)

        return create_success_response(
            f"Integration with {service_name} completed",
            result
        )

    except Exception as e:
        return create_error_response(
            f"Service integration failed: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@app.get("/capabilities")
async def get_capabilities():
    """Get LLM Gateway capabilities and supported features."""
    try:
        capabilities = {
            "llm_providers": ["ollama", "openai", "anthropic", "bedrock", "grok"],
            "core_features": [
                "intelligent_routing",
                "security_filtering",
                "response_caching",
                "rate_limiting",
                "metrics_collection"
            ],
            "service_integrations": [
                "doc_store",
                "prompt_store",
                "memory_agent",
                "interpreter",
                "orchestrator",
                "summarizer_hub",
                "secure_analyzer",
                "code_analyzer",
                "architecture_digitizer",
                "analysis_service"
            ],
            "enhanced_features": [
                "enhanced_processing",
                "workflow_execution",
                "contextual_queries",
                "conversation_memory",
                "document_integration",
                "prompt_optimization"
            ],
            "api_endpoints": [
                "/query",
                "/chat",
                "/embeddings",
                "/stream",
                "/enhanced-query",
                "/workflow-query",
                "/contextual-query",
                "/providers",
                "/metrics",
                "/cache/clear",
                "/services/status",
                "/integrations/{service}/{operation}",
                "/capabilities"
            ],
            "supported_headers": [
                "X-Correlation-ID",
                "X-Use-Enhanced-Processing",
                "X-Store-Interaction",
                "X-Workflow-Type"
            ]
        }

        return create_success_response(
            "LLM Gateway capabilities retrieved",
            capabilities
        )

    except Exception as e:
        return create_error_response(
            f"Failed to get capabilities: {str(e)}",
            error_code=ErrorCodes.INTERNAL_ERROR
        )


if __name__ == "__main__":
    """Run the LLM Gateway service directly."""
    import uvicorn
    print("🚀 Starting LLM Gateway Service...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )
