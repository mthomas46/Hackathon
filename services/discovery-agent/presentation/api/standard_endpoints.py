"""
Standard API endpoints required by ecosystem architecture.

Implements the 4 standard endpoints:
- GET /health - Health check
- GET /about-me - Service descriptor
- GET /endpoints - Endpoint list
- GET /provider-consumer - Service relationships
"""

from fastapi import APIRouter
from datetime import datetime, timezone
from typing import Dict, List, Any
import time

# Track service start time for uptime calculation
SERVICE_START_TIME = time.time()
SERVICE_VERSION = "1.0.0"

router = APIRouter(tags=["standard"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Health status including uptime and service info
    """
    uptime_seconds = int(time.time() - SERVICE_START_TIME)
    
    return {
        "status": "healthy",
        "service": "discovery-agent",
        "version": SERVICE_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_seconds
    }


@router.get("/about-me")
async def about_me() -> Dict[str, Any]:
    """
    Service descriptor endpoint.
    
    Returns comprehensive information about the discovery-agent service,
    including capabilities, features, dependencies, and architecture.
    """
    return {
        "service": "discovery-agent",
        "version": SERVICE_VERSION,
        "description": "Automated service discovery and LangGraph tool generation service",
        
        "capabilities": [
            "OpenAPI specification discovery",
            "Service endpoint extraction",
            "LangGraph tool generation",
            "Semantic endpoint analysis",
            "Tool registry management",
            "Orchestrator integration",
            "Security scanning integration"
        ],
        
        "features": {
            "discovery": {
                "openapi_versions": ["3.0.x", "3.1.x"],
                "sources": ["URL", "inline content"],
                "parsing": "Full OpenAPI 3.0 specification parsing"
            },
            "tool_generation": {
                "target": "LangGraph",
                "naming": "Automatic tool naming from endpoints",
                "categorization": "Semantic analysis for tool categories",
                "validation": "Parameter and schema validation"
            },
            "integration": {
                "orchestrator": "Service and tool registration",
                "log_collector": "Structured logging with correlation IDs",
                "secure_analyzer": "Endpoint security scanning"
            }
        },
        
        "ecosystem_role": "integration",
        "tier": 3,
        
        "dependencies": {
            "providers": [
                {
                    "service": "orchestrator",
                    "purpose": "Service registry and coordination",
                    "critical": True
                },
                {
                    "service": "log-collector",
                    "purpose": "Centralized logging",
                    "critical": False
                }
            ],
            "consumers": [
                {
                    "service": "orchestrator",
                    "purpose": "Consumes discovered services and tools",
                    "frequency": "on-demand"
                },
                {
                    "service": "all-services",
                    "purpose": "Any service can request discovery",
                    "frequency": "as-needed"
                }
            ]
        },
        
        "architecture": {
            "pattern": "DDD",
            "layers": [
                "Domain (entities, value objects, services)",
                "Application (commands, queries, handlers)",
                "Infrastructure (clients, repositories)",
                "Presentation (API, routes)"
            ],
            "patterns": [
                "Domain-Driven Design",
                "Clean Architecture",
                "Repository Pattern",
                "Service Layer Pattern"
            ]
        },
        
        "quality_metrics": {
            "test_coverage": "80%+",
            "total_tests": "133+",
            "test_types": ["unit", "integration", "e2e", "workflow"],
            "code_style": "Black + Pylint",
            "type_checking": "MyPy"
        },
        
        "api": {
            "version": "v1",
            "base_path": "/api/v1",
            "documentation": "/docs",
            "openapi_spec": "/openapi.json"
        },
        
        "configuration": {
            "ports": {
                "http": 5050,
                "internal": 5051
            },
            "timeouts": {
                "discovery": 30,
                "tool_generation": 60
            }
        }
    }


@router.get("/endpoints")
async def list_endpoints() -> Dict[str, Any]:
    """
    Endpoint list endpoint.
    
    Returns a comprehensive list of all available API endpoints
    with metadata about each endpoint.
    """
    endpoints_data = [
        # Standard endpoints
        {
            "path": "/health",
            "methods": ["GET"],
            "description": "Health check endpoint",
            "authentication": "none",
            "category": "standard"
        },
        {
            "path": "/about-me",
            "methods": ["GET"],
            "description": "Service descriptor with capabilities and features",
            "authentication": "none",
            "category": "standard"
        },
        {
            "path": "/endpoints",
            "methods": ["GET"],
            "description": "List all available API endpoints",
            "authentication": "none",
            "category": "standard"
        },
        {
            "path": "/provider-consumer",
            "methods": ["GET"],
            "description": "Service relationships and dependencies",
            "authentication": "none",
            "category": "standard"
        },
        
        # Core discovery endpoints
        {
            "path": "/api/v1/discover",
            "methods": ["POST"],
            "description": "Discover service from OpenAPI specification",
            "authentication": "optional",
            "category": "core",
            "parameters": {
                "service_name": "required",
                "openapi_url": "optional (or openapi_content)",
                "openapi_content": "optional (or openapi_url)"
            }
        },
        {
            "path": "/api/v1/discover/tools",
            "methods": ["POST"],
            "description": "Discover service and generate LangGraph tools",
            "authentication": "optional",
            "category": "core",
            "parameters": {
                "service_name": "required",
                "openapi_url": "optional (or openapi_content)",
                "openapi_content": "optional (or openapi_url)"
            }
        },
        {
            "path": "/api/v1/services/{service_name}",
            "methods": ["GET"],
            "description": "Get information about a discovered service",
            "authentication": "optional",
            "category": "core",
            "parameters": {
                "service_name": "required (path parameter)"
            }
        },
        
        # Documentation endpoints
        {
            "path": "/docs",
            "methods": ["GET"],
            "description": "Interactive API documentation (Swagger UI)",
            "authentication": "none",
            "category": "documentation"
        },
        {
            "path": "/redoc",
            "methods": ["GET"],
            "description": "Alternative API documentation (ReDoc)",
            "authentication": "none",
            "category": "documentation"
        },
        {
            "path": "/openapi.json",
            "methods": ["GET"],
            "description": "OpenAPI specification for this service",
            "authentication": "none",
            "category": "documentation"
        }
    ]
    
    # Count endpoints by category
    categories = {}
    for endpoint in endpoints_data:
        category = endpoint["category"]
        categories[category] = categories.get(category, 0) + 1
    
    return {
        "service": "discovery-agent",
        "version": SERVICE_VERSION,
        "base_url": "http://discovery-agent:5050",
        "endpoints": endpoints_data,
        "total_endpoints": len(endpoints_data),
        "categories": categories,
        "api_version": "v1"
    }


@router.get("/provider-consumer")
async def provider_consumer_relationships() -> Dict[str, Any]:
    """
    Provider-consumer relationships endpoint.
    
    Returns detailed information about this service's relationships
    with other services in the ecosystem.
    """
    return {
        "service": "discovery-agent",
        "version": SERVICE_VERSION,
        
        "relationships": {
            "providers": [
                {
                    "service": "orchestrator",
                    "relationship": "provider",
                    "purpose": "Provides service registry and coordination",
                    "endpoints_used": [
                        "GET /api/v1/services",
                        "POST /api/v1/services/register"
                    ],
                    "data_consumed": [
                        "Service registry information",
                        "Service health status"
                    ]
                }
            ],
            
            "consumers": [
                {
                    "service": "orchestrator",
                    "relationship": "consumer",
                    "purpose": "Receives discovered services and generated tools",
                    "data_provided": [
                        "Discovered service information",
                        "LangGraph tool definitions",
                        "Service endpoint metadata"
                    ]
                },
                {
                    "service": "all-services",
                    "relationship": "consumer",
                    "purpose": "Any service can request discovery of other services",
                    "data_provided": [
                        "Service discovery results",
                        "OpenAPI specifications",
                        "Endpoint information"
                    ]
                }
            ],
            
            "provide_consume": [
                {
                    "service": "log-collector",
                    "relationship": "provide-consume",
                    "purpose": "Sends logs (consumer) and receives log insights (provider)",
                    "data_flow": "bidirectional"
                }
            ]
        },
        
        "dependencies": {
            "external_apis": [
                {
                    "name": "Target Service OpenAPI URLs",
                    "purpose": "Fetching OpenAPI specifications",
                    "required": False,
                    "note": "Can also accept inline content"
                }
            ],
            "databases": [],
            "message_queues": [],
            "cache_systems": []
        },
        
        "provides_data_to": [
            "orchestrator",
            "all-services"
        ],
        
        "consumes_data_from": [
            "orchestrator",
            "target-services"
        ],
        
        "self_contained": False,
        "reason_not_self_contained": "Requires orchestrator for service registration and coordination",
        
        "data_flow": {
            "inbound": [
                {
                    "source": "orchestrator",
                    "data_type": "service_registry_info",
                    "frequency": "on-request"
                },
                {
                    "source": "any-service",
                    "data_type": "discovery_requests",
                    "frequency": "on-demand"
                },
                {
                    "source": "target-services",
                    "data_type": "openapi_specifications",
                    "frequency": "on-discovery"
                }
            ],
            "outbound": [
                {
                    "destination": "orchestrator",
                    "data_type": "discovered_services",
                    "frequency": "on-discovery"
                },
                {
                    "destination": "orchestrator",
                    "data_type": "generated_tools",
                    "frequency": "on-tool-generation"
                },
                {
                    "destination": "log-collector",
                    "data_type": "discovery_logs",
                    "frequency": "continuous"
                }
            ]
        },
        
        "integration_points": {
            "orchestrator": {
                "type": "REST API",
                "direction": "bidirectional",
                "critical": True
            },
            "log-collector": {
                "type": "REST API",
                "direction": "outbound",
                "critical": False
            },
            "secure-analyzer": {
                "type": "REST API",
                "direction": "outbound",
                "critical": False
            }
        }
    }

