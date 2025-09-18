"""LLM Gateway Service Package.

The LLM Gateway provides unified, secure, and optimized access to all LLM providers
in the LLM Documentation Ecosystem. It acts as a service mesh that intelligently
routes requests, manages caching, enforces security policies, and provides
comprehensive metrics and rate limiting.

Key Features:
- Intelligent provider routing based on content analysis
- Security-aware processing for sensitive content
- Response caching with TTL-based expiration
- Comprehensive metrics and performance tracking
- Rate limiting with burst protection
- Multi-provider support (Ollama, OpenAI, Anthropic, AWS Bedrock, Grok)

Main Components:
- main.py: FastAPI application and API endpoints
- modules/provider_router.py: Intelligent provider selection and routing
- modules/security_filter.py: Content analysis and security enforcement
- modules/cache_manager.py: Response caching and optimization
- modules/metrics_collector.py: Usage tracking and analytics
- modules/rate_limiter.py: Request throttling and abuse prevention
- modules/models.py: Pydantic models for API requests/responses
"""

__version__ = "1.0.0"
__author__ = "LLM Documentation Ecosystem Team"
__description__ = "Unified LLM Gateway for secure, optimized access to all LLM providers"

# Service metadata
SERVICE_NAME = "llm-gateway"
SERVICE_TITLE = "LLM Gateway"
SERVICE_DESCRIPTION = "Unified access to all LLM providers with intelligent routing, security, and optimization"
DEFAULT_PORT = 5055

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "SERVICE_NAME",
    "SERVICE_TITLE",
    "SERVICE_DESCRIPTION",
    "DEFAULT_PORT"
]
