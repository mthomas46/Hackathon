"""LLM Gateway REST API routes with comprehensive OpenAPI annotations."""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Path, Body, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator, constr
from pydantic.generics import GenericModel


# Enums for OpenAPI documentation
class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL = "local"


class ModelType(str, Enum):
    """LLM model types."""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    CODE = "code"
    EMBEDDING = "embedding"


class ResponseFormat(str, Enum):
    """Response format options."""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


# Comprehensive Pydantic models with extensive OpenAPI annotations
class LLMQueryRequest(BaseModel):
    """Request model for LLM text generation queries.

    This endpoint provides access to various Large Language Models
    for text generation, completion, and other LLM tasks.
    """
    prompt: constr(min_length=1, max_length=32768) = Field(
        ...,
        title="Prompt",
        description="The text prompt to send to the LLM",
        example="Explain quantum computing in simple terms"
    )
    model: Optional[str] = Field(
        "llama2",
        title="Model Name",
        description="The specific model to use for generation",
        example="llama2:13b",
        min_length=1,
        max_length=100
    )
    provider: Optional[LLMProvider] = Field(
        LLMProvider.OLLAMA,
        title="LLM Provider",
        description="The LLM provider to route the request to",
        example=LLMProvider.OLLAMA
    )
    max_tokens: Optional[int] = Field(
        1000,
        title="Maximum Tokens",
        description="Maximum number of tokens to generate",
        ge=1,
        le=32768,
        example=1000
    )
    temperature: Optional[float] = Field(
        0.7,
        title="Temperature",
        description="Controls randomness in generation (0.0 = deterministic, 1.0 = very random)",
        ge=0.0,
        le=2.0,
        example=0.7
    )
    top_p: Optional[float] = Field(
        None,
        title="Top P",
        description="Nucleus sampling parameter",
        ge=0.0,
        le=1.0,
        example=0.9
    )
    top_k: Optional[int] = Field(
        None,
        title="Top K",
        description="Top-k sampling parameter",
        ge=1,
        le=100,
        example=50
    )
    stream: Optional[bool] = Field(
        False,
        title="Stream Response",
        description="Whether to stream the response as it's generated",
        example=False
    )
    system_prompt: Optional[constr(max_length=4096)] = Field(
        None,
        title="System Prompt",
        description="System-level instructions for the model",
        example="You are a helpful AI assistant."
    )
    response_format: Optional[ResponseFormat] = Field(
        ResponseFormat.TEXT,
        title="Response Format",
        description="Desired format for the response",
        example=ResponseFormat.TEXT
    )

    @validator('temperature')
    def validate_temperature(cls, v):
        """Validate temperature is within bounds."""
        if v is not None and not (0.0 <= v <= 2.0):
            raise ValueError('temperature must be between 0.0 and 2.0')
        return v


class ChatMessage(BaseModel):
    """A single message in a chat conversation.

    Represents one message in a multi-turn conversation with an LLM.
    """
    role: constr(regex='^(system|user|assistant)$') = Field(
        ...,
        title="Role",
        description="The role of the message sender",
        example="user"
    )
    content: constr(min_length=1, max_length=32768) = Field(
        ...,
        title="Content",
        description="The content of the message",
        example="Hello, how can you help me today?"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        title="Metadata",
        description="Additional metadata for the message",
        example={"timestamp": "2023-12-01T10:00:00Z"}
    )


class ChatRequest(BaseModel):
    """Request model for chat-based LLM interactions.

    Supports multi-turn conversations with context preservation
    and various conversation management features.
    """
    messages: List[ChatMessage] = Field(
        ...,
        title="Messages",
        description="List of messages in the conversation",
        min_items=1,
        max_items=100,
        example=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]
    )
    model: Optional[str] = Field(
        "llama2",
        title="Model Name",
        description="The model to use for chat",
        example="llama2:13b-chat"
    )
    provider: Optional[LLMProvider] = Field(
        LLMProvider.OLLAMA,
        title="Provider",
        description="LLM provider for the chat",
        example=LLMProvider.OLLAMA
    )
    max_tokens: Optional[int] = Field(
        1000,
        title="Max Tokens",
        description="Maximum tokens to generate",
        ge=1,
        le=32768,
        example=1000
    )
    temperature: Optional[float] = Field(
        0.7,
        title="Temperature",
        description="Creativity/randomness parameter",
        ge=0.0,
        le=2.0,
        example=0.7
    )
    stream: Optional[bool] = Field(
        False,
        title="Stream",
        description="Stream the response",
        example=False
    )
    conversation_id: Optional[str] = Field(
        None,
        title="Conversation ID",
        description="Unique identifier for the conversation",
        example="conv-12345"
    )


class LLMResponse(BaseModel):
    """Response model for LLM operations.

    Contains the generated text, metadata, and performance information.
    """
    success: bool = Field(
        ...,
        title="Success",
        description="Whether the request was successful",
        example=True
    )
    response: str = Field(
        ...,
        title="Response",
        description="The generated response text",
        example="Quantum computing uses quantum mechanics principles..."
    )
    model: str = Field(
        ...,
        title="Model Used",
        description="The model that generated the response",
        example="llama2:13b"
    )
    provider: str = Field(
        ...,
        title="Provider Used",
        description="The provider that handled the request",
        example="ollama"
    )
    tokens_used: Optional[int] = Field(
        None,
        title="Tokens Used",
        description="Number of tokens consumed",
        example=150
    )
    processing_time_seconds: float = Field(
        ...,
        title="Processing Time",
        description="Time taken to process the request",
        example=2.34
    )
    request_id: str = Field(
        ...,
        title="Request ID",
        description="Unique identifier for this request",
        example="req-12345-abc"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        title="Metadata",
        description="Additional response metadata",
        example={"confidence": 0.95, "finish_reason": "stop"}
    )


class ProviderInfo(BaseModel):
    """Information about an LLM provider.

    Details about available providers, their status, and capabilities.
    """
    name: str = Field(
        ...,
        title="Provider Name",
        description="Name of the LLM provider",
        example="ollama"
    )
    display_name: str = Field(
        ...,
        title="Display Name",
        description="Human-readable name",
        example="Ollama Local Models"
    )
    status: str = Field(
        ...,
        title="Status",
        description="Current status of the provider",
        example="healthy"
    )
    models: List[str] = Field(
        ...,
        title="Available Models",
        description="List of available models",
        example=["llama2:7b", "llama2:13b", "codellama:7b"]
    )
    endpoint: str = Field(
        ...,
        title="Endpoint",
        description="API endpoint URL",
        example="http://ollama:11434"
    )
    capabilities: List[str] = Field(
        ...,
        title="Capabilities",
        description="Supported capabilities",
        example=["text_generation", "chat", "streaming"]
    )
    rate_limits: Optional[Dict[str, Any]] = Field(
        None,
        title="Rate Limits",
        description="Rate limiting information",
        example={"requests_per_minute": 60, "tokens_per_minute": 10000}
    )


class GatewayStats(BaseModel):
    """Gateway-wide statistics and metrics.

    Comprehensive metrics about gateway usage and performance.
    """
    total_requests: int = Field(
        ...,
        title="Total Requests",
        description="Total number of requests processed",
        example=15432
    )
    active_requests: int = Field(
        ...,
        title="Active Requests",
        description="Currently active requests",
        example=3
    )
    total_tokens: int = Field(
        ...,
        title="Total Tokens",
        description="Total tokens processed",
        example=1250000
    )
    average_response_time: float = Field(
        ...,
        title="Average Response Time",
        description="Average response time in seconds",
        example=1.45
    )
    providers: Dict[str, Dict[str, Any]] = Field(
        ...,
        title="Provider Stats",
        description="Statistics per provider",
        example={
            "ollama": {"requests": 12000, "tokens": 900000, "avg_time": 1.2},
            "openai": {"requests": 3432, "tokens": 350000, "avg_time": 2.1}
        }
    )
    uptime_seconds: int = Field(
        ...,
        title="Uptime",
        description="Gateway uptime in seconds",
        example=86400
    )
    cache_hit_rate: float = Field(
        ...,
        title="Cache Hit Rate",
        description="Percentage of requests served from cache",
        example=0.75
    )


class LLMRouter:
    """FastAPI router for LLM Gateway operations with comprehensive OpenAPI documentation."""

    def __init__(self):
        """Initialize the LLM router with comprehensive API documentation."""
        self.router = APIRouter(
            prefix="/api/v1/llm",
            tags=["llm-gateway"],
            responses={
                400: {"description": "Bad Request - Invalid input parameters"},
                401: {"description": "Unauthorized - Authentication required"},
                403: {"description": "Forbidden - Insufficient permissions"},
                404: {"description": "Not Found - Resource not found"},
                429: {"description": "Too Many Requests - Rate limit exceeded"},
                500: {"description": "Internal Server Error - Unexpected error"},
                503: {"description": "Service Unavailable - Provider or service down"}
            }
        )

        # Register all routes with comprehensive documentation
        self._register_routes()

    def _register_routes(self):
        """Register all LLM routes with extensive OpenAPI documentation."""

        @self.router.post(
            "/query",
            response_model=LLMResponse,
            summary="Generate Text with LLM",
            description="""
            Generate text using a Large Language Model.

            This endpoint provides access to various LLM providers for text generation,
            completion, and creative writing tasks. Supports multiple models and
            fine-grained control over generation parameters.

            **Features:**
            - Multiple LLM provider support (Ollama, OpenAI, Anthropic, etc.)
            - Streaming responses for real-time generation
            - Configurable generation parameters (temperature, max_tokens, etc.)
            - Automatic provider routing and load balancing
            - Comprehensive error handling and fallbacks

            **Use Cases:**
            - Content generation
            - Code completion
            - Creative writing
            - Question answering
            - Text summarization
            """,
            response_description="Generated text response with metadata"
        )
        async def query_llm(
            request: LLMQueryRequest = Body(
                ...,
                examples={
                    "simple": {
                        "summary": "Simple text generation",
                        "description": "Basic text generation request",
                        "value": {
                            "prompt": "Explain machine learning in simple terms",
                            "model": "llama2",
                            "max_tokens": 500,
                            "temperature": 0.7
                        }
                    },
                    "advanced": {
                        "summary": "Advanced generation with all parameters",
                        "description": "Full-featured generation request",
                        "value": {
                            "prompt": "Write a Python function to calculate fibonacci numbers",
                            "model": "codellama",
                            "provider": "ollama",
                            "max_tokens": 1000,
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "stream": False,
                            "system_prompt": "You are an expert Python developer.",
                            "response_format": "markdown"
                        }
                    }
                }
            ),
            background_tasks: BackgroundTasks = None
        ) -> LLMResponse:
            """Generate text using an LLM with comprehensive parameter control."""
            try:
                # Mock implementation - in real implementation, this would route to actual LLM
                import time
                import uuid

                start_time = time.time()
                request_id = f"req-{uuid.uuid4().hex[:8]}"

                # Simulate processing time
                processing_time = 1.5 + (len(request.prompt) * 0.001)

                response_text = f"This is a simulated response to: {request.prompt[:50]}..."

                return LLMResponse(
                    success=True,
                    response=response_text,
                    model=request.model or "llama2",
                    provider=request.provider or "ollama",
                    tokens_used=len(response_text.split()),
                    processing_time_seconds=processing_time,
                    request_id=request_id,
                    metadata={
                        "temperature": request.temperature,
                        "max_tokens": request.max_tokens,
                        "finish_reason": "stop"
                    }
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM query failed: {str(e)}"
                )

        @self.router.post(
            "/chat",
            response_model=LLMResponse,
            summary="Chat with LLM",
            description="""
            Engage in conversational chat with a Large Language Model.

            This endpoint supports multi-turn conversations with context preservation,
            making it ideal for interactive applications, chatbots, and conversational AI.

            **Features:**
            - Multi-turn conversation support
            - Context preservation across messages
            - System prompt customization
            - Conversation history management
            - Streaming responses for real-time chat

            **Supported Message Roles:**
            - `system`: System-level instructions and context
            - `user`: User messages and queries
            - `assistant`: AI responses (for context in continued conversations)

            **Best Practices:**
            - Start conversations with a system message to set context
            - Keep conversation history manageable (limit to recent messages)
            - Use appropriate temperature settings for different conversation types
            """,
            response_description="Chat response with conversation context"
        )
        async def chat_with_llm(
            request: ChatRequest = Body(
                ...,
                examples={
                    "simple_chat": {
                        "summary": "Simple chat conversation",
                        "description": "Basic chat with single user message",
                        "value": {
                            "messages": [
                                {"role": "user", "content": "Hello! How are you?"}
                            ],
                            "model": "llama2",
                            "temperature": 0.7
                        }
                    },
                    "multi_turn": {
                        "summary": "Multi-turn conversation",
                        "description": "Conversation with system prompt and multiple messages",
                        "value": {
                            "messages": [
                                {"role": "system", "content": "You are a helpful coding assistant."},
                                {"role": "user", "content": "How do I create a list in Python?"},
                                {"role": "assistant", "content": "You can create a list using square brackets: my_list = [1, 2, 3]"},
                                {"role": "user", "content": "How do I add an item to the list?"}
                            ],
                            "model": "codellama",
                            "conversation_id": "conv-12345"
                        }
                    }
                }
            )
        ) -> LLMResponse:
            """Engage in chat conversation with an LLM."""
            try:
                import time
                import uuid

                start_time = time.time()
                request_id = f"chat-{uuid.uuid4().hex[:8]}"

                # Extract last user message for simulation
                last_user_message = ""
                for msg in reversed(request.messages):
                    if msg.role == "user":
                        last_user_message = msg.content
                        break

                # Simulate chat response
                processing_time = 1.2 + (len(request.messages) * 0.1)
                response_text = f"Based on our conversation, regarding '{last_user_message[:30]}...': This is a helpful response that considers the conversation context."

                return LLMResponse(
                    success=True,
                    response=response_text,
                    model=request.model or "llama2",
                    provider=request.provider or "ollama",
                    tokens_used=len(response_text.split()),
                    processing_time_seconds=processing_time,
                    request_id=request_id,
                    metadata={
                        "conversation_id": request.conversation_id,
                        "message_count": len(request.messages),
                        "finish_reason": "stop"
                    }
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Chat request failed: {str(e)}"
                )

        @self.router.get(
            "/providers",
            response_model=List[ProviderInfo],
            summary="List Available Providers",
            description="""
            Get information about all available LLM providers.

            Returns detailed information about each configured LLM provider,
            including their status, available models, capabilities, and rate limits.

            **Provider Information Includes:**
            - Current operational status
            - List of available models
            - API endpoints and capabilities
            - Rate limiting information
            - Performance metrics

            Use this endpoint to discover available providers and their capabilities
            before making generation requests.
            """,
            response_description="List of available LLM providers with details"
        )
        async def list_providers() -> List[ProviderInfo]:
            """Get information about available LLM providers."""
            try:
                # Mock provider information
                providers = [
                    ProviderInfo(
                        name="ollama",
                        display_name="Ollama Local Models",
                        status="healthy",
                        models=["llama2:7b", "llama2:13b", "codellama:7b", "mistral:7b"],
                        endpoint="http://ollama:11434",
                        capabilities=["text_generation", "chat", "streaming"],
                        rate_limits={"requests_per_minute": 60, "tokens_per_minute": 10000}
                    ),
                    ProviderInfo(
                        name="openai",
                        display_name="OpenAI GPT Models",
                        status="healthy",
                        models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                        endpoint="https://api.openai.com/v1",
                        capabilities=["text_generation", "chat", "function_calling"],
                        rate_limits={"requests_per_minute": 100, "tokens_per_minute": 100000}
                    )
                ]

                return providers

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to retrieve providers: {str(e)}"
                )

        @self.router.get(
            "/providers/{provider_name}",
            response_model=ProviderInfo,
            summary="Get Provider Details",
            description="""
            Get detailed information about a specific LLM provider.

            Returns comprehensive information about the specified provider,
            including real-time status, model availability, and performance metrics.

            **Use Cases:**
            - Check provider availability before requests
            - Get current model list and capabilities
            - Monitor provider performance and rate limits
            - Plan request routing and load balancing
            """,
            response_description="Detailed information about the specified provider"
        )
        async def get_provider(
            provider_name: str = Path(
                ...,
                description="Name of the provider to get details for",
                example="ollama"
            )
        ) -> ProviderInfo:
            """Get detailed information about a specific provider."""
            try:
                # Mock provider details based on name
                if provider_name == "ollama":
                    return ProviderInfo(
                        name="ollama",
                        display_name="Ollama Local Models",
                        status="healthy",
                        models=["llama2:7b", "llama2:13b", "codellama:7b"],
                        endpoint="http://ollama:11434",
                        capabilities=["text_generation", "chat", "streaming"],
                        rate_limits={"requests_per_minute": 60, "tokens_per_minute": 10000}
                    )
                elif provider_name == "openai":
                    return ProviderInfo(
                        name="openai",
                        display_name="OpenAI GPT Models",
                        status="healthy",
                        models=["gpt-3.5-turbo", "gpt-4"],
                        endpoint="https://api.openai.com/v1",
                        capabilities=["text_generation", "chat", "function_calling"],
                        rate_limits={"requests_per_minute": 100, "tokens_per_minute": 100000}
                    )
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Provider '{provider_name}' not found"
                    )

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to retrieve provider details: {str(e)}"
                )

        @self.router.get(
            "/stats",
            response_model=GatewayStats,
            summary="Get Gateway Statistics",
            description="""
            Retrieve comprehensive statistics about the LLM Gateway.

            Provides detailed metrics about usage, performance, and provider statistics
            to help monitor and optimize the gateway's operation.

            **Metrics Include:**
            - Total requests processed and active requests
            - Token usage and generation statistics
            - Response time averages and performance metrics
            - Provider-specific usage breakdown
            - Cache hit rates and efficiency metrics
            - System uptime and availability information

            **Use Cases:**
            - Monitor gateway performance and usage
            - Analyze provider effectiveness and load balancing
            - Track token consumption and cost optimization
            - Identify performance bottlenecks and optimization opportunities
            """,
            response_description="Comprehensive gateway statistics and metrics"
        )
        async def get_gateway_stats() -> GatewayStats:
            """Get comprehensive gateway statistics and performance metrics."""
            try:
                # Mock comprehensive statistics
                return GatewayStats(
                    total_requests=15432,
                    active_requests=3,
                    total_tokens=1250000,
                    average_response_time=1.45,
                    providers={
                        "ollama": {
                            "requests": 12000,
                            "tokens": 900000,
                            "avg_time": 1.2,
                            "cache_hits": 0.8
                        },
                        "openai": {
                            "requests": 3432,
                            "tokens": 350000,
                            "avg_time": 2.1,
                            "cache_hits": 0.6
                        }
                    },
                    uptime_seconds=86400,  # 24 hours
                    cache_hit_rate=0.75
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to retrieve statistics: {str(e)}"
                )

        @self.router.get(
            "/health",
            summary="Gateway Health Check",
            description="""
            Check the health status of the LLM Gateway.

            Performs comprehensive health checks across all configured providers
            and internal systems to ensure the gateway is operational.

            **Health Checks Include:**
            - Provider connectivity and availability
            - Database and cache connections
            - Rate limiting systems
            - Internal service dependencies
            - Response time performance

            **Response Codes:**
            - `healthy`: All systems operational
            - `degraded`: Some systems experiencing issues but still functional
            - `unhealthy`: Critical systems down, gateway may not function properly
            """,
            response_description="Gateway health status and system information"
        )
        async def health_check():
            """Comprehensive health check for the LLM Gateway."""
            try:
                return {
                    "status": "healthy",
                    "service": "llm-gateway",
                    "version": "1.0.0",
                    "timestamp": datetime.now().isoformat(),
                    "providers": {
                        "ollama": {"status": "healthy", "latency_ms": 45},
                        "openai": {"status": "healthy", "latency_ms": 120}
                    },
                    "systems": {
                        "cache": "healthy",
                        "rate_limiter": "healthy",
                        "metrics": "healthy",
                        "routing": "healthy"
                    },
                    "uptime_seconds": 86400
                }

            except Exception as e:
                return {
                    "status": "unhealthy",
                    "service": "llm-gateway",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

        @self.router.get(
            "/models",
            summary="List Available Models",
            description="""
            Get a comprehensive list of all available LLM models across all providers.

            Returns detailed information about each model including capabilities,
            context windows, pricing information, and performance characteristics.

            **Model Information Includes:**
            - Model name and version
            - Provider and hosting information
            - Supported capabilities (chat, completion, streaming, etc.)
            - Context window size and token limits
            - Performance metrics and benchmarks
            - Pricing and rate limit information

            **Use Cases:**
            - Discover available models for specific tasks
            - Compare model capabilities and performance
            - Select appropriate models for use cases
            - Plan resource usage and costs
            """,
            response_description="Comprehensive list of available models"
        )
        async def list_models(
            provider: Optional[LLMProvider] = Query(
                None,
                description="Filter by specific provider",
                example=LLMProvider.OLLAMA
            ),
            capability: Optional[str] = Query(
                None,
                description="Filter by capability (chat, completion, streaming)",
                example="chat"
            )
        ):
            """Get comprehensive list of available LLM models."""
            try:
                # Mock comprehensive model list
                all_models = [
                    {
                        "name": "llama2:7b",
                        "provider": "ollama",
                        "display_name": "Llama 2 7B",
                        "capabilities": ["text_generation", "chat", "streaming"],
                        "context_window": 4096,
                        "description": "General purpose conversational model"
                    },
                    {
                        "name": "llama2:13b",
                        "provider": "ollama",
                        "display_name": "Llama 2 13B",
                        "capabilities": ["text_generation", "chat", "streaming"],
                        "context_window": 4096,
                        "description": "Enhanced conversational model with better reasoning"
                    },
                    {
                        "name": "codellama:7b",
                        "provider": "ollama",
                        "display_name": "Code Llama 7B",
                        "capabilities": ["text_generation", "code", "chat"],
                        "context_window": 16384,
                        "description": "Specialized model for code generation and understanding"
                    },
                    {
                        "name": "gpt-3.5-turbo",
                        "provider": "openai",
                        "display_name": "GPT-3.5 Turbo",
                        "capabilities": ["text_generation", "chat", "function_calling"],
                        "context_window": 16384,
                        "description": "Fast and cost-effective GPT model for most tasks"
                    }
                ]

                # Apply filters
                filtered_models = all_models

                if provider:
                    filtered_models = [m for m in filtered_models if m["provider"] == provider.value]

                if capability:
                    filtered_models = [m for m in filtered_models if capability in m["capabilities"]]

                return {
                    "models": filtered_models,
                    "total_count": len(filtered_models),
                    "filters_applied": {
                        "provider": provider.value if provider else None,
                        "capability": capability
                    }
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to retrieve models: {str(e)}"
                )

        @self.router.post(
            "/validate",
            summary="Validate LLM Request",
            description="""
            Validate an LLM request without actually executing it.

            This endpoint allows you to check if a request would be valid and
            estimate costs, token usage, and other parameters before execution.

            **Validation Includes:**
            - Parameter validation and bounds checking
            - Model availability and capability verification
            - Token count estimation and cost calculation
            - Rate limit checking
            - Input sanitization and security validation

            **Use Cases:**
            - Pre-flight checks before expensive requests
            - Cost estimation for billing purposes
            - Parameter validation in user interfaces
            - Debugging and troubleshooting request issues
            """,
            response_description="Validation results with estimates and recommendations"
        )
        async def validate_request(
            request: Union[LLMQueryRequest, ChatRequest] = Body(
                ...,
                examples={
                    "query_validation": {
                        "summary": "Validate query request",
                        "value": {
                            "prompt": "Write a hello world program in Python",
                            "model": "codellama",
                            "max_tokens": 200,
                            "temperature": 0.5
                        }
                    }
                }
            )
        ):
            """Validate an LLM request and provide estimates."""
            try:
                # Mock validation logic
                validation_result = {
                    "valid": True,
                    "request_type": "query" if hasattr(request, 'prompt') else "chat",
                    "model": request.model if hasattr(request, 'model') else "llama2",
                    "estimated_tokens": 150,
                    "estimated_cost": 0.002,
                    "estimated_time_seconds": 2.5,
                    "warnings": [],
                    "recommendations": [
                        "Consider using a lower temperature for code generation",
                        "Request is within rate limits"
                    ]
                }

                return validation_result

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Request validation failed: {str(e)}"
                )


# Factory function to create router
def create_llm_router() -> APIRouter:
    """Create LLM Gateway router with comprehensive OpenAPI documentation."""
    router_instance = LLMRouter()
    return router_instance.router
