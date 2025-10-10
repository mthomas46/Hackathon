"""
Standard API routes required by all services.

Provides health checks, service metadata, and API documentation endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from infrastructure.config.settings import Settings, get_settings
from utils.constants import (
    SERVICE_NAME,
    SERVICE_VERSION,
    ENDPOINT_HEALTH,
    ENDPOINT_ABOUT_ME,
    ENDPOINT_ENDPOINTS,
    ENDPOINT_PROVIDER_CONSUMER,
)

router = APIRouter()


@router.get(ENDPOINT_HEALTH, tags=["Standard"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns service health status and basic information.
    """
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION
    }


@router.get(ENDPOINT_ABOUT_ME, tags=["Standard"])
async def about_me(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Service metadata endpoint.
    
    Describes the service, its capabilities, and its role in the ecosystem.
    """
    return {
        "service_name": settings.service_name,
        "version": settings.service_version,
        "description": "Intelligent User Discovery & Subject Matter Expert Identification",
        "capabilities": {
            "expert_search": "Find experts by role, topic, or natural language query",
            "sme_identification": "Identify subject matter experts with significant contributions",
            "teammate_discovery": "Find potential collaborators based on shared interests",
            "team_expertise": "Aggregate team capabilities and knowledge areas"
        },
        "ecosystem_role": {
            "type": "Query Service",
            "purpose": "Enables intelligent discovery of users with specific expertise",
            "value_proposition": "Smart, relevance-based expert matching across the ecosystem"
        },
        "architecture": {
            "pattern": "Domain-Driven Design (DDD)",
            "layers": ["domain", "application", "infrastructure", "presentation"],
            "dependencies": ["user-store (primary)", "doc-store (optional)", "external-service-store (optional)"]
        },
        "scoring_algorithm": {
            "role_weight": settings.role_weight,
            "topic_weight": settings.topic_weight,
            "service_weight": settings.service_weight,
            "document_weight": settings.document_weight,
            "description": "Multi-factor relevance scoring with configurable weights"
        }
    }


@router.get(ENDPOINT_ENDPOINTS, tags=["Standard"])
async def list_endpoints() -> Dict[str, List[Dict[str, str]]]:
    """
    List all available API endpoints.
    
    Returns structured information about all endpoints exposed by the service.
    """
    return {
        "standard_endpoints": [
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check"
            },
            {
                "path": "/about-me",
                "method": "GET",
                "description": "Service metadata"
            },
            {
                "path": "/endpoints",
                "method": "GET",
                "description": "List all endpoints"
            },
            {
                "path": "/provider-consumer",
                "method": "GET",
                "description": "Service dependencies"
            },
            {
                "path": "/openapi.json",
                "method": "GET",
                "description": "OpenAPI specification"
            }
        ],
        "business_endpoints": [
            {
                "path": "/api/v1/find-experts",
                "method": "POST",
                "description": "Find experts matching criteria"
            },
            {
                "path": "/api/v1/identify-smes",
                "method": "POST",
                "description": "Identify subject matter experts"
            },
            {
                "path": "/api/v1/find-teammates",
                "method": "POST",
                "description": "Find potential teammates"
            },
            {
                "path": "/api/v1/aggregate-team-expertise",
                "method": "POST",
                "description": "Aggregate team expertise"
            }
        ]
    }


@router.get(ENDPOINT_PROVIDER_CONSUMER, tags=["Standard"])
async def provider_consumer() -> Dict[str, Any]:
    """
    Service relationship map.
    
    Lists all services this service connects to, marking the relationship
    as provider (provides data), consumer (consumes data), or both.
    """
    return {
        "service_name": SERVICE_NAME,
        "relationships": [
            {
                "service": "user-store",
                "relationship": "consumer",
                "description": "Consumes user data for expert matching",
                "criticality": "required",
                "endpoints_used": [
                    "/users/{user_id}",
                    "/users/search",
                    "/users/by-role",
                    "/users/by-topic",
                    "/teams/{team_id}/members"
                ]
            },
            {
                "service": "doc-store",
                "relationship": "consumer",
                "description": "Consumes document authorship data for SME identification",
                "criticality": "optional",
                "endpoints_used": [
                    "/documents/by-author/{user_id}",
                    "/documents/by-topic"
                ]
            },
            {
                "service": "external-service-store",
                "relationship": "consumer",
                "description": "Consumes service contribution data for expertise assessment",
                "criticality": "optional",
                "endpoints_used": [
                    "/services/by-user/{user_id}",
                    "/services/{service_name}/contributors"
                ]
            }
        ],
        "dependency_summary": {
            "required_services": ["user-store"],
            "optional_services": ["doc-store", "external-service-store"],
            "provides_data_to": [],
            "consumes_data_from": ["user-store", "doc-store", "external-service-store"]
        }
    }

