"""Standard API endpoints for bedrock-proxy service.

Implements the 5 standard endpoints required by the microservices architecture:
- GET /health: Service health check
- GET /about-me: Comprehensive service descriptor
- GET /endpoints: List of all available endpoints
- GET /provider-consumer: Service relationships and dependencies
- GET /openapi.json: OpenAPI specification (provided by FastAPI)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter

# Create router for standard endpoints (no prefix, root level)
router = APIRouter(tags=["standard"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.
    
    Returns service health status, version, and uptime information.
    Used by Docker health checks, monitoring systems, and orchestration layers.
    
    Returns:
        Health status with service metadata
    """
    return {
        "service": "bedrock-proxy",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/about-me")
async def about_me() -> Dict[str, Any]:
    """Comprehensive service descriptor endpoint.
    
    Provides detailed information about the service including capabilities,
    features, architecture, dependencies, and integration points.
    
    Returns:
        Complete service descriptor with metadata
    """
    return {
        "service": "bedrock-proxy",
        "version": "1.0.0",
        "description": "AWS Bedrock Integration Gateway with template-driven response generation",
        "capabilities": [
            "AWS Bedrock foundation model access (Claude, Titan, etc.)",
            "Template-driven response generation",
            "Multi-format output support (Markdown, Text, JSON)",
            "Development mocking for cost-free testing",
            "Production-ready proxy with authentication",
        ],
        "features": {
            "templates": {
                "supported": ["summary", "risks", "decisions", "pr_confidence", "life_of_ticket"],
                "description": "Predefined templates for structured AI responses",
            },
            "formats": {
                "supported": ["md", "txt", "json"],
                "description": "Multiple output formats for different use cases",
            },
            "modes": {
                "mock": "Development mode with template-based responses (no AWS costs)",
                "production": "Full AWS Bedrock integration with real foundation models",
            },
            "models": {
                "supported": [
                    "anthropic.claude-3-sonnet-20240229-v1:0",
                    "anthropic.claude-3-haiku-20240307-v1:0",
                    "amazon.titan-text-express-v1",
                ],
                "description": "AWS Bedrock foundation models",
            },
        },
        "ecosystem_role": "ai_gateway",
        "tier": 2,
        "dependencies": {
            "providers": [
                {
                    "service": "aws-bedrock",
                    "purpose": "Foundation model access",
                    "critical": True,
                },
            ],
            "consumers": [
                {
                    "service": "summarizer-hub",
                    "purpose": "Primary AI processing client",
                    "frequency": "high",
                },
                {
                    "service": "llm-gateway",
                    "purpose": "AI provider coordination",
                    "frequency": "medium",
                },
            ],
        },
        "architecture": {
            "pattern": "DDD",
            "layers": [
                "Domain (entities, value objects, services)",
                "Application (commands, handlers)",
                "Infrastructure (processor, templates, validation)",
                "Presentation (API, routes)",
            ],
        },
        "api": {
            "version": "v1",
            "base_path": "/api/v1",
            "documentation": "/docs",
            "openapi_spec": "/openapi.json",
        },
        "configuration": {
            "ports": {
                "internal": 7090,
                "external": 5060,
            },
            "environment_variables": [
                "SERVICE_API_PORT",
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "AWS_REGION",
                "BEDROCK_MOCK_MODE",
            ],
        },
    }


@router.get("/endpoints")
async def endpoints() -> Dict[str, Any]:
    """List all available endpoints.
    
    Provides a comprehensive list of all API endpoints with descriptions,
    methods, authentication requirements, and categorization.
    
    Returns:
        Complete endpoint listing with metadata
    """
    return {
        "service": "bedrock-proxy",
        "version": "1.0.0",
        "base_url": "http://bedrock-proxy:7090",
        "endpoints": [
            {
                "path": "/health",
                "methods": ["GET"],
                "description": "Service health check",
                "authentication": "none",
                "category": "standard",
            },
            {
                "path": "/about-me",
                "methods": ["GET"],
                "description": "Service descriptor with capabilities and features",
                "authentication": "none",
                "category": "standard",
            },
            {
                "path": "/endpoints",
                "methods": ["GET"],
                "description": "List all available endpoints",
                "authentication": "none",
                "category": "standard",
            },
            {
                "path": "/provider-consumer",
                "methods": ["GET"],
                "description": "Service relationships and dependencies",
                "authentication": "none",
                "category": "standard",
            },
            {
                "path": "/openapi.json",
                "methods": ["GET"],
                "description": "OpenAPI 3.1.0 specification",
                "authentication": "none",
                "category": "standard",
            },
            {
                "path": "/api/v1/invoke",
                "methods": ["POST"],
                "description": "AI model invocation with template-driven responses",
                "authentication": "optional",
                "category": "core",
                "parameters": {
                    "prompt": "Input text for AI processing",
                    "model": "AWS Bedrock model identifier",
                    "region": "AWS region",
                    "template": "Response template (summary, risks, decisions, pr_confidence, life_of_ticket)",
                    "format": "Output format (md, txt, json)",
                    "title": "Custom title for response",
                },
            },
        ],
        "categories": {
            "standard": "Standard microservice endpoints (health, about-me, etc.)",
            "core": "Core Bedrock proxy functionality",
        },
    }


@router.get("/provider-consumer")
async def provider_consumer() -> Dict[str, Any]:
    """Service relationships and dependencies.
    
    Documents all provider and consumer relationships, data flow patterns,
    integration points, and dependency information.
    
    Returns:
        Complete service relationship mapping
    """
    return {
        "service": "bedrock-proxy",
        "version": "1.0.0",
        "relationships": {
            "providers": [
                {
                    "service": "aws-bedrock",
                    "relationship": "provider",
                    "purpose": "Provides foundation model access (Claude, Titan, etc.)",
                    "endpoints_used": [
                        "invoke-model",
                        "list-foundation-models",
                    ],
                    "data_consumed": [
                        "Model responses",
                        "Model metadata",
                        "Usage statistics",
                    ],
                },
            ],
            "consumers": [
                {
                    "service": "summarizer-hub",
                    "relationship": "consumer",
                    "purpose": "Primary AI processing client for content summarization",
                    "data_provided": [
                        "Template-driven summaries",
                        "Risk analyses",
                        "Decision documentation",
                    ],
                },
                {
                    "service": "llm-gateway",
                    "relationship": "consumer",
                    "purpose": "AI provider coordination and routing",
                    "data_provided": [
                        "Bedrock model responses",
                        "Provider availability",
                        "Usage metrics",
                    ],
                },
            ],
            "provide_consume": [],
        },
        "dependencies": {
            "external_apis": [
                {
                    "name": "AWS Bedrock",
                    "purpose": "Foundation model access",
                    "required": False,  # False in mock mode
                    "note": "Required in production mode, optional in mock mode",
                },
            ],
            "databases": [],
            "message_queues": [],
            "cache_systems": [],
        },
        "provides_data_to": ["summarizer-hub", "llm-gateway"],
        "consumes_data_from": ["aws-bedrock"],
        "self_contained": True,  # Can run in mock mode without external dependencies
        "reason_self_contained": "Mock mode provides complete functionality without AWS Bedrock",
        "data_flow": {
            "inbound": [
                {
                    "source": "summarizer-hub",
                    "data_type": "ai_requests",
                    "frequency": "high",
                },
                {
                    "source": "llm-gateway",
                    "data_type": "model_requests",
                    "frequency": "medium",
                },
            ],
            "outbound": [
                {
                    "destination": "aws-bedrock",
                    "data_type": "model_invocations",
                    "frequency": "variable",
                    "condition": "production mode only",
                },
            ],
        },
        "integration_points": {
            "aws-bedrock": {
                "type": "REST API / AWS SDK",
                "direction": "outbound",
                "critical": False,  # False in mock mode
            },
            "summarizer-hub": {
                "type": "REST API",
                "direction": "inbound",
                "critical": True,
            },
            "llm-gateway": {
                "type": "REST API",
                "direction": "inbound",
                "critical": False,
            },
        },
    }

